"""
MCP Server for Mem0 Memory Management
Provides memory operations through Model Context Protocol
"""

import asyncio
import json
import sys
import os
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Mem0 imports
from mem0 import Memory

# Initialize MCP Server
app = Server("mem0-mcp-server")

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
    
    # Count character matches for each language
    lang_scores = {}
    for lang, pattern in LANGUAGE_PATTERNS.items():
        matches = len(pattern.findall(text))
        if matches > 0:
            lang_scores[lang] = matches
    
    # Return language with highest match count
    if lang_scores:
        return max(lang_scores, key=lang_scores.get)
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
try:
    m = Memory.from_config(config)
    print("✓ Mem0 initialized successfully", file=sys.stderr)
except Exception as e:
    print(f"✗ Error initializing Mem0: {e}", file=sys.stderr)

# ============= MCP Tool Definitions =============

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools for Mem0 operations."""
    return [
        Tool(
            name="add_memory",
            description="Add a new memory from conversation messages with automatic multilingual support. Extracts facts in the detected language.",
            inputSchema={
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
                    "user_id": {
                        "type": "string",
                        "description": "Unique identifier for the user"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (zh/en/ja/ko/ar/ru/th). If not provided, auto-detect from content.",
                        "enum": ["zh", "en", "ja", "ko", "ar", "ru", "th"]
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata to store with the memory",
                        "additionalProperties": True
                    }
                },
                "required": ["messages", "user_id"]
            }
        ),
        Tool(
            name="search_memory",
            description="Search for relevant memories based on a query. Retrieves contextual information about a user.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant memories"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID to search memories for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    }
                },
                "required": ["query", "user_id"]
            }
        ),
        Tool(
            name="get_all_memories",
            description="Get all memories for a specific user. Returns complete memory history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to retrieve memories for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to return",
                        "default": 100
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="delete_memory",
            description="Delete a specific memory by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "ID of the memory to delete"
                    }
                },
                "required": ["memory_id"]
            }
        ),
        Tool(
            name="delete_all_memories",
            description="Delete all memories for a specific user. This operation cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to delete all memories for"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="create_user_session",
            description="Create a new user session with a unique UUID. Returns the user ID for future operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata for the user session",
                        "additionalProperties": True
                    }
                }
            }
        ),
        Tool(
            name="get_memory_stats",
            description="Get statistics about memories for a user, including total count and recent activity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to get statistics for"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="detect_language",
            description="Detect the language of a given text. Returns language code and confidence.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to detect language from"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="search_memories_by_language",
            description="Search for memories in a specific language or all languages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID to search memories for"
                    },
                    "language": {
                        "type": "string",
                        "description": "Filter by language (zh/en/ja/ko/ar/ru/th). If not provided, search all languages.",
                        "enum": ["zh", "en", "ja", "ko", "ar", "ru", "th"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    }
                },
                "required": ["query", "user_id"]
            }
        )
    ]

# ============= MCP Tool Implementations =============

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls from MCP clients."""
    
    if m is None:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Mem0 not initialized. Check configuration and API keys."
            })
        )]
    
    try:
        if name == "add_memory":
            messages = arguments.get("messages", [])
            user_id = arguments.get("user_id")
            metadata = arguments.get("metadata", {})
            language = arguments.get("language")
            
            # Detect language if not provided
            if not language:
                # Get language from first user message
                for msg in messages:
                    if msg.get("role") == "user":
                        language = detect_language(msg.get("content", ""))
                        break
                if not language:
                    language = "en"
            
            # Add language-specific system prompt
            system_prompt = get_system_prompt(language)
            enhanced_messages = [
                {"role": "system", "content": system_prompt}
            ] + messages
            
            # Add timestamp and language to metadata
            metadata["timestamp"] = datetime.now().isoformat()
            metadata["language"] = language
            
            result = m.add(
                messages=enhanced_messages,
                user_id=user_id,
                metadata=metadata
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "result": result,
                    "language": language,
                    "message": f"Memory added successfully in {language}"
                }, indent=2)
            )]
        
        elif name == "search_memory":
            query = arguments.get("query")
            user_id = arguments.get("user_id")
            limit = arguments.get("limit", 5)
            
            result = m.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "results": result,
                    "count": len(result) if isinstance(result, list) else 0
                }, indent=2)
            )]
        
        elif name == "get_all_memories":
            user_id = arguments.get("user_id")
            limit = arguments.get("limit", 100)
            
            result = m.get_all(user_id=user_id, limit=limit)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "memories": result,
                    "total": len(result) if isinstance(result, list) else 0
                }, indent=2)
            )]
        
        elif name == "delete_memory":
            memory_id = arguments.get("memory_id")
            
            m.delete(memory_id)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Memory {memory_id} deleted successfully"
                }, indent=2)
            )]
        
        elif name == "delete_all_memories":
            user_id = arguments.get("user_id")
            
            m.reset(user_id=user_id)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"All memories for user {user_id} deleted successfully"
                }, indent=2)
            )]
        
        elif name == "create_user_session":
            user_id = str(uuid.uuid4())
            metadata = arguments.get("metadata", {})
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                    "metadata": metadata
                }, indent=2)
            )]
        
        elif name == "get_memory_stats":
            user_id = arguments.get("user_id")
            
            all_memories = m.get_all(user_id=user_id)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "user_id": user_id,
                    "total_memories": len(all_memories) if isinstance(all_memories, list) else 0,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            )]
        
        elif name == "detect_language":
            text = arguments.get("text", "")
            language = detect_language(text)
            
            # Calculate confidence based on character matches
            pattern = LANGUAGE_PATTERNS.get(language)
            if pattern:
                matches = len(pattern.findall(text))
                confidence = min(100, (matches / max(1, len(text))) * 100)
            else:
                confidence = 0
            
            lang_name = {
                "zh": "Chinese (中文)",
                "en": "English",
                "ja": "Japanese (日本語)",
                "ko": "Korean (한국어)",
                "ar": "Arabic (العربية)",
                "ru": "Russian (Русский)",
                "th": "Thai (ไทย)"
            }.get(language, "Unknown")
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "language_code": language,
                    "language_name": lang_name,
                    "confidence": round(confidence, 2),
                    "text_sample": text[:100]
                }, indent=2)
            )]
        
        elif name == "search_memories_by_language":
            query = arguments.get("query")
            user_id = arguments.get("user_id")
            language = arguments.get("language")
            limit = arguments.get("limit", 5)
            
            # First search all memories
            all_results = m.search(
                query=query,
                user_id=user_id,
                limit=limit * 2  # Get more to filter by language
            )
            
            # Filter by language if specified
            if language:
                filtered_results = []
                for item in (all_results if isinstance(all_results, list) else []):
                    # Check if item has language in metadata
                    meta = item.get("metadata", {}) if isinstance(item, dict) else {}
                    if meta.get("language") == language:
                        filtered_results.append(item)
                    if len(filtered_results) >= limit:
                        break
                results = filtered_results
            else:
                results = all_results[:limit] if isinstance(all_results, list) else []
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "query": query,
                    "language_filter": language,
                    "results": results,
                    "count": len(results) if isinstance(results, list) else 0
                }, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}"
                })
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            })
        )]

# ============= Main Entry Point =============

async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
