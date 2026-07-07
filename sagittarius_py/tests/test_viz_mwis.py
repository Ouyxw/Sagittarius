"""
MWIS visualization tests.

Tests for plot_mwis_problem(), plot_mwis_comparison(), and annotate_solution_quality() functions.
All tests save generated images to test_figs/ directory.
"""

import os
import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sagittarius.viz import plot_mwis_problem, plot_mwis_comparison, annotate_solution_quality


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
    """Create a simple 4-atom register for MWIS testing."""
    atoms = [
        MockAtom(0.0, 0.0),
        MockAtom(3.0, 0.0),
        MockAtom(1.5, 2.6),
        MockAtom(4.5, 2.6),
    ]
    return MockRegister(atoms, blockade_radius=4.0)


@pytest.fixture
def chain_register():
    """Create a linear chain register."""
    atoms = [MockAtom(i * 4.0, 0.0) for i in range(5)]
    return MockRegister(atoms, blockade_radius=5.0)


@pytest.fixture
def sample_weights():
    """Sample weights for MWIS problem."""
    return [1.2, 0.8, 1.5, 0.9]


@pytest.fixture
def sample_edges():
    """Sample edges for Unit-Disk Graph."""
    return [(0, 1), (1, 2), (2, 3), (0, 2)]


# ============================================================================
# Basic Functionality Tests
# ============================================================================

