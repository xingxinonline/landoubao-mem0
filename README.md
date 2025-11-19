# Mem0 Local Docker Deployment

This project deploys a Mem0 server with custom configurations for Zhipu AI (LLM) and ModelArk (Embeddings), connected to a remote Qdrant instance.

## Prerequisites

- Docker and Docker Compose installed.
- API Keys for Zhipu AI and ModelArk.

## Configuration

1.  Open `app/.env` and set your API keys:
    ```env
    ZHIPU_API_KEY=your_actual_key
    MODELARK_API_KEY=your_actual_key
    ```
    The Qdrant host is pre-configured to `115.190.27.17`.

## Running the Server

Run the following command in the root directory:

```bash
docker-compose up --build -d
```

The server will start at `http://localhost:8000`.

## API Endpoints

-   **POST /memories**: Add a memory with automatic language detection and language-aware fact extraction.
-   **POST /memories/search**: Search memories (supports cross-language search via vector embeddings).
-   **GET /memories**: Get all memories for a user.
-   **DELETE /memories/{memory_id}**: Delete a specific memory.
-   **DELETE /memories?user_id={user_id}**: Reset memories for a user.
-   **GET /health**: Health check with Mem0 initialization status.

### Language Support

The system automatically detects input language and extracts facts in the same language:

- **中文 (Chinese)** - 自动提取中文事实
- **English** - Automatically extracts English facts
- **日本語 (Japanese)** - 日本語で事実を抽出
- **한국어 (Korean)** - 한국어로 사실 추출
- **العربية (Arabic)** - استخراج الحقائق بالعربية
- **Русский (Russian)** - Извлечение фактов на русском
- **ไทย (Thai)** - สกัดข้อเท็จจริงในภาษาไทย

See [MULTILINGUAL_FACTS.md](./MULTILINGUAL_FACTS.md) for detailed multilingual usage examples.

## API Documentation

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

## Implementation Details

-   **LLM**: Zhipu AI (`glm-4-flash-250414`) via OpenAI-compatible provider.
-   **Embedder**: ModelArk (`Qwen3-Embedding-8B`) via OpenAI-compatible provider.
-   **Vector Store**: Qdrant at `115.190.27.17:6333`.
-   **Package Management**: Uses `uv` for fast Python package management.
-   **Concurrency**: The server uses FastAPI. Blocking Mem0 calls are run in a thread pool to support concurrency.
