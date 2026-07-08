
### 7. MWIS 问题可视化工具 (`mwis_viz.py`) 

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
    algorithm_name: Optional[str] = None,  # 【默认=None】算法名称（如"AQC"、"Greedy"），嵌入标题
    performance_metrics: Optional[Dict[str, float]] = None,  # 【默认=None】性能指标字典（如{"tts": 2.35, "p_success": 0.85}）
    artifact_id: Optional[str] = None,  # 【默认=None】Benchmark artifact ID，用于可追溯性
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

✅ **智能标题生成** 
- **基础模式**: "MWIS Solution: 3 atoms selected, No conflicts (Weight: 4.50)"
- **带算法名**: "AQC | 3 atoms selected | TTS=2.35s"
- **带Artifact**: 标题下方显示 "Artifact: mwis-bench-n16-d0.5-seed42"
- **完整示例**: 
  ```
  AQC | 3 atoms selected | TTS=2.35s
  Artifact: mwis-bench-n16-d0.5-seed42
  ```

✅ **性能指标嵌入** 
- `performance_metrics` 参数支持嵌入TTS、成功率、运行时等
- 支持的键: `tts`, `p_success`, `runtime`, `ratio` 等
- 自动格式化为易读文本

✅ **Artifact追踪** 
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

✅ **元数据验证** 
- 自动检查`algorithm_names`、`performance_metrics_list`、`artifact_ids`长度
- 不匹配时抛出清晰的`ValueError`

**使用示例**:

```python
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

✅ **近似比计算** 
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

```python
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

##### 7.4 `save_mwis_benchmark_figure()` - Benchmark图表保存 

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

```python
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

#### 技术要点

- **Backend-Free**: 纯 NumPy + Matplotlib 实现，不触发 Julia 初始化
- **输入验证**: 全面的长度、字符集、维度检查
- **优先级处理**: `bitstring` 参数优先于其他高亮方式
- **一致性**: 遵循项目可视化规范（zorder、aspect ratio、颜色方案）
- **可扩展性**: 支持任意规模的寄存器和图结构
- **标签偏移优化**: 原子索引和权重标签使用基于点的偏移量（offset points），确保在不同 DPI 和缩放比例下保持一致的视觉效果
- **布局管理**: `plot_mwis_comparison()` 内部使用 `subplots_adjust(wspace=0.3)` 而非 `tight_layout()`，避免复杂多子图场景下的布局警告

#### 测试

测试文件: [`tests/test_viz_mwis.py`](sagittarius_py/tests/test_viz_mwis.py)

运行测试:
```bash
cd sagittarius_py
uv run pytest tests/test_viz_mwis.py -v
# ============================== 35 passed in 4.83s ==============================
```

---

### 8. 比特串空间诊断工具 (`basis_diagnostics.py`) 

**需求**: 提供小型系统专用的调试工具，可视化有效比特串、禁戒比特串、全基/约化基维度、基截断比例，以及阻塞关联边和约化基有效性的关联关系；视图明确标注为诊断用途，严格遵循 Sagittarius 统一比特串排序规则。

**实现位置**: [`sagittarius/viz/basis_diagnostics.py`](sagittarius_py/sagittarius/viz/basis_diagnostics.py)

#### 设计目标

专为理解 Hilbert 空间结构和 Rydberg blockade 约束而设计的诊断工具集，用于：
- **小型系统分析**: N ≤ 10 原子的可管理规模（全基维度 ≤ 1024）
- **基空间可视化**: 直观展示全基 vs 约化基的维度差异
- **约束影响评估**: 量化 blockade 约束对状态空间的修剪效果
- **比特串分类**: 清晰区分有效态（valid）和禁戒态（forbidden）
- **阻塞图分析**: 可视化原子间阻塞约束的拓扑结构

**重要声明**: 
- ⚠️ **DIAGNOSTIC VIEW** - 仅用于小系统调试和理解基结构
- ⚠️ **N ≤ 10 限制** - 超过此规模会自动拒绝（全基维度爆炸）
- ⚠️ **升序整数排序** - 所有比特串严格按 integer value 升序排列（Sagittarius 规范）

#### 核心 API

##### 8.1 `generate_basis_diagnostics()` - 生成诊断数据

```python
from sagittarius.viz import generate_basis_diagnostics

def generate_basis_diagnostics(
    register,  # 【必填】量子寄存器实例
    blockade_radius: float,  # 【必填】阻塞半径(μm)，用于判定约束
    edges: Optional[List[Tuple[int, int]]] = None,  # 【可选，默认=None】预计算的阻塞边列表；None则自动推导
) -> Dict[str, Any]:
    """
    生成完整的基空间诊断数据
    
    Returns:
        Dictionary containing:
        - n_atoms: 原子数量
        - full_dimension: 全基维度 (2^N)
        - reduced_dimension: 约化基维度（有效态数量）
        - pruning_ratio: 修剪比例 (0 to 1)，表示被禁戒的状态占比
        - valid_states: 有效态的整数列表（升序）
        - forbidden_states: 禁戒态的整数列表（升序）
        - valid_bitstrings: 有效态的二进制字符串列表
        - forbidden_bitstrings: 禁戒态的二进制字符串列表
        - edges: 阻塞边列表 [(i, j), ...]
        - blockade_graph_density: 阻塞图密度 = |E| / (N*(N-1)/2)
    """
