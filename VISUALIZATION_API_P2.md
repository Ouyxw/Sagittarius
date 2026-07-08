### 13. 基准性能分析可视化工具 (`benchmark_perf.py`) 

**需求**: 基于受管控基准产物生成标准化图表,包含运行耗时-原子数曲线、内存占用-基维度曲线、CPU/GPU计算误差对比、求解器性能横向对比、运行成功/失败汇总。仅读取官方基准产物或留存实验数据,性能结论需遵循管控规范(SPEC-GOV-001),不可直接将本地临时计时作为官方性能依据。

**实现位置**: [`sagittarius/viz/benchmark_perf.py`](sagittarius_py/sagittarius/viz/benchmark_perf.py)

#### 设计目标

- **性能趋势分析**: 运行时和内存随问题规模的缩放规律
- **求解器对比**: 不同数值方法的性能横向比较
- **成功率统计**: 基准测试成功/失败分布可视化
- **硬件对比**: CPU vs GPU数值精度差异分析
- **合规性保证**: 所有图表包含免责声明,不直接作为硬件校准依据

**重要声明**: 
- ⚠️ **DIAGNOSTIC VIEW - Not for hardware calibration**
- 性能结论必须遵循SPEC-GOV-001管控规范
- 本地临时计时不得作为官方性能证据
- 仅读取受管控的基准产物或已验证的实验数据

#### 核心 API

##### 13.1 `plot_runtime_scaling()` - 运行耗时缩放分析

```python
from sagittarius.viz import plot_runtime_scaling

def plot_runtime_scaling(
    artifacts: List[Dict[str, Any]],  # 【必填】基准产物列表
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (10, 6),  # 【可选,默认=(10,6)】画布尺寸
    show_fit: bool = True,  # 【可选,默认=True】显示幂律拟合曲线
) -> Axes:
```

**功能特性**:

 **幂律缩放拟合**
- 主图: 散点图展示runtime vs n_atoms
- 拟合曲线: T ∝ N^b (对数空间线性拟合)
- 统计摘要: 缩放指数b、前置因子a

**数据结构要求**:
```python
artifacts = [
    {
        'n_atoms': int,           # 原子数量
        'runtime_seconds': float, # 墙钟时间(秒)
        'artifact_id': str        # 唯一标识符
    },
    ...
]
```

**使用示例**:
```python
artifacts = [load_artifact(f"bench_{n}.json") for n in [5, 10, 15, 20]]
ax = plot_runtime_scaling(artifacts, show_fit=True)
plt.savefig("runtime_scaling.png", dpi=150)
```

##### 13.2 `plot_memory_scaling()` - 内存占用缩放分析

```python
from sagittarius.viz import plot_memory_scaling

def plot_memory_scaling(
    artifacts: List[Dict[str, Any]],  # 【必填】基准产物列表
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (10, 6),  # 【可选,默认=(10,6)】画布尺寸
    y_unit: str = 'MB',  # 【可选,默认='MB']内存单位('B','KB','MB','GB')
) -> Axes:
```

**功能特性**:

 **指数增长可视化**
- X轴: Hilbert空间维度(对数刻度)
- Y轴: 内存占用(可配置单位)
- 半对数坐标展示指数增长趋势

**数据结构要求**:
```python
artifacts = [
    {
        'hilbert_dim': int,      # Hilbert空间维度(2^n)
        'memory_bytes': int,     # 峰值内存(字节)
        'artifact_id': str       # 唯一标识符
    },
    ...
]
```

##### 13.3 `plot_solver_comparison()` - 求解器性能对比

```python
from sagittarius.viz import plot_solver_comparison

def plot_solver_comparison(
    results: List[Dict[str, Any]],  # 【必填】求解器结果列表
    metric: str = 'runtime',  # 【可选,默认='runtime'】对比指标
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (12, 6),  # 【可选,默认=(12,6)】画布尺寸
    show_error_bars: bool = True,  # 【可选,默认=True】显示误差棒
) -> Axes:
```

**功能特性**:

 **横向条形图对比**
- 水平条形图展示各求解器性能
- 自动排序(最优者置顶)
- 误差棒显示标准差(如提供)
- ★标记最佳性能者

**支持指标**: `'runtime'`, `'accuracy'`, `'memory'`, `'error'`

**数据结构要求**:
```python
results = [
    {
        'solver_name': str,      # 求解器名称
        'metric_value': float,   # 指标值
        'metric_std': float,     # 标准差(可选)
        'artifact_id': str       # 唯一标识符
    },
    ...
]
```

