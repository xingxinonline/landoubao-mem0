#!/usr/bin/env python3
"""
完整记忆引擎 - Complete Memory Engine

整合功能：
1. 增强型衰退曲线（6因子融合）
2. 定时调度服务（自动压缩）
3. 智能决策引擎（5+场景）
4. 批量处理与合并
5. 生命周期管理

公式:
W(t) = w_time(t) × S(t) × C(t) × I × U × M(t)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import math

from complete_memory_system import (
    Memory, MemoryMetadata, MemoryFactors, MultimodalContent,
    MemoryLevel, MemoryCategory, Modality, MemoryStore
)

logger = logging.getLogger(__name__)


# ============================================================================
# 3. 记忆衰退曲线引擎
# ============================================================================

class UpdateTrigger(Enum):
    """更新触发类型"""
    PASSIVE_DECAY = "passive_decay"         # 被动衰减（定时服务）
    USER_MENTION = "user_mention"           # 用户提及（激活）
    USER_NEGATION = "user_negation"         # 用户否定
    FREQUENT_REINFORCE = "frequent_reinforce"  # 频繁强化
    BATCH_MERGE = "batch_merge"             # 批量合并
    CROSS_MODAL_UPDATE = "cross_modal_update"  # 跨模态更新
    MANUAL_FREEZE = "manual_freeze"         # 用户冻结
    MANUAL_DELETE = "manual_delete"         # 用户删除


class QueryMode(Enum):
    """查询模式"""
    NORMAL = "normal"       # 普通模式：优先FULL/SUMMARY
    REVIEW = "review"       # 回顾模式：允许TRACE/ARCHIVE上浮
    DEBUG = "debug"         # 调试模式：显示所有层级


class CompleteMemoryEngine:
    """完整记忆引擎"""
    
    def __init__(
        self,
        user_factor: float = 1.0,
        time_scale: int = 86400,  # 1天=86400秒
        enable_scheduler: bool = True
    ):
        """
        Args:
            user_factor: 用户个性化因子 U (0.7=慢遗忘, 1.5=快遗忘)
            time_scale: 时间刻度（秒）
            enable_scheduler: 是否启用定时调度
        """
        self.user_factor = user_factor
        self.time_scale = time_scale
        self.enable_scheduler = enable_scheduler
        
        # 类别重要性 I
        self.category_importance = {
            MemoryCategory.IDENTITY: 1.5,           # 身份信息
            MemoryCategory.STABLE_PREFERENCE: 1.3,  # 稳定偏好
            MemoryCategory.SHORT_PREFERENCE: 1.0,   # 短期偏好
            MemoryCategory.SKILL: 1.2,              # 技能
            MemoryCategory.FACT: 1.1,               # 事实
            MemoryCategory.EVENT: 0.9,              # 事件
            MemoryCategory.TEMPORARY: 0.8           # 临时信息
        }
        
        # 类别衰减系数
        self.category_decay_alpha = {
            MemoryCategory.IDENTITY: 0.002,         # 极慢衰减
            MemoryCategory.STABLE_PREFERENCE: 0.005,
            MemoryCategory.SHORT_PREFERENCE: 0.01,
            MemoryCategory.SKILL: 0.007,
            MemoryCategory.FACT: 0.008,
            MemoryCategory.EVENT: 0.012,
            MemoryCategory.TEMPORARY: 0.015         # 快速衰减
        }
        
        # 层级权重阈值
        self.level_thresholds = {
            MemoryLevel.FULL: (0.6, float('inf')),
            MemoryLevel.SUMMARY: (0.3, 0.6),
            MemoryLevel.TAG: (0.1, 0.3),
            MemoryLevel.TRACE: (0.05, 0.1),
            MemoryLevel.ARCHIVE: (0.0, 0.05)
        }
        
        # 频繁强化阈值
        self.frequent_window_hours = 24
        self.frequent_threshold = 3
    
    # ------------------------------------------------------------------------
    # 3.1 时间权重 w_time(t)
    # ------------------------------------------------------------------------
    
    def calculate_time_weight(
        self,
        created_at: str,
        last_activated_at: str,
        category: MemoryCategory,
        now: Optional[datetime] = None
    ) -> float:
        """
        计算时间权重
        
        公式: w_time(t) = 1 / (1 + α_effective × t)
        
        α_effective = base_alpha × U × category_factor
        
        使用 last_activated_at 计算活跃衰减
        """
        if now is None:
            now = datetime.now()
        
        # 使用最后激活时间计算
        last_active = datetime.fromisoformat(last_activated_at)
        delta_seconds = (now - last_active).total_seconds()
        t_days = delta_seconds / self.time_scale
        
        # 类别衰减系数
        alpha_base = self.category_decay_alpha.get(category, 0.01)
        alpha_effective = alpha_base * self.user_factor
        
        w_time = 1.0 / (1.0 + alpha_effective * t_days)
        
        return w_time
    
    # ------------------------------------------------------------------------
    # 3.2 语义强化因子 S(t)
    # ------------------------------------------------------------------------
    
    def calculate_semantic_boost(
        self,
        last_mention_time: Optional[str],
        now: Optional[datetime] = None
    ) -> float:
        """
        计算语义强化因子
        
        公式: S(t) = 1 + 0.5 × exp(-0.05 × Δt)
        
        当用户再次提及时，Δt为距上次提及的天数
        """
        if not last_mention_time:
            return 1.0
        
        if now is None:
            now = datetime.now()
        
        last_mention = datetime.fromisoformat(last_mention_time)
        delta_seconds = (now - last_mention).total_seconds()
        delta_days = delta_seconds / self.time_scale
        
        # 语义强化：初始+50%，随时间指数衰减
        boost = 1.0 + 0.5 * math.exp(-0.05 * delta_days)
        
        return boost
    
    # ------------------------------------------------------------------------
    # 3.3 冲突修正因子 C(t)
    # ------------------------------------------------------------------------
    
    def calculate_conflict_penalty(
        self,
        is_negated: bool,
        is_corrected: bool,
        correction_time: Optional[str],
        now: Optional[datetime] = None
    ) -> float:
        """
        计算冲突修正因子
        
        公式: C(t) = 0.3 + 0.7 × exp(-0.01 × Δt)
        
        用户否定时，初始降至30%，随时间缓慢恢复
        """
        if not (is_negated or is_corrected):
            return 1.0
        
        if not correction_time:
            # 刚否定/修正，立即降权
            return 0.3
        
        if now is None:
            now = datetime.now()
        
        correction_dt = datetime.fromisoformat(correction_time)
        delta_seconds = (now - correction_dt).total_seconds()
        delta_days = delta_seconds / self.time_scale
        
        # 冲突惩罚：初始70%降权，随时间恢复
        penalty = 0.3 + 0.7 * math.exp(-0.01 * delta_days)
        
        return penalty
    
    # ------------------------------------------------------------------------
    # 3.4 重要性因子 I
    # ------------------------------------------------------------------------
    
    def get_importance_factor(self, category: MemoryCategory) -> float:
        """获取类别重要性因子"""
        return self.category_importance.get(category, 1.0)
    
    # ------------------------------------------------------------------------
    # 3.5 动量因子 M(t)
    # ------------------------------------------------------------------------
    
    def calculate_momentum(
        self,
        mention_count: int,
        recent_mentions: List[str],
        now: Optional[datetime] = None
    ) -> float:
        """
        计算动量因子（防止过度放大）
        
        公式: M(t) = 1 + 0.3 × (1 - exp(-0.5 × n))
        
        n 为近期提及次数（24小时内），上限约 1.3
        """
        if now is None:
            now = datetime.now()
        
        # 统计近期提及次数
        window_start = now - timedelta(hours=self.frequent_window_hours)
        recent_count = 0
        
        for mention_time_str in recent_mentions:
            mention_time = datetime.fromisoformat(mention_time_str)
            if mention_time >= window_start:
                recent_count += 1
        
        # 动量因子：饱和曲线
        momentum = 1.0 + 0.3 * (1.0 - math.exp(-0.5 * recent_count))
        
        return momentum
    
    # ------------------------------------------------------------------------
    # 3.6 综合权重 W(t)
    # ------------------------------------------------------------------------
    
    def calculate_enhanced_weight(
        self,
        memory: Memory,
        trigger: UpdateTrigger = UpdateTrigger.PASSIVE_DECAY,
        now: Optional[datetime] = None
    ) -> MemoryFactors:
        """
        计算增强型权重
        
        公式: W(t) = w_time(t) × S(t) × C(t) × I × U × M(t)
        """
        metadata = memory.metadata
        
        # 1. 时间权重 w_time(t)
        w_time = self.calculate_time_weight(
            metadata.created_at,
            metadata.last_activated_at,
            metadata.category,
            now
        )
        
        # 2. 语义强化 S(t)
        semantic_boost = self.calculate_semantic_boost(
            metadata.last_mention_time,
            now
        )
        
        # 3. 冲突修正 C(t)
        correction_time = None
        if metadata.correction_history:
            correction_time = metadata.correction_history[-1].get("timestamp")
        
        conflict_penalty = self.calculate_conflict_penalty(
            metadata.is_negated,
            metadata.is_corrected,
            correction_time,
            now
        )
        
        # 4. 重要性 I
        importance = self.get_importance_factor(metadata.category)
        
        # 5. 用户因子 U（已在alpha_effective中使用）
        user_factor = self.user_factor
        
        # 6. 动量 M(t)
        momentum = self.calculate_momentum(
            metadata.mention_count,
            metadata.recent_mentions,
            now
        )
        
        # 综合权重
        factors = MemoryFactors(
            time_weight=w_time,
            semantic_boost=semantic_boost,
            conflict_penalty=conflict_penalty,
            importance=importance,
            user_factor=user_factor,
            momentum=momentum
        )
        
        total_weight = factors.calculate_total()
        
        # 边界约束
        total_weight = max(0.01, min(2.0, total_weight))
        factors.total_weight = total_weight
        
        return factors
    
    # ------------------------------------------------------------------------
    # 4. 决策引擎
    # ------------------------------------------------------------------------
    
    def detect_frequent_reinforce(
        self,
        recent_mentions: List[str],
        now: Optional[datetime] = None
    ) -> bool:
        """检测频繁强化"""
        if now is None:
            now = datetime.now()
        
        window_start = now - timedelta(hours=self.frequent_window_hours)
        recent_count = sum(
            1 for m in recent_mentions
            if datetime.fromisoformat(m) >= window_start
        )
        
        return recent_count >= self.frequent_threshold
    
    def decide_compression_level(
        self,
        weight: float,
        is_frozen: bool,
        is_sensitive: bool,
        sensitivity_level: int
    ) -> MemoryLevel:
        """
        决定压缩层级
        
        规则:
        - 冻结记忆：不压缩
        - 敏感记忆：根据sensitivity_level保护
        - 普通记忆：根据weight阈值压缩
        """
        if is_frozen:
            return MemoryLevel.FULL
        
        # 敏感性保护
        if is_sensitive:
            if sensitivity_level >= 3:
                return MemoryLevel.FULL
            elif sensitivity_level == 2 and weight < 0.3:
                return MemoryLevel.SUMMARY
            elif sensitivity_level == 1 and weight < 0.1:
                return MemoryLevel.TAG
        
        # 根据权重阈值压缩
        for level, (min_w, max_w) in self.level_thresholds.items():
            if min_w <= weight < max_w:
                return level
        
        return MemoryLevel.ARCHIVE
    
    def decide_action(
        self,
        memory: Memory,
        new_content: str,
        similarity: float,
        trigger: UpdateTrigger,
        now: Optional[datetime] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        智能决策引擎
        
        Returns:
            (action, params)
            
        Actions:
            - KEEP: 保持不变
            - COMPRESS: 压缩层级
            - MERGE: 合并更新
            - CREATE_NEW: 新建记忆
            - MARK_NEGATED: 标记否定
            - FREEZE: 冻结
            - DELETE: 删除
        """
        if now is None:
            now = datetime.now()
        
        metadata = memory.metadata
        
        # 1. 用户冻结
        if trigger == UpdateTrigger.MANUAL_FREEZE:
            return ("FREEZE", {})
        
        # 2. 用户删除
        if trigger == UpdateTrigger.MANUAL_DELETE:
            return ("DELETE", {"soft_delete": True})
        
        # 3. 用户否定
        if trigger == UpdateTrigger.USER_NEGATION:
            return ("MARK_NEGATED", {
                "create_new": True,
                "new_content": new_content,
                "penalty": 0.7
            })
        
        # 4. 频繁强化
        if trigger == UpdateTrigger.FREQUENT_REINFORCE:
            is_frequent = self.detect_frequent_reinforce(
                metadata.recent_mentions,
                now
            )
            if is_frequent:
                return ("MERGE", {
                    "update_timestamp": True,
                    "cap_momentum": True,
                    "new_content": new_content
                })
        
        # 5. 用户提及（激活）
        if trigger == UpdateTrigger.USER_MENTION:
            if similarity >= 0.85:
                # 高度相似：合并更新，刷新时间戳
                return ("MERGE", {
                    "update_timestamp": True,
                    "new_content": new_content,
                    "boost_weight": True
                })
            elif similarity >= 0.60:
                # 中度相似：保持旧记忆，创建关联
                return ("CREATE_NEW", {
                    "link_to_old": True,
                    "new_content": new_content
                })
            else:
                # 低相似度：独立新建
                return ("CREATE_NEW", {
                    "new_content": new_content
                })
        
        # 6. 被动衰减（定时服务）
        if trigger == UpdateTrigger.PASSIVE_DECAY:
            # 计算当前权重
            factors = self.calculate_enhanced_weight(memory, trigger, now)
            current_weight = factors.total_weight
            
            # 决定压缩层级
            new_level = self.decide_compression_level(
                current_weight,
                metadata.is_frozen,
                metadata.is_sensitive,
                metadata.sensitivity_level
            )
            
            if new_level != metadata.level:
                return ("COMPRESS", {
                    "new_level": new_level,
                    "weight": current_weight,
                    "factors": factors,
                    "update_timestamp": False  # 不刷新时间戳
                })
            else:
                return ("KEEP", {"weight": current_weight})
        
        # 7. 跨模态更新
        if trigger == UpdateTrigger.CROSS_MODAL_UPDATE:
            return ("MERGE", {
                "update_modalities": True,
                "new_content": new_content
            })
        
        return ("KEEP", {})
    
    # ------------------------------------------------------------------------
    # 5. 批量处理
    # ------------------------------------------------------------------------
    
    def merge_memories_batch(
        self,
        memories: List[Memory],
        store: MemoryStore,
        id_generator,
        user_id: str,
        now: Optional[datetime] = None
    ) -> Memory:
        """
        批量合并相似记忆
        
        策略:
        1. 提取共同特征
        2. 生成摘要（LLM）
        3. 保留溯源链
        4. 累加mention_count
        """
        if now is None:
            now = datetime.now()
        
        # 1. 生成新记忆ID
        new_memory_id = id_generator.generate_memory_id(user_id)
        
        # 2. 提取共同特征
        categories = [m.metadata.category for m in memories]
        most_common_category = max(set(categories), key=categories.count)
        
        modalities_set = set()
        for m in memories:
            modalities_set.update(m.metadata.modalities)
        
        # 3. 生成摘要内容（简化版，生产环境应使用LLM）
        texts = [m.content.text for m in memories if m.content.text]
        summary_text = self._summarize_texts(texts)
        
        # 4. 创建新记忆
        merged_content = MultimodalContent(text=summary_text)
        
        merged_metadata = MemoryMetadata(
            memory_id=new_memory_id,
            device_uuid=memories[0].metadata.device_uuid,
            user_id=user_id,
            created_at=min(m.metadata.created_at for m in memories),  # 最早创建时间
            last_activated_at=now.isoformat(),
            level=MemoryLevel.SUMMARY,
            category=most_common_category,
            modalities=list(modalities_set),
            mention_count=sum(m.metadata.mention_count for m in memories),
            merged_from=[m.memory_id for m in memories]
        )
        
        merged_memory = Memory(
            memory_id=new_memory_id,
            content=merged_content,
            metadata=merged_metadata
        )
        
        # 5. 存储新记忆
        store.add_memory(merged_memory)
        
        # 6. 删除旧记忆（软删除）
        for m in memories:
            store.delete_memory(m.memory_id, soft_delete=True)
        
        logger.info(f"批量合并: {len(memories)}条记忆 → {new_memory_id}")
        
        return merged_memory
    
    def _summarize_texts(self, texts: List[str]) -> str:
        """简化的文本摘要（生产环境应使用LLM）"""
        if not texts:
            return ""
        
        if len(texts) == 1:
            return texts[0]
        
        # 简单合并
        return f"综合摘要: {', '.join(texts[:3])}" + (f" 等{len(texts)}条" if len(texts) > 3 else "")
    
    # ------------------------------------------------------------------------
    # 6. 可解释性日志
    # ------------------------------------------------------------------------
    
    def add_weight_change_log(
        self,
        memory: Memory,
        trigger: UpdateTrigger,
        old_weight: float,
        new_weight: float,
        factors: MemoryFactors,
        reason: str
    ):
        """添加权重变化日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "trigger": trigger.value,
            "old_weight": round(old_weight, 4),
            "new_weight": round(new_weight, 4),
            "change": round(new_weight - old_weight, 4),
            "factors": {
                "w_time": round(factors.time_weight, 4),
                "S": round(factors.semantic_boost, 4),
                "C": round(factors.conflict_penalty, 4),
                "I": round(factors.importance, 4),
                "U": round(factors.user_factor, 4),
                "M": round(factors.momentum, 4)
            },
            "reason": reason
        }
        
        memory.metadata.weight_change_log.append(log_entry)
        
        # 保留最近50条
        if len(memory.metadata.weight_change_log) > 50:
            memory.metadata.weight_change_log = memory.metadata.weight_change_log[-50:]


# 使用示例
if __name__ == "__main__":
    from complete_memory_system import (
        DeviceManager, UserIdentity, MemoryIDGenerator
    )
    
    # 1. 初始化
    device_manager = DeviceManager()
    user_identity = UserIdentity(user_id="user_001")
    id_generator = MemoryIDGenerator(device_manager)
    store = MemoryStore()
    
    # 2. 创建记忆引擎（快遗忘用户）
    engine = CompleteMemoryEngine(user_factor=1.3)
    
    # 3. 创建记忆
    memory_id = id_generator.generate_memory_id(user_identity.user_id)
    content = MultimodalContent(text="我喜欢喝咖啡")
    
    metadata = MemoryMetadata(
        memory_id=memory_id,
        device_uuid=device_manager.get_device_id(),
        user_id=user_identity.user_id,
        created_at=datetime.now().isoformat(),
        last_activated_at=datetime.now().isoformat(),
        category=MemoryCategory.STABLE_PREFERENCE
    )
    
    memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
    store.add_memory(memory)
    
    print("=== 场景1: 被动衰减（30天后）===")
    future_time = datetime.now() + timedelta(days=30)
    factors = engine.calculate_enhanced_weight(
        memory,
        UpdateTrigger.PASSIVE_DECAY,
        future_time
    )
    print(f"权重: {factors.total_weight:.4f}")
    print(f"  w_time: {factors.time_weight:.4f}")
    print(f"  类别: {metadata.category.value}, I={factors.importance}")
    
    print("\n=== 场景2: 用户激活（刷新时间戳）===")
    memory.metadata.last_activated_at = future_time.isoformat()
    memory.metadata.last_mention_time = future_time.isoformat()
    
    factors2 = engine.calculate_enhanced_weight(
        memory,
        UpdateTrigger.USER_MENTION,
        future_time
    )
    print(f"权重: {factors2.total_weight:.4f}")
    print(f"  S(t): {factors2.semantic_boost:.4f} (语义强化)")
    
    print("\n=== 场景3: 决策测试 ===")
    action, params = engine.decide_action(
        memory,
        "我喜欢喝黑咖啡",
        similarity=0.90,
        trigger=UpdateTrigger.USER_MENTION,
        now=future_time
    )
    print(f"决策: {action}")
    print(f"参数: {params}")
