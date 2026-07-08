"""
Basis diagnostics visualization tests.

Tests for generate_basis_diagnostics(), plot_basis_space_diagram(),
plot_bitstring_space_grid(), plot_blockade_constraint_graph(), and
plot_comprehensive_basis_diagnostics() functions.

All tests save generated images to test_figs/ directory.
DIAGNOSTIC TOOLS: For small systems only (N ≤ 10).
"""

import os
import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sagittarius.viz import (
    generate_basis_diagnostics,
    plot_basis_space_diagram,
    plot_bitstring_space_grid,
    plot_blockade_constraint_graph,
    plot_comprehensive_basis_diagnostics,
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
    """Create a 3-atom register for basis diagnostics."""
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
def sample_edges():
    """Sample blockade edges for 3-atom system."""
    return [(0, 1)]  # Only atoms 0 and 1 are within blockade radius


# ============================================================================
# generate_basis_diagnostics Tests
# ============================================================================

def test_generate_basis_diagnostics_basic(small_register_3atoms, sample_edges):
    """Test basic basis diagnostics generation."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    assert diagnostics['n_atoms'] == 3
    assert diagnostics['full_dimension'] == 8  # 2^3
    assert len(diagnostics['valid_states']) + len(diagnostics['forbidden_states']) == 8
    assert diagnostics['pruning_ratio'] >= 0.0
    assert diagnostics['pruning_ratio'] <= 1.0
    assert 'edges' in diagnostics
    assert 'blockade_graph_density' in diagnostics


def test_generate_basis_diagnostics_auto_edges(small_register_3atoms):
    """Test automatic edge derivation from blockade radius."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=None,  # Auto-derive
    )
    
    assert len(diagnostics['edges']) > 0
    assert diagnostics['n_atoms'] == 3


def test_generate_basis_diagnostics_no_constraints():
    """Test system with no blockade constraints (all states valid)."""
    atoms = [MockAtom(i * 5.0, 0.0) for i in range(3)]  # Far apart
    reg = MockRegister(atoms, blockade_radius=1.0)
    
    diagnostics = generate_basis_diagnostics(reg, blockade_radius=1.0)
    
    assert diagnostics['reduced_dimension'] == 8  # All states valid
    assert len(diagnostics['forbidden_states']) == 0
    assert diagnostics['pruning_ratio'] == 0.0


def test_generate_basis_diagnostics_all_forbidden():
    """Test system where many states are forbidden."""
    # Create tightly packed atoms (many constraints)
    atoms = [MockAtom(i * 0.3, 0.0) for i in range(3)]
    reg = MockRegister(atoms, blockade_radius=1.0)
    
    diagnostics = generate_basis_diagnostics(reg, blockade_radius=1.0)
    
    assert diagnostics['reduced_dimension'] < diagnostics['full_dimension']
    assert len(diagnostics['forbidden_states']) > 0
    assert diagnostics['pruning_ratio'] > 0.0


def test_generate_basis_diagnostics_too_large_raises():
    """Test that large systems raise ValueError."""
    atoms = [MockAtom(i * 1.0, 0.0) for i in range(11)]  # 11 atoms
    reg = MockRegister(atoms, blockade_radius=1.0)
    
    with pytest.raises(ValueError, match="limited to N ≤ 10"):
        generate_basis_diagnostics(reg, blockade_radius=1.0)


def test_generate_basis_diagnostics_bitstring_format(small_register_3atoms, sample_edges):
    """Test that bitstrings are properly formatted."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    # Check all bitstrings have correct length
    for bs in diagnostics['valid_bitstrings']:
        assert len(bs) == 3
        assert all(c in '01' for c in bs)
    
    for bs in diagnostics['forbidden_bitstrings']:
        assert len(bs) == 3
        assert all(c in '01' for c in bs)


def test_generate_basis_diagnostics_sorted_order(small_register_3atoms, sample_edges):
    """Test that states follow ascending integer order (Sagittarius convention)."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    # Verify states are sorted
    assert diagnostics['valid_states'] == sorted(diagnostics['valid_states'])
    assert diagnostics['forbidden_states'] == sorted(diagnostics['forbidden_states'])


# ============================================================================
# plot_basis_space_diagram Tests
# ============================================================================

