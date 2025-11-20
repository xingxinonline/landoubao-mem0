#!/usr/bin/env python3
"""
智能记忆管理私人助理 - 改进版
Advanced Personal Assistant with Smart Memory Management

核心改进：
1. 记忆存储/更新/查询由LLM决策（不是每句话都触发）
2. 时间衰减机制（权重随时间降低）
3. 事件驱动更新（冲突、强化、回忆）
4. 模糊化层次（完整 → 摘要 → 标签）
5. 双层记忆架构（短期上下文 + 长期记忆）
"""

import requests
import json
import time
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 配置
BASE_URL = "http://localhost:8000"
ZHIPU_API_KEY = ""
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 读取API key
try:
    env_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('ZHIPU_API_KEY='):
                    ZHIPU_API_KEY = line.split('=', 1)[1].strip()
                    break
except Exception as e:
    print(f"Warning: Could not read API key: {e}")


class MemoryAction(Enum):
    """记忆操作类型"""
    STORE = "store"          # 存储新记忆
    UPDATE = "update"        # 更新现有记忆
    QUERY = "query"          # 查询记忆
    STRENGTHEN = "strengthen"  # 强化记忆
    IGNORE = "ignore"        # 忽略（不操作）


class MemoryLevel(Enum):
    """记忆清晰度层次 - 五层架构"""
    FULL = "full"           # 完整记忆（权重 > 0.7）
    SUMMARY = "summary"     # 摘要化（0.3 ≤ 权重 ≤ 0.7）
    TAG = "tag"             # 模糊标签（0.1 ≤ 权重 < 0.3）
    TRACE = "trace"         # 痕迹记忆（0.01 ≤ 权重 < 0.1）
    ARCHIVE = "archive"     # 存档记忆（权重 ≤ 0.01，不参与普通检索）


@dataclass
class MemoryItem:
    """记忆项"""
    content: str
    timestamp: str
    weight: float = 1.0
    level: MemoryLevel = MemoryLevel.FULL
    user_id: str = ""
    memory_id: str = ""


class MemoryDecayCalculator:
    """记忆衰减计算器"""
    
    def __init__(self, alpha: float = 0.01):
        """
        初始化衰减计算器
        
        Args:
            alpha: 衰减系数，越大衰减越快
        """
        self.alpha = alpha
    
    def calculate_weight(self, initial_weight: float, days_passed: float) -> float:
        """
        计算时间衰减后的权重
        
        公式: w(t) = w0 / (1 + α * t)
        
        Args:
            initial_weight: 初始权重
            days_passed: 经过的天数
            
        Returns:
            衰减后的权重
        """
        return initial_weight / (1 + self.alpha * days_passed)
    
    def get_memory_level(self, weight: float) -> MemoryLevel:
        """
        根据权重判断记忆清晰度层次 - 五层架构
        
        > 0.7     : full    - 完整保留原文
        0.3 ~ 0.7 : summary - 摘要化
        0.1 ~ 0.3 : tag     - 模糊化标签
        0.03 ~ 0.1: trace   - 痕迹记忆
        ≤ 0.03    : archive - 存档（不参与普通检索）
        """
        if weight > 0.7:
            return MemoryLevel.FULL
        elif weight >= 0.3:
            return MemoryLevel.SUMMARY
        elif weight >= 0.1:
            return MemoryLevel.TAG
        elif weight >= 0.03:
            return MemoryLevel.TRACE
        else:
            return MemoryLevel.ARCHIVE


