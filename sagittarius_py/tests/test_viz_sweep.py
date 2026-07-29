"""
Tests for sweep visualization module.

Tests cover:
- Heatmap plotting with failed run overlay
- Line slice extraction and plotting
- Final observable maps
- Failed run mask visualization
- Summary statistics extraction
- Synthetic data generation
- Artifact link preservation
- Disclaimer display
"""

import pytest
import numpy as np
import matplotlib.pyplot as plt
from sagittarius import SimulationResult, make_sweep_artifact, save_sweep_artifact
from sagittarius.viz.sweep import (
    plot_sweep_heatmap,
    plot_sweep_line_slice,
    plot_final_observable_map,
    plot_observables_comparison,
    plot_failed_run_mask,
    extract_sweep_summary,
    generate_synthetic_sweep_data,
    extract_sweep_artifact_data,
    plot_sweep_artifact_heatmap,
)


@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Automatically close all figures after each test to prevent memory warnings."""
    yield
    plt.close('all')


class TestSweepHeatmap:
    """Tests for plot_sweep_heatmap."""
    
    def create_test_data(self):
        """Create minimal test sweep data."""
        return {
            'parameters': {
                'omega': np.linspace(0.1, 5.0, 10),
                'delta': np.linspace(-2.0, 2.0, 8),
            },
            'results': {
                'pop0': np.random.rand(8, 10),
            },
            'failed_runs': {(2, 3), (5, 6)},
        }
    
    def test_basic_heatmap(self):
        """Test basic heatmap creation."""
        data = self.create_test_data()
        ax = plot_sweep_heatmap(data)
        
        assert ax is not None
        assert len(ax.collections) > 0  # pcolormesh present
        
        plt.close()
    
    def test_with_custom_metric(self):
        """Test with custom metric name."""
        data = self.create_test_data()
        data['results']['energy'] = np.random.rand(8, 10)
        
        ax = plot_sweep_heatmap(data, metric='energy')
        assert ax is not None
        
        plt.close()
    
    def test_with_title(self):
        """Test with custom title."""
        data = self.create_test_data()
        ax = plot_sweep_heatmap(data, title="Custom Title")
        
        assert "Custom Title" in ax.get_title()
        
        plt.close()
    
    def test_without_colorbar(self):
        """Test heatmap without colorbar."""
        data = self.create_test_data()
        fig, ax = plt.subplots()
        result_ax = plot_sweep_heatmap(data, ax=ax, show_colorbar=False)
        
        # Should only have main axes, no colorbar axes
        assert len(fig.axes) == 1
        
        plt.close()
    
    def test_with_existing_axes(self):
        """Test plotting on existing axes."""
        data = self.create_test_data()
        fig, ax = plt.subplots()
        result_ax = plot_sweep_heatmap(data, ax=ax)
        
        assert result_ax is ax
        
        plt.close()
    
    def test_failed_runs_overlay(self):
        """Test that failed runs are marked with X markers."""
        data = self.create_test_data()
        ax = plot_sweep_heatmap(data, show_failed_mask=True)
        
        # Check for scatter plot (X markers)
        assert len(ax.collections) >= 2  # pcolormesh + scatter
        
        plt.close()
    
    def test_disclaimer_present(self):
        """Test that disclaimer is shown."""
        data = self.create_test_data()
        ax = plot_sweep_heatmap(data)
        
        fig = ax.get_figure()
        texts = [child for child in fig.get_children() 
                if hasattr(child, 'get_text')]
        disclaimer_found = any("EXPLORATORY VISUALIZATION" in str(t.get_text()) 
                              for t in texts if hasattr(t, 'get_text'))
        assert disclaimer_found
        
        plt.close()
    
    def test_artifact_link_display(self):
        """Test artifact link is displayed when manifest_links present."""
        data = self.create_test_data()
        data['manifest_links'] = {'run_001': 'artifact_001'}
        
        ax = plot_sweep_heatmap(data)
        
        fig = ax.get_figure()
        all_texts = []
        for child in fig.get_children():
            if hasattr(child, 'get_text'):
                all_texts.append(child.get_text())
        
        artifact_found = any('Artifact' in text for text in all_texts)
        assert artifact_found
        
        plt.close()
    
    def test_missing_parameters_raises(self):
        """Test error when parameters key is missing."""
        data = {'results': {'pop0': np.random.rand(8, 10)}}
        
        with pytest.raises(ValueError, match="Missing 'parameters'"):
            plot_sweep_heatmap(data)
    
    def test_missing_results_raises(self):
        """Test error when results key is missing."""
        data = {'parameters': {'omega': [1, 2], 'delta': [1, 2]}}
        
        with pytest.raises(ValueError, match="Missing 'results'"):
            plot_sweep_heatmap(data)
    
    def test_shape_mismatch_raises(self):
        """Test error when result shape doesn't match parameters."""
        data = {
            'parameters': {
                'omega': np.linspace(0.1, 5.0, 10),
                'delta': np.linspace(-2.0, 2.0, 8),
            },
            'results': {
                'pop0': np.random.rand(5, 5),  # Wrong shape
            },
        }
        
        with pytest.raises(ValueError, match="has shape"):
            plot_sweep_heatmap(data)


