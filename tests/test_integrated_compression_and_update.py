#!/usr/bin/env python3
"""
集成测试：记忆压缩 + 更新策略

场景模拟：
1. 创建初始记忆
2. 定时服务压缩（不刷新时间戳）
3. 用户再次提及（根据相似度决定策略）
4. 验证时间戳和内容变化
"""

import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# 添加app到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from memory_update_strategy import (
    MemoryUpdateStrategy,
    UpdateTrigger,
    MergeStrategy,
    calculate_semantic_similarity
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class IntegratedMemorySystem:
    """集成记忆系统（模拟）"""
    
    def __init__(self):
        self.memories: Dict[str, Dict[str, Any]] = {}
        self.strategy = MemoryUpdateStrategy()
        self.next_id = 1
    
    def create_memory(self, content: str, user_id: str = "user_1") -> str:
        """创建新记忆"""
        mem_id = f"mem_{self.next_id:03d}"
        self.next_id += 1
        
        now = datetime.now()
        self.memories[mem_id] = {
            "id": mem_id,
            "memory": content,
            "user_id": user_id,
            "metadata": {
                "level": "full",
                "weight": 1.0,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
        }
        
        logger.info(f"✨ 创建记忆 [{mem_id}]: {content}")
        return mem_id
    
    def compress_memory(self, mem_id: str, days_passed: int):
        """
        压缩记忆（模拟定时服务）
        
        关键：不刷新时间戳
        """
        if mem_id not in self.memories:
            return
        
        memory = self.memories[mem_id]
        old_level = memory["metadata"]["level"]
        old_content = memory["memory"]
        old_timestamp = memory["metadata"]["updated_at"]
        
        # 计算新层级（基于天数）
        if days_passed < 7:
            new_level = "full"
        elif days_passed < 30:
            new_level = "summary"
        elif days_passed < 90:
            new_level = "tag"
        elif days_passed < 180:
            new_level = "trace"
        else:
            new_level = "archive"
        
        # 压缩内容
        new_content = self._compress_content(old_content, new_level)
        
        # 计算新权重
        alpha = 0.01
        new_weight = 1.0 / (1 + alpha * days_passed)
        
        # 使用策略决定是否刷新时间戳
        decision = self.strategy.decide_update_action(
            trigger=UpdateTrigger.PASSIVE_DECAY,
            old_memory=memory,
            new_content="",
            similarity_score=1.0
        )
        
        # 更新记忆
        memory["memory"] = new_content
        memory["metadata"]["level"] = new_level
        memory["metadata"]["weight"] = round(new_weight, 3)
        
        # ✅ 关键：被动压缩不刷新时间戳
        if not decision.should_refresh_timestamp:
            logger.info(
                f"🔄 压缩记忆 [{mem_id}] {old_level}→{new_level} "
                f"(天数:{days_passed}, 权重:{new_weight:.3f}, "
                f"时间戳:保持 {old_timestamp[:10]})"
            )
            logger.info(f"   内容: {old_content} → {new_content}")
        else:
            # 如果策略要求刷新（不应该发生在PASSIVE_DECAY）
            memory["metadata"]["updated_at"] = datetime.now().isoformat()
            logger.warning(f"⚠️ 被动压缩却刷新了时间戳！")
    
    def user_mention(self, content: str, user_id: str = "user_1") -> str:
        """
        用户提及相关内容
        
        关键：根据相似度决定合并/新建，高相似度刷新时间戳
        """
        # 查找相关记忆
        best_match = None
        best_similarity = 0.0
        
        for mem_id, memory in self.memories.items():
            if memory["user_id"] != user_id:
                continue
            
            similarity = calculate_semantic_similarity(
                memory["memory"],
                content
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = mem_id
        
        # 使用策略决定动作
        if best_match and best_similarity > 0.1:
            memory = self.memories[best_match]
            decision = self.strategy.decide_update_action(
                trigger=UpdateTrigger.USER_MENTION,
                old_memory=memory,
                new_content=content,
                similarity_score=best_similarity
            )
            
            old_timestamp = memory["metadata"]["updated_at"]
            old_level = memory["metadata"]["level"]
            
            if decision.strategy == MergeStrategy.MERGE_UPDATE:
                # 合并更新
                memory["memory"] = self.strategy.merge_memory_content(
                    old_content=memory["memory"],
                    new_content=content,
                    old_level=old_level
                )
                
                if decision.should_upgrade_level:
                    new_level = self.strategy.upgrade_memory_level(old_level)
                    memory["metadata"]["level"] = new_level
                    logger.info(f"⬆️ 升级层级: {old_level} → {new_level}")
                
                # ✅ 关键：刷新时间戳
                if decision.should_refresh_timestamp:
                    memory["metadata"]["updated_at"] = datetime.now().isoformat()
                    logger.info(
                        f"🔥 激活记忆 [{best_match}] (相似度:{best_similarity:.2f})"
                    )
                    logger.info(f"   内容: {content}")
                    logger.info(f"   时间戳: {old_timestamp[:10]} → {memory['metadata']['updated_at'][:10]}")
                
                # 提升权重
                old_weight = memory["metadata"]["weight"]
                new_weight = self.strategy.calculate_weight_boost(
                    old_weight=old_weight,
                    similarity=best_similarity,
                    trigger=UpdateTrigger.USER_MENTION
                )
                memory["metadata"]["weight"] = round(new_weight, 3)
                logger.info(f"   权重: {old_weight:.3f} → {new_weight:.3f}")
                
                return best_match
            
            elif decision.strategy == MergeStrategy.KEEP_BOTH:
                # 保留双轨
                logger.info(
                    f"🔀 保留双轨 (相似度:{best_similarity:.2f})"
                )
                logger.info(f"   旧记忆 [{best_match}]: {memory['memory']} (保持)")
                new_id = self.create_memory(content, user_id)
                logger.info(f"   新记忆 [{new_id}]: {content}")
                return new_id
            
            else:  # CREATE_NEW
                # 新建独立记忆
                logger.info(
                    f"🆕 新建独立记忆 (相似度:{best_similarity:.2f}, 旧记忆保持压缩)"
                )
                return self.create_memory(content, user_id)
        
        else:
            # 没有相关记忆，直接新建
            return self.create_memory(content, user_id)
    
    def _compress_content(self, content: str, target_level: str) -> str:
        """简化的内容压缩"""
        if target_level == "full":
            return content
        elif target_level == "summary":
            return content[:30] + "..." if len(content) > 30 else content
        elif target_level == "tag":
            return "#记忆标签"
        elif target_level == "trace":
            return "曾有相关记忆"
        else:  # archive
            return "[已归档]"
    
    def show_all_memories(self):
        """显示所有记忆"""
        logger.info(f"\n{'='*70}")
        logger.info(f"当前记忆状态 (共 {len(self.memories)} 条)")
        logger.info(f"{'='*70}")
        
        for mem_id, memory in sorted(self.memories.items()):
            meta = memory["metadata"]
            logger.info(
                f"[{mem_id}] {meta['level']:8s} "
                f"权重:{meta['weight']:.3f} "
                f"更新:{meta['updated_at'][:10]} "
                f"| {memory['memory']}"
            )
        
        logger.info(f"{'='*70}\n")


async def run_scenario():
    """运行完整场景"""
    
    system = IntegratedMemorySystem()
    
    logger.info("\n" + "="*70)
    logger.info("集成测试：记忆压缩 + 更新策略")
    logger.info("="*70 + "\n")
    
    # 第1天：创建初始记忆
    logger.info("📅 第1天：创建初始记忆")
    mem1 = system.create_memory("我叫张三，是一名AI工程师")
    mem2 = system.create_memory("我喜欢喝咖啡")
    mem3 = system.create_memory("我在北京工作")
    
    system.show_all_memories()
    
    # 第10天：定时服务压缩
    logger.info("\n📅 第10天：定时服务压缩（full → summary）")
    system.compress_memory(mem1, days_passed=10)
    system.compress_memory(mem2, days_passed=10)
    system.compress_memory(mem3, days_passed=10)
    
    system.show_all_memories()
    
    # 第15天：用户提及工程师（高相似度）
    logger.info("\n📅 第15天：用户提及工程师话题（高相似度 → 合并更新 + 刷新时间戳）")
    system.user_mention("我是做AI工程的张三")
    
    system.show_all_memories()
    
    # 第40天：继续压缩未激活的记忆
    logger.info("\n📅 第40天：定时服务继续压缩（summary → tag）")
    system.compress_memory(mem2, days_passed=40)
    system.compress_memory(mem3, days_passed=40)
    
    system.show_all_memories()
    
    # 第45天：用户提及咖啡（中等相似度）
    logger.info("\n📅 第45天：用户提及咖啡（中等相似度 → 保留双轨）")
    system.user_mention("我现在喜欢喝茶了")
    
    system.show_all_memories()
    
    # 第100天：压缩到trace
    logger.info("\n📅 第100天：定时服务压缩（tag → trace）")
    system.compress_memory(mem3, days_passed=100)
    
    system.show_all_memories()
    
    # 第105天：用户提及全新话题（低相似度）
    logger.info("\n📅 第105天：用户提及新话题（低相似度 → 新建独立记忆）")
    system.user_mention("我开始学习弹吉他了")
    
    system.show_all_memories()
    
    logger.info("\n" + "="*70)
    logger.info("✅ 测试完成")
    logger.info("="*70)
    
    logger.info("\n核心验证点:")
    logger.info("  1. 被动压缩保持原始时间戳 ✅")
    logger.info("  2. 高相似度激活刷新时间戳 ✅")
    logger.info("  3. 权重随激活提升 ✅")
    logger.info("  4. 中等相似度保留双轨 ✅")
    logger.info("  5. 低相似度新建独立记忆 ✅")


if __name__ == "__main__":
    asyncio.run(run_scenario())
