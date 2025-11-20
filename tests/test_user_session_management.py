"""
Advanced test script for user session management with UUID-based tracking.
Demonstrates:
- Creating user sessions with unique UUIDs
- Recording multi-turn conversations
- Tracking language preferences
- Session management and queries
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
API_BASE_URL = "http://localhost:8000"

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{Colors.ENDC}\n")

def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")

def print_json(data: Dict, indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def create_user_session(metadata: Dict = None) -> str:
    """Create a new user session and return the user_id."""
    url = f"{API_BASE_URL}/users/session"
    payload = {"metadata": metadata or {}}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            data = response.json()
            user_id = data.get("user_id")
            print_success(f"User session created: {user_id}")
            return user_id
        else:
            print_error(f"Failed to create session: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error creating session: {e}")
        return None

def record_conversation_turn(
    user_id: str,
    message: str,
    language: str = None,
    metadata: Dict = None
) -> Dict:
    """Record a conversation turn for a user."""
    url = f"{API_BASE_URL}/users/{user_id}/conversation-turn"
    payload = {
        "user_id": user_id,
        "message_content": message,
        "language": language,
        "metadata": metadata or {}
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to record turn: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error recording turn: {e}")
        return None

def get_user_session(user_id: str) -> Dict:
    """Get information about a user session."""
    url = f"{API_BASE_URL}/users/{user_id}/session"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to get session: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error getting session: {e}")
        return None

def get_user_memories_summary(user_id: str) -> Dict:
    """Get a summary of memories for a user."""
    url = f"{API_BASE_URL}/users/{user_id}/memories-summary"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to get summary: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error getting summary: {e}")
        return None

def list_all_users() -> Dict:
    """List all active user sessions."""
    url = f"{API_BASE_URL}/users/list"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to list users: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error listing users: {e}")
        return None

def delete_user_session(user_id: str) -> Dict:
    """Delete a user session and all associated memories."""
    url = f"{API_BASE_URL}/users/{user_id}/session"
    
    try:
        response = requests.delete(url)
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to delete session: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error deleting session: {e}")
        return None

def test_user_session_management():
    """Test the user session management API."""
    
    print_section("Advanced User Session Management Test")
    
    # Test 1: Create multiple users with different metadata
    print_section("Test 1: Creating User Sessions")
    
    users = {}
    user_configs = [
        {
            "name": "李四 (Chinese Developer)",
            "country": "China",
            "role": "Software Engineer"
        },
        {
            "name": "John Smith (English Architect)",
            "country": "USA",
            "role": "Software Architect"
        },
        {
            "name": "田中太郎 (Multilingual PM)",
            "country": "Japan",
            "role": "Product Manager"
        }
    ]
    
    for config in user_configs:
        user_id = create_user_session(metadata=config)
        if user_id:
            users[user_id] = config
            print_info(f"Created session for: {config['name']}")
    
    # Test 2: Record conversation turns for each user
    print_section("Test 2: Recording Multi-Turn Conversations")
    
    conversation_data = [
        {
            "user_id": list(users.keys())[0],
            "language": "zh",
            "turns": [
                "我叫李四，今年28岁，在北京的一家互联网公司担任高级软件工程师。",
                "我拥有8年的Python开发经验，主要从事后端系统架构和数据处理。",
                "我的兴趣爱好包括开源贡献、技术写作和篮球。",
                "最近我在学习Rust和分布式系统设计。"
            ]
        },
        {
            "user_id": list(users.keys())[1],
            "language": "en",
            "turns": [
                "My name is John Smith. I'm 32 years old and work as a Solution Architect in San Francisco.",
                "I specialize in cloud architecture, microservices, and DevOps practices. 12 years in tech.",
                "I enjoy hiking, photography, and mentoring junior developers.",
                "Currently exploring Kubernetes advanced patterns and machine learning operations."
            ]
        },
        {
            "user_id": list(users.keys())[2],
            "language": None,  # Auto-detect
            "turns": [
                "こんにちは。田中太郎と申します。東京でプロダクトマネージャーをしています。",
                "I manage a team of 15 engineers and focus on product strategy and user experience.",
                "我最近在参与一个全球范围的产品发布。能与中日美三国的团队合作很有意思！",
                "I'm passionate about user research, data analytics, and cross-cultural communication."
            ]
        }
    ]
    
    for conv_data in conversation_data:
        user_id = conv_data["user_id"]
        user_name = users[user_id].get("name", "Unknown")
        print_info(f"\nProcessing conversation for: {user_name}")
        
        for turn_idx, message in enumerate(conv_data["turns"], 1):
            print(f"  Turn {turn_idx}: {message[:50]}...")
            result = record_conversation_turn(
                user_id=user_id,
                message=message,
                language=conv_data["language"],
                metadata={"turn_number": turn_idx}
            )
            
            if result and result.get("status") == "success":
                turn_info = result.get("session_info", {})
                print_success(
                    f"Recorded - Turn: {turn_info.get('conversation_turns')}, "
                    f"Languages: {turn_info.get('languages')}, "
                    f"Memories: {turn_info.get('total_memories')}"
                )
            
            time.sleep(0.3)
    
    # Test 3: Get user session details
    print_section("Test 3: User Session Details")
    
    for user_id, config in users.items():
        print(f"\n{Colors.BOLD}User: {config['name']}{Colors.ENDC}")
        session_info = get_user_session(user_id)
        if session_info:
            print(f"  Created: {session_info.get('created_at')}")
            print(f"  Last Activity: {session_info.get('last_activity')}")
            print(f"  Conversation Turns: {session_info.get('conversation_turns')}")
            print(f"  Languages: {', '.join(session_info.get('languages', []))}")
            print(f"  Total Memories: {session_info.get('total_memories')}")
    
    # Test 4: Get memories summary
    print_section("Test 4: User Memories Summary")
    
    for user_id, config in users.items():
        print(f"\n{Colors.BOLD}User: {config['name']}{Colors.ENDC}")
        summary = get_user_memories_summary(user_id)
        if summary:
            print(f"  Session Created: {summary.get('session_created')}")
            print(f"  Total Memories: {summary.get('total_memories')}")
            print(f"  Conversation Turns: {summary.get('conversation_turns')}")
            print(f"  Languages Used: {', '.join(summary.get('languages_used', []))}")
            
            # Show first few memory samples
            memory_samples = summary.get('memory_sample', [])
            if memory_samples:
                print(f"  Memory Samples ({len(memory_samples)}):")
                for idx, mem in enumerate(memory_samples[:2], 1):
                    mem_text = mem.get('memory', str(mem))[:60]
                    print(f"    {idx}. {mem_text}...")
    
    # Test 5: List all users
    print_section("Test 5: List All Active Users")
    
    all_users = list_all_users()
    if all_users:
        total = all_users.get("total_users", 0)
        print_success(f"Total active users: {total}")
        
        users_list = all_users.get("users", [])
        print(f"\n{Colors.BOLD}User Summary:{Colors.ENDC}")
        for user in users_list:
            print(f"  ID: {user['user_id'][:16]}...")
            print(f"    Turns: {user['conversation_turns']}, "
                  f"Languages: {', '.join(user['languages']) if user['languages'] else 'None'}, "
                  f"Memories: {user['total_memories']}")
    
    # Test 6: Delete one user session (cleanup)
    print_section("Test 6: Delete User Session")
    
    # Delete the first user
    user_to_delete = list(users.keys())[0]
    config_to_delete = users[user_to_delete]
    print_info(f"Deleting session for: {config_to_delete['name']}")
    
    result = delete_user_session(user_to_delete)
    if result:
        print_success(f"Session deleted: {result.get('message')}")
    
    # Verify deletion
    print_info("Verifying deletion...")
    all_users_after = list_all_users()
    if all_users_after:
        new_total = all_users_after.get("total_users", 0)
        print_success(f"Remaining active users: {new_total}")
    
    # Test 7: Final summary
    print_section("Test Summary")
    
    final_users = list_all_users()
    if final_users:
        print_success(f"Test completed successfully!")
        print(f"Final active user count: {final_users.get('total_users')}")
        
        # Display detailed stats
        total_turns = sum(u['conversation_turns'] for u in final_users.get('users', []))
        total_memories = sum(u['total_memories'] for u in final_users.get('users', []))
        
        print(f"\nOverall Statistics:")
        print(f"  Total Conversation Turns: {total_turns}")
        print(f"  Total Memories: {total_memories}")
        
        # Language statistics
        all_languages = set()
        for user in final_users.get('users', []):
            all_languages.update(user.get('languages', []))
        
        print(f"  Languages Used: {', '.join(all_languages) if all_languages else 'None'}")

if __name__ == "__main__":
    print(f"{Colors.BOLD}Advanced User Session Management Test{Colors.ENDC}")
    print(f"API Base URL: {API_BASE_URL}\n")
    
    test_user_session_management()