def test_plot_basis_space_diagram_basic(output_dir, small_register_3atoms, sample_edges):
    """Test basic basis space diagram plotting."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(14, 8))
    plot_basis_space_diagram(diagnostics, ax=ax, title="Basis Space Diagram")
    
    save_path = os.path.join(output_dir, "basis_space_diagram.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_basis_space_diagram_log_scale(output_dir, small_register_3atoms, sample_edges):
    """Test that y-axis uses log scale for better visibility."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(14, 8))
    plot_basis_space_diagram(diagnostics, ax=ax)
    
    # Verify log scale
    assert ax.get_yscale() == 'log'
    
    save_path = os.path.join(output_dir, "basis_space_log_scale.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_basis_space_diagram_custom_title(output_dir, small_register_3atoms, sample_edges):
    """Test custom title override."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(14, 8))
    plot_basis_space_diagram(diagnostics, ax=ax, title="My Custom Title")
    
    assert ax.get_title() == "My Custom Title"
    
    save_path = os.path.join(output_dir, "basis_space_custom_title.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_basis_space_diagram_warning_text(output_dir, small_register_3atoms, sample_edges):
    """Test that diagnostic warning is displayed."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(14, 8))
    plot_basis_space_diagram(diagnostics, ax=ax)
    
    # Check for diagnostic warning in text elements
    texts = [t.get_text() for t in ax.texts]
    assert any("DIAGNOSTIC" in t for t in texts)
    
    save_path = os.path.join(output_dir, "basis_space_warning.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# plot_bitstring_space_grid Tests
# ============================================================================

def test_plot_bitstring_space_grid_basic(output_dir, small_register_3atoms, sample_edges):
    """Test basic bitstring space grid plotting."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(12, 10))
    plot_bitstring_space_grid(diagnostics, ax=ax, title="Bitstring Grid")
    
    save_path = os.path.join(output_dir, "bitstring_grid.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_bitstring_space_grid_colors(output_dir, small_register_3atoms, sample_edges):
    """Test that valid/forbidden states have correct colors."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(12, 10))
    plot_bitstring_space_grid(diagnostics, ax=ax)
    
    # Check legend exists
    legend = ax.get_legend()
    assert legend is not None
    
    # Check legend labels
    texts = [t.get_text() for t in legend.get_texts()]
    assert any("Valid" in t for t in texts)
    assert any("Forbidden" in t for t in texts)
    
    save_path = os.path.join(output_dir, "bitstring_grid_colors.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_bitstring_space_grid_truncation(output_dir, chain_register_4atoms):
    """Test grid truncation for larger systems."""
    diagnostics = generate_basis_diagnostics(
        chain_register_4atoms,
        blockade_radius=1.0,
    )
    
    fig, ax = plt.subplots(figsize=(12, 10))
    plot_bitstring_space_grid(
        diagnostics,
        ax=ax,
        max_display_states=10,  # Limit display
    )
    
    # Should show at most 10 states
    assert len(ax.get_yticklabels()) <= 10
    
    save_path = os.path.join(output_dir, "bitstring_grid_truncated.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_bitstring_space_grid_sorting(output_dir, small_register_3atoms, sample_edges):
    """Test that bitstrings are sorted by integer value."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(12, 10))
    plot_bitstring_space_grid(diagnostics, ax=ax)
    
    # Get y-axis labels
    labels = [t.get_text() for t in ax.get_yticklabels()]
    
    # Convert back to integers and verify ascending order
    if labels:
        values = [int(bs, 2) for bs in labels]
        assert values == sorted(values), "Bitstrings not in ascending order"
    
    save_path = os.path.join(output_dir, "bitstring_grid_sorted.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# plot_blockade_constraint_graph Tests
# ============================================================================

def test_plot_blockade_constraint_graph_basic(output_dir, small_register_3atoms, sample_edges):
    """Test basic blockade constraint graph plotting."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_blockade_constraint_graph(diagnostics, small_register_3atoms, ax=ax)
    
    save_path = os.path.join(output_dir, "constraint_graph.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_blockade_constraint_graph_edges_visible(output_dir, small_register_3atoms, sample_edges):
    """Test that blockade edges are drawn as red dashed lines."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_blockade_constraint_graph(diagnostics, small_register_3atoms, ax=ax)
    
    # Check for red dashed lines
    lines = [line for line in ax.lines if line.get_color() == 'r' or line.get_color() == 'red']
    assert len(lines) > 0, "No red blockade edges found"
    
    save_path = os.path.join(output_dir, "constraint_graph_edges.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_blockade_constraint_graph_statistics_box(output_dir, small_register_3atoms, sample_edges):
    """Test that statistics text box is displayed."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_blockade_constraint_graph(diagnostics, small_register_3atoms, ax=ax)
    
    # Check for statistics text
    texts = [t.get_text() for t in ax.texts]
    assert any("Atoms:" in t for t in texts)
    assert any("Blockade edges:" in t for t in texts)
    
    save_path = os.path.join(output_dir, "constraint_graph_stats.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# plot_comprehensive_basis_diagnostics Tests
# ============================================================================

def test_plot_comprehensive_diagnostics_basic(output_dir, small_register_3atoms, sample_edges):
    """Test comprehensive multi-panel diagnostic figure."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    axes = plot_comprehensive_basis_diagnostics(
        diagnostics,
        small_register_3atoms,
        figsize=(18, 14),
    )
    
    assert len(axes) == 3
    
    save_path = os.path.join(output_dir, "comprehensive_diagnostics.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_comprehensive_diagnostics_with_save(output_dir, small_register_3atoms, sample_edges):
    """Test saving comprehensive diagnostics figure."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    save_path = os.path.join(output_dir, "comprehensive_saved.png")
    
    axes = plot_comprehensive_basis_diagnostics(
        diagnostics,
        small_register_3atoms,
        figsize=(18, 14),
        save_path=save_path,
    )
    
    assert os.path.exists(save_path)
    assert len(axes) == 3
    
    plt.close()


def test_plot_comprehensive_diagnostics_suptitle(output_dir, small_register_3atoms, sample_edges):
    """Test that overall suptitle is set."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    axes = plot_comprehensive_basis_diagnostics(
        diagnostics,
        small_register_3atoms,
        figsize=(18, 14),
    )
    
    # Get current figure
    fig = plt.gcf()
    suptitle = fig._suptitle
    assert suptitle is not None
    assert "DIAGNOSTIC" in suptitle.get_text()
    
    plt.close()


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_workflow_chain_4atoms(output_dir, chain_register_4atoms):
    """Test complete workflow on 4-atom chain."""
    # Generate diagnostics
    diagnostics = generate_basis_diagnostics(
        chain_register_4atoms,
        blockade_radius=1.0,
    )
    
    # Verify data structure
    assert diagnostics['n_atoms'] == 4
    assert diagnostics['full_dimension'] == 16
    assert diagnostics['reduced_dimension'] <= 16
    
    # Create comprehensive visualization
    axes = plot_comprehensive_basis_diagnostics(
        diagnostics,
        chain_register_4atoms,
        figsize=(18, 14),
    )
    
    save_path = os.path.join(output_dir, "workflow_chain_4atoms.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(axes) == 3


def test_consistency_across_functions(small_register_3atoms, sample_edges):
    """Test that all plotting functions accept same diagnostics format."""
    diagnostics = generate_basis_diagnostics(
        small_register_3atoms,
        blockade_radius=1.0,
        edges=sample_edges,
    )
    
    # All three individual plotting functions should work
    fig1, ax1 = plt.subplots()
    plot_basis_space_diagram(diagnostics, ax=ax1)
    plt.close()
    
    fig2, ax2 = plt.subplots()
    plot_bitstring_space_grid(diagnostics, ax=ax2)
    plt.close()
    
    fig3, ax3 = plt.subplots()
    plot_blockade_constraint_graph(diagnostics, small_register_3atoms, ax=ax3)
    plt.close()
    
    # If we reach here without exceptions, consistency is verified
    assert True


def test_edge_case_single_atom():
    """Test diagnostics on single atom system."""
    atoms = [MockAtom(0.0, 0.0)]
    reg = MockRegister(atoms, blockade_radius=1.0)
    
    diagnostics = generate_basis_diagnostics(reg, blockade_radius=1.0)
    
    assert diagnostics['n_atoms'] == 1
    assert diagnostics['full_dimension'] == 2
    assert diagnostics['reduced_dimension'] == 2  # No constraints possible
    assert len(diagnostics['forbidden_states']) == 0


def test_validation_error_on_inconsistent_data():
    """Test validation catches inconsistent diagnostics data."""
    # Create intentionally inconsistent diagnostics
    bad_diagnostics = {
        'n_atoms': 3,
        'full_dimension': 8,
        'reduced_dimension': 5,
        'pruning_ratio': 0.375,
        'valid_bitstrings': ['000', '001'],  # Only 2
        'forbidden_bitstrings': ['010'],  # Only 1
        'valid_states': [0, 1],
        'forbidden_states': [2],
        'edges': [],
        'blockade_graph_density': 0.0,
    }
    
    with pytest.raises(ValueError, match="Inconsistent state counts"):
        plot_basis_space_diagram(bad_diagnostics)
