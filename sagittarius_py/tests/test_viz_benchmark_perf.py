"""
Tests for benchmark performance visualization utilities.
"""

import pytest
import numpy as np
import matplotlib.pyplot as plt

@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Automatically close all figures after each test to prevent memory warnings."""
    yield
    plt.close('all')
from sagittarius.viz.benchmark_perf import (
    plot_diagnostic_runtime_scaling,
    plot_diagnostic_memory_scaling,
    plot_diagnostic_solver_comparison,
    plot_diagnostic_success_failure_summary,
    plot_diagnostic_cpu_gpu_error_comparison,
)


class TestPlotRuntimeScaling:
    """Test runtime scaling visualization."""
    
    def test_basic_runtime_scaling(self):
        """Test basic runtime scaling plot with valid data."""
        artifacts = [
            {'n_atoms': 5, 'runtime_seconds': 0.1, 'artifact_id': 'bench_001'},
            {'n_atoms': 10, 'runtime_seconds': 0.5, 'artifact_id': 'bench_002'},
            {'n_atoms': 15, 'runtime_seconds': 2.3, 'artifact_id': 'bench_003'},
            {'n_atoms': 20, 'runtime_seconds': 8.7, 'artifact_id': 'bench_004'},
        ]
        
        ax = plot_diagnostic_runtime_scaling(artifacts, show_fit=True)
        assert ax is not None
        assert ax.get_xlabel() == 'Number of Atoms (N)'
        assert ax.get_ylabel() == 'Runtime (seconds)'
        plt.close()
    
    def test_missing_n_atoms_field(self):
        """Test error when n_atoms field is missing."""
        artifacts = [
            {'runtime_seconds': 0.1},  # Missing n_atoms
        ]
        
        with pytest.raises(ValueError, match="missing 'n_atoms'"):
            plot_diagnostic_runtime_scaling(artifacts)
    
    def test_missing_runtime_field(self):
        """Test error when runtime_seconds field is missing."""
        artifacts = [
            {'n_atoms': 5},  # Missing runtime_seconds
        ]
        
        with pytest.raises(ValueError, match="missing 'runtime_seconds'"):
            plot_diagnostic_runtime_scaling(artifacts)
    
    def test_custom_title(self):
        """Test custom title override."""
        artifacts = [
            {'n_atoms': 5, 'runtime_seconds': 0.1},
            {'n_atoms': 10, 'runtime_seconds': 0.5},
        ]
        
        ax = plot_diagnostic_runtime_scaling(artifacts, title="Custom Title")
        assert "Custom Title" in ax.get_title()
        plt.close()
    
    def test_no_fit_with_insufficient_data(self):
        """Test that fit is skipped with < 3 data points."""
        artifacts = [
            {'n_atoms': 5, 'runtime_seconds': 0.1},
            {'n_atoms': 10, 'runtime_seconds': 0.5},
        ]
        
        ax = plot_diagnostic_runtime_scaling(artifacts, show_fit=True)
        # Should not raise error, just skip fitting
        assert ax is not None
        plt.close()


class TestPlotMemoryScaling:
    """Test memory scaling visualization."""
    
    def test_basic_memory_scaling(self):
        """Test basic memory scaling plot."""
        artifacts = [
            {'hilbert_dim': 32, 'memory_bytes': 1024 * 100, 'artifact_id': 'mem_001'},
            {'hilbert_dim': 64, 'memory_bytes': 1024 * 500, 'artifact_id': 'mem_002'},
            {'hilbert_dim': 128, 'memory_bytes': 1024 * 2000, 'artifact_id': 'mem_003'},
        ]
        
        ax = plot_diagnostic_memory_scaling(artifacts, y_unit='KB')
        assert ax is not None
        assert 'KB' in ax.get_ylabel()
        plt.close()
    
    def test_invalid_unit(self):
        """Test error with invalid memory unit."""
        artifacts = [
            {'hilbert_dim': 32, 'memory_bytes': 1024},
        ]
        
        with pytest.raises(ValueError, match="Invalid y_unit"):
            plot_diagnostic_memory_scaling(artifacts, y_unit='TB')
    
    def test_missing_hilbert_dim(self):
        """Test error when hilbert_dim is missing."""
        artifacts = [
            {'memory_bytes': 1024},
        ]
        
        with pytest.raises(ValueError, match="missing 'hilbert_dim'"):
            plot_diagnostic_memory_scaling(artifacts)


class TestPlotSolverComparison:
    """Test solver comparison visualization."""
    
    def test_basic_solver_comparison(self):
        """Test basic solver comparison plot."""
        results = [
            {'solver_name': 'Tsit5', 'metric_value': 1.23, 'metric_std': 0.05},
            {'solver_name': 'EM', 'metric_value': 2.45, 'metric_std': 0.12},
            {'solver_name': 'MCWF', 'metric_value': 3.67, 'metric_std': 0.23},
        ]
        
        ax = plot_diagnostic_solver_comparison(results, metric='runtime')
        assert ax is not None
        assert 'Runtime' in ax.get_xlabel()
        plt.close()
    
    def test_without_error_bars(self):
        """Test solver comparison without error bars."""
        results = [
            {'solver_name': 'Tsit5', 'metric_value': 1.23},
            {'solver_name': 'EM', 'metric_value': 2.45},
        ]
        
        ax = plot_diagnostic_solver_comparison(results, show_error_bars=False)
        assert ax is not None
        plt.close()
    
    def test_missing_solver_name(self):
        """Test error when solver_name is missing."""
        results = [
            {'metric_value': 1.23},
        ]
        
        with pytest.raises(ValueError, match="missing 'solver_name'"):
            plot_diagnostic_solver_comparison(results)


class TestPlotSuccessFailureSummary:
    """Test success/failure summary visualization."""
    
    def test_basic_summary(self):
        """Test basic success/failure summary."""
        runs = [
            {'status': 'success', 'solver': 'Tsit5', 'n_atoms': 10},
            {'status': 'success', 'solver': 'Tsit5', 'n_atoms': 15},
            {'status': 'failure', 'solver': 'EM', 'n_atoms': 20},
            {'status': 'success', 'solver': 'EM', 'n_atoms': 10},
        ]
        
        ax = plot_diagnostic_success_failure_summary(runs, group_by='solver')
        assert ax is not None
        assert 'Solver' in ax.get_xlabel()
        plt.close()
    
    def test_group_by_n_atoms(self):
        """Test grouping by atom count."""
        runs = [
            {'status': 'success', 'solver': 'Tsit5', 'n_atoms': 10},
            {'status': 'failure', 'solver': 'Tsit5', 'n_atoms': 10},
            {'status': 'success', 'solver': 'Tsit5', 'n_atoms': 15},
        ]
        
        ax = plot_diagnostic_success_failure_summary(runs, group_by='n_atoms')
        assert ax is not None
        plt.close()
    
    def test_missing_status(self):
        """Test error when status field is missing."""
        runs = [
            {'solver': 'Tsit5'},
        ]
        
        with pytest.raises(ValueError, match="missing 'status'"):
            plot_diagnostic_success_failure_summary(runs)


class TestPlotCpuGpuErrorComparison:
    """Test CPU vs GPU error comparison."""
    
    def test_basic_comparison(self):
        """Test basic CPU vs GPU error comparison."""
        cpu_results = [
            {'observable': 'pop_0', 'value': 0.498, 'reference_value': 0.5},
            {'observable': 'pop_1', 'value': 0.502, 'reference_value': 0.5},
        ]
        gpu_results = [
            {'observable': 'pop_0', 'value': 0.497, 'reference_value': 0.5},
            {'observable': 'pop_1', 'value': 0.503, 'reference_value': 0.5},
        ]
        
        ax = plot_diagnostic_cpu_gpu_error_comparison(cpu_results, gpu_results)
        assert ax is not None
        assert 'Relative Error' in ax.get_ylabel()
        plt.close()
    
    def test_absolute_error(self):
        """Test with absolute error metric."""
        cpu_results = [
            {'observable': 'energy', 'value': -1.234, 'reference_value': -1.230},
        ]
        gpu_results = [
            {'observable': 'energy', 'value': -1.235, 'reference_value': -1.230},
        ]
        
        ax = plot_diagnostic_cpu_gpu_error_comparison(
            cpu_results, gpu_results, error_metric='absolute_error'
        )
        assert ax is not None
        plt.close()
    
    def test_no_common_observables(self):
        """Test error when no common observables."""
        cpu_results = [
            {'observable': 'pop_0', 'value': 0.5, 'reference_value': 0.5},
        ]
        gpu_results = [
            {'observable': 'pop_1', 'value': 0.5, 'reference_value': 0.5},
        ]
        
        with pytest.raises(ValueError, match="No common observables"):
            plot_diagnostic_cpu_gpu_error_comparison(cpu_results, gpu_results)
    
    def test_missing_fields(self):
        """Test error when required fields are missing."""
        cpu_results = [
            {'observable': 'pop_0'},  # Missing value and reference_value
        ]
        gpu_results = [
            {'observable': 'pop_0', 'value': 0.5, 'reference_value': 0.5},
        ]
        
        with pytest.raises(ValueError, match="missing 'value'"):
            plot_diagnostic_cpu_gpu_error_comparison(cpu_results, gpu_results)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

from sagittarius.viz.benchmark_governed import plot_runtime_scaling, validate_benchmark_artifact


def _governed_artifact(rows):
    return {
        "schema_version": "benchmark-artifact/v1",
        "artifact_type": "sagittarius.benchmark",
        "name": "visualization-governance-test",
        "parameters": {"scenario": "unit"},
        "timings": rows,
        "versions": {"schema_version": "version-info/v1"},
        "hardware": {"platform": "test"},
        "diagnostics": {"schema_version": "doctor/v2.1"},
        "run_manifests": [],
        "artifacts": {"csv": None, "markdown": None},
    }


def test_governed_runtime_plot_accepts_valid_artifact():
    artifact = _governed_artifact([
        {"n_atoms": 5, "runtime_seconds": 0.1},
        {"n_atoms": 10, "runtime_seconds": 0.5},
    ])
    assert plot_runtime_scaling(artifact) is not None


def test_governed_runtime_plot_rejects_diagnostic_rows():
    with pytest.raises(ValueError, match="benchmark-artifact/v1"):
        plot_runtime_scaling([{"n_atoms": 5, "runtime_seconds": 0.1}])


def test_governed_artifact_rejects_wrong_schema_version():
    artifact = _governed_artifact([{"n_atoms": 5, "runtime_seconds": 0.1}])
    artifact["schema_version"] = "benchmark-artifact/v0"
    with pytest.raises(ValueError, match="schema_version"):
        validate_benchmark_artifact(artifact)
