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
from sagittarius.viz.sweep import (
    plot_sweep_heatmap,
    plot_sweep_line_slice,
    plot_final_observable_map,
    plot_failed_run_mask,
    extract_sweep_summary,
    generate_synthetic_sweep_data,
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
