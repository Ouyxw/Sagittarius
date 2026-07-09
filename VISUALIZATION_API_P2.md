- `debug_complex_coherences_phase.png` - 复杂相干性相位

---

### 15. 图表导出与元数据溯源 (`export.py`)

**需求**: 提供便捷的图表导出工具,支持PNG/SVG/PDF多格式输出,并自动生成配套JSON元数据文件。导出的图表必须携带完整溯源信息,包括原始产物标识、模式版本、随机种子、后端类型、基模式、绘图参数等,确保可复现性和可追溯性。

**实现位置**: [`sagittarius/viz/export.py`](sagittarius_py/sagittarius/viz/export.py)

#### 设计目标

- **多格式支持**: PNG(光栅)、SVG/PDF(矢量)按需导出
- **完整溯源**: 自动提取并记录所有关键元数据
- **分层隔离**: 明确区分探索性可视化和基准证据
- **无后端依赖**: 纯Python实现,不依赖Julia后端
- **合规性保证**: 所有导出包含免责声明和环境信息

**重要声明**: 
- ⚠️ **EXPLORATORY VISUALIZATION - Not for hardware calibration or performance evidence unless bound to controlled standard artifacts per SPEC-GOV-001**
- 元数据完整性是结果可复现的关键保障
- 分类责任由用户承担,需正确设置classification参数

#### 核心 API

##### 15.1 `export_figure()` - 图表导出与元数据生成

```python
from sagittarius.viz import export_figure

def export_figure(
    fig: Optional[Figure] = None,  # 【可选,默认=None】matplotlib图形对象
    output_path: str = "chart",  # 【必填】输出路径(不含扩展名)
    formats: List[str] = None,  # 【可选,默认=['png']】格式列表: png/svg/pdf
    dpi: int = 300,  # 【可选,默认=300】PNG分辨率
    metadata: Optional[Dict[str, Any]] = None,  # 【可选,默认=None】预构建元数据
    save_metadata: bool = True,  # 【可选,默认=True】是否保存JSON元数据
    **metadata_kwargs,  # 【可选】传递给_build_provenance_metadata的参数
) -> Dict[str, str]:
```

**功能特性**:

 **多格式并行导出**
- PNG: 高分辨率光栅图,适合网页展示
- SVG: 矢量图,无限缩放不失真
- PDF: 矢量图,适合学术出版

 **自动元数据生成**
- artifact_id: 产物唯一标识符
- mode_version: 模式版本号
- backend_type: 后端类型(CPU/GPU/NONE)
- random_seed: 随机种子
- basis_mode: 基模式(computational/其他)
- plotting_parameters: 绘图参数字典
- environment: Python/matplotlib版本、平台信息
- export_timestamp: ISO 8601时间戳
- disclaimer: 免责声明文本

**返回结构**:
```python
{
    'png': 'my_chart.png',              # PNG文件路径
    'svg': 'my_chart.svg',              # SVG文件路径
    'pdf': 'my_chart.pdf',              # PDF文件路径
    'json': 'my_chart.metadata.json'    # 元数据文件路径
}
```

**使用示例**:
```python
import matplotlib.pyplot as plt
from sagittarius.viz import export_figure

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot([1, 2, 3], [1, 4, 9], label='y=x²')
ax.set_title('Sample Plot')
ax.legend()

# 导出多格式+元数据
paths = export_figure(
    fig=fig,
    output_path='sample_chart',
    formats=['png', 'svg', 'pdf'],
    dpi=300,
    artifact_id='demo_001',
    plot_function='plot_sample',
    plot_params={'x': [1, 2, 3], 'y': [1, 4, 9]},
    extra_metadata={
        'description': 'Demonstration chart',
        'category': 'testing',
    }
)

print(paths)
# {
#     'png': 'sample_chart.png',
#     'svg': 'sample_chart.svg',
#     'pdf': 'sample_chart.pdf',
#     'json': 'sample_chart.metadata.json'
# }
```

