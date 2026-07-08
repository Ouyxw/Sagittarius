# 诊断视图工具 (Diagnostic Visualization Tools)

## 概述

本模块提供量子仿真过程的数值稳定性和收敛性诊断可视化工具,包括:

1. **时间网格诊断**: 分析仿真时间步长分布和自适应采样策略
2. **Lindblad校验**: 验证密度矩阵的迹守恒和正定性
3. **MCWF vs Lindblad对比**: 比较两种开放系统演化方法的差异
4. **轨迹统计分析**: 蒙特卡洛波函数方法的均值、方差和置信区间

**重要声明**: 所有图表均标注"DIAGNOSTIC VIEW - Not for hardware calibration",仅用于数值诊断,**不作为硬件校准依据或性能佐证材料**。

## 快速开始

### 安装依赖

```bash
cd sagittarius_py
pip install scipy  # 用于置信区间计算
```

### 基本用法

```python
from sagittarius import Simulation, Register, Atom, PulseSequence, SolverConfig
from sagittarius.viz import (
    plot_time_grid_diagnostics,
    plot_lindblad_validation,
    plot_mcwf_vs_lindblad,
    plot_trajectory_statistics,
)

# 运行仿真
reg = Register([Atom(0, 0), Atom(1, 2)], C6=1.0)
seq = PulseSequence(omega=2.0, delta=0.0)
config = SolverConfig(reltol=1e-8)

sim = Simulation(reg, seq, config)
result = sim.run()

# 绘制时间网格诊断
ax = plot_time_grid_diagnostics(result)
plt.savefig("time_grid.png")
```

## API参考

### 1. 时间网格诊断

```python
plot_time_grid_diagnostics(
    result,
    ax=None,
    show_adaptive=True,
    title=None,
    figsize=(10, 6)
)
```

**参数**:
- `result`: SimulationResult对象
- `show_adaptive`: 是否显示自适应步长颜色编码
- `title`: 自定义标题

**返回**: matplotlib Axes对象

**示例输出**:
- 时间点散点图
- 步长统计(min/max/mean Δt)
- 自适应步长的颜色编码热图

---

### 2. Lindblad方程校验

```python
from sagittarius import open_system_sanity_checks

# 运行校验
metrics = open_system_sanity_checks(
    reg, seq,
    config=SolverConfig(gamma=0.1),
    psi0=np.array([0, 1], dtype=complex),
    t_end=2.0,
    observables={"pop": 0},
    n_trajectories=100,
)

# 绘制校验结果
plot_lindblad_validation(result, metrics)
```

**参数**:
- `result`: Lindblad仿真结果
- `metrics`: open_system_sanity_checks返回的字典
- `show_trace_error`: 是否显示迹误差面板
- `show_positivity`: 是否显示正定性面板

**校验指标**:
- `lindblad_trace.ok`: 迹误差是否在容差内
- `lindblad_trace.max_error`: 最大|Tr(ρ) - 1|
- `lindblad_positivity.ok`: 最小本征值是否≥-atol
- `lindblad_positivity.min_eigenvalue`: 最小本征值

**视觉元素**:
- ✓ PASS / ✗ FAIL状态标记
- 容差阈值线(红色虚线)
- 对数坐标轴显示小误差

---

### 3. MCWF与Lindblad对比

```python
# 运行两种方法
result_lind = sim_lindblad.run(observables={'pop0': 0})
result_mcwf = sim_mcwf.run(observables={'pop0': 0})

# 对比绘图
plot_mcwf_vs_lindblad(
    result_lind, result_mcwf,
    observables=['pop0', 'pop1'],
    show_error_bands=True
)
```

**参数**:
- `lindblad_result`: Lindblad仿真结果
- `mcwf_result`: MCWF仿真结果
- `observables`: 要对比的可观测量列表
- `show_error_bands`: 是否显示误差带

**输出**:
- 双曲线对比(Lindblad实线, MCWF虚线)
- 绝对误差演化子图
- 统计摘要(mean_abs_error, max_abs_error)

---

### 4. 轨迹统计分析

```python
# 运行多轨迹MCWF
config = SolverConfig(use_mc=True, n_trajectories=100)
result = sim.run()

# 绘制轨迹统计
plot_trajectory_statistics(
    result, 'pop0',
    confidence_level=0.95,
    show_individual=True,
    n_sample_trajectories=10
)
```

