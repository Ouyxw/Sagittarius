# Phase 19: Visualization & Reporting API - Implementation Documentation

## 概述 (Overview)

本文档详细说明 Sagittarius Phase 19 可视化模块的实现情况，包括需求分析、代码实现、功能效果和使用示例。

**实现日期**: 2026-07-06  
**模块位置**: `sagittarius_py/sagittarius/viz/`  
**优先级**: P0 (基础可视化功能已完成)

---

## 1. 需求分析 (Requirements Analysis)

根据 [REQUIREMENTS.md](../../REQUIREMENTS.md) Phase 19 的定义，本阶段需要实现以下核心功能：

### 1.1 设计目标

| 目标 | 说明 |
|------|------|
| **后端无关性** | 所有绘图函数不得触发 Julia 初始化，仅依赖 matplotlib/numpy/pandas |
| **模块化架构** | 将数据提取与渲染分离，便于未来扩展其他绘图后端 |
| **元数据感知** | 自动从 SimulationResult 的 run_manifest 读取配置信息 |
| **Matplotlib 集成** | 所有函数接受可选 `ax` 参数，返回 Axes 对象供链式调用 |
| **可复现性** | 图表应包含足够的元数据（种子值、阻塞半径、原子数等） |

### 1.2 P0 功能清单

| 功能 | 状态 | 文件 |
|------|------|------|
| 寄存器布局可视化 | ✅ 完成 | `viz/register.py` |
| 相互作用图可视化 | ✅ 完成 | `viz/register.py` |
| 脉冲波形采样与绘图 | ✅ 完成 | `viz/pulse.py` |
| 可观测量轨迹绘图 | ✅ 完成 | `viz/result.py` |
| 比特串分布直方图 | ✅ 完成 | `viz/result.py` |
| Shot 计数直方图 | ✅ 完成 | `viz/result.py` |
| 占据数热图 | ✅ 完成 | `viz/result.py` |
| 综合结果摘要图 | ✅ 完成 | `viz/result.py` |

---

## 2. 代码实现详解 (Implementation Details)

### 2.1 模块结构

```
sagittarius/viz/
├── __init__.py      # 公共 API 导出
├── register.py      # 寄存器和几何可视化
├── pulse.py         # 脉冲波形可视化
└── result.py        # 仿真结果可视化
```

### 2.2 核心设计模式

#### 模式 1: Ax 注入模式
所有绘图函数遵循以下签名：
```python
def plot_xxx(..., ax: Optional[Axes] = None, ...) -> Axes:
    if ax is None:
        fig, ax = plt.subplots(...)
    # ... plotting logic ...
    return ax
```

**优势**:
- 用户可复用已有 Axes，实现多图组合
- 便于单元测试（传入 Mock Axes）
- 支持 Notebook 中的增量绘图

#### 模式 2: 数据提取与渲染分离
```python
# 纯数据提取（无绘图）
def sample_pulse_waveform(pulse_sequence, time_grid, field, atom_index) -> np.ndarray:
    ...

# 渲染层（调用提取器）
def plot_pulse_waveform(pulse_sequence, time_grid, field, atom_index, ax):
    y_values = sample_pulse_waveform(...)  # 复用提取逻辑
    ax.plot(time_grid, y_values)
    ...
```

**优势**:
- 提取器可独立测试
- 用户可直接获取数据进行自定义分析
- 未来添加 Plotly/Bokeh 后端时只需重写渲染层

#### 模式 3: 容错与诊断
所有函数在失败时提供 actionable 错误信息：
```python
if not pop_cols:
    raise ValueError(
        f"No population columns found. Available columns: {list(df.columns)}. "
        "Ensure simulation includes Rydberg population observables."
    )
```

---

## 3. 功能详细说明 (Feature Specifications)

### 3.1 寄存器可视化 (`plot_register`)

**文件**: `sagittarius/viz/register.py`