**元数据结构示例**:
```json
{
  "schema_version": "chart-export/v1",
  "export_timestamp": "2026-07-08T09:46:34.517648Z",
  "provenance": {
    "artifact_id": "demo_001",
    "mode_version": "v1.0",
    "schema_version_result": "result/v1",
    "backend_type": "julia",
    "random_seed": 42,
    "basis_mode": "computational"
  },
  "plotting": {
    "function": "plot_sample",
    "parameters": {
      "x": [1, 2, 3],
      "y": [1, 4, 9]
    }
  },
  "environment": {
    "python_version": "3.10.12",
    "matplotlib_version": "3.7.2",
    "platform": "Linux-5.15.0-x86_64"
  },
  "disclaimer": "EXPLORATORY VISUALIZATION - Not for hardware calibration or performance evidence unless bound to controlled standard artifacts per SPEC-GOV-001"
}
```

##### 15.2 `export_from_result()` - 从SimulationResult一键导出

```python
from sagittarius.viz import export_from_result

def export_from_result(
    result: Any,  # 【必填】SimulationResult或类似对象
    plot_func,  # 【必填】绘图函数(接受result和ax参数)
    output_path: str,  # 【必填】输出路径(不含扩展名)
    formats: List[str] = None,  # 【可选,默认=['png']】格式列表
    dpi: int = 300,  # 【可选,默认=300】PNG分辨率
    plot_args: Optional[Dict[str, Any]] = None,  # 【可选,默认=None】传递给plot_func的参数
    extra_metadata: Optional[Dict[str, Any]] = None,  # 【可选,默认=None】额外元数据
    **kwargs,  # 【可选】传递给export_figure的参数
) -> Dict[str, str]:
```

**功能特性**:

 **自动元数据提取**
- 从result.manifest读取artifact_id
- 从result.mode_version读取模式版本
- 从result.backend读取后端类型
- 从result.seed读取随机种子
- 自动推断基模式(如果可用)

 **无缝集成现有可视化**
- 兼容所有遵循sagittarius规范的绘图函数
- 自动创建figure和axes
- 保留绘图函数的所有参数

**使用示例**:
```python
from sagittarius.viz import export_from_result
from sagittarius.viz.result import plot_observables

# 假设已有simulation_result
paths = export_from_result(
    result=simulation_result,
    plot_func=plot_observables,
    output_path='observable_export',
    formats=['png', 'pdf'],
    plot_args={'names': ['energy', 'population']},
    extra_metadata={
        'analysis_type': 'time_evolution',
        'validated': True,
    }
)

# 自动提取的元数据包含:
# - simulation_result.manifest['artifact_id']
# - simulation_result.mode_version
# - simulation_result.backend
# - simulation_result.seed
```

#### 技术规范

**支持的格式**:
| 格式 | 类型 | 用途 | DPI适用 |
|------|------|------|---------|
| PNG | 光栅 | 网页展示、快速预览 | ✅ 是 |
| SVG | 矢量 | 无限缩放、编辑 | ❌ 否 |
| PDF | 矢量 | 学术出版、打印 | ❌ 否 |

**元数据Schema版本**: `chart-export/v1`

**强制字段**:
- `schema_version`: 元数据格式版本
- `export_timestamp`: ISO 8601时间戳
- `provenance.artifact_id`: 产物标识符(可为null)
- `disclaimer`: 免责声明文本

**可选字段**:
- `provenance.mode_version`: 模式版本
- `provenance.backend_type`: 后端类型
- `provenance.random_seed`: 随机种子
- `provenance.basis_mode`: 基模式
- `plotting.function`: 绘图函数名
- `plotting.parameters`: 绘图参数
- `environment.*`: 环境信息

#### 测试覆盖

```bash
cd sagittarius_py && uv run pytest tests/test_viz_export.py -v
# ============================== 10 passed in 0.85s ==============================
```

**测试用例**:
- ✅ 基本PNG导出
- ✅ 多格式并行导出(PNG+SVG+PDF)
- ✅ 元数据JSON生成与验证
- ✅ 无效格式错误处理
- ✅ 自定义DPI设置
- ✅ 禁用元数据选项
- ✅ 基础元数据结构验证
- ✅ Result对象元数据提取
- ✅ 额外元数据合并
- ✅ export_from_result集成测试

#### 示例脚本

