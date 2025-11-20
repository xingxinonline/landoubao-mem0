#!/usr/bin/env python3
"""
Test Chinese language-aware fact extraction
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_chinese_extraction():
    """Test adding memories in Chinese and verify facts are extracted in Chinese"""
    
    print("\n" + "=" * 70)
    print("Chinese Language-Aware Fact Extraction Test")
    print("=" * 70)
    
    # Test 1: Add Chinese memory
    print("\n【测试 1】添加中文记忆")
    print("-" * 70)
    
    chinese_input = "我叫李四。我是一名高级Python后端工程师。我喜欢使用FastAPI框架进行异步编程。"
    print(f"输入: {chinese_input}")
    print("")
    
    try:
        response = requests.post(
            f"{BASE_URL}/memories",
            json={
                "messages": [
                    {"role": "user", "content": chinese_input}
                ],
                "user_id": "chinese_user_001"
            },
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        if response.status_code == 201:
            facts = result.get("results", [])
            print(f"✓ 提取了 {len(facts)} 个事实:")
            for idx, fact in enumerate(facts, 1):
                memory = fact.get("memory", "")
                print(f"  {idx}. {memory}")
                # Check if fact contains Chinese characters
                has_chinese = any('\u4e00' <= c <= '\u9fff' for c in memory)
                if has_chinese:
                    print(f"     ✓ 包含中文")
                else:
                    print(f"     ✗ 没有中文 (仅英文)")
        else:
            print(f"✗ Error: {result.get('detail', 'Unknown error')}")
            return False
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection error: {e}")
        return False
    
    # Test 2: Search in Chinese
    print("\n【测试 2】用中文查询")
    print("-" * 70)
    
    query = "这个人使用什么框架"
    print(f"查询: {query}")
    print("")
    
    try:
        response = requests.post(
            f"{BASE_URL}/memories/search",
            json={
                "query": query,
                "user_id": "chinese_user_001",
                "limit": 5
            },
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            results = result.get("results", [])
            if results:
                print(f"✓ 找到 {len(results)} 个相关记忆:")
                for item in results:
                    score = item.get("score", 0)
                    memory = item.get("memory", "")
                    print(f"  [{score:.4f}] {memory}")
            else:
                print("✗ 没有找到结果")
                return False
        else:
            print(f"✗ Error: {result.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Test 3: Get memory details with metadata
    print("\n【测试 3】查看记忆元数据")
    print("-" * 70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/memories?user_id=chinese_user_001",
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            memories = result.get("results", [])
            print(f"✓ 用户有 {len(memories)} 条记忆:")
            for memory in memories:
                content = memory.get("memory", "")
                metadata = memory.get("metadata", {})
                detected_lang = metadata.get("detected_language", "unknown")
                print(f"  • {content}")
                print(f"    检测语言: {detected_lang}")
        else:
            print(f"✗ Error: {result.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✓ 中文测试完成")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_chinese_extraction()
    exit(0 if success else 1)
