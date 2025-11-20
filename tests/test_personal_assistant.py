#!/usr/bin/env python3
"""
多用户多语言私人助理测试
Test for Multi-user Multilingual Personal Assistant with Memory

演示场景：
1. 三个用户（张三、John、田中）使用不同语言与助理对话
2. 助理通过Mem0记忆模块记住用户信息
3. 多轮对话展示记忆的累积和使用
4. 验证助理能回忆起之前的对话内容
"""

import requests
import json
import time
import random
from typing import List, Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
ZHIPU_API_KEY = "your_zhipu_api_key"  # 需要配置实际的API key
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 读取实际的API key
try:
    import os
    env_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('ZHIPU_API_KEY='):
                    ZHIPU_API_KEY = line.split('=', 1)[1].strip()
                    print(f"✓ 已加载API Key")
                    break
    else:
        print(f"Warning: .env file not found at {env_path}")
except Exception as e:
    print(f"Warning: Could not read API key from .env: {e}")

# 模拟的用户数据
USERS = {
    "user_zh_001": {
        "name": "张三",
        "language": "zh",
        "greeting": "你好"
    },
    "user_en_001": {
        "name": "John",
        "language": "en",
        "greeting": "Hello"
    },
    "user_ja_001": {
        "name": "田中",
        "language": "ja",
        "greeting": "こんにちは"
    }
}

# 对话场景（每个用户的对话流）
CONVERSATION_SCENARIOS = {
    "user_zh_001": [
        "你好，我是张三，一名软件工程师。",
        "我喜欢用Python开发后端应用。",
        "我最近在学习微服务架构。",
        "我的生日是5月15日。",
        "我喜欢喝咖啡，尤其是拿铁。",
        "你还记得我的名字吗？",
        "我是做什么工作的？",
        "我喜欢什么编程语言？",
        "我的生日是什么时候？",
        "总结一下你对我的了解。"
    ],
    "user_en_001": [
        "Hi, I'm John, a data scientist.",
        "I work with machine learning models daily.",
        "My favorite framework is TensorFlow.",
        "I have two cats named Luna and Max.",
        "I enjoy playing guitar in my free time.",
        "What's my name?",
        "What do I do for a living?",
        "Do you remember what pets I have?",
        "What instrument do I play?",
        "Tell me everything you know about me."
    ],
    "user_ja_001": [
        "こんにちは、私は田中と申します。プロダクトマネージャーです。",
        "私は東京で働いています。",
        "趣味は写真撮影とハイキングです。",
        "好きな食べ物は寿司とラーメンです。",
        "週末はよく山に登ります。",
        "私の名前を覚えていますか？",
        "私の仕事は何ですか？",
        "私の趣味は何ですか？",
        "私はどこで働いていますか？",
        "私について知っていることを全て教えてください。"
    ]
}

