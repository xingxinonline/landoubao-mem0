#!/usr/bin/env python3
"""
改进版记忆衰减曲线可视化 - 对比人类记忆
更大字体，更清晰布局，叠加艾宾浩斯遗忘曲线
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ImprovedMemoryVisualizer:
    """改进版记忆可视化器 - 清晰版"""
    
    def __init__(self, alpha=0.01):
        self.alpha = alpha
        
        # 五层阈值
        self.thresholds = {
            'full': 0.7,
            'summary': 0.3,
            'tag': 0.1,
            'trace': 0.03,
            'archive': 0.0
        }
        
        # 清晰的颜色配置
        self.colors = {
            'full': '#1B5E20',      # 深绿
            'summary': '#43A047',   # 绿
            'tag': '#FF6F00',       # 深橙
            'trace': '#C62828',     # 深红
            'archive': '#616161'    # 深灰
        }
        
        self.mem0_color = '#0D47A1'  # 深蓝
        self.human_color = '#B71C1C'  # 深红
    
    def mem0_decay(self, t):
        """Mem0记忆衰减"""
        return 1.0 / (1 + self.alpha * t)
    
    def human_decay(self, t):
        """人类遗忘曲线（艾宾浩斯）"""
        return np.exp(-0.05 * t)
    
    def plot_main_comparison(self, max_days=10950, output_path=None):
        """
        主对比图：Mem0 vs 人类记忆（30年）
        """
        # 创建更大的图形
        fig, ax = plt.subplots(figsize=(20, 12))
        
        # 生成数据
        days = np.linspace(0, max_days, 2000)
        mem0_weights = self.mem0_decay(days)
        human_weights = self.human_decay(days)
        
        # 绘制主曲线 - 更粗的线条
        ax.plot(days, mem0_weights, color=self.mem0_color, linewidth=4, 
               label='Mem0记忆系统（永不遗忘）', alpha=0.9, zorder=10)
        ax.plot(days, human_weights, color=self.human_color, linewidth=4, 
               label='人类记忆（艾宾浩斯遗忘曲线）', linestyle='--', alpha=0.9, zorder=10)
        
        # 绘制五层记忆区域 - 半透明填充
        ax.fill_between(days, 0.7, 1.0, color=self.colors['full'], 
                       alpha=0.12, label='完整记忆区 (>0.7)')
        ax.fill_between(days, 0.3, 0.7, color=self.colors['summary'], 
                       alpha=0.12, label='摘要记忆区 (0.3-0.7)')
        ax.fill_between(days, 0.1, 0.3, color=self.colors['tag'], 
                       alpha=0.12, label='标签记忆区 (0.1-0.3)')
        ax.fill_between(days, 0.03, 0.1, color=self.colors['trace'], 
                       alpha=0.12, label='痕迹记忆区 (0.03-0.1)')
        ax.fill_between(days, 0, 0.03, color=self.colors['archive'], 
                       alpha=0.12, label='归档记忆区 (≤0.03)')
        
        # 绘制阈值线 - 更清晰
        for name, value in [('full', 0.7), ('summary', 0.3), ('tag', 0.1), ('trace', 0.03)]:
            ax.axhline(y=value, color=self.colors[name], linestyle=':', 
                      linewidth=2.5, alpha=0.6)
        
        # 关键时间点 - 只标注最重要的几个
        key_points = [
            (1, '1天'),
            (7, '1周'),
            (30, '1月'),
            (180, '半年'),
            (365, '1年'),
            (1095, '3年'),
            (1825, '5年'),
            (3650, '10年'),
            (7300, '20年'),
            (10950, '30年')
        ]
        
        for i, (day, label) in enumerate(key_points):
            mem0_val = self.mem0_decay(day)
            human_val = self.human_decay(day)
            
            # 绘制垂直参考线
            ax.axvline(x=day, color='gray', linestyle=':', alpha=0.3, linewidth=1.5)
            
            # Mem0点标注
            ax.plot(day, mem0_val, 'o', color=self.mem0_color, 
                   markersize=14, markeredgecolor='white', markeredgewidth=2, zorder=15)
            
            # 人类记忆点标注（如果还可见）
            if human_val > 0.01:
                ax.plot(day, human_val, 's', color=self.human_color, 
                       markersize=14, markeredgecolor='white', markeredgewidth=2, zorder=15)
            
            # 时间标签 - 放在底部，调整位置避免重叠
            label_y = -0.12 if i % 2 == 0 else -0.18
            ax.text(day, label_y, label, ha='center', va='top',
                   fontsize=13, fontweight='bold', color='black',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', 
                           edgecolor='orange', linewidth=1.5, alpha=0.85))
            
            # Mem0数值标签 - 优化位置，只标注前7个关键点
            if i < 7:
                # 根据位置智能调整偏移
                if i % 2 == 0:
                    y_offset = 50
                    x_offset = -15
                else:
                    y_offset = -55
                    x_offset = 15
                
                ax.annotate(f'{mem0_val:.3f}', 
                           xy=(day, mem0_val),
                           xytext=(x_offset, y_offset),
                           textcoords='offset points',
                           fontsize=12,
                           fontweight='bold',
                           color=self.mem0_color,
                           ha='center',
                           bbox=dict(boxstyle='round,pad=0.35', 
                                   facecolor='white', 
                                   edgecolor=self.mem0_color,
                                   linewidth=1.5,
                                   alpha=0.9),
                           arrowprops=dict(arrowstyle='->', 
                                         color=self.mem0_color,
                                         linewidth=1.5))
            
            # 人类记忆数值标签 - 只标注前5个
            if human_val > 0.01 and i < 5:
                if i % 2 == 0:
                    y_offset = -55
                    x_offset = 15
                else:
                    y_offset = 50
                    x_offset = -15
                    
                ax.annotate(f'{human_val:.3f}', 
                           xy=(day, human_val),
                           xytext=(x_offset, y_offset),
                           textcoords='offset points',
                           fontsize=12,
                           fontweight='bold',
                           color=self.human_color,
                           ha='center',
                           bbox=dict(boxstyle='round,pad=0.35', 
                                   facecolor='white', 
                                   edgecolor=self.human_color,
                                   linewidth=1.5,
                                   alpha=0.9),
                           arrowprops=dict(arrowstyle='->', 
                                         color=self.human_color,
                                         linewidth=1.5))
        
        # 设置坐标轴 - 更大字体
        ax.set_xlabel('时间（天）', fontsize=22, fontweight='bold', labelpad=15)
        ax.set_ylabel('记忆强度', fontsize=22, fontweight='bold', labelpad=15)
        ax.set_title('Mem0 vs 人类记忆曲线对比（30年跨度）\n五层记忆架构 - 永不遗忘设计', 
                    fontsize=26, fontweight='bold', pad=30)
        
        # 图例 - 分两列，更大字体
        ax.legend(loc='upper right', fontsize=15, framealpha=0.95, 
                 ncol=2, columnspacing=2, handlelength=3,
                 edgecolor='black', fancybox=True, shadow=True)
        
        # 网格 - 更清晰
        ax.grid(True, alpha=0.4, linestyle='--', linewidth=1.2)
        
        # 坐标轴范围 - 增加底部空间
        ax.set_xlim(0, max_days)
        ax.set_ylim(-0.22, 1.08)
        
        # 刻度标签字体
        ax.tick_params(axis='both', labelsize=16, width=2, length=8)
        
        # 添加说明框 - 移到左下角避免遮盖
        info_text = f"""核心对比：

