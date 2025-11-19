# Changelog

## [v1.1.0] - 2025-11-19

### ✨ Features
- **Configurable Embedding Models** - Switch between `Qwen3-Embedding-0.6B` (1024 dims, low resource) and `Qwen3-Embedding-8B` (4096 dims, high quality)
- **Admin Reset Endpoint** - `POST /admin/reset-collections` for clearing Qdrant collections when changing embedding dimensions
- **Environment Variable Configuration** - Control embedding model and dimensions via `EMBEDDING_MODEL` and `EMBEDDING_DIMS` env vars

### 🔧 Changes
- Updated `app/main.py` to extract embedding configuration from environment variables
- Added `EMBEDDING_MODEL=Qwen3-Embedding-0.6B` and `EMBEDDING_DIMS=1024` to `.env` (default: low-resource production config)
- Updated `README_CN.md` with embedding model configuration guide
- Updated `DEPLOYMENT_SUMMARY.md` with resource optimization details

### 📊 Performance Impact
- **Memory Reduction**: ~75% reduction in Qdrant storage with 0.6B model (1024 vs 4096 dims)
- **Backward Compatible**: Existing API endpoints unchanged
- **Zero Downtime**: Use `/admin/reset-collections` → update config → restart to switch models

### ✅ Testing
- All API endpoints verified with new 1024-dimensional embeddings
- POST /memories: Memory creation working ✓
- POST /memories/search: Search with relevance scores working ✓
- GET /memories: Memory retrieval working ✓
- POST /admin/reset-collections: Collection reset working ✓

## [v1.0.0] - Initial Release

### Features
- ✅ Full Mem0 Docker deployment
- ✅ Zhipu AI LLM integration (glm-4-flash-250414)
- ✅ ModelArk Embedding integration
- ✅ Qdrant Vector Database (remote: 115.190.24.157:6333)
- ✅ FastAPI REST API with 8 endpoints
- ✅ Async/concurrent request support
- ✅ UV-based Python dependency management
- ✅ Comprehensive test suite
- ✅ Chinese & English documentation
