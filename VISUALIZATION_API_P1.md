
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