#### 功能描述
绘制 2D 原子布局，支持：
- 原子位置散点图
- 阻塞半径内的虚线连接（UDG 边）
- 原子索引标签（0-based）
- 高亮显示特定原子（用于 MWIS 结果展示）

#### 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `register` | Register | 必需 | Sagittarius 寄存器对象 |
| `blockade_radius` | float | None | 阻塞半径（μm），用于绘制边 |
| `edges` | bool | True | 是否绘制阻塞边 |
| `labels` | bool | True | 是否显示原子索引标签 |
| `ax` | Axes | None | Matplotlib axes，自动创建若为空 |
| `highlight_atoms` | List[int] | None | 需要高亮的原子索引列表 |
| `highlight_color` | str | 'red' | 高亮颜色 |
| `atom_size` | int | 100 | 原子标记大小（points） |

#### 返回值
- `matplotlib.axes.Axes`: 可用于进一步定制或保存

#### 使用示例
```python
from sagittarius import Register
from sagittarius.viz import plot_register
import matplotlib.pyplot as plt

# 创建链式寄存器
reg = Register.chain(5, spacing=5.0)

# 基础绘图
ax = plot_register(reg, blockade_radius=6.0)
plt.savefig("register.png", dpi=150)

# 高亮 MWIS 解
ax = plot_register(reg, blockade_radius=6.0, 
                  highlight_atoms=[0, 2, 4],
                  highlight_color='gold')
ax.set_title("MWIS Solution")
plt.show()
```

#### 实现细节
- **位置提取**: 通过 `_extract_positions()` 支持多种 Register 实现（`.positions` 数组或 `.atoms` 对象列表）
- **边绘制**: 双重循环计算所有原子对距离，若 ≤ blockade_radius 则绘制黑色虚线
- **高亮逻辑**: 验证索引范围，避免越界错误

---

### 3.2 脉冲波形可视化 (`plot_pulse_waveform`)

**文件**: `sagittarius/viz/pulse.py`

#### 功能描述
对 PulseSequence 的 omega/delta 字段进行确定性采样并绘制波形。支持：
- 全局脉冲（标量或 callable）
- 局部脉冲（向量或带 atom_index 的 callable）
- 自定义时间网格
- 双字段对比绘图（`plot_pulse_both_fields`）

#### 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `pulse_sequence` | PulseSequence | 必需 | 脉冲序列对象 |
| `time_grid` | np.ndarray | None | 显式时间点数组。若为 None 则从 `.duration` 自动生成 |
| `field` | str | 'omega' | 绘制的字段：'omega' 或 'delta' |
| `atom_index` | int | None | 局部寻址的原子索引（0-based） |
| `ax` | Axes | None | Matplotlib axes |
| `num_samples` | int | 200 | 自动生成时间网格时的采样点数 |

#### 返回值
- `matplotlib.axes.Axes`

#### 使用示例
```python
from sagittarius import Pulse
from sagittarius.viz import plot_pulse_waveform
import numpy as np

# 定义全局脉冲
pulse = Pulse.global_(
    omega=lambda t: 2.0 * np.sin(np.pi * t / 10),
    delta=lambda t: 1.0 - 0.1 * t,
    duration=10.0
)

# 绘制 Rabi 频率
ax = plot_pulse_waveform(pulse, field='omega')
ax.set_ylim(0, 2.5)
plt.savefig("omega_waveform.png")

# 绘制局部脉冲（原子 2）
ax = plot_pulse_waveform(pulse, field='omega', atom_index=2)

# 同时绘制 omega 和 delta
from sagittarius.viz.pulse import plot_pulse_both_fields
ax = plot_pulse_both_fields(pulse)
plt.legend()
plt.show()
```

#### 实现细节
- **采样逻辑**: `_sample_pulse_value()` 处理三种脉冲类型：
  1. **Callable**: 尝试 `f(t, atom_index)`，失败则回退到 `f(t)`
  2. **Array**: 返回第一个值作为常数（简化实现）
  3. **Scalar**: 直接转换为 float
