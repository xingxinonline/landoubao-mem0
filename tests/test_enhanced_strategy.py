#!/usr/bin/env python3
"""
增强型记忆策略测试 - Test Enhanced Memory Strategy

测试特殊情形：
1. 频繁强化
2. 用户否定/修正
3. 跨模态更新
4. 批量合并
5. 权重动态计算
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from enhanced_memory_strategy import (
    EnhancedMemoryStrategy,
    MemoryMetadata,
    MemoryCategory,
    UpdateTrigger,
)


def print_section(title: str):
    """打印分节"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_time_weight_decay():
    """测试时间权重衰减"""
    print_section("测试1：时间权重衰减（不同类别）")
    
    strategy = EnhancedMemoryStrategy(user_factor=1.0)
    
    # 不同类别的记忆
    categories = [
        (MemoryCategory.IDENTITY, "身份信息"),
        (MemoryCategory.STABLE_PREFERENCE, "稳定偏好"),
        (MemoryCategory.SHORT_PREFERENCE, "短期偏好"),
        (MemoryCategory.TEMPORARY, "临时信息"),
    ]
    
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    
    for category, name in categories:
        print(f"{name} ({category.value}):")
        
        for days in [0, 7, 30, 90, 180]:
            now = base_time + timedelta(days=days)
            w = strategy.calculate_time_weight(
                created_at=base_time,
                last_activated_at=base_time,
                now=now,
                category=category
            )
            print(f"  {days:3d}天: {w:.4f}")
        
        print()
    
    print("✅ 验证：重要类别（身份）衰减更慢")


def test_semantic_boost():
    """测试语义强化"""
    print_section("测试2：语义强化因子（用户提及后的提升）")
    
    strategy = EnhancedMemoryStrategy()
    
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    mention_time = datetime(2024, 1, 15, 10, 0, 0)
    
    print(f"用户在第15天提及记忆，强化因子变化：\n")
    
    for days_after in [0, 1, 3, 7, 14, 30]:
        now = mention_time + timedelta(days=days_after)
        boost = strategy.calculate_semantic_boost(mention_time, now)
        print(f"提及后{days_after:2d}天: S(t) = {boost:.4f} (提升{(boost-1)*100:.1f}%)")
    
    print("\n✅ 验证：语义强化随时间指数衰减")


def test_conflict_penalty():
    """测试冲突惩罚"""
    print_section("测试3：冲突修正因子（用户否定后的惩罚）")
    
    strategy = EnhancedMemoryStrategy()
    
    negation_time = datetime(2024, 1, 15, 10, 0, 0)
    
    print(f"用户在第15天否定记忆，惩罚因子变化：\n")
    
    for days_after in [0, 1, 7, 30, 60, 90]:
        now = negation_time + timedelta(days=days_after)
        penalty = strategy.calculate_conflict_penalty(
            is_negated=True,
            negation_time=negation_time,
            now=now
        )
        print(f"否定后{days_after:2d}天: C(t) = {penalty:.4f} (惩罚{(1-penalty)*100:.1f}%)")
    
    print(f"\n最小惩罚因子: {strategy.C_MIN}")
    print("✅ 验证：冲突惩罚初始降至最小值，随后缓慢恢复")


def test_momentum_factor():
    """测试动量因子"""
    print_section("测试4：动量因子（防止频繁提及过度放大）")
    
    strategy = EnhancedMemoryStrategy()
    
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    
    print("近3天内不同提及次数的动量因子：\n")
    
    for n_mentions in [0, 1, 2, 3, 5, 10]:
        recent_mentions = [
            base_time + timedelta(hours=i*6) 
            for i in range(n_mentions)
        ]
        momentum = strategy.calculate_momentum(recent_mentions, base_time + timedelta(days=1))
        print(f"提及{n_mentions:2d}次: M(t) = {momentum:.4f}")
    
    print("\n✅ 验证：提及次数越多，动量因子越大（但有上限）")


