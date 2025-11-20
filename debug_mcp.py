#!/usr/bin/env python
"""调试 MCP Server 返回值"""

import os
import sys
import json

os.environ['ZHIPU_API_KEY'] = 'aa8e1fd415e6414cbe25afc8c713ba56.IJFWPLreK7lZ47g5'

sys.path.insert(0, '.')

from app.personal_assistant import MCPServerClient

try:
    print("=== 测试 MCP Server 客户端 ===")
    mcp = MCPServerClient()
    
    # 先检查健康状态
    print("\n1. 检查 MCP Server 健康状态...")
    health = mcp.health_check()
    print(f"Health check: {health}")
    
    # 创建用户会话
    print("\n2. 创建用户会话...")
    session_result = mcp.create_user_session()
    print(f"Session result type: {type(session_result)}")
    print(f"Session result: {json.dumps(session_result, indent=2, ensure_ascii=False)}")
    
    # 获取所有记忆
    print("\n3. 获取所有记忆...")
    user_id = "test-user-123"
    memories_result = mcp.get_all_memories(user_id, limit=5)
    print(f"Memories result type: {type(memories_result)}")
    print(f"Memories result: {json.dumps(memories_result, indent=2, ensure_ascii=False)}")
    
    # 检查 memories 的结构
    if isinstance(memories_result, dict):
        print(f"\n4. 检查 memories 结构...")
        memories = memories_result.get("memories", [])
        print(f"  memories type: {type(memories)}")
        print(f"  memories: {memories}")
        
except Exception as e:
    import traceback
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
