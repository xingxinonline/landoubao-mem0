#!/usr/bin/env python3
"""
快速测试脚本 - 测试存档记忆回顾功能
使用超快衰减参数，在几分钟内触发存档记忆
"""

import requests
import time
import json
from datetime import datetime

# 配置
MEM0_URL = "http://localhost:8000"
USER_ID = "test_archive_user"

# 使用超快衰减系数，几分钟内就能达到存档状态
# alpha=10 意味着 w(t) = 1/(1+10*t)，其中t以分钟为单位
# 1分钟后：w = 1/11 ≈ 0.09
# 2分钟后：w = 1/21 ≈ 0.048
# 3分钟后：w = 1/31 ≈ 0.032
# 4分钟后：w = 1/41 ≈ 0.024 （存档状态）

def print_section(title):
    """打印分隔标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def add_memory(content: str, metadata: dict = None):
    """添加记忆"""
    data = {
        "messages": [{"role": "user", "content": content}],
        "user_id": USER_ID
    }
    if metadata:
        data["metadata"] = metadata
    
    response = requests.post(f"{MEM0_URL}/memories", json=data)
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✓ 记忆已添加: {content[:50]}...")
        return result
    else:
        print(f"✗ 添加失败: {response.text}")
        return None

def search_memories(query: str, limit: int = 10):
    """搜索记忆"""
    response = requests.post(
        f"{MEM0_URL}/search",
        json={"query": query, "user_id": USER_ID, "limit": limit}
    )
    if response.status_code == 200:
        return response.json()
    return None

def get_all_memories():
    """获取所有记忆"""
    response = requests.get(f"{MEM0_URL}/memories", params={"user_id": USER_ID, "limit": 100})
    if response.status_code == 200:
        return response.json()
    return None

def trigger_maintenance():
    """触发维护任务"""
    try:
        response = requests.post(f"{MEM0_URL}/admin/maintenance/run")
        if response.status_code == 200:
            print("✓ 维护任务已触发")
            return response.json()
        else:
            print(f"✗ 触发失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"⚠ 维护接口错误: {e}")
        print("  提示: 确保容器已重启并正常运行")
        return None

def display_memories(memories, title="记忆列表"):
    """显示记忆"""
    if not memories:
        print(f"  {title}: 无记忆")
        return
    
    print(f"\n{title}:")
    print("-" * 70)
    
    results = memories.get('results', memories) if isinstance(memories, dict) else memories
    
    for i, mem in enumerate(results, 1):
        mem_id = mem.get('id', 'N/A')
        content = mem.get('memory', mem.get('text', 'N/A'))
        score = mem.get('score', mem.get('weight', 0))
        created = mem.get('created_at', mem.get('created_at', 'N/A'))
        
        # 判断层次
        if score > 0.7:
            level = "完整记忆"
            icon = "🟢"
        elif score >= 0.3:
            level = "摘要记忆"
            icon = "🟡"
        elif score >= 0.1:
            level = "标签记忆"
            icon = "🟠"
        elif score >= 0.03:
            level = "痕迹记忆"
            icon = "🔴"
        else:
            level = "存档记忆"
            icon = "⚫"
        
        print(f"{i}. {icon} [{level}] 权重: {score:.4f}")
        print(f"   内容: {content[:80]}...")
        print(f"   ID: {mem_id}")
        print()

def main():
    """主测试流程"""
    print_section("存档记忆回顾功能 - 快速测试")
    
    print("\n📋 测试计划:")
    print("1. 添加一些初始记忆")
    print("2. 等待几分钟让记忆衰减")
    print("3. 触发维护任务更新权重")
    print("4. 测试普通检索（不应返回存档记忆）")
    print("5. 测试回顾模式（应返回存档记忆）")
    
    input("\n按回车键开始测试...")
    
    # 第1步：添加记忆
    print_section("步骤1: 添加初始记忆")
    
    memories = [
        "我最喜欢的颜色是蓝色",
        "我养了一只叫Max的金毛犬",
        "我在北京工作，职业是软件工程师",
        "我喜欢在周末去爬山",
        "我的生日是5月15日"
    ]
    
    for mem in memories:
        add_memory(mem)
        time.sleep(0.5)
    
    print(f"\n✓ 已添加 {len(memories)} 条记忆")
    
    # 显示当前状态
    print_section("当前记忆状态")
    all_mems = get_all_memories()
    display_memories(all_mems, "所有记忆")
    
    # 第2步：等待衰减
    print_section("步骤2: 等待记忆衰减")
    
    print("\n⏰ 等待时间配置:")
    print("  • 使用衰减系数 alpha=0.01 (标准配置)")
    print("  • 需要等待约4-5分钟才能达到存档状态 (权重<0.03)")
    print("\n或者你可以:")
    print("  1. 修改 app/memory_maintenance.py 中的 decay_alpha 为更大值")
    print("  2. 手动修改数据库中的 updated_at 时间戳")
    print("  3. 等待足够时间让记忆自然衰减")
    
    wait_choice = input("\n选择:\n[1] 等待5分钟\n[2] 手动修改配置后继续\n[3] 跳过等待直接测试\n请输入选择 (1/2/3): ")
    
    if wait_choice == "1":
        print("\n⏳ 等待5分钟...")
        for i in range(5, 0, -1):
            print(f"   剩余 {i} 分钟...", end='\r')
            time.sleep(60)
        print("\n✓ 等待完成")
    elif wait_choice == "2":
        print("\n💡 提示:")
        print("  修改 app/memory_maintenance.py:")
        print("  decay_alpha: float = 0.01  →  decay_alpha: float = 10.0")
        print("  然后重启 Docker 容器: docker-compose restart")
        input("\n修改完成后按回车继续...")
    else:
        print("\n⏭ 跳过等待，继续测试...")
    
    # 第3步：触发维护
    print_section("步骤3: 触发维护任务")
    
    result = trigger_maintenance()
    if result:
        print("\n维护结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    time.sleep(2)
    
    # 显示更新后的状态
    print_section("维护后记忆状态")
    all_mems = get_all_memories()
    display_memories(all_mems, "所有记忆（权重已更新）")
    
    # 第4步：普通检索测试
    print_section("步骤4: 普通检索测试（不应返回存档记忆）")
    
    queries = [
        "我喜欢什么颜色",
        "我的宠物",
        "我的工作"
    ]
    
    for query in queries:
        print(f"\n🔍 查询: {query}")
        results = search_memories(query, limit=5)
        if results and results.get('results'):
            display_memories(results, f"检索结果")
        else:
            print("  无匹配结果")
    
    # 第5步：回顾模式测试
    print_section("步骤5: 回顾模式测试（应返回存档记忆）")
    
    review_queries = [
        "回顾一下我以前说过的所有事情",
        "帮我回顾过去的记忆",
        "我很久以前提到过什么"
    ]
    
    print("\n💡 回顾关键词: 回顾、以前、过去、历史、很久以前、曾经")
    
    for query in review_queries:
        print(f"\n🔍 回顾查询: {query}")
        results = search_memories(query, limit=10)
        if results and results.get('results'):
            display_memories(results, f"回顾结果（包含存档记忆）")
        else:
            print("  无匹配结果")
    
    # 总结
    print_section("测试总结")
    
    all_mems = get_all_memories()
    if all_mems:
        results = all_mems.get('results', all_mems) if isinstance(all_mems, dict) else all_mems
        
        levels = {"完整": 0, "摘要": 0, "标签": 0, "痕迹": 0, "存档": 0}
        
        for mem in results:
            score = mem.get('score', mem.get('weight', 0))
            if score > 0.7:
                levels["完整"] += 1
            elif score >= 0.3:
                levels["摘要"] += 1
            elif score >= 0.1:
                levels["标签"] += 1
            elif score >= 0.03:
                levels["痕迹"] += 1
            else:
                levels["存档"] += 1
        
        print("\n📊 记忆层次分布:")
        print(f"  🟢 完整记忆: {levels['完整']} 条 (权重 > 0.7)")
        print(f"  🟡 摘要记忆: {levels['摘要']} 条 (0.3 ~ 0.7)")
        print(f"  🟠 标签记忆: {levels['标签']} 条 (0.1 ~ 0.3)")
        print(f"  🔴 痕迹记忆: {levels['痕迹']} 条 (0.03 ~ 0.1)")
        print(f"  ⚫ 存档记忆: {levels['存档']} 条 (≤ 0.03)")
        
        print("\n✅ 测试要点:")
        print(f"  1. 存档记忆数量: {levels['存档']} 条")
        print("  2. 普通检索不应返回存档记忆（权重<0.03）")
        print("  3. 回顾模式应返回所有层次记忆（包括存档）")
        print("  4. 记忆永不删除，只是转换层次")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸ 测试已中断")
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
