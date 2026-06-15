# Sagittarius Test Suite 🧪

This directory contains the comprehensive test suite for the Sagittarius Python SDK and Julia backend.

## 📁 Directory Structure
- `tests/`: Integrated tests (run via `pytest`).
- `__pycache__/`: Local Python bytecode cache (ignored by Git).

## 🔍 Test Categories

### 1. ⚖️ Scientific Integrity (`test_invariants.py`, `test_benchmarks.py`)
- **Physical Invariants**: Verifies norm conservation ($||\psi||^2=1$) and trace preservation ($Tr(\rho)=1$) across all solvers.
- **Analytic Benchmarks**: Compares numerical results against theoretical limits:
    - **Rabi Oscillations**: Cycle frequency and peak amplitude.
    - **Landau-Zener**: Transition probability $P_{LZ} = 1 - e^{-\frac{\pi \Omega^2}{2|v|}}$.

### 2. 🫧 Open Quantum Systems (`test_mc_trajectories.py`)
- **MCWF vs Lindblad**: Verifies that the Monte Carlo Trajectory solver converges to the Lindblad Master Equation as $N_{traj} \to \infty$.
- **Dissipation**: Checks Rydberg decay and dephasing dynamics.

### 3. 🚀 Performance & Scale (`test_gpu_acceleration.py`, `test_cluster.py`)
- **GPU Parity**: Ensures that GPU backends (CUDA/AMDGPU/Metal) yield identical results to the CPU.
- **Cluster Connectivity**: Verifies worker orchestration and `pmap` distribution.

### 4. 📍 Advanced Features (`test_local_pulses.py`, `test_api_v2.py`, `test_pulse.py`, `test_physics.py`)
- **Local Addressing**: Verifies per-atom pulse sequence alignment.
- **API Ergonomics**: Validates `Simulation` and `SimulationResult` object behavior.
- **Pulse Shapes**: Tests complex waveforms (Piecewise, Ramp, Gaussian).
- **Functional Physics**: Quick checks for blockade and basic dynamics.

### 5. 💾 Operations (`test_serialization.py`)
- **Persistence**: Verifies JSON save/load cycles for `SimulationResult` objects.

### 6. 📈 Performance Benchmarking (`test_performance/`)
Quantitative analysis of solver throughput and scaling behavior.
- **Scaling Profiles**: Measures execution time as a function of atom count ($N$) and Hilbert space dimension.
- **Hardware Benchmarks**: CPU vs. GPU speedup comparisons across various backends.
- **Recent Results**: High-performance evaluation on **NVIDIA RTX 5070 Ti** demonstrates a **19.6x speedup** at $N=20$ atoms.
  - Detailed findings are documented in `tests/test_performance/gpu_bench_conclusion.md`.

## ✅ Passing Evidence
A test is considered passed if:
1.  **Parity**: Mean absolute error (MAE) between numerical and analytic/target results is $< 10^{-2}$.
2.  **Stability**: No numerical divergence or memory overflows occur during integration.
3.  **Invariants**: Unit norm/trace is maintained within $10^{-6}$ tolerance.

## 🛠️ Execution
```bash
cd sagittarius_py
uv run python -m pytest tests/
```

Tests marked `requires_julia_backend` exercise the Julia/PythonCall runtime and are skipped when the backend cannot initialize. To repair a local backend environment, run `uv run python -m juliapkg resolve` and instantiate the Julia project before rerunning the suite.
