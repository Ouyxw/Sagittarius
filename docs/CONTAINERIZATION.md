# Sagittarius 容器化开发环境指南 (GPU 优化版)

本文档介绍了如何利用 Docker 和 VS Code Dev Containers 为 Sagittarius 项目（Julia 核心 + Python SDK）配置高性能、支持 GPU 的开发环境。

## 1. 环境准备

在开始之前，请确保你的宿主机满足以下条件：
- **操作系统**: Linux (推荐 Ubuntu 22.04+) 或 Windows (WSL2)。
- **Docker**: 已安装 Docker Engine。
- **GPU 支持**:
    - 已安装 NVIDIA 驱动。CUDA 12.8/Blackwell 工作流建议 Linux 驱动 `>=570.26`（Windows/WSL `>=570.65`）。
    - 已安装 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。
- **VS Code**: 已安装 [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) 扩展。

## 2. 核心配置文件说明

项目根目录下的 `.devcontainer` 包含以下核心文件：

### 2.1 Dockerfile
- **基础镜像**: `nvidia/cuda:12.8.0-devel-ubuntu22.04`，作为 CUDA 12.8+ 和 Blackwell/RTX 50 系列开发基线。
- **运行时**: 集成 Julia 1.11 系列和 Python 3.11。
- **包管理器**: 使用 `uv` 加速 Python 依赖同步。
- **CUDA.jl**: 容器构建固定安装 `CUDA.jl 6.2.0`，并设置 `CUDA.set_runtime_version!(local_toolkit=true)` 使用容器内 CUDA toolkit。
- **优化**: 构建时预编译 Julia GPU 环境，减少首次运行 GPU 任务的延迟。

### 2.2 devcontainer.json
- **GPU 透传**: 配置 `--gpus all` 允许容器访问物理显卡。
- **VS Code 插件**: 自动安装 Julia、Python、Jupyter、Ruff 等生产力插件。
- **路径映射**: 自动配置 Python 解释器和 Julia 环境路径。

## 3. 快速启动步骤

1. **克隆项目**:
   ```bash
   git clone <repository_url> Sagittarius
   cd Sagittarius
   ```

2. **在 VS Code 中打开**:
   ```bash
   code .
   ```

3. **进入容器**:
   - 当 VS Code 弹出“Reopen in Container”提示时，点击确认。
   - 或者：按 `F1` 键，输入 `Dev Containers: Reopen in Container`。

4. **验证环境**:
   容器启动并完成 `uv sync` 后，先运行诊断：
   ```bash
   cd sagittarius_py
   uv run python - <<'PY'
   from sagittarius import doctor
   print(doctor(backend="CUDA", initialize_backend=True))
   PY
   ```

   GPU parity 测试默认关闭，避免无 GPU 的 CI/开发机误初始化 CUDA。确认诊断通过后显式启用：
   ```bash
   SAGITTARIUS_ENABLE_GPU_TESTS=1 uv run python -m pytest tests/test_gpu_acceleration.py
   ```

## 4. 硬件兼容性与优雅降级

Sagittarius 设计为可在各种硬件上运行。如果协作开发者没有高端 NVIDIA GPU，请参考以下指南。

### 4.1 环境自检工具
在容器内运行以下脚本，自动检测当前硬件支持的后端：
```bash
cd sagittarius_py
uv run python check_env.py
```

### 4.2 非 GPU 环境配置
如果宿主机没有 NVIDIA 显卡，容器可能无法启动。此时需要修改 `.devcontainer/devcontainer.json`：
1. 注释掉 `runArgs` 中的 `"--runtime=nvidia"` 和 `"--gpus", "all"`。
2. 不设置 `SAGITTARIUS_ENABLE_GPU_TESTS=1`。
3. 将应用代码中的 `SolverConfig(use_gpu=True)` 修改为 `False`。

### 4.3 跨平台 GPU 支持
- **Apple Silicon (Mac)**: 支持 `gpu_backend="Metal"`。
- **AMD GPU**: 支持 `gpu_backend="AMDGPU"`。

## 5. GPU 性能优化细节

为了实现最佳吞吐量，代码层面对 GPU 进行了以下优化：
- **无损观测值计算**: `RydbergPopulation` 已移除 `CUDA.@allowscalar`。所有观测值计算都在 GPU 显存内通过向量化操作（broadcasting/mapreduce）完成。
- **算子缓存**: `solve_schrodinger_gpu` 会自动缓存 `CuSparseMatrixCSC` 形式的哈密顿量算子。
- **多后端兼容**: 容器环境支持 CUDA，并为 AMDGPU 和 Metal 留出了扩展接口。

## 5. 常见问题 (FAQ)

**Q: 容器构建非常慢怎么办？**
A: 第一次构建涉及下载 CUDA 12.8 镜像、安装 `CUDA.jl 6.2.0` 和预编译 Julia 包，耗时较长是正常现象。建议配置 `JULIA_PKG_SERVER` 镜像。

**Q: 容器内找不到 GPU (CUDA Error)？**
A: 请确认宿主机执行 `nvidia-smi` 正常，Docker 已配置 `--gpus all` 权限，并在容器内运行 `doctor(backend="CUDA", initialize_backend=True)` 查看 `CUDA_PASSTHROUGH_UNAVAILABLE`、`CUDA_DRIVER_RUNTIME_MISMATCH` 或 `CUDA_BLACKWELL_DRIVER_BELOW_RECOMMENDED` 等诊断码。

---
*Last updated: 2026-06-15*
