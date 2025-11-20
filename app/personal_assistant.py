"""
大模型对话私人助理
集成MCP Server作为记忆模块，提供多轮对话、记忆管理和上下文理解能力
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests
from dataclasses import dataclass, asdict
import sys

# OpenAI SDK 用于调用大模型
try:
    from openai import AsyncOpenAI, OpenAI
except ImportError:
    print("请先安装 openai: pip install openai")
    sys.exit(1)

# ============= 配置 =============

# 大模型配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash-250414")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_API_KEY = os.getenv("ZHIPU_API_KEY", "your_zhipu_key")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# MCP Server 配置
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
MCP_TIMEOUT = 30

# ============= 数据模型 =============

@dataclass
class Message:
    """对话消息"""
    role: str  # user, assistant, system
    content: str
    timestamp: str = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

@dataclass
class ConversationContext:
    """对话上下文"""
    user_id: str
    conversation_id: str
    messages: List[Message] = None
    memories: List[Dict] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.memories is None:
            self.memories = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

# ============= MCP Server 客户端 =============

class MCPServerClient:
    """MCP Server 客户端"""
    
    def __init__(self, base_url: str = MCP_SERVER_URL, timeout: int = MCP_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    def _make_mcp_request(self, method: str, params: Dict = None) -> Dict:
        """发送MCP请求"""
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/mcp/messages",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ MCP Server 请求失败: {e}")
            raise
    
    def _call_tool(self, tool_name: str, **kwargs) -> Dict:
        """调用MCP工具"""
        return self._make_mcp_request("tools/call", {
            "name": tool_name,
            "arguments": kwargs
        })
    
    def add_memory(self, messages: List[Dict], user_id: str, metadata: Dict = None, language: str = None) -> Dict:
        """添加记忆"""
        params = {
            "messages": messages,
            "user_id": user_id,
        }
        if metadata:
            params["metadata"] = metadata
        if language:
            params["language"] = language
        
        response = self._call_tool("add_memory", **params)
        return self._extract_result(response)
    
    def search_memory(self, query: str, user_id: str, limit: int = 5) -> Dict:
        """搜索记忆"""
        response = self._call_tool("search_memory", query=query, user_id=user_id, limit=limit)
        return self._extract_result(response)
    
    def get_all_memories(self, user_id: str, limit: int = 100) -> Dict:
        """获取所有记忆"""
        response = self._call_tool("get_all_memories", user_id=user_id, limit=limit)
        return self._extract_result(response)
    
    def delete_memory(self, memory_id: str) -> Dict:
        """删除记忆"""
        response = self._call_tool("delete_memory", memory_id=memory_id)
        return self._extract_result(response)
    
    def delete_all_memories(self, user_id: str) -> Dict:
        """删除所有记忆"""
        response = self._call_tool("delete_all_memories", user_id=user_id)
        return self._extract_result(response)
    
    def create_user_session(self, metadata: Dict = None) -> Dict:
        """创建用户会话"""
        response = self._call_tool("create_user_session", metadata=metadata or {})
        return self._extract_result(response)
    
    def get_memory_stats(self, user_id: str) -> Dict:
        """获取记忆统计"""
        response = self._call_tool("get_memory_stats", user_id=user_id)
        return self._extract_result(response)
    
    def detect_language(self, text: str) -> Dict:
        """检测语言"""
        response = self._call_tool("detect_language", text=text)
        return self._extract_result(response)
    
    def search_memories_by_language(self, query: str, user_id: str, language: str = None, limit: int = 5) -> Dict:
        """按语言搜索记忆"""
        params = {"query": query, "user_id": user_id, "limit": limit}
        if language:
            params["language"] = language
        response = self._call_tool("search_memories_by_language", **params)
        return self._extract_result(response)
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def _extract_result(response: Dict) -> Dict:
        """提取结果"""
        if "error" in response:
            raise Exception(f"MCP Error: {response['error']['message']}")
        
        result = response.get("result", {})
        if isinstance(result, dict) and "content" in result:
            content = result["content"][0] if result["content"] else {}
            if isinstance(content, dict) and "text" in content:
                try:
                    return json.loads(content["text"])
                except:
                    return content
        return result

# ============= 个人助理 =============

class PersonalAssistant:
    """大模型个人助理"""
    
    SYSTEM_PROMPT = """你是一个智能个人助理，具有以下特点：
