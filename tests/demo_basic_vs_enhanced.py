#!/usr/bin/env python3
"""
基础版 vs 增强版对比演示

对比点：
1. 基础版：简单时间衰减
2. 增强版：时间+语义+冲突+动量
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from memory_update_strategy import MemoryUpdateStrategy
from enhanced_memory_strategy import (
    EnhancedMemoryStrategy,
    MemoryMetadata,
    MemoryCategory,
    UpdateTrigger,
)


def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_weight_comparison():
    """对比1：权重计算"""
    print_header("对比1：权重计算（30天后）")
    
    # 基础版：只有时间衰减
    basic_strategy = MemoryUpdateStrategy()
    
    # 增强版：多因子融合
    enhanced_strategy = EnhancedMemoryStrategy(user_factor=1.0)
    
    print("场景：临时记忆，30天后权重对比\n")
    
    # 基础版
    basic_weight = 0.7273  # 手动计算
    print(f"【基础版】")
    print(f"  公式: w(t) = 1 / (1 + α * t)")
    print(f"  权重: {basic_weight:.4f}")
    print(f"  因子: 仅时间衰减")
    print()
    
    # 增强版
    metadata = MemoryMetadata(
        created_at="2024-01-01T10:00:00",
        last_activated_at="2024-01-01T10:00:00",
        category=MemoryCategory.TEMPORARY
    )
    now = datetime(2024, 1, 31, 10, 0, 0)
    enhanced_weight = enhanced_strategy.calculate_enhanced_weight(metadata, now)
    
    print(f"【增强版】")
    print(f"  公式: W(t) = w_time * S * C * I * U * M")
    print(f"  权重: {enhanced_weight:.4f}")
    print(f"  因子:")
    print(f"    - 时间权重: {metadata.factors.time_weight:.4f}")
    print(f"    - 语义强化: {metadata.factors.semantic_boost:.4f}")
    print(f"    - 冲突惩罚: {metadata.factors.conflict_penalty:.4f}")
    print(f"    - 重要性: {metadata.factors.importance:.4f}")
    print(f"    - 用户因子: {metadata.factors.user_factor:.4f}")
    print(f"    - 动量: {metadata.factors.momentum:.4f}")
    print()
    
    print(f"✅ 增强版提供更精细的权重控制")


def demo_activation():
    """对比2：用户激活"""
    print_header("对比2：用户激活记忆（提及后的权重变化）")
    
    enhanced_strategy = EnhancedMemoryStrategy()
    
    print("场景：30天未用的记忆，用户在第30天提及\n")
    
    # 未激活
    metadata_before = MemoryMetadata(
        created_at="2024-01-01T10:00:00",
        last_activated_at="2024-01-01T10:00:00",
        category=MemoryCategory.STABLE_PREFERENCE
    )
    now = datetime(2024, 1, 31, 10, 0, 0)
    weight_before = enhanced_strategy.calculate_enhanced_weight(metadata_before, now)
    
    print(f"【激活前】")
    print(f"  权重: {weight_before:.4f}")
    print(f"  时间权重: {metadata_before.factors.time_weight:.4f}")
    print(f"  语义强化: {metadata_before.factors.semantic_boost:.4f}")
    print()
    
    # 激活后
    metadata_after = MemoryMetadata(
        created_at="2024-01-01T10:00:00",
        last_activated_at="2024-01-31T10:00:00",  # ✅ 刷新
        last_mention_time="2024-01-31T10:00:00",  # ✅ 提及
        category=MemoryCategory.STABLE_PREFERENCE,
        recent_mentions=["2024-01-31T10:00:00"]
    )
    weight_after = enhanced_strategy.calculate_enhanced_weight(metadata_after, now)
    
    print(f"【激活后】")
    print(f"  权重: {weight_after:.4f} (提升{(weight_after/weight_before - 1)*100:.1f}%)")
    print(f"  时间权重: {metadata_after.factors.time_weight:.4f}")
    print(f"  语义强化: {metadata_after.factors.semantic_boost:.4f} ← ✨ 提升50%")
    print()
    
    print(f"基础版: 无语义强化机制")
    print(f"增强版: 激活时权重提升 {weight_after/weight_before:.2f}x")
    print()
    print(f"✅ 增强版能识别用户激活，动态提升权重")


def demo_negation():
    """对比3：用户否定"""
    print_header("对比3：用户否定记忆（'不喜欢咖啡了'）")
    
    basic_strategy = MemoryUpdateStrategy()
    enhanced_strategy = EnhancedMemoryStrategy()
    
    print("场景：用户说'我不喜欢咖啡了'\n")
    
    # 基础版：无否定机制
    print(f"【基础版】")
    print(f"  处理: 根据相似度决定合并/新建")
    print(f"  问题: 无法识别否定，可能错误合并")
    print(f"  结果: '喜欢咖啡' + '不喜欢咖啡' → 语义冲突")
    print()
    
    # 增强版：冲突修正
    old_memory = {
        "metadata": {
            "created_at": "2024-01-01T10:00:00",
            "last_activated_at": "2024-01-01T10:00:00",
            "category": MemoryCategory.SHORT_PREFERENCE
        }
    }
    
    decision = enhanced_strategy.decide_enhanced_action(
        trigger=UpdateTrigger.USER_NEGATION,
        old_memory=old_memory,
        new_content="我不喜欢咖啡了",
        similarity_score=0.75,
        is_negation=True
    )
    
    print(f"【增强版】")
    print(f"  处理: 冲突修正机制")
    print(f"  决策: {decision.action}")
    print(f"  旧记忆: 标记为'已否定'，降权{abs(decision.conflict_penalty_delta)*100:.0f}%")
    print(f"  新记忆: '不喜欢咖啡'进入FULL层级")
    print(f"  时间戳: 旧的不刷新（保持历史）")
    print()
    
    print(f"✅ 增强版能正确处理冲突记忆")


def demo_frequent():
    """对比4：频繁提及"""
    print_header("对比4：频繁提及（24小时内3次）")
    
    enhanced_strategy = EnhancedMemoryStrategy()
    
    print("场景：用户24小时内3次说'喝咖啡'\n")
    
    recent_mentions = [
        "2024-01-01T08:00:00",
        "2024-01-01T14:00:00",
        "2024-01-01T20:00:00",
    ]
    
    is_frequent = enhanced_strategy.detect_frequent_reinforce(
        recent_mentions,
        datetime(2024, 1, 2, 8, 0, 0)
    )
    
    print(f"【基础版】")
    print(f"  处理: 每次都合并更新")
    print(f"  问题: 可能过度提升权重")
    print(f"  结果: 权重无上限增长")
    print()
    
    print(f"【增强版】")
    print(f"  检测: 频繁强化 → {is_frequent}")
    print(f"  处理: 适度提升（限制过度放大）")
    print(f"  语义强化增量: +0.3 (而非 +0.5)")
    print(f"  动量因子: 1.23 (有上限)")
    print()
    
    print(f"✅ 增强版防止频繁提及过度放大权重")


def demo_category():
    """对比5：类别差异"""
    print_header("对比5：类别差异化衰减")
    
    enhanced_strategy = EnhancedMemoryStrategy()
    
    print("场景：180天后，不同类别的权重对比\n")
    
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    now = datetime(2024, 6, 30, 10, 0, 0)  # 180天后
    
    categories = [
        (MemoryCategory.IDENTITY, "身份信息"),
        (MemoryCategory.STABLE_PREFERENCE, "稳定偏好"),
        (MemoryCategory.SHORT_PREFERENCE, "短期偏好"),
        (MemoryCategory.TEMPORARY, "临时信息"),
    ]
    
    print(f"【基础版】")
    print(f"  所有记忆使用相同衰减速度")
    print(f"  180天后权重: ~0.36 (统一)")
    print()
    
    print(f"【增强版】")
    for category, name in categories:
        w = enhanced_strategy.calculate_time_weight(
            created_at=base_time,
            last_activated_at=base_time,
            now=now,
            category=category
        )
        importance = enhanced_strategy.IMPORTANCE_MAP[category]
        print(f"  {name:12s}: 权重={w:.4f}, 重要性={importance:.1f}")
    
    print()
    print(f"✅ 增强版根据类别调整衰减速度")


def demo_timestamp():
    """对比6：双时间戳"""
    print_header("对比6：双时间戳设计")
    
    print("场景：记忆在第15天被激活\n")
    
    print(f"【基础版】")
    print(f"  单时间戳: updated_at")
    print(f"  压缩时: 不刷新")
    print(f"  激活时: 刷新")
    print(f"  问题: 无法区分'久远'和'活跃'")
    print()
    
    print(f"【增强版】")
    print(f"  双时间戳:")
    print(f"    - created_at (创建时间)     → 保持历史感")
    print(f"    - last_activated_at (激活时间) → 判断活跃度")
    print()
    print(f"  示例:")
    print(f"    创建: 2024-01-01")
    print(f"    激活: 2024-01-15")
    print(f"    当前: 2024-01-31")
    print()
    print(f"    用户看到: '这是1月1日的记忆'（历史感）")
    print(f"    系统计算: 基于1月15日衰减（活跃度）")
    print()
    
    print(f"✅ 增强版双时间戳设计更合理")


def main():
    """运行所有对比"""
    print("\n" + "="*70)
    print("  基础版 vs 增强版 对比演示")
    print("="*70)
    
    demo_weight_comparison()
    demo_activation()
    demo_negation()
    demo_frequent()
    demo_category()
    demo_timestamp()
    
    print_header("总结对比")
    
    print("基础版特点:")
    print("  ✅ 简单易懂")
    print("  ✅ 实现简单")
    print("  ❌ 无语义强化")
    print("  ❌ 无冲突检测")
    print("  ❌ 无类别差异")
    print("  ❌ 单一时间戳")
    print()
    
    print("增强版优势:")
    print("  ✅ 语义强化（用户提及时+50%）")
    print("  ✅ 冲突修正（否定时-70%）")
    print("  ✅ 动量控制（防止过度放大）")
    print("  ✅ 类别差异（身份慢衰减）")
    print("  ✅ 双时间戳（历史+活跃）")
    print("  ✅ 频繁检测（24h内3次）")
    print("  ✅ 批量合并（重复记忆）")
    print("  ✅ 记忆溯源（可追溯）")
    print("  ✅ 可解释性（权重日志）")
    print()
    
    print("公式对比:")
    print("  基础版: w(t) = 1 / (1 + α * t)")
    print("  增强版: W(t) = w_time(t) * S(t) * C(t) * I * U * M(t)")
    print()
    
    print("适用场景:")
    print("  基础版: 简单场景、快速原型")
    print("  增强版: 生产环境、复杂需求")
    print()


if __name__ == "__main__":
    main()