class TestSweepLineSlice:
    """Tests for plot_sweep_line_slice."""
    
    def create_test_data(self):
        """Create minimal test sweep data."""
        return {
            'parameters': {
                'omega': np.linspace(0.1, 5.0, 10),
                'delta': np.linspace(-2.0, 2.0, 8),
            },
            'results': {
                'pop0': np.random.rand(8, 10),
            },
        }
    
    def test_basic_line_slice(self):
        """Test basic line slice creation."""
        data = self.create_test_data()
        ax = plot_sweep_line_slice(data, fixed_param='delta', fixed_value=0.0,
                                   varying_param='omega')
        
        assert ax is not None
        assert len(ax.lines) > 0  # Line plot present
        
        plt.close()
    
    def test_with_error_bars(self):
        """Test line slice with error bars."""
        data = self.create_test_data()
        data['results']['pop0_std'] = np.random.rand(8, 10) * 0.05
        
        ax = plot_sweep_line_slice(data, fixed_param='delta', fixed_value=0.0,
                                   varying_param='omega', show_error_bars=True)
        
        assert ax is not None
        
        plt.close()
    
    def test_with_custom_title(self):
        """Test with custom title."""
        data = self.create_test_data()
        ax = plot_sweep_line_slice(data, fixed_param='delta', fixed_value=0.0,
                                   varying_param='omega', title="Custom")
        
        assert "Custom" in ax.get_title()
        
        plt.close()
    
    def test_disclaimer_present(self):
        """Test that disclaimer is shown."""
        data = self.create_test_data()
        ax = plot_sweep_line_slice(data, fixed_param='delta', fixed_value=0.0,
                                   varying_param='omega')
        
        fig = ax.get_figure()
        texts = [child for child in fig.get_children() 
                if hasattr(child, 'get_text')]
        disclaimer_found = any("EXPLORATORY VISUALIZATION" in str(t.get_text()) 
                              for t in texts if hasattr(t, 'get_text'))
        assert disclaimer_found
        
        plt.close()
    
    def test_missing_parameter_raises(self):
        """Test error when parameter is missing."""
        data = self.create_test_data()
        
        with pytest.raises(ValueError, match="not found"):
            plot_sweep_line_slice(data, fixed_param='gamma', fixed_value=0.0,
                                 varying_param='omega')