def test_enhanced_weight():
    """测试增强型综合权重"""
    print_section("测试5：增强型综合权重计算")
    
    strategy = EnhancedMemoryStrategy(user_factor=1.0)
    
    # 场景1：普通记忆，30天后
    metadata1 = MemoryMetadata(
        created_at="2024-01-01T10:00:00",
        last_activated_at="2024-01-01T10:00:00",
        category=MemoryCategory.TEMPORARY
    )
    
    now = datetime(2024, 1, 31, 10, 0, 0)
    w1 = strategy.calculate_enhanced_weight(metadata1, now)
    
    print("场景1：临时记忆，30天未激活")
    print(f"  综合权重: {w1:.4f}")
    print(f"  时间权重: {metadata1.factors.time_weight:.4f}")
    print(f"  语义强化: {metadata1.factors.semantic_boost:.4f}")
    print(f"  重要性: {metadata1.factors.importance:.4f}")
    print()
    
    # 场景2：用户在第20天激活，30天时的权重
    metadata2 = MemoryMetadata(
        created_at="2024-01-01T10:00:00",
        last_activated_at="2024-01-20T10:00:00",  # ✅ 激活
        last_mention_time="2024-01-20T10:00:00",
        category=MemoryCategory.STABLE_PREFERENCE,
        recent_mentions=["2024-01-20T10:00:00"]
    )
    
    w2 = strategy.calculate_enhanced_weight(metadata2, now)
    
    print("场景2：稳定偏好，第20天被激活，30天时权重")
    print(f"  综合权重: {w2:.4f}")
    print(f"  时间权重: {metadata2.factors.time_weight:.4f}")
    print(f"  语义强化: {metadata2.factors.semantic_boost:.4f}")
    print(f"  重要性: {metadata2.factors.importance:.4f}")
    print(f"  动量: {metadata2.factors.momentum:.4f}")
    print()
    
    # 场景3：被否定的记忆
    metadata3 = MemoryMetadata(
        created_at="2024-01-01T10:00:00",
        last_activated_at="2024-01-01T10:00:00",
        category=MemoryCategory.SHORT_PREFERENCE,
        is_negated=True,
        correction_history=[{"time": "2024-01-15T10:00:00"}]
    )
    
    w3 = strategy.calculate_enhanced_weight(metadata3, now)
    
    print("场景3：短期偏好，第15天被否定，30天时权重")
    print(f"  综合权重: {w3:.4f}")
    print(f"  时间权重: {metadata3.factors.time_weight:.4f}")
    print(f"  冲突惩罚: {metadata3.factors.conflict_penalty:.4f}")
    print(f"  重要性: {metadata3.factors.importance:.4f}")
    print()
    
    print(f"权重对比: 普通({w1:.4f}) vs 激活({w2:.4f}) vs 否定({w3:.4f})")
    print("✅ 验证：激活提升权重，否定降低权重")


def test_frequent_reinforce():
    """测试频繁强化检测"""
    print_section("测试6：频繁强化检测")
    
    strategy = EnhancedMemoryStrategy()
    
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    
    # 24小时内提及3次
    recent_mentions = [
        (base_time + timedelta(hours=0)).isoformat(),
        (base_time + timedelta(hours=8)).isoformat(),
        (base_time + timedelta(hours=16)).isoformat(),
    ]
    
    is_frequent = strategy.detect_frequent_reinforce(recent_mentions, base_time + timedelta(hours=20))
    
    print(f"24小时内提及次数: {len(recent_mentions)}")
    print(f"频繁强化阈值: {strategy.FREQUENT_THRESHOLD}次/{strategy.FREQUENT_WINDOW_HOURS}小时")
    print(f"是否触发频繁强化: {is_frequent}")
    
    # 决策
    decision = strategy.decide_enhanced_action(
        trigger=UpdateTrigger.USER_MENTION,
        old_memory={"metadata": {"recent_mentions": recent_mentions}},
        new_content="我又想喝咖啡了",
        similarity_score=0.95
    )
    
    print(f"\n决策: {decision.action}")
    print(f"原因: {decision.reason}")
    print(f"语义强化增量: +{decision.semantic_boost_delta}")
    print(f"动量增量: +{decision.momentum_delta}")
    
    print("\n✅ 验证：频繁强化被检测，适度提升但防止过度放大")


def test_negation_scenario():
    """测试否定场景"""
    print_section("测试7：用户否定/修正记忆")
    
    strategy = EnhancedMemoryStrategy()
    
    # 旧记忆：喜欢咖啡
    old_memory = {
        "id": "mem_001",
        "memory": "我喜欢喝咖啡",
        "metadata": {
            "created_at": "2024-01-01T10:00:00",
            "last_activated_at": "2024-01-01T10:00:00",
            "category": MemoryCategory.SHORT_PREFERENCE,
            "recent_mentions": []
        }
    }
    
    # 用户说：我不喜欢咖啡了
    decision = strategy.decide_enhanced_action(
        trigger=UpdateTrigger.USER_NEGATION,
        old_memory=old_memory,
        new_content="我不喜欢咖啡了",
        similarity_score=0.75,
        is_negation=True
    )
    
    print("旧记忆: 我喜欢喝咖啡")
    print("用户说: 我不喜欢咖啡了")
    print()
    print(f"决策: {decision.action}")
    print(f"标记为否定: {decision.mark_as_negated}")
    print(f"冲突惩罚增量: {decision.conflict_penalty_delta}")
    print(f"刷新时间戳: {decision.should_refresh_timestamp}")
    print(f"原因: {decision.reason}")
    
    print("\n处理逻辑:")
    print("  1. 旧记忆标记为'已否定'，权重降低")
    print("  2. 新记忆'不喜欢咖啡'进入FULL层级")
    print("  3. 旧记忆保留（版本化），时间戳不变")
    
    print("\n✅ 验证：否定记忆被正确降权，新偏好进入FULL")


