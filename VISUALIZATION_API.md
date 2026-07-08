# Sagittarius 可视化 API 文档

## 📋 概述

#
 Sagittarius Phase 19 可视化模块的实现情况，包括设计目标、核心功能、API 接口和使用示例。

### 设计目标

**稳定、无后端依赖、元数据感知**的 Python 可视化对外接口，支持以下核心能力：

1. **寄存器布局可视化** - 二维原子排布、拓扑元数据、阻塞关联图
2. **脉冲波形采样与绘图** - 确定性脉冲解析，支持多种输入格式
3. **可观测量轨迹绘图** - 自选观测序列，自定义坐标轴
4. **原子布居热图** - 原子-时间维度热图，支持自定义排序
5. **比特串分布可视化** - 末态概率分布，支持 TopK 筛选和基模式标签
6. **测量采样直方图** - 带随机种子的采样统计，计数/频率双模式

### 工具分类

| 类型 | 说明 | 示例 |
|------|------|------|
| **数据提取器** | 从 SimulationResult 提取结构化数据 | `result.to_pandas()`, `result.final_bitstring_distribution()` |
| **绘图封装器** | 封装 Matplotlib 绘图逻辑，自动处理元数据 | `plot_observables()`, `plot_population_heatmap()` |
| **Matplotlib 接口** | 返回 Axes 对象，支持进一步定制 | 所有 `plot_*` 函数均返回 `matplotlib.axes.Axes` |

---

## 🎯 核心功能实现

### 1. 寄存器布局可视化 (`register.py`)

**需求**: 新增无后端依赖绘图工具，绘制二维原子排布、拓扑元数据、原子标签、单位圆盘图/阻塞关联边。

**实现位置**: [`sagittarius/viz/register.py`](sagittarius_py/sagittarius/viz/register.py)

#### 核心 API

```python
from sagittarius.viz import plot_register, plot_interaction_graph

# 通用绘图工具
def plot_register(
    register,  # 【必填】量子寄存器实例，兼容所有Register构造方式
    blockade_radius: Optional[float] = None,  # 【可选，默认=None】里德堡阻塞半径(μm)；None则不绘制阻塞边、阻塞圆盘
    edges: bool = True,  # 【可选，默认=True】是否绘制原子间阻塞虚线连线，仅blockade_radius不为空生效
    labels: bool = True,  # 【可选，默认=True】是否显示0起始原子编号文字标签
    ax: Optional[Axes] = None,  # 【可选，默认=None】外部传入matplotlib子图；不传自动新建8×8画布
    highlight_atoms: Optional[List[int]] = None,  # 【可选，默认=None】待高亮原子索引列表，已废弃，推荐使用bitstring
    highlight_color: str = 'red',  # 【可选，默认='red'】旧高亮模式原子填充色，仅highlight_atoms生效
    atom_size: int = 100,  # 【可选，默认=100】原子散点标记尺寸，单位points
    title: Optional[str] = None,  # 【可选，默认=None】自定义图表标题，为空自动生成内置标题
    show_blockade_disks: bool = False,  # 【可选，默认=False】是否绘制原子周边阻塞透明圆形区域
    disk_alpha: float = 0.1,  # 【可选，默认=0.1】阻塞圆盘透明度，取值0~1
    bitstring: Optional[str] = None,  # 【可选，默认=None】二进制态字符串，"0"基态、"1"激发态；优先级高于highlight_atoms
    excited_state_color: str = 'orange',  # 【可选，默认='orange'】比特1激发态原子颜色
    ground_state_color: str = 'steelblue',  # 【可选，默认='steelblue'】比特0基态原子默认颜色
) -> Axes:

# 拓扑关系可视化简易函数
 def plot_interaction_graph(
    register,  # 【必填】量子寄存器实例，兼容所有Register构造方式
    blockade_radius: float,  # 【必填】里德堡阻塞半径(μm)，用于判定原子相互作用边，不可传None
    ax: Optional[Axes] = None,  # 【可选，默认=None】外部matplotlib子图，不传自动新建8×8画布
    show_distances: bool = False,  # 【可选，默认=False】是否在阻塞连线中点标注原子间距数值
) -> Axes:
```

#### 功能特性

✅ **二维原子排布渲染**
- 使用 `scatter` 绘制原子位置，确保圆形标记（`aspect='equal'`）
- 支持自定义标记大小、颜色、边缘样式

✅ **阻塞关联边绘制**
- 基于距离矩阵自动计算邻接关系
- 使用 `LineCollection` 高效渲染边

✅ **原子标签居中叠加**
- 标签位于原子中心（`ha='center', va='center'`）
- 半透明背景框增强对比度
- 高 zorder 确保不被遮挡

✅ **阻塞圆盘可视化**
- 可选显示每个原子的阻塞范围
- 支持透明度调节（`disk_alpha`）
- 低 zorder 作为背景层

✅ **比特串叠加可视化** ⭐ 新增
- 通过 `bitstring` 参数传入二进制字符串（如 `"10101"`）
- 自动映射到原子位置：'1'=激发态（橙色），'0'=基态（蓝色）
- 支持自定义激发态和基态颜色
- 自动生成包含比特串信息的标题
- 自动添加图例说明状态含义
- 与阻塞圆盘、边等功能无缝集成
- 完整的输入验证（长度匹配、字符合法性）

✅ **三维寄存器支持**
- 当前仅支持二维可视化
- 三维场景需投影到 XY 平面

#### 技术要点

- **零后端依赖**: 纯 NumPy + Matplotlib 实现
- **层级管理**: 显式设置 zorder（网格线=1, 散点=5, 标签=10, 圆盘=0）
- **圆形保证**: `ax.set_aspect('equal', adjustable='datalim')`
- **比特串验证**: 长度检查 + 字符验证 + 清晰错误提示

#### 测试
- workplace里面的register_layout.py

---

### 2. 脉冲波形采样与绘图 (`pulse.py`)

**需求**: 提供确定性脉冲采样工具，基于时间网格解析 Ω/Δ 波形，支持多种输入格式。

**实现位置**: [`sagittarius/viz/pulse.py`](sagittarius_py/sagittarius/viz/pulse.py)

#### 核心 API

```python
from sagittarius.viz import plot_pulse_waveform
# plot_pulse_waveform 单场波形绘图（单独绘制 Ω 或 Δ）
def plot_pulse_waveform(
    pulse_sequence,  # 【必填】任意格式脉冲定义
    time_grid: Optional[np.ndarray] = None,  # 【可选，默认None】自定义时间网格，为空自动根据脉冲时长生成
    field: str = 'omega',  # 【可选，默认'omega'】绘制目标场 omega / delta
    atom_index: Optional[int] = None,  # 【可选，默认None】局域原子索引，None绘制全局脉冲
    ax: Optional[Axes] = None,  # 【可选，默认None】外部传入matplotlib子图，用于多子图拼接
    num_samples: int = 200,  # 【可选，默认200】自动生成网格时的采样点数
    title: Optional[str] = None,  # 【可选，默认None】自定义图表标题，为空使用默认标题
) -> tuple:
    """
    绘制单场脉冲波形，返回绘图坐标轴与完整采样数值数组。
    自动绘制曲线、填充底色、零基准线、图例、坐标轴标签。
    """
# plot_pulse_both_fields Ω 与 Δ 同画布双场绘图
def plot_pulse_both_fields(
    pulse_sequence,  # 【必填】脉冲序列定义
    time_grid: Optional[np.ndarray] = None,  # 【可选，默认None】自定义时间网格，空则自动生成
    atom_index: Optional[int] = None,  # 【可选，默认None】局域原子下标
    ax: Optional[Axes] = None,  # 【可选，默认None】外部绘图坐标轴
    num_samples: int = 200,  # 【可选，默认200】自动网格采样点数
) -> tuple:
    """
    快捷接口，同一画布同时绘制Ω拉比、Δ失谐两条波形，红蓝双色区分。
    返回坐标轴、omega采样数组、delta采样数组三组数据。
    """
```

