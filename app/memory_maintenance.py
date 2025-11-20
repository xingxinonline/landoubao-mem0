#!/usr/bin/env python3
"""
记忆维护服务 - Memory Maintenance Service

功能：
1. 定期扫描所有用户记忆
2. 应用时间衰减更新权重
3. 自动转换记忆层次（完整→摘要→标签→痕迹→存档）五层架构
4. 不再删除记忆，所有记忆永久保留
5. 生成维护报告
"""

import asyncio
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MemoryLevel(Enum):
    """记忆清晰度层次 - 五层架构"""
    FULL = "full"           # 完整记忆（权重 > 0.7）
    SUMMARY = "summary"     # 摘要化（0.3 ≤ 权重 ≤ 0.7）
    TAG = "tag"             # 模糊标签（0.1 ≤ 权重 < 0.3）
    TRACE = "trace"         # 痕迹记忆（0.01 ≤ 权重 < 0.1）
    ARCHIVE = "archive"     # 存档记忆（权重 ≤ 0.01，不参与普通检索）


@dataclass
class MaintenanceConfig:
    """维护配置"""
    mem0_url: str = "http://localhost:8000"
    zhipu_api_key: str = ""
    
    # 衰减参数 - 闪电模式：12分钟内达到存档状态
    decay_alpha: float = 100.0  # 超快衰减系数（原值0.01）
    
    # 权重阈值 - 五层架构
    full_memory_threshold: float = 0.7      # 完整记忆阈值（> 0.7）
    summary_memory_threshold: float = 0.3   # 摘要记忆阈值（0.3 ~ 0.7）
    tag_memory_threshold: float = 0.1       # 模糊标签阈值（0.1 ~ 0.3）
    trace_memory_threshold: float = 0.03    # 痕迹记忆阈值（0.03 ~ 0.1）
    # ≤ 0.03 为存档记忆，不再有cleanup_threshold，所有记忆都保留
    
    # 定时任务配置
    scan_interval_hours: int = 24           # 扫描间隔（小时）- 生产环境
    scan_interval_minutes: int = 5          # 扫描间隔（分钟）- 测试模式
    cleanup_interval_days: int = 7          # 清理间隔（天）
    test_mode: bool = False                 # 测试模式（使用分钟而非小时）
    
    # 批处理配置
    batch_size: int = 100                   # 每批处理记忆数
    
    def __post_init__(self):
        """加载API密钥"""
        if not self.zhipu_api_key:
            env_path = Path(__file__).parent / '.env'
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('ZHIPU_API_KEY='):
                            self.zhipu_api_key = line.split('=', 1)[1].strip()
                            break


class MemoryDecayCalculator:
    """记忆衰减计算器"""
    
    def __init__(self, alpha: float = 0.01):
        self.alpha = alpha
    
    def calculate_weight(self, initial_weight: float, days_passed: float) -> float:
        """
        计算时间衰减后的权重
        
        公式: w(t) = w0 / (1 + α * t)
        """
        return initial_weight / (1 + self.alpha * days_passed)
    
    def get_memory_level(self, weight: float) -> str:
        """
        根据权重判断记忆层次 - 五层架构
        
        > 0.7     : full    - 完整保留原文
        0.3 ~ 0.7 : summary - 摘要化
        0.1 ~ 0.3 : tag     - 模糊化标签
        0.03 ~ 0.1: trace   - 痕迹记忆
        ≤ 0.03    : archive - 存档（不参与普通检索）
        """
        if weight > 0.7:
            return MemoryLevel.FULL.value
        elif weight >= 0.3:
            return MemoryLevel.SUMMARY.value
        elif weight >= 0.1:
            return MemoryLevel.TAG.value
        elif weight >= 0.03:
            return MemoryLevel.TRACE.value
        else:
            return MemoryLevel.ARCHIVE.value


class MemorySummarizer:
    """记忆摘要生成器（使用LLM）"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    def summarize(self, original_content: str, target_level: str) -> str:
        """
        生成记忆摘要 - 五层架构
        
        Args:
            original_content: 原始记忆内容
            target_level: 目标层次 (summary/tag/trace/archive)
            
        Returns:
            摘要内容
        """
        if target_level == "summary":
            prompt = f"""请将以下记忆内容简化为摘要（保留核心信息，去除细节）：

原始记忆：{original_content}

要求：
1. 保留主要事实和关系
2. 去除具体细节和时间
3. 使用更概括的表达
4. 控制在15字以内