Mem0: w(t) = 1 / (1 + {self.alpha} × t)
人类: R(t) = e^(-0.05 × t)

关键差异：
• 30天: Mem0≈0.77  人类≈0.22
• 1年:  Mem0≈0.27  人类≈0.00
• 10年: Mem0≈0.02  人类≈0.00"""
        
        ax.text(0.02, 0.35, info_text, 
               transform=ax.transAxes,
               fontsize=14,
               verticalalignment='top',
               fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.8', 
                       facecolor='lightyellow', 
                       edgecolor='darkorange',
                       linewidth=2.5,
                       alpha=0.92))
        
        # 调整布局
        plt.tight_layout(pad=3)
        
        # 保存
        if output_path is None:
            output_path = os.path.join('..', 'visualizations', 'improved_comparison.svg')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, format='svg', dpi=150, bbox_inches='tight')
        plt.close()
        
        return os.path.abspath(output_path)
    
    def plot_one_year_comparison(self, max_days=365, output_path=None):
        """
        1年期对比 - 重点展示中期记忆变化
        """
        fig, ax = plt.subplots(figsize=(20, 11))
        
        days = np.linspace(0, max_days, 1000)
        mem0_weights = self.mem0_decay(days)
        human_weights = self.human_decay(days)
        
        # 主曲线 - 粗线条
        ax.plot(days, mem0_weights, color=self.mem0_color, linewidth=5, 
               label='Mem0记忆系统（永不遗忘）', alpha=0.9, zorder=10)
        ax.plot(days, human_weights, color=self.human_color, linewidth=5, 
               label='人类记忆（艾宾浩斯遗忘）', linestyle='--', alpha=0.9, zorder=10)
        
        # 五层区域填充
        ax.fill_between(days, 0.7, 1.0, color=self.colors['full'], 
                       alpha=0.12, label='完整记忆区 (>0.7)')
        ax.fill_between(days, 0.3, 0.7, color=self.colors['summary'], 
                       alpha=0.12, label='摘要记忆区 (0.3-0.7)')
        ax.fill_between(days, 0.1, 0.3, color=self.colors['tag'], 
                       alpha=0.12, label='标签记忆区 (0.1-0.3)')
        ax.fill_between(days, 0.03, 0.1, color=self.colors['trace'], 
                       alpha=0.12, label='痕迹记忆区 (0.03-0.1)')
        ax.fill_between(days, 0, 0.03, color=self.colors['archive'], 
                       alpha=0.12, label='归档记忆区 (≤0.03)')
        
        # 阈值线
        for name, value in [('full', 0.7), ('summary', 0.3), ('tag', 0.1), ('trace', 0.03)]:
            ax.axhline(y=value, color=self.colors[name], linestyle=':', 
                      linewidth=2.5, alpha=0.6)
        
        # 关键时间点 - 1年内的重要节点
        key_points = [
            (7, '1周'),
            (15, '半月'),
            (30, '1月'),
            (60, '2月'),
            (90, '3月'),
            (180, '半年'),
            (270, '9月'),
            (365, '1年')
        ]
        
        for i, (day, label) in enumerate(key_points):
            mem0_val = self.mem0_decay(day)
            human_val = self.human_decay(day)
            
            # 垂直参考线
            ax.axvline(x=day, color='gray', linestyle=':', alpha=0.3, linewidth=2)
            
            # 标记点
            ax.plot(day, mem0_val, 'o', color=self.mem0_color, 
                   markersize=16, markeredgecolor='white', markeredgewidth=3, zorder=15)
            
            if human_val > 0.005:
                ax.plot(day, human_val, 's', color=self.human_color, 
                       markersize=16, markeredgecolor='white', markeredgewidth=3, zorder=15)
            
            # 时间标签 - 交错两行
            label_y = -0.14 if i % 2 == 0 else -0.20
            ax.text(day, label_y, label, ha='center', va='top',
                   fontsize=14, fontweight='bold', color='black',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', 
                           edgecolor='orange', linewidth=2, alpha=0.85))
            
            # Mem0数值标注 - 所有点都标注
            if i % 2 == 0:
                y_offset = 55
                x_offset = -20
            else:
                y_offset = -60
                x_offset = 20
            
            ax.annotate(f'{mem0_val:.3f}', 
                       xy=(day, mem0_val),
                       xytext=(x_offset, y_offset),
                       textcoords='offset points',
                       fontsize=13,
                       fontweight='bold',
                       color=self.mem0_color,
                       ha='center',
                       bbox=dict(boxstyle='round,pad=0.4', 
                               facecolor='white', 
                               edgecolor=self.mem0_color,
                               linewidth=2,
                               alpha=0.92),
                       arrowprops=dict(arrowstyle='->', 
                                     color=self.mem0_color,
                                     linewidth=2))
            
            # 人类记忆数值标注 - 只标注可见的，统一放到右侧或上方
            if human_val > 0.005:
                # 根据数值大小决定位置
                if human_val > 0.7:  # 第一个点，放在线上方
                    y_offset = 45
                    x_offset = 0
                    h_align = 'center'
                elif human_val > 0.15:  # 较高的值，放在右上方
                    y_offset = 40
                    x_offset = 35
                    h_align = 'left'
                elif human_val > 0.05:  # 中等值，放在右侧
                    y_offset = 0
                    x_offset = 50
                    h_align = 'left'
                else:  # 较低的值，放在右上方
                    y_offset = 30
                    x_offset = 40
                    h_align = 'left'
                    
                ax.annotate(f'{human_val:.3f}', 
                           xy=(day, human_val),
                           xytext=(x_offset, y_offset),
                           textcoords='offset points',
                           fontsize=13,
                           fontweight='bold',
                           color=self.human_color,
                           ha=h_align,
                           bbox=dict(boxstyle='round,pad=0.4', 
                                   facecolor='white', 
                                   edgecolor=self.human_color,
                                   linewidth=2,
                                   alpha=0.92),
                           arrowprops=dict(arrowstyle='->', 
                                         color=self.human_color,
                                         linewidth=2))
        
        # 设置坐标轴
        ax.set_xlabel('时间（天）', fontsize=22, fontweight='bold', labelpad=15)
        ax.set_ylabel('记忆强度', fontsize=22, fontweight='bold', labelpad=15)
        ax.set_title('1年期记忆对比 - Mem0 vs 人类记忆\n五层记忆架构 vs 艾宾浩斯遗忘曲线', 
                    fontsize=26, fontweight='bold', pad=30)
        
        # 图例
        ax.legend(loc='upper right', fontsize=15, framealpha=0.95, 
                 ncol=2, columnspacing=2, handlelength=3,
                 edgecolor='black', fancybox=True, shadow=True)
        
        # 网格
        ax.grid(True, alpha=0.4, linestyle='--', linewidth=1.2)
        
        # 坐标轴范围
        ax.set_xlim(0, max_days)
        ax.set_ylim(-0.24, 1.08)
        
        # 刻度标签
        ax.tick_params(axis='both', labelsize=16, width=2, length=8)
        
        # 说明框 - 放在中上部
        info_text = f"""1年期对比数据：

