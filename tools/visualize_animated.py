#!/usr/bin/env python3
"""
动态记忆衰减曲线 - 1年期动画版
展示Mem0与人类记忆随时间的变化过程
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class AnimatedMemoryVisualizer:
    """动态记忆可视化器"""
    
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
        
        # 颜色配置
        self.colors = {
            'full': '#1B5E20',
            'summary': '#43A047',
            'tag': '#FF6F00',
            'trace': '#C62828',
            'archive': '#616161'
        }
        
        self.mem0_color = '#0D47A1'
        self.human_color = '#B71C1C'
    
    def mem0_decay(self, t):
        """Mem0记忆衰减"""
        return 1.0 / (1 + self.alpha * t)
    
    def human_decay(self, t):
        """人类遗忘曲线"""
        return np.exp(-0.05 * t)
    
    def get_level_name(self, weight):
        """获取记忆层次名称"""
        if weight > 0.7:
            return '完整记忆'
        elif weight >= 0.3:
            return '摘要记忆'
        elif weight >= 0.1:
            return '标签记忆'
        elif weight >= 0.03:
            return '痕迹记忆'
        else:
            return '归档记忆'
    
    def create_animation(self, max_days=365, duration=15, output_path=None):
        """
        创建动态图 - 1年期
        
        Args:
            max_days: 最大天数（365天）
            duration: 动画时长（秒）
            output_path: 输出路径
        """
        # 创建图形
        fig, (ax_main, ax_bar) = plt.subplots(1, 2, figsize=(22, 10), 
                                               gridspec_kw={'width_ratios': [3, 1]})
        
        # 生成完整数据
        all_days = np.linspace(0, max_days, 1000)
        all_mem0 = self.mem0_decay(all_days)
        all_human = self.human_decay(all_days)
        
        # 初始化主图
        ax_main.set_xlim(0, max_days)
        ax_main.set_ylim(0, 1.05)
        ax_main.set_xlabel('时间（天）', fontsize=18, fontweight='bold')
        ax_main.set_ylabel('记忆强度', fontsize=18, fontweight='bold')
        ax_main.set_title('记忆衰减动画 - Mem0 vs 人类记忆（1年）', 
                         fontsize=22, fontweight='bold', pad=20)
        ax_main.grid(True, alpha=0.4, linestyle='--', linewidth=1)
        ax_main.tick_params(axis='both', labelsize=14)
        
        # 绘制五层背景区域
        ax_main.fill_between(all_days, 0.7, 1.0, color=self.colors['full'], 
                            alpha=0.1, label='完整记忆区')
        ax_main.fill_between(all_days, 0.3, 0.7, color=self.colors['summary'], 
                            alpha=0.1, label='摘要记忆区')
        ax_main.fill_between(all_days, 0.1, 0.3, color=self.colors['tag'], 
                            alpha=0.1, label='标签记忆区')
        ax_main.fill_between(all_days, 0.03, 0.1, color=self.colors['trace'], 
                            alpha=0.1, label='痕迹记忆区')
        ax_main.fill_between(all_days, 0, 0.03, color=self.colors['archive'], 
                            alpha=0.1, label='归档记忆区')
        
        # 阈值线
        for value, color in [(0.7, self.colors['full']), (0.3, self.colors['summary']),
                             (0.1, self.colors['tag']), (0.03, self.colors['trace'])]:
            ax_main.axhline(y=value, color=color, linestyle=':', linewidth=2, alpha=0.5)
        
        # 初始化曲线（空的）
        line_mem0, = ax_main.plot([], [], color=self.mem0_color, linewidth=4, 
                                 label='Mem0记忆', alpha=0.9)
        line_human, = ax_main.plot([], [], color=self.human_color, linewidth=4, 
                                  label='人类记忆', linestyle='--', alpha=0.9)
        
        # 当前点标记
        point_mem0, = ax_main.plot([], [], 'o', color=self.mem0_color, 
                                  markersize=15, markeredgecolor='white', 
                                  markeredgewidth=2, zorder=10)
        point_human, = ax_main.plot([], [], 's', color=self.human_color, 
                                   markersize=15, markeredgecolor='white', 
                                   markeredgewidth=2, zorder=10)
        
        # 时间标签
        time_text = ax_main.text(0.02, 0.98, '', transform=ax_main.transAxes,
                                fontsize=20, fontweight='bold', verticalalignment='top',
                                bbox=dict(boxstyle='round,pad=0.7', facecolor='yellow', 
                                        edgecolor='orange', linewidth=2, alpha=0.9))
        
        # 数值标签
        value_text = ax_main.text(0.02, 0.88, '', transform=ax_main.transAxes,
                                 fontsize=16, fontweight='bold', verticalalignment='top',
                                 bbox=dict(boxstyle='round,pad=0.6', facecolor='lightblue', 
                                         alpha=0.85))
        
        # 图例
        ax_main.legend(loc='upper right', fontsize=13, framealpha=0.95, ncol=2)
        
        # 初始化柱状图
        ax_bar.set_xlim(0, 1)
        ax_bar.set_ylim(-0.5, 1.5)
        ax_bar.set_xticks([])
        ax_bar.set_yticks([0, 1])
        ax_bar.set_yticklabels(['人类记忆', 'Mem0记忆'], fontsize=16, fontweight='bold')
        ax_bar.set_title('实时对比', fontsize=18, fontweight='bold', pad=15)
        ax_bar.set_xlabel('记忆强度', fontsize=14, fontweight='bold')
        
        # 柱状图元素
        bar_mem0 = Rectangle((0, 0.8), 0, 0.15, facecolor=self.mem0_color, 
                            edgecolor='black', linewidth=2)
        bar_human = Rectangle((0, -0.05), 0, 0.15, facecolor=self.human_color, 
                             edgecolor='black', linewidth=2)
        ax_bar.add_patch(bar_mem0)
        ax_bar.add_patch(bar_human)
        
        # 柱状图数值标签
        bar_text_mem0 = ax_bar.text(0, 0.875, '', ha='left', va='center',
                                   fontsize=14, fontweight='bold', color='white')
        bar_text_human = ax_bar.text(0, 0.025, '', ha='left', va='center',
                                    fontsize=14, fontweight='bold', color='white')
        
        # 层次标签
        level_text_mem0 = ax_bar.text(0.5, 1.1, '', ha='center', va='bottom',
                                     fontsize=13, fontweight='bold', color=self.mem0_color)
        level_text_human = ax_bar.text(0.5, -0.3, '', ha='center', va='top',
                                      fontsize=13, fontweight='bold', color=self.human_color)
        
        # 动画帧数
        frames = int(duration * 30)  # 30 FPS
        
        def init():
            """初始化"""
            line_mem0.set_data([], [])
            line_human.set_data([], [])
            point_mem0.set_data([], [])
            point_human.set_data([], [])
            time_text.set_text('')
            value_text.set_text('')
            bar_mem0.set_width(0)
            bar_human.set_width(0)
            bar_text_mem0.set_text('')
            bar_text_human.set_text('')
            level_text_mem0.set_text('')
            level_text_human.set_text('')
            return (line_mem0, line_human, point_mem0, point_human, time_text, 
                   value_text, bar_mem0, bar_human, bar_text_mem0, bar_text_human,
                   level_text_mem0, level_text_human)
        
        def animate(frame):
            """动画更新函数"""
            # 计算当前天数（使用非线性进度，前期慢后期快）
            progress = frame / frames
            # 使用平方曲线使初期变化更明显
            current_day = max_days * (progress ** 1.5)
            
            # 获取当前索引
            idx = int((current_day / max_days) * len(all_days))
            idx = min(idx, len(all_days) - 1)
            
            # 更新曲线
            line_mem0.set_data(all_days[:idx+1], all_mem0[:idx+1])
            line_human.set_data(all_days[:idx+1], all_human[:idx+1])
            
            # 当前值
            mem0_val = all_mem0[idx]
            human_val = all_human[idx]
            
            # 更新点位置
            point_mem0.set_data([current_day], [mem0_val])
            point_human.set_data([current_day], [human_val])
            
            # 更新时间标签
            if current_day < 1:
                time_str = f'开始'
            elif current_day < 30:
                time_str = f'{int(current_day)}天'
            elif current_day < 365:
                time_str = f'{int(current_day/30)}月 ({int(current_day)}天)'
            else:
                time_str = f'1年 (365天)'
            
            time_text.set_text(f'时间: {time_str}')
            
            # 更新数值标签
            value_text.set_text(
                f'Mem0记忆: {mem0_val:.3f}\n'
                f'人类记忆: {human_val:.3f}\n'
                f'差距: {(mem0_val/human_val if human_val > 0.001 else 999):.1f}倍'
            )
            
            # 更新柱状图
            bar_mem0.set_width(mem0_val)
            bar_human.set_width(human_val)
            
            # 更新柱状图数值
            if mem0_val > 0.05:
                bar_text_mem0.set_text(f'  {mem0_val:.3f}')
                bar_text_mem0.set_position((mem0_val, 0.875))
            else:
                bar_text_mem0.set_text('')
            
            if human_val > 0.05:
                bar_text_human.set_text(f'  {human_val:.3f}')
                bar_text_human.set_position((human_val, 0.025))
            else:
                bar_text_human.set_text('')
            
            # 更新层次标签
            level_text_mem0.set_text(f'Mem0: {self.get_level_name(mem0_val)}')
            level_text_human.set_text(f'人类: {self.get_level_name(human_val)}')
            
            return (line_mem0, line_human, point_mem0, point_human, time_text, 
                   value_text, bar_mem0, bar_human, bar_text_mem0, bar_text_human,
                   level_text_mem0, level_text_human)
        
        # 创建动画
        anim = animation.FuncAnimation(fig, animate, init_func=init,
                                      frames=frames, interval=1000/30,
                                      blit=True, repeat=True)
        
        plt.tight_layout()
        
        # 保存
        if output_path is None:
            output_path = os.path.join('..', 'visualizations', 'memory_decay_animated.gif')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"正在生成动画（{duration}秒，{frames}帧）...")
        print("这可能需要1-2分钟，请耐心等待...")
        
        # 保存为GIF
        anim.save(output_path, writer='pillow', fps=30, dpi=100)
        
        plt.close()
        
        return os.path.abspath(output_path)
    
    def create_html_animation(self, max_days=365, output_path=None):
        """
        创建HTML5交互式动画
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # 生成数据
        days = np.linspace(0, max_days, 1000)
        mem0_weights = self.mem0_decay(days)
        human_weights = self.human_decay(days)
        
        # 创建子图
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.7, 0.3],
            subplot_titles=('记忆衰减曲线（1年）', '实时对比'),
            specs=[[{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # 主曲线图
        fig.add_trace(
            go.Scatter(x=days, y=mem0_weights, mode='lines',
                      name='Mem0记忆', line=dict(color=self.mem0_color, width=4)),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=days, y=human_weights, mode='lines',
                      name='人类记忆', line=dict(color=self.human_color, width=4, dash='dash')),
            row=1, col=1
        )
        
        # 添加阈值线
        for name, value in [('完整', 0.7), ('摘要', 0.3), ('标签', 0.1), ('痕迹', 0.03)]:
            fig.add_hline(y=value, line_dash="dot", line_color="gray", 
                         opacity=0.5, row=1, col=1)
        
        # 创建动画帧
        frames = []
        steps = 100
        
        for i in range(steps):
            idx = int((i / steps) * len(days))
            current_day = days[idx]
            mem0_val = mem0_weights[idx]
            human_val = human_weights[idx]
            
            frame_data = [
                go.Scatter(x=days[:idx+1], y=mem0_weights[:idx+1]),
                go.Scatter(x=days[:idx+1], y=human_weights[:idx+1]),
                go.Bar(x=[mem0_val, human_val], y=['Mem0', '人类'], 
                      orientation='h', marker=dict(color=[self.mem0_color, self.human_color]))
            ]
            
            frames.append(go.Frame(data=frame_data, name=str(i)))
        
        fig.frames = frames
        
        # 添加播放按钮
        fig.update_layout(
            updatemenus=[{
                'type': 'buttons',
                'showactive': False,
                'buttons': [
                    {'label': '播放', 'method': 'animate',
                     'args': [None, {'frame': {'duration': 50, 'redraw': True},
                                    'fromcurrent': True}]},
                    {'label': '暂停', 'method': 'animate',
                     'args': [[None], {'frame': {'duration': 0, 'redraw': False},
                                      'mode': 'immediate'}]}
                ]
            }],
            height=600,
            title_text="Mem0 vs 人类记忆 - 动态对比",
            title_font_size=24
        )
        
        fig.update_xaxes(title_text="时间（天）", row=1, col=1)
        fig.update_yaxes(title_text="记忆强度", row=1, col=1)
        fig.update_xaxes(title_text="记忆强度", row=1, col=2)
        
        if output_path is None:
            output_path = os.path.join('..', 'visualizations', 'memory_decay_interactive.html')
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.write_html(output_path)
        
        return os.path.abspath(output_path)


def main():
    """主函数"""
    print("=" * 70)
    print("  动态记忆衰减曲线生成器")
    print("  1年期 Mem0 vs 人类记忆动画")
    print("=" * 70)
    print()
    
    visualizer = AnimatedMemoryVisualizer()
    
    print("📊 生成动态可视化...")
    print()
    
    # GIF动画
    print("1. 生成GIF动画（15秒）...")
    try:
        path1 = visualizer.create_animation(duration=15)
        print(f"✓ GIF动画已保存: {path1}")
    except Exception as e:
        print(f"✗ GIF生成失败: {e}")
        print("  提示: 需要安装pillow库")
    print()
    
    # HTML交互式动画
    print("2. 生成HTML交互式动画...")
    try:
        path2 = visualizer.create_html_animation()
        print(f"✓ HTML动画已保存: {path2}")
    except Exception as e:
        print(f"✗ HTML生成失败: {e}")
        print("  提示: 需要安装plotly库")
    print()
    
    print("=" * 70)
    print("✅ 动画生成完成！")
    print("=" * 70)
    print()
    print("💡 使用说明:")
    print("  • GIF动画: 直接查看或插入文档")
    print("  • HTML动画: 浏览器打开，支持播放/暂停控制")
    print("  • 动画展示1年内记忆衰减过程")
    print("  • 实时显示Mem0与人类记忆的对比")


if __name__ == '__main__':
    main()