**参数**:
- `mcwf_result`: MCWF仿真结果(需包含trajectories属性)
- `observable_name`: 可观测量名称
- `confidence_level`: 置信水平(默认0.95)
- `show_individual`: 是否显示单条轨迹
- `n_sample_trajectories`: 显示的轨迹数量

**统计量**:
- 均值曲线(粗实线)
- 置信区间填充(半透明区域)
- ±1σ标准差边界(虚线)
- 最终时刻值的分布直方图

**注意**: 当前API可能需要扩展以存储个体轨迹数据。

---

## 分层隔离原则

本模块严格遵循以下设计原则:

1. **非校准声明**: 所有图表包含"DIAGNOSTIC VIEW"免责声明
2. **元数据分离**: 可视化不修改原始仿真数据
3. **Artifact链接**: 如result.manifest包含artifact_id,在副标题中显示
4. **诊断提示**: 数据缺失时提供可操作的错误消息

## 适配第14、16阶段验证流程

### 第14阶段: Open System Sanity Checks

```python
# 完整验证流程
metrics = open_system_sanity_checks(reg, seq, config=config)

# 检查所有校验通过
assert metrics['ok'] == True
assert metrics['lindblad_trace']['ok'] == True
assert metrics['lindblad_positivity']['ok'] == True
assert metrics['mcwf_vs_lindblad']['ok'] == True

# 可视化诊断
plot_lindblad_validation(result, metrics)
```

**校验标准**:
- 迹误差 ≤ 1e-6
- 最小本征值 ≥ -1e-7
- MCWF-Lindblad平均误差 ≤ 0.08

### 第16阶段: MWIS基准测试诊断

```python
# 在MWIS AQC求解后添加诊断
result_aqc = sim.run()

# 时间网格分析
plot_time_grid_diagnostics(result_aqc)

# 如果使用了MCWF,分析轨迹收敛性
if hasattr(result_aqc, 'trajectories'):
    plot_trajectory_statistics(result_aqc, 'cost_function')
```

## 故障排除

### 常见问题

**Q: "No time column 't' found"**
```python
# 确保仿真结果包含时间序列
result = sim.run()  # 而非 result = sim.validate()
print(result.data.keys())  # 应包含 't'
```

**Q: "No trajectory data found"**
```python
# 当前API可能未存储个体轨迹
# 需要扩展Simulation.run()以支持trajectory-level输出
config = SolverConfig(use_mc=True, n_trajectories=100)
# TODO: 添加 store_trajectories=True 参数
```

**Q: "Missing 'lindblad_trace' in metrics"**
```python
# 必须使用open_system_sanity_checks的输出
metrics = open_system_sanity_checks(...)  # 正确
# 不要手动构造metrics字典
```

## 性能考虑

- **大数据量**: >1000时间点时,散点图渲染可能较慢
- **多轨迹**: >100条轨迹时,建议设置`show_individual=False`
- **内存**: 存储完整轨迹数据需要O(n_traj × n_time)内存

## 测试

运行完整测试套件:

```bash
cd sagittarius_py
pytest tests/test_viz_diagnostics.py -v
```

测试覆盖:
- ✓ 正常数据显示
- ✓ 缺失数据的错误处理
- ✓ Pass/Fail状态标记
- ✓ 置信区间计算
- ✓  disclaimer文本存在性

## 示例脚本

查看完整示例:

```bash
python examples/diagnostics_demo.py
```

生成图表:
- `time_grid_diagnostics.png`
- `lindblad_validation.png`
- `mcwf_vs_lindblad.png`
- `trajectory_statistics.png`

## 未来扩展

计划中的功能:
- [ ] 自适应步长策略优化建议
- [ ] 轨迹收敛性自动检测
- [ ] 多参数扫描的热图对比
- [ ] 导出诊断报告(PDF/HTML)

## 相关文档

- [可视化API总览](../../VISUALIZATION_API.md)
- [几何参数校验](geometry_diagnostics.md)
- [MWIS问题可视化](mwis_viz.md)
- [关联分析可视化](correlation_viz.md)