#### 支持的输入格式

 **标量值**: `omega=2.0` → 恒定脉冲  
 **列表/数组**: `omega=[1.0, 2.0, 3.0]` → 离散时间点  
 **字典格式**: `seq = PulseSequence(
    omega={0: 1.0, 2: 3.0},  # 原子 0 和 2 有值
    delta={1: 0.5}            # 只有原子 1 有 detuning
)`  
 **可调用函数**: `lambda t: np.sin(t)`  
 **脉冲 AST**: 

| 节点类型 | 说明 | 数学公式 |
|---------|------|---------|
| `Constant` | 恒定值 | Ω(t) = c |
| `Ramp` | 线性斜坡 | Ω(t) = start + (stop-start) * t/duration |
| `Gaussian` | 高斯脉冲 | Ω(t) = A * exp(-(t-t0)²/(2σ²)) |
| `Blackman` | Blackman 窗 | 标准 Blackman 窗口函数 |
| `Sinc` | Sinc 函数 | Ω(t) = A * sinc(ω(t-t0)) |
| `Sinusoidal` | 正弦调制 | Ω(t) = A * sin(ωt + φ) |
| `Piecewise` | 分段组合 | 递归处理子脉冲 |

```
# Constant 脉冲
seq = PulseSequence(
    omega=Pulse.constant(value=2.0, duration=5.0),
    delta=Pulse.constant(value=0.0, duration=5.0)
)

# Ramp 脉冲
seq = PulseSequence(
    omega=Pulse.ramp(start=0.0, end=3.0, duration=5.0),
    delta=0.0
)

# Gaussian 脉冲
seq = PulseSequence(
    omega=Pulse.gaussian(amplitude=3.0, sigma=1.0, duration=5.0),
    delta=0.0
)

# Blackman 脉冲
seq = PulseSequence(
    omega=Pulse.blackman(amplitude=2.0, duration=5.0),
    delta=0.0
)

# Sinc 脉冲
seq = PulseSequence(
    omega=Pulse.sinc(amplitude=2.0, width=1.0, duration=5.0),
    delta=0.0
)

# SinSquared 脉冲
seq = PulseSequence(
    omega=Pulse.sin_squared(amplitude=2.0, duration=5.0),
    delta=0.0
)

# Piecewise 分段脉冲
seq = PulseSequence(
    omega=Pulse.piecewise([
        Pulse.ramp(0.0, 3.0, 2.0),      # 前 2μs
        Pulse.constant(3.0, 1.0),       # 中间 1μs
        Pulse.ramp(3.0, 0.0, 2.0)       # 后 2μs
    ]),
    delta=0.0
)
```
**显式寻址包装器**:
```python
from sagittarius import Pulse, GlobalPulse, LocalPulseVector

# GlobalPulse: 全局场
seq = PulseSequence(
    omega=Pulse.global_(2.0),
    delta=GlobalPulse(0.0)
)

# LocalPulseVector: 局部场（支持列表或字典）
seq = PulseSequence(
    omega=Pulse.local([1.0, 2.0, 3.0]),           # 列表形式
    delta=Pulse.local({0: 0.0, 1: 0.1, 2: 0.2})   # 字典形式
)

# CallablePulse: 显式可调用
seq = PulseSequence(
    omega=Pulse.callable(lambda t: [1.0, 2.0])
)
```



#### 技术要点

- **Backend-Free**: 纯 Python 解析 Pulse AST，不触发 Julia 初始化
- **向量化采样**: 利用 NumPy 广播机制高效计算
- **降级策略**: 不支持的 AST 节点发出 `UserWarning` 并返回默认值
- **时间网格**: 自动基于 `get_pulse_duration` 递归计算总时长

#### 测试
- workplace里面的pulse_demo.py
---

### 3. 可观测量轨迹绘图优化 (`result.py`)

**需求**: 扩展 `SimulationResult.plot()`，支持用户自选观测序列、传入自定义坐标轴、返回绘图对象。

**实现位置**: [`sagittarius/viz/result.py`](sagittarius_py/sagittarius/viz/result.py)

#### 核心 API

```python
def plot_observables(
    result,  # 【必填】SimulationResult仿真结果实例，必须拥有to_pandas()方法
    names: Optional[List[str]] = None,  # 【可选，默认=None】指定要绘制的可观测量名称列表；为空自动过滤时间列并绘制全部可观测量
    ax: Optional[Axes] = None,  # 【可选，默认=None】外部传入matplotlib子图，不传自动新建画布
    show: bool = False,  # 【可选，默认=False】绘图完成后是否直接调用plt.show()展示窗口
    title: Optional[str] = None,  # 【可选，默认=None】自定义图表标题，为空自动生成默认标题
    linewidth: float = 2.0,  # 【可选，默认=2.0】时序曲线线条宽度
    grid_alpha: float = 0.6,  # 【可选，默认=0.6】网格线透明度
) -> Axes:
```

#### 功能特性

 **自动列名检测**
- 排除元数据列（`t`, `schema_version` 等）
- 自动识别数值型观测序列

 **选择性绘图**
- `names` 参数指定要绘制的观测量
- 缺失列时抛出清晰的 `ValueError`

 **向后兼容**
- 保持 `SimulationResult.plot()` 原有行为
- 新增 `plot_observables()` 作为独立接口

 **诊断提示**
- 空结果时提示检查仿真配置
- 缺少列时列出可用选项

#### 使用示例

```python
result = sim.run(...)

# 方式 1: 使用便捷方法
result.plot()

# 方式 2: 使用独立函数（推荐）
ax = plot_observables(result, names=["pop0", "pop1"], show=False)
ax.set_title("Custom Title")
plt.savefig("observables.png")
```

---

### 4. 原子布居热图可视化 (`result.py`)

**需求**: 基于里德堡布居可观测量元数据或标准布居序列名称，生成原子-时间维度布居热图；支持自定义原子排序，缺失观测序列时输出清晰诊断提示。

**实现位置**: [`sagittarius/viz/result.py`](sagittarius_py/sagittarius/viz/result.py) - `plot_population_heatmap()`

#### 核心 API

```python
from sagittarius.viz import plot_population_heatmap

def plot_population_heatmap(
    result,  # 必填：SimulationResult，to_pandas输出包含pop0/pop1系列布居列
    ax: Optional[Axes] = None,  # 可选，默认None：外部子图，不传新建(10,6)画布
    cmap: str = 'viridis',  # 可选，默认viridis：Matplotlib内置色板名称
    title: Optional[str] = None,  # 可选，默认None：自定义标题，默认「Rydberg Population Heatmap」
    show_colorbar: bool = True,  # 可选，默认True：右侧显示颜色刻度图例
    atom_order: Optional[List[int]] = None,  # 可选，默认None：自定义原子纵向展示顺序列表，如[3,2,1,0]
) -> Axes:

# 基础用法（自动检测 pop* 列）
ax = plot_population_heatmap(result)

# 自定义原子排序
ax = plot_population_heatmap(result, atom_order=[4, 2, 0, 3, 1])

# 部分原子选择
ax = plot_population_heatmap(result, atom_order=[0, 2, 4])

# 自定义颜色映射
ax = plot_population_heatmap(result, cmap='plasma')
```

