#!/usr/bin/env python3
"""
记忆衰减曲线可视化工具
Memory Decay Curve Visualization

生成美观的SVG动态图，展示五层记忆架构的衰减过程
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import matplotlib.font_manager as fm
from pathlib import Path
import sys

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class MemoryDecayVisualizer:
    """记忆衰减可视化器"""
    
    def __init__(self, alpha=0.01):
        """
        初始化
        
        Args:
            alpha: 衰减系数
        """
        self.alpha = alpha
        
        # 五层阈值
        self.thresholds = {
            'full': 0.7,
            'summary': 0.3,
            'tag': 0.1,
            'trace': 0.03,
            'archive': 0.0
        }
        
        # 五层颜色（渐变色，从深到浅）
        self.colors = {
            'full': '#2E7D32',      # 深绿
            'summary': '#66BB6A',   # 中绿
            'tag': '#FFA726',       # 橙色
            'trace': '#EF5350',     # 红色
            'archive': '#9E9E9E'    # 灰色
        }
        
        # 层次名称
        self.level_names = {
            'full': '完整记忆',
            'summary': '摘要记忆',
            'tag': '模糊标签',
            'trace': '痕迹记忆',
            'archive': '存档记忆'
        }
    
    def calculate_weight(self, days):
        """计算权重: w(t) = 1 / (1 + α * t)"""
        return 1.0 / (1 + self.alpha * days)
    
    def get_level(self, weight):
        """获取记忆层次"""
        if weight > 0.7:
            return 'full'
        elif weight >= 0.3:
            return 'summary'
        elif weight >= 0.1:
            return 'tag'
        elif weight >= 0.03:
            return 'trace'
        else:
            return 'archive'
    
    def plot_decay_curve(self, max_days=10950, save_path='memory_decay_curve.svg'):
        """
        绘制记忆衰减曲线（静态图）
        
        Args:
            max_days: 最大天数
            save_path: 保存路径
        """
        # 创建图形
        fig, ax = plt.subplots(figsize=(14, 8), dpi=100)
        
        # 计算曲线
        days = np.linspace(0, max_days, 1000)
        weights = [self.calculate_weight(d) for d in days]
        
        # 绘制主曲线
        ax.plot(days, weights, linewidth=3, color='#1976D2', 
               label=f'衰减曲线 (α={self.alpha})', zorder=5)
        
        # 绘制五层背景色块
        y_positions = [1.0, 0.7, 0.3, 0.1, 0.03, 0.0]
        levels = ['full', 'summary', 'tag', 'trace', 'archive']
        
        for i, level in enumerate(levels):
            ax.fill_between(
                days, y_positions[i], y_positions[i+1],
                color=self.colors[level], alpha=0.15,
                label=f'{self.level_names[level]} (>{y_positions[i+1]:.2f})'
            )
        
        # 绘制阈值线
        for threshold_name, threshold_value in self.thresholds.items():
            if threshold_value > 0:
                ax.axhline(y=threshold_value, color=self.colors[threshold_name],
                          linestyle='--', linewidth=1.5, alpha=0.7)
        
        # 标注关键时间点（从1天到30年）
        key_days = [
            1,      # 1天
            7,      # 1周
            15,     # 半月
            30,     # 1月
            60,     # 2月
            180,    # 半年
            365,    # 1年
            730,    # 2年
            1095,   # 3年
            1825,   # 5年
            3650,   # 10年
            7300,   # 20年
            10950   # 30年
        ]
        
        # 时间标签映射
        time_labels = {
            1: '1天',
            7: '1周',
            15: '半月',
            30: '1月',
            60: '2月',
            180: '半年',
            365: '1年',
            730: '2年',
            1095: '3年',
            1825: '5年',
            3650: '10年',
            7300: '20年',
            10950: '30年'
        }
        
        for day in key_days:
            if day <= max_days:
                weight = self.calculate_weight(day)
                level = self.get_level(weight)
                
                # 绘制点
                ax.scatter([day], [weight], s=100, color=self.colors[level],
                          edgecolors='white', linewidths=2, zorder=10)
                
                # 添加注释
                time_label = time_labels.get(day, f'{day}天')
                
                # 计算注释位置（避免重叠）
                if day < 100:
                    xytext_offset = (10, 25)
                elif day < 1000:
                    xytext_offset = (-15, -35)
                else:
                    xytext_offset = (10, -35)
                
                ax.annotate(
                    f'{time_label}\n权重:{weight:.4f}\n{self.level_names[level]}',
                    xy=(day, weight),
                    xytext=xytext_offset,
                    textcoords='offset points',
                    fontsize=8,
                    bbox=dict(boxstyle='round,pad=0.4', fc=self.colors[level], alpha=0.25, edgecolor=self.colors[level]),
                    arrowprops=dict(arrowstyle='->', color=self.colors[level], lw=1.2, alpha=0.7)
                )
        
        # 设置坐标轴
        ax.set_xlabel('时间（天）', fontsize=14, fontweight='bold')
        ax.set_ylabel('记忆权重', fontsize=14, fontweight='bold')
        ax.set_title('记忆衰减曲线 - 五层架构', fontsize=16, fontweight='bold', pad=20)
        
        ax.set_xlim(0, max_days)
        ax.set_ylim(0, 1.05)
        
        # 网格
        ax.grid(True, linestyle=':', alpha=0.3)
        
        # 图例
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
        
        # 添加说明文本
        info_text = f'''记忆衰减公式: w(t) = 1 / (1 + {self.alpha} × t)

五层记忆架构（永不遗忘）：
• 完整记忆 (>0.7)   : 完整保留原文
• 摘要记忆 (0.3~0.7) : 摘要化
• 模糊标签 (0.1~0.3) : 模糊化标签
• 痕迹记忆 (0.03~0.1): 极低权重层级
• 存档记忆 (≤0.03)  : 永久存档，可回顾

关键时间点：1天→1周→1月→半年→1年→
            3年→5年→10年→20年→30年'''
        
        ax.text(0.02, 0.02, info_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='bottom',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # 紧凑布局
        plt.tight_layout()
        
        # 保存
        plt.savefig(save_path, format='svg', dpi=100, bbox_inches='tight')
        print(f"✓ 静态曲线图已保存: {save_path}")
        
        return fig, ax
    
    def plot_comparison(self, alphas=[0.005, 0.01, 0.02, 0.05], 
                       max_days=1000, save_path='memory_decay_comparison.svg'):
        """
        对比不同衰减系数的曲线
        
        Args:
            alphas: 衰减系数列表
            max_days: 最大天数
            save_path: 保存路径
        """
        fig, ax = plt.subplots(figsize=(14, 8), dpi=100)
        
        days = np.linspace(0, max_days, 1000)
        
        # 颜色映射
        cmap = plt.cm.viridis
        colors_list = [cmap(i/len(alphas)) for i in range(len(alphas))]
        
        # 绘制多条曲线
        for i, alpha in enumerate(alphas):
            weights = [1.0 / (1 + alpha * d) for d in days]
            ax.plot(days, weights, linewidth=2.5, color=colors_list[i],
                   label=f'α = {alpha} (100天后: {1/(1+alpha*100):.3f})',
                   alpha=0.8)
        
        # 绘制阈值线
        thresholds_plot = [0.7, 0.3, 0.1, 0.03]
        threshold_names = ['完整', '摘要', '标签', '痕迹']
        threshold_colors = ['#2E7D32', '#66BB6A', '#FFA726', '#EF5350']
        
        for i, (threshold, name) in enumerate(zip(thresholds_plot, threshold_names)):
            ax.axhline(y=threshold, color=threshold_colors[i],
                      linestyle='--', linewidth=1.5, alpha=0.5,
                      label=f'{name}阈值 ({threshold})')
        
        # 设置
        ax.set_xlabel('时间（天）', fontsize=14, fontweight='bold')
        ax.set_ylabel('记忆权重', fontsize=14, fontweight='bold')
        ax.set_title('不同衰减系数对比', fontsize=16, fontweight='bold', pad=20)
        
        ax.set_xlim(0, max_days)
        ax.set_ylim(0, 1.05)
        
        ax.grid(True, linestyle=':', alpha=0.3)
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9, ncol=2)
        
        plt.tight_layout()
        plt.savefig(save_path, format='svg', dpi=100, bbox_inches='tight')
        print(f"✓ 对比图已保存: {save_path}")
        
        return fig, ax
    
    def plot_level_timeline(self, max_days=10950, save_path='memory_level_timeline.svg'):
        """
        绘制记忆层次时间线
        
        Args:
            max_days: 最大天数
            save_path: 保存路径
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                        height_ratios=[2, 1], dpi=100)
        
        # ========== 上图：衰减曲线 ==========
        days = np.linspace(0, max_days, 1000)
        weights = [self.calculate_weight(d) for d in days]
        
        ax1.plot(days, weights, linewidth=3, color='#1976D2', label='衰减曲线')
        
        # 填充色块
        y_positions = [1.0, 0.7, 0.3, 0.1, 0.03, 0.0]
        levels = ['full', 'summary', 'tag', 'trace', 'archive']
        
        for i, level in enumerate(levels):
            ax1.fill_between(
                days, y_positions[i], y_positions[i+1],
                color=self.colors[level], alpha=0.2,
                label=self.level_names[level]
            )
        
        ax1.set_ylabel('记忆权重', fontsize=12, fontweight='bold')
        ax1.set_xlim(0, max_days)
        ax1.set_ylim(0, 1.05)
        ax1.grid(True, linestyle=':', alpha=0.3)
        ax1.legend(loc='upper right', fontsize=10)
        ax1.set_title('记忆衰减曲线与层次分布', fontsize=14, fontweight='bold')
        
        # ========== 下图：层次时间线 ==========
        # 计算每个层次的时间范围
        level_ranges = {
            'full': (0, None),
            'summary': (None, None),
            'tag': (None, None),
            'trace': (None, None),
            'archive': (None, None)
        }
        
        # 找到每个阈值对应的天数
        def find_days_for_weight(target_weight):
            """找到达到目标权重的天数"""
            if target_weight >= 1.0:
                return 0
            # w(t) = 1/(1+α*t) = target
            # 1+α*t = 1/target
            # t = (1/target - 1) / α
            return (1/target_weight - 1) / self.alpha
        
        threshold_days = {
            'full_end': find_days_for_weight(0.7),
            'summary_end': find_days_for_weight(0.3),
            'tag_end': find_days_for_weight(0.1),
            'trace_end': find_days_for_weight(0.03)
        }
        
        # 绘制时间线
        y_level = 0
        bar_height = 0.6
        levels_order = ['full', 'summary', 'tag', 'trace', 'archive']
        
        for i, level in enumerate(levels_order):
            if level == 'full':
                start, end = 0, threshold_days['full_end']
            elif level == 'summary':
                start, end = threshold_days['full_end'], threshold_days['summary_end']
            elif level == 'tag':
                start, end = threshold_days['summary_end'], threshold_days['tag_end']
            elif level == 'trace':
                start, end = threshold_days['tag_end'], threshold_days['trace_end']
            else:  # archive
                start, end = threshold_days['trace_end'], max_days
            
            # 绘制条形
            ax2.barh(i, end - start, left=start, height=bar_height,
                    color=self.colors[level], alpha=0.7,
                    edgecolor='white', linewidth=2)
            
            # 添加文本
            mid_point = (start + end) / 2
            duration_text = f'{end-start:.0f}天' if end - start < max_days else '持续...'
            ax2.text(mid_point, i, f'{self.level_names[level]}\n{duration_text}',
                    ha='center', va='center', fontsize=10, fontweight='bold',
                    color='white' if level in ['full', 'trace'] else 'black')
        
        # 设置
        ax2.set_yticks(range(len(levels_order)))
        ax2.set_yticklabels([self.level_names[l] for l in levels_order])
        ax2.set_xlabel('时间（天）', fontsize=12, fontweight='bold')
        ax2.set_xlim(0, max_days)
        ax2.set_title('各层次持续时间', fontsize=14, fontweight='bold')
        ax2.grid(True, axis='x', linestyle=':', alpha=0.3)
        
        # 添加关键时间点标记
        for name, day in threshold_days.items():
            ax2.axvline(x=day, color='red', linestyle='--', linewidth=1, alpha=0.5)
            ax2.text(day, len(levels_order), f'{day:.0f}天',
                    ha='center', va='bottom', fontsize=8, color='red')
        
        plt.tight_layout()
        plt.savefig(save_path, format='svg', dpi=100, bbox_inches='tight')
        print(f"✓ 时间线图已保存: {save_path}")
        
        return fig, (ax1, ax2)
    
    def create_interactive_html(self, max_days=10950, save_path='memory_decay_interactive.html'):
        """
        创建交互式HTML可视化（使用Plotly）
        
        Args:
            max_days: 最大天数
            save_path: 保存路径
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            print("⚠️  需要安装plotly: pip install plotly")
            return None
        
        # 计算数据
        days = np.linspace(0, max_days, 1000)
        weights = [self.calculate_weight(d) for d in days]
        levels = [self.get_level(w) for w in weights]
        
        # 创建图形
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=('记忆衰减曲线', '记忆层次分布'),
            vertical_spacing=0.12
        )
        
        # 主曲线
        fig.add_trace(
            go.Scatter(
                x=days, y=weights,
                mode='lines',
                name='衰减曲线',
                line=dict(color='#1976D2', width=3),
                hovertemplate='<b>天数:</b> %{x:.0f}<br><b>权重:</b> %{y:.3f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 添加阈值线和填充
        thresholds_data = [
            (0.7, '完整记忆', '#2E7D32'),
            (0.3, '摘要记忆', '#66BB6A'),
            (0.1, '模糊标签', '#FFA726'),
            (0.03, '痕迹记忆', '#EF5350')
        ]
        
        for threshold, name, color in thresholds_data:
            fig.add_hline(
                y=threshold, line_dash="dash", line_color=color,
                annotation_text=name, annotation_position="right",
                row=1, col=1
            )
        
        # 层次分布（饼图）
        level_counts = {}
        for level in levels:
            level_counts[level] = level_counts.get(level, 0) + 1
        
        fig.add_trace(
            go.Pie(
                labels=[self.level_names[l] for l in level_counts.keys()],
                values=list(level_counts.values()),
                marker=dict(colors=[self.colors[l] for l in level_counts.keys()]),
                hovertemplate='<b>%{label}</b><br>占比: %{percent}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title_text=f'记忆衰减曲线可视化 (α={self.alpha})',
            showlegend=True,
            height=800,
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="时间（天）", row=1, col=1)
        fig.update_yaxes(title_text="记忆权重", row=1, col=1)
        
        # 保存
        fig.write_html(save_path)
        print(f"✓ 交互式HTML已保存: {save_path}")
        
        return fig


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  记忆衰减曲线可视化工具")
    print("="*60 + "\n")
    
    # 创建输出目录
    output_dir = Path(__file__).parent.parent / 'visualizations'
    output_dir.mkdir(exist_ok=True)
    
    # 创建可视化器
    visualizer = MemoryDecayVisualizer(alpha=0.01)
    
    print("📊 生成可视化图表...\n")
    
    # 1. 基础衰减曲线（30年）
    print("1. 生成基础衰减曲线（30年时间跨度）...")
    visualizer.plot_decay_curve(
        max_days=10950,  # 30年
        save_path=str(output_dir / 'memory_decay_curve.svg')
    )
    
    # 2. 对比图（5年）
    print("\n2. 生成衰减系数对比图（5年时间跨度）...")
    visualizer.plot_comparison(
        alphas=[0.005, 0.01, 0.02, 0.05],
        max_days=1825,  # 5年
        save_path=str(output_dir / 'memory_decay_comparison.svg')
    )
    
    # 3. 时间线图（30年）
    print("\n3. 生成层次时间线图（30年时间跨度）...")
    visualizer.plot_level_timeline(
        max_days=10950,  # 30年
        save_path=str(output_dir / 'memory_level_timeline.svg')
    )
    
    # 4. 交互式HTML（30年）
    print("\n4. 生成交互式HTML（30年时间跨度）...")
    try:
        visualizer.create_interactive_html(
            max_days=10950,  # 30年
            save_path=str(output_dir / 'memory_decay_interactive.html')
        )
    except Exception as e:
        print(f"⚠️  跳过交互式HTML: {e}")
    
    print("\n" + "="*60)
    print("✅ 所有图表生成完成！")
    print("="*60)
    print(f"\n📁 输出目录: {output_dir}")
    print("\n生成的文件:")
    for file in output_dir.glob('*'):
        print(f"  • {file.name}")
    
    # 显示图表
    print("\n💡 提示: 使用浏览器打开SVG文件或HTML文件查看")
    
    # 可选：显示图表
    if '--show' in sys.argv:
        plt.show()


if __name__ == "__main__":
    main()
