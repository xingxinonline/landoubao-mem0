"""
MCP Server for Mem0 Memory Management - HTTP SSE Transport
Provides memory operations through Model Context Protocol with remote access support
Supports async/concurrent operations
"""

import asyncio
import json
import os
import re
import uuid
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Mem0 imports
from mem0 import Memory

# ============= Language Detection & Multilingual Support =============

LANGUAGE_PATTERNS = {
    "zh": re.compile(r"[\u4e00-\u9fff]"),  # Chinese
    "en": re.compile(r"[a-zA-Z]"),  # English
    "ja": re.compile(r"[\u3040-\u309f\u30a0-\u30ff]"),  # Japanese
    "ko": re.compile(r"[\uac00-\ud7af]"),  # Korean
    "ar": re.compile(r"[\u0600-\u06ff]"),  # Arabic
    "ru": re.compile(r"[\u0400-\u04ff]"),  # Russian
    "th": re.compile(r"[\u0e00-\u0e7f]")   # Thai
}

LANGUAGE_PROMPTS = {
    "zh": """你是一个事实提取助手。请从以下中文内容中提取关键事实。
重要：所有事实必须用中文写出！
- 提取具体的、可验证的事实
- 每个事实应该是简洁的中文陈述
- 使用现在时或一般时
- 避免冗余和重复

例如，如果输入是"我叫李四，是个高级工程师"，应提取为：
- 名字是李四
- 职位是高级工程师""",
    
    "en": """You are a fact extraction assistant. Please extract key facts from the following English content.
Important: All facts must be written in English!
- Extract specific, verifiable facts
- Each fact should be a concise English statement
- Use present tense or general time
- Avoid redundancy and repetition

For example, if the input is "My name is John Smith, I am a senior engineer", extract as:
- Name is John Smith
- Position is senior engineer""",
    
    "ja": """あなたは事実抽出アシスタントです。以下の日本語コンテンツから主要な事実を抽出してください。
重要：すべての事実は日本語で記述する必要があります！
- 具体的で検証可能な事実を抽出
- 各事実は簡潔な日本語の陳述
- 現在時制または一般時を使用
- 冗長性と繰り返しを避ける""",
    
    "ko": """당신은 사실 추출 보조자입니다. 다음 한국어 콘텐츠에서 핵심 사실을 추출해주세요.
중요: 모든 사실은 한국어로 작성되어야 합니다!
- 구체적이고 검증 가능한 사실 추출
- 각 사실은 간결한 한국어 진술
- 현재형 또는 일반형 시제 사용
- 중복성과 반복 피하기""",
    
    "ar": """أنت مساعد استخراج الحقائق. يرجى استخراج الحقائق الرئيسية من المحتوى العربي التالي.
مهم: يجب كتابة جميع الحقائق باللغة العربية!
- استخراج الحقائق المحددة والمميزة
- يجب أن تكون كل حقيقة بيان موجز باللغة العربية
- استخدم الزمن الحاضر أو الزمن العام
- تجنب الحشو والتكرار""",
    
    "ru": """Вы ассистент по извлечению фактов. Пожалуйста, извлеките ключевые факты из следующего русского контента.
Важно: Все факты должны быть написаны на русском языке!
- Извлекайте конкретные, проверяемые факты
- Каждый факт должен быть кратким утверждением на русском языке
- Используйте настоящее время или общее время
- Избегайте избыточности и повторений""",
    
    "th": """คุณเป็นผู้ช่วยในการสกัดข้อเท็จจริง โปรดสกัดข้อเท็จจริงหลักจากเนื้อหาภาษาไทยต่อไปนี้
สำคัญ: ข้อเท็จจริงทั้งหมดต้องเขียนเป็นภาษาไทย!
- สกัดข้อเท็จจริงที่เฉพาะและสามารถตรวจสอบได้
- ข้อเท็จจริงแต่ละข้อควรเป็นข้อความภาษาไทยที่สั้น
- ใช้เวลาปัจจุบันหรือเวลาทั่วไป
- หลีกเลี่ยงความซ้ำซ้อนและการซ้ำ"""
}

