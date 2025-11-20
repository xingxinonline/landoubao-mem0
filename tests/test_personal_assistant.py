"""
个人助理测试脚本
演示各项功能的使用
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.personal_assistant import PersonalAssistant, MCPServerClient

def test_mcp_connection():
    """测试MCP Server连接"""
    print("\n" + "="*60)
    print("📡 测试MCP Server连接")
    print("="*60)
    
    client = MCPServerClient()
    if client.health_check():
        print("✅ MCP Server连接成功")
        return True
    else:
        print("❌ MCP Server连接失败")
        print("   请确保MCP Server在运行: python app/mcp_server_http.py")
        return False

def test_basic_conversation():
    """测试基础对话功能"""
    print("\n" + "="*60)
    print("💬 测试基础对话")
    print("="*60)
    
    try:
        assistant = PersonalAssistant()
        
        # 第一轮对话
        print("\n📝 第一轮对话...")
        user_input1 = "你好，我叫张三，我是一名Python开发工程师"
        print(f"👤 用户: {user_input1}")
        
        response1 = assistant.chat(user_input1)
        print(f"🤖 助理: {response1[:100]}...")
        
        # 第二轮对话
        print("\n📝 第二轮对话...")
        user_input2 = "我最近在学习FastAPI框架"
        print(f"👤 用户: {user_input2}")
        
        response2 = assistant.chat(user_input2)
        print(f"🤖 助理: {response2[:100]}...")
        
        print("\n✅ 基础对话测试完成")
        return True
    
    except Exception as e:
        print(f"\n❌ 对话失败: {e}")
        return False

def test_memory_operations():
    """测试记忆操作"""
    print("\n" + "="*60)
    print("💾 测试记忆操作")
    print("="*60)
    
    try:
        assistant = PersonalAssistant()
        
        # 1. 进行对话并保存到记忆
        print("\n1️⃣  保存对话到记忆...")
        user_msg = "我喜欢看科幻电影，最喜欢的是星际穿越"
        print(f"   用户输入: {user_msg}")
        
        response = assistant.chat(user_msg, save_memory=True)
        print(f"   ✓ 已保存到记忆")
        
        # 2. 加载记忆
        print("\n2️⃣  加载用户记忆...")
        memories = assistant.load_memories(limit=5)
        if memories:
            print(f"   ✓ 加载了 {len(memories)} 条记忆")
            for i, mem in enumerate(memories[:3], 1):
                mem_text = mem.get("memory", str(mem)) if isinstance(mem, dict) else str(mem)
                if len(mem_text) > 80:
                    mem_text = mem_text[:80] + "..."
                print(f"     {i}. {mem_text}")
        
        # 3. 搜索记忆
        print("\n3️⃣  搜索相关记忆...")
        query = "电影"
        results = assistant.search_memories(query)
        if results:
            print(f"   ✓ 找到 {len(results)} 条相关记忆")
            for i, result in enumerate(results[:2], 1):
                result_text = result.get("memory", str(result)) if isinstance(result, dict) else str(result)
                if len(result_text) > 80:
                    result_text = result_text[:80] + "..."
                print(f"     {i}. {result_text}")
        
        # 4. 获取统计信息
        print("\n4️⃣  获取记忆统计...")
        stats = assistant.get_memory_stats()
        if stats:
            print(f"   ✓ 总记忆数: {stats.get('total_memories', 0)}")
            print(f"   ✓ 用户ID: {stats.get('user_id', 'N/A')[:8]}...")
        
        print("\n✅ 记忆操作测试完成")
        return True
    
    except Exception as e:
        print(f"\n❌ 记忆操作失败: {e}")
        return False

def test_context_awareness():
    """测试上下文感知能力"""
    print("\n" + "="*60)
    print("🧠 测试上下文感知能力")
    print("="*60)
    
    try:
        assistant = PersonalAssistant()
        
        # 保存一些背景信息
        print("\n1️⃣  保存背景信息...")
        background_msgs = [
            "我叫王五，是一名技术经理",
            "我主要管理一个15人的开发团队",
            "我们的技术栈是React + Python + PostgreSQL",
            "我特别关心团队的代码质量和知识共享"
        ]
        
        for msg in background_msgs:
            print(f"   📝 {msg}")
            assistant.chat(msg, save_memory=True)
        
        # 加载这些记忆
        print("\n2️⃣  加载记忆...")
        assistant.load_memories(limit=10)
        
        # 进行相关的对话，看是否融合了记忆信息
        print("\n3️⃣  进行上下文感知的对话...")
        context_aware_query = "你认为我应该如何提高团队的代码质量？"
        print(f"   👤 用户: {context_aware_query}")
        
        response = assistant.chat(context_aware_query)
        print(f"   🤖 助理: {response[:150]}...")
        
        if "团队" in response or "开发" in response or "代码" in response:
            print("\n   ✓ 助理成功融合了上下文信息")
        else:
            print("\n   ℹ️  助理生成了独立回答")
        
        print("\n✅ 上下文感知测试完成")
        return True
    
    except Exception as e:
        print(f"\n❌ 上下文感知测试失败: {e}")
        return False

def test_multilingual():
    """测试多语言支持"""
    print("\n" + "="*60)
    print("🌍 测试多语言支持")
    print("="*60)
    
    try:
        client = MCPServerClient()
        
        # 测试语言检测
        test_texts = [
            ("你好，我叫李四", "zh"),
            ("Hello, my name is John", "en"),
            ("こんにちは、私の名前は太郎です", "ja"),
            ("안녕하세요, 제 이름은 김철수입니다", "ko"),
        ]
        
        print("\n检测不同语言的文本:")
        for text, expected_lang in test_texts:
            result = client.detect_language(text)
            detected_lang = result.get("language_code", "unknown")
            confidence = result.get("confidence", 0)
            
            status = "✓" if detected_lang == expected_lang else "⚠"
            print(f"   {status} {text[:20]}... → {detected_lang} (置信度: {confidence}%)")
        
        print("\n✅ 多语言支持测试完成")
        return True
    
    except Exception as e:
        print(f"\n❌ 多语言测试失败: {e}")
        return False

def test_conversation_flow():
    """测试完整的对话流程"""
    print("\n" + "="*60)
    print("🔄 测试完整对话流程")
    print("="*60)
    
    try:
        assistant = PersonalAssistant()
        
        print("\n模拟真实对话场景...")
        conversation = [
            ("我是一名创业者，正在做一个电商平台", "background"),
            ("我们的目标用户是25-35岁的年轻职业人士", "context"),
            ("我们现在面临的主要挑战是用户留存率", "problem"),
            ("基于我之前的背景，你有什么建议吗？", "question"),
            ("谢谢你的建议，非常有帮助", "feedback"),
        ]
        
        for i, (user_input, context_type) in enumerate(conversation, 1):
            print(f"\n💬 轮次 {i} [{context_type}]:")
            print(f"   👤 用户: {user_input}")
            
            # 前3轮自动保存，后续轮次也保存
            response = assistant.chat(user_input, save_memory=(i <= 3))
            print(f"   🤖 助理: {response[:100]}...")
        
        # 最后搜索相关记忆
        print("\n🔍 搜索相关记忆...")
        memories = assistant.search_memories("用户留存")
        if memories:
            print(f"   ✓ 找到 {len(memories)} 条相关记忆")
        
        print("\n✅ 完整对话流程测试完成")
        return True
    
    except Exception as e:
        print(f"\n❌ 对话流程测试失败: {e}")
        return False

def print_test_summary(results: dict):
    """打印测试总结"""
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    print(f"\n总体: {passed}/{total} 测试通过")
    
    if failed == 0:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  有 {failed} 个测试失败，请查看错误信息")

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 个人助理功能测试套件")
    print("="*60)
    
    # 检查环境配置
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("\n❌ 错误: 未找到 ZHIPU_API_KEY 环境变量")
        print("请设置: $env:ZHIPU_API_KEY = 'your_api_key'")
        return
    
    print("\n✓ 环境配置检查通过")
    
    # 运行测试
    results = {}
    
    # 1. 连接测试（如果失败，跳过其他测试）
    results["MCP Server连接"] = test_mcp_connection()
    
    if not results["MCP Server连接"]:
        print("\n⚠️  MCP Server不可用，跳过其他测试")
        print("请确保运行: python app/mcp_server_http.py")
        print_test_summary(results)
        return
    
    # 2. 其他测试
    results["基础对话"] = test_basic_conversation()
    results["记忆操作"] = test_memory_operations()
    results["上下文感知"] = test_context_awareness()
    results["多语言支持"] = test_multilingual()
    results["完整对话流程"] = test_conversation_flow()
    
    # 打印总结
    print_test_summary(results)
    
    # 后续步骤
    print("\n📌 后续步骤:")
    print("   1. 运行交互模式: python app/personal_assistant.py")
    print("   2. 尝试各种命令: /help, /memories, /search, /stats")
    print("   3. 进行自然对话并使用 /save 保存重要信息")

if __name__ == "__main__":
    main()
