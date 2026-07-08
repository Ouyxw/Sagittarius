"""
Geometry diagnostics visualization tests.

Tests for extract_geometry_diagnostics(), plot_geometry_diagnostics(),
and plot_unit_disk_graph() functions.

All tests save generated images to test_figs/ directory.
DIAGNOSTIC TOOLS: For pre-simulation validation only.
"""

import os
import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sagittarius.viz import (
    extract_geometry_diagnostics,
    plot_geometry_diagnostics,
    plot_unit_disk_graph,
)


# Mock classes for testing
class MockAtom:
    """Mock Atom object."""
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class MockRegister:
    """Mock Register object."""
    def __init__(self, atoms, blockade_radius=None):
        self.atoms = atoms
        self.blockade_radius = blockade_radius
    
    @property
    def positions(self):
        return [[a.x, a.y] for a in self.atoms]


# Test fixtures
@pytest.fixture
def output_dir():
    """Create output directory for test figures."""
    output_path = os.path.join(os.path.dirname(__file__), 'test_figs')
    os.makedirs(output_path, exist_ok=True)
    return output_path


@pytest.fixture
def small_register_3atoms():
    """Create a 3-atom register for geometry diagnostics."""
    atoms = [
        MockAtom(0.0, 0.0),
        MockAtom(0.5, 0.0),
        MockAtom(2.0, 0.0),
    ]
    return MockRegister(atoms, blockade_radius=1.0)


@pytest.fixture
def chain_register_4atoms():
    """Create a 4-atom chain register."""
    atoms = [MockAtom(i * 0.6, 0.0) for i in range(4)]
    return MockRegister(atoms, blockade_radius=1.0)


@pytest.fixture
def square_register_4atoms():
    """Create a 4-atom square lattice."""
    atoms = [
        MockAtom(0.0, 0.0),
        MockAtom(1.0, 0.0),
        MockAtom(0.0, 1.0),
        MockAtom(1.0, 1.0),
    ]
    return MockRegister(atoms, blockade_radius=1.5)


# ===== Data Extraction Tests =====

class TestExtractGeometryDiagnostics:
    """Tests for extract_geometry_diagnostics()."""
    
    def test_basic_distance_matrix(self, small_register_3atoms):
        """Test basic distance matrix computation."""
        diag = extract_geometry_diagnostics(small_register_3atoms)
        
        assert diag['n_atoms'] == 3
        assert diag['distance_matrix'].shape == (3, 3)
        assert diag['positions'].shape == (3, 2)
        
        # Check symmetry
        assert np.allclose(diag['distance_matrix'], diag['distance_matrix'].T)
        
        # Check diagonal is zero
        assert np.allclose(np.diag(diag['distance_matrix']), 0)
    
    def test_vdw_matrix_with_C6(self, small_register_3atoms):
        """Test VDW interaction matrix computation."""
        C6 = 80.0  # Typical value for Rydberg atoms
        diag = extract_geometry_diagnostics(small_register_3atoms, C6=C6)
        
        assert diag['vdw_matrix'] is not None
        assert diag['vdw_matrix'].shape == (3, 3)
        
        # Check diagonal is zero
        assert np.allclose(np.diag(diag['vdw_matrix']), 0)
        
        # Check V_ij = C6 / r^6 for off-diagonal elements
        dist_matrix = diag['distance_matrix']
        vdw_matrix = diag['vdw_matrix']
        
        for i in range(3):
            for j in range(3):
                if i != j and dist_matrix[i, j] > 0:
                    expected = C6 / (dist_matrix[i, j]**6)
                    assert np.isclose(vdw_matrix[i, j], expected)
    
    def test_adjacency_matrix_with_blockade(self, small_register_3atoms):
        """Test adjacency matrix computation."""
        diag = extract_geometry_diagnostics(small_register_3atoms, blockade_radius=1.0)
        
        assert diag['adjacency_matrix'] is not None
        assert diag['adjacency_matrix'].shape == (3, 3)
        
        # Check diagonal is zero
        assert np.allclose(np.diag(diag['adjacency_matrix']), 0)
        
        # Check binary values
        assert set(np.unique(diag['adjacency_matrix'])).issubset({0, 1})
    
    def test_edge_list_extraction(self, small_register_3atoms):
        """Test edge list extraction from adjacency matrix."""
        diag = extract_geometry_diagnostics(small_register_3atoms, blockade_radius=1.0)
        
        assert len(diag['edges']) > 0
        assert all(isinstance(edge, tuple) and len(edge) == 2 for edge in diag['edges'])
        
        # Atoms 0 and 1 are at distance 0.5 < R_b=1.0, so should be connected
        assert (0, 1) in diag['edges'] or (1, 0) in diag['edges']
    
    def test_graph_density(self, chain_register_4atoms):
        """Test graph density calculation."""
        diag = extract_geometry_diagnostics(chain_register_4atoms, blockade_radius=1.0)
        
        assert 0.0 <= diag['graph_density'] <= 1.0
        
        # For 4 atoms in a chain with spacing 0.6 and R_b=1.0:
        # Edges: (0,1), (1,2), (2,3) -> 3 edges
        # Max edges: 4*3/2 = 6
        # Density: 3/6 = 0.5
        assert np.isclose(diag['graph_density'], 0.5)
    
    def test_distance_statistics(self, small_register_3atoms):
        """Test distance statistics computation."""
        diag = extract_geometry_diagnostics(small_register_3atoms)
        
        assert diag['min_distance'] > 0
        assert diag['max_distance'] >= diag['min_distance']
        assert diag['mean_distance'] >= diag['min_distance']
        assert diag['mean_distance'] <= diag['max_distance']
    
    def test_invalid_C6_raises(self, small_register_3atoms):
        """Test that invalid C6 raises ValueError."""
        with pytest.raises(ValueError, match="C6 coefficient must be positive"):
            extract_geometry_diagnostics(small_register_3atoms, C6=-1.0)
    
    def test_invalid_blockade_radius_raises(self, small_register_3atoms):
        """Test that invalid blockade radius raises ValueError."""
        with pytest.raises(ValueError, match="Blockade radius must be positive"):
            extract_geometry_diagnostics(small_register_3atoms, blockade_radius=-1.0)
    
    def test_empty_register_raises(self):
        """Test that empty register raises ValueError."""
        empty_reg = MockRegister([])
        with pytest.raises(ValueError, match="Could not extract positions"):
            extract_geometry_diagnostics(empty_reg)


