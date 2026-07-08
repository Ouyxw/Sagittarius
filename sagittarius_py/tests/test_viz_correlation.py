"""
Tests for correlation analysis visualization functions.

Validates:
- Pair correlation matrix plotting
- Connected correlation matrix plotting
- Pauli-ZZ correlation matrix plotting
- Blockade conflict heatmap plotting
- Diagnostic error messages for missing data
- Metadata validation
"""

import os
import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from sagittarius.viz import (
    plot_pair_correlation_matrix,
    plot_connected_correlation_matrix,
    plot_pauli_zz_matrix,
    plot_blockade_conflict_heatmap,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def output_dir(tmp_path):
    """Create temporary output directory for test figures."""
    d = tmp_path / "test_figs"
    d.mkdir(exist_ok=True)
    return str(d)


@pytest.fixture
def mock_result_with_pair_corr():
    """Create mock SimulationResult with pair-correlation observables."""
    
    class MockResult:
        def __init__(self):
            self.data = {
                't': [0.0, 0.5, 1.0],
                'pair_corr_0_1': [0.0, 0.3, 0.45],
                'pair_corr_0_2': [0.0, 0.1, 0.15],
                'pair_corr_1_2': [0.0, 0.2, 0.25],
                'pop0': [1.0, 0.7, 0.6],
                'pop1': [1.0, 0.8, 0.7],
                'pop2': [1.0, 0.9, 0.8],
            }
            self.metadata = {
                'register': {'atom_count': 3}
            }
            self.manifest = {}
        
        def to_pandas(self):
            return pd.DataFrame(self.data)
    
    return MockResult()


@pytest.fixture
def mock_result_with_connected_corr():
    """Create mock SimulationResult with connected-correlation observables."""
    
    class MockResult:
        def __init__(self):
            self.data = {
                't': [0.0, 0.5, 1.0],
                'connected_corr_0_1': [0.0, 0.05, 0.12],
                'connected_corr_0_2': [0.0, -0.02, 0.03],
                'connected_corr_1_2': [0.0, 0.08, 0.15],
            }
            self.metadata = {
                'register': {'atom_count': 3}
            }
            self.manifest = {}
        
        def to_pandas(self):
            return pd.DataFrame(self.data)
    
    return MockResult()


@pytest.fixture
def mock_result_with_pauli_zz():
    """Create mock SimulationResult with Pauli-ZZ observables."""
    
    class MockResult:
        def __init__(self):
            self.data = {
                't': [0.0, 0.5, 1.0],
                'pauli_zz_0_1': [1.0, 0.6, 0.4],
                'pauli_zz_0_2': [1.0, 0.8, 0.7],
                'pauli_zz_1_2': [1.0, 0.5, 0.3],
            }
            self.metadata = {
                'register': {'atom_count': 3}
            }
            self.manifest = {}
        
        def to_pandas(self):
            return pd.DataFrame(self.data)
    
    return MockResult()


@pytest.fixture
def mock_result_with_blockade_violation():
    """Create mock SimulationResult with blockade-violation observables."""
    
    class MockResult:
        def __init__(self):
            self.data = {
                't': [0.0, 0.5, 1.0],
                'blockade_violation_0_1': [0.0, 0.15, 0.25],
                'blockade_violation_0_2': [0.0, 0.05, 0.08],
                'blockade_violation_1_2': [0.0, 0.12, 0.18],
            }
            self.metadata = {
                'register': {'atom_count': 3}
            }
            self.manifest = {}
        
        def to_pandas(self):
            return pd.DataFrame(self.data)
    
    return MockResult()


@pytest.fixture
def mock_result_no_observables():
    """Create mock SimulationResult without correlation observables."""
    
    class MockResult:
        def __init__(self):
            self.data = {
                't': [0.0, 0.5, 1.0],
                'pop0': [1.0, 0.7, 0.6],
                'pop1': [1.0, 0.8, 0.7],
            }
            self.metadata = {
                'register': {'atom_count': 2}
            }
            self.manifest = {}
        
        def to_pandas(self):
            return pd.DataFrame(self.data)
    
    return MockResult()


# ============================================================================
# Test Pair Correlation Matrix
# ============================================================================

class TestPlotPairCorrelationMatrix:
    
    def test_basic_plot(self, mock_result_with_pair_corr, output_dir):
        """Test basic pair correlation matrix plot."""
        ax = plot_pair_correlation_matrix(mock_result_with_pair_corr)
        
        assert isinstance(ax, Axes)
        
        save_path = os.path.join(output_dir, "pair_corr_basic.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_custom_title(self, mock_result_with_pair_corr, output_dir):
        """Test custom title."""
        ax = plot_pair_correlation_matrix(
            mock_result_with_pair_corr,
            title="Custom Pair Correlation Title"
        )
        
        assert "Custom Pair Correlation Title" in ax.get_title()
        
        save_path = os.path.join(output_dir, "pair_corr_custom_title.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_hide_values(self, mock_result_with_pair_corr, output_dir):
        """Test plotting without numerical annotations."""
        ax = plot_pair_correlation_matrix(
            mock_result_with_pair_corr,
            show_values=False
        )
        
        # Should have no text annotations
        assert len(ax.texts) == 0
        
        save_path = os.path.join(output_dir, "pair_corr_no_values.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_missing_observables_raises(self, mock_result_no_observables):
        """Test that missing observables raise clear error."""
        with pytest.raises(ValueError, match="No PairCorrelation observables found"):
            plot_pair_correlation_matrix(mock_result_no_observables)
    
    def test_missing_atom_count_raises(self, mock_result_with_pair_corr):
        """Test that missing atom count raises error."""
        mock_result_with_pair_corr.metadata = {}
        
        with pytest.raises(ValueError, match="Cannot determine atom count"):
            plot_pair_correlation_matrix(mock_result_with_pair_corr)


# ============================================================================
# Test Connected Correlation Matrix
# ============================================================================

class TestPlotConnectedCorrelationMatrix:
    
    def test_basic_plot(self, mock_result_with_connected_corr, output_dir):
        """Test basic connected correlation matrix plot."""
        ax = plot_connected_correlation_matrix(mock_result_with_connected_corr)
        
        assert isinstance(ax, Axes)
        
        save_path = os.path.join(output_dir, "connected_corr_basic.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_significance_threshold(self, mock_result_with_connected_corr, output_dir):
        """Test significance threshold filtering."""
        ax = plot_connected_correlation_matrix(
            mock_result_with_connected_corr,
            significance_threshold=0.1
        )
        
        # Only significant values should be annotated
        texts = [t.get_text() for t in ax.texts]
        for text in texts:
            assert abs(float(text)) >= 0.1
        
        save_path = os.path.join(output_dir, "connected_corr_threshold.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_missing_observables_raises(self, mock_result_no_observables):
        """Test that missing observables raise clear error."""
        with pytest.raises(ValueError, match="No ConnectedPairCorrelation observables found"):
            plot_connected_correlation_matrix(mock_result_no_observables)


# ============================================================================
# Test Pauli-ZZ Matrix
# ============================================================================

class TestPlotPauliZZMatrix:
    
    def test_basic_plot(self, mock_result_with_pauli_zz, output_dir):
        """Test basic Pauli-ZZ matrix plot."""
        ax = plot_pauli_zz_matrix(mock_result_with_pauli_zz)
        
        assert isinstance(ax, Axes)
        
        save_path = os.path.join(output_dir, "pauli_zz_basic.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_diagonal_is_one(self, mock_result_with_pauli_zz):
        """Test that diagonal is fixed to +1."""
        ax = plot_pauli_zz_matrix(mock_result_with_pauli_zz)
        
        # Get the image data
        im = ax.get_images()[0]
        matrix = im.get_array()
        
        # Check diagonal
        for i in range(matrix.shape[0]):
            assert matrix[i, i] == 1.0
        
        plt.close()
    
    def test_missing_observables_raises(self, mock_result_no_observables):
        """Test that missing observables raise clear error."""
        with pytest.raises(ValueError, match="No PauliZZ observables found"):
            plot_pauli_zz_matrix(mock_result_no_observables)


# ============================================================================
# Test Blockade Conflict Heatmap
# ============================================================================

class TestPlotBlockadeConflictHeatmap:
    
    def test_matrix_mode(self, mock_result_with_blockade_violation, output_dir):
        """Test matrix mode plotting."""
        ax = plot_blockade_conflict_heatmap(
            mock_result_with_blockade_violation,
            mode='matrix'
        )
        
        assert isinstance(ax, Axes)
        
        save_path = os.path.join(output_dir, "conflict_matrix.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_edges_mode_with_explicit_edges(self, mock_result_with_blockade_violation, output_dir):
        """Test edges mode with explicit edge list."""
        edges = [(0, 1), (0, 2), (1, 2)]
        
        ax = plot_blockade_conflict_heatmap(
            mock_result_with_blockade_violation,
            mode='edges',
            edges=edges
        )
        
        assert isinstance(ax, Axes)
        
        save_path = os.path.join(output_dir, "conflict_edges.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_invalid_mode_raises(self, mock_result_with_blockade_violation):
        """Test that invalid mode raises error."""
        with pytest.raises(ValueError, match="Invalid mode"):
            plot_blockade_conflict_heatmap(
                mock_result_with_blockade_violation,
                mode='invalid'
            )
    
    def test_edges_mode_no_edges_raises(self, mock_result_with_blockade_violation):
        """Test that edges mode without edges raises error."""
        with pytest.raises(ValueError, match="No edges provided"):
            plot_blockade_conflict_heatmap(
                mock_result_with_blockade_violation,
                mode='edges'
            )
    
    def test_missing_observables_raises(self, mock_result_no_observables):
        """Test that missing observables raise clear error."""
        with pytest.raises(ValueError, match="No BlockadeViolation observables found"):
            plot_blockade_conflict_heatmap(mock_result_no_observables, mode='matrix')


# ============================================================================
# Integration Tests
# ============================================================================

class TestCorrelationVisualizationIntegration:
    
    def test_all_correlation_types_together(self, 
                                            mock_result_with_pair_corr,
                                            mock_result_with_connected_corr,
                                            mock_result_with_pauli_zz,
                                            mock_result_with_blockade_violation,
                                            output_dir):
        """Test creating all correlation plots in one figure."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 16))
        
        plot_pair_correlation_matrix(mock_result_with_pair_corr, ax=axes[0, 0])
        plot_connected_correlation_matrix(mock_result_with_connected_corr, ax=axes[0, 1])
        plot_pauli_zz_matrix(mock_result_with_pauli_zz, ax=axes[1, 0])
        plot_blockade_conflict_heatmap(
            mock_result_with_blockade_violation, 
            mode='matrix',
            ax=axes[1, 1]
        )
        
        plt.tight_layout()
        save_path = os.path.join(output_dir, "all_correlations_combined.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        assert os.path.exists(save_path)
    
    def test_error_messages_are_actionable(self, mock_result_no_observables):
        """Test that error messages provide actionable guidance."""
        try:
            plot_pair_correlation_matrix(mock_result_no_observables)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            assert "Available columns:" in error_msg
            assert "Example:" in error_msg
            assert "PairCorrelation" in error_msg
