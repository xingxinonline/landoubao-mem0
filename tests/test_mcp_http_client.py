"""
Test client for MCP HTTP SSE Server
Demonstrates remote access with async/concurrent operations
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional
import uuid

class MCPHTTPClient:
    """MCP Client using HTTP SSE transport for remote access."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_id = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _next_request_id(self) -> str:
        """Generate next request ID."""
        self.request_id += 1
        return f"req-{self.request_id}"
    
    async def send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Send JSON-RPC 2.0 request to MCP server."""
        request_data = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params or {}
        }
        
        async with self.session.post(
            f"{self.base_url}/mcp/messages",
            json=request_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            result = await response.json()
            
            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")
            
            return result.get("result", {})
    
    async def initialize(self) -> Dict:
        """Initialize MCP connection."""
        return await self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-test-client",
                "version": "1.0.0"
            }
        })
    
    async def list_tools(self) -> Dict:
        """List available tools."""
        return await self.send_request("tools/list")
    
    async def call_tool(self, name: str, arguments: Dict) -> Any:
        """Call a tool."""
        result = await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        
        # Extract text content from MCP response
        content = result.get("content", [])
        if content and len(content) > 0:
            text = content[0].get("text", "{}")
            return json.loads(text)
        return {}
    
    async def add_memory(self, user_id: str, messages: list, language: Optional[str] = None, metadata: Optional[Dict] = None):
        """Add memory with multilingual support."""
        args = {
            "user_id": user_id,
            "messages": messages,
            "metadata": metadata or {}
        }
        if language:
            args["language"] = language
        
        return await self.call_tool("add_memory", args)
    
    async def search_memory(self, user_id: str, query: str, limit: int = 5):
        """Search memories."""
        return await self.call_tool("search_memory", {
            "user_id": user_id,
            "query": query,
            "limit": limit
        })
    
    async def detect_language(self, text: str):
        """Detect text language."""
        return await self.call_tool("detect_language", {"text": text})
    
    async def create_user_session(self, metadata: Optional[Dict] = None):
        """Create new user session."""
        return await self.call_tool("create_user_session", {
            "metadata": metadata or {}
        })

async def test_multilingual_concurrent():
    """Test multilingual memory operations with concurrent requests."""
    async with MCPHTTPClient() as client:
        print("=" * 60)
        print("MCP HTTP SSE Client - Multilingual Concurrent Test")
        print("=" * 60)
        
        # Initialize connection
        print("\n[1] Initializing MCP connection...")
        init_result = await client.initialize()
        print(f"✓ Server: {init_result['serverInfo']['name']} v{init_result['serverInfo']['version']}")
        
        # List available tools
        print("\n[2] Listing available tools...")
        tools_result = await client.list_tools()
        print(f"✓ Available tools: {len(tools_result['tools'])}")
        for tool in tools_result['tools']:
            print(f"  - {tool['name']}")
        
        # Create user sessions concurrently
        print("\n[3] Creating user sessions concurrently...")
        tasks = [
            client.create_user_session({"name": "张三", "language": "zh"}),
            client.create_user_session({"name": "John", "language": "en"}),
            client.create_user_session({"name": "田中", "language": "ja"})
        ]
        users = await asyncio.gather(*tasks)
        print(f"✓ Created {len(users)} users concurrently:")
        for user in users:
            print(f"  - {user['user_id']} ({user['metadata'].get('name')})")
        
        # Add multilingual memories concurrently
        print("\n[4] Adding multilingual memories concurrently...")
        memory_tasks = [
            # Chinese user
            client.add_memory(
                users[0]['user_id'],
                [{"role": "user", "content": "我是一名高级Python工程师，有8年开发经验"}],
                language="zh"
            ),
            client.add_memory(
                users[0]['user_id'],
                [{"role": "user", "content": "我喜欢使用FastAPI和Docker进行开发"}],
                language="zh"
            ),
            # English user
            client.add_memory(
                users[1]['user_id'],
                [{"role": "user", "content": "I am a senior software engineer with 10 years experience"}],
                language="en"
            ),
            client.add_memory(
                users[1]['user_id'],
                [{"role": "user", "content": "I specialize in distributed systems and cloud architecture"}],
                language="en"
            ),
            # Japanese user
            client.add_memory(
                users[2]['user_id'],
                [{"role": "user", "content": "私はフルスタックエンジニアです"}],
                language="ja"
            ),
            client.add_memory(
                users[2]['user_id'],
                [{"role": "user", "content": "ReactとNode.jsが得意です"}],
                language="ja"
            )
        ]
        
        memory_results = await asyncio.gather(*memory_tasks, return_exceptions=True)
        successful = sum(1 for r in memory_results if not isinstance(r, Exception))
        print(f"✓ Added {successful}/{len(memory_tasks)} memories concurrently")
        
        # Language detection test
        print("\n[5] Testing language detection...")
        detect_tasks = [
            client.detect_language("我是中国人"),
            client.detect_language("Hello world"),
            client.detect_language("こんにちは"),
            client.detect_language("안녕하세요")
        ]
        
        detect_results = await asyncio.gather(*detect_tasks)
        for result in detect_results:
            print(f"  - {result['language_name']}: {result['confidence']:.1f}% confidence")
        
        # Search memories concurrently
        print("\n[6] Searching memories concurrently...")
        search_tasks = [
            client.search_memory(users[0]['user_id'], "开发经验", limit=3),
            client.search_memory(users[1]['user_id'], "experience", limit=3),
            client.search_memory(users[2]['user_id'], "エンジニア", limit=3)
        ]
        
        search_results = await asyncio.gather(*search_tasks)
        for i, result in enumerate(search_results):
            user_name = users[i]['metadata']['name']
            count = result.get('count', 0)
            print(f"  - {user_name}: Found {count} memories")
            results_list = result.get('results', [])
            if results_list and isinstance(results_list, list):
                for mem in results_list[:2]:
                    if isinstance(mem, dict):
                        print(f"    • {mem.get('memory', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✓ All concurrent tests completed successfully!")
        print("=" * 60)

async def test_health_check():
    """Test server health."""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8001/health") as response:
            health = await response.json()
            print("\n[Health Check]")
            print(f"Status: {health['status']}")
            print(f"Mem0 Initialized: {health['mem0_initialized']}")
            print(f"Active Connections: {health['active_connections']}")

if __name__ == "__main__":
    print("\n🚀 Starting MCP HTTP SSE Client Tests...\n")
    
    # Run health check
    asyncio.run(test_health_check())
    
    # Run main tests
    asyncio.run(test_multilingual_concurrent())
    
    print("\n✅ All tests completed!\n")
