#!/usr/bin/env python3
"""
增强型记忆管理策略 - Enhanced Memory Management Strategy

核心创新：
1. 时间衰减 + 语义强化 + 上下文重要性 + 个体差异
2. 增强权重公式: W(t) = w_time(t) * S(t) * C(t) * I * U * M(t)
3. 特殊情形处理：频繁强化、否定修正、冲突解决、批量合并
4. 双时间戳设计：created_at（历史感） + last_activated_at（活跃度）
5. 记忆溯源链：压缩后保留原始引用
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class UpdateTrigger(Enum):
    """更新触发类型"""
    PASSIVE_DECAY = "passive_decay"         # 被动衰减（定时服务）
    USER_MENTION = "user_mention"           # 用户主动提及
    USER_NEGATION = "user_negation"         # 用户否定/修正
    MANUAL_EDIT = "manual_edit"             # 手动编辑
    FREQUENT_REINFORCE = "frequent_reinforce"  # 频繁强化
    BATCH_MERGE = "batch_merge"             # 批量合并
    MULTIMODAL_UPDATE = "multimodal_update"  # 跨模态更新


class MemoryCategory(Enum):
    """记忆类别（影响衰减速度）"""
    IDENTITY = "identity"           # 身份信息（慢衰减）
    STABLE_PREFERENCE = "stable_preference"  # 稳定偏好
    SHORT_PREFERENCE = "short_preference"    # 短期偏好（快衰减）
    EVENT = "event"                 # 事件
    SKILL = "skill"                 # 技能
    FACT = "fact"                   # 事实
    TEMPORARY = "temporary"         # 临时信息


class ConflictResolution(Enum):
    """冲突解决策略"""
    LATEST_WINS = "latest_wins"     # 最新优先（覆盖旧记忆）
    VERSION_KEEP = "version_keep"   # 保留多版本（标记时间线）
    WEIGHT_BALANCE = "weight_balance"  # 权重平衡（旧的逐渐衰减）


@dataclass
class MemoryFactors:
    """记忆权重因子"""
    
    # 基础时间权重
    time_weight: float = 1.0
    
    # 语义强化因子 S(t)
    semantic_boost: float = 1.0
    
    # 冲突修正因子 C(t)
    conflict_penalty: float = 1.0
    
    # 上下文重要性 I（静态）
    importance: float = 1.0
    
    # 用户个性化 U（影响衰减速度）
    user_factor: float = 1.0
    
    # 动量/习惯因子 M(t)
    momentum: float = 1.0
    
    # 综合权重
    total_weight: float = 1.0
    
    def calculate_total(self) -> float:
        """计算综合权重"""
        self.total_weight = (
            self.time_weight * 
            self.semantic_boost * 
            self.conflict_penalty * 
            self.importance * 
            self.user_factor * 
            self.momentum
        )
        return self.total_weight


@dataclass
class MemoryMetadata:
    """增强型记忆元数据"""
    
    # 🕐 双时间戳设计
    created_at: str                          # 创建时间（历史感）
    last_activated_at: str                   # 最后激活时间（活跃度）
    
    # 记忆属性
    level: str = "full"                      # 压缩层级
    category: MemoryCategory = MemoryCategory.TEMPORARY
    
    # 权重因子
    factors: MemoryFactors = field(default_factory=MemoryFactors)
    
    # 行为统计
    mention_count: int = 0                   # 提及次数
    reinforce_count: int = 0                 # 强化次数
    last_mention_time: Optional[str] = None  # 最后提及时间
    recent_mentions: List[str] = field(default_factory=list)  # 近期提及时间戳
    
    # 冲突与修正
    is_negated: bool = False                 # 是否被否定
    is_corrected: bool = False               # 是否被修正
    correction_history: List[Dict] = field(default_factory=list)  # 修正历史
    
    # 溯源链
    source_ids: List[str] = field(default_factory=list)  # 来源记忆ID
    merged_from: List[str] = field(default_factory=list)  # 合并自哪些记忆
    compressed_from: Optional[str] = None     # 压缩自哪条记忆
    
    # 敏感标记
    is_sensitive: bool = False               # 是否敏感信息
    sensitivity_level: int = 0               # 敏感级别 0-3
    
    # 多模态
    modalities: List[str] = field(default_factory=list)  # 包含的模态 ["text", "image", "audio"]
    
    # 生命周期
    is_deleted: bool = False                 # 是否已删除
    deletion_time: Optional[str] = None      # 删除时间
    
    # 可解释性
    weight_change_log: List[Dict] = field(default_factory=list)  # 权重变化日志


@dataclass
class EnhancedUpdateDecision:
    """增强型更新决策"""
    
    # 基础决策
    action: str                              # merge/create_new/keep_both/negate/batch_merge
    should_refresh_timestamp: bool
    should_upgrade_level: bool
    
    # 因子更新
    semantic_boost_delta: float = 0.0       # 语义强化增量
    conflict_penalty_delta: float = 0.0     # 冲突惩罚增量
    momentum_delta: float = 0.0             # 动量增量
    
    # 特殊操作
    mark_as_negated: bool = False           # 标记为被否定
    mark_as_corrected: bool = False         # 标记为被修正
    merge_targets: List[str] = field(default_factory=list)  # 批量合并目标
    
    # 元信息
    reason: str = ""
    similarity_score: float = 0.0
    confidence: float = 1.0


class EnhancedMemoryStrategy:
    """增强型记忆策略引擎"""
    
    # 🎯 核心参数
    ALPHA_BASE = 0.01                        # 基础衰减系数
    
    # 相似度阈值
    HIGH_SIMILARITY = 0.85
    MEDIUM_SIMILARITY = 0.60
    NEGATION_SIMILARITY = 0.70               # 否定检测阈值
    
    # 语义强化 S(t)
    S_MAX = 0.5                              # 最大强化幅度
    LAMBDA_S = 0.05                          # 强化衰减速率
    
    # 冲突修正 C(t)
    C_MIN = 0.3                              # 最小冲突惩罚
    LAMBDA_C = 0.01                          # 惩罚恢复速率
    
    # 上下文重要性 I
    IMPORTANCE_MAP = {
        MemoryCategory.IDENTITY: 1.5,
        MemoryCategory.STABLE_PREFERENCE: 1.3,
        MemoryCategory.SHORT_PREFERENCE: 0.9,
        MemoryCategory.EVENT: 1.0,
        MemoryCategory.SKILL: 1.2,
        MemoryCategory.FACT: 1.1,
        MemoryCategory.TEMPORARY: 0.8,
    }
    
    # 动量因子 M(t)
    M_COEF = 0.3                             # 动量系数
    LAMBDA_M = 0.5                           # 动量衰减
    RECENT_WINDOW_DAYS = 3                   # 近期窗口（天）
    
    # 权重边界
    WEIGHT_MIN = 0.01                        # 最小权重
    WEIGHT_MAX = 2.0                         # 最大权重
    
    # 频繁强化检测
    FREQUENT_THRESHOLD = 3                   # N次提及视为频繁
    FREQUENT_WINDOW_HOURS = 24               # 时间窗口（小时）
    
    def __init__(self, user_factor: float = 1.0):
        """
        Args:
            user_factor: 用户个性化因子 U (0.7-1.5)
                        < 1.0: 遗忘慢
                        > 1.0: 遗忘快
        """
        self.user_factor = user_factor
        self.logger = logging.getLogger(__name__)
    
    def calculate_time_weight(
        self,
        created_at: datetime,
        last_activated_at: datetime,
        now: Optional[datetime] = None,
        category: MemoryCategory = MemoryCategory.TEMPORARY
    ) -> float:
        """
        计算基础时间权重
        
        w_time(t) = 1 / (1 + α_effective * t)
        
        其中 α_effective = α_base * U * category_factor
        """
        if now is None:
            now = datetime.now()
        
        # 使用最后激活时间计算衰减
        delta = now - last_activated_at
        days = delta.total_seconds() / 86400
        
        # 类别因子（重要类别衰减慢）
        category_factor = 1.0 / self.IMPORTANCE_MAP[category]
        
        # 有效衰减系数
        alpha_effective = self.ALPHA_BASE * self.user_factor * category_factor
        
        # 时间权重
        w_time = 1.0 / (1.0 + alpha_effective * days)
        
        return w_time
    
    def calculate_semantic_boost(
        self,
        last_mention_time: Optional[datetime],
        now: Optional[datetime] = None
    ) -> float:
        """
        计算语义强化因子
        
        S(t) = 1 + s_max * exp(-λ_s * Δt)
        
        近期提及时暂时提升，随时间指数衰减
        """
        if last_mention_time is None:
            return 1.0
        
        if now is None:
            now = datetime.now()
        
        delta = now - last_mention_time
        days = delta.total_seconds() / 86400
        
        boost = 1.0 + self.S_MAX * math.exp(-self.LAMBDA_S * days)
        
        return boost
    
    def calculate_conflict_penalty(
        self,
        is_negated: bool,
        negation_time: Optional[datetime],
        now: Optional[datetime] = None
    ) -> float:
        """
        计算冲突修正因子
        
        C(t) = c_min + (1 - c_min) * exp(-λ_c * Δt)
        
        被否定时降至 c_min，随后缓慢恢复
        """
        if not is_negated:
            return 1.0
        
        if negation_time is None:
            return self.C_MIN
        
        if now is None:
            now = datetime.now()
        
        delta = now - negation_time
        days = delta.total_seconds() / 86400
        
        penalty = self.C_MIN + (1.0 - self.C_MIN) * math.exp(-self.LAMBDA_C * days)
        
        return penalty
    
    def calculate_momentum(
        self,
        recent_mentions: List[datetime],
        now: Optional[datetime] = None
    ) -> float:
        """
        计算动量/习惯因子
        
        M(t) = 1 + m * (1 - exp(-λ_m * n_recent))
        
        防止短期多次提及过度放大
        """
        if now is None:
            now = datetime.now()
        
        # 统计近期窗口内的提及次数
        cutoff = now - timedelta(days=self.RECENT_WINDOW_DAYS)
        n_recent = sum(1 for mention_time in recent_mentions if mention_time >= cutoff)
        
        momentum = 1.0 + self.M_COEF * (1.0 - math.exp(-self.LAMBDA_M * n_recent))
        
        return momentum
    
    def calculate_enhanced_weight(
        self,
        metadata: MemoryMetadata,
        now: Optional[datetime] = None
    ) -> float:
        """
        计算增强型综合权重
        
        W(t) = w_time(t) * S(t) * C(t) * I * U * M(t)
        """
        if now is None:
            now = datetime.now()
        
        # 解析时间戳
        created_at = datetime.fromisoformat(metadata.created_at)
        last_activated_at = datetime.fromisoformat(metadata.last_activated_at)
        
        # 基础时间权重
        w_time = self.calculate_time_weight(
            created_at, last_activated_at, now, metadata.category
        )
        
        # 语义强化
        last_mention = None
        if metadata.last_mention_time:
            last_mention = datetime.fromisoformat(metadata.last_mention_time)
        s_boost = self.calculate_semantic_boost(last_mention, now)
        
        # 冲突惩罚
        negation_time = None
        if metadata.is_negated and metadata.correction_history:
            negation_time = datetime.fromisoformat(
                metadata.correction_history[-1]["time"]
            )
        c_penalty = self.calculate_conflict_penalty(
            metadata.is_negated, negation_time, now
        )
        
        # 重要性
        importance = self.IMPORTANCE_MAP[metadata.category]
        
        # 动量
        recent_mentions = [
            datetime.fromisoformat(ts) for ts in metadata.recent_mentions
        ]
        momentum = self.calculate_momentum(recent_mentions, now)
        
        # 更新因子
        metadata.factors.time_weight = w_time
        metadata.factors.semantic_boost = s_boost
        metadata.factors.conflict_penalty = c_penalty
        metadata.factors.importance = importance
        metadata.factors.user_factor = self.user_factor
        metadata.factors.momentum = momentum
        
        # 综合权重
        total = metadata.factors.calculate_total()
        
        # 边界约束
        total = max(self.WEIGHT_MIN, min(total, self.WEIGHT_MAX))
        
        return total
    
    def detect_frequent_reinforce(
        self,
        recent_mentions: List[str],
        now: Optional[datetime] = None
    ) -> bool:
        """检测频繁强化"""
        if now is None:
            now = datetime.now()
        
        cutoff = now - timedelta(hours=self.FREQUENT_WINDOW_HOURS)
        recent = [
            datetime.fromisoformat(ts) for ts in recent_mentions
            if datetime.fromisoformat(ts) >= cutoff
        ]
        
        return len(recent) >= self.FREQUENT_THRESHOLD
    
    def decide_enhanced_action(
        self,
        trigger: UpdateTrigger,
        old_memory: Dict[str, Any],
        new_content: str,
        similarity_score: float = 0.0,
        is_negation: bool = False,
        now: Optional[datetime] = None
    ) -> EnhancedUpdateDecision:
        """
        增强型决策引擎
        
        Args:
            trigger: 触发类型
            old_memory: 旧记忆
            new_content: 新内容
            similarity_score: 语义相似度
            is_negation: 是否为否定/修正
            now: 当前时间
        """
        if now is None:
            now = datetime.now()
        
        metadata = old_memory.get("metadata", {})
        
        # 🧩 情况1：被动压缩
        if trigger == UpdateTrigger.PASSIVE_DECAY:
            return EnhancedUpdateDecision(
                action="compress",
                should_refresh_timestamp=False,  # ✅ 不刷新
                should_upgrade_level=False,
                reason="定时服务被动压缩，保持原始时间戳"
            )
        
        # 🧩 情况2：用户否定/修正
        if trigger == UpdateTrigger.USER_NEGATION or is_negation:
            return EnhancedUpdateDecision(
                action="negate",
                should_refresh_timestamp=False,  # 旧记忆不刷新
                should_upgrade_level=False,
                mark_as_negated=True,
                conflict_penalty_delta=-0.7,     # 降权
                reason=f"用户否定/修正，旧记忆降权（相似度{similarity_score:.2f}）"
            )
        
        # 🧩 情况3：频繁强化
        recent_mentions = metadata.get("recent_mentions", [])
        if self.detect_frequent_reinforce(recent_mentions, now):
            return EnhancedUpdateDecision(
                action="merge",
                should_refresh_timestamp=True,
                should_upgrade_level=True,
                semantic_boost_delta=0.3,        # 适度提升
                momentum_delta=0.2,
                reason=f"频繁强化检测（{len(recent_mentions)}次），合并并限制过度提升"
            )
        
        # 🧩 情况4：高相似度 → 合并更新
        if similarity_score >= self.HIGH_SIMILARITY:
            return EnhancedUpdateDecision(
                action="merge",
                should_refresh_timestamp=True,   # ✅ 刷新
                should_upgrade_level=True,
                semantic_boost_delta=0.5,
                reason=f"高相似度({similarity_score:.2f})，合并更新并激活"
            )
        
        # 🧩 情况5：中等相似度 → 保留双轨
        if similarity_score >= self.MEDIUM_SIMILARITY:
            return EnhancedUpdateDecision(
                action="keep_both",
                should_refresh_timestamp=False,  # 旧的不刷新
                should_upgrade_level=False,
                reason=f"中等相似度({similarity_score:.2f})，保留双轨"
            )
        
        # 🧩 情况6：低相似度 → 新建独立
        return EnhancedUpdateDecision(
            action="create_new",
            should_refresh_timestamp=False,      # 旧的不刷新
            should_upgrade_level=False,
            reason=f"低相似度({similarity_score:.2f})，新建独立记忆"
        )
    
    def merge_memories_batch(
        self,
        memories: List[Dict[str, Any]],
        similarity_threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        批量合并相似记忆
        
        用于处理重复记忆（如每天说"喝咖啡"）
        """
        if not memories:
            return {}
        
        # 选择最新的作为基准
        base = max(memories, key=lambda m: m["metadata"]["last_activated_at"])
        
        merged = {
            "memory": self._summarize_batch([m["memory"] for m in memories]),
            "metadata": {
                **base["metadata"],
                "merged_from": [m["id"] for m in memories if m["id"] != base["id"]],
                "mention_count": sum(m["metadata"].get("mention_count", 1) for m in memories),
                "last_activated_at": datetime.now().isoformat()
            }
        }
        
        return merged
    
    def _summarize_batch(self, contents: List[str]) -> str:
        """批量内容摘要（简化版）"""
        # 实际应使用LLM生成摘要
        if len(contents) == 1:
            return contents[0]
        return f"长期偏好摘要（基于{len(contents)}条记忆）"
    
    def add_weight_change_log(
        self,
        metadata: MemoryMetadata,
        old_weight: float,
        new_weight: float,
        reason: str
    ):
        """记录权重变化（可解释性）"""
        log_entry = {
            "time": datetime.now().isoformat(),
            "old_weight": round(old_weight, 4),
            "new_weight": round(new_weight, 4),
            "delta": round(new_weight - old_weight, 4),
            "reason": reason,
            "factors": {
                "time_weight": round(metadata.factors.time_weight, 4),
                "semantic_boost": round(metadata.factors.semantic_boost, 4),
                "conflict_penalty": round(metadata.factors.conflict_penalty, 4),
                "importance": round(metadata.factors.importance, 4),
                "momentum": round(metadata.factors.momentum, 4),
            }
        }
        
        metadata.weight_change_log.append(log_entry)
        
        # 保留最近50条
        if len(metadata.weight_change_log) > 50:
            metadata.weight_change_log = metadata.weight_change_log[-50:]


