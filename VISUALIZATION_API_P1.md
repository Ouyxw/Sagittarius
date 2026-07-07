
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
#### 测试

测试文件: [`tests/test_viz_mwis.py`](sagittarius_py/tests/test_viz_mwis.py)

运行测试:
```bash
cd sagittarius_py
uv run pytest tests/test_viz_mwis.py -v
# ============================== 35 passed in 4.83s ==============================
```

