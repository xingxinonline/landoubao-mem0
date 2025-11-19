import os
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
    Add a new memory.
    """
    if m is None:
        raise HTTPException(status_code=503, detail="Mem0 not initialized")
    
    try:
        # Convert Pydantic models to dicts
        msgs = [msg.model_dump() for msg in request.messages]
        result = m.add(
            messages=msgs,
            user_id=request.user_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            metadata=request.metadata
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