1. 友好、耐心、专业的对话风格
2. 能够记住用户的信息和偏好
3. 可以提供建议、解答问题、进行创意工作
4. 尊重用户隐私，遵守伦理准则
5. 当用户提到重要信息时，主动提出保存为记忆

你有以下能力：
- 通过记忆系统记住用户的个人信息、偏好、目标等
- 在对话中引用已保存的记忆，提供个性化服务
- 建议用户保存有用的信息

对话时的最佳实践：
- 自然地融合之前的记忆信息到对话中
- 主动识别新的重要信息并建议保存
- 提供有上下文感知的帮助和建议
"""
    
    def __init__(self, user_id: str = None, model: str = LLM_MODEL, api_key: str = LLM_API_KEY):
        """
        初始化助理
        
        Args:
            user_id: 用户ID，如果为None则自动生成
            model: 大模型名称
            api_key: API密钥
        """
        self.user_id = user_id or str(uuid.uuid4())
        self.model = model
        self.api_key = api_key
        
        # 初始化客户端 - 禁用代理和SSL验证以避免网络问题
        try:
            import httpx
            # 创建禁用代理的HTTP客户端
            http_client = httpx.Client(
                trust_env=False,  # 不使用环境变量中的代理设置
                verify=False,  # 跳过SSL验证（仅用于开发环境）
            )
            self.llm_client = OpenAI(
                api_key=api_key,
                base_url=LLM_BASE_URL,
                http_client=http_client
            )
        except Exception as e:
            print(f"⚠️  警告: 使用默认HTTP客户端 ({e})")
            try:
                self.llm_client = OpenAI(
                    api_key=api_key,
                    base_url=LLM_BASE_URL
                )
            except Exception as e2:
                print(f"⚠️  警告: OpenAI客户端初始化失败: {e2}")
                self.llm_client = None
        
        self.mcp_client = MCPServerClient()
        
        # 对话上下文
        self.context = ConversationContext(
            user_id=self.user_id,
            conversation_id=str(uuid.uuid4())
        )
        
        # 初始化系统消息
        self.system_message = Message(role="system", content=self.SYSTEM_PROMPT)
        
        if self.llm_client:
            print(f"✓ 个人助理已初始化")
            print(f"  用户ID: {self.user_id}")
            print(f"  大模型: {self.model}")
            print(f"  对话ID: {self.context.conversation_id}")
        else:
            print(f"⚠️  个人助理已初始化（演示模式）")
            print(f"  用户ID: {self.user_id}")
    
    def _check_mcp_availability(self) -> bool:
        """检查MCP Server是否可用"""
        if not self.mcp_client.health_check():
            print("⚠️  警告: MCP Server不可用，记忆功能将被禁用")
            return False
        return True
    
    def load_memories(self, limit: int = 10):
        """加载用户的记忆"""
        try:
            if not self._check_mcp_availability():
                return
            
            result = self.mcp_client.get_all_memories(self.user_id, limit=limit)
            
            # 提取记忆列表 - MCP Server 返回的是 {"memories": {"results": [...]}}
            memories_data = result.get("memories", {})
            if isinstance(memories_data, dict):
                memories = memories_data.get("results", [])
            else:
                memories = memories_data if isinstance(memories_data, list) else []
            
            self.context.memories = memories
            
            if memories:
                print(f"✓ 已加载 {len(memories)} 条记忆")
                return memories
            else:
                print("📝 暂无记忆")
                return []
        except Exception as e:
            print(f"⚠️  加载记忆失败: {e}")
            return []
    
    def _build_context_aware_prompt(self) -> str:
        """构建上下文感知的提示"""
        # 确保 memories 是列表
        memories = self.context.memories
        if not isinstance(memories, list):
            return ""
        
        if not memories:
            return ""
        
        prompt = "\n=== 用户记忆上下文 ===\n"
        for i, memory in enumerate(memories[:5], 1):
            if isinstance(memory, dict):
                memory_text = memory.get("memory", str(memory))
            else:
                memory_text = str(memory)
            
            # 限制每条记忆的长度
            if len(memory_text) > 200:
                memory_text = memory_text[:200] + "..."
            
            prompt += f"{i}. {memory_text}\n"
        
        prompt += "=== 请在回答时参考上述记忆 ===\n"
        return prompt
    
    def search_memories(self, query: str) -> List[Dict]:
        """搜索记忆"""
        try:
            if not self._check_mcp_availability():
                return []
            
            result = self.mcp_client.search_memory(query, self.user_id, limit=5)
            memories = result.get("results", [])
            
            if memories:
                print(f"✓ 找到 {len(memories)} 条相关记忆")
                return memories
            else:
                print("📝 未找到相关记忆")
                return []
        except Exception as e:
            print(f"⚠️  搜索记忆失败: {e}")
            return []
    
    def save_memory(self, user_message: str, assistant_response: str) -> bool:
        """保存对话到记忆"""
        try:
            if not self._check_mcp_availability():
                return False
            
            messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_response}
            ]
            
            metadata = {
                "conversation_id": self.context.conversation_id,
                "type": "conversation",
                "timestamp": datetime.now().isoformat()
            }
            
            result = self.mcp_client.add_memory(
                messages=messages,
                user_id=self.user_id,
                metadata=metadata
            )
            
            print(f"✓ 记忆已保存")
            return True
        except Exception as e:
            print(f"⚠️  保存记忆失败: {e}")
            return False
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计"""
        try:
            if not self._check_mcp_availability():
                return {}
            
            return self.mcp_client.get_memory_stats(self.user_id)
        except Exception as e:
            print(f"⚠️  获取统计失败: {e}")
            return {}
    
    def chat(self, user_input: str, save_memory: bool = False) -> str:
        """
        进行一次对话
        
        Args:
            user_input: 用户输入
            save_memory: 是否保存到记忆
        
        Returns:
            助理的响应
        """
        # 添加用户消息到上下文
        user_message = Message(role="user", content=user_input)
        self.context.messages.append(user_message)
        
        # 如果没有LLM客户端，返回演示响应
        if not self.llm_client:
            demo_response = f"""🤖 演示模式

您说: {user_input}

这是一个演示响应。要启用真实对话，请设置ZHIPU_API_KEY环境变量。"""
            
            # 添加到上下文
            assistant_message = Message(role="assistant", content=demo_response)
            self.context.messages.append(assistant_message)
            return demo_response
        
        # 构建消息列表用于API调用
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
        ]
        
        # 添加记忆上下文
        context_prompt = self._build_context_aware_prompt()
        if context_prompt:
            messages.append({
                "role": "system",
                "content": context_prompt
            })
        
        # 添加对话历史
        for msg in self.context.messages[-10:]:  # 保持最近10条消息
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        try:
            # 调用大模型
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=2000
            )
            
            assistant_response = response.choices[0].message.content or "无法生成响应"
            
            # 添加助理消息到上下文
            assistant_message = Message(role="assistant", content=assistant_response)
            self.context.messages.append(assistant_message)
            
            # 根据需要保存记忆
            if save_memory:
                self.save_memory(user_input, assistant_response)
            
            return assistant_response
        
        except Exception as e:
            error_msg = f"❌ 对话失败: {e}"
            print(error_msg)
            return error_msg
    
    def interactive_mode(self):
        """进入交互模式"""
        print("\n" + "="*60)
        print("🤖 个人助理交互模式")
        print("="*60)
        print("命令列表:")
        print("  /help      - 显示帮助信息")
        print("  /memories  - 显示所有记忆")
        print("  /search    - 搜索记忆")
        print("  /stats     - 显示记忆统计")
        print("  /save      - 下次对话时保存到记忆")
        print("  /clear     - 清空当前对话")
        print("  /exit      - 退出")
        print("="*60 + "\n")
        
        # 加载初始记忆
        self.load_memories()
        
        auto_save = False
        
        while True:
            try:
                user_input = input("\n👤 你: ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith("/"):
                    self._handle_command(user_input, auto_save)
                    if user_input == "/save":
                        auto_save = not auto_save
                        print(f"💾 自动保存: {'开启' if auto_save else '关闭'}")
                    elif user_input == "/clear":
                        self.context.messages.clear()
                        print("✓ 已清空对话历史")
                    elif user_input == "/exit":
                        print("\n👋 再见!")
                        break
                    continue
                
                # 进行对话
                print("\n🤖 助理: ", end="", flush=True)
                response = self.chat(user_input, save_memory=auto_save)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 再见!")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
    
    def _handle_command(self, command: str, auto_save: bool):
        """处理命令"""
        if command == "/help":
            print("""
可用命令:
  /help      - 显示此帮助信息
  /memories  - 列出所有记忆
  /search    - 搜索记忆 (输入: /search <查询>)
  /stats     - 显示记忆统计
  /save      - 切换自动保存模式
  /clear     - 清空当前对话历史
  /exit      - 退出助理
            """)
        
        elif command == "/memories":
            memories = self.load_memories()
            if memories:
                print("\n📚 您的记忆:")
                for i, mem in enumerate(memories[:10], 1):
                    mem_text = mem.get("memory", str(mem)) if isinstance(mem, dict) else str(mem)
                    if len(mem_text) > 100:
                        mem_text = mem_text[:100] + "..."
                    print(f"  {i}. {mem_text}")
        
        elif command.startswith("/search"):
            query = command.replace("/search", "").strip()
            if query:
                memories = self.search_memories(query)
                if memories:
                    print("\n🔍 搜索结果:")
                    for i, mem in enumerate(memories[:5], 1):
                        mem_text = mem.get("memory", str(mem)) if isinstance(mem, dict) else str(mem)
                        if len(mem_text) > 100:
                            mem_text = mem_text[:100] + "..."
                        print(f"  {i}. {mem_text}")
            else:
                print("请输入搜索关键词: /search <关键词>")
        
        elif command == "/stats":
            stats = self.get_memory_stats()
            if stats:
                print(f"\n📊 记忆统计:")
                print(f"  总数: {stats.get('total_memories', 0)}")
                print(f"  更新时间: {stats.get('timestamp', '未知')}")
        
        elif command == "/clear":
            pass  # 在主循环中处理
        
        elif command == "/exit":
            pass  # 在主循环中处理
        
        else:
            print(f"❌ 未知命令: {command}")

# ============= 主程序 =============

async def main_async():
    """异步主程序"""
    assistant = PersonalAssistant()
    
    # 测试对话
    print("\n" + "="*60)
    print("测试对话模式")
    print("="*60)
    
    # 加载记忆
    assistant.load_memories()
    
    # 进行几个测试对话
    test_inputs = [
        "你好，我叫张三，我是一名软件工程师",
        "我的工作主要涉及Python和前端开发",
        "我最近在学习大模型相关的技术"
    ]
    
    for user_input in test_inputs:
        print(f"\n👤 用户: {user_input}")
        response = assistant.chat(user_input, save_memory=True)
        print(f"🤖 助理: {response}")
        await asyncio.sleep(1)

def main():
    """主程序"""
    # 检查环境变量
    if not os.getenv("ZHIPU_API_KEY"):
        print("⚠️  请设置 ZHIPU_API_KEY 环境变量")
        return
    
    print("🚀 启动个人助理...")
    print(f"   MCP Server: {MCP_SERVER_URL}")
    print(f"   大模型: {LLM_MODEL}")
    print()
    
    # 创建助理实例
    assistant = PersonalAssistant()
    
    # 进入交互模式
    assistant.interactive_mode()

if __name__ == "__main__":
    main()
