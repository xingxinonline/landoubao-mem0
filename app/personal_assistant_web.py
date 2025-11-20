"""
Web版个人助理 (FastAPI + Server-Sent Events)
提供HTTP API接口供Web前端调用
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel

from app.personal_assistant import PersonalAssistant, MCPServerClient

# ============= 数据模型 =============

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    user_id: Optional[str] = None
    save_memory: bool = False

class ChatResponse(BaseModel):
    """聊天响应"""
    response: str
    user_id: str
    timestamp: str
    saved_to_memory: bool

class MemoryRequest(BaseModel):
    """记忆请求"""
    user_id: str
    query: Optional[str] = None
    limit: int = 10

class UserSession(BaseModel):
    """用户会话"""
    user_id: str
    created_at: str
    assistant: Optional[Any] = None

# ============= 全局状态 =============

# 存储用户的助理实例
user_assistants: Dict[str, PersonalAssistant] = {}

# 存储活跃的SSE连接
active_connections: Dict[str, asyncio.Queue] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    print("✓ Web助理服务启动")
    yield
    print("✓ Web助理服务关闭")
    user_assistants.clear()

# ============= FastAPI应用 =============

app = FastAPI(
    title="个人助理Web API",
    description="大模型对话私人助理HTTP接口",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= 辅助函数 =============

def get_or_create_assistant(user_id: Optional[str] = None) -> tuple[PersonalAssistant, str]:
    """获取或创建用户的助理实例"""
    if user_id is None:
        user_id = str(uuid.uuid4())
    
    if user_id not in user_assistants:
        try:
            # 从环境变量读取API密钥
            api_key = os.getenv("ZHIPU_API_KEY", "").strip()
            
            # 创建助理实例（API密钥会在PersonalAssistant初始化时使用）
            assistant = PersonalAssistant(user_id=user_id, api_key=api_key if api_key else "dummy_key")
            user_assistants[user_id] = assistant
            print(f"✓ 为用户 {user_id[:8]}... 创建新的助理实例")
        except Exception as e:
            print(f"❌ 创建助理失败: {e}")
            raise
    
    return user_assistants[user_id], user_id

# ============= API端点 =============

@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "个人助理Web API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "POST /api/chat",
            "memories": "GET /api/memories",
            "search": "GET /api/search",
            "stats": "GET /api/stats",
            "session": "POST /api/session",
            "health": "GET /health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    mcp_client = MCPServerClient()
    mcp_available = mcp_client.health_check()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_server": "available" if mcp_available else "unavailable",
        "active_sessions": len(user_assistants)
    }

@app.post("/api/session")
async def create_session(metadata: Optional[Dict] = None) -> UserSession:
    """创建新的用户会话"""
    try:
        user_id = str(uuid.uuid4())
        assistant, _ = get_or_create_assistant(user_id)
        
        # 加载记忆
        assistant.load_memories(limit=5)
        
        return UserSession(
            user_id=user_id,
            created_at=datetime.now().isoformat(),
            assistant=None  # 不返回助理对象本身
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """进行对话"""
    try:
        # 检查环境变量中的API密钥
        api_key = os.getenv("ZHIPU_API_KEY", "").strip()
        
        if not api_key:
            # 没有API密钥，返回演示响应
            demo_response = """🤖 演示模式（未设置API密钥）

要启用真实对话功能，请在启动前设置环境变量：

Windows PowerShell:
  $env:ZHIPU_API_KEY = "your_zhipu_api_key"
  
然后重启Web服务器。

或者设置到系统环境变量中。

获取API密钥: https://open.bigmodel.cn"""
            
            return ChatResponse(
                response=demo_response,
                user_id=request.user_id or str(uuid.uuid4()),
                timestamp=datetime.now().isoformat(),
                saved_to_memory=False
            )
        
        assistant, user_id = get_or_create_assistant(request.user_id)
        
        # 进行对话
        response = assistant.chat(request.message, save_memory=request.save_memory)
        
        return ChatResponse(
            response=response,
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            saved_to_memory=request.save_memory
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat-stream")
async def chat_stream(request: ChatRequest):
    """流式对话 (SSE)"""
    
    async def event_generator():
        try:
            assistant, user_id = get_or_create_assistant(request.user_id)
            
            # 使用OpenAI stream
            stream = assistant.llm_client.chat.completions.create(
                model=assistant.model,
                messages=[
                    {"role": "system", "content": assistant.SYSTEM_PROMPT},
                    {"role": "user", "content": request.message}
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    yield f"data: {json.dumps({'chunk': content, 'user_id': user_id})}\n\n"
            
            # 保存完整对话到记忆
            if request.save_memory:
                assistant.save_memory(request.message, full_response)
            
            # 发送完成信号
            yield f"data: {json.dumps({'done': True, 'full_response': full_response})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/memories")
async def get_memories(user_id: str, limit: int = 10) -> Dict:
    """获取用户记忆"""
    try:
        assistant, _ = get_or_create_assistant(user_id)
        
        memories = assistant.load_memories(limit=limit)
        
        return {
            "user_id": user_id,
            "memories": memories,
            "count": len(memories),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search_memories(user_id: str, query: str, limit: int = 5) -> Dict:
    """搜索记忆"""
    try:
        assistant, _ = get_or_create_assistant(user_id)
        
        results = assistant.search_memories(query)
        
        return {
            "user_id": user_id,
            "query": query,
            "results": results[:limit],
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(user_id: str) -> Dict:
    """获取统计信息"""
    try:
        assistant, _ = get_or_create_assistant(user_id)
        
        stats = assistant.get_memory_stats()
        
        return {
            "user_id": user_id,
            "stats": stats,
            "session_messages": len(assistant.context.messages),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memories")
async def delete_all_memories(user_id: str) -> Dict:
    """删除用户所有记忆"""
    try:
        assistant, _ = get_or_create_assistant(user_id)
        
        assistant.mcp_client.delete_all_memories(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "message": "所有记忆已删除",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memories/save")
async def save_conversation(
    user_id: str,
    user_message: str,
    assistant_message: str
) -> Dict:
    """保存对话到记忆"""
    try:
        assistant, _ = get_or_create_assistant(user_id)
        
        success = assistant.save_memory(user_message, assistant_message)
        
        return {
            "success": success,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def list_sessions() -> Dict:
    """列出所有活跃会话"""
    return {
        "total_sessions": len(user_assistants),
        "sessions": [
            {
                "user_id": uid,
                "created_at": assistant.context.created_at,
                "message_count": len(assistant.context.messages),
                "memory_count": len(assistant.context.memories)
            }
            for uid, assistant in user_assistants.items()
        ],
        "timestamp": datetime.now().isoformat()
    }

# ============= 静态文件 =============

@app.get("/")
async def root_redirect():
    """重定向到Web界面"""
    return FileResponse(
        Path(__file__).parent.parent / "static" / "index.html",
        media_type="text/html"
    )

# 挂载静态文件目录
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ============= 主程序 =============

if __name__ == "__main__":
    # 检查环境
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("⚠️  警告: 未设置 ZHIPU_API_KEY")
    
    # 启动服务器
    print("🚀 启动Web版个人助理...")
    print(f"   API文档: http://localhost:8002/docs")
    print(f"   OpenAPI: http://localhost:8002/openapi.json")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