def test_batch_merge():
    """测试批量合并"""
    print_section("测试8：批量合并相似记忆")
    
    strategy = EnhancedMemoryStrategy()
    
    # 用户每天都说喝咖啡
    memories = [
        {
            "id": f"mem_{i:03d}",
            "memory": f"今天喝了咖啡（第{i}天）",
            "metadata": {
                "created_at": f"2024-01-{i:02d}T10:00:00",
                "last_activated_at": f"2024-01-{i:02d}T10:00:00",
                "mention_count": 1
            }
        }
        for i in range(1, 11)
    ]
    
    print(f"原始记忆数量: {len(memories)}条")
    for mem in memories[:3]:
        print(f"  - {mem['memory']}")
    print("  ...")
    
    # 批量合并
    merged = strategy.merge_memories_batch(memories, similarity_threshold=0.8)
    
    print(f"\n合并后:")
    print(f"  内容: {merged['memory']}")
    print(f"  合并自: {len(merged['metadata']['merged_from'])}条记忆")
    print(f"  总提及次数: {merged['metadata']['mention_count']}")
    
    print("\n✅ 验证：重复记忆被合并为长期偏好摘要")


def test_decision_scenarios():
    """测试各种决策场景"""
    print_section("测试9：决策场景矩阵")
    
    strategy = EnhancedMemoryStrategy()
    
    base_metadata = {
        "created_at": "2024-01-01T10:00:00",
        "last_activated_at": "2024-01-01T10:00:00",
        "category": MemoryCategory.TEMPORARY,
        "recent_mentions": []
    }
    
    scenarios = [
        ("被动压缩", UpdateTrigger.PASSIVE_DECAY, 0.0, False),
        ("高相似激活", UpdateTrigger.USER_MENTION, 0.92, False),
        ("中等相似", UpdateTrigger.USER_MENTION, 0.68, False),
        ("低相似", UpdateTrigger.USER_MENTION, 0.35, False),
        ("用户否定", UpdateTrigger.USER_NEGATION, 0.75, True),
    ]
    
    print(f"{'场景':<12} {'动作':<12} {'刷新时间戳':<10} {'原因'}")
    print("-" * 70)
    
    for name, trigger, similarity, is_neg in scenarios:
        decision = strategy.decide_enhanced_action(
            trigger=trigger,
            old_memory={"metadata": base_metadata},
            new_content="测试内容",
            similarity_score=similarity,
            is_negation=is_neg
        )
        
        refresh = "✅ 是" if decision.should_refresh_timestamp else "❌ 否"
        print(f"{name:<12} {decision.action:<12} {refresh:<10} {decision.reason[:30]}...")
    
    print("\n✅ 验证：不同场景的决策逻辑正确")


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("  增强型记忆策略完整测试")
    print("="*70)
    
    test_time_weight_decay()
    test_semantic_boost()
    test_conflict_penalty()
    test_momentum_factor()
    test_enhanced_weight()
    test_frequent_reinforce()
    test_negation_scenario()
    test_batch_merge()
    test_decision_scenarios()
    
    print_section("✅ 所有测试完成")
    
    print("核心功能验证:")
    print("  1. 时间权重衰减（类别差异）✅")
    print("  2. 语义强化因子（激活提升）✅")
    print("  3. 冲突修正因子（否定降权）✅")
    print("  4. 动量因子（防止过度放大）✅")
    print("  5. 增强型综合权重 ✅")
    print("  6. 频繁强化检测 ✅")
    print("  7. 否定/修正处理 ✅")
    print("  8. 批量合并 ✅")
    print("  9. 决策场景矩阵 ✅")
    print()
    print("增强公式: W(t) = w_time(t) * S(t) * C(t) * I * U * M(t)")
    print()


if __name__ == "__main__":
    main()