def detect_language(text: str) -> str:
    """Detect language from text using Unicode character ranges."""
    if not text:
        return "en"
    
    lang_scores = {}
    for lang, pattern in LANGUAGE_PATTERNS.items():
        matches = len(pattern.findall(text))
        if matches > 0:
            lang_scores[lang] = matches
    
    if lang_scores:
        return max(lang_scores.items(), key=lambda x: x[1])[0]
    return "en"

def get_system_prompt(language: str) -> str:
    """Get language-specific system prompt for fact extraction."""
    return LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS["en"])

# ============= Configuration =============
QDRANT_HOST = os.getenv("QDRANT_HOST", "115.190.24.157")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash-250414")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen3-Embedding-0.6B")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1024"))
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://ai.gitee.com/v1")

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "your_zhipu_key")
MODELARK_API_KEY = os.getenv("MODELARK_API_KEY", "your_modelark_key")

# Build Mem0 configuration
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": QDRANT_HOST,
            "port": QDRANT_PORT,
            "embedding_model_dims": EMBEDDING_DIMS
        }
    },
    "llm": {
        "provider": LLM_PROVIDER,
        "config": {
            "model": LLM_MODEL,
            "api_key": ZHIPU_API_KEY,
            "openai_base_url": LLM_BASE_URL,
            "temperature": LLM_TEMPERATURE,
            "max_tokens": LLM_MAX_TOKENS
        }
    },
    "embedder": {
        "provider": EMBEDDING_PROVIDER,
        "config": {
            "model": EMBEDDING_MODEL,
            "api_key": MODELARK_API_KEY,
            "openai_base_url": EMBEDDING_BASE_URL,
            "embedding_dims": EMBEDDING_DIMS
        }
    }
}

# Initialize Mem0
m = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global m
    try:
        m = Memory.from_config(config)
        print("✓ Mem0 initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing Mem0: {e}")
    yield
    # Cleanup if needed
    print("Shutting down MCP server...")

# Initialize FastAPI app
app = FastAPI(
    title="Mem0 MCP Server",
    description="Model Context Protocol Server for Mem0 Memory Management with HTTP SSE Transport",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for remote access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Connection Management =============
# Store active SSE connections
active_connections: Dict[str, asyncio.Queue] = {}

# ============= MCP Error Codes =============
class MCPErrorCode:
    """MCP Standard Error Codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # Custom error codes (> -32000)
    MEMORY_ERROR = -32001
    LANGUAGE_ERROR = -32002
    INITIALIZATION_ERROR = -32003

# ============= MCP Protocol Handlers =============

def create_error_response(request_id: Optional[str], code: int, message: str, data: Any = None) -> Dict:
    """Create MCP error response."""
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    }
    if data is not None:
        response["error"]["data"] = data
    return response

def create_success_response(request_id: Optional[str], result: Any) -> Dict:
    """Create MCP success response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }

def create_notification(method: str, params: Any = None) -> Dict:
    """Create MCP notification (no response expected)."""
    notification = {
        "jsonrpc": "2.0",
        "method": method
    }
    if params is not None:
        notification["params"] = params
    return notification