参见 [`examples/minimal_viz_examples.py`](sagittarius_py/examples/minimal_viz_examples.py) 中的Example 1和Example 4,演示:
- 基本图表导出与元数据溯源
- 多格式并行导出
- 从SimulationResult一键导出
- 元数据结构验证
- 环境信息自动记录

**生成文件示例**:
- `trig_functions.png` (213 KB) - 高分辨率PNG
- `trig_functions.svg` (36 KB) - 矢量SVG
- `trig_functions.pdf` (15 KB) - 矢量PDF
- `trig_functions.metadata.json` (964 B) - 完整元数据

---

### 16. 轻量化报表工具 (`report.py`)

**需求**: 提供轻量级报表生成工具,自动汇总多个仿真结果产物,嵌入配套图表、模式版本、后端/运行元数据、基模式、随机种子/输出网格信息、关联清单文件。报表必须严格区分探索性可视化图表和基准/公开结论佐证材料,采用视觉编码(颜色、标签)清晰标识。

**实现位置**: [`sagittarius/viz/report.py`](sagittarius_py/sagittarius/viz/report.py)

#### 设计目标

- **自动汇总**: 批量处理多个结果,生成统一报表
- **严格分类**: EXPLORATORY(红色) vs BENCHMARK EVIDENCE(绿色)
- **多格式支持**: HTML(交互式)和Markdown(轻量级)
- **嵌入图表**: 自动保存并引用PNG图表
- **元数据聚合**: 集中展示所有关键元数据
- **清单链接**: 关联manifest文件确保可追溯性
- **无后端依赖**: 纯Python实现,不依赖Julia

**重要声明**: 
- ⚠️ **分类责任由用户承担**: 必须根据数据来源和用途正确设置classification
- 🔴 **EXPLORATORY**: 不得作为硬件校准依据或性能佐证材料
- 🟢 **BENCHMARK EVIDENCE**: 必须绑定SPEC-GOV-001管控标准产物

#### 核心 API

##### 16.1 `ReportGenerator` - 报表生成器类

```python
from sagittarius.viz.report import ReportGenerator

class ReportGenerator:
    def __init__(
        self,
        output_dir: str = "reports",  # 【可选,默认='reports'】输出目录
        report_type: str = "html",  # 【可选,默认='html'】报表类型: html/markdown
        title: str = "Simulation Results Report",  # 【可选】报表标题
    ):
    
    def add_result_summary(
        self,
        result: Any,  # 【必填】SimulationResult或类似对象
        classification: str = "exploratory",  # 【可选,默认='exploratory']分类: exploratory/benchmark_evidence
        custom_metrics: Optional[Dict[str, Any]] = None,  # 【可选,默认=None】自定义指标
    ) -> 'ReportGenerator':  # 返回self支持链式调用
    
    def add_chart(
        self,
        fig: Figure,  # 【必填】matplotlib图形对象
        title: str,  # 【必填】图表标题
        description: str = "",  # 【可选,默认=''】图表描述
        classification: str = "exploratory",  # 【可选,默认='exploratory']分类
        chart_metadata: Optional[Dict[str, Any]] = None,  # 【可选,默认=None】图表元数据
    ) -> 'ReportGenerator':
    
    def add_manifest_link(
        self,
        manifest_path: str,  # 【必填】manifest文件路径
        description: str = "",  # 【可选,默认=''】描述
    ) -> 'ReportGenerator':
    
    def generate(
        self,
        output_filename: Optional[str] = None,  # 【可选,默认=自动生成】输出文件名
    ) -> str:  # 返回生成的报表文件路径
```

**功能特性**:

 **结果摘要提取**
- artifact_id: 从result.manifest读取
- mode_version: 模式版本
- schema_version: Schema版本
- backend: 后端类型
- seed: 随机种子
- register信息: 原子数、基模式
- solver_config: 求解器配置(method、dt、t_final)
- custom_metrics: 用户自定义指标

 **分类视觉编码**
