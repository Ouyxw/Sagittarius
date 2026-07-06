# Phase 19: Visualization & Reporting API

## 📋 概述

Phase 19 为 Sagittarius 量子仿真平台添加了完整的可视化与报告 API，使用户能够轻松生成高质量的图表来分析仿真结果、寄存器几何结构和脉冲序列。

**实现状态**: ✅ P0 功能已完成  
**模块位置**: `sagittarius_py/sagittarius/viz/`  
**文档**: [详细实现文档](../../docs/phase19_visualization_implementation.md)

---

## ✨ 核心功能

### 1. 寄存器可视化 (`plot_register`)
- 绘制 2D 原子布局
- 显示阻塞半径内的相互作用边（UDG）
- 支持原子高亮（用于 MWIS 解展示）
- 自动添加原子索引标签

```python
from sagittarius import Register
from sagittarius.viz import plot_register

reg = Register.chain(5, spacing=5.0)
ax = plot_register(reg, blockade_radius=6.0, highlight_atoms=[0, 2, 4])
plt.savefig("register.png")
```

### 2. 脉冲波形可视化 (`plot_pulse_waveform`)
- 确定性采样 omega/delta 波形
- 支持全局和局部脉冲
- 自定义时间网格
- 双字段对比绘图

```python
from sagittarius import Pulse
from sagittarius.viz import plot_pulse_waveform

pulse = Pulse.global_(omega=lambda t: np.sin(t), delta=0.0, duration=10.0)
ax = plot_pulse_waveform(pulse, field='omega')
```

### 3. 可观测量轨迹 (`plot_observables`)
- 绘制期望值随时间演化
- 支持选择特定可观测量
- 自动从 DataFrame 提取数据

```python
result = sim.run()
ax = plot_observables(result, names=['pop0', 'pop1'])
```

### 4. 比特串分布 (`plot_bitstring_distribution`)
- 显示最终态概率直方图
- Top-K 过滤
- 支持按概率或比特串排序

```python
ax = plot_bitstring_distribution(result, top_k=8)
```

### 5. Shot 计数直方图 (`plot_shot_histogram`)
- 可视化量子采样结果
- 支持原始计数或归一化频率
- 显示总 shot 数元数据

```python
result.sample(shots=1000, seed=42)
ax = plot_shot_histogram(result, normalize=True)
```

### 6. 占据数热图 (`plot_population_heatmap`)
- 原子-时间 2D 热图
- 多种颜色映射选项
- 自动检测 population 列

```python
ax = plot_population_heatmap(result, cmap='plasma')
```

### 7. 综合摘要报告 (`plot_result_summary`)
- 一键生成 2x2 多面板图
- 包含可观测量、比特串、热图和元数据
- 容错处理（单个面板失败不影响其他）

```python
axes = plot_result_summary(result, show=True)
```

---

## 🚀 快速开始

### 安装依赖

```bash
cd sagittarius_py
uv sync
```

可视化依赖已包含在 `pyproject.toml` 中：
- `matplotlib >= 3.5.0`
- `pandas >= 1.4.0`
- `numpy >= 1.21.0`

### 运行示例脚本

```bash
# 生成所有示例图表到 ./viz_examples 目录
python examples_phase19_viz.py

# 保存到自定义目录
python examples_phase19_viz.py --output-dir ./my_plots

# 交互式显示（需要 GUI）
python examples_phase19_viz.py --show
```

### 运行验证测试

```bash
python test_viz_smoke.py
```

预期输出：
```
🎉 All smoke tests passed! Visualization module is ready.
```

---

## 📊 生成的图表示例

运行 `examples_phase19_viz.py` 将生成以下图表：

| 图表类型 | 文件名 | 说明 |
|---------|--------|------|
| 寄存器布局 | `register_chain.png` | 5 原子链式结构 |
| MWIS 高亮 | `register_mwis.png` | 金色高亮选中原子 |
| 相互作用图 | `interaction_graph.png` | 带距离标签的 UDG |
| 恒定脉冲 | `pulse_constant_omega.png` | Omega = 2.0 rad/μs |
| 高斯脉冲 | `pulse_gaussian_omega.png` | 包络调制的 Rabi 频率 |
| 线性扫描 | `pulse_linear_delta.png` | Delta 线性变化 |
| 双字段 | `pulse_both_fields.png` | Omega 和 Delta 对比 |
| 可观测量 | `result_observables.png` | 3 原子 population 动力学 |
| 比特串分布 | `result_bitstrings.png` | Top-8 最终态概率 |
| Shot 直方图 | `result_shots.png` | 500 shots 计数分布 |
| 归一化频率 | `result_shots_normalized.png` | 归一化到 [0,1] |
| 占据热图 | `result_heatmap.png` | Viridis  colormap |
| 替代热图 | `result_heatmap_coolwarm.png` | Coolwarm colormap |
| 综合报告 | `summary_report.png` | 2x2 多面板摘要 |
| 自定义组合 | `custom_multipanel.png` | 2x3 自定义布局 |

---

## 🎯 设计原则

### 1. 后端无关性 (Backend-Free)
所有可视化函数**不触发 Julia 初始化**，仅依赖纯 Python 库：
- ✅ matplotlib
- ✅ numpy
- ✅ pandas