def test_plot_mwis_basic(output_dir, simple_register, sample_weights, sample_edges):
    """Test basic MWIS problem visualization."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        ax=ax,
        title="Basic MWIS Visualization"
    )
    
    save_path = os.path.join(output_dir, "mwis_basic.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    aspect = ax.get_aspect()
    assert aspect == 'equal' or np.isclose(aspect, 1.0)


def test_plot_mwis_without_weights(output_dir, simple_register, sample_edges):
    """Test MWIS visualization without weights."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        edges=sample_edges,
        show_weights=False,
        ax=ax,
        title="Without Weights"
    )
    
    save_path = os.path.join(output_dir, "mwis_no_weights.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_mwis_auto_edges(output_dir, simple_register):
    """Test MWIS visualization with auto-derived edges from blockade_radius."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        blockade_radius=4.0,
        ax=ax,
        title="Auto-derived Edges"
    )
    
    save_path = os.path.join(output_dir, "mwis_auto_edges.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_mwis_conflicts_highlighted(output_dir, simple_register, sample_weights, sample_edges):
    """Test conflict highlighting when adjacent atoms are both excited."""
    # Create a bitstring with conflicts: atoms 0 and 1 are both '1' and connected
    bitstring_with_conflict = "1100"
    
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring=bitstring_with_conflict,
        weights=sample_weights,
        edges=sample_edges,
        highlight_conflicts=True,
        ax=ax,
        title="With Conflict Markers"
    )
    
    save_path = os.path.join(output_dir, "mwis_conflicts.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_mwis_no_conflicts(output_dir, simple_register, sample_weights, sample_edges):
    """Test valid independent set with no conflicts."""
    # Valid IS: no two adjacent atoms are both '1'
    valid_bitstring = "1010"
    
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring=valid_bitstring,
        weights=sample_weights,
        edges=sample_edges,
        highlight_conflicts=True,
        ax=ax,
        title="Valid Independent Set"
    )
    
    save_path = os.path.join(output_dir, "mwis_valid_is.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# Validation Tests
# ============================================================================

def test_mwis_bitstring_length_mismatch_raises(simple_register, sample_edges):
    """Test that bitstring length mismatch raises ValueError."""
    with pytest.raises(ValueError, match="does not match"):
        plot_mwis_problem(simple_register, bitstring="10101")  # 5 bits but 4 atoms


def test_mwis_bitstring_invalid_characters_raises(simple_register, sample_edges):
    """Test that invalid bitstring characters raise ValueError."""
    with pytest.raises(ValueError, match="only '0' and '1'"):
        plot_mwis_problem(simple_register, bitstring="10a0")


def test_mwis_weights_length_mismatch_raises(simple_register, sample_edges):
    """Test that weights length mismatch raises ValueError."""
    with pytest.raises(ValueError, match="does not match"):
        plot_mwis_problem(
            simple_register,
            bitstring="1010",
            weights=[1.0, 2.0, 3.0]  # 3 weights but 4 atoms
        )


def test_mwis_empty_register_raises():
    """Test that empty register raises ValueError."""
    empty_reg = MockRegister([])
    
    with pytest.raises(ValueError):
        plot_mwis_problem(empty_reg, bitstring="")


# ============================================================================
# Visual Customization Tests
# ============================================================================

def test_mwis_custom_colors(output_dir, simple_register, sample_edges):
    """Test custom colors for conflicts and edges."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1100",
        edges=sample_edges,
        conflict_color='purple',
        edge_color='blue',
        ax=ax,
        title="Custom Colors"
    )
    
    save_path = os.path.join(output_dir, "mwis_custom_colors.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_weight_fontsize(output_dir, simple_register, sample_weights, sample_edges):
    """Test different weight font sizes."""
    fig, axes = plt.subplots(1, 3, figsize=(24, 8))
    
    fontsizes = [6, 10, 14]
    titles = ["Small font", "Medium font", "Large font"]
    
    for ax, fontsize, title in zip(axes, fontsizes, titles):
        plot_mwis_problem(
            simple_register,
            bitstring="1010",
            weights=sample_weights,
            edges=sample_edges,
            weight_fontsize=fontsize,
            ax=ax,
            title=title
        )
    
    save_path = os.path.join(output_dir, "mwis_weight_fontsizes.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_hide_edges(output_dir, simple_register, sample_weights, sample_edges):
    """Test hiding graph edges."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        show_edges=False,
        ax=ax,
        title="Edges Hidden"
    )
    
    save_path = os.path.join(output_dir, "mwis_no_edges.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_hide_conflicts(output_dir, simple_register, sample_edges):
    """Test hiding conflict markers."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1100",
        edges=sample_edges,
        highlight_conflicts=False,
        ax=ax,
        title="Conflicts Hidden"
    )
    
    save_path = os.path.join(output_dir, "mwis_no_conflicts_marker.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# Comparison Plot Tests
# ============================================================================

def test_plot_mwis_comparison_two_solutions(output_dir, simple_register, sample_weights, sample_edges):
    """Test comparing two solutions side-by-side."""
    bitstrings = ["1010", "0101"]
    titles = ["Solution A", "Solution B"]
    
    axes = plot_mwis_comparison(
        simple_register,
        bitstrings=bitstrings,
        titles=titles,
        weights=sample_weights,
        edges=sample_edges,
        figsize=(16, 8)
    )
    
    save_path = os.path.join(output_dir, "mwis_comparison_2.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(axes) == 2


def test_plot_mwis_comparison_three_solutions(output_dir, chain_register):
    """Test comparing three solutions."""
    bitstrings = ["10101", "01010", "10001"]
    weights = [1.0, 1.2, 0.8, 1.5, 0.9]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    
    axes = plot_mwis_comparison(
        chain_register,
        bitstrings=bitstrings,
        weights=weights,
        edges=edges,
        blockade_radius=5.0,
        figsize=(24, 8)
    )
    
    save_path = os.path.join(output_dir, "mwis_comparison_3.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(axes) == 3


def test_plot_mwis_comparison_titles_mismatch_raises(simple_register):
    """Test that title count mismatch raises ValueError."""
    with pytest.raises(ValueError, match="doesn't match"):
        plot_mwis_comparison(
            simple_register,
            bitstrings=["1010", "0101"],
            titles=["Only one title"]  # 1 title but 2 bitstrings
        )


def test_plot_mwis_comparison_single_solution(output_dir, simple_register, sample_weights, sample_edges):
    """Test comparison with single solution (edge case)."""
    axes = plot_mwis_comparison(
        simple_register,
        bitstrings=["1010"],
        weights=sample_weights,
        edges=sample_edges,
        figsize=(10, 8)
    )
    
    save_path = os.path.join(output_dir, "mwis_comparison_single.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(axes) == 1


# ============================================================================
# Annotation Tests
# ============================================================================

def test_annotate_solution_quality_valid(output_dir, simple_register, sample_weights, sample_edges):
    """Test annotation on valid solution."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        ax=ax
    )
    
    annotate_solution_quality(
        ax,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges
    )
    
    save_path = os.path.join(output_dir, "mwis_annotation_valid.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_annotate_solution_quality_with_conflicts(output_dir, simple_register, sample_weights, sample_edges):
    """Test annotation on solution with conflicts."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1100",
        weights=sample_weights,
        edges=sample_edges,
        ax=ax
    )
    
    annotate_solution_quality(
        ax,
        bitstring="1100",
        weights=sample_weights,
        edges=sample_edges
    )
    
    save_path = os.path.join(output_dir, "mwis_annotation_conflicts.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_annotate_solution_quality_no_weights(output_dir, simple_register, sample_edges):
    """Test annotation without weights."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        edges=sample_edges,
        ax=ax
    )
    
    annotate_solution_quality(
        ax,
        bitstring="1010",
        edges=sample_edges
    )
    
    save_path = os.path.join(output_dir, "mwis_annotation_no_weights.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_annotate_custom_position(output_dir, simple_register, sample_weights, sample_edges):
    """Test annotation at custom position."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        ax=ax
    )
    
    annotate_solution_quality(
        ax,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        text_position=(0.65, 0.95),
        fontsize=12
    )
    
    save_path = os.path.join(output_dir, "mwis_annotation_custom_pos.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# Integration Tests
# ============================================================================

def test_mwis_chain_layout(output_dir, chain_register):
    """Test MWIS visualization on chain layout."""
    weights = [1.0, 1.2, 0.8, 1.5, 0.9]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4)]
    bitstring = "10101"
    
    fig, ax = plt.subplots(figsize=(16, 6))
    plot_mwis_problem(
        chain_register,
        bitstring=bitstring,
        weights=weights,
        edges=edges,
        blockade_radius=5.0,
        ax=ax,
        title="Chain Layout MWIS"
    )
    
    save_path = os.path.join(output_dir, "mwis_chain.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_large_grid(output_dir):
    """Test MWIS visualization on larger grid layout."""
    # Create 4x4 grid
    atoms = []
    for i in range(4):
        for j in range(4):
            atoms.append(MockAtom(i * 3.0, j * 3.0))
    
    reg = MockRegister(atoms, blockade_radius=4.0)
    
    # Generate random-like bitstring
    bitstring = "1010010110100101"
    weights = [round(0.5 + np.random.rand() * 1.5, 2) for _ in range(16)]
    
    # Derive edges from blockade radius
    edges = []
    pos_array = np.array([[a.x, a.y] for a in atoms])
    for i in range(16):
        for j in range(i+1, 16):
            dist = np.sqrt((pos_array[i, 0] - pos_array[j, 0])**2 + 
                          (pos_array[i, 1] - pos_array[j, 1])**2)
            if dist <= 4.0:
                edges.append((i, j))
    
    fig, ax = plt.subplots(figsize=(14, 14))
    plot_mwis_problem(
        reg,
        bitstring=bitstring,
        weights=weights,
        edges=edges,
        ax=ax,
        title="4x4 Grid MWIS Problem"
    )
    
    save_path = os.path.join(output_dir, "mwis_large_grid.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_all_ground_state(output_dir, simple_register, sample_weights, sample_edges):
    """Test visualization when all atoms are in ground state."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="0000",
        weights=sample_weights,
        edges=sample_edges,
        ax=ax,
        title="All Ground State"
    )
    
    save_path = os.path.join(output_dir, "mwis_all_ground.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_all_excited_with_conflicts(output_dir, simple_register, sample_weights, sample_edges):
    """Test visualization when all atoms are excited (many conflicts)."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1111",
        weights=sample_weights,
        edges=sample_edges,
        ax=ax,
        title="All Excited (Many Conflicts)"
    )
    
    save_path = os.path.join(output_dir, "mwis_all_excited.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_legend_elements(output_dir, simple_register, sample_edges):
    """Test that legend contains all expected elements."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1100",
        edges=sample_edges,
        ax=ax
    )
    
    # Verify legend exists
    legend = ax.get_legend()
    assert legend is not None
    
    # Check legend text content
    texts = [t.get_text() for t in legend.get_texts()]
    assert any("Ground" in t or "0" in t for t in texts)
    assert any("Excited" in t or "1" in t for t in texts)
    assert any("violation" in t.lower() or "conflict" in t.lower() for t in texts)
    assert any("edge" in t.lower() for t in texts)
    
    save_path = os.path.join(output_dir, "mwis_legend.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_title_auto_generation(output_dir, simple_register, sample_weights, sample_edges):
    """Test automatic title generation with solution statistics."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        ax=ax
    )
    
    # Verify title contains key information
    title = ax.get_title()
    # New format includes atom count and either "selected" or "conflicts"
    assert "atoms" in title.lower() and ("selected" in title.lower() or "conflicts" in title.lower())
    
    save_path = os.path.join(output_dir, "mwis_auto_title.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_mwis_combined_features(output_dir, simple_register, sample_weights, sample_edges):
    """Test comprehensive feature combination."""
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Plot with all features enabled
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        show_weights=True,
        show_edges=True,
        highlight_conflicts=True,
        ax=ax,
        title="Full Feature Test"
    )
    
    # Add annotation
    annotate_solution_quality(
        ax,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        text_position=(0.02, 0.95)
    )
    
    save_path = os.path.join(output_dir, "mwis_full_features.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


# ============================================================================
# Phase 16 Benchmark Integration Tests
# ============================================================================

def test_plot_mwis_with_algorithm_name(output_dir, simple_register, sample_weights, sample_edges):
    """Test MWIS visualization with algorithm name embedding."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        algorithm_name="AQC",
        performance_metrics={"tts": 2.35, "p_success": 0.85},
        ax=ax
    )
    
    save_path = os.path.join(output_dir, "mwis_with_algorithm.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    # Check title contains algorithm name
    title = ax.get_title()
    assert "AQC" in title


def test_plot_mwis_with_artifact_id(output_dir, simple_register, sample_weights, sample_edges):
    """Test MWIS visualization with artifact ID tracking."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        artifact_id="mwis-bench-n4-d0.5-seed42",
        ax=ax
    )
    
    save_path = os.path.join(output_dir, "mwis_with_artifact.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    # Check title contains artifact ID
    title = ax.get_title()
    assert "Artifact:" in title or "mwis-bench" in title


def test_plot_mwis_comparison_with_metadata(output_dir, simple_register, sample_weights, sample_edges):
    """Test comparison plot with algorithm names and performance metrics."""
    bitstrings = ["1010", "0101", "1001"]
    algorithm_names = ["AQC", "Greedy", "SA"]
    perf_metrics = [
        {"tts": 2.35, "p_success": 0.85},
        {"ratio": 0.92, "runtime": 0.01},
        {"tts": 1.80, "p_success": 0.78}
    ]
    artifact_ids = ["mwis-aqc", "mwis-greedy", "mwis-sa"]
    
    axes = plot_mwis_comparison(
        simple_register,
        bitstrings=bitstrings,
        algorithm_names=algorithm_names,
        performance_metrics_list=perf_metrics,
        artifact_ids=artifact_ids,
        weights=sample_weights,
        edges=sample_edges,
        figsize=(24, 8)
    )
    
    save_path = os.path.join(output_dir, "mwis_comparison_metadata.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(axes) == 3
    
    # Verify each subplot has correct algorithm name in title
    for ax, algo_name in zip(axes, algorithm_names):
        title = ax.get_title()
        assert algo_name in title


def test_annotate_with_approximation_ratio(output_dir, simple_register, sample_weights, sample_edges):
    """Test annotation with approximation ratio calculation."""
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        ax=ax
    )
    
    # Annotate with optimal weight
    optimal_weight = 2.7  # Sum of all weights if all could be selected
    annotate_solution_quality(
        ax,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        include_approximation_ratio=True,
        optimal_weight=optimal_weight
    )
    
    save_path = os.path.join(output_dir, "mwis_annotation_approx_ratio.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_save_mwis_benchmark_figure(output_dir, simple_register, sample_weights, sample_edges):
    """Test saving benchmark figure with metadata sidecar."""
    from sagittarius.viz import save_mwis_benchmark_figure
    
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_mwis_problem(
        simple_register,
        bitstring="1010",
        weights=sample_weights,
        edges=sample_edges,
        algorithm_name="AQC",
        performance_metrics={"tts": 2.35, "p_success": 0.85},
        artifact_id="test-artifact-001",
        ax=ax
    )
    
    # Define benchmark metadata
    metadata = {
        "artifact_id": "test-artifact-001",
        "schema_version": "benchmark-artifact/v1",
        "algorithm": "AQC",
        "n_atoms": 4,
        "density": 0.5,
        "seed": 42,
        "weights_mode": "random",
        "solution_weight": sum([w for i, w in enumerate(sample_weights) if "1010"[i] == '1']),
        "conflicts": 0,
        "backend": "CPU",
        "solver_method": "Tsit5",
        "performance": {"tts": 2.35, "p_success": 0.85, "runtime": 1.2},
        "commit_sha": "test-commit-abc123"
    }
    
    output_path = os.path.join(output_dir, "mwis_benchmark_test.png")
    save_mwis_benchmark_figure(fig, output_path, metadata, dpi=150)
    
    # Check both files exist
    assert os.path.exists(output_path)
    assert os.path.exists(output_path.replace('.png', '.json'))
    
    # Verify JSON content
    import json
    json_path = output_path.replace('.png', '.json')
    with open(json_path, 'r') as f:
        saved_metadata = json.load(f)
    
    assert saved_metadata['artifact_id'] == "test-artifact-001"
    assert saved_metadata['algorithm'] == "AQC"
    assert 'visualization_saved_at' in saved_metadata


def test_plot_mwis_comparison_metadata_validation(output_dir, simple_register, sample_weights, sample_edges):
    """Test validation of metadata lists in comparison plot."""
    bitstrings = ["1010", "0101"]
    
    # Test mismatched algorithm_names length
    with pytest.raises(ValueError, match="algorithm_names length"):
        plot_mwis_comparison(
            simple_register,
            bitstrings=bitstrings,
            algorithm_names=["AQC"],  # Only 1 name for 2 solutions
            weights=sample_weights,
            edges=sample_edges
        )
    
    # Test mismatched performance_metrics_list length
    with pytest.raises(ValueError, match="performance_metrics_list length"):
        plot_mwis_comparison(
            simple_register,
            bitstrings=bitstrings,
            performance_metrics_list=[{"tts": 2.35}],  # Only 1 metric dict
            weights=sample_weights,
            edges=sample_edges
        )
    
    # Test mismatched artifact_ids length
    with pytest.raises(ValueError, match="artifact_ids length"):
        plot_mwis_comparison(
            simple_register,
            bitstrings=bitstrings,
            artifact_ids=["id1"],  # Only 1 ID
            weights=sample_weights,
            edges=sample_edges
        )


def test_benchmark_workflow_integration(output_dir, chain_register):
    """Test complete benchmark workflow integration."""
    from sagittarius.viz import save_mwis_benchmark_figure
    
    # Simulate benchmark case: N=5, density=0.5, seed=42
    n_atoms = 5
    weights = [1.0 + 0.1*i for i in range(n_atoms)]
    edges = [(i, i+1) for i in range(n_atoms-1)]  # Linear chain
    
    # Multiple algorithm solutions
    solutions = {
        "AQC": ("10101", {"tts": 3.45, "p_success": 0.92, "runtime": 2.5}),
        "Greedy": ("10100", {"ratio": 0.85, "runtime": 0.001}),
        "Optimal": ("10101", {"weight": 3.0, "runtime": 0.5})
    }
    
    # Create comparison figure
    bitstrings = [sol[0] for sol in solutions.values()]
    algo_names = list(solutions.keys())
    perf_metrics = [sol[1] for sol in solutions.values()]
    artifact_ids = [f"mwis-{algo.lower()}-n{n_atoms}" for algo in algo_names]
    
    axes = plot_mwis_comparison(
        chain_register,
        bitstrings=bitstrings,
        algorithm_names=algo_names,
        performance_metrics_list=perf_metrics,
        artifact_ids=artifact_ids,
        weights=weights,
        edges=edges,
        blockade_radius=5.0,
        figsize=(24, 8)
    )
    
    # Add quality annotations to each subplot
    for ax, (algo, (bs, _)) in zip(axes, solutions.items()):
        annotate_solution_quality(ax, bs, weights, edges)
    
    # Save with comprehensive metadata
    fig = plt.gcf()
    metadata = {
        "artifact_id": "mwis-benchmark-chain-n5",
        "schema_version": "benchmark-artifact/v1",
        "n_atoms": n_atoms,
        "geometry": "chain",
        "density": 0.5,
        "seed": 42,
        "algorithms_compared": algo_names,
        "solutions": {
            algo: {"bitstring": bs, "metrics": metrics}
            for algo, (bs, metrics) in solutions.items()
        },
        "timestamp": "2026-07-07T01:00:00Z",
        "commit_sha": "benchmark-test-sha"
    }
    
    output_path = os.path.join(output_dir, "mwis_benchmark_workflow.png")
    save_mwis_benchmark_figure(fig, output_path, metadata, dpi=150)
    
    assert os.path.exists(output_path)
    assert os.path.exists(output_path.replace('.png', '.json'))
    
    plt.close()
