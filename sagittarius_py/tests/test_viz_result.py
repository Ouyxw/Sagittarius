"""
Result visualization tests.

Tests for plot_observables(), plot_bitstring_distribution(), 
plot_shot_histogram(), and plot_population_heatmap() functions.
All tests save generated images to test_figs/ directory.
"""

import os
import pytest
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sagittarius.viz import (
    plot_observables,
    plot_bitstring_distribution,
    plot_shot_histogram,
    plot_population_heatmap
)


# Mock classes for testing
class MockResult:
    """Mock SimulationResult object."""
    def __init__(self, df, bitstrings=None, samples=None):
        self._df = df
        self._bitstrings = bitstrings or {}
        self._samples = samples
    
    def to_pandas(self):
        return self._df
    
    def final_bitstring_distribution(self):
        return self._bitstrings
    
    @property
    def samples(self):
        return self._samples


# Test fixtures
@pytest.fixture
def output_dir():
    """Create output directory for test figures."""
    output_path = os.path.join(os.path.dirname(__file__), 'test_figs')
    os.makedirs(output_path, exist_ok=True)
    return output_path


@pytest.fixture
def mock_observables_result():
    """Create mock result with observables data."""
    times = np.linspace(0, 10, 50)
    data = {
        'time': times,
        'n_up': np.sin(times),
        'energy': np.cos(times),
        'magnetization': np.sin(times) * np.cos(times)
    }
    df = pd.DataFrame(data)
    return MockResult(df)


@pytest.fixture
def mock_bitstrings_result():
    """Create mock result with bitstring distribution."""
    df = pd.DataFrame({'time': [0]})
    bitstrings = {
        '0101': 0.3,
        '1010': 0.25,
        '1100': 0.2,
        '0011': 0.15,
        '0000': 0.1
    }
    return MockResult(df, bitstrings=bitstrings)


@pytest.fixture
def mock_samples_result():
    """Create mock result with samples."""
    df = pd.DataFrame({'time': [0]})
    # Create sample data
    samples = ['0101'] * 30 + ['1010'] * 25 + ['1100'] * 20 + ['0011'] * 15 + ['0000'] * 10
    return MockResult(df, samples=np.array(samples))


@pytest.fixture
def mock_population_result():
    """Create mock result with population data."""
    times = np.linspace(0, 5, 20)
    n_atoms = 4
    
    # Create population data for each atom over time
    data = {'time': times}
    for i in range(n_atoms):
        data[f'pop{i}'] = np.random.rand(len(times))
    
    df = pd.DataFrame(data)
    return MockResult(df)