class SmartMemoryAssistant:
    """智能记忆助理"""
    
    def __init__(self, mem0_url: str, llm_api_key: str):
        self.mem0_url = mem0_url
        self.llm_api_key = llm_api_key
        self.llm_url = ZHIPU_API_URL
        self.decay_calculator = MemoryDecayCalculator(alpha=0.01)
        
        # 短期上下文（当前会话）
        self.short_term_context: Dict[str, List[Dict[str, str]]] = {}
    
    def call_llm(self, messages: List[Dict[str, str]], 
                 system_prompt: str = None) -> str:
        """调用LLM"""
        try:
            full_messages = []
            if system_prompt:
                full_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            full_messages.extend(messages)
            
            response = requests.post(
                self.llm_url,
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4-flash",
                    "messages": full_messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"LLM error: {response.status_code}")
                return ""
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return ""
    
    def decide_memory_action(self, user_id: str, user_message: str, 
                            conversation_history: List[Dict[str, str]]) -> Tuple[MemoryAction, str, bool]:
        """
        让LLM决策是否需要记忆操作
        
        Returns:
            (操作类型, 操作原因/内容, 是否回顾模式)
        """
        system_prompt = """你是一个记忆管理专家。分析用户消息，判断是否需要记忆操作。

记忆操作类型：
1. STORE - 存储新记忆（用户表达偏好、提供身份信息、设定目标等）
2. UPDATE - 更新记忆（用户修改偏好、纠正事实等）
3. QUERY - 查询记忆（用户提问需要历史信息、请求回顾等）
4. STRENGTHEN - 强化记忆（用户重复或强调某事）
5. IGNORE - 忽略（普通闲聊、不需要记忆的内容）

回顾模式触发词：
- 回顾、以前、过去、历史、很久以前、曾经、十年前、早期

请分析用户消息，返回JSON格式：
{
    "action": "STORE/UPDATE/QUERY/STRENGTHEN/IGNORE",
    "reason": "操作原因",
    "key_info": "需要记忆的关键信息（如果有）",
    "review_mode": true/false  # 是否进入回顾模式
}

示例：
用户："我喜欢喝咖啡" → {"action": "STORE", "reason": "用户偏好", "key_info": "喜欢喝咖啡", "review_mode": false}
用户："你好" → {"action": "IGNORE", "reason": "普通问候", "review_mode": false}
用户："我以前说过什么？" → {"action": "QUERY", "reason": "回顾历史", "key_info": "", "review_mode": true}
"""
        
        messages = [
            {"role": "user", "content": f"用户消息：{user_message}\n\n请分析并返回JSON。"}
        ]
        
        response = self.call_llm(messages, system_prompt)
        
        try:
            # 尝试解析JSON
            # 提取JSON部分（去除markdown代码块）
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response)
            action = MemoryAction(result["action"].lower())
            reason = result.get("reason", "")
            key_info = result.get("key_info", "")
            review_mode = result.get("review_mode", False)
            
            return action, key_info if key_info else reason, review_mode
        except Exception as e:
            print(f"解析LLM决策失败: {e}, response: {response}")
            # 默认策略：包含问号则查询，否则忽略
            if "?" in user_message or "吗" in user_message or "什么" in user_message:
                return MemoryAction.QUERY, "", False
            return MemoryAction.IGNORE, "", False
    
    def add_memory_with_metadata(self, user_id: str, content: str, 
                                 weight: float = 1.0) -> Dict[str, Any]:
        """添加记忆（带元数据）"""
        try:
            timestamp = datetime.now().isoformat()
            
            response = requests.post(
                f"{self.mem0_url}/memories",
                json={
                    "messages": [{"role": "user", "content": content}],
                    "user_id": user_id,
                    "metadata": {
                        "timestamp": timestamp,
                        "weight": weight,
                        "level": MemoryLevel.FULL.value
                    }
                },
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json()
            return {"results": []}
        except Exception as e:
            print(f"Error adding memory: {e}")
            return {"results": []}
    
    def search_memory_with_decay(self, user_id: str, query: str, 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """搜索记忆（应用时间衰减）"""
        try:
            response = requests.post(
                f"{self.mem0_url}/memories/search",
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": limit
                },
                timeout=30
            )
            
            if response.status_code == 200:
                memories = response.json().get("results", [])
                
                # 应用时间衰减
                now = datetime.now()
                for mem in memories:
                    metadata = mem.get("metadata", {})
                    timestamp_str = metadata.get("timestamp", "")
                    initial_weight = float(metadata.get("weight", 1.0))
                    
                    if timestamp_str:
                        try:
                            mem_time = datetime.fromisoformat(timestamp_str)
                            days_passed = (now - mem_time).total_seconds() / 86400
                            
                            # 计算衰减后的权重
                            current_weight = self.decay_calculator.calculate_weight(
                                initial_weight, days_passed
                            )
                            mem["current_weight"] = current_weight
                            mem["memory_level"] = self.decay_calculator.get_memory_level(
                                current_weight
                            ).value
                        except:
                            mem["current_weight"] = initial_weight
                            mem["memory_level"] = MemoryLevel.FULL.value
                    else:
                        mem["current_weight"] = initial_weight
                        mem["memory_level"] = MemoryLevel.FULL.value
                
                return memories
            return []
        except Exception as e:
            print(f"Error searching memory: {e}")
            return []
    
    def format_memory_for_context(self, memories: List[Dict[str, Any]], 
                                 review_mode: bool = False) -> str:
        """
        根据记忆层次格式化上下文
        
        Args:
            memories: 记忆列表
            review_mode: 是否为回顾模式（True=显示所有层次，False=只显示高权重）
        """
        context_lines = []
        
        for mem in memories:
            content = mem.get("memory", "")
            level = mem.get("memory_level", MemoryLevel.FULL.value)
            weight = mem.get("current_weight", 1.0)
            
            # 普通模式：只显示完整和摘要记忆（权重 > 0.3）
            if not review_mode and weight < 0.3:
                continue
            
            # 根据层次格式化
            if level == MemoryLevel.FULL.value:
                context_lines.append(f"✓ {content}")
            elif level == MemoryLevel.SUMMARY.value:
                context_lines.append(f"~ {content}（较早前的印象）")
            elif level == MemoryLevel.TAG.value:
                context_lines.append(f"· {content}（模糊的记忆）")
            elif level == MemoryLevel.TRACE.value:
                context_lines.append(f"👣 {content}")
            elif level == MemoryLevel.ARCHIVE.value:
                context_lines.append(f"📦 {content}")
        
        return "\n".join(context_lines) if context_lines else "暂无相关记忆"
    
    def process_conversation(self, user_id: str, user_message: str) -> str:
        """处理对话（智能记忆管理）"""
        
        # 1. 初始化短期上下文
        if user_id not in self.short_term_context:
            self.short_term_context[user_id] = []
        
        # 添加到短期上下文
        self.short_term_context[user_id].append({
            "role": "user",
            "content": user_message
        })
        
        # 2. LLM决策：是否需要记忆操作
        print(f"    🤔 分析记忆需求...")
        action, info, review_mode = self.decide_memory_action(
            user_id, user_message, self.short_term_context[user_id]
        )
        
        if review_mode:
            print(f"    📋 决策: {action.value} - {info} [🔍 回顾模式]")
        else:
            print(f"    📋 决策: {action.value} - {info}")
        
        # 3. 执行记忆操作
        memory_context = ""
        
        if action == MemoryAction.STORE:
            print(f"    💾 存储记忆: {info}")
            result = self.add_memory_with_metadata(user_id, user_message)
            if result.get("results"):
                print(f"    ✓ 已存储 {len(result['results'])} 条记忆")
        
        elif action == MemoryAction.QUERY:
            if review_mode:
                print(f"    🔍 查询记忆（回顾模式 - 包含低权重记忆）...")
            else:
                print(f"    🔍 查询记忆（普通模式 - 仅高权重记忆）...")
            
            memories = self.search_memory_with_decay(user_id, user_message, limit=20)
            
            if review_mode:
                # 回顾模式：显示所有层次的记忆
                all_memories = memories
            else:
                # 普通模式：只显示权重 > 0.3 的记忆
                all_memories = [m for m in memories if m.get("current_weight", 0) >= 0.3]
            
            if all_memories:
                print(f"    ✓ 找到 {len(all_memories)} 条相关记忆")
                memory_context = self.format_memory_for_context(all_memories, review_mode)
                print(f"    📚 记忆上下文:\n{memory_context}")
            else:
                print(f"    ℹ️  未找到相关记忆")
        
        elif action == MemoryAction.UPDATE:
            print(f"    🔄 更新记忆: {info}")
            # 先查询现有记忆
            memories = self.search_memory_with_decay(user_id, info, limit=5)
            if memories:
                print(f"    ✓ 找到 {len(memories)} 条待更新记忆")
            # 存储新记忆（高权重）
            self.add_memory_with_metadata(user_id, user_message, weight=1.0)
            print(f"    ✓ 已添加新记忆（旧记忆会自然衰减）")
        
        elif action == MemoryAction.STRENGTHEN:
            print(f"    💪 强化记忆: {info}")
            # 存储强化记忆
            self.add_memory_with_metadata(user_id, user_message, weight=1.2)
        
        else:  # IGNORE
            print(f"    ⏭️  跳过记忆操作（普通对话）")
        
        # 4. 生成回复（使用短期上下文 + 长期记忆）
        print(f"    🤖 生成回复...")
        
        system_prompt = f"""你是一个友好的私人助理，具有记忆能力。

【长期记忆】
{memory_context if memory_context else '暂无相关长期记忆'}

请根据用户消息和你的记忆，给出自然、友好的回答。
- 如果有相关记忆，自然地提及（但不要过度强调"我记得"）
- 如果是普通闲聊，自然交流即可
- 用户使用什么语言，你就用什么语言回复
"""
        
        response = self.call_llm(
            self.short_term_context[user_id][-5:],  # 只用最近5轮对话
            system_prompt
        )
        
        # 添加助理回复到短期上下文
        self.short_term_context[user_id].append({
            "role": "assistant",
            "content": response
        })
        
        # 保持短期上下文在合理范围（最近10轮）
        if len(self.short_term_context[user_id]) > 20:
            self.short_term_context[user_id] = self.short_term_context[user_id][-20:]
        
        return response


def run_smart_memory_test():
    """运行智能记忆管理测试"""
    
    print("\n" + "="*80)
    print("🧠 智能记忆管理私人助理测试")
    print("="*80)
    
    # 检查服务
    print("\n📡 检查服务...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Mem0服务未运行")
            return False
        print("✓ Mem0服务正常")
    except:
        print("❌ 无法连接Mem0服务")
        return False
    
    if not ZHIPU_API_KEY:
        print("❌ 请配置ZHIPU_API_KEY")
        return False
    
    # 初始化助理
    assistant = SmartMemoryAssistant(BASE_URL, ZHIPU_API_KEY)
    
    # 清空历史
    print("\n🧹 清空历史记忆...")
    try:
        requests.delete(f"{BASE_URL}/memories?user_id=smart_user_001", timeout=10)
    except:
        pass
    
    # 测试场景：展示智能记忆决策
    print("\n" + "="*80)
    print("💬 智能记忆管理对话测试")
    print("="*80)
    
    test_conversations = [
        # 第一组：存储偏好
        ("你好", "普通问候，不需要记忆"),
        ("我叫张三，是一名AI工程师", "身份信息，需要存储"),
        ("我特别喜欢喝咖啡，尤其是美式咖啡", "偏好信息，需要存储"),
        ("天气真好", "普通闲聊，不需要记忆"),
        
        # 第二组：查询记忆
        ("我叫什么名字？", "需要查询记忆"),
        ("我的职业是什么？", "需要查询记忆"),
        ("我喜欢喝什么？", "需要查询记忆"),
        
        # 第三组：更新记忆
        ("我现在改喝茶了，不喝咖啡了", "偏好变更，需要更新"),
        ("其实我是产品经理，不是AI工程师", "纠正信息，需要更新"),
        
        # 第四组：验证更新
        ("我现在喜欢喝什么？", "查询更新后的偏好"),
        ("总结一下你对我的了解", "综合查询"),
    ]
    
    user_id = "smart_user_001"
    
    for idx, (msg, expected) in enumerate(test_conversations, 1):
        print(f"\n{'─'*80}")
        print(f"第 {idx} 轮对话")
        print(f"{'─'*80}")
        print(f"👤 用户: {msg}")
        print(f"💭 预期: {expected}")
        print()
        
        response = assistant.process_conversation(user_id, msg)
        
        print(f"\n🤖 助理:")
        print(f"    {response}")
        
        time.sleep(1.5)  # 避免API限流
    
    # 最终验证：查看所有记忆
    print("\n" + "="*80)
    print("📊 最终记忆状态")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/memories?user_id={user_id}", timeout=10)
        if response.status_code == 200:
            memories = response.json().get("results", [])
            print(f"\n共有 {len(memories)} 条长期记忆：\n")
            
            for idx, mem in enumerate(memories, 1):
                content = mem.get("memory", "")
                metadata = mem.get("metadata", {})
                weight = metadata.get("weight", 1.0)
                timestamp = metadata.get("timestamp", "")
                
                print(f"{idx}. {content}")
                print(f"   [权重: {weight} | 时间: {timestamp[:19] if timestamp else 'N/A'}]")
    except Exception as e:
        print(f"获取记忆失败: {e}")
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)
    
    print("\n🎯 核心改进点展示:")
    print("  1. ✓ LLM决策记忆操作（不是每句话都存储）")
    print("  2. ✓ 智能区分存储/查询/更新/忽略")
    print("  3. ✓ 双层记忆架构（短期上下文 + 长期记忆）")
    print("  4. ✓ 时间衰减计算（权重随时间降低）")
    print("  5. ✓ 记忆层次（完整/摘要/标签）")
    
    return True


if __name__ == "__main__":
    success = run_smart_memory_test()
    exit(0 if success else 1)
