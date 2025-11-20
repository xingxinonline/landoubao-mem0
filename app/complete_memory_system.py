#!/usr/bin/env python3
"""
完整记忆管理系统 - Complete Memory Management System

核心特性：
1. 身份与根ID管理（DeviceUUID + UserID）
2. 多模态记忆存储（文本、图片、语音）
3. 增强型衰退曲线（6因子融合）
4. 定时调度服务（自动压缩、批量处理）
5. 智能检索与reranker
6. 生命周期管理（清理、日志、溯源）

MemoryID结构：
  {DeviceUUID}_{UserID}_{Timestamp}_{SequenceID}
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import math
import uuid
import hashlib
import json

logger = logging.getLogger(__name__)


# ============================================================================
# 1. 身份与根ID管理
# ============================================================================

class DeviceManager:
    """设备管理器"""
    
    def __init__(self, device_uuid: Optional[str] = None):
        """
        Args:
            device_uuid: 设备UUID，若为None则生成新的
        """
        self.device_uuid = device_uuid or self._generate_device_uuid()
    
    def _generate_device_uuid(self) -> str:
        """生成设备UUID"""
        return str(uuid.uuid4())
    
    def get_device_id(self) -> str:
        """获取设备ID"""
        return self.device_uuid


class UserIdentity:
    """用户身份识别"""
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Args:
            user_id: 用户ID（可基于声纹/人脸/指纹等）
        """
        self.user_id = user_id or "default_user"
        self.biometric_hash = None  # 生物特征哈希
    
    def set_biometric(self, biometric_data: bytes):
        """设置生物特征（声纹/人脸等）"""
        self.biometric_hash = hashlib.sha256(biometric_data).hexdigest()
    
    def verify_biometric(self, biometric_data: bytes) -> bool:
        """验证生物特征"""
        if not self.biometric_hash:
            return False
        return self.biometric_hash == hashlib.sha256(biometric_data).hexdigest()


class MemoryIDGenerator:
    """记忆ID生成器"""
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.sequence = 0
    
    def generate_memory_id(self, user_id: str) -> str:
        """
        生成记忆ID
        
        格式: {DeviceUUID}_{UserID}_{Timestamp}_{SequenceID}
        
        示例: a1b2c3d4_user001_20241120103045_00001
        """
        device_uuid = self.device_manager.get_device_id()[:8]  # 截取前8位
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.sequence += 1
        sequence_id = f"{self.sequence:05d}"
        
        return f"{device_uuid}_{user_id}_{timestamp}_{sequence_id}"
    
    def parse_memory_id(self, memory_id: str) -> Dict[str, str]:
        """解析记忆ID"""
        parts = memory_id.split("_")
        if len(parts) != 4:
            raise ValueError(f"Invalid memory ID format: {memory_id}")
        
        return {
            "device_uuid": parts[0],
            "user_id": parts[1],
            "timestamp": parts[2],
            "sequence_id": parts[3]
        }


# ============================================================================
# 2. 记忆存储层
# ============================================================================

class MemoryLevel(Enum):
    """记忆层级"""
    FULL = "full"           # 完整记忆
    SUMMARY = "summary"     # 压缩摘要
    TAG = "tag"             # 模糊标签
    TRACE = "trace"         # 痕迹
    ARCHIVE = "archive"     # 存档


class MemoryCategory(Enum):
    """记忆类别"""
    IDENTITY = "identity"               # 身份信息
    STABLE_PREFERENCE = "stable_preference"  # 稳定偏好
    SHORT_PREFERENCE = "short_preference"    # 短期偏好
    EVENT = "event"                     # 事件
    SKILL = "skill"                     # 技能
    FACT = "fact"                       # 事实
    TEMPORARY = "temporary"             # 临时信息


