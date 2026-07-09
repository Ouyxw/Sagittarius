"""
Tests for diagnostic visualization utilities.

Validates time grid, Lindblad validation, MCWF comparison, and trajectory statistics plots.
"""

import numpy as np
import pytest
import matplotlib.pyplot as plt
from unittest.mock import Mock, MagicMock

from sagittarius.viz.diagnostics import (
    plot_time_grid_diagnostics,
    plot_lindblad_validation,
    plot_mcwf_vs_lindblad,
    plot_trajectory_statistics,
)


@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Automatically close all figures after each test to prevent memory warnings."""
    yield
    plt.close('all')


class MockResult:
    """Mock SimulationResult for testing."""
    def __init__(self, data_dict, manifest=None):
        self.data = data_dict
        self.metadata = {}
        self.diagnostics = {}
        self.manifest = manifest or {}  # Support artifact tracking
        self.t = np.array(data_dict.get('t', []))
        self.trajectories = None
    
    def to_pandas(self):
        import pandas as pd
        return pd.DataFrame(self.data)


def create_mock_result(n_times=50, n_atoms=3):
    """Create a mock result with time series data."""
    t = np.linspace(0, 1.0, n_times)
    data = {'t': t}
    for i in range(n_atoms):
        data[f'pop{i}'] = 0.5 + 0.3 * np.sin(2 * np.pi * t)
    return MockResult(data)


class TestTimeGridDiagnostics:
    """Tests for plot_time_grid_diagnostics."""
    
    def test_normal_data(self):
        """Test with normal time series data."""
        result = create_mock_result(n_times=50)
        ax = plot_time_grid_diagnostics(result)
        
        assert ax is not None
        assert len(ax.collections) > 0  # Scatter plot present
        
        plt.close()
    
    def test_missing_time_column(self):
        """Test error when time column is missing."""
        result = MockResult({'pop0': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="No time column 't' found"):
            plot_time_grid_diagnostics(result)
    
    def test_insufficient_time_points(self):
        """Test error with single time point."""
        result = MockResult({'t': [0.5], 'pop0': [1.0]})
        
        with pytest.raises(ValueError, match="Insufficient time points"):
            plot_time_grid_diagnostics(result)
    
    def test_adaptive_steps_display(self):
        """Test adaptive step size color coding."""
        result = create_mock_result(n_times=30)
        ax = plot_time_grid_diagnostics(result, show_adaptive=True)
        
        # Should have scatter plot with colorbar
        assert len(ax.collections) >= 1
        
        plt.close()
    
    def test_disclaimer_present(self):
        """Test that diagnostic disclaimer is shown."""
        result = create_mock_result()
        ax = plot_time_grid_diagnostics(result)
        
        # Check for disclaimer text in axes
        texts = [child for child in ax.get_children() 
                if hasattr(child, 'get_text')]
        disclaimer_found = any("DIAGNOSTIC VIEW" in str(t.get_text()) 
                              for t in texts if hasattr(t, 'get_text'))
        assert disclaimer_found
        
        plt.close()
    
    def test_artifact_link_display(self):
        """Test artifact link is displayed when manifest is present."""
        result = create_mock_result(n_times=50)
        result.manifest = {'artifact_id': 'test-artifact-123'}
        
        ax = plot_time_grid_diagnostics(result)
        
        # Check for artifact link in the plot
        fig = ax.get_figure()
        all_texts = []
        
        # Collect all text elements from figure
        for child in fig.get_children():
            if hasattr(child, 'get_text'):
                all_texts.append(child.get_text())
            # Also check children of axes
            if hasattr(child, 'get_children'):
                for grandchild in child.get_children():
                    if hasattr(grandchild, 'get_text'):
                        all_texts.append(grandchild.get_text())
        
        artifact_found = any('Artifact: test-artifact-123' in text for text in all_texts)
        disclaimer_found = any('DIAGNOSTIC VIEW' in text for text in all_texts)
        
        assert artifact_found, "Artifact link not found in plot"
        assert disclaimer_found, "Disclaimer not found in plot"
        
        plt.close()
    
    def test_no_artifact_when_manifest_empty(self):
        """Test no artifact link when manifest is empty."""
        result = create_mock_result()
        result.manifest = {}  # Empty manifest
        
        ax = plot_time_grid_diagnostics(result)
        
        # Should only show disclaimer, not artifact link
        fig = ax.get_figure()
        all_texts = []
        
        for child in fig.get_children():
            if hasattr(child, 'get_text'):
                all_texts.append(child.get_text())
            if hasattr(child, 'get_children'):
                for grandchild in child.get_children():
                    if hasattr(grandchild, 'get_text'):
                        all_texts.append(grandchild.get_text())
        
        artifact_found = any('Artifact:' in text for text in all_texts)
        
        assert not artifact_found, "Artifact link should not appear with empty manifest"
        
        plt.close()


class TestLindbladValidation:
    """Tests for plot_lindblad_validation."""
    
    def create_mock_metrics(self, trace_ok=True, pos_ok=True):
        """Create mock sanity check metrics."""
        return {
            "schema_version": "open-system-sanity-checks/v1",
            "ok": trace_ok and pos_ok,
            "atom_count": 2,
            "basis_size": 4,
            "t_start": 0.0,
            "t_end": 1.0,
            "n_trajectories": 100,
            "trace_atol": 1e-6,
            "positivity_atol": 1e-7,
            "lindblad_trace": {
                "ok": trace_ok,
                "max_error": 5e-7 if trace_ok else 2e-6,
            },
            "lindblad_positivity": {
                "ok": pos_ok,
                "min_eigenvalue": -5e-8 if pos_ok else -2e-7,
            },
            "mcwf_vs_lindblad": {
                "ok": True,
                "max_mean_abs_error": 0.05,
                "max_abs_error": 0.12,
                "observables": {},
            },
        }
    
    def test_complete_metrics(self):
        """Test with complete validation metrics."""
        result = create_mock_result()
        metrics = self.create_mock_metrics()
        
        ax = plot_lindblad_validation(result, metrics)
        
        assert ax is not None
        plt.close()
    
    def test_missing_trace_metrics(self):
        """Test error when lindblad_trace is missing."""
        result = create_mock_result()
        metrics = {"lindblad_positivity": {"ok": True, "min_eigenvalue": -1e-8}}
        
        with pytest.raises(ValueError, match="Missing 'lindblad_trace'"):
            plot_lindblad_validation(result, metrics)
    
    def test_missing_positivity_metrics(self):
        """Test error when lindblad_positivity is missing."""
        result = create_mock_result()
        metrics = {"lindblad_trace": {"ok": True, "max_error": 1e-7}}
        
        with pytest.raises(ValueError, match="Missing 'lindblad_positivity'"):
            plot_lindblad_validation(result, metrics)
    
    def test_pass_fail_indicators(self):
        """Test Pass/Fail status display."""
        result = create_mock_result()
        
        # Test PASS case
        metrics_pass = self.create_mock_metrics(trace_ok=True, pos_ok=True)
        ax = plot_lindblad_validation(result, metrics_pass)
        # Would check for green "PASS" text
        
        plt.close()
        
        # Test FAIL case
        metrics_fail = self.create_mock_metrics(trace_ok=False, pos_ok=False)
        ax = plot_lindblad_validation(result, metrics_fail)
        # Would check for red "FAIL" text
        
        plt.close()
    
    def test_single_panel_mode(self):
        """Test with only trace or positivity enabled."""
        result = create_mock_result()
        metrics = self.create_mock_metrics()
        
        ax = plot_lindblad_validation(result, metrics, 
                                     show_trace_error=True, 
                                     show_positivity=False)
        
        assert ax is not None
        plt.close()
    
    def test_artifact_link_in_title(self):
        """Test artifact link appears in figure title."""
        result = create_mock_result()
        result.manifest = {'artifact_id': 'lindblad-check-n2-gamma0.1'}
        metrics = self.create_mock_metrics()
        
        ax = plot_lindblad_validation(result, metrics)
        fig = ax[0].get_figure() if isinstance(ax, (list, np.ndarray)) else ax.get_figure()
        
        # Check suptitle contains artifact ID
        suptitle = fig._suptitle.get_text() if fig._suptitle else ""
        
        assert 'Artifact: lindblad-check-n2-gamma0.1' in suptitle
        assert 'DIAGNOSTIC VIEW' in suptitle
        
        plt.close()


class TestMCWFvsLindblad:
    """Tests for plot_mcwf_vs_lindblad."""
    
    def create_mock_results(self, n_times=50):
        """Create paired Lindblad and MCWF results."""
        t_lind = np.linspace(0, 1.0, n_times)
        t_mcwf = np.linspace(0, 1.0, n_times)
        
        # Simulate slightly different trajectories
        lindblad_data = {
            't': t_lind,
            'pop0': 0.5 + 0.3 * np.sin(2 * np.pi * t_lind),
            'pop1': 0.4 + 0.2 * np.cos(2 * np.pi * t_lind),
        }
        
        mcwf_data = {
            't': t_mcwf,
            'pop0': lindblad_data['pop0'] + np.random.normal(0, 0.02, n_times),
            'pop1': lindblad_data['pop1'] + np.random.normal(0, 0.02, n_times),
        }
        
        lindblad_result = MockResult(lindblad_data)
        mcwf_result = MockResult(mcwf_data)
        
        return lindblad_result, mcwf_result
    
    def test_multiple_observables(self):
        """Test with multiple observables."""
        lindblad_res, mcwf_res = self.create_mock_results()
        
        axes = plot_mcwf_vs_lindblad(lindblad_res, mcwf_res, 
                                    observables=['pop0', 'pop1'])
        
        assert axes is not None
        plt.close()
    
    def test_no_common_observables(self):
        """Test error when no common observables."""
        lindblad_data = {'t': [0, 1], 'pop0': [0.5, 0.6]}
        mcwf_data = {'t': [0, 1], 'pop2': [0.5, 0.6]}
        
        lindblad_res = MockResult(lindblad_data)
        mcwf_res = MockResult(mcwf_data)
        
        with pytest.raises(ValueError, match="No common observables"):
            plot_mcwf_vs_lindblad(lindblad_res, mcwf_res)
    
    def test_auto_detect_observables(self):
        """Test automatic observable detection."""
        lindblad_res, mcwf_res = self.create_mock_results()
        
        axes = plot_mcwf_vs_lindblad(lindblad_res, mcwf_res, observables=None)
        
        assert axes is not None
        plt.close()
    
    def test_error_statistics_display(self):
        """Test mean/max error annotation."""
        lindblad_res, mcwf_res = self.create_mock_results()
        
        axes = plot_mcwf_vs_lindblad(lindblad_res, mcwf_res, 
                                    observables=['pop0'])
        
        # Would verify error stats text box exists
        plt.close()
    
    def test_artifact_links_for_both_results(self):
        """Test artifact links for both Lindblad and MCWF results."""
        lindblad_res, mcwf_res = self.create_mock_results()
        lindblad_res.manifest = {'artifact_id': 'lindblad-run-n2'}
        mcwf_res.manifest = {'artifact_id': 'mcwf-run-n2-traj100'}
        
        axes = plot_mcwf_vs_lindblad(lindblad_res, mcwf_res, 
                                    observables=['pop0'])
        
        fig = axes[0, 0].get_figure() if isinstance(axes, np.ndarray) else axes.get_figure()
        suptitle = fig._suptitle.get_text() if fig._suptitle else ""
        
        assert 'Lindblad: lindblad-run-n2' in suptitle
        assert 'MCWF: mcwf-run-n2-traj100' in suptitle
        assert 'DIAGNOSTIC VIEW' in suptitle
        
        plt.close()


class TestTrajectoryStatistics:
    """Tests for plot_trajectory_statistics."""
    
    def create_mock_mcwf_result(self, n_traj=50, n_times=30):
        """Create MCWF result with trajectory data."""
        t = np.linspace(0, 1.0, n_times)
        data = {'t': t}
        
        # Generate synthetic trajectories
        traj_pop0 = np.zeros((n_traj, n_times))
        for i in range(n_traj):
            noise = np.random.normal(0, 0.05, n_times)
            traj_pop0[i] = 0.5 + 0.3 * np.sin(2 * np.pi * t) + noise
        
        result = MockResult(data)
        result.trajectories = {'pop0': traj_pop0}
        
        return result
    
    def test_complete_trajectory_data(self):
        """Test with full trajectory statistics."""
        result = self.create_mock_mcwf_result(n_traj=50)
        
        axes = plot_trajectory_statistics(result, 'pop0', confidence_level=0.95)
        
        assert axes is not None
        plt.close()
    
    def test_missing_trajectories_attribute(self):
        """Test error when trajectories attribute missing."""
        result = create_mock_result()
        
        with pytest.raises(ValueError, match="No trajectory data found"):
            plot_trajectory_statistics(result, 'pop0')
    
    def test_missing_observable_in_trajectories(self):
        """Test error when observable not in trajectories."""
        result = self.create_mock_mcwf_result()
        
        with pytest.raises(ValueError, match="Observable 'pop1' not found"):
            plot_trajectory_statistics(result, 'pop1')
    
    def test_confidence_level_variation(self):
        """Test different confidence levels."""
        result = self.create_mock_mcwf_result()
        
        # 90% CI should be narrower than 99% CI
        ax_90 = plot_trajectory_statistics(result, 'pop0', confidence_level=0.90)
        ax_99 = plot_trajectory_statistics(result, 'pop0', confidence_level=0.99)
        
        # Would compare fill_between widths
        plt.close('all')
    
    def test_individual_trajectories_display(self):
        """Test showing individual trajectory lines."""
        result = self.create_mock_mcwf_result(n_traj=20)
        
        axes = plot_trajectory_statistics(result, 'pop0', 
                                         show_individual=True,
                                         n_sample_trajectories=5)
        
        assert axes is not None
        plt.close()
    
    def test_final_time_histogram(self):
        """Test final-time distribution histogram."""
        result = self.create_mock_mcwf_result()
        
        axes = plot_trajectory_statistics(result, 'pop0')
        
        # axes[1] should be histogram
        assert len(axes) == 2
        plt.close()
    
    def test_artifact_link_in_disclaimer(self):
        """Test artifact link appears in disclaimer text."""
        result = self.create_mock_mcwf_result(n_traj=50)
        result.manifest = {'artifact_id': 'mcwf-stats-n2-traj50'}
        
        axes = plot_trajectory_statistics(result, 'pop0')
        fig = axes[0].get_figure()
        
        # Check figure-level text for artifact link
        all_texts = []
        for child in fig.get_children():
            if hasattr(child, 'get_text'):
                all_texts.append(child.get_text())
        
        artifact_found = any('Artifact: mcwf-stats-n2-traj50' in text for text in all_texts)
        disclaimer_found = any('DIAGNOSTIC VIEW' in text for text in all_texts)
        
        assert artifact_found, "Artifact link not found in trajectory statistics"
        assert disclaimer_found, "Disclaimer not found in trajectory statistics"
        
        plt.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