##### 13.4 `plot_success_failure_summary()` - 成功/失败汇总

```python
from sagittarius.viz import plot_success_failure_summary

def plot_success_failure_summary(
    benchmark_runs: List[Dict[str, Any]],  # 【必填】基准运行记录
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (10, 8),  # 【可选,默认=(10,8)】画布尺寸
    group_by: str = 'solver',  # 【可选,默认='solver'】分组维度
) -> Axes:
```

**功能特性**:

 **堆叠条形图统计**
- 成功(绿色) + 失败(红色)堆叠
- 百分比标注在条形中央
- 总体成功率文本框
- 支持按solver/n_atoms/problem_type分组

**数据结构要求**:
```python
benchmark_runs = [
    {
        'status': str,           # 'success' 或 'failure'
        'solver': str,           # 求解器名称
        'n_atoms': int,          # 问题规模
        'error_message': str,    # 失败原因(可选)
        'artifact_id': str       # 唯一标识符
    },
    ...
]
```

##### 13.5 `plot_cpu_gpu_error_comparison()` - CPU/GPU误差对比

```python
from sagittarius.viz import plot_cpu_gpu_error_comparison

def plot_cpu_gpu_error_comparison(
    cpu_results: List[Dict[str, Any]],  # 【必填】CPU结果
    gpu_results: List[Dict[str, Any]],  # 【必填】GPU结果
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (12, 6),  # 【可选,默认=(12,6)】画布尺寸
    error_metric: str = 'relative_error',  # 【可选,默认='relative_error'】误差类型
) -> Axes:
```

**功能特性**:

 **分组条形图对比**
- CPU(蓝色) vs GPU(紫色)并排对比
- Y轴对数刻度展示误差量级
- 平均GPU/CPU比率标注
- 支持相对误差/绝对误差

**支持误差类型**: `'relative_error'`, `'absolute_error'`

**数据结构要求**:
```python
cpu_results = [
    {
        'observable': str,        # 可观测量名称
        'value': float,           # 计算值
        'reference_value': float  # 参考值(高精度或解析解)
    },
    ...
]
# gpu_results结构相同
```

#### 测试覆盖

:
```bash
cd sagittarius_py && uv run pytest tests/test_viz_benchmark_perf.py -v
# ============================== 18 passed in 0.69s ==============================
```

**测试用例**:
- ✅ 正常数据: 完整基准产物、有效指标值
- ✅ 缺失字段: n_atoms/runtime_seconds/hilbert_dim等必需字段
- ✅ 无效参数: 不支持的内存单位、无共同可观测量
- ✅ 边界情况: <3个数据点跳过拟合、零参考值处理
- ✅ Artifact链接: artifact_id字段存在性检查

#### 示例脚本

 [`examples/benchmark_perf_demo.py`](sagittarius_py/examples/benchmark_perf_demo.py),演示:
- 运行耗时缩放分析(6个基准点,幂律拟合)
- 内存占用缩放分析(5个维度,KB单位)
- 求解器性能对比(4种方法,带误差棒)
- 成功/失败汇总(按solver和n_atoms分组)
- CPU/GPU误差对比(4个可观测量)

::::::
- `benchmark_runtime_scaling.png` - 运行耗时缩放曲线
- `benchmark_memory_scaling.png` - 内存占用缩放曲线
- `benchmark_solver_comparison.png` - 求解器横向对比
- `benchmark_success_failure_solver.png` - 按求解器分组的成功率
- `benchmark_success_failure_size.png` - 按问题规模分组的成功率
- `benchmark_cpu_gpu_comparison.png` - CPU/GPU数值精度对比

---

### 14. 小型系统调试视图 (`small_system_debug.py`) 

**需求**: 提供低维希尔伯特空间的量子态诊断视图,包括态概率矢量、密度矩阵对角元、密度矩阵幅值热图、相位热图。明确限定仅适用于≤10量子比特系统,数据缺失或维度过大时抛出清晰报错。

**实现位置**: [`sagittarius/viz/small_system_debug.py`](sagittarius_py/sagittarius/viz/small_system_debug.py)

#### 设计目标

EOFEOF,用于:
- **态矢量分析**: 计算基态概率分布可视化
- **密度矩阵诊断**: 占据数(diagonal)和相干性(off-diagonal)分析
- **相位结构**: 复数相干性的相位模式识别
- **非物理态检测**: 负占据数、迹≠1等异常自动警告
- **维度安全限制**: >1024维(>10 qubits)时拒绝可视化

