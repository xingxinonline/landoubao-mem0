"""
Test LLM's ability to use MCP server tools
Connects to MCP server, gets tool list, and tests LLM tool calling
"""

import asyncio
import json
import os
from typing import List, Dict, Any
import httpx
from openai import OpenAI


class MCPClient:
    """Simple MCP HTTP client"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.request_id = 0
    
    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id
    
    async def initialize(self) -> Dict:
        """Initialize connection and get server capabilities"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp/messages",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "test-llm-client",
                            "version": "1.0.0"
                        }
                    }
                }
            )
            return response.json()
    
    async def list_tools(self) -> List[Dict]:
        """Get list of available tools from MCP server"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp/messages",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "tools/list",
                    "params": {}
                }
            )
            result = response.json()
            return result.get("result", {}).get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict) -> Dict:
        """Call a tool on the MCP server"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/mcp/messages",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": arguments
                    }
                }
            )
            return response.json()


def convert_mcp_tools_to_openai_format(mcp_tools: List[Dict]) -> List[Dict]:
    """
    Convert MCP tool definitions to OpenAI function calling format
    
    MCP format:
    {
        "name": "tool_name",
        "description": "...",
        "inputSchema": { JSON Schema }
    }
    
    OpenAI format:
    {
        "type": "function",
        "function": {
            "name": "tool_name",
            "description": "...",
            "parameters": { JSON Schema }
        }
    }
    """
    openai_tools = []
    for tool in mcp_tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["inputSchema"]
            }
        }
        openai_tools.append(openai_tool)
    return openai_tools