```

**功能特性**:

✅ **自动边推导**
- 基于原子坐标和 blockade_radius 计算距离矩阵
- 距离 < R_b 的原子对自动添加阻塞边

✅ **状态分类**
- 遍历所有 2^N 个可能状态
- 检查每个状态是否违反任何阻塞约束
- 相邻原子同时为 '1' → 禁戒态

✅ **严格排序**
- 所有状态按 integer value 升序排列
- 符合 Sagittarius 统一比特串排序规范

✅ **尺寸保护**
- N > 10 时抛出 `ValueError`
- 防止全基维度爆炸（2^11 = 2048 已较大）

**使用示例**:

```python
from sagittarius import Register
from sagittarius.viz import generate_basis_diagnostics

# 创建 4-atom chain
reg = Register.chain(4, spacing=0.6, C6=10.0)
blockade_radius = 1.0

# 生成诊断数据
diagnostics = generate_basis_diagnostics(reg, blockade_radius)

print(f"Atoms: {diagnostics['n_atoms']}")
print(f"Full dimension: {diagnostics['full_dimension']}")  # 16
print(f"Reduced dimension: {diagnostics['reduced_dimension']}")  # 8
print(f"Pruning ratio: {diagnostics['pruning_ratio']:.2%}")  # 50.00%
print(f"Blockade edges: {len(diagnostics['edges'])}")  # 3

# 查看有效态
print("\nValid bitstrings:")
for state, bs in zip(diagnostics['valid_states'], diagnostics['valid_bitstrings']):
    print(f"  State {state:2d}: {bs}")

# 查看禁戒态
print("\nForbidden bitstrings:")
for state, bs in zip(diagnostics['forbidden_states'], diagnostics['forbidden_bitstrings']):
    print(f"  State {state:2d}: {bs}")
```

输出示例:
```
Atoms: 4
Full dimension: 16
Reduced dimension: 8
Pruning ratio: 50.00%
Blockade edges: 3

Valid bitstrings:
  State  0: 0000
  State  1: 0001
  State  2: 0010
  State  4: 0100
  State  5: 0101
  State  8: 1000
  State  9: 1001
  State 10: 1010

Forbidden bitstrings:
  State  3: 0011  ← atoms 2,3 both excited
  State  6: 0110  ← atoms 1,2 both excited
  State  7: 0111  ← multiple violations
  State 11: 1011  ← atoms 2,3 both excited
  State 12: 1100  ← atoms 0,1 both excited
  State 13: 1101  ← atoms 0,1 both excited
  State 14: 1110  ← multiple violations
  State 15: 1111  ← all adjacent pairs violated
```

##### 8.2 `plot_basis_space_diagram()` - 维度分解柱状图

```python
from sagittarius.viz import plot_basis_space_diagram

def plot_basis_space_diagram(
    diagnostics: Dict[str, Any],  # 【必填】generate_basis_diagnostics() 的输出
    ax: Optional[Axes] = None,  # 【可选，默认=None】外部子图，不传新建(14,8)画布
    title: Optional[str] = None,  # 【可选，默认=None】自定义标题
    figsize: Tuple[float, float] = (14, 8),  # 【可选，默认=(14,8)】画布尺寸
) -> Axes:
```

**功能特性**:

✅ **三栏对比**
- Full Hilbert Space（钢蓝色）
- Reduced Basis（森林绿）
- Forbidden States（深红色）

✅ **对数刻度**
- y轴使用 log scale 便于观察大尺度差异
- 适合展示指数级增长的全基维度

✅ **统计信息框**
- 原子数量 N
- 修剪比例 pruning_ratio
- 阻塞边数量
- 图密度 graph_density

✅ **诊断标识**
- 底部红色警告文本："⚠️ DIAGNOSTIC VIEW — Small Systems Only (N ≤ 10)"

**使用示例**:

```python
import matplotlib.pyplot as plt
from sagittarius.viz import plot_basis_space_diagram

fig, ax = plt.subplots(figsize=(14, 8))
plot_basis_space_diagram(diagnostics, ax=ax, title="Basis Space Breakdown")
plt.savefig("basis_dimensions.png", dpi=150, bbox_inches='tight')
```

##### 8.3 `plot_bitstring_space_grid()` - 比特串空间网格

```python
from sagittarius.viz import plot_bitstring_space_grid

def plot_bitstring_space_grid(
    diagnostics: Dict[str, Any],  # 【必填】诊断数据
    ax: Optional[Axes] = None,  # 【可选，默认=None】外部子图
    title: Optional[str] = None,  # 【可选，默认=None】自定义标题
    max_display_states: int = 64,  # 【可选，默认=64】最大显示状态数（避免过度拥挤）
    figsize: Tuple[float, float] = (12, 10),  # 【可选，默认=(12,10)】画布尺寸
) -> Axes:
```

**功能特性**:

✅ **颜色编码**
- 🟢 绿色：有效态（在约化基中）
- 🔴 红色：禁戒态（违反阻塞约束）

✅ **升序排列**
- Y轴从上到下按 integer value 升序
- 严格遵循 Sagittarius 排序规范

✅ **智能截断**
- 状态数 > max_display_states 时只显示前 N 个
- 标题中标注 "(showing first X)"

✅ **图例说明**
- 右上角显示有效态和禁戒态的数量

**使用示例**:

```python
fig, ax = plt.subplots(figsize=(12, 10))
plot_bitstring_space_grid(
    diagnostics,
    ax=ax,
    max_display_states=32  # 只显示前32个状态
)
plt.savefig("bitstring_grid.png", dpi=150, bbox_inches='tight')
```

##### 8.4 `plot_blockade_constraint_graph()` - 阻塞约束图

```python
from sagittarius.viz import plot_blockade_constraint_graph