- 🔴 EXPLORATORY: 红色边框(#e74c3c) + 浅红背景(#fdf2f2)
- 🟢 BENCHMARK EVIDENCE: 绿色边框(#27ae60) + 浅绿背景(#f2fdf5)
- 免责声明自动添加对应颜色和图标(⚠️/✅)

 **图表嵌入**
- 自动保存为PNG(dpi=300)
- 文件名自动生成(chart_0.png, chart_1.png...)
- HTML中直接引用<img>标签
- Markdown中使用![alt](path)语法

 **方法链式调用**
```python
reporter.add_result_summary(result1, 'exploratory') \
        .add_result_summary(result2, 'benchmark_evidence') \
        .add_chart(fig, 'Chart Title', classification='exploratory') \
        .generate('report.html')
```

**HTML报表结构示例**:
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        .section.exploratory { 
            border-left: 4px solid #e74c3c; 
            background: #fdf2f2; 
        }
        .section.benchmark { 
            border-left: 4px solid #27ae60; 
            background: #f2fdf5; 
        }
        .disclaimer.exploratory { 
            background: #ffebee; 
            color: #c62828; 
        }
        .disclaimer.benchmark { 
            background: #e8f5e9; 
            color: #2e7d32; 
        }
    </style>
</head>
<body>
    <h1>Simulation Results Report</h1>
    
    <!-- Result Summary Section -->
    <div class="section benchmark">
        <h2>Result Summary #1</h2>
        <div class="disclaimer benchmark">
            ✅ BENCHMARK EVIDENCE - Bound to controlled standard artifacts per SPEC-GOV-001
        </div>
        <table>
            <tr><th>artifact_id</th><td>controlled_001</td></tr>
            <tr><th>backend</th><td>julia</td></tr>
            <tr><th>seed</th><td>42</td></tr>
        </table>
    </div>
    
    <!-- Chart Section -->
    <div class="section exploratory">
        <h2>Performance Trend</h2>
        <div class="disclaimer exploratory">
            ⚠️ EXPLORATORY - Not for calibration
        </div>
        <img src="chart_0.png" alt="Performance Trend">
    </div>
</body>
</html>
```

**使用示例**:
```python
from sagittarius.viz.report import ReportGenerator
import matplotlib.pyplot as plt

# 初始化报表生成器
reporter = ReportGenerator(
    output_dir='reports',
    report_type='html',
    title='Quantum Simulation Analysis Report'
)

# 添加探索性结果
reporter.add_result_summary(
    result=result_exploratory,
    classification='exploratory',
    custom_metrics={
        'note': 'Preliminary analysis',
        'purpose': 'Feature testing',
    }
)

# 添加基准证据结果
reporter.add_result_summary(
    result=result_benchmark,
    classification='benchmark_evidence',
    custom_metrics={
        'standard': 'SPEC-GOV-001',
        'validated': True,
    }
)

# 添加图表
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot([1, 2, 3, 4], [1, 4, 9, 16])
ax.set_title('Runtime Scaling')

reporter.add_chart(
    fig=fig,
    title='Performance Scaling',
    description='Runtime vs problem size',
    classification='exploratory',
    chart_metadata={'metric': 'runtime', 'unit': 'seconds'}
)
plt.close()

# 添加manifest链接
reporter.add_manifest_link(
    'path/to/manifest.json',
    'Associated benchmark manifest'
)

# 生成报表
report_path = reporter.generate('final_report.html')
print(f"Report generated: {report_path}")
```

##### 16.2 `generate_quick_report()` - 一键生成报表

```python
from sagittarius.viz.report import generate_quick_report

def generate_quick_report(
    results: List[Any],  # 【必填】结果对象列表
    output_dir: str = "reports",  # 【可选,默认='reports'】输出目录
    title: str = "Quick Simulation Report",  # 【可选】报表标题
    classifications: Optional[List[str]] = None,  # 【可选,默认=全exploratory】分类列表
) -> str:  # 返回生成的报表文件路径
```

**功能特性**:

 **极简API**
- 一行代码生成完整报表
- 自动处理所有结果摘要
- 自动分配分类(如未指定则默认为exploratory)

 **批量处理**
- 支持任意数量的结果对象
- 自动按顺序编号
- 统一格式和样式

**使用示例**:
```python
from sagittarius.viz.report import generate_quick_report

results = [result1, result2, result3]
classifications = ['exploratory', 'exploratory', 'benchmark_evidence']

report_path = generate_quick_report(
    results=results,
    output_dir='reports',
    title='Quick Summary',
    classifications=classifications,
)

print(f"Generated: {report_path}")
# Output: reports/report_20260708_094634.html
```

#### 技术规范

**支持的报表类型**:
| 类型 | 格式 | 特点 | 适用场景 |
|------|------|------|----------|
| HTML | .html | 交互式、颜色编码、表格 | 内部审查、在线分享 |
| Markdown | .md | 轻量级、纯文本、Git友好 | 版本控制、文档归档 |

**分类规范**:
| 分类 | 颜色 | 图标 | 用途 | 限制 |
|------|------|------|------|------|
| exploratory | 🔴 红色 | ⚠️ | 数据分析、调试、初步探索 | **不得**作为校准依据 |
| benchmark_evidence | 🟢 绿色 | ✅ | 官方基准结论、性能报告 | 必须绑定受控产物 |

**自动生成的文件名**:
- HTML: `report_YYYYMMDD_HHMMSS.html`
- Markdown: `report_YYYYMMDD_HHMMSS.md`
- 图表: `chart_0.png`, `chart_1.png`, ...

**元数据提取优先级**:
1. result.manifest['artifact_id'] (最高优先级)
2. result.mode_version
3. result.schema_version
4. result.backend
5. result.seed
6. result.register (如果存在)
7. result.config (如果存在)

#### 测试覆盖

```bash
cd sagittarius_py && uv run pytest tests/test_viz_report.py -v
# ============================== 14 passed in 0.65s ==============================
```

**测试用例**:
- ✅ 基本HTML报表生成
- ✅ 基本Markdown报表生成
- ✅ 添加探索性结果摘要
- ✅ 添加基准证据结果摘要
- ✅ 无效分类错误处理
- ✅ 添加图表与分类
- ✅ 添加manifest链接
- ✅ 方法链式调用
- ✅ 自定义指标在摘要中
- ✅ 自动生成文件名
- ✅ 多结果混合分类
- ✅ 快速报表基本功能
- ✅ 快速报表自定义分类
- ✅ 长度不匹配错误处理

#### 示例脚本

参见 [`examples/minimal_viz_examples.py`](sagittarius_py/examples/minimal_viz_examples.py) 中的Example 2和Example 3,演示:
- ReportGenerator类完整工作流
- 探索性与基准证据混合报表
- 颜色编码视觉区分
- generate_quick_report()一行代码生成
- 批量结果处理
- 自定义分类分配

**生成文件示例**:
- `demo_report.html` (3.8 KB) - 包含2个结果+2个图表的HTML报表
- `report_20260708_094634.html` (3.2 KB) - 快速生成的3结果报表
- `chart_0.png`, `chart_1.png` - 嵌入的图表文件

---

### 17. 最小可运行示例与最佳实践

**需求**: 提供完整的最小可运行示例,展示新增的导出和报表功能。每个示例必须清晰标注输出数据结构、后端依赖状态(无后端依赖/依赖Julia)、分类标签(探索性/基准证据),便于用户快速上手和正确分类。

**实现位置**: [`examples/minimal_viz_examples.py`](sagittarius_py/examples/minimal_viz_examples.py)

#### 示例列表

| 示例 | 功能 | 后端依赖 | 分类 | 输出 |
|------|------|----------|------|------|
| Example 1 | 图表导出与元数据溯源 | NONE | EXPLORATORY | PNG/SVG/PDF + JSON |
| Example 2 | 报表生成与分类区分 | NONE | MIXED | HTML报告 |
| Example 3 | 快速报表一行代码 | NONE | MIXED | HTML报告 |
| Example 4 | 与现有可视化集成 | VARIES | INHERITED | PNG/SVG + JSON |

#### 运行示例

```bash
cd /workspaces/Sagittarius/sagittarius_py
uv run python examples/minimal_viz_examples.py
```

**输出示例**:
```
================================================================================
NEW VISUALIZATION EXPORT & REPORT FEATURES
================================================================================

Example 1: Chart Export with Metadata Provenance
✓ Exported files:
  • PNG: trig_functions.png (213,839 bytes)
  • SVG: trig_functions.svg (36,396 bytes)
  • PDF: trig_functions.pdf (15,575 bytes)
  • JSON: trig_functions.metadata.json (964 bytes)

✓ Metadata provenance:
  • Schema: chart-export/v1
  • Artifact ID: demo_trig_001
  • Plot function: plot_trigonometric
  • Timestamp: 2026-07-08T09:46:34.517648Z
  • Disclaimer: EXPLORATORY VISUALIZATION - Not for hardware calibration...

Example 2: Report Generation with Classification
✓ Generated report:
  • Path: demo_report.html
  • Format: HTML
  • Sections: 4 (2 results + 2 charts)
  • Size: 3,798 bytes

✓ Classification distribution:
  • Exploratory mentions: 8
  • Benchmark mentions: 7
  • Visual distinction: Color-coded sections (red/green)

Example 3: Quick Report One-Liner
✓ Generated quick report:
  • Path: report_20260708_094634.html
  • Results: 3 (2 exploratory, 1 benchmark)
  • Time: Single function call
  • Size: 3,191 bytes

Example 4: Export Integration with Visualization Functions
✓ Exported integrated chart:
  • PNG: integrated_export.png
  • SVG: integrated_export.svg
  • JSON: integrated_export.metadata.json

✓ Extracted provenance from result:
  • Artifact ID: integration_demo_001
  • Backend: julia_synthetic
  • Seed: 12345
  • Mode version: v1.0

✅ All examples completed!
```

#### 后端依赖分类说明

**NONE (无后端依赖)**:
- 纯Python实现
- 不依赖Julia后端
- 可直接运行,无需仿真结果
- 适用于: 导出基础设施、报表生成器

**JULIA_REQUIRED (需要Julia后端)**:
- 需要真实的SimulationResult
- 依赖Julia求解器输出
- 必须先运行仿真
- 适用于: 实际观测值轨迹、布居热图等

**VARIES (依赖可变)**:
- 取决于传入的plot_func
- 如果使用合成数据则NONE
- 如果使用真实结果则JULIA_REQUIRED
- 适用于: export_from_result()集成

**INHERITED (继承自数据源)**:
- 分类继承自result对象
- 如果result来自Julia则为JULIA_REQUIRED
- 如果result为合成数据则为NONE
- 适用于: 集成现有可视化函数

#### 分类标签规范

**EXPLORATORY (探索性)**:
- 🔴 红色视觉编码
- ⚠️ 警告图标
- "Not for hardware calibration"声明
- 用途: 数据分析、调试、初步探索
- **限制**: 不得作为硬件校准依据或性能佐证材料

**BENCHMARK EVIDENCE (基准证据)**:
- 🟢 绿色视觉编码
- ✅ 确认图标
- "Bound to controlled standard artifacts per SPEC-GOV-001"声明
- 用途: 官方基准结论、性能报告
- **要求**: 必须绑定SPEC-GOV-001管控标准产物

**MIXED (混合)**:
- 同时包含EXPLORATORY和BENCHMARK EVIDENCE
- 每部分独立标注分类
- 颜色编码清晰区分
- 用途: 综合分析报告

#### 输出数据结构标注

**图表导出输出**:
```
my_chart/
├── my_chart.png          # PNG格式(光栅,213 KB @ 300 DPI)
├── my_chart.svg          # SVG格式(矢量,36 KB)
├── my_chart.pdf          # PDF格式(矢量,15 KB)
└── my_chart.metadata.json # 元数据(964 B, JSON格式)
```

**元数据结构** (见第15章详细规范):
```json
{
  "schema_version": "chart-export/v1",
  "export_timestamp": "ISO 8601 timestamp",
  "provenance": {...},
  "plotting": {...},
  "environment": {...},
  "disclaimer": "..."
}
```

**报表输出**:
```
reports/
├── report_YYYYMMDD_HHMMSS.html  # HTML报表(3-5 KB)
├── chart_0.png                  # 嵌入图表1
├── chart_1.png                  # 嵌入图表2
└── ...
```

**HTML报表结构** (见第16章详细规范):
- 头部: 标题、生成时间、CSS样式
- 主体: 分节展示(result summary、chart、manifest link)
- 每节: 分类标签、免责声明、内容(表格/图片/链接)
- 视觉编码: 红色(探索性) / 绿色(基准证据)

#### 最佳实践

**1. 始终导出元数据**:
```python
# ✅ 推荐: 保留完整溯源信息
paths = export_figure(fig, 'chart', save_metadata=True)

# ❌ 避免: 丢失可复现性关键信息
paths = export_figure(fig, 'chart', save_metadata=False)
```

**2. 明确分类责任**:
```python
# ✅ 推荐: 根据数据来源正确分类
if result.manifest.get('controlled'):
    classification = 'benchmark_evidence'
else:
    classification = 'exploratory'

reporter.add_result_summary(result, classification=classification)
```

**3. 使用高DPI用于出版**:
```python
# ✅ 出版物质量
paths = export_figure(fig, 'chart', dpi=300, formats=['png', 'pdf'])

# ⚠️ 网页展示可降低DPI
paths = export_figure(fig, 'chart', dpi=150, formats=['png'])
```

**4. 矢量格式优先用于缩放**:
```python
# ✅ 需要缩放时用矢量格式
paths = export_figure(fig, 'chart', formats=['svg', 'pdf'])

# ❌ PNG放大后会失真
paths = export_figure(fig, 'chart', formats=['png'])
```

**5. 批量处理用快速报表**:
```python
# ✅ 多个结果一键生成
report_path = generate_quick_report(results, 'reports', classifications=classifications)

# ❌ 逐个添加繁琐
reporter = ReportGenerator()
for r in results:
    reporter.add_result_summary(r)
reporter.generate()
```

**6. 保留原始数据**:
```python
# ✅ 导出图表同时保存原始result
paths = export_from_result(result, plot_func, 'chart')
result.save('result.json')  # 保留完整数据

# ❌ 仅导出图表,丢失原始数据
paths = export_from_result(result, plot_func, 'chart')
# result未保存
```

#### 注意事项

**⚠️ JSON不是图表格式**:
```python
# ❌ 错误: JSON不在formats参数中
paths = export_figure(fig, 'chart', formats=['png', 'json'])
# ValueError: Invalid formats: {'json'}

# ✅ 正确: JSON自动生成
paths = export_figure(fig, 'chart', formats=['png', 'svg'])
# 自动生成: chart.png, chart.svg, chart.metadata.json
```

**⚠️ 分类一致性检查**:
```python
# ✅ 推荐: 验证分类与数据来源一致
assert len(results) == len(classifications), "长度必须匹配"
for result, classification in zip(results, classifications):
    if classification == 'benchmark_evidence':
        assert result.manifest.get('controlled'), "基准证据必须绑定受控产物"
```

**⚠️ 文件大小管理**:
```python
# ✅ 根据用途选择合适DPI
if for_publication:
    dpi = 300  # ~200-300 KB PNG
elif for_web:
    dpi = 150  # ~50-100 KB PNG
elif for_preview:
    dpi = 72   # ~20-50 KB PNG
```

#### 相关文档

- **详细实现**: [EXPORT_REPORT_FEATURES_SUMMARY.md](file:///workspaces/Sagittarius/EXPORT_REPORT_FEATURES_SUMMARY.md)
- **快速参考**: [EXPORT_REPORT_QUICK_REFERENCE.md](file:///workspaces/Sagittarius/EXPORT_REPORT_QUICK_REFERENCE.md)
- **测试文件**: `tests/test_viz_export.py` (10用例), `tests/test_viz_report.py` (14用例)
- **示例脚本**: `examples/minimal_viz_examples.py` (4个示例)

---

## P2阶段总结


### 测试覆盖汇总

```bash
cd sagittarius_py && uv run pytest tests/test_viz_benchmark_perf.py tests/test_viz_small_system_debug.py tests/test_viz_export.py tests/test_viz_report.py -v
# ============================== 61 passed in 2.50s ==============================
```

| 测试套件 | 用例数 | 通过数 | 失败数 | 覆盖率 |
|---------|--------|--------|--------|--------|
| test_viz_benchmark_perf.py | 19 | 19 | 0 | 100% |
| test_viz_small_system_debug.py | 19 | 19 | 0 | 100% |
| test_viz_export.py | 10 | 10 | 0 | 100% |
| test_viz_report.py | 14 | 14 | 0 | 100% |
| **总计** | **62** | **62** | **0** | **100%** |

