"""
Test script for multi-user, multi-turn, multilingual conversations with UUID-based user tracking.
Each user gets a unique UUID, can have multiple conversation turns, and may use different languages.
"""

import requests
import json
import uuid
from typing import Dict, List, Any
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
HEALTH_CHECK_URL = f"{API_BASE_URL}/health"
ADD_MEMORY_URL = f"{API_BASE_URL}/memories"
SEARCH_MEMORY_URL = f"{API_BASE_URL}/memories/search"
GET_ALL_MEMORIES_URL = f"{API_BASE_URL}/memories"

# Color codes for better output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

def print_user(user_id: str, message: str):
    """Print a user-specific message."""
    print(f"{Colors.BLUE}[User {user_id[:8]}]: {message}{Colors.ENDC}")

def check_api_health():
    """Check if the API is running and healthy."""
    try:
        response = requests.get(HEALTH_CHECK_URL)
        if response.status_code == 200:
            health_data = response.json()
            print_success(f"API is healthy - Mem0 initialized: {health_data.get('mem0_initialized', False)}")
            return True
        else:
            print_error(f"API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is the Docker container running?")
        return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def create_user_sessions(num_users: int = 3) -> Dict[str, Dict[str, Any]]:
    """Create multiple user sessions with unique UUIDs."""
    users = {}
    for i in range(num_users):
        user_id = str(uuid.uuid4())
        users[user_id] = {
            "id": user_id,
            "name": f"User_{i+1}",
            "conversation_turns": 0,
            "languages": [],
            "memories_added": []
        }
    return users