# 使用示例
if __name__ == "__main__":
    # 创建策略引擎（用户遗忘较慢）
    strategy = EnhancedMemoryStrategy(user_factor=0.8)
    
    # 创建记忆元数据
    metadata = MemoryMetadata(
        created_at="2024-01-01T10:00:00",
        last_activated_at="2024-01-01T10:00:00",
        category=MemoryCategory.STABLE_PREFERENCE,
        recent_mentions=[]
    )
    
    # 计算初始权重
    weight = strategy.calculate_enhanced_weight(metadata)
    print(f"初始权重: {weight:.4f}")
    
    # 模拟30天后
    now = datetime.fromisoformat("2024-01-31T10:00:00")
    weight = strategy.calculate_enhanced_weight(metadata, now)
    print(f"30天后权重: {weight:.4f}")
    
    # 模拟用户提及（激活）
    metadata.last_activated_at = "2024-01-31T10:00:00"
    metadata.last_mention_time = "2024-01-31T10:00:00"
    metadata.recent_mentions.append("2024-01-31T10:00:00")
    
    weight = strategy.calculate_enhanced_weight(metadata, now)
    print(f"激活后权重: {weight:.4f}")
    
    # 决策测试
    decision = strategy.decide_enhanced_action(
        trigger=UpdateTrigger.USER_MENTION,
        old_memory={"metadata": metadata.__dict__},
        new_content="我还是喜欢咖啡",
        similarity_score=0.92
    )
    
    print(f"\n决策: {decision.action}")
    print(f"刷新时间戳: {decision.should_refresh_timestamp}")
    print(f"原因: {decision.reason}")