这意味着你可以在没有 Julia 环境的情况下查看和分析已保存的结果。

### 2. 模块化架构
采用**数据提取**与**渲染**分离的设计：

```python
# 纯数据提取（无绘图）
values = sample_pulse_waveform(pulse, times, 'omega')

# 渲染层（可替换为其他后端）
ax = plot_pulse_waveform(pulse, time_grid=times, field='omega')
```

### 3. Matplotlib 集成
所有函数遵循统一的签名模式：
```python
def plot_xxx(..., ax: Optional[Axes] = None, ...) -> Axes:
    if ax is None:
        fig, ax = plt.subplots(...)
    # ... plotting logic ...
    return ax
```

**优势**：
- 支持多图组合
- 便于单元测试
- 允许用户进一步定制

### 4. 元数据感知
自动从 `SimulationResult` 提取关键信息：
- 原子数量
- 阻塞半径
- 求解器方法
- 种子值
- 基矢模式

并在图表标题或标签中显示，确保**可追溯性**。

### 5. 容错与诊断
所有函数提供清晰的错误信息：

```python
ValueError: No observable columns found. Available columns: ['time', 'other']. 
Ensure simulation includes Rydberg population observables.
```

---

## 📖 使用指南

### Jupyter Notebook 交互使用

```python
%matplotlib inline

from sagittarius.viz import *

# 直接显示
ax = plot_register(reg, blockade_radius=6.0)
plt.show()

# 链式定制
ax = plot_observables(result)
ax.set_title("Custom Title")
ax.set_ylim(-0.1, 1.1)
plt.show()
```

### 批量生成报告

```python
from pathlib import Path

output_dir = Path("reports/exp_001")
output_dir.mkdir(parents=True, exist_ok=True)

plot_register(reg).figure.savefig(output_dir / "register.png", dpi=150)
plot_observables(result).figure.savefig(output_dir / "obs.png", dpi=150)
plot_bitstring_distribution(result).figure.savefig(
    output_dir / "bits.png", dpi=150, bbox_inches='tight'
)
```

### 服务器/CI 环境

```python
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

# ... 绘图代码 ...
plt.savefig("plot.png")
plt.close('all')  # 释放内存
```

---

## 🧪 测试覆盖

### 烟雾测试 (Smoke Tests)
`test_viz_smoke.py` 验证：
- ✅ 所有模块可导入
- ✅ 寄存器绘图正常工作
- ✅ 脉冲波形采样正确
- ✅ 结果可视化无崩溃
- ✅ 错误处理提供 actionable 消息

运行测试：
```bash
python test_viz_smoke.py
```

### 完整测试套件（待实现）
计划创建 `sagittarius_py/tests/test_viz.py`，覆盖：
- 边界条件（空寄存器、单原子）
- 无效输入处理
- 后端无关性验证
- 图表元素数量检查
- 元数据完整性

---

## 🔮 未来扩展 (Roadmap)

### Phase 19 P1 功能（计划中）

| 功能 | 优先级 | 预计时间 |
|------|-------|---------|
| 关联矩阵热图 | Medium | 2-3 天 |
| 时间分辨空间快照 | Medium | 2 天 |
| Lindblad 诊断图 | Medium | 1-2 天 |
| 参数扫描可视化 | Medium | 3-4 天 |

### Phase 19 P2 功能（高级）

| 功能 | 优先级 | 说明 |
|------|-------|------|
| Benchmark 绘图助手 | Low | 消费 governed artifacts |
| 态矢量诊断 | Low | 小系统调试视图 |
| 图形导出侧车 JSON | Low | 保存图表元数据 |
| 动画就绪助手 | Low | 生成帧数据 |

---

## ❓ 常见问题

### Q: 为什么我的中文标签显示为方块？
**A**: Matplotlib 默认字体不支持中文。解决方法：
```python
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
```

### Q: 如何在 Jupyter 中实现交互式缩放？
**A**: 使用 `%matplotlib widget`：
```python
%matplotlib widget
ax = plot_observables(result)
# 现在可以鼠标缩放和平移
```

### Q: 保存的 PDF 文件太大怎么办？
**A**: 对热图使用 rasterized：
```python
ax = plot_population_heatmap(result)
ax.images[0].set_rasterized(True)
ax.figure.savefig("heatmap.pdf", dpi=300)
```

### Q: 绘图时出现 "Julia not initialized" 错误？
**A**: 这通常是因为 `Simulation.run()` 触发了后端初始化，而非绘图函数本身。确保先完成仿真运行，再调用 viz 函数。

---

## 📚 相关文档

- [详细实现文档](../../docs/phase19_visualization_implementation.md) - 完整的 API 参考和技术细节
- [REQUIREMENTS.md Phase 19](../../REQUIREMENTS.md#phase-19-visualization--reporting-api-planned) - 原始需求规格
- [Sagittarius README](../../README.md) - 项目总体介绍

---

## 📝 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-07-06 | P0 功能初始实现 |

---

## 👥 贡献者

- Sagittarius Development Team

---

**许可证**: MIT  
**最后更新**: 2026-07-06
