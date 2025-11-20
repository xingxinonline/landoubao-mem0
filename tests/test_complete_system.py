#!/usr/bin/env python3
"""
完整记忆系统综合测试

测试场景：
1. 身份与根ID管理
2. 多模态记忆存储
3. 增强型衰退曲线
4. 智能检索与Reranker
5. 定时调度服务
6. 生命周期管理
7. 特殊情形处理
"""

import asyncio
from datetime import datetime, timedelta
import logging

from complete_memory_system import (
    DeviceManager, UserIdentity, MemoryIDGenerator,
    MemoryStore, Memory, MultimodalContent, MemoryMetadata,
    MemoryLevel, MemoryCategory, Modality, QueryMode
)
from complete_memory_engine import (
    CompleteMemoryEngine, UpdateTrigger
)
from smart_retriever import (
    SmartRetriever, RetrievalConfig
)
from scheduler_lifecycle import (
    MemoryScheduler, LifecycleManager, SchedulerConfig
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompleteMemorySystemTest:
    """完整记忆系统测试"""
    
    def __init__(self):
        # 初始化组件
        self.device_manager = DeviceManager()
        self.user_identity = UserIdentity(user_id="alice")
        self.id_generator = MemoryIDGenerator(self.device_manager)
        self.store = MemoryStore()
        
        # 创建引擎（时间刻度=60秒，1分钟=1天）
        self.engine = CompleteMemoryEngine(
            user_factor=1.0,
            time_scale=60  # 1分钟 = 1天
        )
        
        # 创建检索器
        self.retriever = SmartRetriever(self.engine)
        
        # 创建调度器
        scheduler_config = SchedulerConfig(
            compression_interval_seconds=10,  # 10秒压缩一次
            merge_interval_seconds=20,
            cleanup_interval_seconds=30
        )
        self.scheduler = MemoryScheduler(
            self.store,
            self.engine,
            self.id_generator,
            scheduler_config
        )
        
        # 创建生命周期管理器
        self.lifecycle = LifecycleManager(self.store, self.engine)
    
    def test_1_identity_management(self):
        """测试1: 身份与根ID管理"""
        
        print("\n" + "="*60)
        print("测试1: 身份与根ID管理")
        print("="*60)
        
        # 设备UUID
        device_id = self.device_manager.get_device_id()
        print(f"✓ 设备UUID: {device_id}")
        
        # 用户ID
        user_id = self.user_identity.user_id
        print(f"✓ 用户ID: {user_id}")
        
        # 生成记忆ID
        memory_id = self.id_generator.generate_memory_id(user_id)
        print(f"✓ 记忆ID: {memory_id}")
        
        # 解析记忆ID
        parsed = self.id_generator.parse_memory_id(memory_id)
        print(f"✓ 解析结果: {parsed}")
        
        assert parsed["user_id"] == user_id
        assert parsed["device_uuid"] == device_id[:8]
        
        print("✓ 身份管理测试通过")
    
    def test_2_multimodal_storage(self):
        """测试2: 多模态记忆存储"""
        
        print("\n" + "="*60)
        print("测试2: 多模态记忆存储")
        print("="*60)
        
        # 创建多模态内容
        content = MultimodalContent(
            text="我喜欢这张照片",
            image_url="https://example.com/photo.jpg",
            audio_url="https://example.com/voice.mp3"
        )
        
        modalities = content.get_modalities()
        print(f"✓ 模态类型: {[m.value for m in modalities]}")
        
        # 创建记忆
        memory_id = self.id_generator.generate_memory_id(self.user_identity.user_id)
        metadata = MemoryMetadata(
            memory_id=memory_id,
            device_uuid=self.device_manager.get_device_id(),
            user_id=self.user_identity.user_id,
            created_at=datetime.now().isoformat(),
            last_activated_at=datetime.now().isoformat(),
            category=MemoryCategory.EVENT,
            modalities=modalities
        )
        
        memory = Memory(
            memory_id=memory_id,
            content=content,
            metadata=metadata,
            tags=["照片", "语音", "回忆"]
        )
        
        # 存储
        self.store.add_memory(memory)
        
        # 验证
        retrieved = self.store.get_memory(memory_id)
        assert retrieved is not None
        assert len(retrieved.metadata.modalities) == 3
        assert Modality.TEXT in retrieved.metadata.modalities
        assert Modality.IMAGE in retrieved.metadata.modalities
        assert Modality.AUDIO in retrieved.metadata.modalities
        
        print("✓ 多模态存储测试通过")
    
    def test_3_enhanced_decay_curve(self):
        """测试3: 增强型衰退曲线"""
        
        print("\n" + "="*60)
        print("测试3: 增强型衰退曲线（6因子）")
        print("="*60)
        
        # 创建记忆
        memory_id = self.id_generator.generate_memory_id(self.user_identity.user_id)
        content = MultimodalContent(text="我叫Alice")
        
        base_time = datetime.now()
        metadata = MemoryMetadata(
            memory_id=memory_id,
            device_uuid=self.device_manager.get_device_id(),
            user_id=self.user_identity.user_id,
            created_at=base_time.isoformat(),
            last_activated_at=base_time.isoformat(),
            category=MemoryCategory.IDENTITY,  # 身份信息
            mention_count=5
        )
        
        memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
        
        # 场景1: 初始权重
        factors_0 = self.engine.calculate_enhanced_weight(memory, now=base_time)
        print(f"\n场景1 - 初始权重:")
        print(f"  W(0) = {factors_0.total_weight:.4f}")
        print(f"  w_time = {factors_0.time_weight:.4f}")
        print(f"  I = {factors_0.importance:.4f} (身份类别)")
        
        # 场景2: 30天后被动衰减
        future_30d = base_time + timedelta(days=30)
        factors_30 = self.engine.calculate_enhanced_weight(
            memory,
            UpdateTrigger.PASSIVE_DECAY,
            now=future_30d
        )
        print(f"\n场景2 - 30天后被动衰减:")
        print(f"  W(30) = {factors_30.total_weight:.4f}")
        print(f"  w_time = {factors_30.time_weight:.4f}")
        
        # 场景3: 用户激活（刷新时间戳）
        memory.metadata.last_activated_at = future_30d.isoformat()
        memory.metadata.last_mention_time = future_30d.isoformat()
        
        factors_activated = self.engine.calculate_enhanced_weight(
            memory,
            UpdateTrigger.USER_MENTION,
            now=future_30d
        )
        print(f"\n场景3 - 用户激活:")
        print(f"  W(激活) = {factors_activated.total_weight:.4f}")
        print(f"  S(t) = {factors_activated.semantic_boost:.4f} (语义强化)")
        
        # 场景4: 用户否定
        memory.metadata.is_negated = True
        memory.metadata.correction_history = [{
            "timestamp": future_30d.isoformat()
        }]
        
        factors_negated = self.engine.calculate_enhanced_weight(
            memory,
            UpdateTrigger.USER_NEGATION,
            now=future_30d
        )
        print(f"\n场景4 - 用户否定:")
        print(f"  W(否定) = {factors_negated.total_weight:.4f}")
        print(f"  C(t) = {factors_negated.conflict_penalty:.4f} (冲突惩罚)")
        
        # 验证
        assert factors_0.total_weight > factors_30.total_weight  # 衰减
        assert factors_activated.total_weight > factors_30.total_weight  # 激活提升
        assert factors_negated.total_weight < factors_30.total_weight  # 否定降权
        
        print("\n✓ 增强型衰退曲线测试通过")
    
    def test_4_smart_retrieval(self):
        """测试4: 智能检索与Reranker"""
        
        print("\n" + "="*60)
        print("测试4: 智能检索与Reranker")
        print("="*60)
        
        # 创建测试记忆集
        test_data = [
            ("我喜欢喝咖啡", MemoryCategory.STABLE_PREFERENCE, 0),
            ("我喜欢喝黑咖啡", MemoryCategory.STABLE_PREFERENCE, 1),
            ("今天喝了一杯拿铁", MemoryCategory.EVENT, 3),
            ("我叫Alice", MemoryCategory.IDENTITY, 0),
            ("明天要开会", MemoryCategory.TEMPORARY, 5),
        ]
        
        memories = []
        base_time = datetime.now()
        
        for text, category, days_ago in test_data:
            memory_id = self.id_generator.generate_memory_id(self.user_identity.user_id)
            content = MultimodalContent(text=text)
            
            created_time = base_time - timedelta(days=days_ago)
            
            metadata = MemoryMetadata(
                memory_id=memory_id,
                device_uuid=self.device_manager.get_device_id(),
                user_id=self.user_identity.user_id,
                created_at=created_time.isoformat(),
                last_activated_at=created_time.isoformat(),
                category=category,
                mention_count=3 if "咖啡" in text else 1
            )
            
            memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
            memories.append(memory)
        
        # 测试检索
        config = RetrievalConfig(
            query_mode=QueryMode.NORMAL,
            top_k=3,
            similarity_threshold=0.1
        )
        
        results = self.retriever.retrieve(
            query="咖啡偏好",
            memories=memories,
            config=config
        )
        
        print(f"\n检索结果 (Top-{len(results)}):")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.memory.content.text}")
            print(f"   相关性: {result.relevance_score:.4f}")
            print(f"   类别: {result.memory.metadata.category.value}")
            print(f"   层级: {result.memory.metadata.level.value}")
        
        # 验证
        assert len(results) > 0
        assert "咖啡" in results[0].memory.content.text
        
        print("\n✓ 智能检索测试通过")
    
    async def test_5_scheduler(self):
        """测试5: 定时调度服务"""
        
        print("\n" + "="*60)
        print("测试5: 定时调度服务")
        print("="*60)
        
        # 创建临时记忆（快速衰减）
        for i in range(3):
            memory_id = self.id_generator.generate_memory_id(self.user_identity.user_id)
            content = MultimodalContent(text=f"临时记忆 {i+1}")
            
            # 创建1天前的记忆
            past_time = datetime.now() - timedelta(minutes=1)  # 1分钟=1天
            
            metadata = MemoryMetadata(
                memory_id=memory_id,
                device_uuid=self.device_manager.get_device_id(),
                user_id=self.user_identity.user_id,
                created_at=past_time.isoformat(),
                last_activated_at=past_time.isoformat(),
                category=MemoryCategory.TEMPORARY
            )
            
            memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
            self.store.add_memory(memory)
        
        print(f"✓ 创建 {len(self.store.memories)} 条记忆")
        
        # 启动调度器
        await self.scheduler.start()
        print("✓ 调度器已启动，运行15秒...")
        
        await asyncio.sleep(15)
        
        # 停止调度器
        await self.scheduler.stop()
        print("✓ 调度器已停止")
        
        # 检查指标
        snapshot = self.scheduler.metrics.snapshots[-1] if self.scheduler.metrics.snapshots else None
        if snapshot:
            print(f"\n指标快照:")
            print(f"  总记忆数: {snapshot.total_memories}")
            print(f"  压缩次数: {snapshot.compression_count}")
            print(f"  平均权重: {snapshot.avg_weight:.4f}")
            print(f"  层级分布: {snapshot.level_distribution}")
        
        print("\n✓ 定时调度测试通过")
    
    def test_6_lifecycle_management(self):
        """测试6: 生命周期管理"""
        
        print("\n" + "="*60)
        print("测试6: 生命周期管理")
        print("="*60)
        
        # 创建测试记忆
        memory_id = self.id_generator.generate_memory_id(self.user_identity.user_id)
        content = MultimodalContent(text="重要的私密信息")
        
        metadata = MemoryMetadata(
            memory_id=memory_id,
            device_uuid=self.device_manager.get_device_id(),
            user_id=self.user_identity.user_id,
            created_at=datetime.now().isoformat(),
            last_activated_at=datetime.now().isoformat(),
            category=MemoryCategory.IDENTITY
        )
        
        memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
        self.store.add_memory(memory)
        
        # 测试冻结
        print("\n测试冻结:")
        self.lifecycle.freeze_memory(memory_id)
        assert memory.metadata.is_frozen == True
        print("✓ 记忆已冻结")
        
        # 测试敏感标记
        print("\n测试敏感标记:")
        self.lifecycle.mark_sensitive(memory_id, sensitivity_level=3, encrypt=True)
        assert memory.metadata.is_sensitive == True
        assert memory.metadata.sensitivity_level == 3
        assert memory.metadata.is_encrypted == True
        print("✓ 记忆已标记为敏感（等级3，加密）")
        
        # 测试权重解释
        print("\n测试权重解释:")
        explanation = self.lifecycle.explain_weight(memory_id)
        print(f"  总权重: {explanation['total_weight']}")
        print(f"  因子: {explanation['factors']}")
        print("✓ 权重解释生成成功")
        
        # 测试软删除
        print("\n测试软删除:")
        self.lifecycle.delete_memory(memory_id, soft=True)
        assert memory.metadata.is_deleted == True
        print("✓ 记忆已软删除")
        
        print("\n✓ 生命周期管理测试通过")
    
    def test_7_special_scenarios(self):
        """测试7: 特殊情形处理"""
        
        print("\n" + "="*60)
        print("测试7: 特殊情形处理")
        print("="*60)
        
        # 场景1: 频繁强化检测
        print("\n场景1 - 频繁强化:")
        memory_id = self.id_generator.generate_memory_id(self.user_identity.user_id)
        content = MultimodalContent(text="我喜欢巧克力")
        
        now = datetime.now()
        recent_mentions = [
            (now - timedelta(hours=1)).isoformat(),
            (now - timedelta(hours=5)).isoformat(),
            (now - timedelta(hours=10)).isoformat(),
        ]
        
        metadata = MemoryMetadata(
            memory_id=memory_id,
            device_uuid=self.device_manager.get_device_id(),
            user_id=self.user_identity.user_id,
            created_at=now.isoformat(),
            last_activated_at=now.isoformat(),
            category=MemoryCategory.SHORT_PREFERENCE,
            recent_mentions=recent_mentions,
            mention_count=3
        )
        
        memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
        
        is_frequent = self.engine.detect_frequent_reinforce(recent_mentions, now)
        print(f"  24小时内提及: {len(recent_mentions)} 次")
        print(f"  检测结果: {'频繁强化' if is_frequent else '正常'}")
        assert is_frequent == True
        
        # 场景2: 用户否定决策
        print("\n场景2 - 用户否定:")
        action, params = self.engine.decide_action(
            memory,
            new_content="我不喜欢巧克力",
            similarity=0.70,
            trigger=UpdateTrigger.USER_NEGATION,
            now=now
        )
        print(f"  决策: {action}")
        print(f"  参数: {params}")
        assert action == "MARK_NEGATED"
        assert params.get("create_new") == True
        
        # 场景3: 批量合并
        print("\n场景3 - 批量合并:")
        similar_memories = []
        for i in range(3):
            mid = self.id_generator.generate_memory_id(self.user_identity.user_id)
            c = MultimodalContent(text=f"我喜欢喝咖啡 {i+1}")
            m = MemoryMetadata(
                memory_id=mid,
                device_uuid=self.device_manager.get_device_id(),
                user_id=self.user_identity.user_id,
                created_at=now.isoformat(),
                last_activated_at=now.isoformat(),
                category=MemoryCategory.STABLE_PREFERENCE
            )
            mem = Memory(memory_id=mid, content=c, metadata=m)
            similar_memories.append(mem)
            self.store.add_memory(mem)
        
        merged = self.engine.merge_memories_batch(
            similar_memories,
            self.store,
            self.id_generator,
            self.user_identity.user_id,
            now
        )
        
        print(f"  合并前: {len(similar_memories)} 条")
        print(f"  合并后: 1 条 (ID: {merged.memory_id[:16]}...)")
        print(f"  层级: {merged.metadata.level.value}")
        print(f"  提及次数: {merged.metadata.mention_count}")
        assert merged.metadata.level == MemoryLevel.SUMMARY
        assert merged.metadata.mention_count == sum(m.metadata.mention_count for m in similar_memories)
        
        print("\n✓ 特殊情形处理测试通过")
    
    async def run_all_tests(self):
        """运行所有测试"""
        
        print("\n" + "="*60)
        print("完整记忆系统综合测试")
        print("="*60)
        
        self.test_1_identity_management()
        self.test_2_multimodal_storage()
        self.test_3_enhanced_decay_curve()
        self.test_4_smart_retrieval()
        await self.test_5_scheduler()
        self.test_6_lifecycle_management()
        self.test_7_special_scenarios()
        
        print("\n" + "="*60)
        print("✓ 所有测试通过！")
        print("="*60)


async def main():
    test_suite = CompleteMemorySystemTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