class TestFinalObservableMap:
    """Tests for plot_final_observable_map."""
    
    def create_test_data(self):
        """Create minimal test sweep data."""
        return {
            'parameters': {
                'omega': np.linspace(0.1, 5.0, 10),
            },
            'results': {
                'pop0': np.random.rand(10),
            },
        }
    
    def test_basic_map(self):
        """Test basic final observable map."""
        data = self.create_test_data()
        ax = plot_final_observable_map(data, observable_name='pop0')
        
        assert ax is not None
        assert len(ax.lines) > 0
        
        plt.close()
    
    def test_with_2d_data(self):
        """Test with 2D data (takes last time point)."""
        data = {
            'parameters': {
                'omega': np.linspace(0.1, 5.0, 10),
            },
            'results': {
                'pop0': np.random.rand(10, 50),  # 10 params x 50 time points
            },
        }
        
        ax = plot_final_observable_map(data, observable_name='pop0')
        assert ax is not None
        
        plt.close()
    
    def test_disclaimer_present(self):
        """Test that disclaimer is shown."""
        data = self.create_test_data()
        ax = plot_final_observable_map(data, observable_name='pop0')
        
        fig = ax.get_figure()
        texts = [child for child in fig.get_children() 
                if hasattr(child, 'get_text')]
        disclaimer_found = any("EXPLORATORY VISUALIZATION" in str(t.get_text()) 
                              for t in texts if hasattr(t, 'get_text'))
        assert disclaimer_found
        
        plt.close()


class TestFailedRunMask:
    """Tests for plot_failed_run_mask."""
    
    def create_test_data(self):
        """Create minimal test sweep data."""
        return {
            'parameters': {
                'omega': np.linspace(0.1, 5.0, 10),
                'delta': np.linspace(-2.0, 2.0, 8),
            },
            'failed_runs': {(2, 3), (5, 6), (7, 1)},
        }
    
    def test_basic_mask(self):
        """Test basic failed run mask."""
        data = self.create_test_data()
        ax = plot_failed_run_mask(data)
        
        assert ax is not None
        assert len(ax.collections) > 0  # pcolormesh present
        
        plt.close()
    
    def test_with_boolean_array(self):
        """Test with boolean array for failed runs."""
        data = {
            'parameters': {
                'omega': np.linspace(0.1, 5.0, 10),
                'delta': np.linspace(-2.0, 2.0, 8),
            },
            'failed_runs': np.random.rand(8, 10) > 0.9,  # Boolean mask
        }
        
        ax = plot_failed_run_mask(data)
        assert ax is not None
        
        plt.close()
    
    def test_success_rate_in_title(self):
        """Test that success rate is shown in title."""
        data = self.create_test_data()
        ax = plot_failed_run_mask(data)
        
        title = ax.get_title()
        assert 'success' in title.lower() or '%' in title
        
        plt.close()
    
    def test_disclaimer_present(self):
        """Test that disclaimer is shown."""
        data = self.create_test_data()
        ax = plot_failed_run_mask(data)
        
        fig = ax.get_figure()
        texts = [child for child in fig.get_children() 
                if hasattr(child, 'get_text')]
        disclaimer_found = any("EXPLORATORY VISUALIZATION" in str(t.get_text()) 
                              for t in texts if hasattr(t, 'get_text'))
        assert disclaimer_found
        
        plt.close()
    
    def test_missing_failed_runs_raises(self):
        """Test error when failed_runs is missing."""
        data = {
            'parameters': {
                'omega': [1, 2],
                'delta': [1, 2],
            },
        }
        
        with pytest.raises(ValueError, match="Missing 'failed_runs'"):
            plot_failed_run_mask(data)


class TestSweepSummary:
    """Tests for extract_sweep_summary."""
    
    def create_test_data(self):
        """Create minimal test sweep data."""
        return {
            'parameters': {
                'omega': np.linspace(0.1, 5.0, 10),
                'delta': np.linspace(-2.0, 2.0, 8),
            },
            'results': {
                'pop0': np.random.rand(8, 10),
                'energy': np.random.rand(8, 10),
            },
            'failed_runs': {(2, 3), (5, 6)},
        }
    
    def test_basic_summary(self):
        """Test basic summary extraction."""
        data = self.create_test_data()
        summary = extract_sweep_summary(data)
        
        assert 'pop0' in summary
        assert 'min' in summary['pop0']
        assert 'max' in summary['pop0']
        assert 'mean' in summary['pop0']
        assert 'std' in summary['pop0']
    
    def test_specific_metrics(self):
        """Test summary for specific metrics."""
        data = self.create_test_data()
        summary = extract_sweep_summary(data, metrics=['energy'])
        
        assert 'energy' in summary
        assert 'pop0' not in summary
    
    def test_run_statistics(self):
        """Test that run statistics are included."""
        data = self.create_test_data()
        summary = extract_sweep_summary(data)
        
        assert 'run_statistics' in summary
        assert 'total_runs' in summary['run_statistics']
        assert 'failed_runs' in summary['run_statistics']
        assert 'success_rate' in summary['run_statistics']