# ===== Visualization Tests =====

class TestPlotGeometryDiagnostics:
    """Tests for plot_geometry_diagnostics()."""
    
    def test_basic_plot(self, small_register_3atoms, output_dir):
        """Test basic geometry diagnostics plot."""
        save_path = os.path.join(output_dir, "test_geom_diag_basic.png")
        
        axes = plot_geometry_diagnostics(
            small_register_3atoms,
            blockade_radius=1.0,
            save_path=save_path
        )
        
        assert len(axes) == 3  # Register layout + distance matrix + adjacency matrix
        assert os.path.exists(save_path)
    
    def test_plot_with_vdw(self, small_register_3atoms, output_dir):
        """Test plot with VDW matrix."""
        save_path = os.path.join(output_dir, "test_geom_diag_vdw.png")
        
        axes = plot_geometry_diagnostics(
            small_register_3atoms,
            blockade_radius=1.0,
            C6=80.0,
            save_path=save_path
        )
        
        assert len(axes) == 4  # Register + distance + VDW + adjacency
        assert os.path.exists(save_path)
    
    def test_plot_full(self, chain_register_4atoms, output_dir):
        """Test full plot with all panels."""
        save_path = os.path.join(output_dir, "test_geom_diag_full.png")
        
        axes = plot_geometry_diagnostics(
            chain_register_4atoms,
            blockade_radius=1.0,
            C6=80.0,
            show_distances=True,
            save_path=save_path
        )
        
        assert len(axes) == 4  # Register + distance + VDW + adjacency
        assert os.path.exists(save_path)
    
    def test_heatmap_annotations_present(self, small_register_3atoms, output_dir):
        """Test that heatmap cells have numerical annotations."""
        save_path = os.path.join(output_dir, "test_heatmap_annotations.png")
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        plt.close(fig)  # Close the figure we just created
        
        axes_result = plot_geometry_diagnostics(
            small_register_3atoms,
            blockade_radius=1.0,
            save_path=save_path
        )
        
        # The distance matrix should have text annotations
        ax_dist = axes_result[1]
        texts = [child for child in ax_dist.get_children() 
                if hasattr(child, 'get_text')]
        
        # Should have some text elements (annotations)
        assert len(texts) > 0
    
    def test_custom_title(self, small_register_3atoms, output_dir):
        """Test custom title."""
        save_path = os.path.join(output_dir, "test_geom_diag_custom_title.png")
        
        axes = plot_geometry_diagnostics(
            small_register_3atoms,
            blockade_radius=1.0,
            title="Custom Geometry Diagnostic Title",
            save_path=save_path
        )
        
        assert os.path.exists(save_path)
    
    def test_no_adjacency_panel(self, small_register_3atoms, output_dir):
        """Test plot without adjacency panel."""
        save_path = os.path.join(output_dir, "test_geom_diag_no_adj.png")
        
        axes = plot_geometry_diagnostics(
            small_register_3atoms,
            blockade_radius=1.0,
            show_adjacency=False,
            save_path=save_path
        )
        
        assert len(axes) == 2  # Only register + distance
        assert os.path.exists(save_path)
    
    def test_no_vdw_panel(self, small_register_3atoms, output_dir):
        """Test plot without VDW panel."""
        save_path = os.path.join(output_dir, "test_geom_diag_no_vdw.png")
        
        axes = plot_geometry_diagnostics(
            small_register_3atoms,
            blockade_radius=1.0,
            C6=80.0,
            show_vdw_matrix=False,
            save_path=save_path
        )
        
        assert len(axes) == 3  # Register + distance + adjacency (no VDW)
        assert os.path.exists(save_path)