def plot_blockade_constraint_graph(
    diagnostics: Dict[str, Any],  # 【必填】诊断数据
    register,  # 【必填】寄存器对象（用于原子位置）
    ax: Optional[Axes] = None,  # 【可选，默认=None】外部子图
    title: Optional[str] = None,  # 【可选，默认=None】自定义标题
    figsize: Tuple[float, float] = (10, 10),  # 【可选，默认=(10,10)】画布尺寸
) -> Axes:
```

**功能特性**:

✅ **原子布局**
- 复用 `plot_register()` 的渲染逻辑
- 显示原子索引标签

✅ **阻塞边可视化**
- 红色虚线表示阻塞约束
- zorder=3 确保在原子之上可见

✅ **统计信息**
- 左上角黄色文本框显示关键指标
- 包含原子数、边数、图密度、修剪比例

✅ **图例说明**
- 右下角标注 "Blockade constraint"

**使用示例**:

```python
fig, ax = plt.subplots(figsize=(10, 10))
plot_blockade_constraint_graph(diagnostics, reg, ax=ax)
plt.savefig("constraint_graph.png", dpi=150, bbox_inches='tight')
```

##### 8.5 `plot_comprehensive_basis_diagnostics()` - 综合诊断面板

```python
from sagittarius.viz import plot_comprehensive_basis_diagnostics

def plot_comprehensive_basis_diagnostics(
    diagnostics: Dict[str, Any],  # 【必填】诊断数据
    register,  # 【必填】寄存器对象
    figsize: Tuple[float, float] = (18, 14),  # 【可选，默认=(18,14)】整体画布尺寸
    save_path: Optional[str] = None,  # 【可选，默认=None】保存路径（PNG/PDF/SVG）
) -> List[Axes]:
    """
    创建三合一综合诊断图
    
    Returns:
        List of 3 Axes objects: [dimensions_panel, grid_panel, constraint_panel]
    """
```

**功能特性**:

✅ **三面板布局**
1. **左面板**: 维度分解柱状图
2. **中面板**: 比特串空间网格
3. **右面板**: 阻塞约束图

✅ **统一标题**
- 顶部大标题: "Basis Space Diagnostics — N=X Atoms (DIAGNOSTIC VIEW)"

✅ **一键保存**
- `save_path` 参数直接保存为图片文件
- 支持 PNG/PDF/SVG 格式

**使用示例**:

```python
# 生成并保存综合诊断图
axes = plot_comprehensive_basis_diagnostics(
    diagnostics,
    reg,
    figsize=(18, 14),
    save_path="/tmp/basis_diagnostics.png"
)

# axes[0]: 维度分解
# axes[1]: 比特串网格
# axes[2]: 约束图
```

#### 视觉元素层级 (Z-order)

| Z-order | 元素 | 说明 |
|---------|------|------|
| 0 | 阻塞圆盘背景 | 如果启用（低透明度） |
| 1 | 阻塞边（红色虚线） | 约束关系 |
| 2 | 冲突标记 | （本模块暂不使用） |
| 5 | 原子散点 | 主要数据点 |
| 10 | 原子索引标签 | 黑色背景白色文字 |
| 11 | 权重标签 | （本模块暂不使用） |

#### 阻塞约束检测逻辑

```python
def _check_blockade_violation(state: int, edges: List[Tuple[int, int]]) -> bool:
    """检查状态是否违反阻塞约束"""
    for i, j in edges:
        # 检查两个原子是否同时处于激发态 (bit=1)
        if (state & (1 << i)) and (state & (1 << j)):
            return True  # 违反约束
    return False  # 有效状态
```

**示例**: 对于边 (1, 2) 和状态 `0110` (binary):
- Atom 1: bit=1 (excited) ✓
- Atom 2: bit=1 (excited) ✓
- → **Violation!** 状态 `0110` 被禁戒

#### 错误处理

```python
# 系统过大
reg_large = Register.chain(11, spacing=0.5)
generate_basis_diagnostics(reg_large, blockade_radius=1.0)
# ValueError: Basis diagnostics limited to N ≤ 10 atoms for tractability. Got 11 atoms (full dimension would be 2048).