class TestSyntheticDataGeneration:
    """Tests for generate_synthetic_sweep_data."""
    
    def test_basic_generation(self):
        """Test basic synthetic data generation."""
        data = generate_synthetic_sweep_data()
        
        assert 'parameters' in data
        assert 'results' in data
        assert 'failed_runs' in data
        assert 'manifest_links' in data
    
    def test_parameter_ranges(self):
        """Test that parameters are within specified ranges."""
        data = generate_synthetic_sweep_data(
            omega_range=(1.0, 3.0),
            delta_range=(-1.0, 1.0),
        )
        
        omega_vals = data['parameters']['omega']
        delta_vals = data['parameters']['delta']
        
        assert np.min(omega_vals) >= 1.0
        assert np.max(omega_vals) <= 3.0
        assert np.min(delta_vals) >= -1.0
        assert np.max(delta_vals) <= 1.0
    
    def test_grid_dimensions(self):
        """Test that grid dimensions match specifications."""
        data = generate_synthetic_sweep_data(n_omega=15, n_delta=10)
        
        assert len(data['parameters']['omega']) == 15
        assert len(data['parameters']['delta']) == 10
        
        # Check 2D result arrays
        for key, arr in data['results'].items():
            assert arr.shape == (10, 15)
    
    def test_reproducibility(self):
        """Test that same seed produces same data."""
        data1 = generate_synthetic_sweep_data(seed=42)
        data2 = generate_synthetic_sweep_data(seed=42)
        
        assert np.array_equal(data1['results']['pop0'], data2['results']['pop0'])
    
    def test_failure_rate(self):
        """Test that failure rate is approximately correct."""
        data = generate_synthetic_sweep_data(
            n_omega=20, n_delta=15, failure_rate=0.1
        )
        
        total_runs = 20 * 15
        n_failed = len(data['failed_runs'])
        actual_rate = n_failed / total_runs
        
        # Allow 50% tolerance due to randomness
        assert 0.05 <= actual_rate <= 0.15
    
    def test_metadata_present(self):
        """Test that metadata is included."""
        data = generate_synthetic_sweep_data()
        
        assert 'metadata' in data
        assert 'schema_version' in data['metadata']
        assert 'seed' in data['metadata']


# Integration test
class TestSweepIntegration:
    """Integration tests for complete sweep workflow."""
    
    def test_full_workflow(self):
        """Test complete sweep visualization workflow."""
        # Generate synthetic data
        sweep_data = generate_synthetic_sweep_data(
            n_omega=15, n_delta=10, seed=42
        )
        
        # Create heatmap
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        plot_sweep_heatmap(sweep_data, ax=ax1)
        
        # Create line slice
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        plot_sweep_line_slice(
            sweep_data,
            fixed_param='delta',
            fixed_value=0.0,
            varying_param='omega',
            ax=ax2
        )
        
        # Create final observable map
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        plot_final_observable_map(
            sweep_data,
            observable_name='pop0',
            ax=ax3
        )
        
        # Create failed run mask
        fig4, ax4 = plt.subplots(figsize=(10, 8))
        plot_failed_run_mask(sweep_data, ax=ax4)
        
        # Extract summary
        summary = extract_sweep_summary(sweep_data)
        
        # Verify all plots were created
        assert ax1 is not None
        assert ax2 is not None
        assert ax3 is not None
        assert ax4 is not None
        assert 'pop0' in summary
        
        plt.close('all')