# Tests for plot_observables
def test_plot_observables_basic(output_dir, mock_observables_result):
    """Test basic observables plotting."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_observables(mock_observables_result, ax=ax, title="Observables Trajectory")
    
    save_path = os.path.join(output_dir, "observables_basic.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_observables_specific_columns(output_dir, mock_observables_result):
    """Test plotting specific observable columns."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_observables(
        mock_observables_result, 
        names=['n_up', 'energy'],
        ax=ax, 
        title="Selected Observables"
    )
    
    save_path = os.path.join(output_dir, "observables_selected.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_observables_missing_column_raises(mock_observables_result):
    """Test that missing column raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        plot_observables(mock_observables_result, names=['invalid_column'])


def test_plot_observables_empty_df_raises():
    """Test that empty DataFrame raises ValueError."""
    empty_df = pd.DataFrame()
    empty_result = MockResult(empty_df)
    
    with pytest.raises(ValueError):
        plot_observables(empty_result)


# Tests for plot_bitstring_distribution
def test_plot_bitstring_distribution_basic(output_dir, mock_bitstrings_result):
    """Test basic bitstring distribution plotting."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_bitstring_distribution(mock_bitstrings_result, ax=ax, title="Bitstring Distribution")
    
    save_path = os.path.join(output_dir, "bitstring_basic.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_bitstring_distribution_sorted(output_dir, mock_bitstrings_result):
    """Test bitstring distribution sorted by probability."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_bitstring_distribution(
        mock_bitstrings_result, 
        top_k=3,
        sort_by='probability',
        ax=ax, 
        title="Sorted Bitstring Distribution"
    )
    
    save_path = os.path.join(output_dir, "bitstring_sorted.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_bitstring_distribution_show_values(output_dir, mock_bitstrings_result):
    """Test bitstring distribution with value labels."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_bitstring_distribution(
        mock_bitstrings_result, 
        show_values=True,
        ax=ax, 
        title="Bitstring Distribution with Values"
    )
    
    save_path = os.path.join(output_dir, "bitstring_with_values.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_bitstring_distribution_empty_raises():
    """Test that empty bitstring dict raises ValueError."""
    empty_result = MockResult(pd.DataFrame(), bitstrings={})
    
    with pytest.raises(ValueError):
        plot_bitstring_distribution(empty_result)


def test_plot_bitstring_distribution_with_basis_info(output_dir, mock_bitstrings_result):
    """Test bitstring distribution with basis mode and forbidden state info."""
    # Add metadata to mock result
    mock_bitstrings_result.metadata = {
        'readout': {
            'basis_mode': 'reduced',
            'forbidden_bitstring_count': 12
        }
    }
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_bitstring_distribution(
        mock_bitstrings_result, 
        ax=ax, 
        show_basis_info=True,
        title="With Basis Info"
    )
    
    # Verify title contains basis information
    title = ax.get_title()
    assert "Reduced" in title or "Basis" in title
    
    save_path = os.path.join(output_dir, "bitstring_with_basis_info.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_bitstring_distribution_hide_basis_info(output_dir, mock_bitstrings_result):
    """Test bitstring distribution with basis info hidden."""
    # Add metadata to mock result
    mock_bitstrings_result.metadata = {
        'readout': {
            'basis_mode': 'reduced',
            'forbidden_bitstring_count': 12
        }
    }
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_bitstring_distribution(
        mock_bitstrings_result, 
        ax=ax, 
        show_basis_info=False,
        title="Custom Title No Info"
    )
    
    # Verify title does not contain auto-generated basis information
    title = ax.get_title()
    # Should use custom title, not auto-generated one with basis info
    assert title == "Custom Title No Info"
    
    save_path = os.path.join(output_dir, "bitstring_no_basis_info.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# Tests for plot_shot_histogram
def test_plot_shot_histogram_basic(output_dir, mock_samples_result):
    """Test basic shot histogram plotting."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_shot_histogram(mock_samples_result, ax=ax, title="Shot Histogram")
    
    save_path = os.path.join(output_dir, "shot_histogram_basic.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_shot_histogram_normalized(output_dir, mock_samples_result):
    """Test normalized shot histogram."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_shot_histogram(
        mock_samples_result, 
        normalize=True,
        ax=ax, 
        title="Normalized Shot Histogram"
    )
    
    save_path = os.path.join(output_dir, "shot_histogram_normalized.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_shot_histogram_top_k(output_dir, mock_samples_result):
    """Test shot histogram with limited top-k."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_shot_histogram(
        mock_samples_result, 
        top_k=3,
        ax=ax, 
        title="Top-3 Shot Histogram"
    )
    
    save_path = os.path.join(output_dir, "shot_histogram_topk.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_shot_histogram_no_samples_raises():
    """Test that no samples raises AttributeError."""
    result_no_samples = MockResult(pd.DataFrame(), samples=None)
    
    with pytest.raises(AttributeError):
        plot_shot_histogram(result_no_samples)


def test_plot_shot_histogram_empty_samples_raises():
    """Test that empty samples raises ValueError."""
    result_empty_samples = MockResult(pd.DataFrame(), samples=np.array([]))
    
    with pytest.raises(ValueError):
        plot_shot_histogram(result_empty_samples)


def test_plot_shot_histogram_with_seed_info(output_dir, mock_samples_result):
    """Test shot histogram with random seed metadata display."""
    # Add manifest with seed information (measurement-samples/v1 format)
    mock_samples_result.manifest = {
        'readout': {
            'seed': 42,
            'effective_seed': 42
        }
    }
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_shot_histogram(
        mock_samples_result, 
        ax=ax, 
        show_seed_info=True,
        title="With Seed Info"
    )
    
    # Verify title contains seed information
    title = ax.get_title()
    assert "42" in title or "seed" in title.lower()
    
    save_path = os.path.join(output_dir, "shot_histogram_with_seed.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_shot_histogram_hide_seed_info(output_dir, mock_samples_result):
    """Test shot histogram with seed info hidden."""
    # Add manifest with seed information
    mock_samples_result.manifest = {
        'readout': {
            'seed': 999
        }
    }
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_shot_histogram(
        mock_samples_result, 
        ax=ax, 
        show_seed_info=False,
        title="Custom Title No Seed"
    )
    
    # Verify title uses custom title, not auto-generated one with seed info
    title = ax.get_title()
    assert title == "Custom Title No Seed"
    
    save_path = os.path.join(output_dir, "shot_histogram_no_seed.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)

# Tests for plot_population_heatmap
def test_plot_population_heatmap_basic(output_dir, mock_population_result):
    """Test basic population heatmap plotting."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_population_heatmap(mock_population_result, ax=ax, title="Population Heatmap")
    
    save_path = os.path.join(output_dir, "population_heatmap_basic.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_population_heatmap_custom_cmap(output_dir, mock_population_result):
    """Test population heatmap with custom colormap."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_population_heatmap(
        mock_population_result, 
        cmap='plasma',
        ax=ax, 
        title="Custom Colormap"
    )
    
    save_path = os.path.join(output_dir, "population_heatmap_custom_cmap.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_population_heatmap_no_colorbar(output_dir, mock_population_result):
    """Test population heatmap without colorbar."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    plot_population_heatmap(
        mock_population_result, 
        show_colorbar=False,
        ax=ax, 
        title="No Colorbar"
    )
    
    save_path = os.path.join(output_dir, "population_heatmap_no_cbar.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_population_heatmap_no_pop_columns_raises():
    """Test that DataFrame without population columns raises ValueError."""
    df_no_pop = pd.DataFrame({'time': [1, 2, 3], 'other': [4, 5, 6]})
    result_no_pop = MockResult(df_no_pop)
    
    with pytest.raises(ValueError, match="population"):
        plot_population_heatmap(result_no_pop)


def test_plot_population_heatmap_empty_raises():
    """Test that empty DataFrame raises ValueError."""
    empty_df = pd.DataFrame()
    empty_result = MockResult(empty_df)
    
    with pytest.raises(ValueError):
        plot_population_heatmap(empty_result)


def test_plot_population_heatmap_custom_atom_order(output_dir, mock_population_result):
    """Test population heatmap with custom atom ordering."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Custom order: reverse the atoms
    custom_order = [3, 2, 1, 0]
    
    plot_population_heatmap(
        mock_population_result, 
        atom_order=custom_order,
        ax=ax, 
        title="Custom Atom Order"
    )
    
    # Verify y-axis labels match custom order
    y_labels = [t.get_text() for t in ax.get_yticklabels()]
    expected_labels = ['Atom 3', 'Atom 2', 'Atom 1', 'Atom 0']
    assert y_labels == expected_labels
    
    save_path = os.path.join(output_dir, "population_heatmap_custom_order.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_population_heatmap_invalid_atom_order_raises(mock_population_result):
    """Test that invalid atom indices raise ValueError."""
    # Invalid index (99 doesn't exist)
    with pytest.raises(ValueError, match="Invalid atom indices"):
        plot_population_heatmap(mock_population_result, atom_order=[0, 1, 99])


def test_plot_population_heatmap_duplicate_atom_order_raises(mock_population_result):
    """Test that duplicate atom indices raise ValueError."""
    # Duplicate index
    with pytest.raises(ValueError, match="duplicate"):
        plot_population_heatmap(mock_population_result, atom_order=[0, 1, 1, 2])

# Integration test: all visualization types
def test_all_visualization_types_together(output_dir, mock_observables_result, 
                                          mock_bitstrings_result, 
                                          mock_samples_result, 
                                          mock_population_result):
    """Test creating all visualization types in one figure."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot observables
    plot_observables(mock_observables_result, ax=axes[0, 0], title="Observables")
    
    # Plot bitstring distribution
    plot_bitstring_distribution(mock_bitstrings_result, ax=axes[0, 1], title="Bitstrings")
    
    # Plot shot histogram
    plot_shot_histogram(mock_samples_result, ax=axes[1, 0], title="Shot Histogram")
    
    # Plot population heatmap
    plot_population_heatmap(mock_population_result, ax=axes[1, 1], title="Population")
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, "all_visualizations_combined.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