class TestPlotUnitDiskGraph:
    """Tests for plot_unit_disk_graph()."""
    
    def test_basic_udg_plot(self, small_register_3atoms, output_dir):
        """Test basic unit disk graph plot."""
        save_path = os.path.join(output_dir, "test_udg_basic.png")
        
        ax = plot_unit_disk_graph(
            small_register_3atoms,
            blockade_radius=1.0,
            save_path=save_path
        )
        
        assert ax is not None
        assert os.path.exists(save_path)
    
    def test_udg_with_distances(self, small_register_3atoms, output_dir):
        """Test UDG plot with distance annotations."""
        save_path = os.path.join(output_dir, "test_udg_distances.png")
        
        ax = plot_unit_disk_graph(
            small_register_3atoms,
            blockade_radius=1.0,
            show_distances=True,
            save_path=save_path
        )
        
        assert ax is not None
        assert os.path.exists(save_path)
    
    def test_udg_without_labels(self, small_register_3atoms, output_dir):
        """Test UDG plot without atom labels."""
        save_path = os.path.join(output_dir, "test_udg_no_labels.png")
        
        ax = plot_unit_disk_graph(
            small_register_3atoms,
            blockade_radius=1.0,
            show_labels=False,
            save_path=save_path
        )
        
        assert ax is not None
        assert os.path.exists(save_path)
    
    def test_udg_custom_title(self, small_register_3atoms, output_dir):
        """Test UDG plot with custom title."""
        save_path = os.path.join(output_dir, "test_udg_custom_title.png")
        
        ax = plot_unit_disk_graph(
            small_register_3atoms,
            blockade_radius=1.0,
            title="Custom UDG Title",
            save_path=save_path
        )
        
        assert ax is not None
        assert os.path.exists(save_path)


# ===== Integration Tests =====

class TestGeometryDiagnosticsIntegration:
    """Integration tests for complete workflow."""
    
    def test_complete_workflow(self, square_register_4atoms, output_dir):
        """Test complete geometry diagnostics workflow."""
        save_path = os.path.join(output_dir, "test_integration_complete.png")
        
        # Extract diagnostics
        diag = extract_geometry_diagnostics(
            square_register_4atoms,
            blockade_radius=1.5,
            C6=80.0
        )
        
        # Verify data structure
        assert diag['n_atoms'] == 4
        assert diag['distance_matrix'].shape == (4, 4)
        assert diag['vdw_matrix'] is not None
        assert diag['adjacency_matrix'] is not None
        
        # Create visualization
        axes = plot_geometry_diagnostics(
            square_register_4atoms,
            blockade_radius=1.5,
            C6=80.0,
            show_distances=True,
            save_path=save_path
        )
        
        assert len(axes) == 4
        assert os.path.exists(save_path)
    
    def test_consistency_between_extract_and_plot(self, chain_register_4atoms):
        """Test consistency between data extraction and visualization."""
        # Extract data
        diag = extract_geometry_diagnostics(
            chain_register_4atoms,
            blockade_radius=1.0,
            C6=80.0
        )
        
        # Create plot (without saving)
        axes = plot_geometry_diagnostics(
            chain_register_4atoms,
            blockade_radius=1.0,
            C6=80.0,
            show_distances=False,
            show_vdw_matrix=True,
            show_adjacency=True
        )
        
        # Verify all panels are present
        assert len(axes) == 4
        
        plt.close('all')
    
    def test_multiple_configurations(self, small_register_3atoms, output_dir):
        """Test multiple configurations in sequence."""
        configs = [
            {'blockade_radius': 0.5, 'C6': None},
            {'blockade_radius': 1.0, 'C6': 80.0},
            {'blockade_radius': 1.5, 'C6': 120.0},
        ]
        
        for i, config in enumerate(configs):
            save_path = os.path.join(output_dir, f"test_multi_config_{i}.png")
            
            axes = plot_geometry_diagnostics(
                small_register_3atoms,
                **config,
                save_path=save_path
            )
            
            assert os.path.exists(save_path)
        
        plt.close('all')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
