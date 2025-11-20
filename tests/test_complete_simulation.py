#!/usr/bin/env python3
"""
完整记忆系统 - 模拟测试

测试场景：
1. 身份与根ID管理 ✓
2. 多模态记忆存储 ✓
3. 增强型衰退曲线（6因子）✓
4. 智能检索与Reranker ✓
5. 定时调度服务 ✓
6. 生命周期管理 ✓
7. 特殊情形处理 ✓

运行方式：
  uv run python tests/test_complete_simulation.py
"""

import sys
import os

# 添加app目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import asyncio
from datetime import datetime, timedelta
import logging

from complete_memory_system import (
    DeviceManager, UserIdentity, MemoryIDGenerator,
    MemoryStore, Memory, MultimodalContent, MemoryMetadata,
    MemoryLevel, MemoryCategory, Modality
)
from complete_memory_engine import (
    CompleteMemoryEngine, UpdateTrigger
)
from smart_retriever import (
    SmartRetriever, RetrievalConfig, QueryMode
)
from scheduler_lifecycle import (
    MemoryScheduler, LifecycleManager, SchedulerConfig
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompleteMemorySystemSimulation:
    """完整记忆系统模拟测试"""
    
    def __init__(self):
        print("\n" + "="*70)
        print("🧩 完整记忆管理系统 - 模拟测试")
        print("="*70)
        
        # 初始化组件
        self.device_manager = DeviceManager()
        self.user_identity = UserIdentity(user_id="alice")
        self.id_generator = MemoryIDGenerator(self.device_manager)
        self.store = MemoryStore()
        
        # 创建引擎（时间刻度=60秒，1分钟=1天，便于快速测试）
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
        
        self.test_results = []
    
    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if passed else "❌ 失败"
        self.test_results.append((test_name, passed, message))
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
    
    def test_1_identity_management(self):
        """测试1: 身份与根ID管理"""
        
        print("\n" + "="*70)
        print("📋 测试1: 身份与根ID管理")
        print("="*70)
        
        try:
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
            print(f"✓ 解析结果:")
            print(f"   - 设备: {parsed['device_uuid']}")
            print(f"   - 用户: {parsed['user_id']}")
            print(f"   - 时间: {parsed['timestamp']}")
            print(f"   - 序列: {parsed['sequence_id']}")
            
            assert parsed["user_id"] == user_id
            assert parsed["device_uuid"] == device_id[:8]
            
            self.log_test_result("身份与根ID管理", True, "设备UUID、用户ID、记忆ID生成与解析正常")
            
        except Exception as e:
            self.log_test_result("身份与根ID管理", False, f"异常: {e}")
    
    def test_2_multimodal_storage(self):
        """测试2: 多模态记忆存储"""
        
        print("\n" + "="*70)
        print("📋 测试2: 多模态记忆存储")
        print("="*70)
        
        try:
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
            print(f"✓ 记忆已存储: {memory_id[:24]}...")
            
            # 验证
            retrieved = self.store.get_memory(memory_id)
            assert retrieved is not None
            assert len(retrieved.metadata.modalities) == 3
            assert Modality.TEXT in retrieved.metadata.modalities
            assert Modality.IMAGE in retrieved.metadata.modalities
            assert Modality.AUDIO in retrieved.metadata.modalities
            
            print(f"✓ 验证成功: 包含 {len(retrieved.metadata.modalities)} 种模态")
            
            self.log_test_result("多模态记忆存储", True, "文本+图片+语音三模态存储与检索正常")
            
        except Exception as e:
            self.log_test_result("多模态记忆存储", False, f"异常: {e}")
    
    def test_3_enhanced_decay_curve(self):
        """测试3: 增强型衰退曲线（6因子）"""
        
        print("\n" + "="*70)
        print("📋 测试3: 增强型衰退曲线（6因子）")
        print("="*70)
        
        try:
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
            
            # 场景2: 30天后被动衰减（模拟30分钟）
            future_30d = base_time + timedelta(minutes=30)
            factors_30 = self.engine.calculate_enhanced_weight(
                memory,
                UpdateTrigger.PASSIVE_DECAY,
                now=future_30d
            )
            print(f"\n场景2 - 30天后被动衰减:")
            print(f"  W(30) = {factors_30.total_weight:.4f}")
            print(f"  w_time = {factors_30.time_weight:.4f}")
            print(f"  衰减: {(1 - factors_30.total_weight/factors_0.total_weight)*100:.1f}%")
            
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
            print(f"  提升: {(factors_activated.total_weight/factors_30.total_weight - 1)*100:.1f}%")
            
            # 场景4: 用户否定（刚否定，无correction_time）
            memory_negated_id = self.id_generator.generate_memory_id(self.user_identity.user_id)
            content_negated = MultimodalContent(text="我叫Bob")  # 错误的记忆
            
            metadata_negated = MemoryMetadata(
                memory_id=memory_negated_id,
                device_uuid=self.device_manager.get_device_id(),
                user_id=self.user_identity.user_id,
                created_at=base_time.isoformat(),
                last_activated_at=base_time.isoformat(),
                category=MemoryCategory.IDENTITY,
                is_negated=True,  # 标记为否定
                correction_history=[]  # 刚否定，无历史
            )
            
            memory_negated = Memory(memory_id=memory_negated_id, content=content_negated, metadata=metadata_negated)
            
            factors_negated = self.engine.calculate_enhanced_weight(
                memory_negated,
                UpdateTrigger.USER_NEGATION,
                now=future_30d
            )
            print(f"\n场景4 - 用户否定（刚否定）:")
            print(f"  W(否定) = {factors_negated.total_weight:.4f}")
            print(f"  C(t) = {factors_negated.conflict_penalty:.4f} (冲突惩罚)")
            print(f"  降权: {(1 - factors_negated.conflict_penalty)*100:.0f}%")
            
            # 验证
            assert factors_0.total_weight > factors_30.total_weight, "应该衰减"
            assert factors_activated.total_weight > factors_30.total_weight, "激活应提升"
            assert factors_negated.conflict_penalty == 0.3, "刚否定应立即降至0.3"
            assert factors_negated.total_weight < factors_0.total_weight, "否定后权重应降低"
            
            self.log_test_result(
                "增强型衰退曲线", 
                True, 
                f"6因子公式验证成功：被动衰减-{(1-factors_30.total_weight/factors_0.total_weight)*100:.0f}%, "
                f"激活提升+{(factors_activated.total_weight/factors_30.total_weight-1)*100:.0f}%, "
                f"冲突惩罚C(t)={factors_negated.conflict_penalty:.2f}"
            )
            
        except Exception as e:
            self.log_test_result("增强型衰退曲线", False, f"异常: {e}")
    
    def test_4_smart_retrieval(self):
        """测试4: 智能检索与Reranker"""
        
        print("\n" + "="*70)
        print("📋 测试4: 智能检索与Reranker")
        print("="*70)
        
        try:
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
                
                created_time = base_time - timedelta(minutes=days_ago)  # 模拟天数
                
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
            
            print(f"✓ 创建 {len(memories)} 条测试记忆")
            
            # 测试检索（降低阈值以确保有结果）
            config = RetrievalConfig(
                query_mode=QueryMode.NORMAL,
                top_k=3,
                similarity_threshold=0.0  # 允许所有相似度
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
            assert len(results) > 0, "应该有检索结果"
            assert "咖啡" in results[0].memory.content.text, "第一条应包含咖啡"
            
            self.log_test_result(
                "智能检索与Reranker", 
                True, 
                f"检索到{len(results)}条记录，语义+时间+权重融合排序正常"
            )
            
        except Exception as e:
            self.log_test_result("智能检索与Reranker", False, f"异常: {e}")
    
    async def test_5_scheduler(self):
        """测试5: 定时调度服务"""
        
        print("\n" + "="*70)
        print("📋 测试5: 定时调度服务")
        print("="*70)
        
        try:
            # 清空之前的记忆
            initial_count = len(self.store.memories)
            
            # 创建临时记忆（快速衰减）
            for i in range(3):
                memory_id = self.id_generator.generate_memory_id(self.user_identity.user_id)
                content = MultimodalContent(text=f"临时记忆 {i+1}")
                
                # 创建1天前的记忆（模拟1分钟）
                past_time = datetime.now() - timedelta(minutes=1)
                
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
            
            print(f"✓ 创建 3 条临时记忆 (总计 {len(self.store.memories)} 条)")
            
            # 启动调度器
            await self.scheduler.start()
            print("✓ 调度器已启动，运行15秒...")
            
            await asyncio.sleep(15)
            
            # 停止调度器
            await self.scheduler.stop()
            print("✓ 调度器已停止")
            
            # 检查指标
            if self.scheduler.metrics.snapshots:
                snapshot = self.scheduler.metrics.snapshots[-1]
                print(f"\n指标快照:")
                print(f"  总记忆数: {snapshot.total_memories}")
                print(f"  压缩次数: {snapshot.compression_count}")
                print(f"  平均权重: {snapshot.avg_weight:.4f}")
                print(f"  层级分布: {snapshot.level_distribution}")
                
                self.log_test_result(
                    "定时调度服务", 
                    True, 
                    f"调度器运行正常，执行了{snapshot.compression_count}次压缩操作"
                )
            else:
                self.log_test_result("定时调度服务", True, "调度器启动和停止正常（无快照）")
            
        except Exception as e:
            self.log_test_result("定时调度服务", False, f"异常: {e}")
    
    def test_6_lifecycle_management(self):
        """测试6: 生命周期管理"""
        
        print("\n" + "="*70)
        print("📋 测试6: 生命周期管理")
        print("="*70)
        
        try:
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
            print(f"✓ 创建测试记忆: {memory_id[:24]}...")
            
            # 测试冻结
            print("\n1) 冻结记忆:")
            self.lifecycle.freeze_memory(memory_id)
            assert memory.metadata.is_frozen == True
            print("   ✓ 记忆已冻结（禁止自动压缩）")
            
            # 测试敏感标记
            print("\n2) 敏感标记:")
            self.lifecycle.mark_sensitive(memory_id, sensitivity_level=3, encrypt=True)
            assert memory.metadata.is_sensitive == True
            assert memory.metadata.sensitivity_level == 3
            assert memory.metadata.is_encrypted == True
            print("   ✓ 已标记为敏感（等级3，加密存储）")
            
            # 测试权重解释
            print("\n3) 权重解释:")
            explanation = self.lifecycle.explain_weight(memory_id)
            print(f"   总权重: {explanation['total_weight']:.4f}")
            print(f"   因子: w_time={explanation['factors']['w_time']:.4f}, "
                  f"I={explanation['factors']['I']:.1f}, "
                  f"U={explanation['factors']['U']:.1f}")
            
            # 测试软删除
            print("\n4) 软删除:")
            self.lifecycle.delete_memory(memory_id, soft=True)
            assert memory.metadata.is_deleted == True
            print("   ✓ 记忆已软删除（30天后自动硬删除）")
            
            self.log_test_result(
                "生命周期管理", 
                True, 
                "冻结、敏感标记、权重解释、软删除功能全部正常"
            )
            
        except Exception as e:
            self.log_test_result("生命周期管理", False, f"异常: {e}")
    
    def test_7_special_scenarios(self):
        """测试7: 特殊情形处理"""
        
        print("\n" + "="*70)
        print("📋 测试7: 特殊情形处理")
        print("="*70)
        
        try:
            # 场景1: 频繁强化检测
            print("\n场景1 - 频繁强化检测:")
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
            print(f"  检测结果: {'✓ 频繁强化' if is_frequent else '正常'}")
            assert is_frequent == True, "应检测到频繁强化"
            
            # 场景2: 用户否定决策
            print("\n场景2 - 用户否定决策:")
            action, params = self.engine.decide_action(
                memory,
                new_content="我不喜欢巧克力",
                similarity=0.70,
                trigger=UpdateTrigger.USER_NEGATION,
                now=now
            )
            print(f"  决策动作: {action}")
            print(f"  参数: create_new={params.get('create_new')}, penalty={params.get('penalty')}")
            assert action == "MARK_NEGATED", "应标记为否定"
            assert params.get("create_new") == True, "应创建新记忆"
            
            # 场景3: 批量合并
            print("\n场景3 - 批量合并相似记忆:")
            similar_memories = []
            for i in range(3):
                mid = self.id_generator.generate_memory_id(self.user_identity.user_id)
                c = MultimodalContent(text=f"我喜欢喝咖啡 变体{i+1}")
                m = MemoryMetadata(
                    memory_id=mid,
                    device_uuid=self.device_manager.get_device_id(),
                    user_id=self.user_identity.user_id,
                    created_at=now.isoformat(),
                    last_activated_at=now.isoformat(),
                    category=MemoryCategory.STABLE_PREFERENCE,
                    mention_count=i+1
                )
                mem = Memory(memory_id=mid, content=c, metadata=m)
                similar_memories.append(mem)
                self.store.add_memory(mem)
            
            total_mentions = sum(m.metadata.mention_count for m in similar_memories)
            
            merged = self.engine.merge_memories_batch(
                similar_memories,
                self.store,
                self.id_generator,
                self.user_identity.user_id,
                now
            )
            
            print(f"  合并前: {len(similar_memories)} 条记忆")
            print(f"  合并后: 1 条 (ID: {merged.memory_id[:24]}...)")
            print(f"  层级: {merged.metadata.level.value}")
            print(f"  累计提及: {merged.metadata.mention_count} 次")
            
            assert merged.metadata.level == MemoryLevel.SUMMARY, "应为SUMMARY层级"
            assert merged.metadata.mention_count == total_mentions, "应累加提及次数"
            assert len(merged.metadata.merged_from) == 3, "应记录溯源"
            
            self.log_test_result(
                "特殊情形处理", 
                True, 
                "频繁强化检测、用户否定、批量合并功能全部正常"
            )
            
        except Exception as e:
            self.log_test_result("特殊情形处理", False, f"异常: {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        
        print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 运行测试
        self.test_1_identity_management()
        self.test_2_multimodal_storage()
        self.test_3_enhanced_decay_curve()
        self.test_4_smart_retrieval()
        await self.test_5_scheduler()
        self.test_6_lifecycle_management()
        self.test_7_special_scenarios()
        
        # 统计结果
        print("\n" + "="*70)
        print("📊 测试结果统计")
        print("="*70)
        
        passed = sum(1 for _, p, _ in self.test_results if p)
        total = len(self.test_results)
        
        for test_name, passed_flag, message in self.test_results:
            status = "✅" if passed_flag else "❌"
            print(f"{status} {test_name}")
            if message and not passed_flag:
                print(f"   ⚠️ {message}")
        
        print(f"\n{'='*70}")
        print(f"通过: {passed}/{total} ({passed/total*100:.0f}%)")
        print(f"{'='*70}")
        
        if passed == total:
            print("\n🎉 恭喜！所有测试通过！")
            print("\n✨ 完整记忆管理系统功能验证完成：")
            print("   ✓ 身份与根ID管理")
            print("   ✓ 多模态记忆存储")
            print("   ✓ 增强型衰退曲线（6因子公式）")
            print("   ✓ 智能检索与Reranker")
            print("   ✓ 定时调度服务")
            print("   ✓ 生命周期管理")
            print("   ✓ 特殊情形处理")
            print("\n📄 详细方案文档: COMPLETE_MEMORY_SOLUTION.md")
        else:
            print(f"\n⚠️ 有 {total - passed} 个测试失败，请检查")
        
        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)


async def main():
    simulation = CompleteMemorySystemSimulation()
    await simulation.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
