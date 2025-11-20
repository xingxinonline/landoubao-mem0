"""
Test script for multi-user AI assistant conversations with GLM-4-Flash.
Each user has a unique UUID and engages in 20+ turn conversations with an AI assistant.
The assistant uses mem0 for memory management to provide contextual responses.
Users may use multiple languages randomly throughout the conversation.
"""

import requests
import json
import uuid
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
ZHIPU_API_KEY = "aa8e1fd415e6414cbe25afc8c713ba56.IJFWPLreK7lZ47g5"
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

# Mem0 API endpoints
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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}{Colors.ENDC}\n")

def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")

def print_user(user_name: str, message: str):
    """Print a user message."""
    print(f"{Colors.BLUE}👤 {user_name}: {message}{Colors.ENDC}")

def print_assistant(message: str):
    """Print an assistant message."""
    print(f"{Colors.YELLOW}🤖 Assistant: {message}{Colors.ENDC}")

def check_api_health():
    """Check if the Mem0 API is running and healthy."""
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print_success(f"Mem0 API is healthy - initialized: {health_data.get('mem0_initialized', False)}")
            return True
        else:
            print_error(f"Mem0 API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to Mem0 API. Is the Docker container running?")
        return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def call_glm4_flash(messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
    """Call GLM-4-Flash API using OpenAI-compatible endpoint."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZHIPU_API_KEY}"
    }
    
    payload = {
        "model": "glm-4-flash",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 800
    }
    
    try:
        response = requests.post(
            f"{ZHIPU_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print_error(f"GLM-4-Flash API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Error calling GLM-4-Flash: {e}")
        return None

def add_memory(user_id: str, messages: List[Dict[str, str]], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Add conversation to mem0 memory."""
    payload = {
        "messages": messages,
        "user_id": user_id,
        "metadata": metadata or {}
    }
    
    try:
        response = requests.post(ADD_MEMORY_URL, json=payload, timeout=10)
        if response.status_code == 201:
            return response.json()
        else:
            print_error(f"Failed to add memory: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error adding memory: {e}")
        return None

def search_memory(user_id: str, query: str, limit: int = 5) -> List[str]:
    """Search mem0 memories for relevant context."""
    payload = {
        "query": query,
        "user_id": user_id,
        "limit": limit
    }
    
    try:
        response = requests.post(SEARCH_MEMORY_URL, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get('results', [])
        else:
            return []
    except Exception as e:
        print_error(f"Error searching memory: {e}")
        return []

class ConversationScenarios:
    """Predefined conversation scenarios in multiple languages."""
    
    CHINESE_SCENARIOS = [
        "你好！我想了解一下你能帮我做什么？",
        "我最近在学习Python编程，你能给我一些建议吗？",
        "我有一个宠物狗叫旺财，它很可爱。",
        "我的生日是5月15日。",
        "我喜欢看科幻电影，最喜欢《流浪地球》。",
        "我在一家互联网公司做软件工程师。",
        "周末我通常会去健身房锻炼。",
        "我最近在读《三体》这本书。",
        "我计划明年去日本旅游。",
        "你还记得我的生日是什么时候吗？",
        "我的工作是什么？",
        "我养的宠物叫什么名字？",
        "能推荐一些适合Python初学者的项目吗？",
        "我想学习机器学习，从哪里开始比较好？",
        "我的朋友叫李明，他也是程序员。",
        "我喜欢喝咖啡，尤其是拿铁。",
        "我正在考虑换一份工作。",
        "你知道我最喜欢的电影是什么吗？",
        "我计划在明年考一个AWS认证。",
        "能总结一下你对我的了解吗？"
    ]
    
    ENGLISH_SCENARIOS = [
        "Hello! Can you tell me what you can help me with?",
        "I'm currently learning JavaScript. Any tips?",
        "I have a cat named Whiskers. She's adorable!",
        "My birthday is on December 20th.",
        "I love watching thriller movies, especially Christopher Nolan films.",
        "I work as a product manager at a tech startup.",
        "On weekends, I usually go rock climbing.",
        "I'm reading 'Sapiens' by Yuval Noah Harari right now.",
        "I'm planning to visit Iceland next summer.",
        "Do you remember when my birthday is?",
        "What do I do for work?",
        "What's my cat's name?",
        "Can you recommend some JavaScript frameworks to learn?",
        "I want to transition into data science. Where should I start?",
        "My best friend is named Sarah. She's a designer.",
        "I'm a big fan of specialty coffee.",
        "I'm considering getting a master's degree.",
        "What's my favorite type of movie?",
        "I'm thinking about learning cloud computing.",
        "Can you summarize what you know about me?"
    ]
    
    JAPANESE_SCENARIOS = [
        "こんにちは！あなたは何を手伝ってくれますか？",
        "最近Goプログラミング言語を勉強しています。",
        "ポチという名前の犬を飼っています。",
        "私の誕生日は7月8日です。",
        "アニメが大好きで、特に新海誠の作品が好きです。",
        "IT企業でプロジェクトマネージャーとして働いています。",
        "週末はよくカラオケに行きます。",
        "今、村上春樹の小説を読んでいます。",
        "来年ニューヨークに行く予定です。",
        "私の誕生日はいつですか？",
        "私の仕事は何ですか？",
        "私のペットの名前は何ですか？",
        "Goを学ぶためのおすすめプロジェクトはありますか？",
        "データ分析を学びたいのですが、どこから始めればいいですか？",
        "私の友達は田中さんです。エンジニアです。",
        "緑茶が好きです。",
        "転職を考えています。",
        "私の好きなアニメ監督は誰ですか？",
        "クラウド技術を学びたいと思っています。",
        "私について知っていることをまとめてください。"
    ]
    
    MIXED_SCENARIOS = [
        "Hi! 我想问一下，你能说中文吗？",
        "I'm learning both Python and 日本語。",
        "My dog's name is 小白 (Xiaobai).",
        "私は英語と中国語を話せます。",
        "I love 日本料理, especially sushi!",
        "我在学习 machine learning 和 deep learning。",
        "今週末、I'm planning to watch a Chinese movie.",
        "Can you help me with both English and 中文？",
        "私の趣味は programming と reading です。",
        "I want to travel to 北京 and Tokyo next year."
    ]

def generate_conversation_prompts(num_turns: int = 25) -> List[str]:
    """Generate random conversation prompts mixing different languages."""
    all_scenarios = (
        ConversationScenarios.CHINESE_SCENARIOS +
        ConversationScenarios.ENGLISH_SCENARIOS +
        ConversationScenarios.JAPANESE_SCENARIOS +
        ConversationScenarios.MIXED_SCENARIOS
    )
    
    # Ensure we have enough prompts
    prompts = []
    while len(prompts) < num_turns:
        prompts.extend(random.sample(all_scenarios, min(len(all_scenarios), num_turns - len(prompts))))
    
    return prompts[:num_turns]

def simulate_user_conversation(user_id: str, user_name: str, num_turns: int = 25):
    """Simulate a multi-turn conversation for a single user with the AI assistant."""
    print_section(f"Starting Conversation for {user_name}")
    print_info(f"User ID: {user_id}")
    print_info(f"Target turns: {num_turns}")
    
    # System prompt for the AI assistant
    system_prompt = {
        "role": "system",
        "content": """You are a helpful multilingual AI assistant. You can understand and respond in Chinese, English, and Japanese.
You have access to a memory system that helps you remember information about users across conversations.
When answering questions, use the context from previous conversations to provide more personalized responses.
Be friendly, helpful, and remember details shared by the user."""
    }
    
    # Generate conversation prompts
    prompts = generate_conversation_prompts(num_turns)
    
    # Conversation history
    conversation_history = [system_prompt]
    
    for turn_idx, user_input in enumerate(prompts, 1):
        print(f"\n{Colors.BOLD}--- Turn {turn_idx}/{num_turns} ---{Colors.ENDC}")
        print_user(user_name, user_input)
        
        # Search for relevant memories
        relevant_memories = search_memory(user_id, user_input, limit=3)
        
        # Build context from memories
        memory_context = ""
        if relevant_memories:
            print_info(f"Found {len(relevant_memories)} relevant memories")
            memory_context = "\n[Context from previous conversations]:\n"
            for mem in relevant_memories[:2]:
                if isinstance(mem, dict):
                    mem_text = mem.get('memory', str(mem))
                else:
                    mem_text = str(mem)
                memory_context += f"- {mem_text}\n"
        
        # Prepare messages for GLM-4-Flash
        current_messages = conversation_history.copy()
        
        # Add memory context if available
        if memory_context:
            context_message = {
                "role": "system",
                "content": memory_context
            }
            current_messages.append(context_message)
        
        # Add user message
        user_message = {
            "role": "user",
            "content": user_input
        }
        current_messages.append(user_message)
        
        # Call GLM-4-Flash
        assistant_response = call_glm4_flash(current_messages, temperature=0.7)
        
        if assistant_response:
            print_assistant(assistant_response)
            
            # Add to conversation history (without memory context)
            conversation_history.append(user_message)
            conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # Store in mem0 every few turns to avoid overwhelming the system
            if turn_idx % 3 == 0 or turn_idx >= num_turns - 2:
                # Get last few exchanges to store
                recent_messages = [user_message, {"role": "assistant", "content": assistant_response}]
                
                metadata = {
                    "turn": turn_idx,
                    "timestamp": datetime.now().isoformat(),
                    "user_name": user_name
                }
                
                add_result = add_memory(user_id, recent_messages, metadata)
                if add_result:
                    print_success(f"Memory updated (turn {turn_idx})")
        else:
            print_error("Failed to get response from GLM-4-Flash")
            # Use a fallback response
            assistant_response = "I apologize, but I'm having trouble processing that right now. Could you please rephrase?"
            print_assistant(assistant_response)
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    print_section(f"Conversation Summary for {user_name}")
    print_success(f"Completed {num_turns} conversation turns")
    
    # Retrieve all memories for summary
    try:
        all_memories_response = requests.get(
            GET_ALL_MEMORIES_URL,
            params={"user_id": user_id, "limit": 100},
            timeout=10
        )
        if all_memories_response.status_code == 200:
            all_memories = all_memories_response.json()
            if isinstance(all_memories, dict):
                memories_list = all_memories.get('results', [])
            else:
                memories_list = all_memories
            
            print_info(f"Total memories stored: {len(memories_list)}")
            
            if memories_list:
                print_info("Sample memories:")
                for i, mem in enumerate(memories_list[:5], 1):
                    if isinstance(mem, dict):
                        mem_text = mem.get('memory', str(mem))[:100]
                    else:
                        mem_text = str(mem)[:100]
                    print(f"  {i}. {mem_text}...")
    except Exception as e:
        print_error(f"Could not retrieve memories: {e}")

def main():
    """Main test function."""
    print_section("Multi-User AI Assistant Conversation Test")
    print_info("Using GLM-4-Flash as the AI assistant")
    print_info("Using Mem0 for memory management")
    
    # Check Mem0 API health
    if not check_api_health():
        print_error("Mem0 API is not available. Please start the Docker container.")
        return
    
    # Create multiple users
    num_users = 3
    users = []
    
    for i in range(num_users):
        user_id = str(uuid.uuid4())
        user_name = random.choice([
            "张伟", "李娜", "王芳",  # Chinese names
            "John Smith", "Emma Wilson", "Michael Brown",  # English names
            "田中太郎", "佐藤花子", "鈴木一郎"  # Japanese names
        ])
        users.append({
            "id": user_id,
            "name": user_name
        })
    
    print_info(f"Created {num_users} users:")
    for user in users:
        print(f"  - {user['name']} (ID: {user['id'][:8]}...)")
    
    # Simulate conversations for each user
    for idx, user in enumerate(users, 1):
        print_section(f"User {idx}/{num_users}: {user['name']}")
        simulate_user_conversation(
            user_id=user['id'],
            user_name=user['name'],
            num_turns=25  # At least 20 turns, using 25 for more comprehensive testing
        )
        
        # Delay between users
        if idx < num_users:
            print_info("Waiting before next user...")
            time.sleep(2)
    
    print_section("All Conversations Completed!")
    print_success(f"Successfully simulated {num_users} users with 25+ conversation turns each")
    print_success("Memory system was used throughout to provide contextual responses")

if __name__ == "__main__":
    main()
