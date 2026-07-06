# Sagittarius Phase 19 可视化模块 - 快速参考

## 🚀 快速开始

```python
from sagittarius.viz import *
import matplotlib.pyplot as plt

# 1. 寄存器布局
ax = plot_register(reg, blockade_radius=6.0)

# 2. 脉冲波形
ax = plot_pulse_waveform(pulse, field='omega')

# 3. 结果可视化
result = sim.run()
result.sample(shots=500, seed=42)
plot_result_summary(result, show=True)
```

---

## 📊 API 速查表

### 寄存器可视化

| 函数 | 参数 | 说明 |
|------|------|------|
| `plot_register(reg, ...)` | `blockade_radius`, `highlight_atoms`, `labels` | 2D 原子布局 |
| `plot_interaction_graph(reg, R_b)` | `show_distances` | 相互作用图（带距离） |

### 脉冲可视化

| 函数 | 参数 | 说明 |
|------|------|------|
| `plot_pulse_waveform(pulse, ...)` | `field='omega'`, `atom_index`, `time_grid` | 单字段波形 |
| `plot_pulse_both_fields(pulse)` | `time_grid` | Omega + Delta 对比 |
| `sample_pulse_waveform(...)` | - | **纯数据提取器** |

### 结果可视化

| 函数 | 参数 | 说明 |
|------|------|------|
| `plot_observables(result)` | `names`, `ax` | 可观测量轨迹 |
| `plot_bitstring_distribution(result)` | `top_k=10`, `sort_by` | 比特串概率直方图 |
| `plot_shot_histogram(result)` | `normalize`, `top_k` | Shot 计数/频率 |
| `plot_population_heatmap(result)` | `cmap='viridis'` | 原子-时间热图 |
| `plot_result_summary(result)` | `figsize` | 2x2 综合报告 |

---

## 🎨 常用定制

### 保存图表

```python
ax = plot_register(reg)
ax.figure.savefig("plot.png", dpi=150, bbox_inches='tight')
plt.close('all')  # 释放内存
```

### 多图组合

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
plot_register(reg, ax=axes[0])
plot_pulse_waveform(pulse, ax=axes[1])
plt.tight_layout()
```

### 自定义样式

```python
ax = plot_observables(result)
ax.set_title("Custom Title", fontsize=14)
ax.set_ylim(-0.1, 1.1)
ax.legend(loc='lower right')
```

---

## ⚙️ 环境配置

### Jupyter Notebook

```python
%matplotlib inline  # 静态显示
# 或
%matplotlib widget  # 交互式缩放
```

### 服务器/CI

```python
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
```

### 中文字体

```python
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
```

---

## 🧪 测试与验证

```bash
# 运行烟雾测试
python test_viz_smoke.py

# 生成示例图表
python examples_phase19_viz.py --output-dir ./viz_examples
```

---

## ❗ 常见错误

| 错误 | 原因 | 解决方法 |
|------|------|---------|
| `No observable columns found` | DataFrame 缺少 'pop' 列 | 检查仿真是否包含 population observables |
| `Samples array is empty` | 未调用 `result.sample()` | 先执行 `result.sample(shots=N, seed=S)` |
| `Julia not initialized` | 在 `sim.run()` 之前绘图 | 先运行仿真，再可视化结果 |

---

## 📚 完整文档

- [详细实现文档](docs/phase19_visualization_implementation.md)
- [模块 README](sagittarius_py/sagittarius/viz/README.md)
- [实现总结](PHASE19_IMPLEMENTATION_SUMMARY.md)

---

**版本**: v1.0 | **更新**: 2026-07-06