class Modality(Enum):
    """模态类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class QueryMode(Enum):
    """查询模式"""
    NORMAL = "normal"       # 普通模式：优先FULL/SUMMARY
    REVIEW = "review"       # 回顾模式：允许TRACE/ARCHIVE上浮
    DEBUG = "debug"         # 调试模式：显示所有层级


@dataclass
class MultimodalContent:
    """多模态内容"""
    text: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    embeddings: Dict[str, List[float]] = field(default_factory=dict)  # 各模态的embeddings
    
    def get_modalities(self) -> List[Modality]:
        """获取包含的模态类型"""
        modalities = []
        if self.text:
            modalities.append(Modality.TEXT)
        if self.image_url:
            modalities.append(Modality.IMAGE)
        if self.audio_url:
            modalities.append(Modality.AUDIO)
        if self.video_url:
            modalities.append(Modality.VIDEO)
        return modalities


@dataclass
class MemoryFactors:
    """记忆权重因子"""
    time_weight: float = 1.0            # w_time(t)
    semantic_boost: float = 1.0         # S(t)
    conflict_penalty: float = 1.0       # C(t)
    importance: float = 1.0             # I
    user_factor: float = 1.0            # U
    momentum: float = 1.0               # M(t)
    total_weight: float = 1.0           # W(t)
    
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
    """记忆元数据"""
    
    # 🆔 身份信息
    memory_id: str                      # 记忆ID
    device_uuid: str                    # 设备UUID
    user_id: str                        # 用户ID
    
    # 🕐 双时间戳
    created_at: str                     # 创建时间（历史感）
    last_activated_at: str              # 最后激活时间（活跃度）
    
    # 📊 记忆属性
    level: MemoryLevel = MemoryLevel.FULL
    category: MemoryCategory = MemoryCategory.TEMPORARY
    
    # 🎯 权重因子
    factors: MemoryFactors = field(default_factory=MemoryFactors)
    
    # 📈 行为统计
    mention_count: int = 0              # 提及次数
    reinforce_count: int = 0            # 强化次数
    last_mention_time: Optional[str] = None
    recent_mentions: List[str] = field(default_factory=list)
    
    # ⚠️ 冲突与修正
    is_negated: bool = False
    is_corrected: bool = False
    correction_history: List[Dict] = field(default_factory=list)
    
    # 🔗 溯源链
    source_ids: List[str] = field(default_factory=list)
    merged_from: List[str] = field(default_factory=list)
    compressed_from: Optional[str] = None
    parent_id: Optional[str] = None     # 父记忆ID
    children_ids: List[str] = field(default_factory=list)  # 子记忆ID
    
    # 🎨 多模态
    modalities: List[Modality] = field(default_factory=list)
    
    # 🔒 隐私与敏感性
    is_sensitive: bool = False
    sensitivity_level: int = 0          # 0-3
    is_encrypted: bool = False
    
    # ♻️ 生命周期
    is_deleted: bool = False
    deletion_time: Optional[str] = None
    is_frozen: bool = False             # 用户冻结（不自动压缩）
    
    # 📝 可解释性
    weight_change_log: List[Dict] = field(default_factory=list)
    compression_history: List[Dict] = field(default_factory=list)
    
    # 👥 群体记忆
    is_group_memory: bool = False       # 是否为群体记忆
    group_id: Optional[str] = None      # 群组ID
    shared_with: List[str] = field(default_factory=list)  # 分享给哪些用户


@dataclass
class Memory:
    """完整记忆对象"""
    
    memory_id: str
    content: MultimodalContent
    metadata: MemoryMetadata
    
    # 额外字段
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    entities: List[Dict] = field(default_factory=list)  # 命名实体
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "memory_id": self.memory_id,
            "content": asdict(self.content),
            "metadata": asdict(self.metadata),
            "tags": self.tags,
            "keywords": self.keywords,
            "entities": self.entities
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """从字典创建"""
        content = MultimodalContent(**data["content"])
        
        # 重建metadata
        metadata_dict = data["metadata"]
        metadata_dict["level"] = MemoryLevel(metadata_dict["level"])
        metadata_dict["category"] = MemoryCategory(metadata_dict["category"])
        metadata_dict["modalities"] = [Modality(m) for m in metadata_dict.get("modalities", [])]
        metadata_dict["factors"] = MemoryFactors(**metadata_dict.get("factors", {}))
        
        metadata = MemoryMetadata(**metadata_dict)
        
        return cls(
            memory_id=data["memory_id"],
            content=content,
            metadata=metadata,
            tags=data.get("tags", []),
            keywords=data.get("keywords", []),
            entities=data.get("entities", [])
        )


# ============================================================================
# 3. 记忆存储库
# ============================================================================

class MemoryStore:
    """记忆存储库"""
    
    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self.user_index: Dict[str, Set[str]] = {}  # user_id -> memory_ids
        self.device_index: Dict[str, Set[str]] = {}  # device_uuid -> memory_ids
        self.group_index: Dict[str, Set[str]] = {}  # group_id -> memory_ids
    
    def add_memory(self, memory: Memory):
        """添加记忆"""
        self.memories[memory.memory_id] = memory
        
        # 更新索引
        user_id = memory.metadata.user_id
        if user_id not in self.user_index:
            self.user_index[user_id] = set()
        self.user_index[user_id].add(memory.memory_id)
        
        device_uuid = memory.metadata.device_uuid
        if device_uuid not in self.device_index:
            self.device_index[device_uuid] = set()
        self.device_index[device_uuid].add(memory.memory_id)
        
        # 群组索引
        if memory.metadata.is_group_memory and memory.metadata.group_id:
            group_id = memory.metadata.group_id
            if group_id not in self.group_index:
                self.group_index[group_id] = set()
            self.group_index[group_id].add(memory.memory_id)
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        return self.memories.get(memory_id)
    
    def get_user_memories(self, user_id: str) -> List[Memory]:
        """获取用户的所有记忆"""
        memory_ids = self.user_index.get(user_id, set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_device_memories(self, device_uuid: str) -> List[Memory]:
        """获取设备的所有记忆"""
        memory_ids = self.device_index.get(device_uuid, set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_group_memories(self, group_id: str) -> List[Memory]:
        """获取群组的所有记忆"""
        memory_ids = self.group_index.get(group_id, set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def delete_memory(self, memory_id: str, soft_delete: bool = True):
        """删除记忆"""
        memory = self.memories.get(memory_id)
        if not memory:
            return
        
        if soft_delete:
            # 软删除（标记）
            memory.metadata.is_deleted = True
            memory.metadata.deletion_time = datetime.now().isoformat()
        else:
            # 硬删除
            del self.memories[memory_id]
            
            # 清理索引
            user_id = memory.metadata.user_id
            if user_id in self.user_index:
                self.user_index[user_id].discard(memory_id)
            
            device_uuid = memory.metadata.device_uuid
            if device_uuid in self.device_index:
                self.device_index[device_uuid].discard(memory_id)
            
            if memory.metadata.group_id:
                group_id = memory.metadata.group_id
                if group_id in self.group_index:
                    self.group_index[group_id].discard(memory_id)
    
    def export_to_json(self, filepath: str, user_id: Optional[str] = None):
        """导出为JSON"""
        if user_id:
            memories = self.get_user_memories(user_id)
        else:
            memories = list(self.memories.values())
        
        data = [m.to_dict() for m in memories]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_from_json(self, filepath: str):
        """从JSON导入"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            memory = Memory.from_dict(item)
            self.add_memory(memory)


