#!/usr/bin/env python3
"""
Test Chinese memory extraction and multilingual support
"""
import requests
import json

BASE_URL = "http://localhost:8000"
USER_ID = "chinese_user_001"

def test_chinese_memory():
    """Test adding Chinese memories and searching"""
    
    print("=" * 60)
    print("测试：中文记忆提取和搜索")
    print("=" * 60)
    
    # Test 1: Add Chinese memories
    print("\n[测试1] 添加中文记忆...")
    messages = [
        {"role": "user", "content": "我叫李四。我是Python后端工程师。我喜欢使用FastAPI框架。"}
    ]
    
    response = requests.post(
        f"{BASE_URL}/memories",
        json={
            "messages": messages,
            "user_id": USER_ID,
            "metadata": {"category": "profile"}
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if response.status_code == 201:
        extracted_facts = [item["memory"] for item in result.get("results", [])]
        print(f"\n✓ 提取的事实:")
        for fact in extracted_facts:
            print(f"  - {fact}")
    
    # Test 2: Search with Chinese query
    print("\n" + "=" * 60)
    print("[测试2] 用中文查询...")
    response = requests.post(
        f"{BASE_URL}/memories/search",
        json={
            "query": "李四做什么工作",
            "user_id": USER_ID,
            "limit": 5
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if response.status_code == 200:
        print(f"\n✓ 搜索结果 ({len(result.get('results', []))} 条):")
        for item in result.get("results", []):
            score = item.get("score", 0)
            memory = item.get("memory", "")
            print(f"  - [{score:.4f}] {memory}")
    
    # Test 3: Search with English query
    print("\n" + "=" * 60)
    print("[测试3] 用英文查询中文事实...")
    response = requests.post(
        f"{BASE_URL}/memories/search",
        json={
            "query": "What does Li Si do for work",
            "user_id": USER_ID,
            "limit": 5
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if response.status_code == 200:
        print(f"\n✓ 搜索结果 ({len(result.get('results', []))} 条):")
        for item in result.get("results", []):
            score = item.get("score", 0)
            memory = item.get("memory", "")
            print(f"  - [{score:.4f}] {memory}")
    
    # Test 4: Get all memories
    print("\n" + "=" * 60)
    print("[测试4] 获取所有记忆...")
    response = requests.get(
        f"{BASE_URL}/memories",
        params={"user_id": USER_ID}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200:
        memories = result.get("results", [])
        print(f"\n✓ 共 {len(memories)} 条记忆:")
        for item in memories:
            memory = item.get("memory", "")
            created = item.get("created_at", "")
            print(f"  - {memory}")
            print(f"    创建时间: {created}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_chinese_memory()
