#!/usr/bin/env python3
"""
智能记忆管理完整演示
Integrated Demo: Smart Memory Management + Maintenance Service

演示场景：
1. 用户进行多轮对话（存储记忆）
2. 模拟时间流逝（修改记忆时间戳）
3. 运行维护服务（应用衰减、生成摘要）
4. 验证记忆层次变化
"""

import requests
import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# 添加app目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

# 配置
BASE_URL = "http://localhost:8000"
ZHIPU_API_KEY = ""

# 读取API key
try:
    env_path = Path(__file__).parent.parent / 'app' / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('ZHIPU_API_KEY='):
                    ZHIPU_API_KEY = line.split('=', 1)[1].strip()
                    break
    print(f"✓ 已加载API Key")
except Exception as e:
    print(f"Warning: Could not read API key: {e}")


def print_section(title):
    """打印章节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def check_services():
    """检查服务状态"""
    print_section("📡 步骤1: 检查服务状态")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Mem0服务运行正常")
            return True
        else:
            print("❌ Mem0服务异常")
            return False
    except Exception as e:
        print(f"❌ 无法连接Mem0服务: {e}")
        return False


def create_test_memories(user_id):
    """创建测试记忆"""
    print_section("💾 步骤2: 创建测试记忆")
    
    test_messages = [
        "我叫张三，是一名AI工程师",
        "我特别喜欢喝咖啡，尤其是美式咖啡",
        "我住在北京朝阳区",
        "我的生日是5月15日",
        "我最喜欢的编程语言是Python",
        "我有一只猫叫Tom",
    ]
    
    memory_ids = []
    
    for msg in test_messages:
        print(f"存储: {msg}")
        try:
            response = requests.post(
                f"{BASE_URL}/memories",
                json={
                    "messages": [{"role": "user", "content": msg}],
                    "user_id": user_id,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "weight": 1.0,
                        "level": "full"
                    }
                },
                timeout=30
            )
            
            if response.status_code == 201:
                results = response.json().get("results", [])
                print(f"  ✓ 创建了 {len(results)} 条记忆")
                for r in results:
                    if 'id' in r:
                        memory_ids.append(r['id'])
            
            time.sleep(0.5)
        except Exception as e:
            print(f"  ✗ 失败: {e}")
    
    print(f"\n✓ 共创建 {len(memory_ids)} 条记忆")
    return memory_ids


def simulate_time_passage(user_id, days_ago_list):
    """模拟时间流逝（修改记忆时间戳）"""
    print_section("⏰ 步骤3: 模拟时间流逝")
    
    print("获取当前记忆...")
    try:
        response = requests.get(f"{BASE_URL}/memories?user_id={user_id}", timeout=10)
        if response.status_code != 200:
            print("❌ 无法获取记忆")
            return False
        
        memories = response.json().get("results", [])
        print(f"找到 {len(memories)} 条记忆\n")
        
        # 为不同记忆设置不同的时间（模拟不同时期的记忆）
        for idx, mem in enumerate(memories[:len(days_ago_list)]):
            days_ago = days_ago_list[idx]
            old_time = datetime.now() - timedelta(days=days_ago)
            
            print(f"记忆 {idx+1}: {mem.get('memory', '')[:40]}...")
            print(f"  设置为 {days_ago} 天前 ({old_time.strftime('%Y-%m-%d')})")
            
            # 注意：Mem0 API可能不支持直接更新时间戳
            # 这里仅做演示，实际需要通过Qdrant直接操作
            # 或者在创建时就设置不同时间
        
        print("\n⚠️  注意: Mem0 API暂不支持直接修改时间戳")
        print("   在真实场景中，记忆会随时间自然老化")
        print("   这里我们将通过调整decay_alpha来加速演示\n")
        
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def view_memories_before_maintenance(user_id):
    """维护前查看记忆"""
    print_section("📋 步骤4: 维护前的记忆状态")
    
    try:
        response = requests.get(f"{BASE_URL}/memories?user_id={user_id}", timeout=10)
        if response.status_code == 200:
            memories = response.json().get("results", [])
            
            print(f"当前记忆总数: {len(memories)}\n")
            
            for idx, mem in enumerate(memories, 1):
                content = mem.get("memory", "")
                metadata = mem.get("metadata", {})
                timestamp = metadata.get("timestamp", "")
                weight = metadata.get("weight", 1.0)
                level = metadata.get("level", "full")
                
                print(f"{idx}. {content[:50]}")
                print(f"   层次: {level} | 权重: {weight} | 时间: {timestamp[:19]}")
            
            return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def run_maintenance_once():
    """运行一次维护任务"""
    print_section("🔧 步骤5: 执行记忆维护")
    
    print("启动维护服务...")
    print("命令: python app/memory_maintenance.py --once\n")
    
    # 导入维护服务
    try:
        from memory_maintenance import MemoryMaintenanceService, MaintenanceConfig
        
        # 配置（加速衰减用于演示）
        config = MaintenanceConfig(
            decay_alpha=0.1,  # 大幅提高衰减速度用于演示
            full_memory_threshold=0.7,
            summary_memory_threshold=0.3,
            cleanup_threshold=0.05,
        )
        
        service = MemoryMaintenanceService(config)
        
        # 异步运行
        asyncio.run(service.run_maintenance_cycle())
        
        print("\n✓ 维护任务完成")
        return True
    except Exception as e:
        print(f"❌ 维护任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def view_memories_after_maintenance(user_id):
    """维护后查看记忆"""
    print_section("📊 步骤6: 维护后的记忆状态")
    
    try:
        response = requests.get(f"{BASE_URL}/memories?user_id={user_id}", timeout=10)
        if response.status_code == 200:
            memories = response.json().get("results", [])
            
            print(f"维护后记忆总数: {len(memories)}\n")
            
            stats = {"full": 0, "summary": 0, "tag": 0}
            
            for idx, mem in enumerate(memories, 1):
                content = mem.get("memory", "")
                metadata = mem.get("metadata", {})
                timestamp = metadata.get("timestamp", "")
                weight = metadata.get("weight", 1.0)
                level = metadata.get("level", "full")
                
                stats[level] = stats.get(level, 0) + 1
                
                # 标记变化
                marker = ""
                if level == "summary":
                    marker = "📝 [已摘要] "
                elif level == "tag":
                    marker = "🏷️  [已标签化] "
                elif weight < 0.7:
                    marker = "⚠️  [权重降低] "
                
                print(f"{idx}. {marker}{content[:50]}")
                print(f"   层次: {level} | 权重: {weight:.3f} | 时间: {timestamp[:19]}")
            
            print(f"\n统计:")
            print(f"  完整记忆: {stats.get('full', 0)}")
            print(f"  摘要记忆: {stats.get('summary', 0)}")
            print(f"  标签记忆: {stats.get('tag', 0)}")
            
            return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def demonstrate_query_with_decay(user_id):
    """演示带衰减的查询"""
    print_section("🔍 步骤7: 测试记忆查询（带衰减）")
    
    queries = [
        "我叫什么名字？",
        "我喜欢什么？",
        "我的个人信息有哪些？"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/memories/search",
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": 5
                },
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                print(f"找到 {len(results)} 条相关记忆:")
                
                for idx, mem in enumerate(results, 1):
                    content = mem.get("memory", "")
                    score = mem.get("score", 0)
                    metadata = mem.get("metadata", {})
                    level = metadata.get("level", "full")
                    
                    level_icon = {
                        "full": "✓",
                        "summary": "~",
                        "tag": "·"
                    }.get(level, "?")
                    
                    print(f"  {level_icon} [{score:.3f}] {content[:60]}")
        except Exception as e:
            print(f"  ✗ 查询失败: {e}")
        
        time.sleep(0.5)


def run_full_demo():
    """运行完整演示"""
    print("\n" + "🌟"*40)
    print("  智能记忆管理完整演示")
    print("  演示内容：记忆存储 → 时间流逝 → 自动维护 → 智能查询")
    print("🌟"*40)
    
    user_id = "demo_user_001"
    
    # 步骤1: 检查服务
    if not check_services():
        return False
    
    # 清空旧记忆
    print("\n清空旧记忆...")
    try:
        requests.delete(f"{BASE_URL}/memories?user_id={user_id}", timeout=10)
        print("✓ 清空完成")
    except:
        pass
    
    # 步骤2: 创建测试记忆
    memory_ids = create_test_memories(user_id)
    if not memory_ids:
        print("❌ 创建记忆失败")
        return False
    
    time.sleep(1)
    
    # 步骤3: 模拟时间流逝
    # 设置不同的时间：最近、30天前、100天前、200天前
    days_list = [0, 30, 100, 200, 300, 500]
    simulate_time_passage(user_id, days_list)
    
    # 步骤4: 维护前查看
    view_memories_before_maintenance(user_id)
    
    input("\n按回车键继续执行维护任务...")
    
    # 步骤5: 运行维护
    if not run_maintenance_once():
        print("❌ 维护任务失败")
        # 继续执行以查看当前状态
    
    # 步骤6: 维护后查看
    view_memories_after_maintenance(user_id)
    
    # 步骤7: 测试查询
    demonstrate_query_with_decay(user_id)
    
    # 总结
    print_section("✅ 演示完成")
    print("核心展示:")
    print("  1. ✓ 记忆随时间自动衰减")
    print("  2. ✓ 权重降低自动转为摘要")
    print("  3. ✓ 三层记忆架构（完整/摘要/标签）")
    print("  4. ✓ 查询时考虑记忆清晰度")
    print("  5. ✓ 低权重记忆自动清理")
    
    print("\n💡 提示:")
    print("  - 查看维护日志: cat app/memory_maintenance.log")
    print("  - 查看维护报告: cat app/maintenance_reports/report_*.json")
    print("  - 启动定时服务(测试模式): python app/memory_maintenance.py --test")
    
    return True


if __name__ == "__main__":
    success = run_full_demo()
    exit(0 if success else 1)