#### 功能特性

 **标准布居序列检测**
- 自动识别 `pop0`, `pop1`, `pop2`... 等列
- 按列名字典序默认排序

 **自定义原子排序** ⭐ 新增
- `atom_order` 参数指定显示顺序
- 支持部分原子选择
- 无效索引检测（越界、重复）

 **原子-时间热图**
- X 轴: 时间
- Y 轴: 原子索引
- 颜色: 布居值（0-1）

 **清晰诊断提示**
```python
ValueError: No population columns found in result. 
Available columns: ['t', 'energy']. 
Ensure simulation includes Rydberg population observables.
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | SimulationResult | - | 仿真结果对象 |
| `atom_order` | List[int] | None | 自定义原子顺序（0-based） |
| `cmap` | str | 'viridis' | 颜色映射 |
| `show_colorbar` | bool | True | 显示颜色条 |
| `ax` | Axes | None | 自定义坐标轴 |
| `title` | str | None | 自定义标题 |

#### 错误处理

```python
# 无效索引
plot_population_heatmap(result, atom_order=[10])
# ValueError: atom_order contains invalid indices: [10]. Valid range: 0-4

# 重复索引
plot_population_heatmap(result, atom_order=[0, 0, 1])
# ValueError: atom_order contains duplicate indices: [0]
```

---

### 5. 比特串分布可视化 (`result.py`)

**需求**: 基于 `SimulationResult.final_bitstring_distribution()` 绘制末态比特串概率分布；支持 TopK 筛选、排序、约化基禁戒比特串过滤、基模式标签。

**实现位置**: [`sagittarius/viz/result.py`](sagittarius_py/sagittarius/viz/result.py) - `plot_bitstring_distribution()`

#### 核心 API

```python
from sagittarius.viz import plot_bitstring_distribution
from sagittarius import load_result
def plot_bitstring_distribution(
    result,  # 必填：SimulationResult，必须实现final_bitstring_distribution()方法获取概率字典
    top_k: int = 10,  # 可选，默认10：仅展示概率最高前K个比特态，其余截断舍弃
    ax: Optional[Axes] = None,  # 可选，默认None：外部自定义子图，不传新建(12,6)画布
    sort_by: str = 'probability',  # 可选，默认probability：排序规则，probability降序 / bitstring字典升序
    title: Optional[str] = None,  # 可选，默认None：自定义标题；空则自动拼接基矢、禁态、总概率信息
    bar_color: str = 'steelblue',  # 可选，默认steelblue：柱状填充色
    show_values: bool = True,  # 可选，默认True：柱子顶部显示概率小数数值
    show_basis_info: bool = True,  # 可选，默认True：右上角文本框展示基矢模式、禁比特态数量
) -> Axes:


# 直接绘图
result = sim.run(...)
ax = plot_bitstring_distribution(result, top_k=8)

# 从文件加载
result = load_result("simulation.json")
ax = plot_bitstring_distribution(result, show_basis_info=True)

# 自定义排序
ax = plot_bitstring_distribution(result, sort_by='bitstring')
```

#### 功能特性

 **TopK 筛选**
- `top_k` 参数控制显示数量
- 自动标注 "top K of N unique"

 **双排序模式**
- `sort_by='probability'`: 按概率降序（默认）
- `sort_by='bitstring'`: 按比特串字典序

 **基模式标签** ⭐ 新增
- 自动从 `result.metadata` 提取基模式
- 标题显示 "Full Basis" 或 "Reduced Basis"
- 显示禁戒比特串数量（如 "12 forbidden states excluded")

 **信息框展示**
```
Basis: Reduced
Forbidden: 12
```

 **兼容 load_result()**
- 自动从保存的文件提取元数据
- 无需手动传递基模式信息

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | SimulationResult | - | 仿真结果对象 |
| `top_k` | int | 10 | 显示前 K 个比特串 |
| `sort_by` | str | 'probability' | 排序方式 |
| `show_basis_info` | bool | True | 显示基模式信息 |
| `bar_color` | str | 'steelblue' | 柱状图颜色 |
| `show_values` | bool | True | 显示概率值 |
| `ax` | Axes | None | 自定义坐标轴 |
| `title` | str | None | 自定义标题 |

#### 标题示例

**缩减基模式**:
```
Final Bitstring Distribution (top 4)
Reduced Basis
12 forbidden states excluded
Total probability: 0.9000
```

**全基模式**:
```
Final Bitstring Distribution (top 4)
Full Basis
Total probability: 0.9000
```

---

### 6. 测量采样直方图可视化 (`result.py`)

**需求**: 读取 measurement-samples/v1 采样输出，绘制带随机种子的测量次数直方图；支持计数/频率双模式、采样次数展示、随机种子元数据。

**实现位置**: [`sagittarius/viz/result.py`](sagittarius_py/sagittarius/viz/result.py) - `plot_shot_histogram()`

#### 核心 API

```python
from sagittarius.viz import plot_shot_histogram
from sagittarius import load_result

def plot_shot_histogram(
    result,  # 必填：SimulationResult，存在samples采样数组属性
    ax: Optional[Axes] = None,  # 可选，默认None：外部子图，不传新建(12,6)画布
    top_k: int = 20,  # 可选，默认20：展示采样次数最多前K种比特串
    normalize: bool = False,  # 可选，默认False：True归一化为频率0~1，False显示原始测量次数
    title: Optional[str] = None,  # 可选，默认None：自定义标题；空自动填充总shots、随机种子
    bar_color: str = 'coral',  # 可选，默认coral：柱状填充色
    show_seed_info: bool = True,  # 可选，默认True：右上角文本框展示随机种子、总采样数、计数模式
) -> Axes:

# 基础用法
result = sim.run(...)
result.sample(shots=1000, seed=42)
ax = plot_shot_histogram(result)

# 频率模式
ax = plot_shot_histogram(result, normalize=True)

# 从文件加载（measurement-samples/v1）
result = load_result("simulation.json")
ax = plot_shot_histogram(result, show_seed_info=True)
```

#### 功能特性

 **measurement-samples/v1 支持**
- 从 `result.manifest` 或 `result.metadata` 提取种子信息
- 兼容保存的仿真产物文件

 **计数/频率双模式** ⭐
- `normalize=False`: 显示原始 shot count（默认）
- `normalize=True`: 显示归一化频率（总和为 1）

 **随机种子元数据** ⭐ 新增
- 标题显示 "Random seed: {seed}"
- 右上角信息框显示种子、采样次数、模式

 **统一比特串排序**
- 始终按计数降序排列
- Top-K 筛选后显示最重要状态

 **剩余比特串提示**
- 截断时标注未显示的比特串数量
- 右下角信息框显示 "Remaining: N"

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | SimulationResult | - | 仿真结果对象 |
| `top_k` | int | 20 | 显示前 K 个比特串 |
| `normalize` | bool | False | 归一化为频率 |
| `show_seed_info` | bool | True | 显示种子信息 |
| `bar_color` | str | 'coral' | 柱状图颜色 |
| `ax` | Axes | None | 自定义坐标轴 |
| `title` | str | None | 自定义标题 |

#### 信息框示例

```
Seed: 42
Shots: 1000
Mode: Count    (或 Frequency)
```

#### 标题示例

**带种子信息**:
```
Measurement Shot Histogram (top 4 of 8 unique)
Total shots: 90
Random seed: 42
```

**不带种子信息**:
```
Measurement Shot Histogram (top 4 of 8 unique)
Total shots: 90
```

---

### 7. MWIS 问题可视化工具 (`mwis_viz.py`) ⭐ 新增

**需求**: 提供可选工具，在寄存器布局上叠加目标比特串、权重、图边、约束冲突标记，适配实验流程与第 16 阶段基准测试；该绘图工具仅作展示，不直接生成优化性能相关结论。

**实现位置**: [`sagittarius/viz/mwis_viz.py`](sagittarius_py/sagittarius/viz/mwis_viz.py)

#### 设计目标

专为 Maximum Weighted Independent Set (MWIS) 问题设计的可视化工具集，用于：
- **实验流程演示**: 直观展示优化解的质量和约束满足情况
- **Phase 16 基准测试**: 对比不同算法（AQC、Greedy、SA等）的求解效果
- **约束验证**: 快速识别违反阻塞约束的原子对
- **Artifact追踪**: 通过artifact ID链接到governed benchmark artifacts
- **性能指标嵌入**: 在图表中直接显示TTS、成功率等关键指标

**重要声明**: 本模块仅用于可视化展示，不直接生成优化性能结论。性能声明需要governed benchmark artifacts支持（参见SPEC-GOV-001）。

#### 核心 API

##### 7.1 `plot_mwis_problem()` - MWIS 问题单图可视化

```python
from sagittarius.viz import plot_mwis_problem

