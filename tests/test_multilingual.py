#!/usr/bin/env python3
"""
Test multilingual memory extraction with automatic language detection
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_multilingual_extraction():
    """Test adding memories in different languages"""
    
    test_cases = [
        {
            "language": "中文 (Chinese)",
            "content": "我叫李四，是一名Python后端工程师，喜欢使用FastAPI框架。",
            "user_id": "user_zh"
        },
        {
            "language": "English",
            "content": "My name is John Smith. I work as a senior software engineer. I love working with Python and Django.",
            "user_id": "user_en"
        },
        {
            "language": "日本語 (Japanese)",
            "content": "私の名前は田中太郎です。ソフトウェアエンジニアとして働いています。Pythonを使うのが好きです。",
            "user_id": "user_ja"
        },
        {
            "language": "한국어 (Korean)",
            "content": "내 이름은 박민수입니다. 저는 소프트웨어 엔지니어로 일하고 있습니다. Python 프로그래밍을 좋아합니다.",
            "user_id": "user_ko"
        },
        {
            "language": "Español (Spanish)",
            "content": "Mi nombre es Carlos García. Soy ingeniero de software. Me encanta trabajar con Python y Django.",
            "user_id": "user_es"
        },
    ]
    
    for test_case in test_cases:
        language = test_case["language"]
        content = test_case["content"]
        user_id = test_case["user_id"]
        
        print("\n" + "=" * 70)
        print(f"Testing: {language}")
        print("=" * 70)
        print(f"Input: {content[:100]}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/memories",
                json={
                    "messages": [
                        {"role": "user", "content": content}
                    ],
                    "user_id": user_id,
                    "metadata": {"language": language}
                },
                timeout=30
            )
        except requests.exceptions.Timeout:
            print("✗ Request timed out (server busy)")
            continue
        except requests.exceptions.ConnectionError as e:
            print(f"✗ Connection error: {e}")
            continue
        
        print(f"\nStatus Code: {response.status_code}")
        result = response.json()
        
        if response.status_code == 201:
            facts = result.get("results", [])
            print(f"✓ Extracted {len(facts)} facts:")
            for idx, fact in enumerate(facts, 1):
                memory = fact.get("memory", "")
                print(f"  {idx}. {memory}")
        else:
            print(f"✗ Error: {result.get('detail', 'Unknown error')}")
        
        # Now search in the same language
        if language == "中文 (Chinese)":
            query = "这个人做什么工作"
        elif language == "日本語 (Japanese)":
            query = "この人の職業は何ですか"
        elif language == "한국어 (Korean)":
            query = "이 사람의 직업은 무엇입니까"
        elif language == "Español (Spanish)":
            query = "¿Cuál es la profesión de esta persona?"
        else:
            query = "What is this person's job?"
        
        print(f"\nSearching with: {query}")
        try:
            search_response = requests.post(
                f"{BASE_URL}/memories/search",
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": 3
                },
                timeout=30
            )
        except requests.exceptions.Timeout:
            print("✗ Search request timed out")
            continue
        except requests.exceptions.ConnectionError as e:
            print(f"✗ Search connection error: {e}")
            continue
        
        if search_response.status_code == 200:
            search_result = search_response.json()
            results = search_result.get("results", [])
            if results:
                print("✓ Search results:")
                for item in results:
                    score = item.get("score", 0)
                    memory = item.get("memory", "")
                    print(f"  [{score:.4f}] {memory}")
            else:
                print("No results found")
        else:
            print(f"Search error: {search_response.json()}")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Multilingual Memory Extraction Test")
    print("=" * 70)
    test_multilingual_extraction()
    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)