**重要声明**: 
- ⚠️ **仅限小系统**: MAX_SAFE_DIM = 1024 (2^10 qubits)
- ⚠️ **DIAGNOSTIC VIEW - Not for hardware calibration**
- 超维系统将抛出ValueError并提示替代方案
- 非物理态会触发UserWarning但不阻止绘图

#### 核心 API

##### 14.1 `plot_state_probabilities()` - 态概率矢量

```python
from sagittarius.viz import plot_state_probabilities

def plot_state_probabilities(
    state_vector: Union[List[complex], np.ndarray],  # 【必填】态矢量|ψ⟩
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (12, 6),  # 【可选,默认=(12,6)】画布尺寸
    show_labels: bool = True,  # 【可选,默认=True】显示二进制标签
    basis: str = 'computational',  # 【可选,默认='computational'】基底类型
) -> Axes:
```

**功能特性**:

 **概率分布柱状图**
- 高概率态(>0.01)用深色,低概率态用浅色
- X轴二进制标签(|00⟩, |01⟩, ..., |11⟩)
- 统计摘要: 非零态数、最大概率态
- 自动归一化警告(如Σ|ψ_i|² ≠ 1)

**输入验证**:
- 必须为1D数组
- 维度必须为2的幂(2^n)
- 维度 ≤ 1024 (10 qubits)

**使用示例**:
```python
# Bell state: (|00⟩ + |11⟩) / √2
psi = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
ax = plot_state_probabilities(psi, show_labels=True)
plt.savefig("bell_state_probs.png", dpi=150)
```

**错误处理**:
```python
ValueError: State vector dimension 3 is not a power of 2. Expected dimension 2^n for n qubits.
# 解决方案: 确保态矢量维度为2的幂

ValueError: Hilbert space dimension 2048 exceeds safe limit (1024). This corresponds to more than 11 qubits.
# 解决方案: 仅支持≤10 qubits系统,考虑使用稀疏表示或降维可观测量

UserWarning: State vector not normalized: Σ|ψ_i|^2 = 0.500000. Probabilities will be normalized for visualization.
# 说明: 态矢量未归一化,将自动归一化后绘图
```

##### 14.2 `plot_density_matrix_diagonal()` - 密度矩阵对角元

```python
from sagittarius.viz import plot_density_matrix_diagonal

def plot_density_matrix_diagonal(
    density_matrix: Union[List[List[complex]], np.ndarray],  # 【必填】密度矩阵ρ
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (12, 6),  # 【可选,默认=(12,6)】画布尺寸
    normalize: bool = True,  # 【可选,默认=True】归一化对角元
) -> Axes:
```

**功能特性**:

 **占据数(Population)可视化**
- 柱状图展示ρ_ii (i=0,...,dim-1)
- 高占据态用深色标记
- 统计摘要: 非零占据数、最大占据态、对角纯度
- 负占据数警告(非物理态)

**输入验证**:
- 必须为2D方阵
- 维度必须为2的幂
- 维度 ≤ 1024

**使用示例**:
```python
# Maximally mixed state: ρ = I/2
rho = np.array([[0.5, 0], [0, 0.5]])
ax = plot_density_matrix_diagonal(rho, normalize=True)
plt.savefig("mixed_state_diagonal.png", dpi=150)
```

##### 14.3 `plot_density_matrix_magnitude()` - 密度矩阵幅值热图

```python
from sagittarius.viz import plot_density_matrix_magnitude

def plot_density_matrix_magnitude(
    density_matrix: Union[List[List[complex]], np.ndarray],  # 【必填】密度矩阵ρ
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (10, 8),  # 【可选,默认=(10,8)】画布尺寸
    cmap: str = 'viridis',  # 【可选,默认='viridis'】色图
    show_values: bool = False,  # 【可选,默认=False】标注数值(仅dim≤16)
) -> Axes:
```

**功能特性**:

 **热力图**
- 完整密度矩阵幅值可视化
- 对角线红色虚线标记(populations)
- 可选数值标注(仅小系统dim≤16)
- Colorbar显示幅值范围

**视觉特性**:
- viridis色图(从紫到黄)
- 对角线zorder=10红色虚线
- 小系统(dim≤32)显示二进制标签

**使用示例**:
```python
# Pure state |+⟩⟨+| with coherences
psi = np.array([1/np.sqrt(2), 1/np.sqrt(2)])
rho = np.outer(psi, psi.conj())
ax = plot_density_matrix_magnitude(rho, show_values=True)
plt.savefig("pure_state_magnitude.png", dpi=150)
```

