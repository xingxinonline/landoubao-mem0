#!/usr/bin/env python3
"""
记忆更新策略 - Memory Update Strategy

核心逻辑：
1. 被动演化：定时服务压缩，不刷新时间戳（保持历史感）
2. 主动激活：用户提及相关内容时，根据相似度决定合并或新建

情况分类：
- 情况1：定时服务压缩 → 时间戳不变（系统被动维护）
- 情况2：用户再次提及 → 判断相似度 → 合并更新或新建记忆
"""

from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class UpdateTrigger(Enum):
    """更新触发类型"""
    PASSIVE_DECAY = "passive_decay"      # 被动衰减（定时服务）
    USER_MENTION = "user_mention"        # 用户主动提及
    MANUAL_EDIT = "manual_edit"          # 手动编辑


class MergeStrategy(Enum):
    """合并策略"""
    MERGE_UPDATE = "merge_update"        # 合并更新（高相似度）
    CREATE_NEW = "create_new"            # 新建记忆（低相似度）
    KEEP_BOTH = "keep_both"              # 保留双轨（中等相似度）


@dataclass
class UpdateDecision:
    """更新决策结果"""
    strategy: MergeStrategy
    should_refresh_timestamp: bool
    should_upgrade_level: bool
    reason: str
    similarity_score: float = 0.0


class MemoryUpdateStrategy:
    """记忆更新策略引擎"""
    
    # 相似度阈值
    HIGH_SIMILARITY_THRESHOLD = 0.85    # 高度相似 → 合并更新
    MEDIUM_SIMILARITY_THRESHOLD = 0.60  # 中等相似 → 保留双轨
    # < 0.60 → 新建独立记忆
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def decide_update_action(
        self,
        trigger: UpdateTrigger,
        old_memory: Dict[str, Any],
        new_content: str,
        similarity_score: float = 0.0
    ) -> UpdateDecision:
        """
        决定更新动作
        
        Args:
            trigger: 触发类型（被动衰减 or 用户提及）
            old_memory: 旧记忆数据
            new_content: 新内容
            similarity_score: 语义相似度（0-1）
            
        Returns:
            UpdateDecision: 更新决策
        """
        
        # 🧩 情况1：定时服务的被动压缩
        if trigger == UpdateTrigger.PASSIVE_DECAY:
            return UpdateDecision(
                strategy=MergeStrategy.MERGE_UPDATE,
                should_refresh_timestamp=False,  # ✅ 不刷新时间
                should_upgrade_level=False,
                reason="定时服务自动压缩，保持原始时间戳以体现历史感",
                similarity_score=1.0
            )
        
        # 🧩 情况2：用户再次提及相关内容
        if trigger == UpdateTrigger.USER_MENTION:
            old_level = old_memory.get("metadata", {}).get("level", "full")
            
            # 情况2.1：高度相似 → 合并更新 + 刷新时间 + 可能升级
            if similarity_score >= self.HIGH_SIMILARITY_THRESHOLD:
                should_upgrade = self._should_upgrade_level(old_level, similarity_score)
                return UpdateDecision(
                    strategy=MergeStrategy.MERGE_UPDATE,
                    should_refresh_timestamp=True,  # ✅ 刷新时间戳
                    should_upgrade_level=should_upgrade,
                    reason=f"高相似度({similarity_score:.2f})，合并更新并激活记忆",
                    similarity_score=similarity_score
                )
            
            # 情况2.2：中等相似 → 保留双轨（旧的保持压缩，新建fresh记忆）
            elif similarity_score >= self.MEDIUM_SIMILARITY_THRESHOLD:
                return UpdateDecision(
                    strategy=MergeStrategy.KEEP_BOTH,
                    should_refresh_timestamp=False,  # 旧的不刷新
                    should_upgrade_level=False,
                    reason=f"中等相似度({similarity_score:.2f})，保留历史痕迹并新建记忆",
                    similarity_score=similarity_score
                )
            
            # 情况2.3：低相似度 → 新建独立记忆
            else:
                return UpdateDecision(
                    strategy=MergeStrategy.CREATE_NEW,
                    should_refresh_timestamp=False,  # 旧的不刷新
                    should_upgrade_level=False,
                    reason=f"低相似度({similarity_score:.2f})，创建新记忆，旧记忆保持压缩状态",
                    similarity_score=similarity_score
                )
        
        # 手动编辑 → 总是刷新
        return UpdateDecision(
            strategy=MergeStrategy.MERGE_UPDATE,
            should_refresh_timestamp=True,
            should_upgrade_level=False,
            reason="手动编辑，刷新时间戳",
            similarity_score=1.0
        )
    
    def _should_upgrade_level(self, current_level: str, similarity: float) -> bool:
        """
        判断是否应该升级记忆层级
        
        规则：
        - archive/trace → tag (如果相似度 > 0.9)
        - tag → summary (如果相似度 > 0.9)
        - summary → full (如果相似度 > 0.95)
        """
        if similarity > 0.95 and current_level in ["summary", "tag", "trace", "archive"]:
            return True
        if similarity > 0.90 and current_level in ["tag", "trace", "archive"]:
            return True
        return False
    
    def merge_memory_content(
        self,
        old_content: str,
        new_content: str,
        old_level: str
    ) -> str:
        """
        合并记忆内容
        
        策略：
        - 如果旧记忆已压缩（summary/tag/trace），用新内容替换
        - 如果旧记忆是full，合并关键信息
        """
        if old_level in ["tag", "trace", "archive"]:
            # 已高度压缩，直接用新内容
            return new_content
        
        elif old_level == "summary":
            # 摘要 + 新内容 → 生成新摘要
            return f"{old_content}；{new_content}"[:50]  # 简化合并
        
        else:  # full
            # 完整记忆合并
            if new_content not in old_content:
                return f"{old_content}。{new_content}"
            return old_content
    
    def calculate_weight_boost(
        self,
        old_weight: float,
        similarity: float,
        trigger: UpdateTrigger
    ) -> float:
        """
        计算权重提升
        
        规则：
        - 被动衰减：不提升权重
        - 用户提及：根据相似度提升权重
        """
        if trigger == UpdateTrigger.PASSIVE_DECAY:
            return old_weight  # 不提升
        
        # 用户主动提及 → 权重提升
        if similarity >= self.HIGH_SIMILARITY_THRESHOLD:
            # 高相似度：大幅提升（朝1.0靠拢）
            boost = (1.0 - old_weight) * 0.6
            return min(1.0, old_weight + boost)
        
        elif similarity >= self.MEDIUM_SIMILARITY_THRESHOLD:
            # 中等相似度：中等提升
            boost = (1.0 - old_weight) * 0.3
            return min(1.0, old_weight + boost)
        
        else:
            # 低相似度：小幅提升（保持活跃即可）
            return min(1.0, old_weight + 0.1)
    
    def upgrade_memory_level(self, current_level: str) -> str:
        """
        升级记忆层级
        
        archive → trace → tag → summary → full
        """
        upgrade_map = {
            "archive": "trace",
            "trace": "tag",
            "tag": "summary",
            "summary": "full",
            "full": "full"
        }
        return upgrade_map.get(current_level, "full")