1周:   Mem0≈0.93  人类≈0.70
1月:   Mem0≈0.77  人类≈0.22
3月:   Mem0≈0.53  人类≈0.01
半年:  Mem0≈0.36  人类≈0.00
1年:   Mem0≈0.27  人类≈0.00

关键发现：
• 1月后差距3.5倍
• 3月后人类几乎遗忘
• Mem0始终保留可用记忆"""
        
        ax.text(0.50, 0.95, info_text, 
               transform=ax.transAxes,
               fontsize=14,
               verticalalignment='top',
               horizontalalignment='center',
               fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.8', 
                       facecolor='lightcyan', 
                       edgecolor='darkblue',
                       linewidth=2.5,
                       alpha=0.92))
        
        plt.tight_layout(pad=3)
        
        if output_path is None:
            output_path = os.path.join('..', 'visualizations', 'one_year_comparison.svg')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, format='svg', dpi=150, bbox_inches='tight')
        plt.close()
        
        return os.path.abspath(output_path)
    
    def plot_short_term(self, max_days=30, output_path=None):
        """
        短期对比（30天） - 清晰版
        """
        fig, ax = plt.subplots(figsize=(18, 11))
        
        days = np.linspace(0, max_days, 500)
        mem0_weights = self.mem0_decay(days)
        human_weights = self.human_decay(days)
        
        # 主曲线
        ax.plot(days, mem0_weights, color=self.mem0_color, linewidth=5, 
               label='Mem0记忆系统', alpha=0.9)
        ax.plot(days, human_weights, color=self.human_color, linewidth=5, 
               label='人类记忆（艾宾浩斯）', linestyle='--', alpha=0.9)
        
        # 五层区域
        ax.fill_between(days, 0.7, 1.0, color=self.colors['full'], alpha=0.15)
        ax.fill_between(days, 0.3, 0.7, color=self.colors['summary'], alpha=0.15)
        ax.fill_between(days, 0.1, 0.3, color=self.colors['tag'], alpha=0.15)
        ax.fill_between(days, 0.03, 0.1, color=self.colors['trace'], alpha=0.15)
        
        # 阈值线
        for value, color in [(0.7, self.colors['full']), (0.3, self.colors['summary']),
                             (0.1, self.colors['tag']), (0.03, self.colors['trace'])]:
            ax.axhline(y=value, color=color, linestyle=':', linewidth=3, alpha=0.6)
        
        # 关键点
        key_days = [1, 3, 7, 15, 30]
        labels = ['1天', '3天', '1周', '半月', '1月']
        
        for day, label in zip(key_days, labels):
            mem0_val = self.mem0_decay(day)
            human_val = self.human_decay(day)
            
            # 标记点
            ax.plot(day, mem0_val, 'o', color=self.mem0_color, markersize=18,
                   markeredgecolor='white', markeredgewidth=3)
            ax.plot(day, human_val, 's', color=self.human_color, markersize=18,
                   markeredgecolor='white', markeredgewidth=3)
            
            # 垂直线
            ax.axvline(x=day, color='gray', linestyle=':', alpha=0.3, linewidth=2)
            
            # 标签
            ax.text(day, -0.13, label, ha='center', fontsize=16, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.6', facecolor='yellow', 
                           edgecolor='orange', linewidth=2))
            
            # 数值
            ax.text(day, mem0_val + 0.08, f'{mem0_val:.3f}', ha='center',
                   fontsize=14, fontweight='bold', color=self.mem0_color,
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                           edgecolor=self.mem0_color, linewidth=2))
            
            ax.text(day, human_val - 0.08, f'{human_val:.3f}', ha='center',
                   fontsize=14, fontweight='bold', color=self.human_color,
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                           edgecolor=self.human_color, linewidth=2))
        
        # 设置
        ax.set_xlabel('时间（天）', fontsize=22, fontweight='bold', labelpad=15)
        ax.set_ylabel('记忆强度', fontsize=22, fontweight='bold', labelpad=15)
        ax.set_title('短期记忆对比（30天） - Mem0 vs 人类记忆', 
                    fontsize=26, fontweight='bold', pad=25)
        
        ax.legend(fontsize=18, loc='upper right', framealpha=0.95,
                 edgecolor='black', fancybox=True, shadow=True)
        ax.grid(True, alpha=0.4, linestyle='--', linewidth=1.2)
        ax.set_xlim(0, max_days)
        ax.set_ylim(-0.17, 1.08)
        ax.tick_params(axis='both', labelsize=16, width=2, length=8)
        
        # 说明
        info = """对比发现（30天）：

