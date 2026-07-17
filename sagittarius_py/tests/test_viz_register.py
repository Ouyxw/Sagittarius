"""
Register visualization tests.

Tests for plot_register() and plot_interaction_graph() functions.
All tests save generated images to test_figs/ directory.
"""

import os
import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Automatically close all figures after each test to prevent memory warnings."""
    yield
    plt.close('all')
from sagittarius.viz import plot_register, plot_interaction_graph


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
def simple_register():
    """Create a simple 3-atom register."""
    atoms = [
        MockAtom(0.0, 0.0),
        MockAtom(3.0, 0.0),
        MockAtom(1.5, 2.6),
    ]
    return MockRegister(atoms, blockade_radius=4.0)


@pytest.fixture
def chain_register():
    """Create a linear chain register."""
    atoms = [MockAtom(i * 4.0, 0.0) for i in range(5)]
    return MockRegister(atoms, blockade_radius=5.0)


@pytest.fixture
def negative_coords_register():
    """Create register with negative coordinates."""
    atoms = [
        MockAtom(-3.0, -3.0),
        MockAtom(0.0, 0.0),
        MockAtom(3.0, 3.0),
    ]
    return MockRegister(atoms, blockade_radius=6.0)


# Tests
def test_plot_register_basic(output_dir, simple_register):
    """Test basic register plotting."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, ax=ax, title="Basic Register")
    
    save_path = os.path.join(output_dir, "register_basic.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    # get_aspect() returns 'equal' string or numeric value 1.0
    aspect = ax.get_aspect()
    assert aspect == 'equal' or np.isclose(aspect, 1.0)


def test_plot_register_with_edges(output_dir, simple_register):
    """Test register plotting with blockade edges."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, edges=True, ax=ax,
                 title="Register with Edges")
    
    save_path = os.path.join(output_dir, "register_with_edges.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_without_labels(output_dir, simple_register):
    """Test register plotting without atom labels."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, labels=False, ax=ax,
                 title="Register without Labels")
    
    save_path = os.path.join(output_dir, "register_no_labels.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_highlight_atoms(output_dir, simple_register):
    """Test register plotting with highlighted atoms."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, 
                 highlight_atoms=[0, 2], highlight_color='red',
                 ax=ax, title="Register with Highlights")
    
    save_path = os.path.join(output_dir, "register_highlights.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_custom_atom_size(output_dir, simple_register):
    """Test register plotting with custom atom sizes."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    sizes = [50, 200, 500]
    titles = ["Small (50)", "Medium (200)", "Large (500)"]
    
    for ax, size, title in zip(axes, sizes, titles):
        plot_register(simple_register, blockade_radius=4.0, 
                     atom_size=size, ax=ax, title=title)
    
    save_path = os.path.join(output_dir, "register_atom_sizes.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_chain_layout(output_dir, chain_register):
    """Test register plotting with chain layout (long aspect ratio)."""
    fig, ax = plt.subplots(figsize=(14, 4))
    plot_register(chain_register, blockade_radius=5.0, ax=ax,
                 title="Chain Layout")
    
    save_path = os.path.join(output_dir, "register_chain.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    # Verify atoms are still circular despite long aspect ratio
    # get_aspect() returns 'equal' string or numeric value 1.0
    aspect = ax.get_aspect()
    assert aspect == 'equal' or np.isclose(aspect, 1.0)


def test_plot_register_negative_coordinates(output_dir, negative_coords_register):
    """Test register plotting with negative coordinates."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(negative_coords_register, blockade_radius=6.0, ax=ax,
                 title="Negative Coordinates")
    
    save_path = os.path.join(output_dir, "register_negative_coords.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_empty_raises(simple_register):
    """Test that empty register raises ValueError."""
    empty_reg = MockRegister([], blockade_radius=4.0)
    
    with pytest.raises(ValueError):
        plot_register(empty_reg, blockade_radius=4.0)


def test_plot_register_invalid_highlight_index_raises(simple_register):
    """Test that invalid highlight index raises ValueError."""
    with pytest.raises(ValueError, match="out of range"):
        plot_register(simple_register, blockade_radius=4.0, 
                     highlight_atoms=[10])


def test_plot_interaction_graph_basic(output_dir, simple_register):
    """Test basic interaction graph plotting."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_interaction_graph(simple_register, blockade_radius=4.0, ax=ax)
    
    save_path = os.path.join(output_dir, "interaction_graph_basic.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_interaction_graph_with_distances(output_dir, simple_register):
    """Test interaction graph with distance labels."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_interaction_graph(simple_register, blockade_radius=4.0, 
                          show_distances=True, ax=ax)
    
    save_path = os.path.join(output_dir, "interaction_graph_distances.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_circular_atoms_verification(output_dir):
    """Verify that atoms are perfect circles in various layouts."""
    # Create registers with different aspect ratios
    test_cases = [
        ("Square", [MockAtom(0, 0), MockAtom(3, 0), MockAtom(0, 3), MockAtom(3, 3)], 4.0),
        ("Wide", [MockAtom(0, 0), MockAtom(10, 0), MockAtom(5, 0.1)], 6.0),
        ("Tall", [MockAtom(0, 0), MockAtom(0.1, 10), MockAtom(0, 5)], 6.0),
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for ax, (title, atoms, radius) in zip(axes, test_cases):
        reg = MockRegister(atoms, radius)
        plot_register(reg, blockade_radius=radius, atom_size=300, ax=ax, title=title)
    
    save_path = os.path.join(output_dir, "circular_atoms_verification.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify all axes have equal aspect ratio
    for ax in axes:
        aspect = ax.get_aspect()
        assert aspect == 'equal' or np.isclose(aspect, 1.0)


def test_plot_register_label_positioning(output_dir):
    """Test that labels don't overlap with atoms or axis ticks."""
    # Create atoms at various positions including near origin
    atoms = [
        MockAtom(0.0, 0.0),
        MockAtom(1.0, 0.0),
        MockAtom(0.0, 1.0),
        MockAtom(-1.0, 0.0),
        MockAtom(0.0, -1.0),
    ]
    reg = MockRegister(atoms, blockade_radius=2.0)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(reg, blockade_radius=2.0, atom_size=200, ax=ax,
                 title="Label Positioning Test")
    
    save_path = os.path.join(output_dir, "label_positioning.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# Blockade Disk Rendering Tests
# ============================================================================

@pytest.fixture
def two_atom_register():
    """Create a simple 2-atom register for basic disk testing."""
    atoms = [
        MockAtom(0.0, 0.0),
        MockAtom(5.0, 0.0),
    ]
    return MockRegister(atoms, blockade_radius=4.0)


@pytest.fixture
def overlapping_disks_register():
    """Create register where blockade disks overlap significantly."""
    atoms = [
        MockAtom(0.0, 0.0),
        MockAtom(3.0, 0.0),
        MockAtom(1.5, 2.6),
    ]
    return MockRegister(atoms, blockade_radius=4.0)


def test_blockade_disks_basic_rendering(output_dir, two_atom_register):
    """Test basic blockade disk rendering with visible circles."""
    from matplotlib.patches import Circle
    
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_register(two_atom_register, blockade_radius=4.0, 
                 show_blockade_disks=True, disk_alpha=0.2,
                 ax=ax, title="Basic Blockade Disks")
    
    save_path = os.path.join(output_dir, "blockade_disks_basic.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify that circles were added to the axes
    circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
    assert len(circles) == 2, f"Expected 2 circles, got {len(circles)}"
    
    # Verify circle properties
    for circle in circles:
        assert np.isclose(circle.get_radius(), 4.0), "Circle radius mismatch"
        assert circle.get_alpha() == 0.2, "Circle alpha mismatch"


def test_blockade_disks_overlap_visualization(output_dir, overlapping_disks_register):
    """Test blockade disk overlap visualization (alpha blending)."""
    from matplotlib.patches import Circle
    
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(overlapping_disks_register, blockade_radius=4.0, 
                 show_blockade_disks=True, disk_alpha=0.15,
                 ax=ax, title="Overlapping Blockade Disks")
    
    save_path = os.path.join(output_dir, "blockade_disks_overlap.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify circles exist
    circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
    assert len(circles) == 3, f"Expected 3 circles, got {len(circles)}"


def test_blockade_disks_with_different_alphas(output_dir, two_atom_register):
    """Test blockade disks with various alpha values."""
    from matplotlib.patches import Circle
    
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    
    alphas = [0.05, 0.1, 0.2, 0.4]
    titles = [f"Alpha={alpha}" for alpha in alphas]
    
    for ax, alpha, title in zip(axes, alphas, titles):
        plot_register(two_atom_register, blockade_radius=4.0, 
                     show_blockade_disks=True, disk_alpha=alpha,
                     ax=ax, title=title)
    
    save_path = os.path.join(output_dir, "blockade_disks_alpha_comparison.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify each subplot has correct alpha
    for ax, expected_alpha in zip(axes, alphas):
        circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
        assert len(circles) == 2
        for circle in circles:
            assert circle.get_alpha() == expected_alpha


def test_blockade_disks_chain_layout(output_dir, chain_register):
    """Test blockade disks in chain layout with multiple overlaps."""
    from matplotlib.patches import Circle
    
    fig, ax = plt.subplots(figsize=(16, 5))
    plot_register(chain_register, blockade_radius=5.0, 
                 show_blockade_disks=True, disk_alpha=0.1,
                 ax=ax, title="Chain Layout with Blockade Disks")
    
    save_path = os.path.join(output_dir, "blockade_disks_chain.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify all 5 circles are present
    circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
    assert len(circles) == 5, f"Expected 5 circles, got {len(circles)}"


def test_blockade_disks_with_edges_and_labels(output_dir, overlapping_disks_register):
    """Test blockade disks combined with edges and labels."""
    from matplotlib.patches import Circle
    
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(overlapping_disks_register, blockade_radius=4.0, 
                 show_blockade_disks=True, disk_alpha=0.1,
                 edges=True, labels=True,
                 ax=ax, title="Disks + Edges + Labels")
    
    save_path = os.path.join(output_dir, "blockade_disks_combined.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify both circles and lines exist
    circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
    lines = [line for line in ax.lines if len(line.get_xdata()) == 2]
    
    assert len(circles) == 3, "Missing blockade disks"
    assert len(lines) > 0, "Missing blockade edges"


def test_blockade_disks_disabled_by_default(output_dir, two_atom_register):
    """Test that blockade disks are not shown by default."""
    from matplotlib.patches import Circle
    
    fig, ax = plt.subplots(figsize=(8, 6))
    plot_register(two_atom_register, blockade_radius=4.0, ax=ax)
    
    save_path = os.path.join(output_dir, "blockade_disks_disabled.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify no circles were added
    circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
    assert len(circles) == 0, "Circles should not be rendered by default"


def test_blockade_disks_highlight_atoms(output_dir, overlapping_disks_register):
    """Test blockade disks with highlighted atoms (different colors)."""
    from matplotlib.patches import Circle
    
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(overlapping_disks_register, blockade_radius=4.0, 
                 show_blockade_disks=True, disk_alpha=0.15,
                 highlight_atoms=[0, 2], highlight_color='red',
                 ax=ax, title="Highlighted Atoms with Disks")
    
    save_path = os.path.join(output_dir, "blockade_disks_highlighted.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify circles have correct colors matching atom colors
    circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
    assert len(circles) == 3
    
    # Check that highlighted atoms have red disks (approximate color check)
    # get_facecolor() returns RGBA tuple, access directly
    highlighted_circles = []
    for c in circles:
        facecolor = c.get_facecolor()
        # Handle both tuple and array formats
        if hasattr(facecolor, '__iter__') and len(facecolor) >= 2:
            r, g = facecolor[0], facecolor[1]
            if r > 0.9 and g < 0.1:
                highlighted_circles.append(c)
    
    assert len(highlighted_circles) == 2, "Highlighted atoms should have red disks"


def test_blockade_disks_custom_atom_sizes(output_dir, two_atom_register):
    """Test blockade disks with different atom sizes."""
    from matplotlib.patches import Circle
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    sizes = [50, 200, 500]
    titles = ["Small atoms", "Medium atoms", "Large atoms"]
    
    for ax, size, title in zip(axes, sizes, titles):
        plot_register(two_atom_register, blockade_radius=4.0, 
                     show_blockade_disks=True, disk_alpha=0.15,
                     atom_size=size, ax=ax, title=title)
    
    save_path = os.path.join(output_dir, "blockade_disks_atom_sizes.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify circles are independent of atom size
    for ax in axes:
        circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
        assert len(circles) == 2
        for circle in circles:
            assert np.isclose(circle.get_radius(), 4.0)


def test_blockade_disks_zorder_verification(output_dir, overlapping_disks_register):
    """Test that disks are rendered below atoms (zorder)."""
    from matplotlib.patches import Circle
    
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(overlapping_disks_register, blockade_radius=4.0, 
                 show_blockade_disks=True, disk_alpha=0.3,
                 ax=ax, title="Z-order Verification")
    
    save_path = os.path.join(output_dir, "blockade_disks_zorder.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify zorder of circles is lower than scatter points
    circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
    assert len(circles) == 3
    
    for circle in circles:
        assert circle.get_zorder() == 0, "Disks should have zorder=0"


def test_blockade_disks_geometry_accuracy(output_dir):
    """Test that blockade disks are perfect circles with correct radius."""
    from matplotlib.patches import Circle
    
    # Create atoms at known positions
    atoms = [
        MockAtom(0.0, 0.0),
        MockAtom(10.0, 0.0),
    ]
    reg = MockRegister(atoms, blockade_radius=3.0)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    plot_register(reg, blockade_radius=3.0, 
                 show_blockade_disks=True, disk_alpha=0.2,
                 ax=ax, title="Geometry Accuracy Test")
    
    save_path = os.path.join(output_dir, "blockade_disks_geometry.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    
    # Verify circle centers and radii
    circles = [patch for patch in ax.patches if isinstance(patch, Circle)]
    assert len(circles) == 2
    
    # Check first circle at origin
    assert np.isclose(circles[0].get_center()[0], 0.0)
    assert np.isclose(circles[0].get_center()[1], 0.0)
    assert np.isclose(circles[0].get_radius(), 3.0)
    
    # Check second circle at (10, 0)
    assert np.isclose(circles[1].get_center()[0], 10.0)
    assert np.isclose(circles[1].get_center()[1], 0.0)
    assert np.isclose(circles[1].get_radius(), 3.0)


def test_blockade_disks_large_register(output_dir):
    """Test blockade disks with a larger register (performance test)."""
    # Create a 5x5 grid
    atoms = []
    for i in range(5):
        for j in range(5):
            atoms.append(MockAtom(i * 3.0, j * 3.0))
    
    reg = MockRegister(atoms, blockade_radius=4.0)
    
    fig, ax = plt.subplots(figsize=(12, 12))
    plot_register(reg, blockade_radius=4.0, show_blockade_disks=True, 
                 disk_alpha=0.1, atom_size=80, ax=ax, title="Large Register with Disks")
    
    save_path = os.path.join(output_dir, "blockade_disks_large.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# Bitstring Overlay Tests
# ============================================================================

def test_plot_register_with_bitstring(output_dir, simple_register):
    """Test register plotting with bitstring overlay."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, 
                 bitstring="101", ax=ax, title="Bitstring Overlay: 101")
    
    save_path = os.path.join(output_dir, "register_bitstring.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_bitstring_custom_colors(output_dir, simple_register):
    """Test bitstring overlay with custom colors."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, 
                 bitstring="010",
                 excited_state_color='red',
                 ground_state_color='lightblue',
                 ax=ax, title="Custom Colors")
    
    save_path = os.path.join(output_dir, "register_bitstring_colors.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_bitstring_length_mismatch_raises(simple_register):
    """Test that bitstring length mismatch raises ValueError."""
    with pytest.raises(ValueError, match="does not match"):
        plot_register(simple_register, bitstring="1010")  # 4 bits but 3 atoms


def test_plot_register_bitstring_invalid_characters_raises(simple_register):
    """Test that invalid bitstring characters raise ValueError."""
    with pytest.raises(ValueError, match="only '0' and '1'"):
        plot_register(simple_register, bitstring="10a")


def test_plot_register_bitstring_all_excited(output_dir):
    """Test bitstring with all atoms excited."""
    atoms = [MockAtom(i * 3.0, 0.0) for i in range(4)]
    reg = MockRegister(atoms, blockade_radius=4.0)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_register(reg, blockade_radius=4.0, bitstring="1111", ax=ax,
                 title="All Excited States")
    
    save_path = os.path.join(output_dir, "bitstring_all_excited.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_bitstring_alternating(output_dir):
    """Test alternating bitstring pattern."""
    atoms = [MockAtom(i * 3.0, 0.0) for i in range(6)]
    reg = MockRegister(atoms, blockade_radius=4.0)
    
    fig, ax = plt.subplots(figsize=(14, 6))
    plot_register(reg, blockade_radius=4.0, bitstring="101010", ax=ax,
                 title="Alternating Pattern: 101010")
    
    save_path = os.path.join(output_dir, "bitstring_alternating.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_bitstring_with_edges_and_disks(output_dir, simple_register):
    """Test bitstring overlay combined with edges and blockade disks."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, 
                 bitstring="101",
                 edges=True,
                 show_blockade_disks=True,
                 disk_alpha=0.15,
                 ax=ax, title="Bitstring + Edges + Disks")
    
    save_path = os.path.join(output_dir, "bitstring_combined.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_bitstring_title_auto_generation(output_dir, simple_register):
    """Test that title is auto-generated with bitstring info."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, 
                 bitstring="110", ax=ax)
    
    # Verify title contains bitstring information
    title = ax.get_title()
    assert "110" in title
    assert "excited" in title.lower()
    
    save_path = os.path.join(output_dir, "bitstring_auto_title.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_bitstring_legend(output_dir, simple_register):
    """Test that legend shows ground/excited state labels."""
    fig, ax = plt.subplots(figsize=(8, 8))
    plot_register(simple_register, blockade_radius=4.0, 
                 bitstring="101", ax=ax)
    
    # Verify legend exists
    legend = ax.get_legend()
    assert legend is not None
    
    # Check legend text
    texts = [t.get_text() for t in legend.get_texts()]
    assert any("Ground" in t or "0" in t for t in texts)
    assert any("Excited" in t or "1" in t for t in texts)
    
    save_path = os.path.join(output_dir, "bitstring_legend.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_register_bitstring_overrides_highlight_atoms(output_dir, simple_register):
    """Test that bitstring parameter overrides highlight_atoms."""
    fig, ax = plt.subplots(figsize=(8, 8))
    # Both parameters provided - bitstring should take precedence
    plot_register(simple_register, blockade_radius=4.0, 
                 bitstring="101",
                 highlight_atoms=[0],  # This should be ignored
                 ax=ax, title="Bitstring Overrides Highlight")
    
    save_path = os.path.join(output_dir, "bitstring_override.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
