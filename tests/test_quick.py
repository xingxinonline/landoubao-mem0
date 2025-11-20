#!/usr/bin/env python3
"""
简化快速测试 - 直接测试存档记忆回顾
"""

import requests
import time

MEM0_URL = "http://localhost:8000"
USER_ID = "quick_test_user"

def add_memory(content):
    """添加记忆"""
    response = requests.post(f"{MEM0_URL}/memories", json={
        "messages": [{"role": "user", "content": content}],
        "user_id": USER_ID
    })
    if response.status_code in [200, 201]:
        print(f"✓ 添加: {content}")
        return response.json()
    print(f"✗ 失败: {content}")
    return None

def get_memories():
    """获取所有记忆"""
    response = requests.get(f"{MEM0_URL}/memories", params={"user_id": USER_ID, "limit": 100})
    return response.json() if response.status_code == 200 else None

def trigger_maintenance():
    """触发维护"""
    response = requests.post(f"{MEM0_URL}/admin/maintenance/run")
    if response.status_code == 200:
        print("✓ 维护完成")
        return response.json()
    print(f"✗ 维护失败")
    return None

def search(query):
    """搜索记忆"""
    response = requests.post(f"{MEM0_URL}/memories/search", json={
        "query": query, 
        "user_id": USER_ID, 
        "limit": 20
    })
    return response.json() if response.status_code == 200 else None

def display_memories(mems, title):
    """显示记忆"""
    print(f"\n{title}:")
    print("-" * 60)
    if not mems or not mems.get('results'):
        print("  无记忆")
        return
    
    for i, m in enumerate(mems['results'][:10], 1):
        w = m.get('score', 0)
        content = m.get('memory', '')[:60]
        level = "🟢完整" if w > 0.7 else "🟡摘要" if w >= 0.3 else "🟠标签" if w >= 0.1 else "🔴痕迹" if w >= 0.03 else "⚫存档"
        print(f"{i}. {level} [{w:.4f}] {content}")

print("=" * 70)
print("  存档记忆快速测试 - 闪电模式 (alpha=100)")
print("=" * 70)

# 步骤1：添加记忆
print("\n📝 步骤1: 添加测试记忆")
memories = [
    "我最喜欢的颜色是蓝色",
    "我养了一只叫Max的金毛犬",
    "我在北京工作，职业是软件工程师",
    "我喜欢在周末去爬山",
    "我的生日是5月15日"
]

for mem in memories:
    add_memory(mem)
    time.sleep(0.3)

# 步骤2：查看初始状态
print("\n📊 步骤2: 查看当前状态")
all_mems = get_memories()
display_memories(all_mems, "所有记忆")

# 步骤3：等待衰减
print("\n⏳ 步骤3: 等待记忆衰减")
print("  使用 alpha=100.0 (闪电模式)")
print("  公式: w(t) = 1 / (1 + 100 × t)")
print("  时间说明:")
print("    - 36秒后: 权重约0.5")
print("    - 2分钟后: 权重约0.008 (进入痕迹层)")
print("    - 12分钟后: 权重约0.001 (进入存档层)")

wait_secs = input("\n⏰ 等待多少秒后触发维护? [推荐:120秒=2分钟] (直接回车=120): ")
wait_secs = int(wait_secs) if wait_secs.strip() else 120

print(f"\n等待 {wait_secs} 秒...")
for i in range(wait_secs, 0, -10):
    print(f"  剩余 {i} 秒...", end='\r')
    time.sleep(min(10, i))
print("\n✓ 等待完成")

# 步骤4：触发维护
print("\n🔧 步骤4: 触发维护任务")
result = trigger_maintenance()
if result:
    print(f"  更新记忆数: {result.get('report', {}).get('updated_memories', 0)}")

time.sleep(2)

# 步骤5：查看更新后状态
print("\n📊 步骤5: 维护后状态")
all_mems = get_memories()
display_memories(all_mems, "所有记忆（权重已更新）")

# 统计分布
if all_mems and all_mems.get('results'):
    levels = {"完整": 0, "摘要": 0, "标签": 0, "痕迹": 0, "存档": 0}
    for m in all_mems['results']:
        w = m.get('score', 0)
        if w > 0.7: levels["完整"] += 1
        elif w >= 0.3: levels["摘要"] += 1
        elif w >= 0.1: levels["标签"] += 1
        elif w >= 0.03: levels["痕迹"] += 1
        else: levels["存档"] += 1
    
    print(f"\n📈 记忆层次分布:")
    print(f"  🟢 完整: {levels['完整']}  🟡 摘要: {levels['摘要']}  🟠 标签: {levels['标签']}  🔴 痕迹: {levels['痕迹']}  ⚫ 存档: {levels['存档']}")

# 步骤6：测试普通搜索
print("\n🔍 步骤6: 普通搜索测试")
queries = ["我喜欢什么颜色", "我的宠物", "我的工作"]
for q in queries:
    print(f"\n查询: {q}")
    results = search(q)
    display_memories(results, "  结果")

# 步骤7：测试回顾模式
print("\n🔍 步骤7: 回顾模式测试")
print("  💡 回顾关键词会触发检索所有层次（包括存档）")
review_queries = ["回顾一下我以前说过的", "帮我回顾过去的记忆"]
for q in review_queries:
    print(f"\n回顾查询: {q}")
    results = search(q)
    display_memories(results, "  结果（应包含存档记忆）")

print("\n" + "=" * 70)
print("✅ 测试完成！")
print("=" * 70)
print("\n💡 关键点:")
print("  1. 存档记忆 (权重<0.03) 不应在普通搜索中返回")
print("  2. 回顾模式应返回所有层次记忆")
print("  3. 记忆永不删除，只是转换层次")