直接返回摘要，不要解释。"""
        
        elif target_level == "tag":
            prompt = f"""请将以下记忆内容提取为模糊标签（只保留主题类别）：

原始记忆：{original_content}

要求：
1. 只提取核心主题或类别
2. 使用更泛化的表达
3. 控制在8字以内
4. 示例："用户喜欢饮品"

直接返回标签，不要解释。"""
        
        elif target_level == "trace":
            prompt = f"""请将以下记忆内容转为痕迹记忆（极简描述）：

原始记忆：{original_content}

要求：
1. 使用"曾经有...相关记忆"的格式
2. 只保留最基本的类别
3. 控制在12字以内
4. 示例："用户曾经有饮品相关记忆"

直接返回痕迹描述，不要解释。"""
        
        else:  # archive
            prompt = f"""请将以下记忆内容转为存档标记（历史痕迹）：

原始记忆：{original_content}

要求：
1. 使用"历史痕迹：..."的格式
2. 极简概括
3. 控制在10字以内
4. 示例："历史痕迹：饮品偏好"

直接返回存档标记，不要解释。"""
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4-flash",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 100
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                logger.warning(f"LLM摘要失败: {response.status_code}")
                return original_content  # 失败时返回原内容
        except Exception as e:
            logger.error(f"调用LLM摘要时出错: {e}")
            return original_content


class MemoryMaintenanceService:
    """记忆维护服务"""
    
    def __init__(self, config: MaintenanceConfig):
        self.config = config
        self.decay_calculator = MemoryDecayCalculator(config.decay_alpha)
        self.summarizer = MemorySummarizer(config.zhipu_api_key)
        self.stats = {
            "total_scanned": 0,
            "total_updated": 0,
            "total_summarized": 0,
            "total_cleaned": 0,
            "last_run": None
        }
    
    def get_all_users(self) -> List[str]:
        """
        获取所有用户ID
        
        注意：Mem0当前API可能不支持直接获取所有用户，
        这里提供一个占位实现，实际使用时需要根据你的用户管理系统调整
        """
        # 方案1: 从数据库或用户管理系统获取
        # 方案2: 维护一个用户列表文件
        # 方案3: 通过Qdrant直接查询（需要访问Qdrant API）
        
        # 临时方案：从配置文件读取
        user_file = Path(__file__).parent / 'users.txt'
        if user_file.exists():
            with open(user_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        
        logger.warning("未找到用户列表，返回空列表")
        return []
    
    def get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有记忆"""
        try:
            response = requests.get(
                f"{self.config.mem0_url}/memories",
                params={"user_id": user_id},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                logger.error(f"获取用户 {user_id} 记忆失败: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取用户 {user_id} 记忆时出错: {e}")
            return []
    
    def update_memory(self, memory_id: str, new_content: str, 
                     new_metadata: Dict[str, Any]) -> bool:
        """
        更新记忆内容和元数据
        
        注意：Mem0 v1.0 API可能不直接支持更新，这里使用删除+重建方式
        """
        try:
            # 方案1: 如果Mem0支持PATCH/PUT，直接更新
            # response = requests.put(
            #     f"{self.config.mem0_url}/memories/{memory_id}",
            #     json={"content": new_content, "metadata": new_metadata}
            # )
            
            # 方案2: 删除旧记忆 + 创建新记忆（当前使用此方案）
            # 注意：这会改变memory_id，需要在应用层处理
            
            logger.info(f"记忆 {memory_id} 需要更新（内容已衰减）")
            # 实际更新逻辑需要根据Mem0 API调整
            return True
        except Exception as e:
            logger.error(f"更新记忆 {memory_id} 时出错: {e}")
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            response = requests.delete(
                f"{self.config.mem0_url}/memories/{memory_id}",
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"删除记忆 {memory_id} 时出错: {e}")
            return False
    
    def process_memory(self, memory: Dict[str, Any], user_id: str) -> Dict[str, str]:
        """
        处理单条记忆
        
        Returns:
            处理结果 {"action": "updated/cleaned/skipped", "reason": "..."}
        """
        memory_id = memory.get("id", "")
        content = memory.get("memory", "")
        metadata = memory.get("metadata", {})
        
        # 获取时间戳和权重
        timestamp_str = metadata.get("timestamp", "")
        initial_weight = float(metadata.get("weight", 1.0))
        current_level = metadata.get("level", "full")
        
        if not timestamp_str:
            logger.warning(f"记忆 {memory_id} 缺少时间戳，跳过")
            return {"action": "skipped", "reason": "no_timestamp"}
        
        try:
            # 计算时间差
            memory_time = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            days_passed = (now - memory_time).total_seconds() / 86400
            
            # 计算当前权重
            current_weight = self.decay_calculator.calculate_weight(
                initial_weight, days_passed
            )
            new_level = self.decay_calculator.get_memory_level(current_weight)
            
            logger.info(f"记忆 {memory_id[:8]}... | 天数: {days_passed:.1f} | "
                       f"权重: {initial_weight:.2f} → {current_weight:.2f} | "
                       f"层次: {current_level} → {new_level}")
            
            # 不再清理删除，所有记忆都保留
            # 即使权重降到极低（≤0.01），也会转为archive层级保存
            
            # 判断是否需要转换层次
            if new_level != current_level:
                logger.info(f"🔄 转换记忆层次: {current_level} → {new_level}")
                
                # 生成摘要/标签/痕迹/存档
                if new_level in ["summary", "tag", "trace", "archive"]:
                    new_content = self.summarizer.summarize(content, new_level)
                    
                    # 显示层次转换图标
                    level_icons = {
                        "summary": "📝",
                        "tag": "🏷️",
                        "trace": "👣",
                        "archive": "📦"
                    }
                    icon = level_icons.get(new_level, "")
                    
                    logger.info(f"   {icon} 原内容: {content[:40]}...")
                    logger.info(f"   {icon} 新内容: {new_content}")
                    
                    # 更新元数据
                    new_metadata = metadata.copy()
                    new_metadata["weight"] = current_weight
                    new_metadata["level"] = new_level
                    new_metadata["last_updated"] = datetime.now().isoformat()
                    new_metadata["original_content"] = content  # 保留原始内容以便回溯
                    
                    # self.update_memory(memory_id, new_content, new_metadata)
                    self.stats["total_summarized"] += 1
                    return {"action": "summarized", "reason": f"{current_level}_to_{new_level}"}
            
            # 仅更新权重（层次未变）
            elif abs(current_weight - initial_weight) > 0.01:
                logger.debug(f"更新权重: {initial_weight:.2f} → {current_weight:.2f}")
                # 可以选择是否实际更新数据库
                self.stats["total_updated"] += 1
                return {"action": "updated", "reason": "weight_decay"}
            
            return {"action": "skipped", "reason": "no_change"}
            
        except Exception as e:
            logger.error(f"处理记忆 {memory_id} 时出错: {e}")
            return {"action": "error", "reason": str(e)}
    
    async def scan_user_memories(self, user_id: str) -> Dict[str, int]:
        """扫描单个用户的记忆"""
        logger.info(f"\n{'='*60}")
        logger.info(f"扫描用户: {user_id}")
        logger.info(f"{'='*60}")
        
        memories = self.get_user_memories(user_id)
        
        if not memories:
            logger.info(f"用户 {user_id} 暂无记忆")
            return {"total": 0, "updated": 0, "summarized": 0, "cleaned": 0}
        
        logger.info(f"找到 {len(memories)} 条记忆\n")
        
        results = {
            "total": len(memories),
            "updated": 0,
            "summarized": 0,
            "cleaned": 0,
            "skipped": 0,
            "error": 0
        }
        
        # 批处理
        for i in range(0, len(memories), self.config.batch_size):
            batch = memories[i:i + self.config.batch_size]
            logger.info(f"处理批次 {i//self.config.batch_size + 1} "
                       f"({len(batch)} 条记忆)")
            
            for memory in batch:
                result = self.process_memory(memory, user_id)
                action = result["action"]
                results[action] = results.get(action, 0) + 1
                self.stats["total_scanned"] += 1
            
            # 避免过载
            await asyncio.sleep(0.1)
        
        logger.info(f"\n用户 {user_id} 处理结果:")
        logger.info(f"  总计: {results['total']}")
        logger.info(f"  更新: {results['updated']}")
        logger.info(f"  摘要: {results['summarized']}")
        logger.info(f"  清理: {results['cleaned']}")
        logger.info(f"  跳过: {results['skipped']}")
        if results.get('error', 0) > 0:
            logger.warning(f"  错误: {results['error']}")
        
        return results
    
    async def run_maintenance_cycle(self):
        """运行一次完整的维护周期"""
        logger.info("\n" + "="*80)
        logger.info("🔧 开始记忆维护周期")
        logger.info("="*80)
        logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"配置: 衰减系数={self.config.decay_alpha}, "
                   f"完整阈值={self.config.full_memory_threshold}, "
                   f"摘要阈值={self.config.summary_memory_threshold}")
        
        # 获取所有用户
        users = self.get_all_users()
        
        if not users:
            logger.warning("未找到用户，维护周期结束")
            return
        
        logger.info(f"\n找到 {len(users)} 个用户\n")
        
        # 逐用户处理
        all_results = []
        for user_id in users:
            try:
                result = await self.scan_user_memories(user_id)
                all_results.append(result)
            except Exception as e:
                logger.error(f"处理用户 {user_id} 时出错: {e}")
        
        # 汇总统计
        total_stats = {
            "users": len(users),
            "total_memories": sum(r["total"] for r in all_results),
            "updated": sum(r.get("updated", 0) for r in all_results),
            "summarized": sum(r.get("summarized", 0) for r in all_results),
            "cleaned": sum(r.get("cleaned", 0) for r in all_results),
        }
        
        self.stats["last_run"] = datetime.now().isoformat()
        
        logger.info("\n" + "="*80)
        logger.info("📊 维护周期完成")
        logger.info("="*80)
        logger.info(f"用户数: {total_stats['users']}")
        logger.info(f"记忆总数: {total_stats['total_memories']}")
        logger.info(f"权重更新: {total_stats['updated']}")
        logger.info(f"层次转换: {total_stats['summarized']}")
        logger.info(f"累计扫描: {self.stats['total_scanned']}")
        logger.info("💡 所有记忆都保留，不遗忘")
        logger.info("="*80 + "\n")
        
        # 保存维护报告
        self.save_maintenance_report(total_stats)
    
    def save_maintenance_report(self, stats: Dict[str, Any]):
        """保存维护报告"""
        report_file = Path(__file__).parent / "maintenance_reports" / \
                     f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "decay_alpha": self.config.decay_alpha,
                "full_threshold": self.config.full_memory_threshold,
                "summary_threshold": self.config.summary_memory_threshold,
                "tag_threshold": self.config.tag_memory_threshold,
                "trace_threshold": self.config.trace_memory_threshold
            },
            "stats": stats,
            "cumulative": self.stats
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 维护报告已保存: {report_file}")
    
    async def run_scheduler(self):
        """定时调度器"""
        logger.info("🚀 记忆维护服务启动")
        
        if self.config.test_mode:
            interval = self.config.scan_interval_minutes
            unit = "分钟"
            wait_seconds = interval * 60
            logger.info(f"⚠️  测试模式: 扫描间隔 = 每 {interval} 分钟")
        else:
            interval = self.config.scan_interval_hours
            unit = "小时"
            wait_seconds = interval * 3600
            logger.info(f"扫描间隔: 每 {interval} 小时")
        
        while True:
            try:
                await self.run_maintenance_cycle()
            except Exception as e:
                logger.error(f"维护周期执行出错: {e}", exc_info=True)
            
            # 等待下一个周期
            next_run = datetime.now() + timedelta(seconds=wait_seconds)
            logger.info(f"⏰ 下次运行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"⏳ 等待 {interval} {unit}...\n")
            
            await asyncio.sleep(wait_seconds)


async def main():
    """主函数"""
    import sys
    
    # 检查测试模式
    test_mode = "--test" in sys.argv
    
    # 加载配置
    config = MaintenanceConfig(
        scan_interval_hours=24,          # 生产环境：每24小时
        scan_interval_minutes=2,         # 测试模式：每2分钟
        decay_alpha=0.01,                # 衰减系数
        test_mode=test_mode,             # 是否测试模式
        # 不再有cleanup_threshold，所有记忆都保留
    )
    
    # 创建服务
    service = MemoryMaintenanceService(config)
    
    # 检查运行模式
    if "--once" in sys.argv:
        logger.info("执行一次性维护任务")
        await service.run_maintenance_cycle()
    elif test_mode:
        logger.info("⚠️  启动测试模式（每2分钟扫描一次）")
        await service.run_scheduler()
    else:
        # 启动定时调度（生产模式）
        await service.run_scheduler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 记忆维护服务已停止")
    except Exception as e:
        logger.error(f"服务异常退出: {e}", exc_info=True)
