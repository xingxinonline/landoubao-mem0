import os
import re
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from mem0 import Memory

# Initialize FastAPI app
app = FastAPI(title="Mem0 API Server", description="Custom Mem0 Deployment with Zhipu AI and ModelArk")

# ============= Configuration with environment variable support =============

# Vector Store Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "115.190.24.157")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# LLM Configuration (Zhipu AI)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash-250414")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# Embedding Configuration (ModelArk)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen3-Embedding-0.6B")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1024"))
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://ai.gitee.com/v1")

# API Keys
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "your_zhipu_key")
MODELARK_API_KEY = os.getenv("MODELARK_API_KEY", "your_modelark_key")

# ============= Language Detection and Adaptive Prompts =============

# Language detection patterns
LANGUAGE_PATTERNS = {
    'zh': re.compile(r'[\u4e00-\u9fff]'),  # Chinese characters
    'ja': re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),  # Japanese hiragana/katakana
    'ko': re.compile(r'[\uac00-\ud7af]'),  # Korean Hangul
    'ar': re.compile(r'[\u0600-\u06ff]'),  # Arabic
    'ru': re.compile(r'[а-яА-ЯёЁ]'),  # Russian Cyrillic
    'th': re.compile(r'[\u0e00-\u0e7f]'),  # Thai
}

LANGUAGE_PROMPTS = {
    'zh': """提取以下中文内容中的关键事实。重要：所有事实必须用中文写出！
从给定的文本中提取具体的、可验证的事实。每个事实应该是：
- 简洁的中文陈述
- 现在时或一般时
- 避免冗余

例如，如果输入是"我叫李四，是个工程师"，则应提取为：
- 名字是李四
- 是工程师

现在，请从以下内容中提取事实，用中文表达：""",
    'en': """You are a fact extraction expert. Extract key facts from user input.
Requirements:
1. Extract facts in concise English
2. Each fact should be a simple statement
3. Use present tense or general tense
4. Avoid redundant information
""",
    'ja': """あなたは事実抽出の専門家です。ユーザー入力から重要な事実を抽出してください。
要件：
1. 簡潔な日本語で事実を抽出してください
2. 各事実は単純なステートメントである必要があります
3. 現在時制または一般的な時制を使用してください
4. 冗長な情報は避けてください
""",
    'ko': """당신은 사실 추출 전문가입니다. 사용자 입력에서 핵심 사실을 추출하십시오.
요구사항:
1. 간결한 한국어로 사실을 추출하십시오
2. 각 사실은 단순한 설명이어야 합니다
3. 현재 시제를 사용하십시오
4. 중복되는 정보는 피하십시오
""",
    'ar': """أنت خبير استخراج الحقائق. استخرج الحقائق الرئيسية من مدخلات المستخدم.
المتطلبات:
1. استخرج الحقائق بلغة عربية موجزة
2. يجب أن تكون كل حقيقة بيانًا بسيطًا
3. استخدم الوقت الحالي أو الزمن العام
4. تجنب المعلومات المكررة
""",
    'ru': """Вы эксперт по извлечению фактов. Извлеките ключевые факты из пользовательского ввода.
Требования:
1. Извлекайте факты на кратком русском языке
2. Каждый факт должен быть простым утверждением
3. Используйте настоящее время или общее время
4. Избегайте избыточной информации
""",
    'th': """คุณเป็นผู้เชี่ยวชาญในการสกัดข้อเท็จจริง สกัดข้อเท็จจริงที่สำคัญจากอินพุตของผู้ใช้
ข้อกำหนด:
1. สกัดข้อเท็จจริงในภาษาไทยที่กระชับ
2. ข้อเท็จจริงแต่ละอย่างควรเป็นข้อความอย่างง่าย
3. ใช้กาลปัจจุบันหรือกาลทั่วไป
4. หลีกเลี่ยงข้อมูลที่ซ้ำซ้อน
""",
}

def detect_language(text: str) -> str:
    """
    Detect the language of input text based on character patterns.
    Returns language code: 'zh', 'en', 'ja', 'ko', 'ar', 'ru', 'th', etc.
    Default to 'en' if no specific pattern matches.
    """
    if not text or not isinstance(text, str):
        return 'en'
    
    # Count character occurrences for each language
    language_scores = {}
    for lang, pattern in LANGUAGE_PATTERNS.items():
        matches = len(pattern.findall(text))
        if matches > 0:
            language_scores[lang] = matches
    
    # Return the language with the most matches
    if language_scores:
        detected_lang = max(language_scores, key=language_scores.get)
        return detected_lang
    
    # Default to English if no specific pattern matches
    return 'en'

def get_system_prompt(language: str) -> str:
    """Get the system prompt for a specific language."""
    return LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS['en'])

# ============= Build Mem0 Configuration Dictionary =============
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

# Initialize Mem0 (non-blocking startup)
m = None
initialization_error = None

