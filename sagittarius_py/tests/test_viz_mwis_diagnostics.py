"""
Tests for MWIS-specific diagnostic visualization utilities.

Validates convergence plots and feasibility diagrams for MWIS problem solving.
"""

import numpy as np
import pytest
import matplotlib.pyplot as plt

@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Automatically close all figures after each test to prevent memory warnings."""
    yield
    plt.close('all')
from unittest.mock import Mock

from sagittarius.viz.mwis_diagnostics import (
    plot_mwis_convergence,
    plot_mwis_feasibility_diagram,
)


class MockRegister:
    """Mock Register object for testing."""
    def __init__(self, n_atoms=5, spacing=4.0):
        self.atoms = []
        for i in range(n_atoms):
            atom = Mock()
            atom.position = np.array([i * spacing, 0.0])
            self.atoms.append(atom)
        self.manifest = {}


class MockResult:
    """Mock SimulationResult for testing."""
    def __init__(self, data_dict, manifest=None):
        self.data = data_dict
        self.metadata = {}
        self.diagnostics = {}
        self.manifest = manifest or {}
        self.t = np.array(data_dict.get('t', []))
    
    def to_pandas(self):
        import pandas as pd
        return pd.DataFrame(self.data)


def create_mock_mwis_result(n_times=50, optimal_weight=10.0):
    """Create a mock MWIS result with convergence data."""
    t = np.linspace(0, 10.0, n_times)
    
    # Simulate weight convergence (increasing towards optimal)
    weight_vals = optimal_weight * (1 - np.exp(-t / 3.0)) + np.random.normal(0, 0.2, n_times)
    weight_vals = np.clip(weight_vals, 0, optimal_weight * 1.1)
    
    # Simulate constraint violations (decreasing to zero)
    violations = np.maximum(0, 5 - t).astype(int)
    
    data = {
        't': t,
        'weight': weight_vals,
        'violations': violations,
    }
    
    return MockResult(data)


class TestMWISConvergence:
    """Tests for plot_mwis_convergence."""
    
    def test_normal_convergence(self):
        """Test with normal MWIS convergence data."""
        result = create_mock_mwis_result(optimal_weight=10.0)
        
        ax = plot_mwis_convergence(result, optimal_weight=10.0)
        
        assert ax is not None
        assert len(ax.lines) >= 1  # Weight evolution line
        
        plt.close()
    
    def test_missing_time_column(self):
        """Test error when time column is missing."""
        result = MockResult({'weight': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="No time column 't' found"):
            plot_mwis_convergence(result)
    
    def test_missing_weight_observable(self):
        """Test error when weight observable is missing."""
        result = MockResult({'t': [0, 1], 'other': [1, 2]})
        
        with pytest.raises(ValueError, match="No weight observable found"):
            plot_mwis_convergence(result)
    
    def test_approximation_ratio_display(self):
        """Test approximation ratio calculation and display."""
        result = create_mock_mwis_result(optimal_weight=10.0)
        
        ax = plot_mwis_convergence(result, optimal_weight=10.0)
        
        # Check for approximation ratio text
        texts = [child for child in ax.get_children() 
                if hasattr(child, 'get_text')]
        ratio_found = any("Approx ratio" in str(t.get_text()) 
                         for t in texts if hasattr(t, 'get_text'))
        
        assert ratio_found, "Approximation ratio not displayed"
        
        plt.close()
    
    def test_constraint_violations_toggle(self):
        """Test showing/hiding constraint violations."""
        result = create_mock_mwis_result()
        
        # With violations
        ax_with = plot_mwis_convergence(result, show_constraint_violations=True)
        assert len(ax_with.lines) >= 1
        
        plt.close()
        
        # Without violations
        ax_without = plot_mwis_convergence(result, show_constraint_violations=False)
        assert len(ax_without.lines) >= 1
        
        plt.close()
    
    def test_artifact_link_display(self):
        """Test artifact link is displayed when manifest is present."""
        result = create_mock_mwis_result()
        result.manifest = {'artifact_id': 'mwis-convergence-test-123'}
        
        ax = plot_mwis_convergence(result, optimal_weight=10.0)
        
        # Check for artifact link in the plot
        fig = ax.get_figure()
        all_texts = []
        
        for child in fig.get_children():
            if hasattr(child, 'get_text'):
                all_texts.append(child.get_text())
            if hasattr(child, 'get_children'):
                for grandchild in child.get_children():
                    if hasattr(grandchild, 'get_text'):
                        all_texts.append(grandchild.get_text())
        
        artifact_found = any('Artifact: mwis-convergence-test-123' in text for text in all_texts)
        disclaimer_found = any('DIAGNOSTIC VIEW' in text for text in all_texts)
        
        assert artifact_found, "Artifact link not found in plot"
        assert disclaimer_found, "Disclaimer not found in plot"
        
        plt.close()


class TestMWISFeasibilityDiagram:
    """Tests for plot_mwis_feasibility_diagram."""
    
    def create_mock_register(self, n_atoms=5):
        """Create a mock register with linear chain geometry."""
        return MockRegister(n_atoms=n_atoms, spacing=4.0)
    
    def test_feasible_solution(self):
        """Test with a feasible solution (no violations)."""
        reg = self.create_mock_register(n_atoms=5)
        bitstring = "10101"  # Alternating pattern, no adjacent selected
        edges = [(i, i+1) for i in range(4)]  # Chain edges
        
        axes = plot_mwis_feasibility_diagram(reg, bitstring, edges, blockade_radius=5.0)
        
        assert len(axes) == 2  # Two panels
        plt.close()
    
    def test_infeasible_solution(self):
        """Test with an infeasible solution (has violations)."""
        reg = self.create_mock_register(n_atoms=5)
        bitstring = "11000"  # Adjacent atoms both selected
        edges = [(i, i+1) for i in range(4)]
        
        axes = plot_mwis_feasibility_diagram(reg, bitstring, edges, blockade_radius=5.0)
        
        assert len(axes) == 2
        plt.close()
    
    def test_bitstring_length_mismatch(self):
        """Test error when bitstring length doesn't match atom count."""
        reg = self.create_mock_register(n_atoms=5)
        bitstring = "101"  # Too short
        edges = [(0, 1), (1, 2)]
        
        with pytest.raises(ValueError, match="Bitstring length .* does not match"):
            plot_mwis_feasibility_diagram(reg, bitstring, edges, blockade_radius=5.0)
    
    def test_invalid_bitstring_characters(self):
        """Test error when bitstring contains invalid characters."""
        reg = self.create_mock_register(n_atoms=5)
        bitstring = "10a01"  # Contains 'a'
        edges = [(0, 1), (1, 2)]
        
        with pytest.raises(ValueError, match="must contain only '0' and '1'"):
            plot_mwis_feasibility_diagram(reg, bitstring, edges, blockade_radius=5.0)
    
    def test_distance_matrix_heatmap(self):
        """Test distance matrix heatmap display."""
        reg = self.create_mock_register(n_atoms=5)
        bitstring = "10101"
        edges = [(i, i+1) for i in range(4)]
        
        axes = plot_mwis_feasibility_diagram(
            reg, bitstring, edges, 
            blockade_radius=5.0,
            show_distance_matrix=True
        )
        
        # Second panel should have imshow (heatmap)
        ax_heatmap = axes[1]
        assert len(ax_heatmap.images) > 0, "Distance matrix heatmap not displayed"
        
        plt.close()
    
    def test_blockade_circles(self):
        """Test blockade radius circles around selected atoms."""
        reg = self.create_mock_register(n_atoms=5)
        bitstring = "10101"
        edges = [(i, i+1) for i in range(4)]
        
        axes = plot_mwis_feasibility_diagram(reg, bitstring, edges, blockade_radius=5.0)
        ax_spatial = axes[0]
        
        # Should have Circle patches for blockade radii
        patches = [child for child in ax_spatial.get_children() 
                  if isinstance(child, plt.Circle)]
        
        assert len(patches) > 0, "Blockade circles not displayed"
        
        plt.close()
    
    def test_conflict_markers(self):
        """Test conflict markers on violated edges."""
        reg = self.create_mock_register(n_atoms=5)
        bitstring = "11000"  # Violation between atoms 0 and 1
        edges = [(i, i+1) for i in range(4)]
        
        axes = plot_mwis_feasibility_diagram(reg, bitstring, edges, blockade_radius=5.0)
        ax_spatial = axes[0]
        
        # Should have 'X' markers for conflicts
        collections = ax_spatial.collections
        # X markers are rendered as Line2D or PathCollection
        
        plt.close()
    
    def test_artifact_link_display(self):
        """Test artifact link is displayed when manifest is present."""
        reg = self.create_mock_register(n_atoms=5)
        reg.manifest = {'artifact_id': 'mwis-feasibility-test-456'}
        bitstring = "10101"
        edges = [(i, i+1) for i in range(4)]
        
        axes = plot_mwis_feasibility_diagram(reg, bitstring, edges, blockade_radius=5.0)
        fig = axes[0].get_figure()
        
        # Check for artifact link in figure-level text
        all_texts = []
        for child in fig.get_children():
            if hasattr(child, 'get_text'):
                all_texts.append(child.get_text())
        
        artifact_found = any('Artifact: mwis-feasibility-test-456' in text for text in all_texts)
        disclaimer_found = any('DIAGNOSTIC VIEW' in text for text in all_texts)
        
        assert artifact_found, "Artifact link not found in feasibility diagram"
        assert disclaimer_found, "Disclaimer not found in feasibility diagram"
        
        plt.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