def plot_mwis_problem(
    register,  # 【必填】量子寄存器实例
    bitstring: str,  # 【必填】二进制字符串表示独立集解，'1'=选中，'0'=未选中
    weights: Optional[List[float]] = None,  # 【可选，默认=None】节点权重列表，长度需匹配原子数
    edges: Optional[List[Tuple[int, int]]] = None,  # 【可选，默认=None】图边列表，为空时从blockade_radius自动推导
    blockade_radius: Optional[float] = None,  # 【可选，默认=None】阻塞半径(μm)，用于自动推导边
    show_weights: bool = True,  # 【可选，默认=True】是否显示权重标签
    show_edges: bool = True,  # 【可选，默认=True】是否绘制图边
    highlight_conflicts: bool = True,  # 【可选，默认=True】是否高亮约束冲突
    conflict_color: str = 'red',  # 【可选，默认='red'】冲突标记颜色
    edge_color: str = 'gray',  # 【可选，默认='gray'】边颜色
    weight_fontsize: int = 8,  # 【可选，默认=8】权重字体大小
    ax: Optional[Axes] = None,  # 【可选，默认=None】外部子图，不传新建10×10画布
    title: Optional[str] = None,  # 【可选，默认=None】自定义标题，为空自动生成含统计信息的标题
    algorithm_name: Optional[str] = None,  # 【新增，默认=None】算法名称（如"AQC"、"Greedy"），嵌入标题
    performance_metrics: Optional[Dict[str, float]] = None,  # 【新增，默认=None】性能指标字典（如{"tts": 2.35, "p_success": 0.85}）
    artifact_id: Optional[str] = None,  # 【新增，默认=None】Benchmark artifact ID，用于可追溯性
) -> Axes:
```

**功能特性**:

✅ **比特串状态映射**
- '1' → 激发态（深橙色 #FF8C00）
- '0' → 基态（钢蓝色 #4682B4）
- 自动添加图例说明

✅ **权重标签显示**
- 每个原子旁显示权重值（如 "w=1.25"）
- 淡黄色背景框增强可读性
- zorder=11 确保在最顶层

✅ **图边渲染**
- 实线灰色表示正常边
- 虚线红色表示冲突边（两端均为'1'）
- 可自定义颜色和样式

✅ **冲突检测与标记**
- 自动检测相邻原子同时为'1'的违规情况
- 红色 X 标记标注冲突位置
- 标题和注释中显示冲突数量

✅ **智能标题生成** ⭐ Phase 16增强
- **基础模式**: "MWIS Solution: 3 atoms selected, No conflicts (Weight: 4.50)"
- **带算法名**: "AQC | 3 atoms selected | TTS=2.35s"
- **带Artifact**: 标题下方显示 "Artifact: mwis-bench-n16-d0.5-seed42"
- **完整示例**: 
  ```
  AQC | 3 atoms selected | TTS=2.35s
  Artifact: mwis-bench-n16-d0.5-seed42
  ```

✅ **性能指标嵌入** ⭐ Phase 16增强
- `performance_metrics` 参数支持嵌入TTS、成功率、运行时等
- 支持的键: `tts`, `p_success`, `runtime`, `ratio` 等
- 自动格式化为易读文本

✅ **Artifact追踪** ⭐ Phase 16增强
- `artifact_id` 参数链接到governed benchmark artifacts
- 符合SPEC-GOV-001性能声明治理要求
- 确保结果可追溯到原始数据和commit SHA

**使用示例**:

```python
from sagittarius import Register
from sagittarius.viz import plot_mwis_problem, annotate_solution_quality

# 创建寄存器
reg = Register.chain(5, spacing=4.0, C6=1.0)

# 定义 MWIS 问题
bitstring = "10101"
weights = [1.2, 0.8, 1.5, 0.9, 1.1]
edges = [(0, 1), (1, 2), (2, 3), (3, 4)]

# ========== 基础用法 ==========
fig, ax = plt.subplots(figsize=(12, 6))
plot_mwis_problem(
    reg,
    bitstring=bitstring,
    weights=weights,
    edges=edges,
    blockade_radius=5.0,
    ax=ax,
    title="Greedy Algorithm Solution"
)

# ========== Phase 16增强用法 ==========
fig, ax = plt.subplots(figsize=(12, 6))
plot_mwis_problem(
    reg,
    bitstring=bitstring,
    weights=weights,
    edges=edges,
    blockade_radius=5.0,
    algorithm_name="AQC",  # 算法名称
    performance_metrics={  # 性能指标
        "tts": 2.35,
        "p_success": 0.85,
        "runtime": 1.8
    },
    artifact_id="mwis-bench-n16-d0.5-seed42-aqc",  # Artifact ID
    ax=ax
)

# 添加质量注释
annotate_solution_quality(ax, bitstring, weights, edges)
plt.savefig("mwis_aqc_benchmark.png", dpi=150, bbox_inches='tight')
```

##### 7.2 `plot_mwis_comparison()` - 多解对比可视化

```python
from sagittarius.viz import plot_mwis_comparison

def plot_mwis_comparison(
    register,  # 【必填】量子寄存器实例
    bitstrings: List[str],  # 【必填】多个候选解的比特串列表
    titles: Optional[List[str]] = None,  # 【可选，默认=None】子图标题列表
    weights: Optional[List[float]] = None,  # 【可选，默认=None】共享权重
    edges: Optional[List[Tuple[int, int]]] = None,  # 【可选，默认=None】共享边
    blockade_radius: Optional[float] = None,  # 【可选，默认=None】阻塞半径
    figsize: Tuple[int, int] = (16, 6),  # 【可选，默认=(16,6)】画布尺寸
    algorithm_names: Optional[List[str]] = None,  # 【新增，默认=None】算法名称列表
    performance_metrics_list: Optional[List[Dict[str, float]]] = None,  # 【新增，默认=None】性能指标列表
    artifact_ids: Optional[List[str]] = None,  # 【新增，默认=None】Artifact ID列表
) -> List[Axes]:
```

**功能特性**:

✅ **并排对比**
- 支持 2-N 个解决方案的同时展示
- 统一的视觉风格便于比较

✅ **自动布局**
- 根据解的数量自动调整子图宽度
- 保持 aspect='equal' 确保圆形原子

✅ **灵活标题**
- 可自定义每个子图的标题
- 或通过`algorithm_names`自动生成

✅ **元数据验证** ⭐ Phase 16增强
- 自动检查`algorithm_names`、`performance_metrics_list`、`artifact_ids`长度
- 不匹配时抛出清晰的`ValueError`

**使用示例**:

```
# ========== 基础用法 ==========
axes = plot_mwis_comparison(
    reg,
    bitstrings=["10101", "01010", "10001"],
    titles=["AQC Solution", "Greedy Baseline", "Simulated Annealing"],
    weights=[1.2, 0.8, 1.5, 0.9, 1.1],
    edges=[(0,1), (1,2), (2,3), (3,4)],
    blockade_radius=5.0,
    figsize=(24, 8)
)

