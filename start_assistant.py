"""
快速启动脚本 - 一键启动完整系统
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          🤖 智能个人助理 - 快速启动系统                        ║
║                                                                ║
║     集成MCP记忆模块的大模型对话私人助理                        ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)

def check_requirements():
    """检查依赖和环境"""
    print("\n📋 检查环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本需要3.8及以上")
        return False
    print(f"✅ Python版本: {sys.version_info.major}.{sys.version_info.minor}")
    
    # 检查API密钥
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("⚠️  警告: 未设置 ZHIPU_API_KEY 环境变量")
        print("   请执行: $env:ZHIPU_API_KEY = 'your_api_key'")
        return False
    print("✅ API密钥已设置")
    
    # 检查必要的包
    packages = ['openai', 'fastapi', 'uvicorn', 'requests']
    missing = []
    
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ 缺少依赖包: {', '.join(missing)}")
        print(f"   执行: pip install {' '.join(missing)}")
        return False
    
    print(f"✅ 所有依赖包已安装")
    return True

def start_service(name: str, script: str, port: int) -> subprocess.Popen:
    """启动服务"""
    print(f"\n🚀 启动 {name} (端口: {port})...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent
        )
        
        # 给服务一些启动时间
        time.sleep(2)
        
        # 检查进程是否还活跃
        if process.poll() is None:
            print(f"   ✅ {name} 已启动")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"   ❌ {name} 启动失败")
            if stderr:
                print(f"   错误: {stderr[:200]}")
            return None
    
    except Exception as e:
        print(f"   ❌ 启动失败: {e}")
        return None

def check_service(url: str, timeout: int = 10) -> bool:
    """检查服务是否可用"""
    import requests
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except:
            pass
        
        time.sleep(1)
    
    return False

def main():
    """主程序"""
    print_banner()
    
    # 检查环境
    if not check_requirements():
        print("\n❌ 环境检查失败，请修复上述问题后重试")
        sys.exit(1)
    
    print("\n✅ 环境检查通过")
    
    # 获取项目根目录
    root_dir = Path(__file__).parent
    
    # 定义要启动的服务
    services = [
        {
            "name": "MCP Server",
            "script": "app/mcp_server_http.py",
            "port": 8001,
            "url": "http://localhost:8001/health",
            "doc": "http://localhost:8001"
        },
        {
            "name": "Web助理API",
            "script": "app/personal_assistant_web.py",
            "port": 8002,
            "url": "http://localhost:8002/health",
            "doc": "http://localhost:8002/docs"
        }
    ]
    
    processes = []
    failed_services = []
    
    # 启动所有服务
    for service in services:
        process = start_service(
            service["name"],
            str(root_dir / service["script"]),
            service["port"]
        )
        
        if process:
            processes.append(process)
            
            # 检查服务可用性
            print(f"   检查服务可用性...", end=" ", flush=True)
            if check_service(service["url"]):
                print("✅")
            else:
                print("⚠️  (启动中)")
        else:
            failed_services.append(service["name"])
    
    # 总结启动结果
    print("\n" + "="*60)
    print("📊 启动结果")
    print("="*60)
    
    if failed_services:
        print(f"\n❌ 以下服务启动失败:")
        for service in failed_services:
            print(f"   - {service}")
        
        print("\n⚠️  部分服务不可用，某些功能可能受限")
    else:
        print("\n✅ 所有服务启动成功！")
    
    # 打印访问信息
    print("\n📌 访问信息:")
    print("="*60)
    
    for service in services:
        status = "⚠️ " if service["name"] in failed_services else "✅"
        print(f"\n{status} {service['name']}")
        print(f"   端口: {service['port']}")
        print(f"   URL: {service['doc']}")
    
    # 选择启动方式
    print("\n" + "="*60)
    print("🎯 选择启动方式")
    print("="*60)
    print("""
1. CLI模式 (命令行交互)
   python app/personal_assistant.py

2. Web模式 (浏览器界面)
   打开: http://localhost:8002/static/index.html

3. 测试模式 (运行功能测试)
   python tests/test_personal_assistant.py

4. API模式 (调用API接口)
   POST http://localhost:8002/api/chat
    """)
    
    # 尝试打开Web界面
    try:
        print("\n🌐 尝试打开Web界面...")
        webbrowser.open("http://localhost:8002/static/index.html")
        print("   ✅ 已在浏览器中打开")
    except Exception as e:
        print(f"   ℹ️  无法自动打开浏览器: {e}")
        print("   请手动访问: http://localhost:8002/static/index.html")
    
    # 保持运行
    print("\n⏳ 系统运行中... (按 Ctrl+C 停止)")
    print("="*60)
    
    try:
        while True:
            time.sleep(1)
            
            # 检查进程是否还活跃
            for process in processes:
                if process and process.poll() is not None:
                    print("\n⚠️  一个服务已停止")
                    break
    
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，关闭所有服务...")
        
        for process in processes:
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()
        
        print("✅ 所有服务已停止")
        print("\n👋 再见!")

if __name__ == "__main__":
    main()
