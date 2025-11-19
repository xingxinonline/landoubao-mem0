# 快速设置指南

## 1️⃣ 复制环境配置模板

```bash
cd app
cp .env.example .env
```

## 2️⃣ 编辑 `.env` 文件，填入您的 API Keys

编辑 `app/.env`：

```env
# 替换为您的实际 API Keys
ZHIPU_API_KEY=your_actual_zhipu_api_key
MODELARK_API_KEY=your_actual_modelark_api_key

# 其他配置可根据需要调整
```

### 获取 API Keys

- **智谱 AI API Key**: https://open.bigmodel.cn
- **模力方舟 API Key**: https://modelark.cn

## 3️⃣ 启动服务

```bash
docker-compose up -d
```

## 4️⃣ 验证安装

```bash
curl http://localhost:8000/health
# 返回: {"status":"healthy","mem0_initialized":true}
```

## ⚠️ 重要安全提示

- ✅ `.env.example` 可以上传到 git（这是模板）
- ❌ `.env` 绝对不要上传到 git（包含真实的 API Keys）
- `.env` 已自动添加到 `.gitignore` 防止误提交

如果您的 API Keys 曾被泄露，请立即更新：
1. 登录智谱 AI 账户，重新生成 API Key
2. 登录模力方舟账户，重新生成 API Key
3. 更新本地 `.env` 文件

## 📖 完整配置说明

详见：
- `README_CN.md` - 中文完整指南
- `CONFIG_REFERENCE.md` - 详细的配置参考

## 🔍 故障排查

如果 `.env` 不存在，启动会失败：
```bash
# 如果遇到错误，确保已复制 .env.example
cp app/.env.example app/.env
```