# ========== Phase 16增强用法 ==========
axes = plot_mwis_comparison(
    reg,
    bitstrings=[aqc_sol, greedy_sol, sa_sol],
    algorithm_names=["AQC", "Greedy", "SA"],
    performance_metrics_list=[
        {"tts": 2.35, "p_success": 0.85},
        {"ratio": 0.92, "runtime": 0.01},
        {"tts": 1.80, "p_success": 0.78}
    ],
    artifact_ids=["mwis-aqc-n16", "mwis-greedy-n16", "mwis-sa-n16"],
    weights=[1.2, 0.8, 1.5, 0.9, 1.1],
    edges=[(0,1), (1,2), (2,3), (3,4)],
    blockade_radius=5.0,
    figsize=(28, 8)
)

# 为每个子图添加质量注释
for ax, bs in zip(axes, [aqc_sol, greedy_sol, sa_sol]):
    annotate_solution_quality(ax, bs, weights, edges)

plt.tight_layout()
plt.savefig("algorithm_comparison.png", dpi=150, bbox_inches='tight')
```

##### 7.3 `annotate_solution_quality()` - 解质量注释

```python
from sagittarius.viz import annotate_solution_quality

def annotate_solution_quality(
    ax: Axes,  # 【必填】要注释的坐标轴
    bitstring: str,  # 【必填】解的比特串
    weights: Optional[List[float]] = None,  # 【可选，默认=None】权重列表
    edges: Optional[List[Tuple[int, int]]] = None,  # 【可选，默认=None】边列表
    text_position: Tuple[float, float] = (0.02, 0.98),  # 【可选，默认=(0.02,0.98)】注释位置（归一化坐标）
    fontsize: int = 10,  # 【可选，默认=10】字体大小
    include_approximation_ratio: bool = False,  # 【新增，默认=False】是否显示近似比
    optimal_weight: Optional[float] = None,  # 【新增，默认=None】最优解权重（用于计算近似比）
) -> None:
```

**功能特性**:

✅ **关键指标展示**
- 选中原子数 / 总原子数
- 总权重值
- 冲突数量
- 有效性判定（✓ Valid IS 或 ✗ N violations）

✅ **近似比计算** ⭐ Phase 16增强
- `include_approximation_ratio=True` 显示相对于最优解的比值
- 格式: "Approx ratio: 0.923"
- 需要提供`optimal_weight`参数

✅ **颜色编码**
- 绿色文本: 有效独立集（无冲突）
- 红色文本: 存在约束违例

✅ **灵活定位**
- 使用 axes 坐标系（0-1 范围）
- 默认左上角，可自定义位置

**使用示例**:

```
# ========== 基础用法 ==========
ax = plot_mwis_problem(reg, bitstring="10101", weights=w, edges=e)
annotate_solution_quality(ax, "10101", weights=w, edges=e)

# ========== Phase 16增强用法（带近似比）==========
ax = plot_mwis_problem(reg, bitstring="10101", weights=w, edges=e)
annotate_solution_quality(
    ax, 
    "10101", 
    weights=w, 
    edges=e,
    include_approximation_ratio=True,
    optimal_weight=15.5  # ILP最优解权重
)
# 输出示例:
# Atoms selected: 3/5
# Total weight: 14.35
# Approx ratio: 0.926
# Conflicts: 0
# ✓ Valid IS
```

##### 7.4 `save_mwis_benchmark_figure()` - Benchmark图表保存 ⭐ 新增

```python
from sagittarius.viz import save_mwis_benchmark_figure

def save_mwis_benchmark_figure(
    fig,  # 【必填】Matplotlib Figure对象
    output_path: str,  # 【必填】输出文件路径（PNG/PDF/SVG）
    metadata: Dict[str, Any],  # 【必填】Benchmark元数据字典
    dpi: int = 150,  # 【可选，默认=150】图像分辨率
    save_metadata_sidecar: bool = True,  # 【可选，默认=True】是否保存JSON sidecar
) -> None:
```

**功能特性**:

✅ **自动化Artifact管理**
- 保存图像文件（PNG/PDF/SVG）
- 自动生成JSON元数据sidecar
- 符合`benchmark-artifact/v1` schema

✅ **元数据丰富**
- 自动添加timestamp
- 记录image path和dpi
- 支持任意自定义字段

✅ **Governance合规**
- 包含schema_version标识
- 支持commit_sha追踪
- 链接到原始benchmark数据

**使用示例**:

```
from sagittarius.viz import save_mwis_benchmark_figure

# 创建图表
fig, ax = plt.subplots(figsize=(12, 12))
plot_mwis_problem(
    register,
    bitstring=solution,
    weights=weights,
    edges=edges,
    algorithm_name="AQC",
    performance_metrics={"tts": 2.35, "p_success": 0.85},
    artifact_id="mwis-bench-n16-d0.5-seed42",
    ax=ax
)

# 定义元数据
metadata = {
    "artifact_id": "mwis-bench-n16-d0.5-seed42",
    "schema_version": "benchmark-artifact/v1",
    "algorithm": "AQC",
    "n_atoms": 16,
    "density": 0.5,
    "seed": 42,
    "weights_mode": "random",
    "solution_bitstring": solution,
    "performance": {
        "tts": 2.35,
        "p_success": 0.85,
        "runtime": 1.8
    },
    "backend": "CUDA",
    "solver_method": "Tsit5",
    "commit_sha": "abc123def456...",
    "timestamp": "2026-07-07T01:00:00Z"
}

# 保存（自动生成 .png + .json）
save_mwis_benchmark_figure(
    fig,
    "mwis_result.png",
    metadata,
    dpi=150
)
# 输出:
# Saved figure: mwis_result.png
# Saved metadata: mwis_result.json
```

#### 视觉元素层级 (Z-order)

| Z-order | 元素 | 说明 |
|---------|------|------|
| 0 | 阻塞圆盘 | 背景层（如果启用） |
| 1 | 图边 | 灰色实线或红色虚线（冲突） |
| 2 | 冲突标记 | 红色 X 符号 |
| 5 | 原子散点 | 主要数据点 |
| 10 | 原子索引标签 | 黑色背景白色文字 |
| 11 | 权重标签 | 黄色背景深绿色文字 |

#### 冲突检测逻辑

```python
# 遍历所有边 (i, j)
for i, j in edges:
    if bitstring[i] == '1' and bitstring[j] == '1':
        # 相邻原子同时被选中 → 冲突
        conflicts.append((i, j))
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `register` | Register | - | 量子寄存器对象 |
| `bitstring` | str | - | 二进制解字符串 |
| `weights` | List[float] | None | 节点权重 |
| `edges` | List[Tuple[int,int]] | None | 图边列表 |
| `blockade_radius` | float | None | 阻塞半径 |
| `show_weights` | bool | True | 显示权重标签 |
| `show_edges` | bool | True | 显示图边 |
| `highlight_conflicts` | bool | True | 高亮冲突 |
| `conflict_color` | str | 'red' | 冲突颜色 |
| `edge_color` | str | 'gray' | 边颜色 |
| `weight_fontsize` | int | 8 | 权重大小 |
| `ax` | Axes | None | 自定义坐标轴 |
| `title` | str | None | 自定义标题 |