##### 14.4 `plot_density_matrix_phase()` - 密度矩阵相位热图

```python
from sagittarius.viz import plot_density_matrix_phase

def plot_density_matrix_phase(
    density_matrix: Union[List[List[complex]], np.ndarray],  # 【必填】密度矩阵ρ
    ax: Optional[Axes] = None,  # 【可选,默认=None】外部子图
    title: Optional[str] = None,  # 【可选,默认=None】自定义标题
    figsize: Tuple[float, float] = (10, 8),  # 【可选,默认=(10,8)】画布尺寸
    cmap: str = 'twilight',  # 【可选,默认='twilight'】循环色图
    threshold: float = 1e-3,  # 【可选,默认=1e-3】掩蔽阈值
) -> Axes:
```

**功能特性**:

 **arg(ρ_ij)相位热力图**
- 相位范围[-π, π]用twilight循环色图
- 小幅值元素(|ρ_ij| < threshold)被掩蔽
- 白色对角线标记
- 掩蔽元素数量统计

**视觉特性**:
- twilight色图(适合循环相位数据)
- Colorbar标注-π到π刻度
- 灰色文本框显示掩蔽元素数

**使用示例**:
```python
# Density matrix with complex coherences
rho = np.array([
    [0.5, 0.1*np.exp(1j*np.pi/4)],
    [0.1*np.exp(-1j*np.pi/4), 0.5]
])
ax = plot_density_matrix_phase(rho, threshold=1e-3)
plt.savefig("density_matrix_phase.png", dpi=150)
```

#### 维度安全限制

**MAX_SAFE_DIM = 1024** (对应10 qubits)

```python
_validate_hilbert_dimension(dim, context="visualization")
# 如果 dim > 1024, 抛出:
# ValueError: Hilbert space dimension {dim} exceeds safe limit (1024).
#             This corresponds to more than {n_qubits} qubits.
#             Visualization is only supported for small systems (≤ 10 qubits).
#             Consider using sparse representations or reduced observable sets for larger systems.
```

#### 分层隔离原则

1. **只读访问**: 所有函数仅读取态矢量/密度矩阵数据,不修改原始对象
2. **非校准声明**: 所有图表标题/角落包含"DIAGNOSTIC VIEW - Not for hardware calibration"
3. **元数据分离**: 可视化不修改原始量子态数据,仅展示特征
4. **小系统限定**: 明确标注适用系统规模,避免误用于大规模系统

#### zorder 层级

| Z-order | 元素 | 说明 |
|---------|------|------|
| 0 | 背景网格 | 辅助线(alpha=0.3) |
| 5 | 柱状图/热力图 | 主要数据可视化 |
| 10 | 对角线/统计文本 | 参考线和标注 |
| 11 | 免责声明 | 黄色背景红色文字 |

#### 测试覆盖

:
```bash
cd sagittarius_py && uv run pytest tests/test_viz_small_system_debug.py -v
# ============================== 19 passed in 0.52s ==============================
```

**测试用例**:
- ✅ 正常数据: Bell态、GHZ态、混合态、纯态
- ✅ 维度验证: 非2的幂、超大维度(2048)、多维数组
- ✅ 非物理态: 负占据数、迹≠1、未归一化态矢量
- ✅ 边界情况: dim=1024(边界)、dim=1025(超限)
- ✅ 可选参数: show_labels、normalize、show_values、threshold

#### 示例脚本

 [`examples/small_system_debug_demo.py`](sagittarius_py/examples/small_system_debug_demo.py),演示:
- Bell态概率分布(2 qubits)
- GHZ态概率分布(3 qubits)
- 最大混合态对角元(1 qubit)
- 纯态|+⟩幅值和相位热图
- 复杂相干性相位结构(2 qubits)
- 维度限制错误处理(11 qubits → 2048维)
- 非物理态警告检测(负占据数)

::::::
- `debug_bell_state_probabilities.png` - Bell态势概率
- `debug_ghz_state_probabilities.png` - GHZ态势概率
- `debug_mixed_state_diagonal.png` - 混合态对角元
- `debug_pure_state_magnitude.png` - 纯态幅值热图
- `debug_pure_state_phase.png` - 纯态相位热图
- `debug_complex_coherences_magnitude.png` - 复杂相干性幅值
- `debug_complex_coherences_phase.png` - 复杂相干性相位

---