- **时间网格**: 优先使用用户提供的 `time_grid`，否则从 `pulse.duration` 生成 linspace
- **填充效果**: 使用 `fill_between` 添加半透明填充，增强视觉效果

---

### 3.3 可观测量轨迹绘图 (`plot_observables`)

**文件**: `sagittarius/viz/result.py`

#### 功能描述
从 SimulationResult 提取时间序列数据，绘制可观量的期望值随时间的演化。

#### 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | SimulationResult | 必需 | 仿真结果对象 |
| `names` | List[str] | None | 要绘制的可观测量名称列表。None 则绘制所有非元数据列 |
| `ax` | Axes | None | Matplotlib axes |
| `show` | bool | False | 是否立即调用 plt.show() |
| `linewidth` | float | 2.0 | 曲线线宽 |

#### 返回值
- `matplotlib.axes.Axes`

#### 使用示例
```python
from sagittarius import Simulation, Register, Pulse
from sagittarius.viz import plot_observables

# 运行仿真
reg = Register.chain(3, spacing=5.0)
pulse = Pulse.global_(omega=2.0, delta=0.0, duration=5.0)
sim = Simulation(register=reg, pulse=pulse, observables={'pop0': 0, 'pop1': 1})
result = sim.run()

# 绘制所有可观测量
ax = plot_observables(result)

# 仅绘制特定原子
ax = plot_observables(result, names=['pop0', 'pop2'])
ax.set_ylim(-0.1, 1.1)
ax.set_title("Rydberg Population Dynamics")
plt.savefig("observables.png", dpi=150)
```

#### 实现细节
- **数据提取**: 调用 `result.to_pandas()` 获取 DataFrame
- **时间轴识别**: 依次检查 'time'、't' 列，最后使用 DataFrame index
- **列过滤**: 排除常见元数据列名（'time', 'timestamp', 'index'）
- **错误诊断**: 若指定的 `names` 不存在，列出所有可用列名

---

### 3.4 比特串分布直方图 (`plot_bitstring_distribution`)

**文件**: `sagittarius/viz/result.py`

#### 功能描述
绘制最终态比特串的概率分布，显示 top-K 最可能的量子态。

#### 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | SimulationResult | 必需 | 仿真结果对象 |
| `top_k` | int | 10 | 显示的最高概率比特串数量 |
| `ax` | Axes | None | Matplotlib axes |
| `sort_by` | str | 'probability' | 排序方式：'probability'（降序）或 'bitstring'（升序） |
| `show_values` | bool | True | 是否在柱状图上显示数值标签 |
| `bar_color` | str | 'steelblue' | 柱子颜色 |

#### 返回值
- `matplotlib.axes.Axes`

#### 使用示例
```python
result = sim.run()

# 基础用法
ax = plot_bitstring_distribution(result, top_k=8)
plt.xticks(rotation=45, ha='right')  # 旋转标签避免重叠
plt.tight_layout()
plt.savefig("bitstring_dist.png")

# 按比特串排序
ax = plot_bitstring_distribution(result, sort_by='bitstring', show_values=False)
```

#### 实现细节
- **数据源**: 调用 `result.final_bitstring_distribution()` 获取 dict
- **排序**: 使用 pandas Series 进行高效排序
- **截断**: 若唯一比特串数 > top_k，仅显示前 K 个，并在标题中注明总概率
- **数值标注**: 在每个柱子上方显示概率值（保留 3 位小数）

---

### 3.5 Shot 计数直方图 (`plot_shot_histogram`)

**文件**: `sagittarius/viz/result.py`

#### 功能描述
可视化量子采样结果，显示每个比特串被观测到的次数（或归一化频率）。

#### 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | SimulationResult | 必需 | 包含 `.samples` 属性的结果对象 |
| `ax` | Axes | None | Matplotlib axes |
| `top_k` | int | 20 | 显示的唯一比特串上限 |
| `normalize` | bool | False | 若为 True，将计数归一化为频率（总和=1） |
| `bar_color` | str | 'coral' | 柱子颜色 |