def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    计算语义相似度（简化版）
    
    生产环境应使用：
    - sentence-transformers
    - OpenAI embeddings
    - 智谱AI embeddings
    
    这里使用简单的字符重叠度作为近似
    """
    if not text1 or not text2:
        return 0.0
    
    # 简单的字符集合交集比例
    set1 = set(text1)
    set2 = set(text2)
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    # Jaccard相似度
    jaccard = intersection / union
    
    # 检查子串包含
    contains_score = 0.0
    if text1 in text2 or text2 in text1:
        contains_score = 0.3
    
    # 综合得分
    return min(1.0, jaccard + contains_score)


# 使用示例
if __name__ == "__main__":
    strategy = MemoryUpdateStrategy()
    
    # 示例1：定时服务压缩
    old_mem = {
        "id": "123",
        "memory": "我叫张三，是一名AI工程师",
        "metadata": {"level": "full", "weight": 0.5}
    }
    
    decision = strategy.decide_update_action(
        trigger=UpdateTrigger.PASSIVE_DECAY,
        old_memory=old_mem,
        new_content="",  # 压缩时无新内容
        similarity_score=1.0
    )
    
    print(f"定时压缩: {decision.reason}")
    print(f"刷新时间戳: {decision.should_refresh_timestamp}")  # False
    print()
    
    # 示例2：用户再次提及（高相似度）
    decision = strategy.decide_update_action(
        trigger=UpdateTrigger.USER_MENTION,
        old_memory={
            "id": "123",
            "memory": "#职业:工程师",
            "metadata": {"level": "tag", "weight": 0.15}
        },
        new_content="我是AI工程师张三",
        similarity_score=0.92  # 高相似度
    )
    
    print(f"用户提及(高相似): {decision.reason}")
    print(f"策略: {decision.strategy.value}")
    print(f"刷新时间戳: {decision.should_refresh_timestamp}")  # True
    print(f"升级层级: {decision.should_upgrade_level}")  # True
    print()
    
    # 示例3：用户提及（低相似度）
    decision = strategy.decide_update_action(
        trigger=UpdateTrigger.USER_MENTION,
        old_memory={
            "id": "123",
            "memory": "#职业:工程师",
            "metadata": {"level": "tag", "weight": 0.15}
        },
        new_content="我喜欢喝咖啡",
        similarity_score=0.25  # 低相似度
    )
    
    print(f"用户提及(低相似): {decision.reason}")
    print(f"策略: {decision.strategy.value}")  # create_new
    print(f"刷新时间戳: {decision.should_refresh_timestamp}")  # False
