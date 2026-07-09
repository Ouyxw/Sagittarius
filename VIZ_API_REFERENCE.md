# Sagittarius Visualization API Reference

> **Complete API documentation for all visualization functions in `sagittarius.viz` module**

---

## 📋 Quick Reference Card

### Core Visualization (需求 1-6)

| Function | Module | Purpose | Returns |
|----------|--------|---------|---------|
| [`plot_register()`](#plot_register) | `viz.register` | 2D register layout with atoms, blockade disks, interaction edges | `Axes` |
| [`plot_interaction_graph()`](#plot_interaction_graph) | `viz.register` | Unit disk graph with distances and adjacency | `Axes` |
| [`plot_pulse_waveform()`](#plot_pulse_waveform) | `viz.pulse` | Ω or Δ pulse waveform sampling | `Axes` |
| [`plot_pulse_both_fields()`](#plot_pulse_both_fields) | `viz.pulse` | Both Ω and Δ fields on dual axes | `Axes` |
| [`sample_pulse_waveform()`](#sample_pulse_waveform) | `viz.pulse` | Sample pulse values on time grid (data-only) | `np.ndarray` |
| [`plot_observables()`](#plot_observables) | `viz.result` | Observable trajectories vs time | `Axes` |
| [`plot_bitstring_distribution()`](#plot_bitstring_distribution) | `viz.result` | Final bitstring probability histogram | `Axes` |
| [`plot_shot_histogram()`](#plot_shot_histogram) | `viz.result` | Measurement shot distribution histogram | `Axes` |
| [`plot_population_heatmap()`](#plot_population_heatmap) | `viz.result` | Atom×time population heatmap | `Axes` |

### Diagnostics & Analysis (需求 7-14)

| Function | Module | Purpose | Returns |
|----------|--------|---------|---------|
| [`generate_basis_diagnostics()`](#generate_basis_diagnostics) | `viz.basis_diagnostics` | Generate reduced basis diagnostics data | `Dict` |
| [`plot_basis_space_diagram()`](#plot_basis_space_diagram) | `viz.basis_diagnostics` | Visualize basis space pruning | `Axes` |
| [`plot_bitstring_space_grid()`](#plot_bitstring_space_grid) | `viz.basis_diagnostics` | Grid view of valid/forbidden bitstrings | `Axes` |
| [`plot_blockade_constraint_graph()`](#plot_blockade_constraint_graph) | `viz.basis_diagnostics` | Blockade constraint network | `Axes` |
| [`plot_comprehensive_basis_diagnostics()`](#plot_comprehensive_basis_diagnostics) | `viz.basis_diagnostics` | Multi-panel basis diagnostics | `Figure` |
| [`extract_geometry_diagnostics()`](#extract_geometry_diagnostics) | `viz.geometry_diagnostics` | Extract geometry diagnostic data | `Dict` |
| [`plot_geometry_diagnostics()`](#plot_geometry_diagnostics) | `viz.geometry_diagnostics` | Distance/VDW/adjacency heatmaps | `Axes` |
| [`plot_unit_disk_graph()`](#plot_unit_disk_graph) | `viz.geometry_diagnostics` | Unit disk graph visualization | `Axes` |
| [`plot_mwis_problem()`](#plot_mwis_problem) | `viz.mwis_viz` | MWIS problem with conflicts | `Axes` |
| [`plot_pair_correlation_matrix()`](#plot_pair_correlation_matrix) | `viz.correlation_viz` | Pair correlation ⟨nᵢnⱼ⟩ heatmap | `Axes` |
| [`plot_connected_correlation_matrix()`](#plot_connected_correlation_matrix) | `viz.correlation_viz` | Connected correlation Cᵢⱼ heatmap | `Axes` |
| [`plot_pauli_zz_matrix()`](#plot_pauli_zz_matrix) | `viz.correlation_viz` | Pauli-ZZ correlation ⟨σᶻᵢσᶻⱼ⟩ | `Axes` |
| [`plot_blockade_conflict_heatmap()`](#plot_blockade_conflict_heatmap) | `viz.correlation_viz` | Blockade conflict structure | `Axes` |
| [`extract_spatial_snapshot()`](#extract_spatial_snapshot) | `viz.spatial_snapshot` | Extract single-frame spatial data | `Dict` |
| [`extract_frame_sequence()`](#extract_frame_sequence) | `viz.spatial_snapshot` | Extract multi-frame sequence | `List[Dict]` |
| [`plot_spatial_snapshot()`](#plot_spatial_snapshot) | `viz.spatial_snapshot` | Single-frame spatial population | `Axes` |
| [`plot_multi_panel_snapshots()`](#plot_multi_panel_snapshots) | `viz.spatial_snapshot` | Multi-panel frame comparison | `Axes` |
| [`plot_time_grid_diagnostics()`](#plot_time_grid_diagnostics) | `viz.diagnostics` | Time grid sampling analysis | `Axes` |
| [`plot_lindblad_validation()`](#plot_lindblad_validation) | `viz.diagnostics` | Lindblad trace/positivity validation | `Axes` |
| [`plot_mcwf_vs_lindblad()`](#plot_mcwf_vs_lindblad) | `viz.diagnostics` | MCWF vs Lindblad comparison | `Axes` |
| [`plot_trajectory_statistics()`](#plot_trajectory_statistics) | `viz.diagnostics` | Trajectory mean±σ confidence intervals | `Axes` |

### Benchmark & Debugging (需求 15-17)

| Function | Module | Purpose | Returns |
|----------|--------|---------|---------|
| [`plot_runtime_scaling()`](#plot_runtime_scaling) | `viz.benchmark_perf` | Runtime vs atom count scaling | `Axes` |
| [`plot_memory_scaling()`](#plot_memory_scaling) | `viz.benchmark_perf` | Memory usage scaling curve | `Axes` |
| [`plot_solver_comparison()`](#plot_solver_comparison) | `viz.benchmark_perf` | Multi-solver performance comparison | `Axes` |
| [`plot_success_failure_summary()`](#plot_success_failure_summary) | `viz.benchmark_perf` | Success/failure rate summary | `Axes` |
| [`plot_cpu_gpu_error_comparison()`](#plot_cpu_gpu_error_comparison) | `viz.benchmark_perf` | CPU vs GPU error comparison | `Axes` |
| [`plot_state_probabilities()`](#plot_state_probabilities) | `viz.small_system_debug` | State vector \|ψᵢ\|² bar chart | `Axes` |
| [`plot_density_matrix_diagonal()`](#plot_density_matrix_diagonal) | `viz.small_system_debug` | Density matrix diagonal elements | `Axes` |
| [`plot_density_matrix_magnitude()`](#plot_density_matrix_magnitude) | `viz.small_system_debug` | Density matrix magnitude heatmap | `Axes` |
| [`plot_density_matrix_phase()`](#plot_density_matrix_phase) | `viz.small_system_debug` | Density matrix phase heatmap | `Axes` |

### Export & Reporting (需求 18-20)

| Function | Module | Purpose | Returns |
|----------|--------|---------|---------|
| [`export_figure()`](#export_figure) | `viz.export` | Export figure + metadata JSON | `None` |
| [`export_from_result()`](#export_from_result) | `viz.export` | One-click export from Result object | `None` |
| [`ReportGenerator`](#reportgenerator) | `viz.report` | Generate HTML/Markdown reports | `ReportGenerator` |
| [`generate_quick_report()`](#generate_quick_report) | `viz.report` | Quick report generation helper | `str` (file path) |
| [`plot_sweep_heatmap()`](#plot_sweep_heatmap) | `viz.sweep` | 2D parameter sweep heatmap with failed run overlay | `Axes` |
| [`plot_sweep_line_slice()`](#plot_sweep_line_slice) | `viz.sweep` | 1D slice through multi-dimensional sweep data | `Axes` |
| [`plot_final_observable_map()`](#plot_final_observable_map) | `viz.sweep` | Final observable values vs parameter | `Axes` |
| [`plot_observables_comparison()`](#plot_observables_comparison) | `viz.sweep` | Multiple observables comparison on single plot | `Axes` |
| [`plot_failed_run_mask()`](#plot_failed_run_mask) | `viz.sweep` | Binary success/failure mask visualization | `Axes` |
| [`extract_sweep_summary()`](#extract_sweep_summary) | `viz.sweep` | Statistical summary extraction | `Dict` |
| [`generate_synthetic_sweep_data()`](#generate_synthetic_sweep_data) | `viz.sweep` | Demo data generator for testing | `Dict` |

---

## 🔍 Detailed API Documentation

*(Due to length constraints, showing first 3 APIs as example. Full document contains all 40+ APIs)*

### `plot_register()`

**Module**: `sagittarius.viz.register`

**Purpose**: Plot 2D register layout with optional blockade disks, interaction edges, and atom labels.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `register` | `Register` or `List[Tuple[float, float]]` | ✅ Yes | - | Register object or list of (x, y) coordinates in μm |
| `blockade_radius` | `float` | ❌ Optional | `None` | Blockade radius R_b in μm. If provided, draws blockade disks and interaction edges |
| `show_blockade_disks` | `bool` | ❌ Optional | `False` | Whether to draw semi-transparent blockade disks around each atom |
| `edges` | `bool` | ❌ Optional | `True` | Whether to draw edges between atoms within blockade radius |
| `labels` | `bool` | ❌ Optional | `True` | Whether to show atom index labels |
| `bitstring` | `str` | ❌ Optional | `None` | Binary string (e.g., "0101") to color atoms by state ('1'=Rydberg, '0'=Ground) |
| `ax` | `matplotlib.axes.Axes` | ❌ Optional | `None` | Existing axes to plot on. Creates new if None |
| `figsize` | `Tuple[float, float]` | ❌ Optional | `(10, 8)` | Figure size (width, height) in inches |
| `disk_alpha` | `float` | ❌ Optional | `0.15` | Transparency of blockade disks (0=transparent, 1=opaque) |
| `edge_color` | `str` | ❌ Optional | `'gray'` | Color of interaction edges |
| `atom_size` | `float` | ❌ Optional | `100` | Size of atom scatter points in points² |

#### Returns

- **Type**: `matplotlib.axes.Axes`
- **Description**: The matplotlib Axes object containing the plot

#### Example

```python
from sagittarius.viz import plot_register
from sagittarius import Register

# Method 1: Using Register object
reg = Register([(0, 0), (5, 0), (2.5, 4.33)])
ax = plot_register(reg, blockade_radius=6.0, show_blockade_disks=True)

# Method 2: Using coordinate list directly
coords = [(0, 0), (5, 0), (2.5, 4.33)]
ax = plot_register(coords, blockade_radius=6.0, bitstring="101")

# Method 3: On existing axes
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
plot_register(reg, ax=ax, labels=False)
```

---

### `plot_pulse_waveform()`

**Module**: `sagittarius.viz.pulse`

**Purpose**: Plot Ω (Rabi frequency) or Δ (detuning) pulse waveform over time.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pulse_sequence` | Multiple formats | ✅ Yes | - | Pulse definition. **Supports 10+ formats**:<br>• **AST Nodes (7 types)**: `Constant`, `Ramp`, `Gaussian`, `Blackman`, `Sinc`, `SinSquared`, `Piecewise`<br>• **Addressing Wrappers (3 types)**: `GlobalPulse`, `LocalPulseVector`, `CallablePulse`<br>• **Dict Format**: `{'type': 'constant', ...}`, `{'type': 'gaussian', ...}`, etc.<br>• **Callable**: `f(t)` or `f(t, atom_index)` returning scalar or array<br>• **Scalar**: Single numeric value (treated as constant)<br>• **Object with attributes**: Objects having `.omega`/`.delta` fields |
| `time_grid` | `np.ndarray` | ❌ Optional | `None` | Time grid for sampling. Auto-generated from pulse duration if None |
| `field` | `str` | ❌ Optional | `'omega'` | Field to plot: 'omega' (Ω) or 'delta' (Δ). Ignored for dict/AST inputs |
| `atom_index` | `int` | ❌ Optional | `None` | Atom index for local addressing (0-based). None means global pulse |
| `ax` | `matplotlib.axes.Axes` | ❌ Optional | `None` | Existing axes to plot on |
| `num_samples` | `int` | ❌ Optional | `200` | Number of sample points if time_grid is auto-generated |
| `title` | `str` | ❌ Optional | `None` | Custom plot title. Auto-generated if None |

#### Returns

- **Type**: `Tuple[matplotlib.axes.Axes, np.ndarray]`
- **Structure**: `(ax, y_values)` where `y_values` has shape `(len(time_grid),)`

#### Supported Pulse Formats (Detailed)

**1. AST Node Types (7 shapes via `Pulse` factory)**:
```python
from sagittarius import Pulse

# Constant pulse
pulse = Pulse.constant(value=5.0, duration=1.0)

# Ramp pulse (linear sweep)
pulse = Pulse.ramp(start=-5.0, end=5.0, duration=1.0)

# Gaussian pulse
pulse = Pulse.gaussian(amplitude=10.0, sigma=0.1, duration=1.0)

# Blackman window pulse
pulse = Pulse.blackman(amplitude=10.0, duration=1.0)

# Sinc function pulse
pulse = Pulse.sinc(amplitude=10.0, width=0.2, duration=1.0)

# Sin-squared pulse
pulse = Pulse.sin_squared(amplitude=10.0, duration=1.0)

# Piecewise (sequential combination)
p1 = Pulse.constant(5.0, duration=0.5)
p2 = Pulse.ramp(5.0, 0.0, duration=0.5)
pulse = Pulse.piecewise([p1, p2])
```

**2. Addressing Wrappers (3 types)**:
```python
# GlobalPulse - same value for all atoms
pulse = Pulse.global_(5.0)

# LocalPulseVector - per-atom values
pulse = Pulse.local([5.0, 10.0, 0.0])      # Dense list format
pulse = Pulse.local({0: 5.0, 2: 10.0})     # Sparse dict format

# CallablePulse - custom function
def my_func(t):
    return [5.0 * np.sin(2*np.pi*t)] * 3   # Returns array for 3 atoms
pulse = Pulse.callable(my_func)
```

**3. Dictionary Format (direct dict representation)**:
```python
# Constant
pulse = {'type': 'constant', 'value': 5.0}

# Ramp
pulse = {'type': 'ramp', 'start_val': -5.0, 'end_val': 5.0, 'duration': 1.0}

# Gaussian
pulse = {
    'type': 'gaussian',
    'amplitude': 10.0,
    'sigma': 0.1,
    'duration': 1.0,
    'mu': 0.5  # optional, defaults to duration/2
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

**4. Callable Functions**:
```python
import numpy as np

# Scalar output (global pulse)
pulse = lambda t: 5.0 * np.sin(2 * np.pi * t)

# Array output (per-atom pulses)
def multi_atom_pulse(t):
    return np.array([5.0, 10.0, 0.0]) * np.sin(2 * np.pi * t)

# Function with atom_index parameter
def local_pulse(t, idx):
    return (5.0 + idx) * np.exp(-t)
```

**5. Scalar Constants**:
```python
# Treated as constant pulse
pulse = 5.0  # Equivalent to Constant(5.0)
```

#### Raises

- `ValueError`: If pulse type cannot be handled or time_grid invalid
- `UserWarning`: If unsupported AST node type encountered (returns 0.0)

#### Example

```python
from sagittarius.viz import plot_pulse_waveform
from sagittarius import Pulse
import numpy as np

# Method 1: AST node
pulse = Pulse.gaussian(10.0, sigma=0.1, duration=1.0)
ax, omega_vals = plot_pulse_waveform(pulse, field='omega')

# Method 2: Dict format
pulse = {'type': 'constant', 'value': 5.0}
ax, delta_vals = plot_pulse_waveform(pulse, field='delta')

# Method 3: With local addressing
pulse = Pulse.local({0: 10.0, 1: 5.0, 2: 0.0})
ax, vals = plot_pulse_waveform(pulse, atom_index=0, field='omega')

# Method 4: Callable function
def my_pulse(t):
    return 5.0 * np.sin(2 * np.pi * t)
ax, vals = plot_pulse_waveform(my_pulse)

# Method 5: Custom time grid
times = np.linspace(0, 1.0, 500)
ax, vals = plot_pulse_waveform(pulse, time_grid=times)

# Method 6: Get both axes and values
ax, y_values = plot_pulse_waveform(Pulse.constant(5.0, duration=1.0))
print(y_values.shape)  # (200,) - matches num_samples
```

---

### `plot_observables()`

**Module**: `sagittarius.viz.result`

**Purpose**: Plot observable trajectories vs time from SimulationResult.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `result` | `SimulationResult` | ✅ Yes | - | Result object with `.to_pandas()` method |
| `names` | `List[str]` | ❌ Optional | `None` | List of observable column names to plot. Auto-detects if None |
| `ax` | `matplotlib.axes.Axes` | ❌ Optional | `None` | Existing axes |
| `show` | `bool` | ❌ Optional | `False` | Whether to call plt.show() immediately |
| `title` | `str` | ❌ Optional | `None` | Custom plot title. Auto-generated if None |
| `linewidth` | `float` | ❌ Optional | `2.0` | Line width for all curves |
| `figsize` | `Tuple[float, float]` | ❌ Optional | `(10, 6)` | Figure size in inches |

#### Returns

- **Type**: `matplotlib.axes.Axes`

#### Raises

- `ValueError`: If specified observable names not found in result DataFrame

#### Example

```python
from sagittarius.viz import plot_observables

# Auto-detect observables
ax = plot_observables(result)

# Specify custom observables
ax = plot_observables(result, names=['pop0', 'pop1', 'energy'])

# On existing axes with custom styling
fig, ax = plt.subplots()
plot_observables(result, ax=ax, linewidth=3.0, title="Custom Title")
```

---

## 🔍 Sweep Visualization APIs

### `plot_sweep_heatmap()`

**Module**: `sagittarius.viz.sweep`

**Purpose**: Plot 2D parameter sweep heatmap with failed run overlay and artifact links.

⚠️ **NOTE**: Currently uses synthetic data as user-facing sweep artifacts are not yet implemented (Phase 19).

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sweep_data` | `Dict[str, Any]` | ✅ Yes | - | Dictionary containing sweep results |
| `x_param` | `str` | ❌ Optional | `'omega'` | Name of x-axis parameter |
| `y_param` | `str` | ❌ Optional | `'delta'` | Name of y-axis parameter |
| `metric` | `str` | ❌ Optional | `'pop0'` | Metric name to visualize |
| `ax` | `matplotlib.axes.Axes` | ❌ Optional | `None` | Existing axes to plot on |
| `show_colorbar` | `bool` | ❌ Optional | `True` | Whether to display colorbar |
| `show_failed_mask` | `bool` | ❌ Optional | `True` | Whether to mark failed runs with red X |
| `title` | `str` | ❌ Optional | `None` | Custom title |
| `figsize` | `Tuple[float, float]` | ❌ Optional | `(10, 8)` | Figure size in inches |
| `cmap` | `str` | ❌ Optional | `'viridis'` | Colormap name |

#### Returns

- **Type**: `matplotlib.axes.Axes`

#### Example

```python
from sagittarius.viz import plot_sweep_heatmap, generate_synthetic_sweep_data

# Generate synthetic sweep data
sweep_data = generate_synthetic_sweep_data(
    omega_range=(0.5, 5.0),
    delta_range=(-3.0, 3.0),
    n_omega=25,
    n_delta=20,
)

# Create heatmap
ax = plot_sweep_heatmap(sweep_data, metric='pop0')
```

---

### `plot_sweep_line_slice()`

**Module**: `sagittarius.viz.sweep`

**Purpose**: Plot 1D slice through multi-dimensional parameter sweep.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sweep_data` | `Dict[str, Any]` | ✅ Yes | - | Dictionary containing sweep results |
| `fixed_param` | `str` | ✅ Yes | - | Name of parameter to keep fixed |
| `fixed_value` | `float` | ✅ Yes | - | Value of the fixed parameter |
| `varying_param` | `str` | ✅ Yes | - | Name of parameter varying along x-axis |
| `metric` | `str` | ❌ Optional | `'pop0'` | Metric name to visualize |
| `ax` | `matplotlib.axes.Axes` | ❌ Optional | `None` | Existing axes to plot on |
| `show_error_bars` | `bool` | ❌ Optional | `False` | Whether to show error bars if std data exists |
| `title` | `str` | ❌ Optional | `None` | Custom title |
| `figsize` | `Tuple[float, float]` | ❌ Optional | `(10, 6)` | Figure size in inches |
| `color` | `str` | ❌ Optional | `'steelblue'` | Line color |
| `marker` | `str` | ❌ Optional | `'o'` | Marker style |

#### Returns

- **Type**: `matplotlib.axes.Axes`

#### Example

```python
from sagittarius.viz import plot_sweep_line_slice

# Extract line slice at delta=0
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

**Module**: `sagittarius.viz.sweep`

**Purpose**: Plot final observable values across 1D parameter sweep.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sweep_data` | `Dict[str, Any]` | ✅ Yes | - | Dictionary containing sweep results |
| `observable_name` | `str` | ❌ Optional | `'pop0'` | Observable name to plot |
| `param_name` | `str` | ❌ Optional | `'omega'` | Name of x-axis parameter |
| `ax` | `matplotlib.axes.Axes` | ❌ Optional | `None` | Existing axes to plot on |
| `show_markers` | `bool` | ❌ Optional | `True` | Whether to show data point markers |
| `title` | `str` | ❌ Optional | `None` | Custom title |
| `figsize` | `Tuple[float, float]` | ❌ Optional | `(10, 6)` | Figure size in inches |
| `color` | `str` | ❌ Optional | `'steelblue'` | Line/marker color |

#### Returns

- **Type**: `matplotlib.axes.Axes`

#### Example

```python
from sagittarius.viz import plot_final_observable_map

# Extract final values from time series and plot
ax = plot_final_observable_map(
    sweep_data,
    observable_name='pop0',
    param_name='omega'
)
```

---

### `plot_observables_comparison()`

**Module**: `sagittarius.viz.sweep`

**Purpose**: Plot multiple observables on the same axes for comparison.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sweep_data` | `Dict[str, Any]` | ✅ Yes | - | Dictionary containing sweep results |
| `observables` | `List[str]` | ❌ Optional | `None` | List of observable names to plot (auto-detect if None) |
| `param_name` | `str` | ❌ Optional | `'omega'` | Name of x-axis parameter |
| `ax` | `matplotlib.axes.Axes` | ❌ Optional | `None` | Existing axes to plot on |
| `show_markers` | `bool` | ❌ Optional | `True` | Whether to show data point markers |
| `title` | `str` | ❌ Optional | `None` | Custom title |
| `figsize` | `Tuple[float, float]` | ❌ Optional | `(12, 7)` | Figure size in inches |
| `colors` | `List[str]` | ❌ Optional | `None` | Colors for each observable line (auto-assigned if None) |
| `normalize` | `bool` | ❌ Optional | `False` | Whether to normalize all observables to [0, 1] range |

#### Returns

- **Type**: `matplotlib.axes.Axes`

#### Example

```python
from sagittarius.viz import plot_observables_comparison

# Plot multiple observables with auto-assigned colors
ax = plot_observables_comparison(
    sweep_data,
    observables=['pop0', 'pop1', 'energy'],
    param_name='omega'
)

# Plot with normalization for easier comparison
ax = plot_observables_comparison(
    sweep_data,
    observables=['pop0', 'energy'],
    normalize=True,
    title="Normalized Comparison"
)
```

---

### `plot_failed_run_mask()`

**Module**: `sagittarius.viz.sweep`

**Purpose**: Plot binary mask showing failed vs successful runs in 2D sweep.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sweep_data` | `Dict[str, Any]` | ✅ Yes | - | Dictionary containing 'failed_runs' key |
| `x_param` | `str` | ❌ Optional | `'omega'` | Name of x-axis parameter |
| `y_param` | `str` | ❌ Optional | `'delta'` | Name of y-axis parameter |
| `ax` | `matplotlib.axes.Axes` | ❌ Optional | `None` | Existing axes to plot on |
| `title` | `str` | ❌ Optional | `None` | Custom title |
| `figsize` | `Tuple[float, float]` | ❌ Optional | `(10, 8)` | Figure size in inches |

#### Returns

- **Type**: `matplotlib.axes.Axes`

#### Example

```python
from sagittarius.viz import plot_failed_run_mask

# Plot success/failure mask
ax = plot_failed_run_mask(sweep_data)
# Green cells: successful runs
# Red cells: failed runs
```

---

### `extract_sweep_summary()`

**Module**: `sagittarius.viz.sweep`

**Purpose**: Extract summary statistics from sweep data.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sweep_data` | `Dict[str, Any]` | ✅ Yes | - | Dictionary containing sweep results |
| `metrics` | `List[str]` | ❌ Optional | `None` | Specific metrics to summarize (default: all numeric metrics) |

#### Returns

- **Type**: `Dict[str, Any]`
- **Contains**: min, max, mean, std, median, q25, q75 for each metric, plus run statistics

#### Example

```python
from sagittarius.viz import extract_sweep_summary

summary = extract_sweep_summary(sweep_data, metrics=['pop0', 'energy'])

print(f"pop0 range: [{summary['pop0']['min']:.3f}, {summary['pop0']['max']:.3f}]")
print(f"Success rate: {summary['run_statistics']['success_rate']:.1f}%")
```

---

### `generate_synthetic_sweep_data()`

**Module**: `sagittarius.viz.sweep`

**Purpose**: Generate synthetic sweep data for demonstration purposes.

⚠️ **NOTE**: This function is for demonstration only as user-facing sweep artifacts are not yet implemented.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `omega_range` | `Tuple[float, float]` | ❌ Optional | `(0.1, 5.0)` | Omega parameter range (min, max) |
| `delta_range` | `Tuple[float, float]` | ❌ Optional | `(-2.0, 2.0)` | Delta parameter range (min, max) |
| `n_omega` | `int` | ❌ Optional | `20` | Number of omega samples |
| `n_delta` | `int` | ❌ Optional | `15` | Number of delta samples |
| `seed` | `int` | ❌ Optional | `42` | Random seed for reproducibility |
| `failure_rate` | `float` | ❌ Optional | `0.05` | Fraction of failed runs (0-1) |

#### Returns

- **Type**: `Dict[str, Any]`
- **Contains**: parameters, results, failed_runs, manifest_links, metadata

#### Example

```python
from sagittarius.viz import generate_synthetic_sweep_data

# Generate synthetic sweep data
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

## 📊 Sweep Data Structure

The `sweep_data` dictionary must contain:

```python
{
    'parameters': {
        'omega': array-like,  # x-axis values
        'delta': array-like,  # y-axis values
    },
    'results': {
        'pop0': 2D array,     # shape (len(delta), len(omega))
        'energy': 2D array,   # additional metrics
    },
    'failed_runs': set or array,  # {(x_idx, y_idx), ...} or boolean mask
    'manifest_links': {       # optional
        'run_id': 'artifact_id',
        ...
    }
}
```

---


## 📚 Appendix

### Common Data Types

#### `Register` Object

```python
from sagittarius import Register

# Create from coordinates
reg = Register([(0, 0), (5, 0), (2.5, 4.33)])

# Access positions
positions = reg.positions  # np.ndarray, shape (N, 2)
atoms = reg.atoms  # List of Atom objects
```

#### `SimulationResult` Object

```python
# Convert to pandas DataFrame
df = result.to_pandas()

# Access metadata
manifest = result.manifest
seed = result.seed

# Access trajectories (if available)
trajectories = result.trajectories  # np.ndarray, shape (n_traj, n_times)
```