#### 返回值
- `matplotlib.axes.Axes`

#### 使用示例
```python
# 先进行采样
result = sim.run()
samples = result.sample(shots=1000, seed=42)

# 绘制原始计数
ax = plot_shot_histogram(result, top_k=15)
ax.set_title("Raw Shot Counts")

# 绘制归一化频率
ax = plot_shot_histogram(result, normalize=True, bar_color='lightgreen')
ax.set_ylabel("Frequency")
```

#### 实现细节
- **数据源**: `result.samples` 应为字符串数组（如 `['010', '101', ...]`）
- **计数**: 使用 `np.unique(samples, return_counts=True)` 高效统计
- **归一化**: 若 `normalize=True`，将 counts 除以 total_shots
- **剩余提示**: 若截断显示，在右下角添加文本框说明剩余 shot 数

---

### 3.6 占据数热图 (`plot_population_heatmap`)

**文件**: `sagittarius/viz/result.py`

#### 功能描述
创建 2D 热图，横轴为时间，纵轴为原子索引，颜色表示 Rydberg 占据数。

#### 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | SimulationResult | 必需 | 包含 population 数据的结果对象 |
| `ax` | Axes | None | Matplotlib axes |
| `cmap` | str | 'viridis' | Matplotlib colormap 名称 |
| `show_colorbar` | bool | True | 是否显示颜色条 |

#### 返回值
- `matplotlib.axes.Axes`

#### 使用示例
```python
result = sim.run()

# 基础热图
ax = plot_population_heatmap(result, cmap='plasma')
plt.colorbar(ax.collections[0], label='Population')
plt.savefig("population_heatmap.png", dpi=150)

# 自定义颜色映射
ax = plot_population_heatmap(result, cmap='coolwarm', show_colorbar=False)
```

#### 实现细节
- **列识别**: 查找以 'pop' 开头的列（pop0, pop1, ...）
- **矩阵转置**: `data_matrix.T` 使纵轴为原子，横轴为时间
- **extent 设置**: 使用实际时间值作为 x 轴范围
- **网格线**: 在原子之间添加白色分隔线，提升可读性

---

### 3.7 综合结果摘要 (`plot_result_summary`)

**文件**: `sagittarius/viz/result.py`

#### 功能描述
一键生成 2x2 多面板摘要图，包含：
1. 可观测量轨迹
2. 比特串分布
3. 占据数热图
4. 元数据文本摘要

#### 参数说明
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | SimulationResult | 必需 | 仿真结果对象 |
| `figsize` | tuple | (14, 10) | 图形尺寸（英寸） |
| `show` | bool | False | 是否立即显示 |

#### 返回值
- `List[Axes]`: 四个子图的 Axes 列表

#### 使用示例
```python
result = sim.run()
axes = plot_result_summary(result, show=True)

# 单独调整某个子图
axes[0].set_ylim(-0.1, 1.1)  # 调整 observable 轴范围
plt.savefig("summary.png", dpi=150, bbox_inches='tight')
```

#### 实现细节
- **容错处理**: 每个子图独立 try-except，失败时显示错误文本而非崩溃
- **元数据提取**: 从 `result.run_manifest` 和 `result.metadata` 读取关键信息
- **布局优化**: 使用 `plt.tight_layout()` 避免标签重叠

---

## 4. 验收标准对照 (Acceptance Criteria Mapping)

根据 REQUIREMENTS.md Phase 19 的验收标准，逐项说明实现情况：

