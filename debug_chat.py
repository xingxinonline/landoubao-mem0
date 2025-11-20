#!/usr/bin/env python
"""调试chat函数的问题"""

import os
import sys
import traceback

# 设置环境变量
os.environ['ZHIPU_API_KEY'] = 'aa8e1fd415e6414cbe25afc8c713ba56.IJFWPLreK7lZ47g5'

sys.path.insert(0, '.')

from app.personal_assistant import PersonalAssistant

try:
    print("=== 步骤1: 创建PersonalAssistant ===")
    api_key = os.getenv("ZHIPU_API_KEY", "").strip()
    print(f"API Key from env: {api_key[:10]}...")
    
    assistant = PersonalAssistant(api_key=api_key)
    print(f"✓ PersonalAssistant created successfully")
    print(f"  LLM Client: {assistant.llm_client}")
    print(f"  Model: {assistant.model}")
    
    print("\n=== 步骤2: 加载记忆 ===")
    assistant.load_memories(limit=5)
    
    print("\n=== 步骤3: 调用 chat 方法 ===")
    try:
        response = assistant.chat("你好，今天天气如何？")
        print(f"✓ Chat successful!")
        print(f"Response: {response[:200]}...")
    except Exception as e:
        print(f"✗ Chat failed: {e}")
        traceback.print_exc()
        
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