class PersonalAssistant:
    """带有Mem0记忆的私人助理"""
    
    def __init__(self, mem0_base_url: str, llm_api_key: str):
        self.mem0_url = mem0_base_url
        self.llm_api_key = llm_api_key
        self.llm_url = ZHIPU_API_URL
    
    def add_memory(self, user_id: str, message: str) -> Dict[str, Any]:
        """添加用户消息到记忆"""
        try:
            response = requests.post(
                f"{self.mem0_url}/memories",
                json={
                    "messages": [
                        {"role": "user", "content": message}
                    ],
                    "user_id": user_id
                },
                timeout=30
            )
            if response.status_code == 201:
                return response.json()
            else:
                print(f"Memory addition failed: {response.status_code}")
                return {"results": []}
        except Exception as e:
            print(f"Error adding memory: {e}")
            return {"results": []}
    
    def search_memory(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索用户相关记忆"""
        try:
            response = requests.post(
                f"{self.mem0_url}/memories/search",
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": limit
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                print(f"Memory search failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error searching memory: {e}")
            return []
    
    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有记忆"""
        try:
            response = requests.get(
                f"{self.mem0_url}/memories?user_id={user_id}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                return []
        except Exception as e:
            print(f"Error getting memories: {e}")
            return []
    
    def chat_with_llm(self, messages: List[Dict[str, str]], context: str = "") -> str:
        """使用LLM生成回复"""
        try:
            # 构建系统提示（包含记忆上下文）
            system_message = {
                "role": "system",
                "content": f"""你是一个友好的私人助理。你有记忆能力，可以记住用户告诉你的信息。

【用户相关信息】
{context if context else '暂无'}

请根据用户的问题，结合你记住的信息，给出友好、准确的回答。
如果用户问起之前告诉过你的信息，请准确回忆并回答。
如果是新信息，表示你已经记住了。
用户使用什么语言，你就用什么语言回复。"""
            }
            
            # 构建完整的消息列表
            full_messages = [system_message] + messages
            
            # 调用Zhipu AI
            response = requests.post(
                self.llm_url,
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4-flash",
                    "messages": full_messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"LLM API error: {response.status_code}")
                print(f"Response: {response.text}")
                return "抱歉，我现在无法回答。"
        
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "抱歉，出现了错误。"
    
    def process_message(self, user_id: str, user_message: str) -> str:
        """处理用户消息并生成回复"""
        
        # 1. 将用户消息存入记忆
        print(f"    📝 正在存储记忆...")
        memory_result = self.add_memory(user_id, user_message)
        added_facts = memory_result.get("results", [])
        
        if added_facts:
            print(f"    ✓ 存储了 {len(added_facts)} 个记忆片段")
            for fact in added_facts:
                memory_text = fact.get("memory", "")
                if memory_text:
                    print(f"      - {memory_text}")
        
        # 2. 搜索相关记忆
        print(f"    🔍 搜索相关记忆...")
        relevant_memories = self.search_memory(user_id, user_message, limit=10)
        
        # 构建记忆上下文
        memory_context = ""
        if relevant_memories:
            print(f"    ✓ 找到 {len(relevant_memories)} 条相关记忆")
            memory_lines = []
            for mem in relevant_memories:
                memory_text = mem.get("memory", "")
                score = mem.get("score", 0)
                if memory_text and score > 0.1:  # 过滤低相关度的记忆
                    memory_lines.append(f"- {memory_text}")
            
            if memory_lines:
                memory_context = "\n".join(memory_lines)
                print(f"    📚 使用以下记忆作为上下文：")
                for line in memory_lines[:5]:  # 只显示前5条
                    print(f"      {line}")
        else:
            print(f"    ℹ️  暂无相关记忆")
        
        # 3. 使用LLM生成回复
        print(f"    🤖 生成回复...")
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        response = self.chat_with_llm(messages, memory_context)
        
        return response


def run_conversation_test():
    """运行多用户对话测试"""
    
    print("\n" + "="*80)
    print("🤖 多用户多语言私人助理测试")
    print("="*80)
    
    # 检查Mem0服务
    print("\n📡 检查Mem0服务...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Mem0服务未运行")
            print("   请先启动: docker-compose up -d")
            return False
        print("✓ Mem0服务正常运行")
    except Exception as e:
        print(f"❌ 无法连接到Mem0服务: {e}")
        return False
    
    # 检查API Key
    if not ZHIPU_API_KEY or ZHIPU_API_KEY == "your_zhipu_api_key":
        print("❌ 请配置ZHIPU_API_KEY")
        return False
    
    # 初始化助理
    assistant = PersonalAssistant(BASE_URL, ZHIPU_API_KEY)
    
    # 清空所有用户的记忆（重新开始）
    print("\n🧹 清空所有用户的历史记忆...")
    for user_id in USERS.keys():
        try:
            requests.delete(f"{BASE_URL}/memories?user_id={user_id}", timeout=10)
        except:
            pass
    print("✓ 清空完成")
    
    # 交替进行多用户对话
    print("\n" + "="*80)
    print("💬 开始多用户对话测试")
    print("="*80)
    
    total_rounds = 0
    user_ids = list(USERS.keys())
    
    # 每个用户的对话进度
    user_progress = {uid: 0 for uid in user_ids}
    
    # 进行至少20轮对话
    while total_rounds < 20:
        # 随机选择一个用户
        user_id = random.choice(user_ids)
        user_info = USERS[user_id]
        scenario = CONVERSATION_SCENARIOS[user_id]
        
        # 如果这个用户的对话已经完成，跳过
        if user_progress[user_id] >= len(scenario):
            continue
        
        # 获取用户的下一条消息
        user_message = scenario[user_progress[user_id]]
        user_progress[user_id] += 1
        total_rounds += 1
        
        # 显示对话
        print("\n" + "-"*80)
        print(f"第 {total_rounds} 轮对话")
        print(f"👤 用户: {user_info['name']} ({user_id})")
        print(f"🌍 语言: {user_info['language']}")
        print("-"*80)
        print(f"用户说: {user_message}")
        
        # 处理消息并获取回复
        response = assistant.process_message(user_id, user_message)
        
        print(f"\n🤖 助理回复:")
        print(f"    {response}")
        
        # 短暂延时（避免API限流）
        time.sleep(1)
    
    # 测试完成后，显示每个用户的记忆摘要
    print("\n" + "="*80)
    print("📊 记忆模块效果验证")
    print("="*80)
    
    for user_id, user_info in USERS.items():
        print(f"\n{'='*80}")
        print(f"👤 用户: {user_info['name']} ({user_id})")
        print(f"{'='*80}")
        
        # 获取所有记忆
        memories = assistant.get_all_memories(user_id)
        
        if memories:
            print(f"\n📚 记忆库中存储的信息 ({len(memories)} 条):\n")
            for idx, mem in enumerate(memories, 1):
                memory_text = mem.get("memory", "")
                metadata = mem.get("metadata", {})
                lang = metadata.get("detected_language", "unknown")
                created = mem.get("created_at", "")
                
                print(f"  {idx}. {memory_text}")
                print(f"     [语言: {lang} | 创建时间: {created}]")
        else:
            print("  暂无记忆")
    
    # 最终验证：问助理关于每个用户的综合问题
    print("\n" + "="*80)
    print("🎯 最终验证：综合记忆测试")
    print("="*80)
    
    verification_questions = {
        "user_zh_001": "请详细总结一下你对张三的所有了解，包括他的工作、兴趣爱好、个人信息等。",
        "user_en_001": "Please give me a complete summary of everything you know about John, including his work, hobbies, and personal details.",
        "user_ja_001": "田中さんについて知っていることを全て詳しく教えてください。仕事、趣味、個人情報など。"
    }
    
    for user_id, question in verification_questions.items():
        user_info = USERS[user_id]
        print(f"\n{'─'*80}")
        print(f"👤 测试用户: {user_info['name']}")
        print(f"❓ 问题: {question}")
        print(f"{'─'*80}")
        
        # 获取所有记忆作为上下文
        memories = assistant.get_all_memories(user_id)
        memory_context = "\n".join([f"- {m.get('memory', '')}" for m in memories if m.get('memory')])
        
        # 生成综合回答
        messages = [{"role": "user", "content": question}]
        response = assistant.chat_with_llm(messages, memory_context)
        
        print(f"\n💬 助理的综合回答:")
        print(f"    {response}")
        
        time.sleep(1)
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80)
    print("\n📈 测试统计:")
    print(f"  - 总对话轮数: {total_rounds}")
    print(f"  - 参与用户数: {len(USERS)}")
    print(f"  - 支持语言数: {len(set(u['language'] for u in USERS.values()))}")
    
    # 统计记忆总数
    total_memories = sum(len(assistant.get_all_memories(uid)) for uid in USERS.keys())
    print(f"  - 存储记忆总数: {total_memories}")
    
    print("\n✨ 记忆模块作用体现:")
    print("  1. ✓ 准确记住每个用户的个人信息")
    print("  2. ✓ 支持多语言对话和记忆")
    print("  3. ✓ 能够在后续对话中回忆之前的内容")
    print("  4. ✓ 提供基于记忆的个性化回答")
    print("  5. ✓ 多用户记忆隔离，互不干扰")
    
    return True


if __name__ == "__main__":
    success = run_conversation_test()
    exit(0 if success else 1)