# 数据不一致
bad_diagnostics = {
    'n_atoms': 3,
    'full_dimension': 8,
    'valid_bitstrings': ['000', '001'],  # 只有2个
    'forbidden_bitstrings': ['010'],  # 只有1个
    # ... 其他字段
}
plot_basis_space_diagram(bad_diagnostics)
# ValueError: Inconsistent state counts: 2 valid + 1 forbidden ≠ 8 total
```


#### 技术要点

- **Backend-Free**: 纯 NumPy + Matplotlib 实现，不触发 Julia 初始化
- **输入验证**: 全面的尺寸、一致性、字符合法性检查
- **严格排序**: 所有比特串按 integer value 升序（Sagittarius 规范）
- **诊断标识**: 所有图表包含醒目的 ⚠️ 警告标记
- **资源管理**: 正确关闭 figure 避免内存泄漏
- **可扩展性**: 支持任意小规模寄存器（N ≤ 10）

#### 测试覆盖

测试文件: [`tests/test_viz_basis_diagnostics.py`](sagittarius_py/tests/test_viz_basis_diagnostics.py)

| 测试类别 | 测试数 | 覆盖内容 |
|---------|--------|---------|
| 数据生成 | 7 | 基础功能、自动边推导、无约束、全禁戒、尺寸保护、比特串格式、排序验证 |
| 维度图 | 4 | 基础绘图、对数刻度、自定义标题、警告文本 |
| 比特串网格 | 4 | 基础绘图、颜色编码、截断显示、排序验证 |
| 约束图 | 3 | 基础绘图、边可见性、统计框 |
| 综合面板 | 3 | 基础绘图、保存功能、总标题 |
| 集成测试 | 3 | 完整工作流、函数一致性、单原子边界 |
| 错误处理 | 1 | 不一致数据验证 |
| **总计** | **25** | **✅ 100% 通过 (3.56s)** |

运行测试:
```bash
cd sagittarius_py
uv run pytest tests/test_viz_basis_diagnostics.py -v
# ============================== 25 passed in 3.56s ==============================
```



#### 最佳实践

1. **何时使用**: 
   - 调试约化基仿真时
   - 理解 blockade 约束的影响
   - 教学演示 Hilbert 空间结构
   - 验证基生成的正确性

2. **何时不使用**:
   - N > 10 的大系统（会自动拒绝）
   - 生产环境的结果展示（应使用 `result.py`）
   - 性能基准测试（应使用 `mwis_viz.py`）

3. **组合使用**:
   ```python
   # 先用诊断工具理解基结构
   diag = generate_basis_diagnostics(reg, R_b)
   plot_comprehensive_basis_diagnostics(diag, reg)
   
   # 再运行仿真
   result = sim.run(...)
   
   # 最后用结果可视化工具展示
   result.plot_observables()
   result.plot_bitstring_distribution()
   ```

---

### 9. 几何参数校验工具 (`geometry_diagnostics.py`) ⭐ 新增

**需求**: 提供无后端依赖的绘图/数据提取工具，输出原子间距、范德华相互作用矩阵、阻塞邻接矩阵、单位圆盘叠加图；用于用户在高开销求解计算前，校验几何参数、单位、阻塞半径配置是否合理。

**实现位置**: [`sagittarius/viz/geometry_diagnostics.py`](sagittarius_py/sagittarius/viz/geometry_diagnostics.py)

#### 设计目标

**前置几何验证**设计的诊断工具集，用于在运行昂贵仿真前捕获配置错误：
- **快速校验**: 纯Python/NumPy实现，毫秒级响应
- **分层隔离**: 明确标注为诊断用途，不作为性能佐证
- **多维分析**: 距离矩阵、VDW强度、阻塞图、可视化叠加
- **数值标注**: 所有热力图均标注具体数值，便于精确分析

**重要声明**: 
- ⚠️ **DIAGNOSTIC VIEW ONLY** - 仅用于几何参数合理性检查
- ⚠️ **NOT FOR CALIBRATION** - 不得作为硬件校准依据
- ⚠️ **PRE-SIMULATION TOOL** - 应在仿真前使用，避免浪费计算资源

#### 核心 API

##### 9.1 `extract_geometry_diagnostics()` - 综合几何诊断数据提取

```python
from sagittarius.viz import extract_geometry_diagnostics

def extract_geometry_diagnostics(
    register,
    blockade_radius: Optional[float] = None,
    C6: Optional[float] = None,
) -> Dict[str, Any]:
    """
    从寄存器配置中提取几何诊断信息
    
    Args:
        register: Register对象（必需）
        blockade_radius: 阻塞半径(μm)，用于构建邻接矩阵
        C6: 范德华系数，用于计算相互作用矩阵
    
    Returns:
        Dictionary containing:
        - n_atoms: int - 原子数量
        - positions: np.ndarray - Nx2坐标数组
        - distance_matrix: np.ndarray - NxN距离矩阵(μm)
        - vdw_matrix: np.ndarray | None - VDW相互作用矩阵（如提供C6）
        - adjacency_matrix: np.ndarray | None - 二值邻接矩阵（如提供R_b）
        - edges: List[Tuple[int,int]] - 阻塞边列表
        - graph_density: float - 图密度 = |E| / (N*(N-1)/2)
        - min_distance: float - 最小原子间距
        - max_distance: float - 最大原子间距
        - mean_distance: float - 平均原子间距
    """
```

**使用示例**:
```python
from sagittarius import Register

reg = Register.chain(4, spacing=0.6)
diag = extract_geometry_diagnostics(reg, blockade_radius=1.0, C6=80.0)

print(f"原子数量: {diag['n_atoms']}")
print(f"最小间距: {diag['min_distance']:.3f} μm")
print(f"最大间距: {diag['max_distance']:.3f} μm")
print(f"阻塞边数: {len(diag['edges'])}")
print(f"图密度: {diag['graph_density']:.2%}")

