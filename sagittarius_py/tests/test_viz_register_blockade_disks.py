"""
Test register visualization with blockade disk rendering.

Tests for show_blockade_disks parameter in plot_register().
"""

import pytest
import numpy as np
import matplotlib.pyplot as plt

@pytest.fixture(autouse=True)
def cleanup_matplotlib_figures():
    """Automatically close all figures after each test to prevent memory warnings."""
    yield
    plt.close('all')
from matplotlib.patches import Circle
from sagittarius.viz import plot_register


class MockAtom:
    """Mock atom object with x, y coordinates."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


class MockRegister:
    """Mock register object with atoms list."""
    def __init__(self, atoms, blockade_radius=None):
        self.atoms = atoms
        self.blockade_radius = blockade_radius


def test_plot_register_with_blockade_disks():
    """Test that blockade disks are rendered when enabled."""
    # Create a simple 3-atom register
    atoms = [MockAtom(0, 0), MockAtom(5, 0), MockAtom(2.5, 4)]
    reg = MockRegister(atoms, blockade_radius=6.0)
    
    fig, ax = plt.subplots()
    result_ax = plot_register(reg, blockade_radius=6.0, show_blockade_disks=True, ax=ax)
    
    # Check that circles were added to the axes
    patches = [p for p in ax.patches if isinstance(p, Circle)]
    assert len(patches) == 3, f"Expected 3 blockade disks, got {len(patches)}"
    
    # Verify circle properties
    for i, circle in enumerate(patches):
        assert circle.radius == 6.0, f"Circle {i} radius mismatch"
        center = circle.center
        assert np.isclose(center[0], atoms[i].x, atol=0.01)
        assert np.isclose(center[1], atoms[i].y, atol=0.01)
    
    plt.close(fig)


def test_plot_register_without_blockade_disks():
    """Test that blockade disks are not rendered when disabled."""
    atoms = [MockAtom(0, 0), MockAtom(5, 0)]
    reg = MockRegister(atoms, blockade_radius=6.0)
    
    fig, ax = plt.subplots()
    result_ax = plot_register(reg, blockade_radius=6.0, show_blockade_disks=False, ax=ax)
    
    # No circles should be present
    patches = [p for p in ax.patches if isinstance(p, Circle)]
    assert len(patches) == 0, f"Expected no blockade disks, got {len(patches)}"
    
    plt.close(fig)


def test_plot_register_blockade_disks_custom_alpha():
    """Test blockade disks with custom transparency."""
    atoms = [MockAtom(0, 0)]
    reg = MockRegister(atoms, blockade_radius=5.0)
    
    fig, ax = plt.subplots()
    result_ax = plot_register(
        reg, 
        blockade_radius=5.0, 
        show_blockade_disks=True, 
        disk_alpha=0.3,
        ax=ax
    )
    
    patches = [p for p in ax.patches if isinstance(p, Circle)]
    assert len(patches) == 1
    assert np.isclose(patches[0].get_alpha(), 0.3, atol=0.01)
    
    plt.close(fig)


def test_plot_register_blockade_disks_with_highlight():
    """Test that highlighted atoms have matching disk colors."""
    atoms = [MockAtom(0, 0), MockAtom(5, 0), MockAtom(10, 0)]
    reg = MockRegister(atoms, blockade_radius=6.0)
    
    fig, ax = plt.subplots()
    result_ax = plot_register(
        reg, 
        blockade_radius=6.0, 
        show_blockade_disks=True,
        highlight_atoms=[1],
        highlight_color='red',
        ax=ax
    )
    
    patches = [p for p in ax.patches if isinstance(p, Circle)]
    assert len(patches) == 3
    
    # Check that highlighted atom has red disk
    highlighted_circle = patches[1]
    facecolor = highlighted_circle.get_facecolor()
    # Red color should have high R component
    assert facecolor[0] > 0.5, "Highlighted atom disk should be red"
    
    plt.close(fig)


def test_plot_register_no_blockade_radius_no_disks():
    """Test that no disks are drawn when blockade_radius is None."""
    atoms = [MockAtom(0, 0), MockAtom(5, 0)]
    reg = MockRegister(atoms)
    
    fig, ax = plt.subplots()
    result_ax = plot_register(reg, show_blockade_disks=True, ax=ax)
    
    # No circles should be present without blockade_radius
    patches = [p for p in ax.patches if isinstance(p, Circle)]
    assert len(patches) == 0
    
    plt.close(fig)


def test_plot_register_blockade_disks_zorder():
    """Test that blockade disks are behind atoms (lower zorder)."""
    atoms = [MockAtom(0, 0)]
    reg = MockRegister(atoms, blockade_radius=5.0)
    
    fig, ax = plt.subplots()
    result_ax = plot_register(reg, blockade_radius=5.0, show_blockade_disks=True, ax=ax)
    
    patches = [p for p in ax.patches if isinstance(p, Circle)]
    assert len(patches) == 1
    
    # Disk should have zorder=0 (behind atoms which have zorder=5)
    assert patches[0].get_zorder() == 0
    
    plt.close(fig)


def test_plot_register_blockade_disks_different_radii():
    """Test blockade disks with different radii produce different sizes."""
    atoms = [MockAtom(0, 0)]
    reg = MockRegister(atoms)
    
    # Test with small radius
    fig1, ax1 = plt.subplots()
    plot_register(reg, blockade_radius=2.0, show_blockade_disks=True, ax=ax1)
    patches1 = [p for p in ax1.patches if isinstance(p, Circle)]
    radius1 = patches1[0].radius
    
    # Test with large radius
    fig2, ax2 = plt.subplots()
    plot_register(reg, blockade_radius=10.0, show_blockade_disks=True, ax=ax2)
    patches2 = [p for p in ax2.patches if isinstance(p, Circle)]
    radius2 = patches2[0].radius
    
    assert radius2 > radius1, "Larger blockade radius should produce larger disk"
    
    plt.close(fig1)
    plt.close(fig2)


def test_plot_register_integration_edges_and_disks():
    """Test that edges and disks can coexist."""
    atoms = [MockAtom(0, 0), MockAtom(3, 0), MockAtom(6, 0)]
    reg = MockRegister(atoms, blockade_radius=4.0)
    
    fig, ax = plt.subplots()
    result_ax = plot_register(
        reg, 
        blockade_radius=4.0, 
        edges=True,
        show_blockade_disks=True,
        ax=ax
    )
    
    # Should have both disks and edges
    patches = [p for p in ax.patches if isinstance(p, Circle)]
    assert len(patches) == 3, "Should have 3 blockade disks"
    
    # Count lines (edges)
    lines = [l for l in ax.lines if len(l.get_xdata()) == 2]
    assert len(lines) >= 2, "Should have at least 2 edges between nearby atoms"
    
    plt.close(fig)
