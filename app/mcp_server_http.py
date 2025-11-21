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
import time
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

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
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "mem0")

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

# Concurrency settings
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "20"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
THREAD_POOL_SIZE = int(os.getenv("THREAD_POOL_SIZE", "10"))

# Build Mem0 configuration
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": QDRANT_COLLECTION_NAME,
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
# Thread pool for blocking operations
executor = None
# Semaphore for concurrent request limiting
request_semaphore = None
# Request metrics
request_metrics = {
    "total_requests": 0,
    "active_requests": 0,
    "failed_requests": 0,
    "avg_response_time": 0.0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application."""
    global m, executor, request_semaphore
    
    # Initialize thread pool
    executor = ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE)
    print(f"✓ Thread pool initialized with {THREAD_POOL_SIZE} workers")
    
    # Initialize request semaphore for concurrency control
    request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    print(f"✓ Concurrent request limit set to {MAX_CONCURRENT_REQUESTS}")
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to initialize Mem0...")
            print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
            m = Memory.from_config(config)
            print("✓ Mem0 initialized successfully")
            break
        except Exception as e:
            print(f"✗ Error initializing Mem0 (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("Failed to initialize Mem0 after all retries")
    yield
    # Cleanup
    print("Shutting down MCP server...")
    if executor:
        executor.shutdown(wait=True)
        print("✓ Thread pool shut down")

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
                "description": "Add new memories from conversation messages. Automatically detects language and stores memories in their original language. The LLM should provide conversation messages that need to be remembered.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "description": "Array of conversation messages to extract and store as memories. The system will automatically detect the language and extract facts in that language.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                                    "content": {"type": "string"}
                                },
                                "required": ["role", "content"]
                            }
                        },
                        "user_id": {"type": "string", "description": "REQUIRED. Unique identifier for the user. Must be a top-level parameter, NOT inside metadata."},
                        "metadata": {"type": "object", "description": "Optional additional metadata", "additionalProperties": True}
                    },
                    "required": ["messages", "user_id"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search for relevant memories based on a query. Returns memories in any language that match the semantic meaning of the query. The LLM should interpret and summarize the results for the user.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query in any language"},
                        "user_id": {"type": "string", "description": "User ID whose memories to search"},
                        "limit": {"type": "integer", "description": "Maximum number of results to return", "default": 10}
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
    
    loop = asyncio.get_event_loop()
    start_time = time.time()
    
    # Run tool operations concurrently using asyncio
    if name == "add_memory":
        messages = arguments.get("messages", [])
        user_id = arguments.get("user_id")
        metadata = arguments.get("metadata", {})
        
        # Fallback: check if user_id is in metadata
        if not user_id and isinstance(metadata, dict) and "user_id" in metadata:
            user_id = metadata.pop("user_id")
            print(f"Recovered user_id from metadata: {user_id}")
        
        # Auto-detect language from messages
        language = "en"
        for msg in messages:
            if msg.get("role") == "user":
                detected = detect_language(msg.get("content", ""))
                if detected:
                    language = detected
                    break
        
        # Add language-specific system prompt for fact extraction
        system_prompt = get_system_prompt(language)
        enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Add metadata
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["language"] = language
        
        # Run in thread pool to avoid blocking, with timeout
        result = await asyncio.wait_for(
            loop.run_in_executor(
                executor,
                lambda: m.add(messages=enhanced_messages, user_id=user_id, metadata=metadata)
            ),
            timeout=REQUEST_TIMEOUT
        )
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "result": result,
                    "message": "Memory added successfully"
                }, indent=2, ensure_ascii=False)
            }]
        }
    
    elif name == "search_memory":
        query = arguments.get("query")
        user_id = arguments.get("user_id")
        limit = arguments.get("limit", 10)
        
        result = await asyncio.wait_for(
            loop.run_in_executor(
                executor,
                lambda: m.search(query=query, user_id=user_id, limit=limit)
            ),
            timeout=REQUEST_TIMEOUT
        )
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "results": result,
                    "count": len(result) if isinstance(result, list) else 0
                }, indent=2, ensure_ascii=False)
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
    start_time = time.time()
    
    # Acquire semaphore for concurrent request limiting
    async with request_semaphore:
        request_metrics["total_requests"] += 1
        request_metrics["active_requests"] += 1
        
        try:
            request_data = await request.json()
            response = await process_request(request_data)
            
            # Update metrics
            elapsed = time.time() - start_time
            request_metrics["avg_response_time"] = (
                request_metrics["avg_response_time"] * 0.95 + elapsed * 0.05
            )
            
            return JSONResponse(content=response)
        except json.JSONDecodeError:
            request_metrics["failed_requests"] += 1
            return JSONResponse(
                content=create_error_response(None, MCPErrorCode.PARSE_ERROR, "Invalid JSON"),
                status_code=400
            )
        except Exception as e:
            request_metrics["failed_requests"] += 1
            return JSONResponse(
                content=create_error_response(None, MCPErrorCode.INTERNAL_ERROR, str(e)),
                status_code=500
            )
        finally:
            request_metrics["active_requests"] -= 1

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
        "concurrency": {
            "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
            "active_requests": request_metrics["active_requests"],
            "thread_pool_size": THREAD_POOL_SIZE,
            "request_timeout": REQUEST_TIMEOUT
        },
        "metrics": {
            "total_requests": request_metrics["total_requests"],
            "failed_requests": request_metrics["failed_requests"],
            "avg_response_time_ms": round(request_metrics["avg_response_time"] * 1000, 2),
            "success_rate": round(
                (1 - request_metrics["failed_requests"] / max(request_metrics["total_requests"], 1)) * 100,
                2
            )
        },
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