| 验收标准 | 实现状态 | 对应函数/代码 |
|---------|---------|--------------|
| **AC1**: 无需 Julia 即可绘制 2D 寄存器布局 | ✅ 完成 | `plot_register()` 仅使用 numpy/matplotlib |
| **AC2**: 支持显式时间网格的脉冲波形采样 | ✅ 完成 | `sample_pulse_waveform()` + `plot_pulse_waveform()` |
| **AC3**: 可观测量绘图支持系列选择、ax 注入、返回 axes | ✅ 完成 | `plot_observables(names=..., ax=...) -> Axes` |
| **AC4**: 原子-时间占据数热图 | ✅ 完成 | `plot_population_heatmap()` 自动检测 pop 列 |
| **AC5**: 从 result 或 load_result() 绘制比特串概率直方图 | ✅ 完成 | `plot_bitstring_distribution()` 调用 `final_bitstring_distribution()` |
| **AC6**: 绘制 seeded shot 计数直方图 | ✅ 完成 | `plot_shot_histogram()` 处理 `result.samples` |
| **AC9**: 数据提取与绘图包装分离，返回可复用对象 | ✅ 完成 | `sample_pulse_waveform()` 为纯数据提取器 |
| **AC19**: 自动化测试使用非交互式 backend，覆盖 smoke rendering | ⏳ 待实现 | 需添加 `tests/test_viz.py` |

---

## 5. 使用指南 (Usage Guide)

### 5.1 快速开始

```python
import matplotlib
matplotlib.use('Agg')  # 非交互式后端（服务器/测试环境）

from sagittarius import Simulation, Register, Pulse
from sagittarius.viz import (
    plot_register,
    plot_pulse_waveform,
    plot_observables,
    plot_bitstring_distribution,
    plot_shot_histogram,
    plot_population_heatmap,
    plot_result_summary
)
import matplotlib.pyplot as plt

# 1. 创建并运行仿真
reg = Register.chain(4, spacing=5.0)
pulse = Pulse.global_(omega=2.0, delta=0.0, duration=5.0)
sim = Simulation(
    register=reg,
    pulse=pulse,
    observables={'pop0': 0, 'pop1': 1, 'pop2': 2, 'pop3': 3}
)
result = sim.run()

# 2. 采样
result.sample(shots=500, seed=123)

# 3. 可视化
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# 寄存器布局
plot_register(reg, blockade_radius=6.0, ax=axes[0, 0])

# 脉冲波形
plot_pulse_waveform(pulse, field='omega', ax=axes[0, 1])

# 可观测量
plot_observables(result, ax=axes[0, 2])

# 比特串分布
plot_bitstring_distribution(result, top_k=6, ax=axes[1, 0])
axes[1, 0].tick_params(axis='x', rotation=45)

# Shot 直方图
plot_shot_histogram(result, top_k=10, ax=axes[1, 1])
axes[1, 1].tick_params(axis='x', rotation=45)

# 占据数热图
plot_population_heatmap(result, ax=axes[1, 2])

plt.tight_layout()
plt.savefig("complete_workflow.png", dpi=150, bbox_inches='tight')
print("✅ 所有图表已保存到 complete_workflow.png")
```

### 5.2 Jupyter Notebook 交互使用

```python
%matplotlib inline

from sagittarius.viz import *

# 直接显示单个图表
ax = plot_register(reg, blockade_radius=6.0)
plt.show()

# 链式调用定制
ax = plot_observables(result)
ax.set_title("Custom Title")
ax.set_ylim(-0.1, 1.1)
ax.legend(loc='lower right')
plt.show()

# 综合摘要
plot_result_summary(result, show=True)
```

### 5.3 批量生成报告

```python
import os
from pathlib import Path

output_dir = Path("reports/experiment_001")
output_dir.mkdir(parents=True, exist_ok=True)

# 生成多个角度的图表
plot_register(reg, blockade_radius=6.0).figure.savefig(
    output_dir / "register.png", dpi=150
)

plot_pulse_waveform(pulse, field='omega').figure.savefig(
    output_dir / "pulse_omega.png", dpi=150
)

plot_observables(result).figure.savefig(
    output_dir / "observables.png", dpi=150
)

plot_bitstring_distribution(result).figure.savefig(
    output_dir / "bitstrings.png", dpi=150, bbox_inches='tight'
)

plot_population_heatmap(result).figure.savefig(
    output_dir / "heatmap.png", dpi=150
)

print(f"✅ 报告已生成到 {output_dir}")
```