print("\n距离矩阵:")
print(diag['distance_matrix'].round(2))
# [[0.   0.6  1.2  1.8 ]
#  [0.6  0.   0.6  1.2 ]
#  [1.2  0.6  0.   0.6 ]
#  [1.8  1.2  0.6  0.  ]]

print("\nVDW相互作用矩阵 (MHz):")
print(np.round(diag['vdw_matrix'], 2))
# [[   0.      1714.68    26.79     2.35]
#  [1714.68     0.      1714.68    26.79]
#  [  26.79   1714.68     0.      1714.68]
#  [   2.35     26.79   1714.68     0.  ]]
```

##### 9.2 `plot_geometry_diagnostics()` - 综合几何诊断可视化

```python
from sagittarius.viz import plot_geometry_diagnostics

def plot_geometry_diagnostics(
    register,
    blockade_radius: Optional[float] = None,
    C6: Optional[float] = None,
    show_distances: bool = False,
    show_vdw_matrix: bool = True,
    show_adjacency: bool = True,
    figsize: Tuple[float, float] = (16, 12),
    ax: Optional[Axes] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> List[Axes]:
    """
    创建多面板几何诊断可视化
    
    Panels:
        1. Register布局 + 阻塞圆盘 + 约束边
        2. 距离矩阵热力图（带数值标注）
        3. VDW相互作用矩阵热力图（带数值标注，如提供C6）
        4. 阻塞邻接矩阵热力图（带数值标注，如提供R_b）
    
    Visual Elements (zorder):
        - zorder=0: 阻塞圆盘背景（低透明度）
        - zorder=1: 阻塞边连线（虚线）
        - zorder=5: 原子散点
        - zorder=10: 原子索引标签
        - zorder=11: 距离标注文本（可选）
    
    Returns:
        List of Axes objects for each panel
    """
```

**使用示例**:
```python
import matplotlib.pyplot as plt
from sagittarius import Register

reg = Register.chain(4, spacing=0.6)

axes = plot_geometry_diagnostics(
    reg,
    blockade_radius=1.0,
    C6=80.0,
    show_distances=True,  # 在布局图上标注距离
    show_vdw_matrix=True,
    show_adjacency=True,
    figsize=(18, 14),
    title="4-Atom Chain - Geometry Diagnostics",
    save_path="geometry_diagnostics.png"
)

print(f"生成了 {len(axes)} 个面板")
# 输出: ✓ Geometry diagnostics saved to: geometry_diagnostics.png
#       生成了 4 个面板
```

**视觉特征**:
- **Panel 1**: 寄存器布局，钢蓝色原子，红色阻塞圆盘和虚线边
- **Panel 2**: 距离矩阵热力图（viridis色图），每个单元格标注距离值
- **Panel 3**: VDW矩阵热力图（hot色图，log尺度），标注科学计数法数值
- **Panel 4**: 邻接矩阵热力图（Reds色图），标注0/1整数
- **顶部标题**: "GEOMETRY DIAGNOSTICS — Pre-Simulation Validation"
- **警告标识**: "⚠️ FOR PARAMETER VALIDATION ONLY — Not for calibration"

**热力图数值标注特性**:
- ✅ **自动格式化**: 根据数值大小选择合适精度（.2f或.2e）
- ✅ **智能对比度**: 根据背景亮度自动选择白色或黑色文字
- ✅ **阈值过滤**: 邻接矩阵仅标注非零值，避免冗余
- ✅ **字体大小自适应**: 根据矩阵规模调整字号，避免拥挤

##### 9.3 `plot_unit_disk_graph()` - 简化单位圆盘图

```python
from sagittarius.viz import plot_unit_disk_graph

def plot_unit_disk_graph(
    register,
    blockade_radius: float,
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (10, 10),
    show_labels: bool = True,
    show_distances: bool = False,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
    """
    简化的单位圆盘图可视化，仅显示阻塞结构
    
    Visual Elements (zorder):
        - zorder=0: 橙色半透明阻塞圆盘
        - zorder=1: 红色虚线约束边
        - zorder=5: 钢蓝色原子散点
        - zorder=10: 黑底白字索引标签
        - zorder=11: 距离标注（可选）
    """
```

**使用示例**:
```python
ax = plot_unit_disk_graph(
    reg,
    blockade_radius=1.0,
    show_distances=True,
    show_labels=True,
    title=f"Unit Disk Graph (R_b = 1.0 μm)",
    save_path="unit_disk_graph.png"
)
```

**适用场景**:
- 快速预览阻塞结构
- 演示文稿中的简洁图示
- 教学材料中的概念展示


#### 测试覆盖

完整测试套件位于 [`tests/test_viz_geometry_diagnostics.py`](sagittarius_py/tests/test_viz_geometry_diagnostics.py)：

- ✅ **数据提取测试** (9个): 距离矩阵、VDW矩阵、邻接矩阵、边列表、统计量、边界情况
- ✅ **可视化测试** (7个): 基础绘图、VDW面板、完整面板、数值标注验证、自定义标题
- ✅ **集成测试** (3个): 完整工作流、一致性验证、多配置测试
- ✅ **总计**: 23个测试全部通过

运行测试:
```bash
cd sagittarius_py && uv run pytest tests/test_viz_geometry_diagnostics.py -v
# ============================== 23 passed in 5.60s ==============================
```

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

完整测试套件位于 [`tests/test_viz_correlation.py`](sagittarius_py/tests/test_viz_correlation.py)：

- ✅ **成对关联测试** (5个): 基础绘图、自定义标题、隐藏数值、缺失数据诊断、原子计数验证
- ✅ **连通关联测试** (3个): 基础绘图、显著性阈值过滤、缺失数据诊断
- ✅ **Pauli-ZZ测试** (3个): 基础绘图、对角线验证、缺失数据诊断
- ✅ **阻塞冲突测试** (5个): 矩阵模式、边模式、无效模式、无边错误、缺失数据诊断
- ✅ **集成测试** (2个): 四合一仪表板、错误消息可操作性验证
- ✅ **总计**: 18个测试全部通过

运行测试:
```
cd sagittarius_py && uv run pytest tests/test_viz_correlation.py -v
# ============================== 18 passed in 2.10s ==============================
```

#### 示例脚本

参考 [`examples/correlation_viz_demo.py`](sagittarius_py/examples/correlation_viz_demo.py)，演示：
- 4种关联类型的单独可视化
- 组合仪表板创建
- 诊断洞察输出

生成文件:
- `correlation_pair.png` - 成对关联矩阵
- `correlation_connected.png` - 连通关联矩阵
- `correlation_pauli_zz.png` - Pauli-ZZ矩阵
- `conflict_matrix.png` - 阻塞冲突矩阵
- `conflict_edges.png` - 阻塞冲突边热图
- `correlation_dashboard.png` - 综合仪表板

---

### 11. 空间快照与动画帧提取工具 (`spatial_snapshot.py`) ⭐ 新增

**需求**: 生成空间快照、多子图或可直接生成动画的标准化帧数据；按单/多输出时刻为原子着色，映射布居或指定可观测量数值。动画功能为可选扩展，但提取的帧数据格式稳定、兼容本地产物文件。

**实现位置**: [`sagittarius/viz/spatial_snapshot.py`](sagittarius_py/sagittarius/viz/spatial_snapshot.py)

#### 设计目标

提供从仿真结果中提取空间配置数据的工具集，用于：
- **单时刻快照**: 提取特定时间步的原子位置和可观测量值
- **动画帧序列**: 批量提取多个时间步的标准化帧数据
- **本地存储**: 将帧数据保存为JSON格式，兼容外部动画工具
- **颜色映射**: 根据可观测量值（如布居）为原子着色
- **分层隔离**: 只读访问result.data，不修改原始数据

**重要声明**: 
- ⚠️ **DIAGNOSTIC VIEW** - 仅用于数据探索和可视化
- ⚠️ **NOT FOR CALIBRATION** - 不得作为硬件校准依据
- ⚠️ **FRAME DATA ONLY** - 本模块仅提取帧数据，不直接生成动画视频

#### 核心 API

##### 11.1 `extract_spatial_snapshot()` - 提取单时刻空间快照

```python
from sagittarius.viz import extract_spatial_snapshot

def extract_spatial_snapshot(
    result,  # 【必填】SimulationResult对象
    register,  # 【必填】Register对象（提供原子位置）
    time_index: int,  # 【必填】时间步索引（0-based）
    observable_name: str = 'pop',  # 【可选】可观测量前缀（默认'pop'）
) -> Dict[str, Any]:
    """
    提取单个时间步的完整空间配置快照
    
    Returns:
        Dictionary containing:
        - n_atoms: int - 原子数量
        - time_index: int - 时间步索引
        - time_value: float - 实际时间值
        - positions: np.ndarray - Nx2坐标数组
        - observables: Dict[int, float] - 原子索引到可观测量值的映射
        - metadata: Dict - 元数据（register信息、可观测量类型等）
    """
```

**必需数据格式**:
```python
result.data = {
    't': [0.0, 0.1, 0.2, ...],
    'pop0': [1.0, 0.8, 0.6, ...],
    'pop1': [1.0, 0.7, 0.5, ...],
    'pop2': [1.0, 0.9, 0.7, ...],
}
```

**使用示例**:
```python
snapshot = extract_spatial_snapshot(result, reg, time_index=10)
print(f"t={snapshot['time_value']:.3f}s")
for idx, val in snapshot['observables'].items():
    pos = snapshot['positions'][idx]
    print(f"  Atom {idx} at ({pos[0]:.2f}, {pos[1]:.2f}): pop={val:.3f}")
```

**诊断提示**:
```python
ValueError: Time index 100 out of range [0, 49]. Result has 50 time steps.
# 解决方案：检查result.to_pandas()的长度，确保time_index在有效范围内

ValueError: No observable columns with prefix 'pop' found.
Available columns: ['t', 'energy'].
# 解决方案：使用正确的observable_name参数，如observable_name='energy'
```

##### 11.2 `extract_frame_sequence()` - 提取帧序列

```python
from sagittarius.viz import extract_frame_sequence

def extract_frame_sequence(
    result,
    register,
    time_indices: Optional[List[int]] = None,  # 【可选】自定义时间索引列表
    observable_name: str = 'pop',
    stride: int = 1,  # 【可选】自动采样步长（当time_indices=None时）
) -> List[Dict[str, Any]]:
    """
    提取多个时间步的快照序列，用于动画或多面板可视化
    
    Returns:
        List of snapshot dictionaries (see extract_spatial_snapshot)
    """
```

**使用示例**:
```python
# 方式1：自动采样（每5步提取一帧）
frames = extract_frame_sequence(result, reg, stride=5)
print(f"Extracted {len(frames)} frames")

# 方式2：自定义时间点
frames = extract_frame_sequence(
    result, reg, 
    time_indices=[0, 10, 20, 30, 40]
)
```

**诊断提示**:
```python
ValueError: Invalid time indices: [100]. Valid range: [0, 49]
# 解决方案：确保所有time_indices在有效范围内
```

##### 11.3 `save_frame_data()` - 保存帧数据到JSON

```python
from sagittarius.viz import save_frame_data

def save_frame_data(
    frames: List[Dict[str, Any]],
    output_path: str,
    format: str = 'json',  # 【可选】目前仅支持'json'
) -> None:
    """
    将帧数据保存为标准化的JSON格式
    
    JSON Schema:
    {
        "schema_version": "spatial-snapshot/v1",
        "frame_count": int,
        "frames": [
            {
                "n_atoms": int,
                "time_index": int,
                "time_value": float,
                "positions": [[x, y], ...],
                "observables": {"0": val, "1": val, ...},
                "metadata": {...}
            },
            ...
        ]
    }
    """
```

**使用示例**:
```python
frames = extract_frame_sequence(result, reg, stride=5)
save_frame_data(frames, "animation_frames.json")

# 验证JSON结构
import json
with open("animation_frames.json") as f:
    data = json.load(f)
print(f"Schema: {data['schema_version']}")
print(f"Frames: {data['frame_count']}")
```

**兼容性**:
- ✅ 标准JSON格式，可被任何JSON解析器读取
- ✅ 包含schema_version标识，便于版本管理
- ✅ numpy数组自动转换为列表，确保跨平台兼容
- ✅ 适合作为本地artifact存储或传递给外部动画工具

##### 11.4 `plot_spatial_snapshot()` - 绘制单时刻快照

```python
from sagittarius.viz import plot_spatial_snapshot

def plot_spatial_snapshot(
    snapshot: Dict[str, Any],
    ax: Optional[Axes] = None,
    figsize: Tuple[float, float] = (8, 8),
    cmap: str = 'viridis',  # 【可选】色图名称
    vmin: Optional[float] = None,  # 【可选】颜色范围最小值
    vmax: Optional[float] = None,  # 【可选】颜色范围最大值
    show_colorbar: bool = True,
    show_labels: bool = True,
    atom_size: int = 200,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Axes:
    """
    绘制空间快照，原子颜色映射可观测量值
    
    Visual Elements (zorder):
        - zorder=5: 原子散点（按可观测量着色）
        - zorder=10: 原子索引标签（白色文字）
    """
```

**视觉特性**:
- 原子位置散点图，颜色表示可观测量值
- 智能颜色范围（自动或手动设置vmin/vmax）
- 原子索引标签（白色粗体，居中显示）
- 可选颜色条图例
- aspect='equal'确保几何比例正确

**使用示例**:
```python
snapshot = extract_spatial_snapshot(result, reg, time_index=10)
ax = plot_spatial_snapshot(
    snapshot,
    cmap='plasma',
    title=f"Spatial Snapshot at t={snapshot['time_value']:.3f}",
    save_path="snapshot_t10.png"
)
plt.colorbar(ax.collections[0], label='Population')
```

##### 11.5 `plot_multi_panel_snapshots()` - 多面板快照对比

```python
from sagittarius.viz import plot_multi_panel_snapshots

def plot_multi_panel_snapshots(
    frames: List[Dict[str, Any]],
    panel_indices: Optional[List[int]] = None,  # 【可选】要显示的帧索引
    figsize_per_panel: Tuple[float, float] = (6, 6),
    cmap: str = 'viridis',
    vmin: Optional[float] = None,  # 【可选】全局统一颜色范围
    vmax: Optional[float] = None,
    show_colorbar: bool = False,
    suptitle: Optional[str] = None,
    save_path: Optional[str] = None,
) -> List[Axes]:
    """
    创建多面板可视化，对比不同时间步的空间状态
    
    Returns:
        List of Axes objects for each panel
    """
```

**视觉特性**:
- 2×2网格布局（最多4个面板）
- 全局统一颜色范围（便于跨时间对比）
- 可选共享颜色条
- 自定义总标题（suptitle）

**使用示例**:
```python
frames = extract_frame_sequence(result, reg, stride=10)
axes = plot_multi_panel_snapshots(
    frames,
    panel_indices=[0, 3, 6, 9],  # 显示第0,3,6,9帧
    cmap='viridis',
    show_colorbar=True,
    suptitle="Quantum State Evolution",
    save_path="evolution_multipanel.png"
)
```

**诊断提示**:
```python
ValueError: Panel indices [10, 15] exceed available frames (10). Valid range: [0, 9]
# 解决方案：确保panel_indices在可用帧数范围内
```

#### 分层隔离原则

1. **只读访问**: 所有函数仅读取`result.to_pandas()`，不修改原始数据
2. **标准化输出**: 帧数据采用固定JSON schema，便于长期存档和工具互操作
3. **无性能声明**: 图表标题仅显示时间和可观测量类型，不包含优化结论
4. **本地产物兼容**: JSON格式可直接作为benchmark artifact的一部分

#### zorder层级

| Z-order | 元素 | 说明 |
|---------|------|------|
| 0 | 背景网格 | 辅助线（alpha=0.4） |
| 5 | 原子散点 | 按可观测量着色，黑色边框 |
| 10 | 原子索引标签 | 白色粗体文字，居中对齐 |

#### 使用场景

1. **动画制作前置步骤**:
   ```python
   # 提取帧数据
   frames = extract_frame_sequence(result, reg, stride=2)
   save_frame_data(frames, "frames.json")
   
   # 使用外部工具（如ffmpeg、matplotlib.animation）生成视频
   # ffmpeg -i frames.json -vf "..." output.mp4
   ```

2. **时间演化对比**:
   ```python
   # 展示关键时间点的状态
   frames = extract_frame_sequence(result, reg, stride=5)
   plot_multi_panel_snapshots(
       frames, panel_indices=[0, 5, 10, 15],
       suptitle="Rabi Oscillation Evolution"
   )
   ```

3. **本地artifact归档**:
   ```python
   # 保存仿真结果的可视化数据
   frames = extract_frame_sequence(result, reg)
   save_frame_data(frames, f"result_{experiment_id}_frames.json")
   # JSON文件可作为benchmark artifact的一部分提交
   ```


运行测试:
```bash
cd sagittarius_py && uv run pytest tests/test_viz_spatial_snapshot.py -v
# ============================== 23 passed in 1.26s ==============================
```

#### 示例脚本

参考 [`examples/spatial_snapshot_demo.py`](sagittarius_py/examples/spatial_snapshot_demo.py)，演示：
- 单时刻快照提取和可视化
- 帧序列批量提取
- JSON格式保存和验证
- 多面板时间演化对比

生成文件:
- `spatial_snapshot_single.png` - 单时刻快照
- `spatial_snapshots_multipanel.png` - 多面板演化对比
- `animation_frames.json` - 标准化帧数据（可用于外部动画工具）

---

### 12. 诊断视图工具 (`diagnostics.py`) 

**需求**: 提供仿真过程的数值稳定性和收敛性诊断可视化工具,包括时间网格分析、Lindblad方程校验、MCWF与Lindblad对比、轨迹统计分析;严格遵循分层隔离原则,所有图表标注"DIAGNOSTIC VIEW - Not for hardware calibration",不作为硬件校准依据或性能佐证材料。

**实现位置**: [`sagittarius/viz/diagnostics.py`](sagittarius_py/sagittarius/viz/diagnostics.py)

#### 设计目标

DIAGNOSTICS_SECTION,用于:
- **第14阶段验证**: `open_system_sanity_checks`结果可视化
- **第16阶段基准测试**: MWIS AQC解质量诊断
- **求解器调试**: 自适应步长策略评估
- **收敛性分析**: MCWF轨迹数量对统计误差的影响

**重要声明**: 
- ⚠️ **DIAGNOSTIC VIEW** - 仅用于数值诊断,不作为硬件校准依据
- ⚠️ **分层隔离**: 可视化不修改原始数据,仅展示数据特征
- ⚠️ **非性能佐证**: 图表不包含性能结论,需结合governed benchmark artifacts

#### 核心 API

##### 12.1 `plot_time_grid_diagnostics()` - 时间网格采样分析

```python
from sagittarius.viz import plot_time_grid_diagnostics

def plot_time_grid_diagnostics(
    result,
    ax: Optional[Axes] = None,
    show_adaptive: bool = True,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (10, 6),
) -> Axes:
```

**功能**: 可视化时间点分布和自适应步长模式

**示例**:
```python
result = sim.run()
ax = plot_time_grid_diagnostics(result, show_adaptive=True)
plt.savefig("time_grid.png", dpi=150)
```

##### 12.2 `plot_lindblad_validation()` - Lindblad方程校验

```python
from sagittarius import open_system_sanity_checks
from sagittarius.viz import plot_lindblad_validation

metrics = open_system_sanity_checks(reg, seq, config=config)
ax = plot_lindblad_validation(result, metrics)
```

**功能**: 双面板显示迹误差和正定性校验,含Pass/Fail标记

##### 12.3 `plot_mcwf_vs_lindblad()` - MCWF与Lindblad对比

```python
from sagittarius.viz import plot_mcwf_vs_lindblad

axes = plot_mcwf_vs_lindblad(result_lind, result_mcwf, observables=['pop0', 'pop1'])
```

**功能**: 多子图对比两种方法的observable演化,标注误差统计

##### 12.4 `plot_trajectory_statistics()` - 轨迹统计分析

```python
from sagittarius.viz import plot_trajectory_statistics

axes = plot_trajectory_statistics(result, 'pop0', confidence_level=0.95, show_individual=True)
```

**功能**: 双面板显示均值+置信区间和最终值分布直方图

#### 测试覆盖

:::::: [`tests/test_viz_diagnostics.py`](sagittarius_py/tests/test_viz_diagnostics.py)

:
```bash
cd sagittarius_py
uv run pytest tests/test_viz_diagnostics.py -v
# ============================== 20 passed in 3.25s ==============================
```

#### 示例脚本

'DIAGNOSTICS_SECTION': [`examples/diagnostics_demo.py`](sagittarius_py/examples/diagnostics_demo.py)

:
- `time_grid_diagnostics.png`
- `lindblad_validation.png`
- `mcwf_vs_lindblad.png`
- `trajectory_statistics.png`

---
