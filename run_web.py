#!/usr/bin/env python
"""
Web版个人助理启动脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault("PYTHONPATH", str(project_root))

# 导入并运行Web应用
from app.personal_assistant_web import app, uvicorn

if __name__ == "__main__":
    print("🚀 启动Web版个人助理...")
    print(f"   API文档: http://localhost:8002/docs")
    print(f"   Web界面: http://localhost:8002/static/index.html")
    print(f"   健康检查: http://localhost:8002/health")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