---

## 6. 技术细节 (Technical Notes)

### 6.1 依赖管理

在 `sagittarius_py/pyproject.toml` 中添加可选依赖：

```toml
[project.optional-dependencies]
viz = [
    "matplotlib>=3.5.0",
    "pandas>=1.4.0",
    "numpy>=1.21.0",
]
```

安装命令：
```bash
pip install sagittarius[viz]
# 或
uv add matplotlib pandas
```

### 6.2 后端兼容性

| Matplotlib Backend | 适用场景 | 配置方法 |
|-------------------|---------|---------|
| `Agg` | 服务器、CI/CD、批量生成 | `matplotlib.use('Agg')` |
| `TkAgg` | 本地开发、交互式调试 | 默认（大多数 Linux） |
| `MacOSX` | macOS 原生窗口 | 自动检测 |
| `nbAgg` | Jupyter Notebook 交互 | `%matplotlib notebook` |

### 6.3 性能优化建议

1. **大数据集**: 对于 >1000 个时间点的 observable，使用 `linewidth=1` 减少渲染开销
2. **高分辨率**: 保存 PNG 时使用 `dpi=150` 或更高，SVG 用于论文出版
3. **内存管理**: 批量生成图表后调用 `plt.close('all')` 释放内存

### 6.4 已知限制

| 限制 | 说明 |  workaround |
|------|------|-----------|
| **3D 寄存器** | 当前仅支持 2D 布局 | 未来版本可添加 `plot_register_3d()` |
| **动画支持** | 未实现时间演化动画 | 可使用 `plot_population_heatmap` 作为静态替代 |
| **关联矩阵** | 未实现 pair-correlation 热图 | Phase 19 P1 功能，待后续开发 |
| **参数扫描** | 未实现 sweep 可视化 | 需等待 Phase 15 参数扫描 API 完成 |

---

## 7. 测试策略 (Testing Strategy)

### 7.1 单元测试框架

创建 `sagittarius_py/tests/test_viz.py`：