# 使用示例
if __name__ == "__main__":
    # 1. 初始化设备和用户
    device_manager = DeviceManager()
    user_identity = UserIdentity(user_id="user_001")
    id_generator = MemoryIDGenerator(device_manager)
    
    print(f"设备UUID: {device_manager.get_device_id()}")
    print(f"用户ID: {user_identity.user_id}")
    
    # 2. 创建记忆
    memory_id = id_generator.generate_memory_id(user_identity.user_id)
    print(f"\n记忆ID: {memory_id}")
    
    # 3. 解析记忆ID
    parsed = id_generator.parse_memory_id(memory_id)
    print(f"解析结果: {parsed}")
    
    # 4. 创建多模态内容
    content = MultimodalContent(
        text="我喜欢喝咖啡",
        image_url="https://example.com/coffee.jpg"
    )
    
    # 5. 创建元数据
    metadata = MemoryMetadata(
        memory_id=memory_id,
        device_uuid=device_manager.get_device_id(),
        user_id=user_identity.user_id,
        created_at=datetime.now().isoformat(),
        last_activated_at=datetime.now().isoformat(),
        level=MemoryLevel.FULL,
        category=MemoryCategory.STABLE_PREFERENCE,
        modalities=content.get_modalities()
    )
    
    # 6. 创建记忆对象
    memory = Memory(
        memory_id=memory_id,
        content=content,
        metadata=metadata,
        tags=["咖啡", "饮品", "偏好"]
    )
    
    # 7. 存储记忆
    store = MemoryStore()
    store.add_memory(memory)
    
    print(f"\n记忆已存储")
    print(f"模态类型: {[m.value for m in content.get_modalities()]}")
    print(f"记忆层级: {metadata.level.value}")
    print(f"记忆类别: {metadata.category.value}")
    
    # 8. 检索记忆
    user_memories = store.get_user_memories("user_001")
    print(f"\n用户记忆数量: {len(user_memories)}")
    
    # 9. 导出/导入
    store.export_to_json("memories_backup.json", user_id="user_001")
    print(f"\n记忆已导出到 memories_backup.json")
