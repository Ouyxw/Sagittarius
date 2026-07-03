# 使用 NVIDIA CUDA 12.8 基础镜像；CUDA 12.8 GA 是 Blackwell/RTX 50 系列的最低推荐容器基线。
FROM nvidia/cuda:12.8.0-devel-ubuntu22.04

# 设置非交互模式
ENV DEBIAN_FRONTEND=noninteractive

# 安装基础依赖：Python, Git, Curl, Build-essential, Node.js, GPG
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    git \
    curl \
    build-essential \
    libatomic1 \
    gnupg2 \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# 全局安装 Gemini CLI 和 Codex CLI
RUN npm install -g @google/gemini-cli @openai/codex

# 设置 Python 软链接
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# 安装 uv (高性能 Python 包管理器)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 安装 Julia，并固定到 juliacall 当前兼容的 1.11 系列
RUN curl -fsSL https://install.julialang.org | sh -s -- -y && \
    /root/.juliaup/bin/juliaup add 1.11 && \
    /root/.juliaup/bin/juliaup default 1.11
ENV PATH="/root/.juliaup/bin:${PATH}"

# 设置 Julia 镜像 (可选，加速国内下载)
# ENV JULIA_PKG_SERVER="https://mirrors.ustc.edu.cn/julia"

# 设置工作目录
WORKDIR /workspaces/Sagittarius

# 拷贝项目文件 (使用通配符确保即使 uv.lock 不存在也不会报错)
COPY Sagittarius.jl/Project.toml ./Sagittarius.jl/
COPY sagittarius_py/pyproject.toml sagittarius_py/uv.lock* ./sagittarius_py/

# 强制重新生成 CUDA-only 项目环境，并锁定使用本地 CUDA 运行时。
# CUDA.jl 6.2.x includes current CUDA 13.x runtime selection fixes while remaining compatible with CUDA 12.8+ driver/toolkit workflows.
# AMDGPU/Metal are intentionally not installed in this CUDA parity environment because their current dependency bounds conflict with CUDA.jl 6.2.x.
RUN JULIA_PKG_PRECOMPILE_AUTO=0 julia -e 'using Pkg; \
    Pkg.Registry.add("General"); \
    Pkg.activate("Sagittarius_Env", shared=true); \
    Pkg.add(["OrdinaryDiffEq", "StaticArrays", "DiffEqCallbacks", "SciMLBase", "LinearAlgebra", "SparseArrays", "Random", "Distributed", "PythonCall", "CondaPkg", "PrecompileTools", "JSON", "Parsers"]); \
    Pkg.add(Pkg.PackageSpec(name="CUDA", version="6.2.0")); \
    Pkg.instantiate(); \
    using CUDA; CUDA.set_runtime_version!(local_toolkit=true); \
    Pkg.precompile()'

# 将生成的环境链接到项目目录（可选，方便后续使用）
ENV JULIA_PROJECT="@Sagittarius_Env"
ENV PYTHON_JULIAPKG_PROJECT="/root/.julia/environments/Sagittarius_Env"

# 预安装 Python 依赖 (如果 uv.lock 不存在则忽略错误，由 postCreate 处理)
RUN cd sagittarius_py && (uv sync || echo "uv.lock not found, skipping sync in build stage")

# 暴露常用的 Jupyter/Dashboard 端口
EXPOSE 8888 8050

# 默认启动 Bash
CMD ["/bin/bash"]
