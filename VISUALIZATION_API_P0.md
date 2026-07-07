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