async def handle_initialize(params: Dict) -> Dict:
    """Handle MCP initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {
                "listChanged": True
            },
            "resources": {},
            "prompts": {}
        },
        "serverInfo": {
            "name": "mem0-mcp-server",
            "version": "1.0.0"
        }
    }

async def handle_tools_list() -> Dict:
    """List available MCP tools."""
    return {
        "tools": [
            {
                "name": "add_memory",
                "description": "Add a new memory from conversation messages with automatic multilingual support. Extracts facts in the detected language.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "description": "Array of conversation messages to store as memory",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                                    "content": {"type": "string"}
                                },
                                "required": ["role", "content"]
                            }
                        },
                        "user_id": {"type": "string", "description": "Unique identifier for the user"},
                        "language": {
                            "type": "string",
                            "description": "Language code (zh/en/ja/ko/ar/ru/th). If not provided, auto-detect from content.",
                            "enum": ["zh", "en", "ja", "ko", "ar", "ru", "th"]
                        },
                        "metadata": {"type": "object", "description": "Additional metadata", "additionalProperties": True}
                    },
                    "required": ["messages", "user_id"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search for relevant memories based on a query.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "user_id": {"type": "string", "description": "User ID"},
                        "limit": {"type": "integer", "description": "Max results", "default": 5}
                    },
                    "required": ["query", "user_id"]
                }
            },
            {
                "name": "get_all_memories",
                "description": "Get all memories for a specific user.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"},
                        "limit": {"type": "integer", "description": "Max memories", "default": 100}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "delete_memory",
                "description": "Delete a specific memory by its ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_id": {"type": "string", "description": "Memory ID"}
                    },
                    "required": ["memory_id"]
                }
            },
            {
                "name": "delete_all_memories",
                "description": "Delete all memories for a user.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "create_user_session",
                "description": "Create a new user session with UUID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "metadata": {"type": "object", "description": "User metadata", "additionalProperties": True}
                    }
                }
            },
            {
                "name": "get_memory_stats",
                "description": "Get statistics about user memories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User ID"}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "detect_language",
                "description": "Detect language of text.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to detect"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "search_memories_by_language",
                "description": "Search memories filtered by language.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "user_id": {"type": "string", "description": "User ID"},
                        "language": {"type": "string", "enum": ["zh", "en", "ja", "ko", "ar", "ru", "th"]},
                        "limit": {"type": "integer", "default": 5}
                    },
                    "required": ["query", "user_id"]
                }
            }
        ]
    }

async def handle_tools_call(name: str, arguments: Dict) -> Dict:
    """Handle MCP tool call - async with concurrent support."""
    if m is None:
        raise Exception("Mem0 not initialized")
    
    # Run tool operations concurrently using asyncio
    if name == "add_memory":
        messages = arguments.get("messages", [])
        user_id = arguments.get("user_id")
        metadata = arguments.get("metadata", {})
        language = arguments.get("language")
        
        # Detect language if not provided
        if not language:
            for msg in messages:
                if msg.get("role") == "user":
                    language = detect_language(msg.get("content", ""))
                    break
            if not language:
                language = "en"
        
        # Add language-specific system prompt
        system_prompt = get_system_prompt(language)
        enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
        
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["language"] = language
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: m.add(messages=enhanced_messages, user_id=user_id, metadata=metadata)
        )
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "result": result,
                    "language": language,
                    "message": f"Memory added successfully in {language}"
                }, indent=2)
            }]
        }
    
    elif name == "search_memory":
        query = arguments.get("query")
        user_id = arguments.get("user_id")
        limit = arguments.get("limit", 5)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: m.search(query=query, user_id=user_id, limit=limit)
        )
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "results": result,
                    "count": len(result) if isinstance(result, list) else 0
                }, indent=2)
            }]
        }
    
    elif name == "get_all_memories":
        user_id = arguments.get("user_id")
        limit = arguments.get("limit", 100)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: m.get_all(user_id=user_id, limit=limit)
        )
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "memories": result,
                    "total": len(result) if isinstance(result, list) else 0
                }, indent=2)
            }]
        }
    
    elif name == "delete_memory":
        memory_id = arguments.get("memory_id")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: m.delete(memory_id))
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": f"Memory {memory_id} deleted successfully"
                }, indent=2)
            }]
        }
    
    elif name == "delete_all_memories":
        user_id = arguments.get("user_id")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: m.reset(user_id=user_id))
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "message": f"All memories for user {user_id} deleted"
                }, indent=2)
            }]
        }
    
    elif name == "create_user_session":
        user_id = str(uuid.uuid4())
        metadata = arguments.get("metadata", {})
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                    "metadata": metadata
                }, indent=2)
            }]
        }
    
    elif name == "get_memory_stats":
        user_id = arguments.get("user_id")
        
        loop = asyncio.get_event_loop()
        all_memories = await loop.run_in_executor(
            None,
            lambda: m.get_all(user_id=user_id)
        )
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "total_memories": len(all_memories) if isinstance(all_memories, list) else 0,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            }]
        }
    
    elif name == "detect_language":
        text = arguments.get("text", "")
        language = detect_language(text)
        
        pattern = LANGUAGE_PATTERNS.get(language)
        if pattern:
            matches = len(pattern.findall(text))
            confidence = min(100, (matches / max(1, len(text))) * 100)
        else:
            confidence = 0
        
        lang_name = {
            "zh": "Chinese (中文)", "en": "English", "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)", "ar": "Arabic (العربية)", 
            "ru": "Russian (Русский)", "th": "Thai (ไทย)"
        }.get(language, "Unknown")
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "language_code": language,
                    "language_name": lang_name,
                    "confidence": round(confidence, 2),
                    "text_sample": text[:100]
                }, indent=2)
            }]
        }
    
    elif name == "search_memories_by_language":
        query = arguments.get("query")
        user_id = arguments.get("user_id")
        language = arguments.get("language")
        limit = arguments.get("limit", 5)
        
        loop = asyncio.get_event_loop()
        all_results = await loop.run_in_executor(
            None,
            lambda: m.search(query=query, user_id=user_id, limit=limit * 2)
        )
        
        if language:
            filtered_results = []
            for item in (all_results if isinstance(all_results, list) else []):
                meta = item.get("metadata", {}) if isinstance(item, dict) else {}
                if meta.get("language") == language:
                    filtered_results.append(item)
                if len(filtered_results) >= limit:
                    break
            results = filtered_results
        else:
            results = all_results[:limit] if isinstance(all_results, list) else []
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "query": query,
                    "language_filter": language,
                    "results": results,
                    "count": len(results)
                }, indent=2)
            }]
        }
    
    else:
        raise Exception(f"Unknown tool: {name}")

async def process_request(request_data: Dict) -> Dict:
    """Process incoming MCP request."""
    try:
        # Validate JSON-RPC 2.0 format
        if request_data.get("jsonrpc") != "2.0":
            return create_error_response(
                request_data.get("id"),
                MCPErrorCode.INVALID_REQUEST,
                "Invalid JSON-RPC version"
            )
        
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        # Handle different MCP methods
        if method == "initialize":
            result = await handle_initialize(params)
            return create_success_response(request_id, result)
        
        elif method == "tools/list":
            result = await handle_tools_list()
            return create_success_response(request_id, result)
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_arguments = params.get("arguments", {})
            result = await handle_tools_call(tool_name, tool_arguments)
            return create_success_response(request_id, result)
        
        else:
            return create_error_response(
                request_id,
                MCPErrorCode.METHOD_NOT_FOUND,
                f"Method not found: {method}"
            )
    
    except Exception as e:
        return create_error_response(
            request_data.get("id"),
            MCPErrorCode.INTERNAL_ERROR,
            str(e),
            {"traceback": str(type(e).__name__)}
        )

# ============= HTTP Endpoints =============

@app.get("/")
async def root():
    """Root endpoint with server info."""
    return {
        "name": "Mem0 MCP Server",
        "version": "1.0.0",
        "protocol": "MCP over HTTP SSE",
        "transport": "sse",
        "capabilities": ["tools"],
        "status": "running"
    }

@app.post("/mcp/messages")
async def handle_message(request: Request):
    """Handle client-to-server messages via HTTP POST."""
    try:
        request_data = await request.json()
        response = await process_request(request_data)
        return JSONResponse(content=response)
    except json.JSONDecodeError:
        return JSONResponse(
            content=create_error_response(None, MCPErrorCode.PARSE_ERROR, "Invalid JSON"),
            status_code=400
        )
    except Exception as e:
        return JSONResponse(
            content=create_error_response(None, MCPErrorCode.INTERNAL_ERROR, str(e)),
            status_code=500
        )

@app.get("/mcp/sse")
async def handle_sse(request: Request):
    """Handle server-to-client messages via Server-Sent Events."""
    connection_id = str(uuid.uuid4())
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for the client."""
        queue: asyncio.Queue = asyncio.Queue()
        active_connections[connection_id] = queue
        
        try:
            # Send connection established event
            yield f"data: {json.dumps(create_notification('connection/established', {'connectionId': connection_id}))}\n\n"
            
            # Keep connection alive and send queued messages
            while True:
                try:
                    # Wait for messages with timeout for keep-alive
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    yield f": keep-alive\n\n"
                except Exception as e:
                    print(f"Error in SSE stream: {e}")
                    break
        finally:
            # Clean up connection
            if connection_id in active_connections:
                del active_connections[connection_id]
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mem0_initialized": m is not None,
        "active_connections": len(active_connections),
        "timestamp": datetime.now().isoformat()
    }

# ============= Main Entry Point =============

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True
    )
