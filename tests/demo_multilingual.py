#!/usr/bin/env python3
"""
快速演示脚本：展示中文和英文事实提取的对比
Quick demo script: Show Chinese and English fact extraction comparison
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def demo_chinese():
    """演示中文事实提取 (Demonstrate Chinese fact extraction)"""
    
    print("\n" + "="*70)
    print("【中文演示】Chinese Demo")
    print("="*70)
    
    chinese_text = "我叫张三。我是一名资深数据科学家。我热爱机器学习和数据分析。"
    
    print(f"\n输入 (Input): {chinese_text}")
    print("-"*70)
    
    response = requests.post(
        f"{BASE_URL}/memories",
        json={
            "messages": [{"role": "user", "content": chinese_text}],
            "user_id": "demo_zh"
        }
    )
    
    if response.status_code == 201:
        result = response.json()
        facts = result.get("results", [])
        
        print(f"\n提取的事实 ({len(facts)} facts extracted):\n")
        for idx, fact in enumerate(facts, 1):
            memory = fact.get("memory", "")
            print(f"  {idx}. {memory}")
            # 检查是否是中文
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in memory)
            status = "✓ 中文" if has_chinese else "✗ English"
            print(f"     {status}\n")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

def demo_english():
    """演示英文事实提取 (Demonstrate English fact extraction)"""
    
    print("\n" + "="*70)
    print("【英文演示】English Demo")
    print("="*70)
    
    english_text = "My name is Alice. I am a senior software architect. I love designing distributed systems."
    
    print(f"\nInput: {english_text}")
    print("-"*70)
    
    response = requests.post(
        f"{BASE_URL}/memories",
        json={
            "messages": [{"role": "user", "content": english_text}],
            "user_id": "demo_en"
        }
    )
    
    if response.status_code == 201:
        result = response.json()
        facts = result.get("results", [])
        
        print(f"\nExtracted {len(facts)} facts:\n")
        for idx, fact in enumerate(facts, 1):
            memory = fact.get("memory", "")
            print(f"  {idx}. {memory}")
            # Check if it's English
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in memory)
            status = "✗ Chinese" if has_chinese else "✓ English"
            print(f"     {status}\n")
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

def demo_search():
    """演示跨语言搜索 (Demonstrate cross-language search)"""
    
    print("\n" + "="*70)
    print("【跨语言搜索演示】Cross-Language Search Demo")
    print("="*70)
    
    # 用中文查询英文数据
    print("\n用中文查询英文数据 (Chinese query on English data):")
    print("-"*70)
    
    query_zh = "这个人的职位是什么"
    print(f"查询 (Query): {query_zh}")
    
    response = requests.post(
        f"{BASE_URL}/memories/search",
        json={
            "query": query_zh,
            "user_id": "demo_en",
            "limit": 3
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        results = result.get("results", [])
        
        if results:
            print(f"\n搜索结果 (Search results):\n")
            for item in results:
                score = item.get("score", 0)
                memory = item.get("memory", "")
                print(f"  [{score:.4f}] {memory}")
        else:
            print("No results found.")
    else:
        print(f"Error: {response.status_code}")

def demo_metadata():
    """演示元数据 (Demonstrate metadata tracking)"""
    
    print("\n" + "="*70)
    print("【元数据追踪演示】Metadata Tracking Demo")
    print("="*70)
    
    print("\n中文用户的记忆元数据 (Chinese user memories with metadata):")
    print("-"*70)
    
    response = requests.get(
        f"{BASE_URL}/memories?user_id=demo_zh"
    )
    
    if response.status_code == 200:
        result = response.json()
        memories = result.get("results", [])
        
        if memories:
            print(f"\n找到 {len(memories)} 条记忆:\n")
            for memory in memories:
                content = memory.get("memory", "")
                metadata = memory.get("metadata", {})
                lang = metadata.get("detected_language", "unknown")
                
                print(f"  记忆 (Memory): {content}")
                print(f"  语言 (Language): {lang}\n")
        else:
            print("No memories found.")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Mem0 多语言事实提取演示")
    print("Mem0 Multilingual Fact Extraction Demo")
    print("="*70)
    
    try:
        # 检查服务器是否运行
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n✗ 服务器未运行 (Server not running)")
            print("  Please start the server with: docker-compose up -d")
            exit(1)
    except requests.ConnectionError:
        print("\n✗ 无法连接到服务器 (Cannot connect to server)")
        print("  Please start the server with: docker-compose up -d")
        exit(1)
    
    # 运行演示
    demo_chinese()
    demo_english()
    demo_search()
    demo_metadata()
    
    print("\n" + "="*70)
    print("演示完成 (Demo completed)")
    print("="*70 + "\n")
