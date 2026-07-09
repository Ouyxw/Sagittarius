"""
Tests for small-system debugging visualization utilities.
"""

import pytest
import numpy as np
import matplotlib.pyplot as plt

@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Automatically close all figures after each test to prevent memory warnings."""
    yield
    plt.close('all')
from sagittarius.viz.small_system_debug import (
    plot_state_probabilities,
    plot_density_matrix_diagonal,
    plot_density_matrix_magnitude,
    plot_density_matrix_phase,
)


class TestPlotStateProbabilities:
    """Test state probability visualization."""
    
    def test_basic_state_vector(self):
        """Test basic state probability plot."""
        # Bell state: (|00⟩ + |11⟩) / √2
        psi = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)])
        
        ax = plot_state_probabilities(psi)
        assert ax is not None
        assert 'Probability' in ax.get_ylabel()
        plt.close()
    
    def test_3_qubit_state(self):
        """Test with 3-qubit system."""
        # GHZ state: (|000⟩ + |111⟩) / √2
        psi = np.zeros(8)
        psi[0] = 1/np.sqrt(2)
        psi[7] = 1/np.sqrt(2)
        
        ax = plot_state_probabilities(psi)
        assert ax is not None
        assert '3 qubits' in ax.get_title()
        plt.close()
    
    def test_invalid_dimension(self):
        """Test error with non-power-of-2 dimension."""
        psi = np.array([0.5, 0.5, 0.5])  # dim=3, not power of 2
        
        with pytest.raises(ValueError, match="not a power of 2"):
            plot_state_probabilities(psi)
    
    def test_dimension_too_large(self):
        """Test error with dimension exceeding safe limit."""
        # 2^11 = 2048 > MAX_SAFE_DIM (1024)
        psi = np.zeros(2048)
        psi[0] = 1.0
        
        with pytest.raises(ValueError, match="exceeds safe limit"):
            plot_state_probabilities(psi)
    
    def test_not_normalized_warning(self):
        """Test warning for non-normalized state."""
        psi = np.array([0.5, 0.5])  # Sum of squares = 0.5, not 1
        
        with pytest.warns(UserWarning, match="not normalized"):
            ax = plot_state_probabilities(psi)
            assert ax is not None
        plt.close()
    
    def test_multidimensional_array(self):
        """Test error with multidimensional array."""
        psi = np.array([[0.5, 0.5], [0.5, 0.5]])  # 2D instead of 1D
        
        with pytest.raises(ValueError, match="must be 1D"):
            plot_state_probabilities(psi)
    
    def test_custom_title(self):
        """Test custom title override."""
        psi = np.array([1.0, 0.0])  # |0⟩ state
        
        ax = plot_state_probabilities(psi, title="Custom Title")
        assert "Custom Title" in ax.get_title()
        plt.close()


class TestPlotDensityMatrixDiagonal:
    """Test density matrix diagonal visualization."""
    
    def test_basic_density_matrix(self):
        """Test basic density matrix diagonal plot."""
        # Maximally mixed state for 1 qubit
        rho = np.array([[0.5, 0], [0, 0.5]])
        
        ax = plot_density_matrix_diagonal(rho)
        assert ax is not None
        assert 'Population' in ax.get_ylabel()
        plt.close()
    
    def test_pure_state(self):
        """Test with pure state density matrix."""
        # |0⟩⟨0|
        rho = np.array([[1.0, 0], [0, 0.0]])
        
        ax = plot_density_matrix_diagonal(rho)
        assert ax is not None
        plt.close()
    
    def test_non_square_matrix(self):
        """Test error with non-square matrix."""
        rho = np.array([[0.5, 0.5, 0.5], [0.5, 0.5, 0.5]])  # 2x3
        
        with pytest.raises(ValueError, match="must be square"):
            plot_density_matrix_diagonal(rho)
    
    def test_negative_populations_warning(self):
        """Test warning for negative diagonal elements."""
        rho = np.array([[-0.1, 0], [0, 1.1]])  # Unphysical
        
        with pytest.warns(UserWarning, match="negative diagonal"):
            ax = plot_density_matrix_diagonal(rho)
            assert ax is not None
        plt.close()
    
    def test_dimension_too_large(self):
        """Test error with large dimension."""
        dim = 2048  # > MAX_SAFE_DIM
        rho = np.eye(dim) / dim
        
        with pytest.raises(ValueError, match="exceeds safe limit"):
            plot_density_matrix_diagonal(rho)


class TestPlotDensityMatrixMagnitude:
    """Test density matrix magnitude heatmap."""
    
    def test_basic_magnitude_plot(self):
        """Test basic magnitude heatmap."""
        rho = np.array([
            [0.5, 0.1+0.1j],
            [0.1-0.1j, 0.5]
        ])
        
        ax = plot_density_matrix_magnitude(rho)
        assert ax is not None
        assert 'Magnitude' in ax.get_title() or '|ρ' in ax.get_title()
        plt.close()
    
    def test_with_values_annotation(self):
        """Test with numeric value annotations."""
        rho = np.array([
            [0.6, 0.2],
            [0.2, 0.4]
        ])
        
        ax = plot_density_matrix_magnitude(rho, show_values=True)
        assert ax is not None
        plt.close()
    
    def test_non_square_matrix(self):
        """Test error with non-square matrix."""
        rho = np.array([[0.5, 0.5, 0.5], [0.5, 0.5, 0.5]])
        
        with pytest.raises(ValueError, match="must be square"):
            plot_density_matrix_magnitude(rho)


class TestPlotDensityMatrixPhase:
    """Test density matrix phase heatmap."""
    
    def test_basic_phase_plot(self):
        """Test basic phase heatmap."""
        # Create density matrix with complex coherences
        rho = np.array([
            [0.5, 0.1*np.exp(1j*np.pi/4)],
            [0.1*np.exp(-1j*np.pi/4), 0.5]
        ])
        
        ax = plot_density_matrix_phase(rho)
        assert ax is not None
        assert 'Phase' in ax.get_title() or 'arg' in ax.get_title()
        plt.close()
    
    def test_with_threshold(self):
        """Test with custom threshold for masking."""
        rho = np.array([
            [0.5, 1e-5],  # Small off-diagonal
            [1e-5, 0.5]
        ])
        
        ax = plot_density_matrix_phase(rho, threshold=1e-4)
        assert ax is not None
        plt.close()
    
    def test_real_density_matrix(self):
        """Test with real density matrix (phase should be 0 or π)."""
        rho = np.array([
            [0.6, 0.2],
            [0.2, 0.4]
        ])
        
        ax = plot_density_matrix_phase(rho)
        assert ax is not None
        plt.close()
    
    def test_dimension_too_large(self):
        """Test error with large dimension."""
        dim = 2048
        rho = np.eye(dim) / dim
        
        with pytest.raises(ValueError, match="exceeds safe limit"):
            plot_density_matrix_phase(rho)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