async def test_llm_with_mcp_tools():
    """Test LLM's ability to use MCP tools"""
    
    # Step 1: Connect to MCP server and get tools
    print("=" * 60)
    print("Step 1: Connecting to MCP Server")
    print("=" * 60)
    
    mcp_client = MCPClient()
    
    # Initialize connection
    init_response = await mcp_client.initialize()
    print(f"\n✓ Connected to MCP server")
    print(f"Server: {init_response.get('result', {}).get('serverInfo', {})}")
    
    # Get tool list
    mcp_tools = await mcp_client.list_tools()
    print(f"\n✓ Retrieved {len(mcp_tools)} tools from MCP server:")
    for tool in mcp_tools:
        print(f"  - {tool['name']}: {tool['description'][:60]}...")
    
    # Step 2: Convert to OpenAI format
    print("\n" + "=" * 60)
    print("Step 2: Converting MCP Tools to OpenAI Format")
    print("=" * 60)
    
    openai_tools = convert_mcp_tools_to_openai_format(mcp_tools)
    print(f"\n✓ Converted {len(openai_tools)} tools to OpenAI format")
    print("\nExample converted tool:")
    print(json.dumps(openai_tools[0], indent=2, ensure_ascii=False))
    
    # Step 3: Initialize LLM client
    print("\n" + "=" * 60)
    print("Step 3: Testing LLM Tool Calling")
    print("=" * 60)
    
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("\n✗ Error: ZHIPU_API_KEY not set")
        return
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4"
    )
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Memory Storage Test",
            "user_message": "请帮我记住这些信息:我叫张三,是一名高级Python开发工程师,喜欢研究AI技术。用户ID是user_001。",
            "expected_tool": "add_memory"
        },
        {
            "name": "Memory Search Test", 
            "user_message": "帮我搜索一下user_001关于'Python'的记忆",
            "expected_tool": "search_memory"
        },
        {
            "name": "Multilingual Memory Storage",
            "user_message": "请记住: My name is John Smith, I'm a senior software engineer. User ID: user_002",
            "expected_tool": "add_memory"
        },
        {
            "name": "Memory Correction Test",
            "user_message": "我之前说最喜欢咖啡，但现在我改变主意了，我最喜欢茶。请更新我的喜好。用户ID: user_001",
            "expected_tool": "add_memory"
        },
        {
            "name": "Verify Correction",
            "user_message": "user_001最喜欢的饮料是什么？",
            "expected_tool": "search_memory"
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n{'─' * 60}")
        print(f"Test: {scenario['name']}")
        print(f"{'─' * 60}")
        print(f"User: {scenario['user_message']}")
        
        try:
            # Call LLM with tools
            response = client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个智能助手,可以使用提供的工具来帮助用户管理记忆。请根据用户需求选择合适的工具。注意:user_id必须作为顶层参数传递,不能放在metadata中。"
                    },
                    {
                        "role": "user",
                        "content": scenario["user_message"]
                    }
                ],
                tools=openai_tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Check if LLM wants to call a tool
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"\n✓ LLM chose to call tool: {tool_name}")
                print(f"  Arguments: {json.dumps(tool_args, indent=2, ensure_ascii=False)}")
                
                # Verify correct tool selection
                expected_match = tool_name == scenario["expected_tool"]
                print(f"  Expected: {scenario['expected_tool']}")
                print(f"  Match: {'✓' if expected_match else '✗'}")
                
                # Actually call the MCP tool
                print(f"\n  Executing tool via MCP server...")
                mcp_result = await mcp_client.call_tool(tool_name, tool_args)
                
                if "result" in mcp_result:
                    print(f"  ✓ Tool execution successful")
                    tool_output = mcp_result["result"]["content"][0]["text"]
                    print(f"  Result preview: {tool_output[:200]}...")
                    
                    # Get final response from LLM
                    final_response = client.chat.completions.create(
                        model="glm-4-flash",
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一个智能助手,可以使用提供的工具来帮助用户管理记忆。"
                            },
                            {
                                "role": "user",
                                "content": scenario["user_message"]
                            },
                            message,
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": tool_output
                            }
                        ],
                        tools=openai_tools
                    )
                    
                    final_message = final_response.choices[0].message.content
                    print(f"\n  Final Response: {final_message}")
                    
                    results.append({
                        "scenario": scenario["name"],
                        "success": True,
                        "tool_called": tool_name,
                        "expected_match": expected_match
                    })
                else:
                    print(f"  ✗ Tool execution failed: {mcp_result.get('error', {})}")
                    results.append({
                        "scenario": scenario["name"],
                        "success": False,
                        "error": "Tool execution failed"
                    })
            else:
                print(f"\n✗ LLM did not call any tool")
                print(f"  Response: {message.content}")
                results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "error": "No tool call"
                })
        
        except Exception as e:
            print(f"\n✗ Error: {repr(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "scenario": scenario["name"],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r.get("success"))
    total_count = len(results)
    
    print(f"\nTotal Tests: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    print(f"Success Rate: {success_count/total_count*100:.1f}%")
    
    print("\nDetailed Results:")
    for result in results:
        status = "✓" if result.get("success") else "✗"
        print(f"  {status} {result['scenario']}")
        if result.get("tool_called"):
            match = "✓" if result.get("expected_match") else "✗"
            print(f"    Tool: {result['tool_called']} {match}")
        if result.get("error"):
            print(f"    Error: {result['error']}")


async def demo_tool_discovery():
    """Demonstrate MCP tool discovery and conversion"""
    
    print("=" * 60)
    print("MCP Tool Discovery and Conversion Demo")
    print("=" * 60)
    
    mcp_client = MCPClient()
    
    # Get tools from MCP
    print("\n1. Fetching tools from MCP server...")
    mcp_tools = await mcp_client.list_tools()
    
    print(f"\n   Found {len(mcp_tools)} MCP tools:\n")
    for i, tool in enumerate(mcp_tools, 1):
        print(f"   {i}. {tool['name']}")
        print(f"      {tool['description']}")
        print()
    
    # Convert to OpenAI format
    print("\n2. Converting to OpenAI tool format...\n")
    openai_tools = convert_mcp_tools_to_openai_format(mcp_tools)
    
    # Show comparison
    print("   MCP Format vs OpenAI Format:\n")
    print("   MCP Tool Schema:")
    print(json.dumps(mcp_tools[0], indent=4, ensure_ascii=False))
    print("\n   ↓ Converted to ↓\n")
    print("   OpenAI Tool Schema:")
    print(json.dumps(openai_tools[0], indent=4, ensure_ascii=False))
    
    # Save to file for reference
    with open("mcp_tools_openai_format.json", "w", encoding="utf-8") as f:
        json.dump(openai_tools, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved converted tools to: mcp_tools_openai_format.json")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Just show tool discovery and conversion
        asyncio.run(demo_tool_discovery())
    else:
        # Run full LLM test
        asyncio.run(test_llm_with_mcp_tools())