#### 错误处理

```python
# 比特串长度不匹配
plot_mwis_problem(reg, bitstring="101010")  
# ValueError: Bitstring length (6) does not match number of atoms (5)

# 无效字符
plot_mwis_problem(reg, bitstring="10a01")  
# ValueError: Bitstring must contain only '0' and '1'

# 权重数量不匹配
plot_mwis_problem(reg, bitstring="10101", weights=[1.0, 2.0])  
# ValueError: Weights length (2) does not match number of atoms (5)
```

#### 典型应用场景

**场景 1: Phase 16基准测试对比** ⭐ 增强
```
# 对比 AQC vs 经典算法，嵌入性能指标和artifact追踪
bitstrings = [aqc_sol, greedy_sol, sa_sol, cplex_sol]
algo_names = ["AQC", "Greedy", "SA", "CPLEX"]
perf_metrics = [
    {"tts": 2.35, "p_success": 0.85},
    {"ratio": 0.92, "runtime": 0.01},
    {"tts": 1.80, "p_success": 0.78},
    {"weight": 14.5, "runtime": 0.5}
]
artifact_ids = [
    "mwis-aqc-n16-d0.5-seed42",
    "mwis-greedy-n16-d0.5-seed42",
    "mwis-sa-n16-d0.5-seed42",
    "mwis-cplex-n16-d0.5-seed42"
]

axes = plot_mwis_comparison(
    register,
    bitstrings=bitstrings,
    algorithm_names=algo_names,
    performance_metrics_list=perf_metrics,
    artifact_ids=artifact_ids,
    weights=weights,
    edges=edges,
    blockade_radius=R,
    figsize=(32, 8)
)

# 添加质量注释
for ax, bs in zip(axes, bitstrings):
    annotate_solution_quality(ax, bs, weights, edges)

# 保存为benchmark artifact
metadata = {
    "artifact_id": "mwis-benchmark-n16-d0.5-seed42",
    "schema_version": "benchmark-artifact/v1",
    "algorithms_compared": algo_names,
    "n_atoms": 16,
    "density": 0.5,
    "seed": 42
}
save_mwis_benchmark_figure(plt.gcf(), "benchmark_comparison.png", metadata)
```

**场景 2: 约束验证与可行性分析**
```python
# 快速检查实验结果是否满足约束
fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# 可行解
plot_mwis_problem(
    register,
    bitstring=feasible_result,
    weights=weights,
    edges=edges,
    highlight_conflicts=True,
    algorithm_name="Feasible",
    ax=axes[0]
)
annotate_solution_quality(axes[0], feasible_result, weights, edges)

# 不可行解（有冲突）
plot_mwis_problem(
    register,
    bitstring=infeasible_result,
    weights=weights,
    edges=edges,
    highlight_conflicts=True,
    conflict_color='red',
    algorithm_name="Infeasible",
    ax=axes[1]
)
annotate_solution_quality(axes[1], infeasible_result, weights, edges)

plt.suptitle("Feasibility Analysis", fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig("feasibility_check.png", dpi=150, bbox_inches='tight')
```

**场景 3: 带近似比的解质量评估** ⭐ Phase 16增强
```
# 评估启发式算法相对于最优解的质量
optimal_weight = 15.5  # ILP求得的最优解权重

ax = plot_mwis_problem(
    register,
    bitstring=heuristic_solution,
    weights=weights,
    edges=edges,
    algorithm_name="Greedy",
    performance_metrics={"runtime": 0.01}
)

annotate_solution_quality(
    ax, 
    heuristic_solution, 
    weights, 
    edges,
    include_approximation_ratio=True,
    optimal_weight=optimal_weight
)
# 输出:
# Atoms selected: 4/5
# Total weight: 14.35
# Approx ratio: 0.926
# Conflicts: 0
# ✓ Valid IS
```

**场景 4: 出版物质量图表**
```
# 生成论文级别的可视化
fig, ax = plt.subplots(figsize=(10, 10))
plot_mwis_problem(
    optimal_register,
    bitstring=optimal_solution,
    weights=weights,
    edges=edges,
    show_weights=True,
    show_edges=True,
    highlight_conflicts=False,  # 最优解无冲突
    ax=ax,
    title="Optimal MWIS Solution (Weight = 12.45)"
)
plt.savefig("mwis_optimal.pdf", dpi=300, bbox_inches='tight')
```

**场景 5: Scaling Study可视化** ⭐ Phase 16增强
```
# 展示不同规模问题的求解结果
sizes = [8, 12, 16, 20]
fig, axes = plt.subplots(1, len(sizes), figsize=(32, 8))

for idx, n in enumerate(sizes):
    reg = create_register(n)
    sol = solve_mwis(reg)
    
    plot_mwis_problem(
        reg,
        bitstring=sol,
        weights=weights,
        edges=edges,
        algorithm_name=f"AQC (N={n})",
        performance_metrics={"runtime": 0.1 * n},
        ax=axes[idx]
    )
    
    annotate_solution_quality(axes[idx], sol, weights, edges)

plt.suptitle(f"Scaling Study: N={', '.join(map(str, sizes))}", 
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig("scaling_study.png", dpi=150, bbox_inches='tight')
```

#### 技术要点

- **Backend-Free**: 纯 NumPy + Matplotlib 实现，不触发 Julia 初始化
- **输入验证**: 全面的长度、字符集、维度检查
- **优先级处理**: `bitstring` 参数优先于其他高亮方式
- **一致性**: 遵循项目可视化规范（zorder、aspect ratio、颜色方案）
- **可扩展性**: 支持任意规模的寄存器和图结构

#### 测试覆盖

测试文件: [`tests/test_viz_mwis.py`](sagittarius_py/tests/test_viz_mwis.py)

| 测试类别 | 测试数 | 覆盖内容 |
|---------|--------|---------|
| 基本功能 | 5 | 基础绘图、无边权重、自动边推导、冲突检测 |
| 输入验证 | 4 | 长度 mismatch、无效字符、权重维度 |
| 视觉定制 | 4 | 自定义颜色、字体大小、隐藏元素 |
| 对比绘图 | 4 | 2/3/N 解对比、标题 mismatch |
| 注释功能 | 4 | 有效/无效解、无权重、自定义位置 |
| 集成测试 | 7 | Chain/Grid 布局、全基/全激、图例、标题 |
| **Phase 16增强** | **7** | **算法名称、artifact ID、性能指标、近似比、sidecar保存、元数据验证、完整工作流** |
| **总计** | **35** | **✅ 100% 通过 (4.83s)** |

**Phase 16新增测试**:
- `test_plot_mwis_with_algorithm_name` - 算法名称嵌入
- `test_plot_mwis_with_artifact_id` - Artifact ID追踪
- `test_plot_mwis_comparison_with_metadata` - 对比图元数据
- `test_annotate_with_approximation_ratio` - 近似比标注
- `test_save_mwis_benchmark_figure` - Sidecar保存与元数据验证
- `test_plot_mwis_comparison_metadata_validation` - 元数据列表长度验证
- `test_benchmark_workflow_integration` - 完整benchmark工作流集成

运行测试:
```bash
cd sagittarius_py
uv run pytest tests/test_viz_mwis.py -v
# ============================== 35 passed in 4.83s ==============================
```

#### 示例脚本