```python
import pytest
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

import matplotlib.pyplot as plt
import numpy as np
from sagittarius import Register, Pulse, Simulation
from sagittarius.viz import (
    plot_register,
    plot_pulse_waveform,
    plot_observables,
    plot_bitstring_distribution,
    plot_shot_histogram,
    plot_population_heatmap,
)


class TestRegisterVisualization:
    """测试寄存器可视化功能"""
    
    def test_plot_register_basic(self):
        """基础寄存器绘图测试"""
        reg = Register.chain(3, spacing=5.0)
        ax = plot_register(reg)
        
        assert ax is not None
        assert len(ax.collections) == 1  # scatter plot
        
        plt.close('all')
    
    def test_plot_register_with_blockade(self):
        """带阻塞边的寄存器绘图"""
        reg = Register.chain(3, spacing=5.0)
        ax = plot_register(reg, blockade_radius=6.0)
        
        # 应绘制 2 条边（0-1, 1-2）
        assert len(ax.lines) >= 2
        
        plt.close('all')
    
    def test_plot_register_highlight(self):
        """高亮原子测试"""
        reg = Register.chain(3, spacing=5.0)
        ax = plot_register(reg, highlight_atoms=[0, 2])
        
        # 检查颜色数组
        scatter = ax.collections[0]
        colors = scatter.get_facecolors()
        assert len(colors) == 3
        
        plt.close('all')
    
    def test_extract_positions_error(self):
        """无效寄存器对象的错误处理"""
        class FakeRegister:
            pass
        
        with pytest.raises(ValueError, match="Could not extract positions"):
            plot_register(FakeRegister())


class TestPulseVisualization:
    """测试脉冲波形可视化"""
    
    def test_plot_pulse_global(self):
        """全局脉冲绘图"""
        pulse = Pulse.global_(omega=2.0, delta=0.0, duration=5.0)
        ax = plot_pulse_waveform(pulse, field='omega')
        
        assert len(ax.lines) == 1
        line_data = ax.lines[0].get_ydata()
        assert np.allclose(line_data, 2.0)  # 恒定值
        
        plt.close('all')
    
    def test_plot_pulse_callable(self):
        """callable 脉冲绘图"""
        pulse = Pulse.global_(
            omega=lambda t: np.sin(t),
            delta=0.0,
            duration=10.0
        )
        ax = plot_pulse_waveform(pulse, field='omega', num_samples=100)
        
        line_data = ax.lines[0].get_ydata()
        assert len(line_data) == 100
        assert np.abs(line_data).max() <= 1.0  # sin 范围
        
        plt.close('all')
    
    def test_sample_pulse_waveform(self):
        """纯数据提取测试"""
        from sagittarius.viz.pulse import sample_pulse_waveform
        
        pulse = Pulse.global_(omega=3.0, delta=0.0, duration=5.0)
        times = np.linspace(0, 5, 50)
        values = sample_pulse_waveform(pulse, times, 'omega')
        
        assert values.shape == (50,)
        assert np.allclose(values, 3.0)


class TestResultVisualization:
    """测试结果可视化"""
    
    @pytest.fixture
    def simulation_result(self):
        """创建测试用的仿真结果"""
        reg = Register.chain(2, spacing=5.0)
        pulse = Pulse.global_(omega=2.0, delta=0.0, duration=3.0)
        sim = Simulation(
            register=reg,
            pulse=pulse,
            observables={'pop0': 0, 'pop1': 1}
        )
        result = sim.run()
        result.sample(shots=100, seed=42)
        return result
    
    def test_plot_observables(self, simulation_result):
        """可观测量轨迹绘图"""
        ax = plot_observables(simulation_result)
        
        assert len(ax.lines) == 2  # pop0, pop1
        assert ax.get_xlabel() == "Time (μs)"
        
        plt.close('all')
    
    def test_plot_observables_select_names(self, simulation_result):
        """选择特定可观测量"""
        ax = plot_observables(simulation_result, names=['pop0'])
        
        assert len(ax.lines) == 1
        
        plt.close('all')
    
    def test_plot_bitstring_distribution(self, simulation_result):
        """比特串分布绘图"""
        ax = plot_bitstring_distribution(simulation_result, top_k=5)
        
        assert len(ax.patches) > 0  # 有柱状图
        
        plt.close('all')
    
    def test_plot_shot_histogram(self, simulation_result):
        """Shot 直方图"""
        ax = plot_shot_histogram(simulation_result, top_k=10)
        
        assert len(ax.patches) > 0
        assert "Total shots: 100" in ax.get_title()
        
        plt.close('all')
    
    def test_plot_population_heatmap(self, simulation_result):
        """占据数热图"""
        ax = plot_population_heatmap(simulation_result)
        
        # 检查是否有 imshow 生成的图像
        assert len(ax.images) > 0
        
        plt.close('all')
    
    def test_missing_observables_error(self):
        """缺少可观测量列的错误处理"""
        class FakeResult:
            def to_pandas(self):
                import pandas as pd
                return pd.DataFrame({'time': [0, 1], 'other': [1, 2]})
        
        with pytest.raises(ValueError, match="No observable columns found"):
            plot_observables(FakeResult())
    
    def test_empty_samples_error(self):
        """空 samples 的错误处理"""
        class FakeResult:
            samples = np.array([])
        
        with pytest.raises(ValueError, match="Samples array is empty"):
            plot_shot_histogram(FakeResult())


class TestBackendFree:
    """验证后端无关性"""
    
    def test_no_julia_import_in_viz(self):
        """确保 viz 模块不导入 juliapkg"""
        import sys
        
        # 移除可能已导入的 julia 相关模块
        modules_to_check = [k for k in sys.modules.keys() if 'julia' in k.lower()]
        
        # 导入 viz 模块
        from sagittarius import viz
        
        # 检查是否新导入了 julia 模块
        new_julia_modules = [k for k in sys.modules.keys() 
                            if 'julia' in k.lower() and k not in modules_to_check]
        
        assert len(new_julia_modules) == 0, \
            f"viz 模块意外导入了 Julia 相关模块: {new_julia_modules}"
```

