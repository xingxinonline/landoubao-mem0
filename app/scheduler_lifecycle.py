#!/usr/bin/env python3
"""
定时调度服务 & 生命周期管理器

功能:
1. 定时权重计算与自动压缩
2. 批量合并冗余记忆
3. 自动清理无价值记忆
4. 用户控制（冻结/删除）
5. 日志与可解释性
6. 监控指标收集
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import logging
import json

from complete_memory_system import (
    Memory, MemoryStore, MemoryLevel, MemoryCategory
)
from complete_memory_engine import (
    CompleteMemoryEngine, UpdateTrigger
)

logger = logging.getLogger(__name__)


# ============================================================================
# 1. 调度配置
# ============================================================================

@dataclass
class SchedulerConfig:
    """调度器配置"""
    
    # 调度周期
    compression_interval_seconds: int = 3600  # 1小时压缩一次
    merge_interval_seconds: int = 7200        # 2小时合并一次
    cleanup_interval_seconds: int = 86400     # 1天清理一次
    
    # 批量处理
    batch_size: int = 100
    merge_similarity_threshold: float = 0.85
    merge_min_count: int = 3  # 至少3条才合并
    
    # 清理阈值
    cleanup_weight_threshold: float = 0.01
    cleanup_days_threshold: int = 365
    
    # 性能优化
    enable_parallel: bool = True
    max_workers: int = 4


# ============================================================================
# 2. 监控指标
# ============================================================================

@dataclass
class MetricsSnapshot:
    """指标快照"""
    
    timestamp: str
    
    # 记忆统计
    total_memories: int = 0
    level_distribution: Dict[str, int] = field(default_factory=dict)
    category_distribution: Dict[str, int] = field(default_factory=dict)
    
    # 操作统计
    compression_count: int = 0
    merge_count: int = 0
    deletion_count: int = 0
    activation_count: int = 0
    
    # 权重统计
    avg_weight: float = 0.0
    min_weight: float = 0.0
    max_weight: float = 0.0
    
    # 性能统计
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_memories": self.total_memories,
            "level_distribution": self.level_distribution,
            "category_distribution": self.category_distribution,
            "operations": {
                "compression": self.compression_count,
                "merge": self.merge_count,
                "deletion": self.deletion_count,
                "activation": self.activation_count
            },
            "weights": {
                "avg": round(self.avg_weight, 4),
                "min": round(self.min_weight, 4),
                "max": round(self.max_weight, 4)
            },
            "performance_ms": round(self.processing_time_ms, 2)
        }


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.snapshots: List[MetricsSnapshot] = []
        self.operation_counters = {
            "compression": 0,
            "merge": 0,
            "deletion": 0,
            "activation": 0,
            "negation": 0
        }
    
    def collect_snapshot(
        self,
        store: MemoryStore,
        engine: CompleteMemoryEngine,
        processing_time_ms: float = 0.0
    ) -> MetricsSnapshot:
        """收集指标快照"""
        
        all_memories = list(store.memories.values())
        
        # 层级分布
        level_dist = {}
        for level in MemoryLevel:
            count = sum(1 for m in all_memories if m.metadata.level == level)
            level_dist[level.value] = count
        
        # 类别分布
        category_dist = {}
        for category in MemoryCategory:
            count = sum(1 for m in all_memories if m.metadata.category == category)
            category_dist[category.value] = count
        
        # 权重统计
        weights = []
        for memory in all_memories:
            if not memory.metadata.is_deleted:
                factors = engine.calculate_enhanced_weight(memory)
                weights.append(factors.total_weight)
        
        snapshot = MetricsSnapshot(
            timestamp=datetime.now().isoformat(),
            total_memories=len(all_memories),
            level_distribution=level_dist,
            category_distribution=category_dist,
            compression_count=self.operation_counters["compression"],
            merge_count=self.operation_counters["merge"],
            deletion_count=self.operation_counters["deletion"],
            activation_count=self.operation_counters["activation"],
            avg_weight=sum(weights) / len(weights) if weights else 0.0,
            min_weight=min(weights) if weights else 0.0,
            max_weight=max(weights) if weights else 0.0,
            processing_time_ms=processing_time_ms
        )
        
        self.snapshots.append(snapshot)
        
        # 保留最近100条
        if len(self.snapshots) > 100:
            self.snapshots = self.snapshots[-100:]
        
        return snapshot
    
    def increment_operation(self, operation: str):
        """增加操作计数"""
        if operation in self.operation_counters:
            self.operation_counters[operation] += 1
    
    def export_metrics(self, filepath: str):
        """导出指标"""
        data = {
            "snapshots": [s.to_dict() for s in self.snapshots],
            "operation_counters": self.operation_counters
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================================
# 3. 定时调度服务
# ============================================================================

class MemoryScheduler:
    """记忆调度服务"""
    
    def __init__(
        self,
        store: MemoryStore,
        engine: CompleteMemoryEngine,
        id_generator,
        config: Optional[SchedulerConfig] = None
    ):
        self.store = store
        self.engine = engine
        self.id_generator = id_generator
        self.config = config or SchedulerConfig()
        
        self.metrics = MetricsCollector()
        self.is_running = False
        
        # 任务句柄
        self._compression_task = None
        self._merge_task = None
        self._cleanup_task = None
    
    # ------------------------------------------------------------------------
    # 3.1 自动压缩任务
    # ------------------------------------------------------------------------
    
    async def _auto_compression_loop(self):
        """自动压缩循环"""
        
        while self.is_running:
            try:
                logger.info("开始自动压缩...")
                start_time = datetime.now()
                
                # 处理所有用户的记忆
                for user_id in self.store.user_index.keys():
                    await self._compress_user_memories(user_id)
                
                # 收集指标
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                snapshot = self.metrics.collect_snapshot(
                    self.store,
                    self.engine,
                    elapsed_ms
                )
                
                logger.info(f"自动压缩完成: {snapshot.compression_count} 条记忆")
                
            except Exception as e:
                logger.error(f"自动压缩失败: {e}", exc_info=True)
            
            # 等待下次调度
            await asyncio.sleep(self.config.compression_interval_seconds)
    
    async def _compress_user_memories(self, user_id: str):
        """压缩用户记忆"""
        
        memories = self.store.get_user_memories(user_id)
        now = datetime.now()
        
        for memory in memories:
            # 跳过冻结/删除/敏感
            if memory.metadata.is_frozen:
                continue
            if memory.metadata.is_deleted:
                continue
            if memory.metadata.is_sensitive and memory.metadata.sensitivity_level >= 3:
                continue
            
            # 计算当前权重
            old_factors = memory.metadata.factors
            old_weight = old_factors.total_weight
            
            new_factors = self.engine.calculate_enhanced_weight(
                memory,
                UpdateTrigger.PASSIVE_DECAY,
                now
            )
            new_weight = new_factors.total_weight
            
            # 更新因子
            memory.metadata.factors = new_factors
            
            # 决定是否压缩
            new_level = self.engine.decide_compression_level(
                new_weight,
                memory.metadata.is_frozen,
                memory.metadata.is_sensitive,
                memory.metadata.sensitivity_level
            )
            
            if new_level != memory.metadata.level:
                # 执行压缩
                self._compress_memory(memory, new_level, old_weight, new_weight, new_factors)
                self.metrics.increment_operation("compression")
    
    def _compress_memory(
        self,
        memory: Memory,
        new_level: MemoryLevel,
        old_weight: float,
        new_weight: float,
        factors
    ):
        """执行记忆压缩"""
        
        old_level = memory.metadata.level
        
        # 更新层级
        memory.metadata.level = new_level
        
        # 记录压缩历史
        compression_entry = {
            "timestamp": datetime.now().isoformat(),
            "old_level": old_level.value,
            "new_level": new_level.value,
            "old_weight": round(old_weight, 4),
            "new_weight": round(new_weight, 4),
            "reason": "自动压缩（定时服务）"
        }
        memory.metadata.compression_history.append(compression_entry)
        
        # 添加权重变化日志
        self.engine.add_weight_change_log(
            memory,
            UpdateTrigger.PASSIVE_DECAY,
            old_weight,
            new_weight,
            factors,
            f"层级压缩: {old_level.value} → {new_level.value}"
        )
        
        logger.debug(
            f"压缩记忆 {memory.memory_id[:16]}: "
            f"{old_level.value} → {new_level.value} "
            f"(权重 {old_weight:.4f} → {new_weight:.4f})"
        )
    
    # ------------------------------------------------------------------------
    # 3.2 批量合并任务
    # ------------------------------------------------------------------------
    
    async def _auto_merge_loop(self):
        """自动合并循环"""
        
        while self.is_running:
            try:
                logger.info("开始批量合并...")
                
                for user_id in self.store.user_index.keys():
                    await self._merge_user_memories(user_id)
                
                logger.info(f"批量合并完成: {self.metrics.operation_counters['merge']} 次")
                
            except Exception as e:
                logger.error(f"批量合并失败: {e}", exc_info=True)
            
            await asyncio.sleep(self.config.merge_interval_seconds)
    
    async def _merge_user_memories(self, user_id: str):
        """合并用户记忆"""
        
        memories = self.store.get_user_memories(user_id)
        
        # 按类别分组
        category_groups: Dict[MemoryCategory, List[Memory]] = {}
        
        for memory in memories:
            if memory.metadata.is_deleted:
                continue
            if memory.metadata.is_frozen:
                continue
            
            category = memory.metadata.category
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(memory)
        
        # 对每个类别，查找相似记忆并合并
        for category, group_memories in category_groups.items():
            if len(group_memories) < self.config.merge_min_count:
                continue
            
            # 查找高度相似的记忆组
            similar_groups = self._find_similar_groups(
                group_memories,
                self.config.merge_similarity_threshold
            )
            
            for similar_group in similar_groups:
                if len(similar_group) >= self.config.merge_min_count:
                    # 批量合并
                    merged = self.engine.merge_memories_batch(
                        similar_group,
                        self.store,
                        self.id_generator,
                        user_id
                    )
                    
                    self.metrics.increment_operation("merge")
                    
                    logger.info(
                        f"合并 {len(similar_group)} 条记忆 → {merged.memory_id[:16]}"
                    )
    
    def _find_similar_groups(
        self,
        memories: List[Memory],
        threshold: float
    ) -> List[List[Memory]]:
        """查找相似记忆组"""
        
        # 简化版：使用贪心算法
        # TODO: 生产环境使用聚类算法（DBSCAN、层次聚类等）
        
        groups = []
        visited = set()
        
        for i, mem1 in enumerate(memories):
            if i in visited:
                continue
            
            group = [mem1]
            visited.add(i)
            
            for j, mem2 in enumerate(memories[i+1:], i+1):
                if j in visited:
                    continue
                
                # 计算相似度（简化版）
                text1 = mem1.content.text or ""
                text2 = mem2.content.text or ""
                
                tokens1 = set(text1.lower().split())
                tokens2 = set(text2.lower().split())
                
                if not tokens1 or not tokens2:
                    continue
                
                similarity = len(tokens1 & tokens2) / len(tokens1 | tokens2)
                
                if similarity >= threshold:
                    group.append(mem2)
                    visited.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    # ------------------------------------------------------------------------
    # 3.3 自动清理任务
    # ------------------------------------------------------------------------
    
    async def _auto_cleanup_loop(self):
        """自动清理循环"""
        
        while self.is_running:
            try:
                logger.info("开始自动清理...")
                
                for user_id in self.store.user_index.keys():
                    await self._cleanup_user_memories(user_id)
                
                logger.info(f"自动清理完成: {self.metrics.operation_counters['deletion']} 条")
                
            except Exception as e:
                logger.error(f"自动清理失败: {e}", exc_info=True)
            
            await asyncio.sleep(self.config.cleanup_interval_seconds)
    
    async def _cleanup_user_memories(self, user_id: str):
        """清理用户记忆"""
        
        memories = self.store.get_user_memories(user_id)
        now = datetime.now()
        
        to_delete = []
        
        for memory in memories:
            # 已删除的软删除记忆，超过30天后硬删除
            if memory.metadata.is_deleted:
                deletion_time = datetime.fromisoformat(memory.metadata.deletion_time)
                if (now - deletion_time).days >= 30:
                    to_delete.append(memory.memory_id)
                    continue
            
            # 跳过冻结/敏感
            if memory.metadata.is_frozen:
                continue
            if memory.metadata.is_sensitive:
                continue
            
            # 权重极低且时间久远
            factors = self.engine.calculate_enhanced_weight(memory, now=now)
            
            if factors.total_weight < self.config.cleanup_weight_threshold:
                created_time = datetime.fromisoformat(memory.metadata.created_at)
                days_old = (now - created_time).days
                
                if days_old >= self.config.cleanup_days_threshold:
                    to_delete.append(memory.memory_id)
        
        # 执行删除
        for memory_id in to_delete:
            self.store.delete_memory(memory_id, soft_delete=False)
            self.metrics.increment_operation("deletion")
            logger.info(f"清理记忆: {memory_id[:16]}")
    
    # ------------------------------------------------------------------------
    # 3.4 启动/停止
    # ------------------------------------------------------------------------
    
    async def start(self):
        """启动调度服务"""
        
        if self.is_running:
            logger.warning("调度服务已在运行")
            return
        
        self.is_running = True
        
        # 启动三个任务
        self._compression_task = asyncio.create_task(self._auto_compression_loop())
        self._merge_task = asyncio.create_task(self._auto_merge_loop())
        self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
        
        logger.info("调度服务已启动")
    
    async def stop(self):
        """停止调度服务"""
        
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 取消任务
        if self._compression_task:
            self._compression_task.cancel()
        if self._merge_task:
            self._merge_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        logger.info("调度服务已停止")


# ============================================================================
# 4. 生命周期管理器
# ============================================================================

class LifecycleManager:
    """生命周期管理器"""
    
    def __init__(self, store: MemoryStore, engine: CompleteMemoryEngine):
        self.store = store
        self.engine = engine
    
    # ------------------------------------------------------------------------
    # 4.1 用户控制
    # ------------------------------------------------------------------------
    
    def freeze_memory(self, memory_id: str):
        """冻结记忆（禁止自动压缩）"""
        
        memory = self.store.get_memory(memory_id)
        if not memory:
            logger.warning(f"记忆不存在: {memory_id}")
            return
        
        memory.metadata.is_frozen = True
        
        logger.info(f"冻结记忆: {memory_id[:16]}")
    
    def unfreeze_memory(self, memory_id: str):
        """解冻记忆"""
        
        memory = self.store.get_memory(memory_id)
        if not memory:
            return
        
        memory.metadata.is_frozen = False
        
        logger.info(f"解冻记忆: {memory_id[:16]}")
    
    def delete_memory(self, memory_id: str, soft: bool = True):
        """删除记忆"""
        
        self.store.delete_memory(memory_id, soft_delete=soft)
        
        logger.info(f"{'软' if soft else '硬'}删除记忆: {memory_id[:16]}")
    
    def mark_sensitive(
        self,
        memory_id: str,
        sensitivity_level: int,
        encrypt: bool = False
    ):
        """标记敏感记忆"""
        
        memory = self.store.get_memory(memory_id)
        if not memory:
            return
        
        memory.metadata.is_sensitive = True
        memory.metadata.sensitivity_level = min(3, max(0, sensitivity_level))
        memory.metadata.is_encrypted = encrypt
        
        logger.info(
            f"标记敏感: {memory_id[:16]} "
            f"(等级 {sensitivity_level}, 加密={encrypt})"
        )
    
    # ------------------------------------------------------------------------
    # 4.2 日志与可解释性
    # ------------------------------------------------------------------------
    
    def get_weight_history(self, memory_id: str) -> List[Dict]:
        """获取权重变化历史"""
        
        memory = self.store.get_memory(memory_id)
        if not memory:
            return []
        
        return memory.metadata.weight_change_log
    
    def get_compression_history(self, memory_id: str) -> List[Dict]:
        """获取压缩历史"""
        
        memory = self.store.get_memory(memory_id)
        if not memory:
            return []
        
        return memory.metadata.compression_history
    
    def explain_weight(self, memory_id: str) -> Dict[str, Any]:
        """解释当前权重"""
        
        memory = self.store.get_memory(memory_id)
        if not memory:
            return {}
        
        factors = self.engine.calculate_enhanced_weight(memory)
        
        return {
            "memory_id": memory_id,
            "total_weight": round(factors.total_weight, 4),
            "factors": {
                "w_time": round(factors.time_weight, 4),
                "S(t)": round(factors.semantic_boost, 4),
                "C(t)": round(factors.conflict_penalty, 4),
                "I": round(factors.importance, 4),
                "U": round(factors.user_factor, 4),
                "M(t)": round(factors.momentum, 4)
            },
            "level": memory.metadata.level.value,
            "category": memory.metadata.category.value,
            "created_at": memory.metadata.created_at,
            "last_activated_at": memory.metadata.last_activated_at,
            "mention_count": memory.metadata.mention_count
        }


# ============================================================================
# 使用示例
# ============================================================================

async def main():
    from complete_memory_system import (
        DeviceManager, UserIdentity, MemoryIDGenerator,
        MultimodalContent, MemoryMetadata
    )
    
    # 1. 初始化
    device_manager = DeviceManager()
    user_identity = UserIdentity(user_id="user_001")
    id_generator = MemoryIDGenerator(device_manager)
    store = MemoryStore()
    
    # 2. 创建引擎（时间刻度=1秒，模拟快速运行）
    engine = CompleteMemoryEngine(user_factor=1.0, time_scale=1)
    
    # 3. 创建测试记忆
    for i in range(5):
        memory_id = id_generator.generate_memory_id(user_identity.user_id)
        content = MultimodalContent(text=f"测试记忆 {i+1}")
        
        metadata = MemoryMetadata(
            memory_id=memory_id,
            device_uuid=device_manager.get_device_id(),
            user_id=user_identity.user_id,
            created_at=datetime.now().isoformat(),
            last_activated_at=datetime.now().isoformat(),
            category=MemoryCategory.TEMPORARY
        )
        
        memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
        store.add_memory(memory)
    
    print(f"创建 {len(store.memories)} 条测试记忆")
    
    # 4. 创建调度器（快速运行）
    config = SchedulerConfig(
        compression_interval_seconds=5,  # 5秒压缩
        merge_interval_seconds=10,       # 10秒合并
        cleanup_interval_seconds=15      # 15秒清理
    )
    
    scheduler = MemoryScheduler(store, engine, id_generator, config)
    
    # 5. 启动调度服务
    await scheduler.start()
    
    print("调度服务已启动，运行30秒...")
    await asyncio.sleep(30)
    
    # 6. 停止服务
    await scheduler.stop()
    
    # 7. 导出指标
    scheduler.metrics.export_metrics("scheduler_metrics.json")
    print("指标已导出")
    
    # 8. 生命周期管理
    lifecycle = LifecycleManager(store, engine)
    
    if store.memories:
        first_id = list(store.memories.keys())[0]
        
        print(f"\n=== 权重解释 ===")
        explanation = lifecycle.explain_weight(first_id)
        print(json.dumps(explanation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