**基础示例**: [`examples/mwis_viz_demo.py`](sagittarius_py/examples/mwis_viz_demo.py)

```bash
uv run python examples/mwis_viz_demo.py
```

生成 4 个示例图片:
- `mwis_example_basic.png` - 基础 MWIS 可视化
- `mwis_example_conflicts.png` - 冲突检测演示
- `mwis_example_comparison.png` - 多解对比
- `mwis_example_2d_grid.png` - 2D 网格布局

**Phase 16基准测试示例**: [`examples/mwis_benchmark_example.py`](sagittarius_py/examples/mwis_benchmark_example.py) ⭐ 新增

```bash
uv run python examples/mwis_benchmark_example.py
```

生成 4 个benchmark场景示例（含JSON元数据sidecar）:
- `example_1_aqc_solution.png` + `.json` - 单算法结果+完整元数据
- `example_2_algorithm_comparison.png` + `.json` - 多算法对比（AQC vs Greedy vs SA）
- `example_3_feasibility.png` - 可行解vs不可行解分析
- `example_4_scaling.png` - Scaling study (N=8, 12, 16)

每个示例都展示了Phase 16增强的核心功能：
- ✅ 算法名称嵌入
- ✅ 性能指标显示（TTS、成功率等）
- ✅ Artifact ID追踪
- ✅ JSON元数据sidecar自动生成
- ✅ 近似比计算
- ✅ 完整benchmark工作流集成

---

### 10. 关联分析可视化工具 (`correlation_viz.py`) ⭐ 新增

**需求**: 支持成对关联、连通关联、Pauli-ZZ 关联、阻塞冲突矩阵/边热图绘制；仅当结果包含匹配可观测量序列与元数据时生效，缺失数据输出可定位问题的诊断提示。

**实现位置**: [`sagittarius/viz/correlation_viz.py`](sagittarius_py/sagittarius/viz/correlation_viz.py)

#### 设计目标

提供四种关联分析可视化工具，用于探索量子模拟结果中的空间关联模式：
- **成对关联**: `<n_i n_j>` 联合激发概率
- **连通关联**: `C_ij = <n_i n_j> - <n_i><n_j>` 真实关联（去除独立贡献）
- **Pauli-ZZ关联**: `<ZZ>_ij` 计算基下的自旋-自旋关联
- **阻塞冲突**: 阻塞违例概率矩阵或边热图

**重要声明**: 本模块仅用于数据探索和诊断，不直接生成性能结论。

#### 核心 API

##### 10.1 `plot_pair_correlation_matrix()` - 成对关联矩阵

```python
from sagittarius.viz import plot_pair_correlation_matrix

def plot_pair_correlation_matrix(
    result,  # 【必填】SimulationResult，包含 pair_corr_i_j 列
    register=None,  # 【可选】Register对象（暂未使用，保留接口）
    ax: Optional[Axes] = None,  # 【可选】外部子图
    figsize: Tuple[float, float] = (8, 8),  # 【可选】画布尺寸
    cmap: str = 'viridis',  # 【可选】色图名称
    show_values: bool = True,  # 【可选】标注数值
    title: Optional[str] = None,  # 【可选】自定义标题
    save_path: Optional[str] = None,  # 【可选】保存路径
) -> Axes:
```

**必需数据格式**:
```python
result.data = {
    't': [...],
    'pair_corr_0_1': [0.0, 0.3, 0.45],  # 原子0和1的成对关联
    'pair_corr_0_2': [0.0, 0.1, 0.15],
    'pair_corr_1_2': [0.0, 0.2, 0.25],
}
```

**视觉特性**:
- NxN对称矩阵热图（viridis色图，范围[0, 1]）
- 对角线填充单原子布居值（如可用）
- 单元格数值标注（两位小数，智能对比度）
- 标题显示关联对数量

**诊断提示**:
```python
ValueError: No PairCorrelation observables found in result.
Available columns: ['t', 'pop0', 'pop1'].
To enable PairCorrelation plots, include PairCorrelation in simulation observables.
Example:
    observables = {
        "pair_corr_0_1": PairCorrelation(atom_i=0, atom_j=1, N_atoms=N),
        "pair_corr_1_2": PairCorrelation(atom_i=1, atom_j=2, N_atoms=N),
    }
```

##### 10.2 `plot_connected_correlation_matrix()` - 连通关联矩阵

```python
from sagittarius.viz import plot_connected_correlation_matrix

def plot_connected_correlation_matrix(
    result,  # 【必填】SimulationResult，包含 connected_corr_i_j 列
    register=None,
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    cmap: str = 'coolwarm',  # 【可选】发散色图
    show_values: bool = True,
    significance_threshold: float = 0.1,  # 【可选】显著性阈值
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
```

**必需数据格式**:
```python
result.data = {
    'connected_corr_0_1': [0.0, 0.05, 0.12],  # C_01 = <n0 n1> - <n0><n1>
    'connected_corr_0_2': [0.0, -0.02, 0.03],
    'connected_corr_1_2': [0.0, 0.08, 0.15],
}
```

**视觉特性**:
- 发散色图（coolwarm），零值居中
- 正负对称颜色范围
- 仅标注显著关联（|C_ij| > threshold）
- 标题显示显著关联对数量

##### 10.3 `plot_pauli_zz_matrix()` - Pauli-ZZ关联矩阵

```python
from sagittarius.viz import plot_pauli_zz_matrix

def plot_pauli_zz_matrix(
    result,  # 【必填】SimulationResult，包含 pauli_zz_i_j 列
    register=None,
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    cmap: str = 'RdBu_r',  # 【可选】红蓝发散色图
    show_values: bool = True,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
```

**必需数据格式**:
```python
result.data = {
    'pauli_zz_0_1': [1.0, 0.6, 0.4],  # <ZZ>_01
    'pauli_zz_0_2': [1.0, 0.8, 0.7],
    'pauli_zz_1_2': [1.0, 0.5, 0.3],
}
```

**视觉特性**:
- 红蓝发散色图（RdBu_r），范围[-1, 1]
- 对角线固定为+1（自关联）
- 全量数值标注

##### 10.4 `plot_blockade_conflict_heatmap()` - 阻塞冲突热图

```python
from sagittarius.viz import plot_blockade_conflict_heatmap

def plot_blockade_conflict_heatmap(
    result,  # 【必填】SimulationResult，包含 blockade_violation_i_j 列
    register=None,  # 【可选】用于自动推导边
    edges: Optional[List[Tuple[int, int]]] = None,  # 【可选】显式边列表
    blockade_radius: Optional[float] = None,  # 【可选】阻塞半径
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    mode: str = 'matrix',  # 【可选】'matrix' 或 'edges'
    cmap: str = 'Reds',
    show_values: bool = True,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
```

**必需数据格式**:
```python
result.data = {
    'blockade_violation_0_1': [0.0, 0.15, 0.25],  # P(both excited)
    'blockade_violation_0_2': [0.0, 0.05, 0.08],
    'blockade_violation_1_2': [0.0, 0.12, 0.18],
}
```

**两种模式**:

1. **Matrix模式**: NxN冲突概率矩阵
   - 红色色图，范围[0, 1]
   - 高亮高频冲突对

2. **Edges模式**: 沿边的冲突频率水平条形图
   - 按冲突概率降序排列
   - 适合稀疏图可视化
   - 需要`edges`参数或`register + blockade_radius`

**视觉特性**:
- 矩阵模式：对称热力图
- 边模式：排序条形图，红色渐变
- 仅标注显著冲突（> 0.01）

#### 分层隔离原则

