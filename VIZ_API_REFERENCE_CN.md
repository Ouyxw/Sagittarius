# Sagittarius 可视化 API 参考文档

> **`sagittarius.viz` 模块所有可视化函数的完整 API 文档**

---

## 📋 快速查阅卡片

### 核心可视化功能 (需求 1-6)

| 函数 | 模块 | 功能 | 返回值 |
|------|------|------|--------|
| [`plot_register()`](#plot_register) | `viz.register` | 2D寄存器布局,含原子、阻塞圆盘、相互作用边 | `Axes` |
| [`plot_interaction_graph()`](#plot_interaction_graph) | `viz.register` | 单位圆盘图,含距离标注和邻接矩阵 | `Axes` |
| [`plot_pulse_waveform()`](#plot_pulse_waveform) | `viz.pulse` | Ω或Δ脉冲波形采样绘图 | `Axes` |
| [`plot_pulse_both_fields()`](#plot_pulse_both_fields) | `viz.pulse` | 双轴同时绘制Ω和Δ场 | `Axes` |
| [`sample_pulse_waveform()`](#sample_pulse_waveform) | `viz.pulse` | 在时间网格上采样脉冲值(仅数据) | `np.ndarray` |
| [`plot_observables()`](#plot_observables) | `viz.result` | 可观测量轨迹随时间变化 | `Axes` |
| [`plot_bitstring_distribution()`](#plot_bitstring_distribution) | `viz.result` | 末态比特串概率直方图 | `Axes` |
| [`plot_shot_histogram()`](#plot_shot_histogram) | `viz.result` | 测量次数分布直方图 | `Axes` |
| [`plot_population_heatmap()`](#plot_population_heatmap) | `viz.result` | 原子×时间布居热图 | `Axes` |

### 诊断与分析 (需求 7-14)

| 函数 | 模块 | 功能 | 返回值 |
|------|------|------|--------|
| [`generate_basis_diagnostics()`](#generate_basis_diagnostics) | `viz.basis_diagnostics` | 生成约化基诊断数据 | `Dict` |
| [`plot_basis_space_diagram()`](#plot_basis_space_diagram) | `viz.basis_diagnostics` | 可视化基空间剪枝 | `Axes` |
| [`plot_bitstring_space_grid()`](#plot_bitstring_space_grid) | `viz.basis_diagnostics` | 有效/禁戒比特串网格视图 | `Axes` |
| [`plot_blockade_constraint_graph()`](#plot_blockade_constraint_graph) | `viz.basis_diagnostics` | 阻塞约束网络图 | `Axes` |
| [`plot_comprehensive_basis_diagnostics()`](#plot_comprehensive_basis_diagnostics) | `viz.basis_diagnostics` | 多面板综合基诊断 | `Figure` |
| [`extract_geometry_diagnostics()`](#extract_geometry_diagnostics) | `viz.geometry_diagnostics` | 提取几何诊断数据 | `Dict` |
| [`plot_geometry_diagnostics()`](#plot_geometry_diagnostics) | `viz.geometry_diagnostics` | 距离/VDW/邻接热力图 | `Axes` |
| [`plot_unit_disk_graph()`](#plot_unit_disk_graph) | `viz.geometry_diagnostics` | 单位圆盘图可视化 | `Axes` |
| [`plot_mwis_problem()`](#plot_mwis_problem) | `viz.mwis_viz` | MWIS问题含冲突标记 | `Axes` |
| [`plot_pair_correlation_matrix()`](#plot_pair_correlation_matrix) | `viz.correlation_viz` | 成对关联⟨nᵢnⱼ⟩热力图 | `Axes` |
| [`plot_connected_correlation_matrix()`](#plot_connected_correlation_matrix) | `viz.correlation_viz` | 连通关联Cᵢⱼ热力图 | `Axes` |
| [`plot_pauli_zz_matrix()`](#plot_pauli_zz_matrix) | `viz.correlation_viz` | Pauli-ZZ关联⟨σᶻᵢσᶻⱼ⟩ | `Axes` |
| [`plot_blockade_conflict_heatmap()`](#plot_blockade_conflict_heatmap) | `viz.correlation_viz` | 阻塞冲突结构热力图 | `Axes` |
| [`extract_spatial_snapshot()`](#extract_spatial_snapshot) | `viz.spatial_snapshot` | 提取单帧空间数据 | `Dict` |
| [`extract_frame_sequence()`](#extract_frame_sequence) | `viz.spatial_snapshot` | 提取多帧序列 | `List[Dict]` |
| [`plot_spatial_snapshot()`](#plot_spatial_snapshot) | `viz.spatial_snapshot` | 单帧空间布居快照 | `Axes` |
| [`plot_multi_panel_snapshots()`](#plot_multi_panel_snapshots) | `viz.spatial_snapshot` | 多面板帧对比 | `Axes` |
| [`plot_time_grid_diagnostics()`](#plot_time_grid_diagnostics) | `viz.diagnostics` | 时间网格采样分析 | `Axes` |
| [`plot_lindblad_validation()`](#plot_lindblad_validation) | `viz.diagnostics` | Lindblad迹/正定性验证 | `Axes` |
| [`plot_mcwf_vs_lindblad()`](#plot_mcwf_vs_lindblad) | `viz.diagnostics` | MCWF与Lindblad对比 | `Axes` |
| [`plot_trajectory_statistics()`](#plot_trajectory_statistics) | `viz.diagnostics` | 轨迹均值±σ置信区间 | `Axes` |

### 基准测试与调试 (需求 15-17)

| 函数 | 模块 | 功能 | 返回值 |
|------|------|------|--------|
| [`plot_runtime_scaling()`](#plot_runtime_scaling) | `viz.benchmark_perf` | 运行时随原子数缩放曲线 | `Axes` |
| [`plot_memory_scaling()`](#plot_memory_scaling) | `viz.benchmark_perf` | 内存使用缩放曲线 | `Axes` |
| [`plot_solver_comparison()`](#plot_solver_comparison) | `viz.benchmark_perf` | 多求解器性能对比 | `Axes` |
| [`plot_success_failure_summary()`](#plot_success_failure_summary) | `viz.benchmark_perf` | 成功/失败率摘要 | `Axes` |
| [`plot_cpu_gpu_error_comparison()`](#plot_cpu_gpu_error_comparison) | `viz.benchmark_perf` | CPU与GPU误差对比 | `Axes` |
| [`plot_state_probabilities()`](#plot_state_probabilities) | `viz.small_system_debug` | 态矢量\|ψᵢ\|²柱状图 | `Axes` |
| [`plot_density_matrix_diagonal()`](#plot_density_matrix_diagonal) | `viz.small_system_debug` | 密度矩阵对角元 | `Axes` |
| [`plot_density_matrix_magnitude()`](#plot_density_matrix_magnitude) | `viz.small_system_debug` | 密度矩阵模值热力图 | `Axes` |
| [`plot_density_matrix_phase()`](#plot_density_matrix_phase) | `viz.small_system_debug` | 密度矩阵相位热力图 | `Axes` |

### 导出与报告 (需求 18-20)

| 函数 | 模块 | 功能 | 返回值 |
|------|------|------|--------|
| [`export_figure()`](#export_figure) | `viz.export` | 导出图表+元数据JSON | `None` |
| [`export_from_result()`](#export_from_result) | `viz.export` | 从Result对象一键导出 | `None` |
| [`ReportGenerator`](#reportgenerator) | `viz.report` | 生成HTML/Markdown报告 | `ReportGenerator` |
| [`generate_quick_report()`](#generate_quick_report) | `viz.report` | 快速报告生成助手 | `str` (文件路径) |
| [`plot_sweep_heatmap()`](#plot_sweep_heatmap) | `viz.sweep` | 2D参数扫描热力图,带失败运行标记 | `Axes` |
| [`plot_sweep_line_slice()`](#plot_sweep_line_slice) | `viz.sweep` | 多维扫描数据的1D切片提取 | `Axes` |
| [`plot_final_observable_map()`](#plot_final_observable_map) | `viz.sweep` | 最终可观测量值随参数变化图 | `Axes` |
| [`plot_failed_run_mask()`](#plot_failed_run_mask) | `viz.sweep` | 成功/失败二元掩码可视化 | `Axes` |
| [`extract_sweep_summary()`](#extract_sweep_summary) | `viz.sweep` | 统计摘要提取 | `Dict` |
| [`generate_synthetic_sweep_data()`](#generate_synthetic_sweep_data) | `viz.sweep` | 用于测试的合成数据生成器 | `Dict` |

---

## 🔍 详细 API 文档

### `plot_register()`

**模块**: `sagittarius.viz.register`

**功能**: 绘制2D寄存器布局,可选显示阻塞圆盘、相互作用边和原子标签。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | Register对象或(x, y)坐标列表(单位:μm) |
| `blockade_radius` | `float` | ❌ 可选 | `None` | 阻塞半径R_b(单位:μm)。如提供,则绘制阻塞圆盘和相互作用边 |
| `show_blockade_disks` | `bool` | ❌ 可选 | `False` | 是否绘制每个原子周围的半透明阻塞圆盘 |
| `edges` | `bool` | ❌ 可选 | `True` | 是否绘制阻塞半径内原子之间的边 |
| `labels` | `bool` | ❌ 可选 | `True` | 是否显示原子索引标签 |
| `bitstring` | `str` | ❌ 可选 | `None` | 二进制字符串(如"0101"),用于按状态着色原子('1'=里德堡态,'0'=基态) |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴。如为None则创建新的 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸(宽,高),单位:英寸 |
| `disk_alpha` | `float` | ❌ 可选 | `0.15` | 阻塞圆盘透明度(0=完全透明,1=完全不透明) |
| `edge_color` | `str` | ❌ 可选 | `'gray'` | 相互作用边的颜色 |
| `atom_size` | `float` | ❌ 可选 | `100` | 原子散点的大小,单位:points² |

#### 返回值

- **类型**: `matplotlib.axes.Axes`
- **描述**: 包含绘图的matplotlib Axes对象

#### 示例

```python
from sagittarius.viz import plot_register
from sagittarius import Register

# 方法1: 使用Register对象
reg = Register([(0, 0), (5, 0), (2.5, 4.33)])
ax = plot_register(reg, blockade_radius=6.0, show_blockade_disks=True)

# 方法2: 直接使用坐标列表
coords = [(0, 0), (5, 0), (2.5, 4.33)]
ax = plot_register(coords, blockade_radius=6.0, bitstring="101")

# 方法3: 在现有坐标轴上绘制
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
plot_register(reg, ax=ax, labels=False)
```

---

### `plot_interaction_graph()`

**模块**: `sagittarius.viz.register`

**功能**: 可视化单位圆盘图,含距离标注和邻接矩阵。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | Register对象或坐标列表 |
| `blockade_radius` | `float` | ✅ 是 | - | 用于边检测的阻塞半径R_b(单位:μm) |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_distances` | `bool` | ❌ 可选 | `False` | 是否在边上标注距离值 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_interaction_graph

reg = Register([(0, 0), (5, 0), (2.5, 4.33)])
ax = plot_interaction_graph(reg, blockade_radius=6.0, show_distances=True)
```

---
### `plot_pulse_waveform()`

**模块**: `sagittarius.viz.pulse`

**功能**: 绘制Ω(Rabi频率)或Δ(失谐)脉冲波形随时间的变化。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `pulse_sequence` | 多种格式 | ✅ 是 | - | 脉冲定义。**支持10+种格式**:<br>• **AST节点(7种)**: `Constant`, `Ramp`, `Gaussian`, `Blackman`, `Sinc`, `SinSquared`, `Piecewise`<br>• **寻址包装器(3种)**: `GlobalPulse`, `LocalPulseVector`, `CallablePulse`<br>• **字典格式**: `{'type': 'constant', ...}`, `{'type': 'gaussian', ...}`等<br>• **可调用函数**: `f(t)` 或 `f(t, atom_index)` 返回标量或数组<br>• **标量**: 单个数值(视为恒定脉冲)<br>• **带属性的对象**: 具有`.omega`/`.delta`字段的对象 |
| `time_grid` | `np.ndarray` | ❌ 可选 | `None` | 采样的时间网格。如为None则从脉冲持续时间自动生成 |
| `field` | `str` | ❌ 可选 | `'omega'` | 要绘制的场:'omega'(Ω)或'delta'(Δ)。对于字典/AST输入会被忽略 |
| `atom_index` | `int` | ❌ 可选 | `None` | 局域寻址的原子索引(从0开始)。None表示全局脉冲 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `num_samples` | `int` | ❌ 可选 | `200` | 如果time_grid是自动生成的，采样点数量 |
| `title` | `str` | ❌ 可选 | `None` | 自定义图表标题。如为None则自动生成 |

#### 返回值

- **类型**: `Tuple[matplotlib.axes.Axes, np.ndarray]`
- **结构**: `(ax, y_values)`，其中 `y_values` 的形状为 `(len(time_grid),)`

#### 支持的脉冲格式(详细说明)

**1. AST节点类型(通过`Pulse`工厂的7种形状)**:
```python
from sagittarius import Pulse

# 恒定脉冲
pulse = Pulse.constant(value=5.0, duration=1.0)

# Ramp脉冲(线性扫描)
pulse = Pulse.ramp(start=-5.0, end=5.0, duration=1.0)

# 高斯脉冲
pulse = Pulse.gaussian(amplitude=10.0, sigma=0.1, duration=1.0)

# Blackman窗脉冲
pulse = Pulse.blackman(amplitude=10.0, duration=1.0)

# Sinc函数脉冲
pulse = Pulse.sinc(amplitude=10.0, width=0.2, duration=1.0)

# Sin-squared脉冲
pulse = Pulse.sin_squared(amplitude=10.0, duration=1.0)

# Piecewise(顺序组合)
p1 = Pulse.constant(5.0, duration=0.5)
p2 = Pulse.ramp(5.0, 0.0, duration=0.5)
pulse = Pulse.piecewise([p1, p2])
```

**2. 寻址包装器(3种类型)**:
```python
# GlobalPulse - 所有原子使用相同值
pulse = Pulse.global_(5.0)

# LocalPulseVector - 每原子值
pulse = Pulse.local([5.0, 10.0, 0.0])      # 密集列表格式
pulse = Pulse.local({0: 5.0, 2: 10.0})     # 稀疏字典格式

# CallablePulse - 自定义函数
def my_func(t):
    return [5.0 * np.sin(2*np.pi*t)] * 3   # 返回3个原子的数组
pulse = Pulse.callable(my_func)
```

**3. 字典格式(直接字典表示)**:
```python
# 恒定
pulse = {'type': 'constant', 'value': 5.0}

# Ramp
pulse = {'type': 'ramp', 'start_val': -5.0, 'end_val': 5.0, 'duration': 1.0}

# 高斯
pulse = {
    'type': 'gaussian',
    'amplitude': 10.0,
    'sigma': 0.1,
    'duration': 1.0,
    'mu': 0.5  # 可选，默认为duration/2
}

# Blackman
pulse = {'type': 'blackman', 'amplitude': 10.0, 'duration': 1.0}

# Sinc
pulse = {'type': 'sinc', 'amplitude': 10.0, 'width': 0.2, 'duration': 1.0}

# Sin-squared
pulse = {'type': 'sin_squared', 'amplitude': 10.0, 'duration': 1.0}

# Piecewise
pulse = {
    'type': 'piecewise',
    'pulses': [
        {'type': 'constant', 'value': 5.0, 'duration': 0.5},
        {'type': 'ramp', 'start_val': 5.0, 'end_val': 0.0, 'duration': 0.5}
    ]
}
```

**4. 可调用函数**:
```python
import numpy as np

# 标量输出(全局脉冲)
pulse = lambda t: 5.0 * np.sin(2 * np.pi * t)

# 数组输出(每原子脉冲)
def multi_atom_pulse(t):
    return np.array([5.0, 10.0, 0.0]) * np.sin(2 * np.pi * t)

# 带atom_index参数的函数
def local_pulse(t, idx):
    return (5.0 + idx) * np.exp(-t)
```

**5. 标量常量**:
```python
# 视为恒定脉冲
pulse = 5.0  # 等价于 Constant(5.0)
```

#### 异常

- `ValueError`: 如果脉冲类型无法处理或time_grid无效
- `UserWarning`: 如果遇到不支持的AST节点类型(返回0.0)

#### 示例

```python
from sagittarius.viz import plot_pulse_waveform
from sagittarius import Pulse
import numpy as np

# 方法1: AST节点
pulse = Pulse.gaussian(10.0, sigma=0.1, duration=1.0)
ax, omega_vals = plot_pulse_waveform(pulse, field='omega')

# 方法2: 字典格式
pulse = {'type': 'constant', 'value': 5.0}
ax, delta_vals = plot_pulse_waveform(pulse, field='delta')

# 方法3: 带局域寻址
pulse = Pulse.local({0: 10.0, 1: 5.0, 2: 0.0})
ax, vals = plot_pulse_waveform(pulse, atom_index=0, field='omega')

# 方法4: 可调用函数
def my_pulse(t):
    return 5.0 * np.sin(2 * np.pi * t)
ax, vals = plot_pulse_waveform(my_pulse)

# 方法5: 自定义时间网格
times = np.linspace(0, 1.0, 500)
ax, vals = plot_pulse_waveform(pulse, time_grid=times)

# 方法6: 同时获取坐标轴和值
ax, y_values = yplot_pulse_waveform(Pulse.constant(5.0, duration=1.0))
print(y_values.shape)  # (200,) - 与num_samples匹配
```

---
### `plot_pulse_both_fields()`

**模块**: `sagittarius.viz.pulse`

**功能**: 在双y轴上同时绘制Ω和Δ两个场。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `pulse` | `Pulse`、`Dict` 或 `callable` | ✅ 是 | - | 脉冲定义 |
| `t_grid` | `np.ndarray` | ❌ 可选 | `None` | 采样的时间网格 |
| `atom_index` | `int` | ❌ 可选 | `None` | 局域寻址的原子索引 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 主坐标轴(左y轴用于Ω) |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 5)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `Tuple[matplotlib.axes.Axes, matplotlib.axes.Axes]` - (ax_omega, ax_delta)

#### 示例

```python
from sagittarius.viz import plot_pulse_both_fields

pulse = {
    'omega': {'type': 'gaussian', 'amplitude': 10.0, 'center': 0.5, 'sigma': 0.1},
    'delta': {'type': 'ramp', 'start_val': -5.0, 'end_val': 5.0}
}
ax_omega, ax_delta = plot_pulse_both_fields(pulse)
```

---

### `sample_pulse_waveform()`

**模块**: `sagittarius.viz.pulse`

**功能**: 在时间网格上采样脉冲值,不进行绘图(仅数据提取)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `pulse` | `Pulse`、`Dict` 或 `callable` | ✅ 是 | - | 脉冲定义 |
| `t_grid` | `np.ndarray` | ✅ 是 | - | 采样的时间网格 |
| `atom_index` | `int` | ❌ 可选 | `None` | 局域寻址的原子索引 |
| `field` | `str` | ❌ 可选 | `'omega'` | 要采样的场:'omega'或'delta' |

#### 返回值

- **类型**: `np.ndarray`
- **形状**: `(len(t_grid),)`
- **描述**: 每个时间点的脉冲幅值数组

#### 示例

```python
from sagittarius.viz import sample_pulse_waveform
import numpy as np

pulse = {'type': 'constant', 'value': 5.0}
t_grid = np.linspace(0, 1.0, 100)
values = sample_pulse_waveform(pulse, t_grid, field='omega')
print(values.shape)  # (100,)
print(values[:5])    # [5.0, 5.0, 5.0, 5.0, 5.0]
```

---

### `plot_observables()`

**模块**: `sagittarius.viz.result`

**功能**: 从SimulationResult绘制可观测量轨迹随时间的变化。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 具有`.to_pandas()`方法的Result对象 |
| `names` | `List[str]` | ❌ 可选 | `None` | 要绘制的可观测量列名列表。如为None则自动检测 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show` | `bool` | ❌ 可选 | `False` | 是否立即调用plt.show() |
| `title` | `str` | ❌ 可选 | `None` | 自定义图表标题。如为None则自动生成 |
| `linewidth` | `float` | ❌ 可选 | `2.0` | 所有曲线的线宽 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 异常

- `ValueError`: 如果指定的可观测量名称在结果DataFrame中不存在

#### 示例

```python
from sagittarius.viz import plot_observables

# 自动检测可观测量
ax = plot_observables(result)

# 指定自定义可观测量
ax = plot_observables(result, names=['pop0', 'pop1', 'energy'])

# 在现有坐标轴上绘制并自定义样式
fig, ax = plt.subplots()
plot_observables(result, ax=ax, linewidth=3.0, title="自定义标题")
```

---

### `plot_bitstring_distribution()`

**模块**: `sagittarius.viz.result`

**功能**: 将末态比特串概率分布绘制为柱状图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含比特串分布数据的Result对象 |
| `top_k` | `int` | ❌ 可选 | `10` | 显示的最高概率比特串数量 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `sort_by` | `str` | ❌ 可选 | `'probability'` | 排序方式:'probability'(降序)或'bitstring'(升序) |
| `show_basis_info` | `bool` | ❌ 可选 | `True` | 是否在标题中显示基模式和禁戒计数信息 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_bitstring_distribution

# 显示前10个比特串并包含基信息
ax = plot_bitstring_distribution(result, top_k=10)

# 按比特串而非概率排序
ax = plot_bitstring_distribution(result, sort_by='bitstring')

# 隐藏基信息
ax = plot_bitstring_distribution(result, show_basis_info=False)
```

---

### `plot_shot_histogram()`

**模块**: `sagittarius.viz.result`

**功能**: 绘制某个观测量的测量次数分布直方图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含测量样本的Result对象 |
| `observable` | `str` | ❌ 可选 | `'energy'` | 要直方图化的可观测量名称 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `bins` | `int` | ❌ 可选 | `30` | 直方图的bin数量 |
| `show_stats` | `bool` | ❌ 可选 | `True` | 是否显示均值/标准差标注 |
| `normalized` | `bool` | ❌ 可选 | `False` | 是否归一化直方图(density=True) |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 异常

- `ValueError`: 如果在result中未找到测量样本

#### 示例

```python
from sagittarius.viz import plot_shot_histogram

# 能量分布并显示统计信息
ax = plot_shot_histogram(result, observable='energy', show_stats=True)

# 归一化直方图
ax = plot_shot_histogram(result, normalized=True, bins=50)

# 自定义可观测量
ax = plot_shot_histogram(result, observable='magnetization')
```

---

### `plot_population_heatmap()`

**模块**: `sagittarius.viz.result`

**功能**: 绘制原子×时间布居热图(2D彩色地图)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含布居时间序列的Result对象 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `cmap` | `str` | ❌ 可选 | `'viridis'` | 颜色映射名称(matplotlib colormap) |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_population_heatmap

# 默认viridis颜色映射
ax = plot_population_heatmap(result)

# 自定义颜色映射
ax = plot_population_heatmap(result, cmap='plasma', title="布居动力学")
```

---

### `generate_basis_diagnostics()`

**模块**: `sagittarius.viz.basis_diagnostics`

**功能**: 生成约化基诊断数据(有效/禁戒比特串)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | Register对象或坐标列表 |
| `blockade_radius` | `float` | ✅ 是 | - | 用于约束检测的阻塞半径 |
| `edges` | `List[Tuple[int, int]]` | ❌ 可选 | `None` | 预计算的边列表。如为None则自动计算 |

#### 返回值

- **类型**: `Dict[str, Any]`
- **结构**:
  ```python
  {
      'n_atoms': int,
      'full_dimension': int,  # 2^N
      'reduced_dimension': int,  # len(valid_states)
      'pruning_ratio': float,  # 1 - reduced/full
      'valid_bitstrings': List[str],  # 如: ['0000', '0001', ...]
      'forbidden_bitstrings': List[str],  # 如: ['0011', '1100', ...]
      'edges': List[Tuple[int, int]]
  }
  ```

#### 异常

- `ValueError`: 如果n_atoms > 10(组合爆炸)

#### 示例

```python
from sagittarius.viz import generate_basis_diagnostics

reg = Register([(0, 0), (5, 0), (2.5, 4.33)])
diagnostics = generate_basis_diagnostics(reg, blockade_radius=6.0)

print(f"完整维度: {diagnostics['full_dimension']}")  # 8
print(f"约化维度: {diagnostics['reduced_dimension']}")  # 5
print(f"剪枝比例: {diagnostics['pruning_ratio']:.2%}")  # 37.50%
```

---

### `plot_basis_space_diagram()`

**模块**: `sagittarius.viz.basis_diagnostics`

**功能**: 可视化基空间剪枝(完整维度vs约化维度)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `diagnostics` | `Dict` | ✅ 是 | - | `generate_basis_diagnostics()`的输出 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `log_scale` | `bool` | ❌ 可选 | `True` | 是否对维度使用对数刻度 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import generate_basis_diagnostics, plot_basis_space_diagram

diag = generate_basis_diagnostics(reg, R_b=6.0)
ax = plot_basis_space_diagram(diag, log_scale=True)
```

---

### `plot_bitstring_space_grid()`

**模块**: `sagittarius.viz.basis_diagnostics`

**功能**: 网格化可视化有效(绿色)和禁戒(红色)比特串。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `diagnostics` | `Dict` | ✅ 是 | - | `generate_basis_diagnostics()`的输出 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `max_display` | `int` | ❌ 可选 | `100` | 最大显示的比特串数量(超过则截断) |
| `sort_order` | `str` | ❌ 可选 | `'ascending'` | 排序方式:'ascending'或'descending'(按整数值) |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_bitstring_space_grid

ax = plot_bitstring_space_grid(diagnostics, max_display=50)
```

---

### `plot_blockade_constraint_graph()`

**模块**: `sagittarius.viz.basis_diagnostics`

**功能**: 将阻塞约束网络可视化为图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `diagnostics` | `Dict` | ✅ 是 | - | `generate_basis_diagnostics()`的输出 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_statistics` | `bool` | ❌ 可选 | `True` | 是否显示约束统计信息框 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_blockade_constraint_graph

ax = plot_blockade_constraint_graph(diagnostics, show_statistics=True)
```

---

### `plot_comprehensive_basis_diagnostics()`

**模块**: `sagittarius.viz.basis_diagnostics`

**功能**: 生成多面板综合基诊断图形。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | Register对象或坐标列表 |
| `blockade_radius` | `float` | ✅ 是 | - | 阻塞半径 |
| `save_path` | `str` | ❌ 可选 | `None` | 如提供,则将图形保存到此路径 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(16, 12)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.figure.Figure`

#### 示例

```python
from sagittarius.viz import plot_comprehensive_basis_diagnostics

fig = plot_comprehensive_basis_diagnostics(reg, R_b=6.0, 
                                           save_path="basis_diag.png")
```

---

### `extract_geometry_diagnostics()`

**模块**: `sagittarius.viz.geometry_diagnostics`

**功能**: 提取几何诊断数据(距离、VDW、邻接)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | Register对象或坐标列表 |
| `blockade_radius` | `float` | ❌ 可选 | `None` | 用于邻接矩阵的阻塞半径 |
| `C6` | `float` | ❌ 可选 | `None` | van der Waals系数用于VDW矩阵 |

#### 返回值

- **类型**: `Dict[str, Any]`
- **结构**:
  ```python
  {
      'distance_matrix': np.ndarray,  # N×N对称矩阵
      'vdw_matrix': np.ndarray or None,  # 如提供C6则为N×N
      'adjacency_matrix': np.ndarray or None,  # 如提供R_b则为N×N二值矩阵
      'edges': List[Tuple[int, int]],
      'graph_density': float,
      'min_distance': float,
      'max_distance': float,
      'mean_distance': float
  }
  ```

#### 示例

```python
from sagittarius.viz import extract_geometry_diagnostics

diag = extract_geometry_diagnostics(reg, blockade_radius=6.0, C6=80.0)
print(diag['distance_matrix'].shape)  # (N, N)
print(diag['graph_density'])  # 0.0 - 1.0
```

---

### `plot_geometry_diagnostics()`

**模块**: `sagittarius.viz.geometry_diagnostics`

**功能**: 绘制几何诊断热力图(距离/VDW/邻接)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | Register对象或坐标列表 |
| `blockade_radius` | `float` | ❌ 可选 | `None` | 阻塞半径 |
| `C6` | `float` | ❌ 可选 | `None` | VDW系数 |
| `show_vdw_matrix` | `bool` | ❌ 可选 | `True` | 是否显示VDW热力图面板 |
| `show_adjacency` | `bool` | ❌ 可选 | `True` | 是否显示邻接热力图面板 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(16, 12)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes` 或 `np.ndarray[Axes]`(多面板)

#### 示例

```python
from sagittarius.viz import plot_geometry_diagnostics

axes = plot_geometry_diagnostics(reg, R_b=6.0, C6=80.0)
```

---

### `plot_unit_disk_graph()`

**模块**: `sagittarius.viz.geometry_diagnostics`

**功能**: 可视化含节点和边的单位圆盘图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | Register对象或坐标列表 |
| `blockade_radius` | `float` | ✅ 是 | - | 用于边检测的阻塞半径 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_distances` | `bool` | ❌ 可选 | `False` | 是否标注边距离 |
| `labels` | `bool` | ❌ 可选 | `True` | 是否显示原子索引标签 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_unit_disk_graph

ax = plot_unit_disk_graph(reg, R_b=6.0, show_distances=True)
```

---

### `plot_mwis_problem()`

**模块**: `sagittarius.viz.mwis_viz`

**功能**: 可视化MWIS问题,含节点权重、边和冲突高亮。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | Register对象或坐标列表 |
| `bitstring` | `str` | ✅ 是 | - | 解比特串(如"1010") |
| `weights` | `List[float]` | ❌ 可选 | `None` | MWIS目标的节点权重 |
| `edges` | `List[Tuple[int, int]]` | ❌ 可选 | `None` | 边列表。如为None则从R_b自动计算 |
| `blockade_radius` | `float` | ❌ 可选 | `None` | 用于自动边检测的阻塞半径 |
| `highlight_conflicts` | `bool` | ❌ 可选 | `True` | 是否高亮约束违反 |
| `algorithm_name` | `str` | ❌ 可选 | `None` | 算法名称用于标注 |
| `performance_metrics` | `Dict` | ❌ 可选 | `None` | 性能指标字典 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 10)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_mwis_problem

reg = Register([(0, 0), (5, 0), (2.5, 4.33)])
solution = "101"
weights = [1.0, 2.0, 1.5]

ax = plot_mwis_problem(reg, solution, weights=weights, 
                       blockade_radius=6.0, highlight_conflicts=True,
                       algorithm_name="QAOA",
                       performance_metrics={'approximation_ratio': 0.95})
```

---

### `plot_pair_correlation_matrix()`

**模块**: `sagittarius.viz.correlation_viz`

**功能**: 绘制成对关联⟨nᵢnⱼ⟩热力图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含关联观测量的Result |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `threshold` | `float` | ❌ 可选 | `0.01` | 标注的最小绝对值 |
| `show_values` | `bool` | ❌ 可选 | `True` | 是否标注单元格值 |
| `cmap` | `str` | ❌ 可选 | `'RdBu_r'` | 颜色映射 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 异常

- `ValueError`: 如果在result中未找到关联观测量

#### 示例

```python
from sagittarius.viz import plot_pair_correlation_matrix

ax = plot_pair_correlation_matrix(result, threshold=0.05)
```

---

### `plot_connected_correlation_matrix()`

**模块**: `sagittarius.viz.correlation_viz`

**功能**: 绘制连通关联Cᵢⱼ = ⟨nᵢnⱼ⟩ - ⟨nᵢ⟩⟨nⱼ⟩热力图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含关联观测量的Result |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `significance_threshold` | `float` | ❌ 可选 | `0.05` | 显著性掩码阈值 |
| `show_values` | `bool` | ❌ 可选 | `True` | 是否标注值 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_connected_correlation_matrix

ax = plot_connected_correlation_matrix(result, significance_threshold=0.1)
```

---

### `plot_pauli_zz_matrix()`

**模块**: `sagittarius.viz.correlation_viz`

**功能**: 绘制Pauli-ZZ关联⟨σᶻᵢσᶻⱼ⟩热力图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含Pauli-ZZ观测量的Result |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_values` | `bool` | ❌ 可选 | `True` | 是否标注值 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_pauli_zz_matrix

ax = plot_pauli_zz_matrix(result)
```

---

### `plot_blockade_conflict_heatmap()`

**模块**: `sagittarius.viz.correlation_viz`

**功能**: 绘制阻塞冲突结构热力图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含比特串数据的Result |
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | 用于几何的Register |
| `mode` | `str` | ❌ 可选 | `'matrix'` | 模式:'matrix'或'edges' |
| `edges` | `List[Tuple[int, int]]` | ❌ 可选 | `None` | 边列表(如mode='edges'则必需) |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_blockade_conflict_heatmap

# 矩阵模式
ax = plot_blockade_conflict_heatmap(result, reg, mode='matrix')

# 边模式
ax = plot_blockade_conflict_heatmap(result, reg, mode='edges', edges=edge_list)
```

---

### `extract_spatial_snapshot()`

**模块**: `sagittarius.viz.spatial_snapshot`

**功能**: 提取单帧空间布居数据。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含时间序列数据的Result |
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | 用于原子位置的Register |
| `time_index` | `int` | ✅ 是 | - | 要提取的时间步索引 |
| `observable_name` | `str` | ❌ 可选 | `'pop'` | 可观测量前缀(如'pop'对应pop0, pop1, ...) |

#### 返回值

- **类型**: `Dict[str, Any]`
- **结构**:
  ```python
  {
      'time': float,
      'positions': np.ndarray,  # (N, 2)
      'populations': Dict[int, float],  # {atom_idx: pop_value}
      'observable_name': str,
      'n_atoms': int
  }
  ```

#### 示例

```python
from sagittarius.viz import extract_spatial_snapshot

snapshot = extract_spatial_snapshot(result, reg, time_index=50)
print(snapshot['time'])  # 0.5
print(snapshot['populations'][0])  # 0.85
```

---

### `extract_frame_sequence()`

**模块**: `sagittarius.viz.spatial_snapshot`

**功能**: 提取多帧序列用于动画或对比。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含时间序列数据的Result |
| `register` | `Register` 或 `List[Tuple[float, float]]` | ✅ 是 | - | 用于位置的Register |
| `time_indices` | `List[int]` | ❌ 可选 | `None` | 时间索引列表。如为None则自动生成4个均匀间隔的索引 |
| `observable_name` | `str` | ❌ 可选 | `'pop'` | 可观测量前缀 |

#### 返回值

- **类型**: `List[Dict]` - 快照字典列表

#### 示例

```python
from sagittarius.viz import extract_frame_sequence

frames = extract_frame_sequence(result, reg, time_indices=[0, 25, 50, 75])
print(len(frames))  # 4
```

---

### `plot_spatial_snapshot()`

**模块**: `sagittarius.viz.spatial_snapshot`

**功能**: 绘制单帧空间布居快照。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `snapshot` | `Dict` | ✅ 是 | - | `extract_spatial_snapshot()`的输出 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `cmap` | `str` | ❌ 可选 | `'viridis'` | 颜色映射 |
| `show_labels` | `bool` | ❌ 可选 | `True` | 是否显示原子索引标签 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `save_path` | `str` | ❌ 可选 | `None` | 如提供则保存到此路径 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import extract_spatial_snapshot, plot_spatial_snapshot

snapshot = extract_spatial_snapshot(result, reg, time_index=50)
ax = plot_spatial_snapshot(snapshot, cmap='plasma')
```

---

### `plot_multi_panel_snapshots()`

**模块**: `sagittarius.viz.spatial_snapshot`

**功能**: 绘制多面板帧对比。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `snapshot_list` | `List[Dict]` | ✅ 是 | - | 快照字典列表 |
| `ax_list` | `List[Axes]` | ❌ 可选 | `None` | 坐标轴列表。如为None则自动创建2×2网格 |
| `shared_colorbar` | `bool` | ❌ 可选 | `True` | 是否使用共享颜色条 |
| `suptitle` | `str` | ❌ 可选 | `None` | 超级标题 |
| `save_path` | `str` | ❌ 可选 | `None` | 保存路径 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(16, 12)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes` 或 `np.ndarray[Axes]`

#### 示例

```python
from sagittarius.viz import extract_frame_sequence, plot_multi_panel_snapshots

frames = extract_frame_sequence(result, reg)
axes = plot_multi_panel_snapshots(frames, suptitle="时间演化")
```

---

### `plot_time_grid_diagnostics()`

**模块**: `sagittarius.viz.diagnostics`

**功能**: 绘制时间网格采样诊断,含自适应步长可视化。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | 包含时间序列数据的Result |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_adaptive` | `bool` | ❌ 可选 | `True` | 是否显示自适应步长着色 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_time_grid_diagnostics

ax = plot_time_grid_diagnostics(result, show_adaptive=True)
```

---

### `plot_lindblad_validation()`

**模块**: `sagittarius.viz.diagnostics`

**功能**: 绘制Lindblad方程验证(迹误差和正定性)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | Result对象 |
| `metrics` | `Dict` | ✅ 是 | - | Julia求解器的健全性检查指标字典 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_trace_error` | `bool` | ❌ 可选 | `True` | 是否显示迹误差面板 |
| `show_positivity` | `bool` | ❌ 可选 | `True` | 是否显示正定性面板 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 5)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes` 或 `np.ndarray[Axes]`

#### 异常

- `ValueError`: 如果缺少必需的指标字段

#### 示例

```python
from sagittarius.viz import plot_lindblad_validation

metrics = result.metadata.get('sanity_checks', {})
ax = plot_lindblad_validation(result, metrics)
```

---

### `plot_mcwf_vs_lindblad()`

**模块**: `sagittarius.viz.diagnostics`

**功能**: 绘制MCWF与Lindblad模拟对比。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `lindblad_result` | `SimulationResult` | ✅ 是 | - | Lindblad模拟结果 |
| `mcwf_result` | `SimulationResult` | ✅ 是 | - | MCWF模拟结果 |
| `observables` | `List[str]` | ❌ 可选 | `None` | 要对比的可观测量名称。如为None则自动检测共同的观测量 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes` 或 `np.ndarray[Axes]`

#### 示例

```python
from sagittarius.viz import plot_mcwf_vs_lindblad

axes = plot_mcwf_vs_lindblad(lindblad_res, mcwf_res, 
                             observables=['pop0', 'energy'])
```

---

### `plot_trajectory_statistics()`

**模块**: `sagittarius.viz.diagnostics`

**功能**: 绘制轨迹统计含置信区间(均值 ± σ)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `trajectories` | `np.ndarray` | ✅ 是 | - | 轨迹数据数组,形状(n_trajectories, n_times) |
| `t` | `np.ndarray` | ✅ 是 | - | 时间数组,形状(n_times,) |
| `observable_name` | `str` | ❌ 可选 | `'observable'` | 用于标记的可观测量名称 |
| `confidence_level` | `float` | ❌ 可选 | `0.95` | 置信区间水平(0.95 = ±2σ) |
| `show_individual` | `bool` | ❌ 可选 | `False` | 是否显示单个轨迹 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_trajectory_statistics

# 从result提取轨迹
trajectories = result.trajectories  # 形状: (50, 100)
t = result.t

ax = plot_trajectory_statistics(trajectories, t, 
                                observable_name='energy',
                                confidence_level=0.95,
                                show_individual=True)
```

---

### `plot_runtime_scaling()`

**模块**: `sagittarius.viz.benchmark_perf`

**功能**: 绘制运行时随原子数的缩放曲线。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `artifacts` | `List[Dict]` | ✅ 是 | - | 基准artifact字典列表 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |
| `show_fit` | `bool` | ❌ 可选 | `True` | 是否拟合并显示幂律曲线 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### Artifact格式

```python
{
    'n_atoms': int,
    'runtime_seconds': float,
    'artifact_id': str,
    'status': str  # 'success' 或 'failed'
}
```

#### 示例

```python
from sagittarius.viz import plot_runtime_scaling

artifacts = [
    {'n_atoms': 5, 'runtime_seconds': 0.5, 'artifact_id': 'bench-n5'},
    {'n_atoms': 10, 'runtime_seconds': 2.3, 'artifact_id': 'bench-n10'},
    {'n_atoms': 15, 'runtime_seconds': 8.7, 'artifact_id': 'bench-n15'}
]

ax = plot_runtime_scaling(artifacts, show_fit=True)
```

---

### `plot_memory_scaling()`

**模块**: `sagittarius.viz.benchmark_perf`

**功能**: 绘制内存使用随希尔伯特空间维度的缩放曲线。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `artifacts` | `List[Dict]` | ✅ 是 | - | 基准artifact列表 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `unit` | `str` | ❌ 可选 | `'MB'` | 内存单位:'KB'、'MB'或'GB' |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_memory_scaling

artifacts = [...]  # 必须包含'memory_mb'和'hilbert_dim'字段
ax = plot_memory_scaling(artifacts, unit='GB')
```

---

### `plot_solver_comparison()`

**模块**: `sagittarius.viz.benchmark_perf`

**功能**: 对比多个求解器的性能。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `artifacts_by_solver` | `Dict[str, List[Dict]]` | ✅ 是 | - | 映射求解器名称到artifact列表的字典 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_error_bars` | `bool` | ❌ 可选 | `True` | 是否显示误差棒 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_solver_comparison

artifacts_by_solver = {
    'MCWF': [...],
    'Lindblad': [...],
    'TensorNetwork': [...]
}

ax = plot_solver_comparison(artifacts_by_solver)
```

---

### `plot_success_failure_summary()`

**模块**: `sagittarius.viz.benchmark_perf`

**功能**: 绘制成功/失败率摘要。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `artifacts` | `List[Dict]` | ✅ 是 | - | 基准artifact列表 |
| `group_by` | `str` | ❌ 可选 | `'solver'` | 分组方式:'solver'或'n_atoms' |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_success_failure_summary

# 按求解器分组
ax = plot_success_failure_summary(artifacts, group_by='solver')

# 按原子数分组
ax = plot_success_failure_summary(artifacts, group_by='n_atoms')
```

---

### `plot_cpu_gpu_error_comparison()`

**模块**: `sagittarius.viz.benchmark_perf`

**功能**: 对比CPU与GPU模拟误差。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `cpu_artifacts` | `List[Dict]` | ✅ 是 | - | CPU基准artifact |
| `gpu_artifacts` | `List[Dict]` | ✅ 是 | - | GPU基准artifact |
| `error_type` | `str` | ❌ 可选 | `'relative'` | 误差类型:'relative'或'absolute' |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_cpu_gpu_error_comparison

ax = plot_cpu_gpu_error_comparison(cpu_artifacts, gpu_artifacts, 
                                   error_type='relative')
```

---

### `plot_state_probabilities()`

**模块**: `sagittarius.viz.small_system_debug`

**功能**: 将态矢量概率\|ψᵢ\|²绘制为柱状图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `state_vector` | `np.ndarray` | ✅ 是 | - | 态矢量数组,形状(2^N,) |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_labels` | `bool` | ❌ 可选 | `True` | 是否显示比特串标签 |
| `top_k` | `int` | ❌ 可选 | `None` | 仅显示前K个态。None表示全部 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 异常

- `ValueError`: 如果希尔伯特空间维度 > 1024 (>10量子比特)

#### 示例

```python
from sagittarius.viz import plot_state_probabilities
import numpy as np

# Bell态: (|00⟩ + |11⟩) / √2
psi = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
ax = plot_state_probabilities(psi, top_k=4)
```

---

### `plot_density_matrix_diagonal()`

**模块**: `sagittarius.viz.small_system_debug`

**功能**: 绘制密度矩阵对角元(布居数)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `rho` | `np.ndarray` | ✅ 是 | - | 密度矩阵,形状(2^N, 2^N) |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_labels` | `bool` | ❌ 可选 | `True` | 是否显示比特串标签 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(12, 6)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_density_matrix_diagonal
import numpy as np

# 纯态密度矩阵
psi = np.array([1, 0, 0, 0])
rho = np.outer(psi, psi.conj())
ax = plot_density_matrix_diagonal(rho)
```

---

### `plot_density_matrix_magnitude()`

**模块**: `sagittarius.viz.small_system_debug`

**功能**: 绘制密度矩阵模值热力图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `rho` | `np.ndarray` | ✅ 是 | - | 密度矩阵 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `cmap` | `str` | ❌ 可选 | `'viridis'` | 颜色映射 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例


---

### `plot_sweep_heatmap()`

**模块**: `sagittarius.viz.sweep`

**功能**: 绘制2D参数扫描热力图,支持失败运行标记和artifact链接。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `sweep_data` | `Dict[str, Any]` | ✅ 是 | - | 包含扫描结果的字典 |
| `x_param` | `str` | ❌ 可选 | `'omega'` | x轴参数名 |
| `y_param` | ❌ 可选 | `'delta'` | ' y轴参数名 |
| `metric` | `str` | ❌ 可选 | `'pop0'` | 要可视化的指标名 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_colorbar` | `bool` | ❌ 可选 | `True` | 是否显示颜色条 |
| `show_failed_mask` | `bool` | ❌ 可选 | `True` | 是否用红色X标记失败的运行 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |
| `cmap` | `str` | ❌ 可选 | `'viridis'` | 颜色映射名称 |

#### sweep_data结构

```python
{
    'parameters': {
        'omega': array-like,  # x轴值
        'delta': array-like,  # y轴值
    },
    'results': {
        'metric_name': 2D array,  # shape (len(delta), len(omega))
        ...
    },
    'failed_runs': set of tuples  # {(omega_idx, delta_idx), ...}
                   or boolean mask array,
    'manifest_links': {  # 可选
        'run_id': 'artifact_id',
        ...
    }
}
```

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_sweep_heatmap, generate_synthetic_sweep_data

# 生成合成数据
sweep_data = generate_synthetic_sweep_data(
    omega_range=(0.5, 5.0),
    delta_range=(-3.0, 3.0),
    n_omega=25,
    n_delta=20,
)

# 绘制热力图
ax = plot_sweep_heatmap(sweep_data, metric='pop0')
```

---

### `plot_sweep_line_slice()`

**模块**: `sagittarius.viz.sweep`

**功能**: 绘制参数扫描的1D切片(线切片)。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `sweep_data` | `Dict[str, Any]` | ✅ 是 | - | 包含扫描结果的字典 |
| `fixed_param` | `str` | ✅ 是 | - | 保持固定的参数名 |
| `fixed_value` | `float` | ✅ 是 | - | 固定参数的值 |
| `varying_param` | `str` | ✅ 是 | - | 沿x轴变化的参数名 |
| `metric` | `str` | ❌ 可选 | `'pop0'` | 要可视化的指标名 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_error_bars` | `bool` | ❌ 可选 | `False` | 如果存在std数据,是否显示误差棒 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |
| `color` | `str` | ❌ 可选 | `'steelblue'` | 线条颜色 |
| `marker` | `str` | ❌ 可选 | `'o'` | 标记样式 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_sweep_line_slice

# 在delta=0处提取omega切片
ax = plot_sweep_line_slice(
    sweep_data,
    fixed_param='delta',
    fixed_value=0.0,
    varying_param='omega',
    show_error_bars=True
)
```

---

### `plot_final_observable_map()`

**模块**: `sagittarius.viz.sweep`

**功能**: 绘制1D参数扫描的最终可观测量值。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `sweep_data` | `Dict[str, Any]` | ✅ 是 | - | 包含扫描结果的字典 |
| `observable_name` | `str` | ❌ 可选 | `'pop0'` | 要绘制的可观测量名 |
| `param_name` | `str` | ❌ 可选 | `'omega'` | x轴参数名 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `show_markers` | `bool` | ❌ 可选 | `True` | 是否显示数据点标记 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 6)` | 图形尺寸,单位:英寸 |
| `color` | `str` | ❌ 可选 | `'steelblue'` | 线条/标记颜色 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_final_observable_map

# 从时间序列数据中提取最终值并绘制
ax = plot_final_observable_map(
    sweep_data,
    observable_name='pop0',
    param_name='omega'
)
```

---

### `plot_failed_run_mask()`

**模块**: `sagittarius.viz.sweep`

**功能**: 绘制二进制掩码,显示2D扫描中失败与成功的运行。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `sweep_data` | `Dict[str, Any]` | ✅ 是 | - | 包含'failed_runs'键的扫描结果字典 |
| `x_param` | `str` | ❌ 可选 | `'omega'` | x轴参数名 |
| `y_param` | `str` | ❌ 可选 | `'delta'` | y轴参数名 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `title` | `str` | ❌ 可选 | `None` | 自定义标题 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_failed_run_mask

# 绘制成功/失败掩码
ax = plot_failed_run_mask(sweep_data)
# 绿色单元格: 成功运行
# 红色单元格: 失败运行
```

---

### `extract_sweep_summary()`

**模块**: `sagittarius.viz.sweep`

**功能**: 从扫描数据中提取摘要统计信息。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `sweep_data` | `Dict[str, Any]` | ✅ 是 | - | 包含扫描结果的字典 |
| `metrics` | `List[str]` | ❌ 可选 | `None` | 要汇总的特定指标(默认:所有数值指标) |

#### 返回值

- **类型**: `Dict[str, Any]`
- **包含**: 每个指标的min、max、mean、std、median、q25、q75,以及运行统计信息

#### 示例

```python
from sagittarius.viz import extract_sweep_summary

summary = extract_sweep_summary(sweep_data, metrics=['pop0', 'energy'])

print(f"pop0范围: [{summary['pop0']['min']:.3f}, {summary['pop0']['max']:.3f}]")
print(f"成功率: {summary['run_statistics']['success_rate']:.1f}%")
```

---

### `generate_synthetic_sweep_data()`

**模块**: `sagittarius.viz.sweep`

**功能**: 生成用于演示的合成扫描数据。

⚠️ **注意**: 此函数仅用于演示目的,因为用户-facing的sweep artifacts尚未实现。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `omega_range` | `Tuple[float, float]` | ❌ 可选 | `(0.1, 5.0)` | omega参数范围(min, max) |
| `delta_range` | `Tuple[float, float]` | ❌ 可选 | `(-2.0, 2.0)` | delta参数范围(min, max) |
| `n_omega` | `int` | ❌ 可选 | `20` | omega值的采样数量 |
| `n_delta` | `int` | ❌ 可选 | `15` | delta值的采样数量 |
| `seed` | `int` | ❌ 可选 | `42` | 随机种子,确保可复现性 |
| `failure_rate` | `float` | ❌ 可选 | `0.05` | 失败运行的比例(0-1) |

#### 返回值

- **类型**: `Dict[str, Any]`
- **包含**: parameters、results、failed_runs、manifest_links、metadata

#### 示例

```python
from sagittarius.viz import generate_synthetic_sweep_data

# 生成合成扫描数据
sweep_data = generate_synthetic_sweep_data(
    omega_range=(0.5, 5.0),
    delta_range=(-3.0, 3.0),
    n_omega=25,
    n_delta=20,
    seed=42,
    failure_rate=0.08,
)
```

---

## 快速参考卡片

| 可视化类型 | 函数名 | 用途 | 后端依赖 |
|-----------|--------|------|----------|
| **Sweep热力图** | [`plot_sweep_heatmap()`](file:///workspaces/Sagittarius/sagittarius_py/sagittarius/viz/sweep.py#L18-L179) | 2D参数扫描可视化 | 无(纯Python) |
| **线切片** | [`plot_sweep_line_slice()`](file:///workspaces/Sagittarius/sagittarius_py/sagittarius/viz/sweep.py#L182-L291) | 1D参数切片 | 无(纯Python) |
| **最终可观测量图** | [`plot_final_observable_map()`](file:///workspaces/Sagittarius/sagittarius_py/sagittarius/viz/sweep.py#L294-L407) | 最终值vs参数 | 无(纯Python) |
| **失败运行掩码** | [`plot_failed_run_mask()`](file:///workspaces/Sagittarius/sagittarius_py/sagittarius/viz/sweep.py#L410-L512) | 成功/失败二元图 | 无(纯Python) |
| **摘要统计** | [`extract_sweep_summary()`](file:///workspaces/Sagittarius/sagittarius_py/sagittarius/viz/sweep.py#L515-L585) | 统计信息提取 | 无(纯Python) |
| **合成数据生成** | [`generate_synthetic_sweep_data()`](file:///workspaces/Sagittarius/sagittarius_py/sagittarius/viz/sweep.py#L588-L677) | 演示数据生成 | 无(纯Python) |

---

## 附录: Sweep可视化规范

### 分层隔离要求

根据项目规范,所有sweep可视化必须遵循以下原则:

1. **探索性标识**: 所有图表必须包含免责声明"⚠️ EXPLORATORY VISUALIZATION - Not for hardware calibration"
2. **Artifact链接**: 当提供manifest_links时,必须在图表中显示sample artifact ID
3. **参数保留**: 所有图表必须保留原始参数值和位置信息
4. **失败标记**: 失败的运行必须清晰标记(红色X或红色单元格)
5. **无后端依赖**: 优先采用无后端依赖方案,直接基于Python对象或已保存产物提取数据

### 数据结构要求

`sweep_data`字典必须包含:
- `parameters`: 参数字典,键为参数名,值为数组
- `results`: 结果字典,键为指标名,值为与参数维度匹配的数组
- `failed_runs`: 失败运行的索引集合或布尔掩码数组
- `manifest_links` (可选): run_id到artifact_id的映射字典

### 合规性检查

✅ **已实现的功能**:
- 2D热力图 with failed run overlay
- 1D line slices with error bars
- Final observable extraction from time series
- Binary success/failure masks
- Statistical summary extraction
- Artifact link preservation
- Mandatory disclaimers on all plots
- No backend dependency (pure Python/NumPy/Matplotlib)

✅ **符合REQUIREMENTS.md要求**:
- Preserves parameter values ✓
- Preserves result locations ✓
- Marks failed runs clearly ✓
- Links to run manifests when available ✓
- Clearly marked as EXPLORATORY (not for calibration) ✓

```python
from sagittarius.viz import plot_density_matrix_magnitude

ax = plot_density_matrix_magnitude(rho, cmap='plasma')
```

---

### `plot_density_matrix_phase()`

**模块**: `sagittarius.viz.small_system_debug`

**功能**: 绘制密度矩阵相位热力图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `rho` | `np.ndarray` | ✅ 是 | - | 密度矩阵 |
| `ax` | `matplotlib.axes.Axes` | ❌ 可选 | `None` | 现有的绘图坐标轴 |
| `cmap` | `str` | ❌ 可选 | `'twilight'` | 颜色映射 |
| `figsize` | `Tuple[float, float]` | ❌ 可选 | `(10, 8)` | 图形尺寸,单位:英寸 |

#### 返回值

- **类型**: `matplotlib.axes.Axes`

#### 示例

```python
from sagittarius.viz import plot_density_matrix_phase

ax = plot_density_matrix_phase(rho)
```

---

### `export_figure()`

**模块**: `sagittarius.viz.export`

**功能**: 将图形导出为文件并附带元数据JSON。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `fig` | `matplotlib.figure.Figure` | ✅ 是 | - | 要导出的Figure对象 |
| `output_path` | `str` | ✅ 是 | - | 输出文件路径(不含扩展名) |
| `formats` | `List[str]` | ❌ 可选 | `['png']` | 输出格式:'png'、'svg'、'pdf' |
| `metadata` | `Dict` | ❌ 可选 | `None` | 自定义元数据字典 |
| `save_metadata` | `bool` | ❌ 可选 | `True` | 是否保存.metadata.json文件 |
| `dpi` | `int` | ❌ 可选 | `300` | PNG输出的DPI |

#### 返回值

- **类型**: `None`
- **副作用**: 保存图片文件和可选的元数据JSON

#### 示例

```python
from sagittarius.viz import export_figure
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])

export_figure(fig, 'my_plot', formats=['png', 'svg'], dpi=300)
# 创建: my_plot.png, my_plot.svg, my_plot.metadata.json
```

---

### `export_from_result()`

**模块**: `sagittarius.viz.export`

**功能**: 从Result对象一键导出并自动绘图。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `result` | `SimulationResult` | ✅ 是 | - | Result对象 |
| `plot_function` | `callable` | ✅ 是 | - | 绘图函数(如`plot_observables`) |
| `output_path` | `str` | ✅ 是 | - | 输出路径(不含扩展名) |
| `plot_kwargs` | `Dict` | ❌ 可选 | `{}` | 绘图函数的关键字参数 |
| `formats` | `List[str]` | ❌ 可选 | `['png']` | 输出格式 |
| `metadata` | `Dict` | ❌ 可选 | `None` | 附加元数据 |

#### 返回值

- **类型**: `None`

#### 示例

```python
from sagittarius.viz import export_from_result, plot_observables

export_from_result(
    result, 
    plot_observables, 
    'observable_plot',
    plot_kwargs={'names': ['pop0', 'pop1']},
    formats=['png', 'pdf']
)
```

---

### `ReportGenerator`

**模块**: `sagittarius.viz.report`

**功能**: 生成含嵌入图形的HTML或Markdown报告。

#### 构造函数参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `title` | `str` | ✅ 是 | - | 报告标题 |
| `classification` | `str` | ❌ 可选 | `'EXPLORATORY'` | 分类:'EXPLORATORY'或'BENCHMARK_EVIDENCE' |
| `author` | `str` | ❌ 可选 | `None` | 作者姓名 |
| `description` | `str` | ❌ 可选 | `''` | 报告描述 |

#### 方法

##### `add_section(title, content, figures=None)`

向报告添加章节。

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `title` | `str` | ✅ 是 | - | 章节标题 |
| `content` | `str` | ✅ 是 | - | 章节内容(Markdown格式) |
| `figures` | `List[str]` | ❌ 可选 | `None` | 图形文件路径列表 |

##### `generate(output_path, format='html')`

生成报告文件。

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `output_path` | `str` | ✅ 是 | - | 输出文件路径 |
| `format` | `str` | ❌ 可选 | `'html'` | 格式:'html'或'markdown' |

**返回值**: `str` - 输出文件路径

#### 示例

```python
from sagittarius.viz import ReportGenerator, plot_observables
import matplotlib.pyplot as plt

# 创建报告
report = ReportGenerator(
    title="模拟结果",
    classification="EXPLORATORY",
    author="张三"
)

# 添加含图形的章节
fig, ax = plt.subplots()
plot_observables(result, ax=ax)
fig.savefig('obs_plot.png')

report.add_section(
    title="可观测量轨迹",
    content="关键可观测量随时间的演化。",
    figures=['obs_plot.png']
)

# 生成报告
output_path = report.generate('report.html', format='html')
print(f"报告已保存到: {output_path}")
```

---

### `generate_quick_report()`

**模块**: `sagittarius.viz.report`

**功能**: 快速一行式报告生成助手。

#### 参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `title` | `str` | ✅ 是 | - | 报告标题 |
| `sections` | `List[Dict]` | ✅ 是 | - | 章节字典列表 |
| `output_path` | `str` | ✅ 是 | - | 输出文件路径 |
| `classification` | `str` | ❌ 可选 | `'EXPLORATORY'` | 分类 |
| `format` | `str` | ❌ 可选 | `'html'` | 输出格式 |

#### 章节字典格式

```python
{
    'title': str,
    'content': str,
    'figures': List[str]  # 可选
}
```

#### 返回值

- **类型**: `str` - 输出文件路径

#### 示例

```python
from sagittarius.viz import generate_quick_report

sections = [
    {
        'title': '结果',
        'content': '模拟成功完成。',
        'figures': ['plot1.png', 'plot2.png']
    },
    {
        'title': '分析',
        'content': '主要发现...'
    }
]

path = generate_quick_report(
    title="快速报告",
    sections=sections,
    output_path='quick_report.html'
)
```

---

## 📚 附录

### 常用数据类型

#### `Register` 对象

```python
from sagittarius import Register

# 从坐标创建
reg = Register([(0, 0), (5, 0), (2.5, 4.33)])

# 访问位置
positions = reg.positions  # np.ndarray, 形状 (N, 2)
atoms = reg.atoms  # Atom对象列表
```

#### `SimulationResult` 对象

```python
# 转换为pandas DataFrame
df = result.to_pandas()

# 访问元数据
manifest = result.manifest
seed = result.seed

# 访问轨迹(如可用)
trajectories = result.trajectories  # np.ndarray, 形状 (n_traj, n_times)
```

#### `Pulse` 格式

```python
# 字典格式
pulse = {
    'type': 'gaussian',
    'amplitude': 10.0,
    'center': 0.5,
    'sigma': 0.1
}

# AST节点(来自Julia)
from sagittarius import Pulse
pulse = Pulse(...)

# 可调用函数
def my_pulse(t):
    return 5.0 * np.sin(2 * np.pi * t)
```

### 错误处理

所有可视化函数遵循一致的错误处理:

1. **输入验证**: 检查参数类型和范围
2. **清晰的错误消息**: 提供可操作的错误消息和上下文
3. **优雅降级**: 当可选参数缺失时使用合理的默认值


