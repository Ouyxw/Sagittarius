"""
Benchmark performance analysis visualization examples.

Demonstrates how to generate standardized charts from governed benchmark artifacts,
including runtime scaling, memory usage, solver comparisons, and success/failure summaries.

IMPORTANT: These visualizations are for diagnostic purposes only and should NOT be
used as hardware calibration evidence or official performance claims without proper
governance validation (SPEC-GOV-001).
"""

import numpy as np
import matplotlib.pyplot as plt
from sagittarius.viz import (
    plot_runtime_scaling,
    plot_memory_scaling,
    plot_solver_comparison,
    plot_success_failure_summary,
    plot_cpu_gpu_error_comparison,
)


def example_runtime_scaling():
    """Example 1: Runtime vs atom count scaling analysis."""
    print("=" * 80)
    print("Example 1: Runtime Scaling Analysis")
    print("=" * 80)
    
    # Simulated benchmark artifacts (in practice, load from actual benchmark runs)
    artifacts = [
        {'n_atoms': 5, 'runtime_seconds': 0.05, 'artifact_id': 'bench_001'},
        {'n_atoms': 10, 'runtime_seconds': 0.23, 'artifact_id': 'bench_002'},
        {'n_atoms': 15, 'runtime_seconds': 1.12, 'artifact_id': 'bench_003'},
        {'n_atoms': 20, 'runtime_seconds': 4.87, 'artifact_id': 'bench_004'},
        {'n_atoms': 25, 'runtime_seconds': 18.34, 'artifact_id': 'bench_005'},
        {'n_atoms': 30, 'runtime_seconds': 67.92, 'artifact_id': 'bench_006'},
    ]
    
    # Generate plot with power-law fit
    ax = plot_runtime_scaling(artifacts, show_fit=True)
    plt.tight_layout()
    plt.savefig('benchmark_runtime_scaling.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: benchmark_runtime_scaling.png")
    plt.close()
    
    print(f"  • Analyzed {len(artifacts)} benchmark runs")
    print(f"  • Atom range: {artifacts[0]['n_atoms']} - {artifacts[-1]['n_atoms']}")
    print(f"  • Runtime range: {artifacts[0]['runtime_seconds']:.2f}s - {artifacts[-1]['runtime_seconds']:.2f}s\n")


def example_memory_scaling():
    """Example 2: Memory usage vs Hilbert space dimension."""
    print("=" * 80)
    print("Example 2: Memory Scaling Analysis")
    print("=" * 80)
    
    # Simulated memory benchmarks
    artifacts = [
        {'hilbert_dim': 32, 'memory_bytes': 1024 * 50, 'artifact_id': 'mem_001'},      # 5 qubits
        {'hilbert_dim': 64, 'memory_bytes': 1024 * 200, 'artifact_id': 'mem_002'},     # 6 qubits
        {'hilbert_dim': 128, 'memory_bytes': 1024 * 800, 'artifact_id': 'mem_003'},    # 7 qubits
        {'hilbert_dim': 256, 'memory_bytes': 1024 * 3200, 'artifact_id': 'mem_004'},   # 8 qubits
        {'hilbert_dim': 512, 'memory_bytes': 1024 * 12800, 'artifact_id': 'mem_005'},  # 9 qubits
    ]
    
    # Generate plot
    ax = plot_memory_scaling(artifacts, y_unit='KB')
    plt.tight_layout()
    plt.savefig('benchmark_memory_scaling.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: benchmark_memory_scaling.png")
    plt.close()
    
    print(f"  • Analyzed {len(artifacts)} memory benchmarks")
    print(f"  • Dimension range: {artifacts[0]['hilbert_dim']} - {artifacts[-1]['hilbert_dim']}")
    print(f"  • Memory range: {artifacts[0]['memory_bytes']/1024:.0f}KB - {artifacts[-1]['memory_bytes']/1024:.0f}KB\n")


def example_solver_comparison():
    """Example 3: Solver performance comparison."""
    print("=" * 80)
    print("Example 3: Solver Comparison")
    print("=" * 80)
    
    # Simulated solver comparison results (same problem instance)
    results = [
        {'solver_name': 'Tsit5', 'metric_value': 1.23, 'metric_std': 0.05, 'artifact_id': 'solver_001'},
        {'solver_name': 'EM', 'metric_value': 2.45, 'metric_std': 0.12, 'artifact_id': 'solver_002'},
        {'solver_name': 'MCWF (100 traj)', 'metric_value': 3.67, 'metric_std': 0.23, 'artifact_id': 'solver_003'},
        {'solver_name': 'RK4', 'metric_value': 1.89, 'metric_std': 0.08, 'artifact_id': 'solver_004'},
    ]
    
    # Generate horizontal bar chart
    ax = plot_solver_comparison(results, metric='runtime', show_error_bars=True)
    plt.tight_layout()
    plt.savefig('benchmark_solver_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: benchmark_solver_comparison.png")
    plt.close()
    
    print(f"  • Compared {len(results)} solvers")
    print(f"  • Best performer: {results[0]['solver_name']} ({results[0]['metric_value']:.2f}s)\n")


def example_success_failure_summary():
    """Example 4: Benchmark success/failure statistics."""
    print("=" * 80)
    print("Example 4: Success/Failure Summary")
    print("=" * 80)
    
    # Simulated benchmark run log
    runs = []
    solvers = ['Tsit5', 'EM', 'MCWF']
    n_atoms_list = [10, 15, 20, 25]
    
    # Generate synthetic data
    np.random.seed(42)
    for solver in solvers:
        for n_atoms in n_atoms_list:
            for _ in range(5):  # 5 runs per configuration
                # Simulate success rate (decreases with problem size)
                success_prob = max(0.3, 0.95 - 0.02 * n_atoms)
                status = 'success' if np.random.random() < success_prob else 'failure'
                
                runs.append({
                    'status': status,
                    'solver': solver,
                    'n_atoms': n_atoms,
                    'artifact_id': f'run_{solver}_{n_atoms}_{_}'
                })
    
    # Generate summary grouped by solver
    ax = plot_success_failure_summary(runs, group_by='solver')
    plt.tight_layout()
    plt.savefig('benchmark_success_failure_solver.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: benchmark_success_failure_solver.png")
    plt.close()
    
    # Also generate summary grouped by problem size
    ax = plot_success_failure_summary(runs, group_by='n_atoms')
    plt.tight_layout()
    plt.savefig('benchmark_success_failure_size.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: benchmark_success_failure_size.png")
    plt.close()
    
    total_runs = len(runs)
    success_count = sum(1 for r in runs if r['status'] == 'success')
    print(f"  • Total runs: {total_runs}")
    print(f"  • Success rate: {success_count/total_runs*100:.1f}%\n")


def example_cpu_gpu_comparison():
    """Example 5: CPU vs GPU numerical accuracy comparison."""
    print("=" * 80)
    print("Example 5: CPU vs GPU Error Comparison")
    print("=" * 80)
    
    # Simulated CPU and GPU results with reference values
    observables = ['population_0', 'population_1', 'coherence_01', 'energy']
    reference_values = [0.5, 0.5, 0.3, -1.234]
    
    cpu_results = []
    gpu_results = []
    
    np.random.seed(123)
    for obs, ref in zip(observables, reference_values):
        # CPU: small errors (~1e-6)
        cpu_val = ref + np.random.normal(0, 1e-6)
        cpu_results.append({
            'observable': obs,
            'value': float(cpu_val),
            'reference_value': float(ref)
        })
        
        # GPU: slightly larger errors (~1e-5) due to floating-point differences
        gpu_val = ref + np.random.normal(0, 1e-5)
        gpu_results.append({
            'observable': obs,
            'value': float(gpu_val),
            'reference_value': float(ref)
        })
    
    # Generate comparison plot
    ax = plot_cpu_gpu_error_comparison(cpu_results, gpu_results, error_metric='relative_error')
    plt.tight_layout()
    plt.savefig('benchmark_cpu_gpu_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: benchmark_cpu_gpu_comparison.png")
    plt.close()
    
    print(f"  • Compared {len(observables)} observables")
    print(f"  • CPU typical error: ~1e-6")
    print(f"  • GPU typical error: ~1e-5\n")


def main():
    """Run all benchmark performance visualization examples."""
    print("\n" + "=" * 80)
    print("Sagittarius Benchmark Performance Visualization Examples")
    print("=" * 80)
    print("\n⚠️  IMPORTANT: All charts include 'DIAGNOSTIC VIEW' disclaimers.")
    print("   Performance conclusions must follow SPEC-GOV-001 governance.\n")
    
    try:
        example_runtime_scaling()
        example_memory_scaling()
        example_solver_comparison()
        example_success_failure_summary()
        example_cpu_gpu_comparison()
        
        print("=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)
        print("\nGenerated files:")
        print("  • benchmark_runtime_scaling.png")
        print("  • benchmark_memory_scaling.png")
        print("  • benchmark_solver_comparison.png")
        print("  • benchmark_success_failure_solver.png")
        print("  • benchmark_success_failure_size.png")
        print("  • benchmark_cpu_gpu_comparison.png")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        raise


if __name__ == '__main__':
    main()