开始:  两者相同 (1.00)
1天:   差距微小
1周:   Mem0领先约7%
1月:   Mem0≈0.77  人类≈0.22
         Mem0保留3.5倍记忆！"""
        
        ax.text(0.98, 0.50, info, transform=ax.transAxes,
               fontsize=16, ha='right', va='center', fontweight='bold',
               bbox=dict(boxstyle='round,pad=1', facecolor='lightgreen',
                       edgecolor='darkgreen', linewidth=3, alpha=0.9))
        
        plt.tight_layout(pad=3)
        
        if output_path is None:
            output_path = os.path.join('..', 'visualizations', 'short_term_clear.svg')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, format='svg', dpi=150, bbox_inches='tight')
        plt.close()
        
        return os.path.abspath(output_path)


def main():
    """主函数"""
    print("=" * 70)
    print("  改进版记忆曲线可视化 - 清晰大字体版本")
    print("  叠加人类艾宾浩斯遗忘曲线对比")
    print("=" * 70)
    print()
    
    visualizer = ImprovedMemoryVisualizer()
    
    print("📊 生成清晰对比图表...")
    print()
    
    # 主对比图（30年）
    print("1. 生成主对比图（30年跨度）...")
    path1 = visualizer.plot_main_comparison()
    print(f"✓ 已保存: {path1}")
    print()
    
    # 1年期对比
    print("2. 生成1年期对比图...")
    path2 = visualizer.plot_one_year_comparison()
    print(f"✓ 已保存: {path2}")
    print()
    
    # 短期对比（30天）
    print("3. 生成短期对比图（30天）...")
    path3 = visualizer.plot_short_term()
    print(f"✓ 已保存: {path3}")
    print()
    
    print("=" * 70)
    print("✅ 所有图表生成完成！")
    print("=" * 70)
    print()
    print("生成的文件:")
    print("  • improved_comparison.svg - 主对比图（30年）")
    print("  • one_year_comparison.svg - 1年期对比图")
    print("  • short_term_clear.svg - 短期对比（30天）")
    print()
    print("💡 改进说明:")
    print("  ✓ 字体大幅增大（标题26pt，标签22pt）")
    print("  ✓ 线条加粗（4-5px）")
    print("  ✓ 标注间距加大，避免重叠")
    print("  ✓ 叠加人类艾宾浩斯遗忘曲线")
    print("  ✓ 更清晰的颜色对比")
    print("  ✓ 图例分栏显示")
    print("  ✓ 新增1年期中期对比图")


if __name__ == '__main__':
    main()