### 7.2 运行测试

```bash
cd sagittarius_py
uv run python -m pytest tests/test_viz.py -v
```

---

## 8. 未来扩展路线 (Roadmap)

### Phase 19 P1 功能（待实现）

| 功能 | 优先级 | 预计工作量 |
|------|-------|----------|
| 关联矩阵热图 (`plot_correlation_matrix`) | Medium | 2-3 天 |
| 时间分辨空间人口快照 (`plot_spatial_snapshot`) | Medium | 2 天 |
| 开放系统诊断图 (Lindblad trace/positivity) | Medium | 1-2 天 |
| 参数扫描热图 (`plot_sweep_heatmap`) | Medium | 3-4 天（依赖 Phase 15） |

### Phase 19 P2 功能（高级）

| 功能 | 优先级 | 说明 |
|------|-------|------|
| Benchmark 绘图助手 | Low | 消费 governed benchmark artifacts |
| 态矢量/密度矩阵诊断 | Low | 仅限小系统调试 |
| 图形导出侧车 JSON | Low | 保存图表元数据 |
| 动画就绪助手 | Low | 生成帧数据用于 animation |

---

## 9. 常见问题 (FAQ)

### Q1: 为什么我的图表中文标签显示为方块？
**A**: Matplotlib 默认字体不支持中文。解决方法：
```python
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
```

### Q2: 如何在 Jupyter 中实现交互式缩放？
**A**: 使用 `%matplotlib notebook` 或 `%matplotlib widget`：
```python
%matplotlib widget
ax = plot_observables(result)
# 现在可以使用鼠标缩放和平移
```

### Q3: 保存的 PDF 文件太大怎么办？
**A**: 简化路径或使用 rasterized 元素：
```python
ax = plot_population_heatmap(result)
ax.figure.savefig("heatmap.pdf", dpi=300, bbox_inches='tight')
# 或对热图使用 rasterized
im = ax.images[0]
im.set_rasterized(True)
```

### Q4: 如何自定义颜色映射？
**A**: 所有接受 `cmap` 参数的函数都支持 Matplotlib 内置 colormap：
```python
# 推荐 colormap
cmap_options = ['viridis', 'plasma', 'coolwarm', 'RdBu_r', 'YlOrRd']
ax = plot_population_heatmap(result, cmap='coolwarm')
```

### Q5: 绘图时出现 "Julia not initialized" 错误？
**A**: 这通常是因为 `Simulation.run()` 触发了后端初始化，而非绘图函数本身。确保：
1. 先完成仿真运行
2. 再调用 viz 函数（此时不再需要 Julia）

---

## 10. 总结 (Summary)

Phase 19 P0 可视化模块已成功实现，提供了一套完整、易用、后端无关的绘图工具。核心特点：

✅ **完全后端无关**: 所有函数仅依赖 matplotlib/numpy/pandas  
✅ **模块化设计**: 数据提取与渲染分离，便于扩展  
✅ **元数据感知**: 自动从结果中提取配置信息  
✅ **容错性强**: 提供清晰的错误诊断和修复建议  
✅ **易于集成**: 支持 Notebook、脚本、批量报告生成  

下一步工作：
1. 编写完整的单元测试套件（`test_viz.py`）
2. 在文档中添加可视化教程（`docs/getting-started/visualization.md`）
3. 根据用户反馈迭代 P1/P2 功能

---

**文档版本**: v1.0  
**最后更新**: 2026-07-06  
**维护者**: Sagittarius Development Team