def initialize_mem0():
    global m, initialization_error
    try:
        print(f"Initializing Mem0 with config...")
        print(f"  - Qdrant Host: {QDRANT_HOST}:{QDRANT_PORT}")
        print(f"  - LLM Provider: {LLM_PROVIDER} | Model: {LLM_MODEL} | URL: {LLM_BASE_URL}")
        print(f"  - LLM Temperature: {LLM_TEMPERATURE} | Max Tokens: {LLM_MAX_TOKENS}")
        print(f"  - Embedder Provider: {EMBEDDING_PROVIDER} | Model: {EMBEDDING_MODEL}")
        print(f"  - Embedding Dims: {EMBEDDING_DIMS} | URL: {EMBEDDING_BASE_URL}")
        
        m = Memory.from_config(config)
        print("✓ Mem0 initialized successfully with custom config.")
        initialization_error = None
    except Exception as e:
        print(f"✗ Error initializing Mem0: {e}")
        import traceback
        traceback.print_exc()
        initialization_error = str(e)
        m = None

# Try to initialize at startup
initialize_mem0()

# Pydantic Models
class Message(BaseModel):
    role: str
    content: str

class AddMemoryRequest(BaseModel):
    messages: List[Message]
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    language: Optional[str] = None  # Auto-detected if not provided

class SearchMemoryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    results: List[Dict[str, Any]]

# Endpoints

@app.get("/")
def root():
    return {"message": "Welcome to Mem0 API", "docs_url": "/docs"}

@app.get("/health")
def health_check():
    """Health check endpoint with detailed initialization status."""
    if m is not None:
        return {"status": "healthy", "mem0_initialized": True}
    elif initialization_error:
        return {
            "status": "degraded",
            "mem0_initialized": False,
            "error": initialization_error,
            "message": "Mem0 not initialized. Check Qdrant connectivity and API keys."
        }
    else:
        return {
            "status": "initializing",
            "mem0_initialized": False,
            "message": "Mem0 is initializing..."
        }

@app.post("/memories", status_code=201)
def add_memory(request: AddMemoryRequest):
    """
    Add a new memory with auto-detected language support.
    The system detects the input language and generates facts in the same language.
    """
    if m is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")
    
    try:
        # Detect language from messages
        combined_text = " ".join([msg.content for msg in request.messages])
        detected_lang = detect_language(combined_text) if not request.language else request.language
        system_prompt = get_system_prompt(detected_lang)
        
        # Create enhanced messages with language-aware instructions
        # Inject the system prompt as a user message to influence fact extraction
        enhanced_messages = []
        
        # For the first message, prepend the language instruction
        if request.messages:
            first_msg = request.messages[0]
            enhanced_content = f"{system_prompt}\n\n[用户输入]\n{first_msg.content}" if detected_lang == 'zh' else f"{system_prompt}\n\n[User Input]\n{first_msg.content}"
            enhanced_messages.append({
                "role": "user",
                "content": enhanced_content
            })
            
            # Add remaining messages as-is
            for msg in request.messages[1:]:
                enhanced_messages.append(msg.model_dump())
        
        # Use global Mem0 instance with enhanced messages
        result = m.add(
            messages=enhanced_messages,
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            metadata={
                **(request.metadata or {}),
                "detected_language": detected_lang
            }
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memories/search")
def search_memory(request: SearchMemoryRequest):
    """
    Search for memories.
    """
    if m is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")
    
    try:
        result = m.search(
            query=request.query,
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            limit=request.limit,
            filters=request.filters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories")
def get_all_memories(user_id: Optional[str] = None, limit: int = 100):
    """
    Get all memories (simplified wrapper around get_all if available or search).
    Mem0 'get_all' might be 'get_all(user_id=...)'.
    """
    if m is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")
    
    try:
        # Check if get_all exists, otherwise use search with empty query or similar
        if hasattr(m, 'get_all'):
            return m.get_all(user_id=user_id, limit=limit)
        else:
            # Fallback to search if get_all is not directly exposed or different signature
            # But usually m.get_all() is available
            return m.get_all(user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories/{memory_id}")
def delete_memory(memory_id: str):
    """
    Delete a memory by ID.
    """
    if m is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")
    
    try:
        m.delete(memory_id)
        return {"status": "success", "message": f"Memory {memory_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memories")
def delete_all_memories(user_id: str):
    """
    Delete all memories for a user.
    """
    if m is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")
    
    try:
        m.reset(user_id=user_id)
        return {"status": "success", "message": f"All memories for user {user_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/reset-collections")
def reset_qdrant_collections():
    """
    Admin endpoint to reset/clear all Qdrant collections.
    Use this when changing embedding model dimensions to clear incompatible vectors.
    """
    try:
        from qdrant_client import QdrantClient
        
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        collections = client.get_collections()
        
        deleted_collections = []
        for collection in collections.collections:
            try:
                client.delete_collection(collection.name)
                deleted_collections.append(collection.name)
            except Exception as e:
                print(f"Failed to delete collection {collection.name}: {e}")
        
        return {
            "status": "success",
            "message": f"Reset {len(deleted_collections)} Qdrant collections",
            "deleted_collections": deleted_collections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset collections: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
