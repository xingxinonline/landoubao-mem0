import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    print(f"\n=== {title} ===")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

def main():
    # 1. 健康检查
    resp = requests.get(f"{BASE_URL}/health")
    print_response("健康检查", resp)

    # 用户 ID
    user_id = "developer_001"

    # 2. 添加记忆 (Add Memory)
    print(f"\n正在为用户 {user_id} 添加记忆...")
    add_payload = {
        "messages": [
            {"role": "user", "content": "我叫李四，是一名Python后端工程师，喜欢使用FastAPI框架。"}
        ],
        "user_id": user_id,
        "metadata": {"category": "profile"}
    }
    resp = requests.post(f"{BASE_URL}/memories", json=add_payload)
    print_response("添加记忆结果", resp)

    # 3. 搜索记忆 (Search Memory)
    query = "李四是做什么的？"
    print(f"\n正在搜索: {query}")
    search_payload = {
        "query": query,
        "user_id": user_id,
        "limit": 3
    }
    resp = requests.post(f"{BASE_URL}/memories/search", json=search_payload)
    print_response("搜索记忆结果", resp)

    # 4. 获取所有记忆 (Get All Memories)
    print(f"\n获取用户 {user_id} 的所有记忆...")
    resp = requests.get(f"{BASE_URL}/memories", params={"user_id": user_id})
    print_response("所有记忆", resp)

    # 5. 删除记忆 (演示，需要具体的 memory_id，这里先不执行实际删除，或者先获取ID再删除)
    # if resp.status_code == 200:
    #     memories = resp.json()
    #     if memories:
    #         mem_id = memories[0]['id']
    #         print(f"\n删除记忆 ID: {mem_id}")
    #         del_resp = requests.delete(f"{BASE_URL}/memories/{mem_id}")
    #         print_response("删除结果", del_resp)

if __name__ == "__main__":
    main()
