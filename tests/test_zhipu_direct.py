#!/usr/bin/env python3
"""
Direct test of Zhipu AI API to verify the configuration works.
"""
import os
import requests
import json
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent.parent / "app" / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

def test_zhipu_api():
    """Test Zhipu AI API directly."""
    print("=" * 60)
    print("Zhipu AI API Direct Test")
    print("=" * 60)
    
    url = f"{ZHIPU_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4-flash-250414",
        "messages": [
            {
                "role": "user",
                "content": "你好，请简单介绍一下自己。"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    print(f"\nURL: {url}")
    print(f"Headers: Authorization: Bearer ***")
    print(f"Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            print("\n✓ Zhipu AI API is working correctly!")
            return True
        else:
            print(f"\n✗ Zhipu AI API returned error code {response.status_code}")
            return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_zhipu_api()