class TestObservablesComparison:
    """Test plot_observables_comparison function."""
    
    def create_test_data(self):
        """Create test sweep data with multiple observables."""
        omega = np.linspace(0.5, 5.0, 20)
        
        # Create multiple observables
        pop0 = np.sin(omega)**2 * np.exp(-0.1 * omega)
        pop1 = np.cos(omega)**2 * np.exp(-0.1 * omega)
        energy = omega**2 / (1 + omega)
        
        return {
            'parameters': {
                'omega': omega,
            },
            'results': {
                'pop0': pop0,
                'pop1': pop1,
                'energy': energy,
            },
        }
    
    def test_basic_comparison(self):
        """Test basic multi-observable comparison."""
        data = self.create_test_data()
        
        fig, ax = plt.subplots(figsize=(12, 7))
        result_ax = plot_observables_comparison(data, ax=ax)
        
        assert result_ax is not None
        assert len(ax.get_lines()) == 3  # Three observables plotted
        
        # Check legend has all three observables
        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        assert 'pop0' in legend_texts
        assert 'pop1' in legend_texts
        assert 'energy' in legend_texts
        
        plt.close(fig)
    
    def test_with_custom_colors(self):
        """Test comparison with custom colors."""
        data = self.create_test_data()
        colors = ['red', 'green', 'blue']
        
        fig, ax = plt.subplots(figsize=(12, 7))
        plot_observables_comparison(data, ax=ax, colors=colors)
        
        lines = ax.get_lines()
        assert len(lines) == 3
        
        # Check colors are applied
        for line, expected_color in zip(lines, colors):
            assert line.get_color() == expected_color
        
        plt.close(fig)
    
    def test_with_normalization(self):
        """Test comparison with normalization."""
        data = self.create_test_data()
        
        fig, ax = plt.subplots(figsize=(12, 7))
        plot_observables_comparison(data, ax=ax, normalize=True)
        
        # Check y-axis label mentions normalization
        ylabel = ax.get_ylabel()
        assert 'Normalized' in ylabel
        
        # Check all values are in [0, 1] range
        for line in ax.get_lines():
            y_data = line.get_ydata()
            assert np.min(y_data) >= 0.0
            assert np.max(y_data) <= 1.0
        
        plt.close(fig)
    
    def test_specific_observables(self):
        """Test plotting only specific observables."""
        data = self.create_test_data()
        
        fig, ax = plt.subplots(figsize=(12, 7))
        plot_observables_comparison(data, observables=['pop0', 'energy'], ax=ax)
        
        assert len(ax.get_lines()) == 2
        
        legend_texts = [t.get_text() for t in ax.get_legend().get_texts()]
        assert 'pop0' in legend_texts
        assert 'energy' in legend_texts
        assert 'pop1' not in legend_texts
        
        plt.close(fig)
    
    def test_disclaimer_present(self):
        """Test that disclaimer is present in the figure."""
        data = self.create_test_data()
        
        fig, ax = plt.subplots(figsize=(12, 7))
        plot_observables_comparison(data, ax=ax)
        
        # Check for disclaimer text
        texts = [child for child in fig.get_children() if isinstance(child, plt.Text)]
        disclaimer_found = False
        for text in texts:
            if 'EXPLORATORY VISUALIZATION' in text.get_text():
                disclaimer_found = True
                break
        
        assert disclaimer_found, "Disclaimer not found in figure"
        plt.close(fig)
    
    def test_missing_observable_warning(self):
        """Test warning when observable is missing."""
        data = self.create_test_data()
        
        fig, ax = plt.subplots(figsize=(12, 7))
        # Should print warning but not raise error
        plot_observables_comparison(data, observables=['pop0', 'nonexistent'], ax=ax)
        
        # Only pop0 should be plotted
        assert len(ax.get_lines()) == 1
        plt.close(fig)

