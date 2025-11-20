#!/usr/bin/env python3
"""
记忆维护服务模拟测试
使用秒/分钟级别的时间周期快速验证五层记忆架构

功能：
1. 可配置执行周期（秒/分钟）
2. 可配置衰减系数
3. 模拟时间快进（秒代替天）
4. 实时观察记忆层次转换
5. 生成可视化报告
"""

import asyncio
import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

# 配置日志（修复Windows终端Unicode编码问题）
import sys
import io

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maintenance_simulation.log', encoding='utf-8'),
        logging.StreamHandler(
            io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        )
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """模拟测试配置（从环境变量加载）"""
    # 服务地址
    mem0_url: str = ""
    zhipu_api_key: str = ""
    
    # 时间单位配置（模拟加速）
    time_unit: str = "second"  # "second" 或 "minute"
    time_scale: float = 1.0    # 时间加速倍数（1秒 = 多少天）
    
    # 执行周期配置
    scan_interval_seconds: int = 10  # 扫描间隔（秒）
    
    # 衰减参数
    decay_alpha: float = 0.5  # 衰减系数（模拟环境下使用更大的值）
    
    # 五层阈值（基于时间）
    threshold_full_to_summary: float = 7.0    # full → summary: 7天
    threshold_summary_to_tag: float = 30.0    # summary → tag: 30天
    threshold_tag_to_trace: float = 90.0      # tag → trace: 90天
    threshold_trace_to_archive: float = 180.0 # trace → archive: 180天
    threshold_weight_archive: float = 0.015   # 权重阈值：trace→archive
    
    # 测试配置
    max_cycles: int = 10  # 最大测试周期数（0=无限循环）
    
    def __post_init__(self):
        """从环境变量加载配置"""
        import os
        from dotenv import load_dotenv
        
        # 加载.env文件
        env_path = Path(__file__).parent.parent / 'app' / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        # 从环境变量读取（优先级更高）
        self.mem0_url = os.getenv('MEM0_URL', 'http://localhost:8000')
        self.zhipu_api_key = os.getenv('ZHIPU_API_KEY', '')
        
        # 可选配置
        self.time_unit = os.getenv('SIM_TIME_UNIT', self.time_unit)
        self.time_scale = float(os.getenv('SIM_TIME_SCALE', str(self.time_scale)))
        self.scan_interval_seconds = int(os.getenv('SIM_SCAN_INTERVAL', str(self.scan_interval_seconds)))
        self.decay_alpha = float(os.getenv('SIM_DECAY_ALPHA', str(self.decay_alpha)))
        self.max_cycles = int(os.getenv('SIM_MAX_CYCLES', str(self.max_cycles)))


