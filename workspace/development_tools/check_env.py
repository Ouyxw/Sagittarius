import os
import sys
import platform
import subprocess

def print_header(text):
    print(f"\n{'-'*20} {text} {'-'*20}")

def check_python():
    print_header("Python Environment")
    print(f"Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    try:
        import numpy
        print(f"NumPy: {numpy.__version__}")
    except ImportError:
        print("NumPy: NOT INSTALLED")

def check_julia_integration():
    print_header("Julia & Juliacall Integration")
    try:
        from juliacall import Main as jl
        print("Juliacall: Connected successfully")
        version = jl.seval("VERSION")
        print(f"Julia Version: {version}")
        
        # Check Project environment
        project_path = jl.seval("import Pkg; Pkg.project().path")
        print(f"Julia Project: {project_path}")
    except Exception as e:
        print(f"Juliacall/Julia: FAILED - {str(e)}")
        return None
    return jl

def check_gpu_backends(jl):
    print_header("Hardware Acceleration (GPU)")
    if jl is None:
        print("Skipping GPU checks due to Julia failure.")
        return

    # 1. Check CUDA (NVIDIA)
    try:
        jl.seval("using CUDA")
        cuda_functional = jl.seval("CUDA.functional()")
        if cuda_functional:
            device = jl.seval("CUDA.name(CUDA.device())")
            mem = jl.seval("CUDA.totalmem(CUDA.device()) / 1024^3")
            print(f"[✅] CUDA: Functional (Device: {device}, Memory: {mem:.2f} GB)")
        else:
            print("[❌] CUDA: Driver found but not functional (Check Container Toolkit)")
    except:
        print("[ ] CUDA: Not available/not loaded")

    # 2. Check Metal (Apple Silicon)
    try:
        jl.seval("using Metal")
        if jl.seval("Metal.functional()"):
            print("[✅] Metal: Functional (Apple Silicon)")
        else:
            print("[❌] Metal: Not functional")
    except:
        print("[ ] Metal: Not available (Requires macOS)")

    # 3. Check AMDGPU (ROCm)
    try:
        jl.seval("using AMDGPU")
        if jl.seval("AMDGPU.functional()"):
            print("[✅] AMDGPU: Functional")
        else:
            print("[❌] AMDGPU: Not functional")
    except:
        print("[ ] AMDGPU: Not available")

def check_docker_context():
    print_header("Container Context")
    is_docker = os.path.exists('/.dockerenv')
    print(f"Running inside Docker: {'YES' if is_docker else 'NO'}")
    
    if is_docker:
        try:
            # Check for NVIDIA runtime
            res = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True)
            if "libcuda.so" in res.stdout:
                print("NVIDIA Library Mapping: FOUND")
            else:
                print("NVIDIA Library Mapping: NOT FOUND (Check --runtime=nvidia)")
        except:
            pass

def main():
    print("====================================================")
    print("      Sagittarius Environment Diagnostic Tool       ")
    print("====================================================")
    
    check_python()
    check_docker_context()
    jl = check_julia_integration()
    
    # Track functional backends
    results = []
    if jl:
        # Check CUDA
        try:
            jl.seval("using CUDA")
            if jl.seval("CUDA.functional()"):
                results.append("CUDA")
        except: pass
        
        # Check others...
        try:
            if jl.seval("using Metal; Metal.functional()"): results.append("Metal")
        except: pass
        try:
            if jl.seval("using AMDGPU; AMDGPU.functional()"): results.append("AMDGPU")
        except: pass

    check_gpu_backends(jl)
    
    print("\n" + "="*52)
    print("Recommendation:")
    if results:
        print(f">>> System is GPU-READY ({', '.join(results)}). Use SolverConfig(use_gpu=True).")
    else:
        print(">>> No functional GPU detected. Use SolverConfig(use_gpu=False).")
    print("="*52 + "\n")

if __name__ == "__main__":
    main()