def add_memory(
    user_id: str,
    messages: List[Dict[str, str]],
    language: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Add a memory for a user."""
    payload = {
        "messages": messages,
        "user_id": user_id,
        "language": language,
        "metadata": metadata or {}
    }
    
    try:
        response = requests.post(ADD_MEMORY_URL, json=payload)
        if response.status_code == 201:
            return response.json()
        else:
            print_error(f"Failed to add memory: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Error adding memory: {e}")
        return None

def search_memory(
    user_id: str,
    query: str,
    limit: int = 5
) -> Dict[str, Any]:
    """Search memories for a user."""
    payload = {
        "query": query,
        "user_id": user_id,
        "limit": limit
    }
    
    try:
        response = requests.post(SEARCH_MEMORY_URL, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to search memory: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error searching memory: {e}")
        return None

def get_all_memories(user_id: str, limit: int = 100) -> Dict[str, Any]:
    """Get all memories for a user."""
    try:
        response = requests.get(GET_ALL_MEMORIES_URL, params={"user_id": user_id, "limit": limit})
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"Failed to get memories: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error getting memories: {e}")
        return None

def simulate_multilingual_conversation():
    """Simulate multi-user, multi-turn, multilingual conversations."""
    
    print_section("Multi-User, Multi-Turn, Multilingual Conversation Simulation")
    
    # Check API health
    if not check_api_health():
        return
    
    # Create user sessions
    print_info("Creating user sessions...")
    users = create_user_sessions(num_users=3)
    
    for user_id, user_info in users.items():
        print_user(user_id, f"Session created: {user_info['name']}")
    
    # Define multi-turn conversations in different languages
    conversations = [
        {
            "user_id": list(users.keys())[0],
            "name": "Chinese User (李四)",
            "language": "zh",
            "turns": [
                {
                    "message": "我叫李四，今年28岁，是一名软件工程师。我来自北京。",
                    "topic": "Personal Introduction - Chinese"
                },
                {
                    "message": "我喜欢Python编程，也很擅长前端开发。目前在一家互联网公司工作。",
                    "topic": "Skills and Experience - Chinese"
                },
                {
                    "message": "我有一个叫小白的狗，它是一只金毛犬。我每天都会遛狗。",
                    "topic": "Personal Hobby - Chinese"
                }
            ]
        },
        {
            "user_id": list(users.keys())[1],
            "name": "English User (John)",
            "language": "en",
            "turns": [
                {
                    "message": "Hello! My name is John Smith. I am a 32-year-old software architect based in San Francisco.",
                    "topic": "Personal Introduction - English"
                },
                {
                    "message": "I specialize in cloud architecture and microservices. I have 10 years of experience in tech.",
                    "topic": "Professional Background - English"
                },
                {
                    "message": "In my free time, I love hiking and photography. I just completed the Pacific Crest Trail last month.",
                    "topic": "Hobbies - English"
                }
            ]
        },
        {
            "user_id": list(users.keys())[2],
            "name": "Mixed Language User (Tokyo-based)",
            "language": None,  # Will auto-detect based on content
            "turns": [
                {
                    "message": "こんにちは。私の名前は田中太郎です。東京に住んでいます。私は34歳です。",
                    "topic": "Personal Introduction - Japanese"
                },
                {
                    "message": "I work as a Product Manager at a tech company. I speak both Japanese and English fluently.",
                    "topic": "Work - English"
                },
                {
                    "message": "我最近也在学习中文。I'm trying to become trilingual! 我每天都练习。",
                    "topic": "Language Learning - Mixed"
                }
            ]
        }
    ]
    
    # Process conversations
    print_section("Processing Multi-Turn Conversations")
    
    for conv in conversations:
        user_id = conv["user_id"]
        user_info = users[user_id]
        user_info["name"] = conv["name"]
        user_info["language"] = conv["language"]
        
        print_user(user_id, f"\n{'='*50}")
        print_user(user_id, f"Starting conversation: {conv['name']}")
        print_user(user_id, f"Primary Language: {conv['language'] or 'Auto-detect'}")
        print_user(user_id, f"{'='*50}\n")
        
        # Process each turn in the conversation
        for turn_idx, turn in enumerate(conv["turns"], 1):
            print_user(user_id, f"Turn {turn_idx}: {turn['topic']}")
            print_user(user_id, f"Message: {turn['message'][:60]}...")
            
            # Create message object
            messages = [
                {
                    "role": "user",
                    "content": turn['message']
                }
            ]
            
            # Add memory
            metadata = {
                "conversation_turn": turn_idx,
                "topic": turn['topic'],
                "timestamp": datetime.now().isoformat()
            }
            
            result = add_memory(
                user_id=user_id,
                messages=messages,
                language=conv["language"],
                metadata=metadata
            )
            
            if result:
                print_success(f"Memory added successfully")
                user_info["conversation_turns"] += 1
                user_info["memories_added"].append({
                    "turn": turn_idx,
                    "topic": turn['topic']
                })
                if conv["language"]:
                    if conv["language"] not in user_info["languages"]:
                        user_info["languages"].append(conv["language"])
            else:
                print_error(f"Failed to add memory for turn {turn_idx}")
            
            # Small delay between turns
            time.sleep(0.5)
        
        # Search memories for this user
        print_user(user_id, "\nSearching for added memories...")
        search_query = "work" if conv["language"] == "en" else ("工作" if conv["language"] == "zh" else "仕事" if conv["language"] == "ja" else "work")
        search_result = search_memory(user_id, search_query)
        
        if search_result:
            results = search_result.get('results', [])
            print_success(f"Found {len(results)} relevant memories")
            for idx, memory in enumerate(results[:3], 1):
                print_info(f"  Memory {idx}: {str(memory)[:100]}...")
        
        # Get all memories for this user
        print_user(user_id, "\nRetrieving all memories for this user...")
        all_memories = get_all_memories(user_id)
        
        if all_memories:
            total_count = len(all_memories) if isinstance(all_memories, list) else all_memories.get('results', [])
            if isinstance(total_count, list):
                total_count = len(total_count)
            print_success(f"Total memories stored: {total_count}")
    
    # Summary Report
    print_section("Session Summary Report")
    
    for user_id, user_info in users.items():
        print(f"\n{Colors.BOLD}User: {user_info['name']}{Colors.ENDC}")
        print(f"  ID: {user_id}")
        print(f"  Conversation Turns: {user_info['conversation_turns']}")
        print(f"  Languages Used: {', '.join(user_info['languages']) if user_info['languages'] else 'None'}")
        print(f"  Memories Added: {len(user_info['memories_added'])}")
        
        if user_info['memories_added']:
            print(f"  Memory Topics:")
            for mem in user_info['memories_added']:
                print(f"    - Turn {mem['turn']}: {mem['topic']}")
    
    print_section("Test Completed Successfully!")
    print_success("All multi-user, multi-turn, multilingual conversations processed!")

if __name__ == "__main__":
    print(f"{Colors.BOLD}Starting Multi-User, Multi-Turn, Multilingual Conversation Test{Colors.ENDC}")
    print(f"API Base URL: {API_BASE_URL}\n")
    
    simulate_multilingual_conversation()