1. **只读访问**: 所有函数仅读取`result.data`，不修改原始数据
2. **诊断导向**: 错误消息明确指出缺失的observable类型和修复示例
3. **无性能声明**: 图表标题仅显示数据统计特征，不包含优化结论
4. **Artifact链接**: 如`result.manifest`包含`artifact_id`，在副标题中显示

#### zorder层级

| Z-order | 元素 | 说明 |
|---------|------|------|
| 0 | 背景网格 | 辅助线 |
| 1 | 热力图单元格 | imshow图像 |
| 5 | 数值标注文本 | 白色/黑色智能对比 |
| 10 | 原子索引标签 | （如有register布局） |
| 11 | 冲突标记 | X符号（边模式） |

#### 使用示例

```python
from sagittarius.viz import (
    plot_pair_correlation_matrix,
    plot_connected_correlation_matrix,
    plot_pauli_zz_matrix,
    plot_blockade_conflict_heatmap,
)

# 单独绘制
ax1 = plot_pair_correlation_matrix(result, save_path="pair_corr.png")
ax2 = plot_connected_correlation_matrix(result, significance_threshold=0.05)
ax3 = plot_pauli_zz_matrix(result)
ax4 = plot_blockade_conflict_heatmap(result, mode='matrix')
ax5 = plot_blockade_conflict_heatmap(result, mode='edges', edges=[(0,1), (1,2)])

# 组合仪表板
fig, axes = plt.subplots(2, 2, figsize=(16, 16))
plot_pair_correlation_matrix(result, ax=axes[0, 0])
plot_connected_correlation_matrix(result, ax=axes[0, 1])
plot_pauli_zz_matrix(result, ax=axes[1, 0])
plot_blockade_conflict_heatmap(result, mode='matrix', ax=axes[1, 1])
plt.suptitle("Correlation Analysis Dashboard")
plt.tight_layout()
plt.savefig("correlation_dashboard.png", dpi=150)
```

#### 测试覆盖

- ✅ 18个单元测试涵盖4种关联类型
- ✅ 正常数据、缺失数据、元数据不匹配场景
- ✅ 诊断提示的可读性和可操作性验证
- ✅ 集成测试验证多面板组合
- ✅ 无回归问题（202个可视化测试全部通过）

---

## 🧪 测试覆盖

### 测试文件组织

```
tests/
 test_viz_register.py                  # Register 可视化测试
 test_viz_pulse.py                     # Pulse 可视化测试
 test_viz_result.py                    # Result 可视化测试
```

### 运行测试

```bash
cd /workspaces/Sagittarius/sagittarius_py
uv run pytest tests/test_viz_result.py -v
```

### 测试统计

| 模块 | 测试数 | 状态 |
|------|--------|------|
| `plot_observables` | 4 | ✅ 全部通过 |
| `plot_bitstring_distribution` | 6 | ✅ 全部通过 |
| `plot_shot_histogram` | 7 | ✅ 全部通过 |
| `plot_population_heatmap` | 8 | ✅ 全部通过 |
| 综合测试 | 1 | ✅ 全部通过 |
| **总计** | **26** | **✅ 100%** |

### 关键测试场景

#### plot_population_heatmap
- ✅ 基础热图绘制
- ✅ 自定义颜色映射
- ✅ 隐藏颜色条
- ✅ 缺失列错误处理
- ✅ **自定义原子排序**
- ✅ **无效索引检测**
- ✅ **重复索引检测**

#### plot_bitstring_distribution
- ✅ 基础分布绘图
- ✅ 概率排序
- ✅ 显示概率值
- ✅ 空分布错误处理
- ✅ **基模式信息显示**
- ✅ **隐藏基模式信息**

#### plot_shot_histogram
- ✅ 基础直方图
- ✅ 归一化频率
- ✅ Top-K 筛选
- ✅ 无样本错误处理
- ✅ 空样本错误处理
- ✅ **种子信息显示**
- ✅ **隐藏种子信息**

---

## 💡 使用最佳实践

### 1. 选择合适的可视化工具

| 场景 | 推荐函数 | 说明 |
|------|---------|------|
| 查看原子布局 | `plot_register()` | 二维排布 + 阻塞关联 |
| 分析脉冲形状 | `plot_pulse_waveform()` | Ω/Δ 波形采样 |
| 追踪演化轨迹 | `plot_observables()` | 多观测量时序 |
| 分析布居动力学 | `plot_population_heatmap()` | 原子-时间热图 |
| 查看末态分布 | `plot_bitstring_distribution()` | 概率分布柱状图 |
| 统计采样结果 | `plot_shot_histogram()` | 测量计数直方图 |

### 2. 自定义绘图流程

```python
import matplotlib.pyplot as plt
from sagittarius.viz import plot_observables, plot_population_heatmap

result = sim.run(...)

# 创建多子图布局
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 子图 1: 可观测量轨迹
plot_observables(result, ax=axes[0, 0], names=["pop0", "pop1"])
axes[0, 0].set_title("Population Evolution")

# 子图 2: 布居热图
plot_population_heatmap(result, ax=axes[0, 1], atom_order=[4, 2, 0, 3, 1])
axes[0, 1].set_title("Population Heatmap")

# 子图 3: 比特串分布
plot_bitstring_distribution(result, ax=axes[1, 0], top_k=5)
axes[1, 0].set_title("Bitstring Distribution")

# 子图 4: 采样直方图
plot_shot_histogram(result, ax=axes[1, 1], normalize=True)
axes[1, 1].set_title("Shot Histogram (Normalized)")

plt.tight_layout()
plt.savefig("comprehensive_analysis.png", dpi=150)
```

### 3. 从保存的文件加载

```python
from sagittarius import load_result
from sagittarius.viz import plot_bitstring_distribution, plot_shot_histogram

# 加载仿真结果
result = load_result("simulation_result.json")

# 自动提取元数据（基模式、种子等）
ax1 = plot_bitstring_distribution(result, show_basis_info=True)
ax2 = plot_shot_histogram(result, show_seed_info=True)

plt.show()
```

### 4. 错误处理与诊断

```python
try:
    ax = plot_population_heatmap(result)
except ValueError as e:
    print(f"诊断信息: {e}")
    # 输出: No population columns found. Available columns: ['t', 'energy']
    
    # 检查仿真配置
    print("可用列:", result.to_pandas().columns.tolist())
```

---

## 🔧 技术架构

### 模块依赖关系

```
sagittarius/viz/
 __init__.py              # 导出公共 API
 register.py              # Register 可视化
   ├── plot_register()
   └── plot_interaction_graph()
 pulse.py                 # Pulse 波形可视化
   └── plot_pulse_waveform()
 result.py                # Result 结果可视化
    ├── plot_observables()
    ├── plot_bitstring_distribution()
    ├── plot_shot_histogram()
    └── plot_population_heatmap()
```

### 设计原则

1. **Backend-Free**: 所有可视化函数仅依赖 NumPy + Matplotlib，不触发 Julia 初始化
2. **元数据感知**: 自动从 `result.metadata` 和 `result.manifest` 提取上下文信息
3. **返回 Axes 对象**: 所有函数返回 `matplotlib.axes.Axes`，支持进一步定制
4. **向后兼容**: 保持现有 API 行为，新功能通过可选参数启用
5. **清晰诊断**: 错误时提供明确的修复建议和可用选项

### 性能优化

- **向量化操作**: 利用 NumPy 广播机制避免 Python 循环
- **延迟渲染**: 仅在需要时创建 Figure/Axes
- **高效数据结构**: 使用 `pd.Series` 和 `np.unique` 加速统计计算
- **缓存友好**: 避免重复计算距离矩阵、邻接表等

---