def _saved_two_axis_sweep(tmp_path):
    sweep_dir = tmp_path / "sweep"
    runs_dir = sweep_dir / "runs"
    runs_dir.mkdir(parents=True)
    values = {
        ("omega-1", "delta-negative"): 0.2,
        ("omega-2", "delta-negative"): 0.4,
        ("omega-1", "delta-positive"): 0.6,
    }
    items = []
    for omega, omega_id in ((1.0, "omega-1"), (2.0, "omega-2")):
        for delta, delta_id in ((-1.0, "delta-negative"), (1.0, "delta-positive")):
            item_id = f"{omega_id}-{delta_id}"
            if (omega_id, delta_id) not in values:
                items.append({
                    "item_id": item_id,
                    "parameters": {"omega": omega, "delta": delta},
                    "status": "failed",
                    "attempts": 1,
                    "result_path": None,
                    "manifest_path": None,
                    "failure": {
                        "code": "SOLVER_EXECUTION_FAILED",
                        "message": "synthetic sweep failure",
                        "remediation": "retry this item",
                    },
                })
                continue
            result_path = runs_dir / f"{item_id}.result.json"
            SimulationResult(
                {"t": [0.0, 1.0], "population": [0.0, values[(omega_id, delta_id)]]}
            ).save(result_path)
            items.append({
                "item_id": item_id,
                "parameters": {"omega": omega, "delta": delta},
                "status": "succeeded",
                "attempts": 1,
                "result_path": f"runs/{result_path.name}",
                "manifest_path": f"runs/{item_id}.manifest.json",
                "failure": None,
            })

    artifact = make_sweep_artifact(
        axes=[
            {"name": "omega", "path": "pulse.omega", "values": [1.0, 2.0]},
            {"name": "delta", "path": "pulse.delta", "values": [-1.0, 1.0]},
        ],
        items=items,
        base_config={"schema_version": "experiment-config/v1"},
    )
    artifact_path = sweep_dir / "scan.sweep.json"
    save_sweep_artifact(artifact, artifact_path)
    return artifact_path, runs_dir


def test_extract_sweep_artifact_data_resolves_results_failures_and_links(tmp_path):
    artifact_path, runs_dir = _saved_two_axis_sweep(tmp_path)

    data = extract_sweep_artifact_data(artifact_path, "population")

    np.testing.assert_allclose(
        data["results"]["population"],
        [[0.2, 0.4], [0.6, np.nan]],
        equal_nan=True,
    )
    assert data["failed_runs"].tolist() == [[False, False], [False, True]]
    assert data["item_statuses"]["omega-2-delta-positive"] == "failed"
    assert data["failure_records"]["omega-2-delta-positive"]["code"] == "SOLVER_EXECUTION_FAILED"
    assert data["result_paths"]["omega-1-delta-negative"] == str(
        runs_dir / "omega-1-delta-negative.result.json"
    )
    assert data["manifest_links"]["omega-1-delta-negative"] == str(
        runs_dir / "omega-1-delta-negative.manifest.json"
    )
    assert data["resumability"]["pending_item_ids"] == ["omega-2-delta-positive"]


def test_plot_sweep_artifact_heatmap_draws_artifact_failures(tmp_path):
    artifact_path, _ = _saved_two_axis_sweep(tmp_path)

    ax = plot_sweep_artifact_heatmap(
        artifact_path, "population", show_colorbar=False
    )

    assert ax.get_xlabel() == "omega"
    assert ax.get_ylabel() == "delta"
    assert len(ax.collections) >= 2


def test_sweep_artifact_visualization_does_not_initialize_julia(monkeypatch, tmp_path):
    artifact_path, _ = _saved_two_axis_sweep(tmp_path)

    import sagittarius.api as api

    def unexpected_backend_initialization(*args, **kwargs):
        raise AssertionError("Visualization unexpectedly initialized Julia")

    monkeypatch.setattr(api, "get_modules", unexpected_backend_initialization)
    data = extract_sweep_artifact_data(artifact_path, "population")
    ax = plot_sweep_artifact_heatmap(
        artifact_path, "population", show_colorbar=False
    )

    assert data["source_schema_version"] == "sweep-artifact/v1"
    assert ax is not None

def test_sweep_artifact_visualization_rejects_benchmark_artifacts():
    from sagittarius import make_benchmark_artifact
    from sagittarius.runtime import SagittariusValidationError

    benchmark = make_benchmark_artifact(
        name="not a sweep",
        description="boundary regression",
        parameters={"omega": [1.0]},
        rows=[{"omega": 1.0, "time_s": 0.01}],
        diagnostics={"requested_backend": "CPU"},
        run_manifests=[],
    )

    with pytest.raises(SagittariusValidationError) as excinfo:
        extract_sweep_artifact_data(benchmark, "population")

    assert excinfo.value.issue.code == "VALIDATION_SWEEP_ARTIFACT_SCHEMA"