class MemorySimulator:
    """记忆模拟器"""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.simulation_start_time = datetime.now()
        self.cycle_count = 0
        
        # 🔥 层级和内容状态缓存（内存中追踪，因Mem0 API不支持更新metadata）
        self.memory_levels: Dict[str, str] = {}  # {memory_id: current_level}
        self.memory_contents: Dict[str, str] = {}  # {memory_id: compressed_content}
        
        # 统计数据
        self.stats = {
            "total_cycles": 0,
            "total_memories_scanned": 0,
            "level_transitions": {
                "full_to_summary": 0,
                "summary_to_tag": 0,
                "tag_to_trace": 0,
                "trace_to_archive": 0
            },
            "current_distribution": {
                "full": 0,
                "summary": 0,
                "tag": 0,
                "trace": 0,
                "archive": 0
            }
        }
    
    def get_simulated_days(self) -> float:
        """
        计算模拟经过的天数
        
        Returns:
            模拟天数
        """
        real_elapsed = (datetime.now() - self.simulation_start_time).total_seconds()
        
        if self.config.time_unit == "second":
            # 1秒 = time_scale天
            return real_elapsed * self.config.time_scale
        else:  # minute
            # 1分钟 = time_scale天
            return (real_elapsed / 60) * self.config.time_scale
    
    def calculate_decay_weight(self, initial_weight: float, memory_timestamp: str) -> float:
        """
        计算衰减后的权重（基于模拟时间）
        
        Args:
            initial_weight: 初始权重
            memory_timestamp: 记忆创建时间
            
        Returns:
            衰减后的权重
        """
        try:
            mem_time = datetime.fromisoformat(memory_timestamp)
            
            # 计算真实经过的秒数
            real_elapsed = (datetime.now() - mem_time).total_seconds()
            
            # 转换为模拟天数
            if self.config.time_unit == "second":
                simulated_days = real_elapsed * self.config.time_scale
            else:  # minute
                simulated_days = (real_elapsed / 60) * self.config.time_scale
            
            # 应用衰减公式: w(t) = w0 / (1 + α * t)
            current_weight = initial_weight / (1 + self.config.decay_alpha * simulated_days)
            
            return current_weight
        except Exception as e:
            logger.error(f"计算衰减权重失败: {e}")
            return initial_weight
    
    def get_next_memory_level(self, current_level: str, days_elapsed: float, weight: float) -> str:
        """
        根据当前层级、经过天数和权重确定下一层级
        
        层次转换规则：
        - full → summary:  7天未访问
        - summary → tag:   30天未访问
        - tag → trace:     90天未访问
        - trace → archive: 180天未访问 或 权重<0.015
        """
        # full层：7天后降级到summary
        if current_level == "full" and days_elapsed >= self.config.threshold_full_to_summary:
            return "summary"
        
        # summary层：30天后降级到tag
        if current_level == "summary" and days_elapsed >= self.config.threshold_summary_to_tag:
            return "tag"
        
        # tag层：90天后降级到trace
        if current_level == "tag" and days_elapsed >= self.config.threshold_tag_to_trace:
            return "trace"
        
        # trace层：180天后或权重过低时归档
        if current_level == "trace":
            if days_elapsed >= self.config.threshold_trace_to_archive or weight < self.config.threshold_weight_archive:
                return "archive"
        
        # 其他情况保持原层级
        return current_level
    
    def get_level_icon(self, level: str) -> str:
        """获取层次图标"""
        icons = {
            "full": "✓",
            "summary": "📝",
            "tag": "🏷️",
            "trace": "👣",
            "archive": "📦"
        }
        return icons.get(level, "?")
    
    def compress_memory_content(self, content: str, old_level: str, new_level: str) -> str:
        """
        压缩记忆内容（模拟真实的遗忘过程）
        
        核心理念：随时间流逝，记忆从完整→摘要→标签→痕迹→归档
        每次转换都是不可逆的信息损失
        """
        # 如果层级未变，不压缩
        if old_level == new_level:
            return content
        
        # full → summary: 提取核心信息（保留50%）
        if new_level == "summary":
            # 规则：保留关键词和主要动词
            keywords = []
            if "叫" in content or "是" in content:
                # 提取人名、职业等核心实体
                for char in ["叫", "是", "在", "做", "有"]:
                    if char in content:
                        idx = content.index(char)
                        keywords.append(content[max(0, idx-3):min(len(content), idx+8)])
            if not keywords:
                keywords = [content[:20]]
            return "，".join(keywords)[:30]
        
        # summary → tag: 转为关键词标签（保留20%）
        elif new_level == "tag":
            # 提取核心标签
            tags = []
            if "工程师" in content:
                tags.append("#职业:工程师")
            if "咖啡" in content:
                tags.append("#爱好:咖啡")
            if "北京" in content or "海淀" in content:
                tags.append("#地点:北京")
            if "起床" in content or "7点" in content:
                tags.append("#习惯:早起")
            
            # 如果没有匹配到特定标签，提取前几个字作为通用标签
            if not tags:
                words = content[:15].replace("，", " ").split()
                tags = [f"#{w}" for w in words[:2]]
            
            return " ".join(tags)
        
        # tag → trace: 模糊痕迹（仅保留类别信息，<5%）
        elif new_level == "trace":
            if "#职业" in content:
                return "曾有职业相关记忆"
            elif "#爱好" in content:
                return "曾有个人爱好记忆"
            elif "#地点" in content:
                return "曾有地理位置记忆"
            elif "#习惯" in content:
                return "曾有生活习惯记忆"
            else:
                return "曾有某类记忆痕迹"
        
        # trace/archive: 完全归档（几乎不可检索）
        elif new_level == "archive":
            return "[已归档]"  
        
        return content
    
    def update_memory_in_mem0(self, memory_id: str, user_id: str, new_content: str, new_level: str, new_weight: float) -> bool:
        """
        在Mem0中更新记忆内容（压缩）
        
        策略：由于Mem0 API不直接支持内容更新，采用删除+重建方式
        注意：保持原始ID和时间戳以维持连续性
        """
        try:
            # 方法1：尝试PUT更新（可能不支持）
            response = requests.put(
                f"{self.config.mem0_url}/memories/{memory_id}",
                json={
                    "text": new_content,
                    "metadata": {
                        "level": new_level,
                        "weight": new_weight,
                        "compressed_at": datetime.now().isoformat()
                    }
                },
                timeout=5
            )
            
            if response.status_code in [200, 204]:
                return True
            
            # 方法2：如果PUT失败，使用删除+重建（模拟测试中不实际操作）
            logger.debug(f"PUT更新不支持，模拟环境中仅在内存记录压缩")
            return True  # 在模拟环境中，内存缓存已足够
            
        except Exception as e:
            logger.debug(f"更新记忆内容 [{memory_id[:8]}]: {e}（使用内存缓存）")
            return True  # 模拟环境容错
    
    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有记忆"""
        try:
            response = requests.get(
                f"{self.config.mem0_url}/memories",
                params={"user_id": user_id},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                logger.error(f"获取记忆失败: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取记忆时出错: {e}")
            return []
    
    def process_memory(self, memory: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        处理单条记忆（计算衰减和层次转换）
        
        Returns:
            处理结果
        """
        memory_id = memory.get("id", "")
        original_content = memory.get("memory", "")
        metadata = memory.get("metadata", {})
        
        # 🔥 优先使用缓存的压缩内容（如果存在）
        content = self.memory_contents.get(memory_id) or original_content or ""
        
        # 获取元数据
        timestamp = metadata.get("timestamp", "")
        initial_weight = float(metadata.get("weight", 1.0))
        
        # 🔥 优先从缓存获取层级，如果不存在则使用metadata中的值（默认full）
        current_level = self.memory_levels.get(memory_id) or metadata.get("level") or "full"
        
        if not timestamp:
            return {
                "action": "skipped",
                "reason": "no_timestamp"
            }
        
        # 计算模拟时间
        mem_time = datetime.fromisoformat(timestamp)
        real_elapsed_seconds = (datetime.now() - mem_time).total_seconds()
        
        if self.config.time_unit == "second":
            simulated_days = real_elapsed_seconds * self.config.time_scale
            time_display = f"{real_elapsed_seconds:.1f}秒 (模拟{simulated_days:.2f}天)"
        else:
            simulated_days = (real_elapsed_seconds / 60) * self.config.time_scale
            time_display = f"{real_elapsed_seconds/60:.1f}分钟 (模拟{simulated_days:.2f}天)"
        
        # 计算衰减权重
        current_weight = self.calculate_decay_weight(initial_weight, timestamp)
        
        # 根据当前层级和经过天数判断下一层级
        new_level = self.get_next_memory_level(current_level, simulated_days, current_weight)
        
        # 层次转换检测
        transition_key = f"{current_level}_to_{new_level}"
        level_changed = new_level != current_level
        
        result = {
            "memory_id": memory_id[:8],
            "content": content[:40] + "..." if len(content) > 40 else content,
            "time_elapsed": time_display,
            "weight": {
                "initial": initial_weight,
                "current": current_weight,
                "change": current_weight - initial_weight
            },
            "level": {
                "old": current_level,
                "new": new_level,
                "changed": level_changed
            },
            "action": "level_transition" if level_changed else "weight_updated"
        }
        
        # 更新统计和执行压缩
        compressed_content = content
        if level_changed:
            if transition_key in self.stats["level_transitions"]:
                self.stats["level_transitions"][transition_key] += 1
            
            # 🔥 压缩记忆内容（核心功能）
            compressed_content = self.compress_memory_content(content, current_level, new_level)
            
            # 更新Mem0中的记忆（尝试，模拟环境可能失败但不影响测试）
            self.update_memory_in_mem0(memory_id, user_id, compressed_content, new_level, current_weight)
            
            # 更新内存缓存（层级和压缩内容）
            self.memory_levels[memory_id] = new_level
            self.memory_contents[memory_id] = compressed_content
        
        # 打印详细信息
        icon_old = self.get_level_icon(current_level)
        icon_new = self.get_level_icon(new_level)
        
        logger.info(f"  [{memory_id[:8]}] {content[:30]}...")
        logger.info(f"    时间: {time_display}")
        logger.info(f"    权重: {initial_weight:.3f} → {current_weight:.3f} (Δ{current_weight-initial_weight:+.3f})")
        
        if level_changed:
            logger.info(f"    层次: {icon_old} {current_level} → {icon_new} {new_level} ⚡")
            # 显示压缩效果
            original_len = len(content)
            compressed_len = len(compressed_content)
            compression_ratio = (1 - compressed_len / original_len) * 100 if original_len > 0 else 0
            logger.info(f"    压缩: '{content[:20]}' → '{compressed_content}' ({compression_ratio:.0f}%↓)")
        else:
            logger.info(f"    层次: {icon_new} {new_level} (未变)")
        
        return result
    
    async def run_maintenance_cycle(self, user_id: str):
        """运行一次维护周期"""
        self.cycle_count += 1
        self.stats["total_cycles"] += 1
        
        simulated_days = self.get_simulated_days()
        
        logger.info("\n" + "="*80)
        logger.info(f"🔧 维护周期 #{self.cycle_count}")
        logger.info("="*80)
        logger.info(f"真实时间: {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"模拟天数: {simulated_days:.2f} 天")
        logger.info(f"衰减系数: α = {self.config.decay_alpha}")
        logger.info("")
        
        # 获取所有记忆
        memories = self.get_all_memories(user_id)
        
        if not memories:
            logger.warning("⚠️  暂无记忆")
            return
        
        logger.info(f"📊 发现 {len(memories)} 条记忆\n")
        
        # 处理每条记忆
        results = []
        level_distribution = {"full": 0, "summary": 0, "tag": 0, "trace": 0, "archive": 0}
        
        for memory in memories:
            result = self.process_memory(memory, user_id)
            results.append(result)
            
            if result["action"] != "skipped":
                self.stats["total_memories_scanned"] += 1
                level_distribution[result["level"]["new"]] += 1
        
        # 更新当前分布
        self.stats["current_distribution"] = level_distribution
        
        # 汇总统计
        logger.info("\n" + "-"*80)
        logger.info("📈 本周期统计")
        logger.info("-"*80)
        logger.info(f"总记忆数: {len(memories)}")
        logger.info(f"层次转换: {sum(1 for r in results if r.get('level', {}).get('changed', False))}")
        logger.info(f"权重更新: {sum(1 for r in results if r.get('action') == 'weight_updated')}")
        logger.info("")
        logger.info("当前层次分布:")
        logger.info(f"  ✓ 完整记忆 (full):    {level_distribution['full']}")
        logger.info(f"  📝 摘要记忆 (summary): {level_distribution['summary']}")
        logger.info(f"  🏷️  标签记忆 (tag):     {level_distribution['tag']}")
        logger.info(f"  👣 痕迹记忆 (trace):   {level_distribution['trace']}")
        logger.info(f"  📦 存档记忆 (archive): {level_distribution['archive']}")
        logger.info("="*80 + "\n")
    
    async def run_simulation(self, user_id: str):
        """运行模拟测试"""
        logger.info("\n" + "="*80)
        logger.info("🚀 记忆维护服务模拟测试启动")
        logger.info("="*80)
        logger.info(f"用户ID: {user_id}")
        logger.info(f"时间单位: {self.config.time_unit}")
        logger.info(f"时间加速: 1{self.config.time_unit} = {self.config.time_scale} 天")
        logger.info(f"扫描间隔: 每 {self.config.scan_interval_seconds} 秒")
        logger.info(f"衰减系数: α = {self.config.decay_alpha}")
        logger.info(f"最大周期: {self.config.max_cycles if self.config.max_cycles > 0 else '无限'}")
        logger.info("="*80)
        
        try:
            while True:
                # 运行维护周期
                await self.run_maintenance_cycle(user_id)
                
                # 检查是否达到最大周期
                if self.config.max_cycles > 0 and self.cycle_count >= self.config.max_cycles:
                    logger.info("✅ 达到最大测试周期，停止模拟")
                    break
                
                # 等待下次周期
                next_run = datetime.now() + timedelta(seconds=self.config.scan_interval_seconds)
                logger.info(f"⏰ 下次扫描: {next_run.strftime('%H:%M:%S')}")
                logger.info(f"⏳ 等待 {self.config.scan_interval_seconds} 秒...\n")
                
                await asyncio.sleep(self.config.scan_interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  用户中断")
        
        # 打印最终统计
        self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        logger.info("\n" + "="*80)
        logger.info("📊 模拟测试最终统计")
        logger.info("="*80)
        logger.info(f"总周期数: {self.stats['total_cycles']}")
        logger.info(f"总扫描数: {self.stats['total_memories_scanned']}")
        logger.info(f"模拟天数: {self.get_simulated_days():.2f} 天")
        logger.info("")
        logger.info("层次转换统计:")
        for transition, count in self.stats["level_transitions"].items():
            if count > 0:
                logger.info(f"  {transition.replace('_', ' → ')}: {count} 次")
        logger.info("")
        logger.info("最终层次分布:")
        for level, count in self.stats["current_distribution"].items():
            icon = self.get_level_icon(level)
            logger.info(f"  {icon} {level}: {count}")
        logger.info("="*80)


def create_test_memories(mem0_url: str, user_id: str, count: int = 5):
    """创建测试记忆"""
    logger.info(f"\n🧪 创建 {count} 条测试记忆...")
    
    test_messages = [
        "我叫张三，是一名AI工程师",
        "我特别喜欢喝咖啡，尤其是美式咖啡",
        "我每天早上7点起床",
        "我的生日是3月15日",
        "我住在北京海淀区",
        "我有一只叫旺财的狗",
        "我最喜欢的颜色是蓝色",
        "我周末喜欢去爬山",
        "我在清华大学读的本科",
        "我的手机号是138xxxxxxxx"
    ]
    
    created = 0
    for i in range(min(count, len(test_messages))):
        msg = test_messages[i]
        try:
            response = requests.post(
                f"{mem0_url}/memories",
                json={
                    "messages": [{"role": "user", "content": msg}],
                    "user_id": user_id,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "weight": 1.0,
                        "level": "full"
                    }
                },
                timeout=10
            )
            
            if response.status_code == 201:
                created += 1
                logger.info(f"  ✓ [{created}] {msg}")
            else:
                logger.warning(f"  ✗ 创建失败: {msg}")
        except Exception as e:
            logger.error(f"  ✗ 错误: {e}")
        
        time.sleep(0.5)  # 避免过快
    
    logger.info(f"\n✅ 成功创建 {created}/{count} 条记忆\n")
    return created


async def main():
    """主函数"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(
        description="记忆维护服务模拟测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
环境变量配置:
  MEM0_URL              Mem0服务地址 (默认: http://localhost:8000)
  ZHIPU_API_KEY         智谱AI API密钥
  SIM_TIME_UNIT         时间单位 (second/minute, 默认: second)
  SIM_TIME_SCALE        时间加速倍数 (默认: 1.0)
  SIM_SCAN_INTERVAL     扫描间隔秒数 (默认: 10)
  SIM_DECAY_ALPHA       衰减系数 (默认: 0.5)
  SIM_MAX_CYCLES        最大周期数 (默认: 10)
  SIM_USER_ID           测试用户ID (默认: test_user_sim)
  SIM_CREATE_MEMORIES   创建测试记忆数量 (默认: 0)

使用示例:
  # 使用默认配置
  uv run test-simulation
  
  # 自定义参数
  uv run test-simulation --max-cycles 20 --decay-alpha 1.0
  
  # 使用环境变量
  SIM_DECAY_ALPHA=2.0 SIM_MAX_CYCLES=15 uv run test-simulation
        """
    )
    parser.add_argument("--user-id", default=os.getenv('SIM_USER_ID', 'test_user_sim'), 
                       help="测试用户ID")
    parser.add_argument("--create-memories", type=int, 
                       default=int(os.getenv('SIM_CREATE_MEMORIES', '0')), 
                       help="创建测试记忆数量（0=不创建）")
    parser.add_argument("--time-unit", choices=["second", "minute"], 
                       help="时间单位（覆盖环境变量）")
    parser.add_argument("--time-scale", type=float,
                       help="时间加速倍数（覆盖环境变量）")
    parser.add_argument("--scan-interval", type=int,
                       help="扫描间隔秒数（覆盖环境变量）")
    parser.add_argument("--decay-alpha", type=float,
                       help="衰减系数（覆盖环境变量）")
    parser.add_argument("--max-cycles", type=int,
                       help="最大测试周期数（覆盖环境变量）")
    parser.add_argument("--clean", action="store_true",
                       help="清空用户历史记忆")
    
    args = parser.parse_args()
    
    # 创建配置（从环境变量加载）
    config = SimulationConfig()
    
    # 命令行参数覆盖环境变量
    if args.time_unit:
        config.time_unit = args.time_unit
    if args.time_scale is not None:
        config.time_scale = args.time_scale
    if args.scan_interval is not None:
        config.scan_interval_seconds = args.scan_interval
    if args.decay_alpha is not None:
        config.decay_alpha = args.decay_alpha
    if args.max_cycles is not None:
        config.max_cycles = args.max_cycles
    
    # 检查服务
    logger.info("📡 检查Mem0服务...")
    try:
        response = requests.get(f"{config.mem0_url}/health", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Mem0服务未运行")
            return
        logger.info("✓ Mem0服务正常\n")
    except Exception as e:
        logger.error(f"❌ 无法连接Mem0服务: {e}")
        logger.info(f"提示: 请检查 MEM0_URL={config.mem0_url}")
        return
    
    # 清空历史（如果需要）
    if args.clean:
        logger.info(f"🧹 清空用户 {args.user_id} 的历史记忆...")
        try:
            requests.delete(
                f"{config.mem0_url}/memories?user_id={args.user_id}",
                timeout=10
            )
            logger.info("✓ 已清空\n")
        except Exception as e:
            logger.warning(f"清空失败: {e}\n")
    
    # 创建测试记忆（如果需要）
    if args.create_memories > 0:
        created = create_test_memories(
            config.mem0_url,
            args.user_id,
            args.create_memories
        )
        if created == 0:
            logger.error("❌ 未能创建测试记忆，退出")
            return
    
    # 创建模拟器
    simulator = MemorySimulator(config)
    
    # 运行模拟
    await simulator.run_simulation(args.user_id)
    
    logger.info("\n👋 模拟测试结束")


if __name__ == "__main__":
    asyncio.run(main())
