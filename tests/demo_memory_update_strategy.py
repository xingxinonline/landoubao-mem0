#!/usr/bin/env python3
"""
快速演示：记忆更新策略

用法:
  uv run python demo_memory_update_strategy.py
"""

import sys
from pathlib import Path

# 添加app到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from memory_update_strategy import (
    MemoryUpdateStrategy,
    UpdateTrigger,
    MergeStrategy,
    calculate_semantic_similarity
)


def demo():
    """快速演示"""
    
    print("\n" + "="*70)
    print("  记忆更新策略快速演示")
    print("="*70 + "\n")
    
    strategy = MemoryUpdateStrategy()
    
    # 演示1：被动压缩
    print("📌 演示1：定时服务压缩（被动）")
    print("-" * 70)
    
    memory = {
        "id": "mem_001",
        "memory": "我叫张三，是一名AI工程师",
        "metadata": {
            "level": "full",
            "weight": 0.5,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00"
        }
    }
    
    print(f"原始记忆: {memory['memory']}")
    print(f"更新时间: {memory['metadata']['updated_at']}\n")
    
    decision = strategy.decide_update_action(
        trigger=UpdateTrigger.PASSIVE_DECAY,
        old_memory=memory,
        new_content="",
        similarity_score=1.0
    )
    
    print(f"✅ 决策: {decision.reason}")
    print(f"✅ 刷新时间戳: {decision.should_refresh_timestamp}")
    print(f"   → 结论: 定时压缩保持原始时间 2024-01-01\n")
    
    # 演示2：用户提及（高相似度）
    print("📌 演示2：用户提及（高相似度 → 合并更新）")
    print("-" * 70)
    
    old_memory = {
        "id": "mem_002",
        "memory": "#职业:工程师",
        "metadata": {
            "level": "tag",
            "weight": 0.15,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:00:00"
        }
    }
    
    new_content = "我是AI工程师"
    similarity = 0.92
    
    print(f"旧记忆: {old_memory['memory']} (2024-01-01)")
    print(f"用户提及: {new_content}")
    print(f"相似度: {similarity}\n")
    
    decision = strategy.decide_update_action(
        trigger=UpdateTrigger.USER_MENTION,
        old_memory=old_memory,
        new_content=new_content,
        similarity_score=similarity
    )
    
    print(f"✅ 决策: {decision.reason}")
    print(f"✅ 策略: {decision.strategy.value}")
    print(f"✅ 刷新时间戳: {decision.should_refresh_timestamp}")
    print(f"✅ 升级层级: {decision.should_upgrade_level}")
    
    new_level = strategy.upgrade_memory_level("tag")
    new_weight = strategy.calculate_weight_boost(0.15, similarity, UpdateTrigger.USER_MENTION)
    
    print(f"   → 结果: tag → {new_level}, 权重 0.15 → {new_weight:.2f}, 时间戳刷新为今天\n")
    
    # 演示3：用户提及（中等相似度）
    print("📌 演示3：用户提及（中等相似度 → 保留双轨）")
    print("-" * 70)
    
    old_memory = {
        "id": "mem_003",
        "memory": "曾有职业相关记忆",
        "metadata": {"level": "trace", "weight": 0.08}
    }
    
    new_content = "我现在是产品经理"
    similarity = 0.68
    
    print(f"旧记忆: {old_memory['memory']}")
    print(f"用户提及: {new_content}")
    print(f"相似度: {similarity}\n")
    
    decision = strategy.decide_update_action(
        trigger=UpdateTrigger.USER_MENTION,
        old_memory=old_memory,
        new_content=new_content,
        similarity_score=similarity
    )
    
    print(f"✅ 决策: {decision.reason}")
    print(f"✅ 策略: {decision.strategy.value}")
    print(f"✅ 旧记忆时间戳: 不变（保持历史）")
    print(f"✅ 新记忆时间戳: 今天（新建）")
    print(f"   → 结果: 双轨并存，旧记忆保持压缩状态\n")
    
    # 演示4：用户提及（低相似度）
    print("📌 演示4：用户提及（低相似度 → 新建独立记忆）")
    print("-" * 70)
    
    old_memory = {
        "id": "mem_004",
        "memory": "#职业:工程师",
        "metadata": {"level": "tag", "weight": 0.12}
    }
    
    new_content = "我喜欢喝咖啡"
    similarity = 0.25
    
    print(f"旧记忆: {old_memory['memory']}")
    print(f"用户提及: {new_content}")
    print(f"相似度: {similarity}\n")
    
    decision = strategy.decide_update_action(
        trigger=UpdateTrigger.USER_MENTION,
        old_memory=old_memory,
        new_content=new_content,
        similarity_score=similarity
    )
    
    print(f"✅ 决策: {decision.reason}")
    print(f"✅ 策略: {decision.strategy.value}")
    print(f"   → 结果: 新建独立记忆，旧记忆保持压缩状态\n")
    
    # 总结
    print("="*70)
    print("  总结")
    print("="*70 + "\n")
    
    print("核心规则:")
    print("  1. 被动压缩（定时服务） → 时间戳不变 ✅")
    print("  2. 用户提及 + 高相似度 → 合并更新 + 刷新时间戳 ✅")
    print("  3. 用户提及 + 中等相似度 → 保留双轨 ✅")
    print("  4. 用户提及 + 低相似度 → 新建独立记忆 ✅")
    print()
    print("相似度阈值:")
    print(f"  高相似度: >= {strategy.HIGH_SIMILARITY_THRESHOLD}")
    print(f"  中等相似度: >= {strategy.MEDIUM_SIMILARITY_THRESHOLD}")
    print(f"  低相似度: < {strategy.MEDIUM_SIMILARITY_THRESHOLD}")
    print()
    print("详细文档: MEMORY_UPDATE_STRATEGY.md")
    print()


if __name__ == "__main__":
    demo()
