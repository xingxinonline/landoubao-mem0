#!/usr/bin/env python3
"""
智能检索与Reranker - Smart Retrieval & Reranking

功能:
1. 多阶段检索（粗排→精排）
2. 语义相似度 + 时间权重融合
3. 查询模式区分（NORMAL/REVIEW/DEBUG）
4. 跨模态检索
5. 用户行为信号融合
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import math

from complete_memory_system import (
    Memory, MemoryLevel, MemoryCategory, Modality, QueryMode
)
from complete_memory_engine import CompleteMemoryEngine, UpdateTrigger

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """检索配置"""
    query_mode: QueryMode = QueryMode.NORMAL
    top_k: int = 10
    similarity_threshold: float = 0.6
    time_weight_ratio: float = 0.3  # 时间权重占比
    semantic_weight_ratio: float = 0.7  # 语义权重占比
    enable_rerank: bool = True
    enable_cross_modal: bool = False
    include_deleted: bool = False
    include_archived: bool = False


@dataclass
class RetrievalResult:
    """检索结果"""
    memory: Memory
    relevance_score: float  # 相关性分数
    semantic_score: float   # 语义分数
    time_score: float       # 时间分数
    weight_score: float     # 权重分数
    explanation: str        # 可解释性
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory.memory_id,
            "content": self.memory.content.text,
            "level": self.memory.metadata.level.value,
            "category": self.memory.metadata.category.value,
            "relevance_score": round(self.relevance_score, 4),
            "semantic_score": round(self.semantic_score, 4),
            "time_score": round(self.time_score, 4),
            "weight_score": round(self.weight_score, 4),
            "explanation": self.explanation
        }


class SmartRetriever:
    """智能检索器"""
    
    def __init__(
        self,
        memory_engine: CompleteMemoryEngine,
        config: Optional[RetrievalConfig] = None
    ):
        self.engine = memory_engine
        self.config = config or RetrievalConfig()
    
    # ------------------------------------------------------------------------
    # 1. 语义相似度计算（占位符，生产环境使用embeddings）
    # ------------------------------------------------------------------------
    
    def calculate_semantic_similarity(
        self,
        query: str,
        memory: Memory,
        modality: Modality = Modality.TEXT
    ) -> float:
        """
        计算语义相似度
        
        TODO: 生产环境使用:
        - sentence-transformers: paraphrase-multilingual-MiniLM-L12-v2
        - GLM embeddings: embedding-2
        - OpenAI embeddings: text-embedding-ada-002
        
        当前使用简化的Jaccard相似度
        """
        if modality == Modality.TEXT:
            content_text = memory.content.text or ""
            
            # 简化的Jaccard相似度
            query_tokens = set(query.lower().split())
            content_tokens = set(content_text.lower().split())
            
            if not query_tokens or not content_tokens:
                return 0.0
            
            intersection = query_tokens & content_tokens
            union = query_tokens | content_tokens
            
            similarity = len(intersection) / len(union) if union else 0.0
            return similarity
        
        elif modality == Modality.IMAGE:
            # TODO: 使用CLIP或其他视觉模型
            return 0.0
        
        elif modality == Modality.AUDIO:
            # TODO: 使用Whisper转文本后计算
            return 0.0
        
        return 0.0
    
    # ------------------------------------------------------------------------
    # 2. 时间分数计算
    # ------------------------------------------------------------------------
    
    def calculate_time_score(
        self,
        memory: Memory,
        now: Optional[datetime] = None
    ) -> float:
        """
        计算时间分数（越新越高）
        
        公式: time_score = exp(-0.01 × days)
        """
        if now is None:
            now = datetime.now()
        
        last_active = datetime.fromisoformat(memory.metadata.last_activated_at)
        delta_seconds = (now - last_active).total_seconds()
        delta_days = delta_seconds / self.engine.time_scale
        
        # 时间衰减
        time_score = math.exp(-0.01 * delta_days)
        
        return time_score
    
    # ------------------------------------------------------------------------
    # 3. 权重分数计算
    # ------------------------------------------------------------------------
    
    def calculate_weight_score(
        self,
        memory: Memory,
        now: Optional[datetime] = None
    ) -> float:
        """计算当前权重分数"""
        factors = self.engine.calculate_enhanced_weight(
            memory,
            UpdateTrigger.PASSIVE_DECAY,
            now
        )
        
        # 归一化到[0, 1]
        weight_score = factors.total_weight / 2.0  # 因为max=2.0
        
        return weight_score
    
    # ------------------------------------------------------------------------
    # 4. 相关性分数计算
    # ------------------------------------------------------------------------
    
    def calculate_relevance_score(
        self,
        query: str,
        memory: Memory,
        config: RetrievalConfig,
        now: Optional[datetime] = None
    ) -> Tuple[float, str]:
        """
        计算综合相关性分数
        
        公式: relevance = α × semantic + β × time + γ × weight
        
        Returns:
            (score, explanation)
        """
        # 1. 语义分数
        semantic_score = self.calculate_semantic_similarity(query, memory)
        
        # 2. 时间分数
        time_score = self.calculate_time_score(memory, now)
        
        # 3. 权重分数
        weight_score = self.calculate_weight_score(memory, now)
        
        # 4. 融合分数
        alpha = config.semantic_weight_ratio
        beta = config.time_weight_ratio
        gamma = 1.0 - alpha - beta
        
        relevance = (
            alpha * semantic_score +
            beta * time_score +
            gamma * weight_score
        )
        
        # 5. 生成解释
        explanation = (
            f"语义:{semantic_score:.2f} × {alpha} + "
            f"时间:{time_score:.2f} × {beta} + "
            f"权重:{weight_score:.2f} × {gamma} = {relevance:.2f}"
        )
        
        return relevance, explanation
    
    # ------------------------------------------------------------------------
    # 5. 层级过滤
    # ------------------------------------------------------------------------
    
    def filter_by_query_mode(
        self,
        memories: List[Memory],
        query_mode: QueryMode
    ) -> List[Memory]:
        """根据查询模式过滤记忆层级"""
        
        if query_mode == QueryMode.NORMAL:
            # 普通模式：优先FULL/SUMMARY
            allowed_levels = {
                MemoryLevel.FULL,
                MemoryLevel.SUMMARY
            }
            return [m for m in memories if m.metadata.level in allowed_levels]
        
        elif query_mode == QueryMode.REVIEW:
            # 回顾模式：允许TRACE/ARCHIVE上浮
            return memories  # 不过滤
        
        elif query_mode == QueryMode.DEBUG:
            # 调试模式：显示所有
            return memories
        
        return memories
    
    # ------------------------------------------------------------------------
    # 6. 粗排（初筛）
    # ------------------------------------------------------------------------
    
    def coarse_ranking(
        self,
        query: str,
        memories: List[Memory],
        config: RetrievalConfig,
        now: Optional[datetime] = None
    ) -> List[Tuple[Memory, float]]:
        """
        粗排：快速过滤
        
        策略:
        1. 简单相似度计算
        2. 阈值过滤
        3. Top-K初筛
        """
        candidates = []
        
        for memory in memories:
            # 跳过已删除
            if memory.metadata.is_deleted and not config.include_deleted:
                continue
            
            # 跳过存档
            if memory.metadata.level == MemoryLevel.ARCHIVE and not config.include_archived:
                continue
            
            # 简单相似度
            similarity = self.calculate_semantic_similarity(query, memory)
            
            if similarity >= config.similarity_threshold:
                candidates.append((memory, similarity))
        
        # 按相似度排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Top-K初筛（取2倍，留给精排）
        top_candidates = candidates[:config.top_k * 2]
        
        return top_candidates
    
    # ------------------------------------------------------------------------
    # 7. 精排（Reranker）
    # ------------------------------------------------------------------------
    
    def fine_ranking(
        self,
        query: str,
        candidates: List[Tuple[Memory, float]],
        config: RetrievalConfig,
        now: Optional[datetime] = None
    ) -> List[RetrievalResult]:
        """
        精排：综合打分
        
        融合因子:
        1. 语义相关性
        2. 时间新鲜度
        3. 权重重要性
        4. 用户行为信号（提及次数、强化次数）
        """
        results = []
        
        for memory, coarse_score in candidates:
            # 计算综合相关性
            relevance, explanation = self.calculate_relevance_score(
                query, memory, config, now
            )
            
            # 用户行为信号加成
            behavior_boost = 1.0
            if memory.metadata.mention_count > 5:
                behavior_boost += 0.1
            if memory.metadata.reinforce_count > 3:
                behavior_boost += 0.1
            
            # 类别加成
            category_boost = 1.0
            if memory.metadata.category in [
                MemoryCategory.IDENTITY,
                MemoryCategory.STABLE_PREFERENCE
            ]:
                category_boost = 1.2
            
            # 最终分数
            final_score = relevance * behavior_boost * category_boost
            
            # 创建结果
            result = RetrievalResult(
                memory=memory,
                relevance_score=final_score,
                semantic_score=coarse_score,
                time_score=self.calculate_time_score(memory, now),
                weight_score=self.calculate_weight_score(memory, now),
                explanation=explanation
            )
            
            results.append(result)
        
        # 按最终分数排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:config.top_k]
    
    # ------------------------------------------------------------------------
    # 8. 主检索接口
    # ------------------------------------------------------------------------
    
    def retrieve(
        self,
        query: str,
        memories: List[Memory],
        config: Optional[RetrievalConfig] = None,
        now: Optional[datetime] = None
    ) -> List[RetrievalResult]:
        """
        主检索接口
        
        流程:
        1. 层级过滤
        2. 粗排（初筛）
        3. 精排（Reranker）
        """
        if config is None:
            config = self.config
        
        if now is None:
            now = datetime.now()
        
        # 1. 层级过滤
        filtered_memories = self.filter_by_query_mode(
            memories,
            config.query_mode
        )
        
        logger.info(f"层级过滤: {len(memories)} → {len(filtered_memories)}")
        
        # 2. 粗排
        candidates = self.coarse_ranking(
            query,
            filtered_memories,
            config,
            now
        )
        
        logger.info(f"粗排: {len(filtered_memories)} → {len(candidates)}")
        
        # 3. 精排
        if config.enable_rerank:
            results = self.fine_ranking(
                query,
                candidates,
                config,
                now
            )
        else:
            # 不启用精排，直接返回粗排结果
            results = [
                RetrievalResult(
                    memory=m,
                    relevance_score=score,
                    semantic_score=score,
                    time_score=0.0,
                    weight_score=0.0,
                    explanation="粗排分数"
                )
                for m, score in candidates[:config.top_k]
            ]
        
        logger.info(f"精排: Top-{len(results)}")
        
        return results
    
    # ------------------------------------------------------------------------
    # 9. 跨模态检索
    # ------------------------------------------------------------------------
    
    def retrieve_cross_modal(
        self,
        query: str,
        query_modality: Modality,
        memories: List[Memory],
        config: Optional[RetrievalConfig] = None
    ) -> List[RetrievalResult]:
        """
        跨模态检索
        
        示例:
        - 文本查询 → 图片记忆
        - 语音查询 → 文本记忆
        """
        # TODO: 实现跨模态检索
        # 需要多模态embeddings（如CLIP）
        
        logger.warning("跨模态检索尚未实现，降级为文本检索")
        return self.retrieve(query, memories, config)


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    from complete_memory_system import (
        DeviceManager, UserIdentity, MemoryIDGenerator,
        MemoryStore, MultimodalContent, MemoryMetadata
    )
    from datetime import timedelta
    
    # 1. 初始化
    device_manager = DeviceManager()
    user_identity = UserIdentity(user_id="user_001")
    id_generator = MemoryIDGenerator(device_manager)
    store = MemoryStore()
    
    # 2. 创建记忆引擎和检索器
    engine = CompleteMemoryEngine(user_factor=1.0)
    retriever = SmartRetriever(engine)
    
    # 3. 创建测试记忆
    test_memories = [
        ("我喜欢喝咖啡", MemoryCategory.STABLE_PREFERENCE, 0),
        ("今天天气很好", MemoryCategory.EVENT, 1),
        ("我喜欢黑咖啡", MemoryCategory.STABLE_PREFERENCE, 2),
        ("我的名字是张三", MemoryCategory.IDENTITY, 0),
        ("明天要开会", MemoryCategory.TEMPORARY, 5),
    ]
    
    memories = []
    base_time = datetime.now()
    
    for text, category, days_ago in test_memories:
        memory_id = id_generator.generate_memory_id(user_identity.user_id)
        content = MultimodalContent(text=text)
        
        created_time = base_time - timedelta(days=days_ago)
        
        metadata = MemoryMetadata(
            memory_id=memory_id,
            device_uuid=device_manager.get_device_id(),
            user_id=user_identity.user_id,
            created_at=created_time.isoformat(),
            last_activated_at=created_time.isoformat(),
            category=category,
            mention_count=3 if "咖啡" in text else 1
        )
        
        memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
        memories.append(memory)
        store.add_memory(memory)
    
    # 4. 测试检索
    print("=== 普通模式检索 ===")
    config_normal = RetrievalConfig(
        query_mode=QueryMode.NORMAL,
        top_k=3,
        similarity_threshold=0.1
    )
    
    results = retriever.retrieve(
        query="咖啡偏好",
        memories=memories,
        config=config_normal
    )
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.memory.content.text}")
        print(f"   分数: {result.relevance_score:.4f}")
        print(f"   层级: {result.memory.metadata.level.value}")
        print(f"   类别: {result.memory.metadata.category.value}")
        print(f"   解释: {result.explanation}")
    
    print("\n=== 回顾模式检索 ===")
    config_review = RetrievalConfig(
        query_mode=QueryMode.REVIEW,
        top_k=5
    )
    
    results_review = retriever.retrieve(
        query="天气",
        memories=memories,
        config=config_review
    )
    
    print(f"找到 {len(results_review)} 条记忆")
    for result in results_review:
        print(f"- {result.memory.content.text} (分数: {result.relevance_score:.4f})")
