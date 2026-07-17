"""
Pulse visualization tests.

Tests for plot_pulse_waveform() function.
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
from sagittarius.viz import plot_pulse_waveform, sample_pulse_waveform


# Mock classes for testing
class MockPulse:
    """Mock Pulse object with omega and delta attributes."""
    def __init__(self, omega, delta, duration):
        self.omega = omega
        self.delta = delta
        self.duration = duration


# Test fixtures
@pytest.fixture
def output_dir():
    """Create output directory for test figures."""
    output_path = os.path.join(os.path.dirname(__file__), 'test_figs')
    os.makedirs(output_path, exist_ok=True)
    return output_path


@pytest.fixture
def constant_pulse():
    """Create a constant pulse."""
    return MockPulse(omega=2.0, delta=0.0, duration=5.0)


@pytest.fixture
def ramp_pulse():
    """Create a ramp pulse."""
    return MockPulse(
        omega=lambda t: 0.6 * t,  # Ramp from 0 to 3 over 5μs
        delta=0.0, 
        duration=5.0
    )


@pytest.fixture
def gaussian_pulse():
    """Create a Gaussian pulse."""
    amplitude = 3.0
    sigma = 1.0
    center = 2.5
    return MockPulse(
        omega=lambda t: amplitude * np.exp(-((t - center)**2) / (2 * sigma**2)),
        delta=0.0,
        duration=5.0
    )


# Tests
def test_plot_pulse_constant_omega(output_dir, constant_pulse):
    """Test plotting constant omega pulse."""
    fig, ax = plt.subplots(figsize=(10, 4))
    
    ax_result, omega_vals = plot_pulse_waveform(
        constant_pulse, 
        field='omega',
        num_samples=100,
        ax=ax,
        title="Constant Omega Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_constant_omega.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert ax_result is not None
    assert len(omega_vals) == 100


def test_plot_pulse_constant_delta(output_dir, constant_pulse):
    """Test plotting constant delta pulse."""
    constant_pulse_with_delta = MockPulse(omega=0.0, delta=1.5, duration=5.0)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    ax_result, delta_vals = plot_pulse_waveform(
        constant_pulse_with_delta, 
        field='delta',
        num_samples=100,
        ax=ax,
        title="Constant Delta Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_constant_delta.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert ax_result is not None
    assert len(delta_vals) == 100


def test_plot_pulse_both_fields(output_dir, constant_pulse):
    """Test plotting both omega and delta pulses."""
    pulse_with_both = MockPulse(omega=2.0, delta=1.5, duration=5.0)
    
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    # Plot omega
    ax_omega, omega_vals = plot_pulse_waveform(
        pulse_with_both, 
        field='omega',
        num_samples=100,
        ax=axes[0],
        title="Omega Pulse"
    )
    
    # Plot delta
    ax_delta, delta_vals = plot_pulse_waveform(
        pulse_with_both, 
        field='delta',
        num_samples=100,
        ax=axes[1],
        title="Delta Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_both_components.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 100
    assert len(delta_vals) == 100


def test_plot_pulse_ramp(output_dir, ramp_pulse):
    """Test plotting ramp pulse."""
    fig, ax = plt.subplots(figsize=(10, 4))
    
    ax_result, omega_vals = plot_pulse_waveform(
        ramp_pulse, 
        field='omega',
        num_samples=100,
        ax=ax,
        title="Ramp Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_ramp.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 100


def test_plot_pulse_gaussian(output_dir, gaussian_pulse):
    """Test plotting Gaussian pulse."""
    fig, ax = plt.subplots(figsize=(10, 4))
    
    ax_result, omega_vals = plot_pulse_waveform(
        gaussian_pulse, 
        field='omega',
        num_samples=200,
        ax=ax,
        title="Gaussian Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_gaussian.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 200


def test_plot_pulse_custom_time_grid(output_dir, constant_pulse):
    """Test plotting with custom time grid."""
    custom_times = np.linspace(0, 10, 150)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    ax_result, omega_vals = plot_pulse_waveform(
        constant_pulse, 
        time_grid=custom_times,
        field='omega',
        ax=ax,
        title="Custom Time Grid"
    )
    
    save_path = os.path.join(output_dir, "pulse_custom_time.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 150


def test_plot_pulse_different_durations(output_dir):
    """Test plotting pulses with different durations."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    durations = [2.0, 5.0, 10.0]
    titles = ["Short (2μs)", "Medium (5μs)", "Long (10μs)"]
    
    for ax, duration, title in zip(axes, durations, titles):
        pulse = MockPulse(omega=2.0, delta=0.0, duration=duration)
        _, omega_vals = plot_pulse_waveform(pulse, field='omega', num_samples=100, ax=ax, title=title)
        assert len(omega_vals) == 100
    
    save_path = os.path.join(output_dir, "pulse_different_durations.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_pulse_zero_duration_raises():
    """Test that zero duration raises ValueError."""
    pulse = MockPulse(omega=2.0, delta=0.0, duration=0.0)
    
    with pytest.raises(ValueError):
        plot_pulse_waveform(pulse, field='omega')


def test_plot_pulse_negative_duration_raises():
    """Test that negative duration raises ValueError."""
    pulse = MockPulse(omega=2.0, delta=0.0, duration=-1.0)
    
    with pytest.raises(ValueError):
        plot_pulse_waveform(pulse, field='omega')


def test_plot_pulse_no_axes_provided(constant_pulse):
    """Test plotting without providing axes (should create new figure)."""
    ax_result, omega_vals = plot_pulse_waveform(
        constant_pulse, 
        field='omega',
        num_samples=100
    )
    
    assert ax_result is not None
    assert len(omega_vals) == 100
    plt.close()


def test_plot_pulse_local_addressing(output_dir):
    """Test plotting local pulse with atom index."""
    # Create a pulse that varies by atom index
    def omega_func(t, atom_idx):
        return 2.0 + 0.5 * atom_idx
    
    pulse = MockPulse(omega=omega_func, delta=0.0, duration=5.0)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for idx, ax in enumerate(axes):
        _, omega_vals = plot_pulse_waveform(
            pulse, 
            field='omega',
            atom_index=idx,
            num_samples=100,
            ax=ax,
            title=f"Atom {idx}"
        )
        assert len(omega_vals) == 100
    
    save_path = os.path.join(output_dir, "pulse_local_addressing.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)


def test_plot_pulse_missing_field_raises():
    """Test that missing field raises ValueError."""
    # Create a mock object without the requested field
    class MockObject:
        def __init__(self):
            self.omega = 2.0
            self.duration = 5.0
            # Note: no 'delta' or 'invalid_field' attribute
    
    bad_obj = MockObject()
    
    with pytest.raises(ValueError, match="field"):
        plot_pulse_waveform(bad_obj, time_grid=np.linspace(0, 5.0, 100), field='invalid_field')


def test_plot_pulse_invalid_time_grid_raises(constant_pulse):
    """Test that invalid time grid raises ValueError."""
    # Time grid with only 1 point
    bad_time_grid = np.array([0.0])
    
    with pytest.raises(ValueError, match="at least 2 points"):
        plot_pulse_waveform(constant_pulse, time_grid=bad_time_grid, field='omega')


# New tests for dictionary and AST support
def test_plot_pulse_dict_constant(output_dir):
    """Test plotting constant pulse from dictionary format."""
    pulse_dict = {'type': 'constant', 'value': 2.5, 'duration': 5.0}
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        pulse_dict, 
        num_samples=100,
        ax=ax,
        title="Dict Constant Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_dict_constant.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 100
    assert np.allclose(omega_vals, 2.5)


def test_plot_pulse_dict_ramp(output_dir):
    """Test plotting ramp pulse from dictionary format."""
    pulse_dict = {'type': 'ramp', 'initial': 0.0, 'final': 3.0, 'duration': 5.0}
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        pulse_dict, 
        num_samples=100,
        ax=ax,
        title="Dict Ramp Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_dict_ramp.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 100
    # Check ramp goes from ~0 to ~3
    assert np.isclose(omega_vals[0], 0.0, atol=0.1)
    assert np.isclose(omega_vals[-1], 3.0, atol=0.1)


def test_plot_pulse_dict_gaussian(output_dir):
    """Test plotting Gaussian pulse from dictionary format."""
    pulse_dict = {
        'type': 'gaussian', 
        'amplitude': 3.0, 
        'sigma': 1.0, 
        'center': 2.5,
        'duration': 5.0
    }
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        pulse_dict, 
        num_samples=200,
        ax=ax,
        title="Dict Gaussian Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_dict_gaussian.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    # Peak should be near center (2.5)
    peak_idx = np.argmax(omega_vals)
    peak_time = 5.0 * peak_idx / 199  # Map index to time
    assert np.isclose(peak_time, 2.5, atol=0.3)


def test_plot_pulse_dict_piecewise(output_dir):
    """Test plotting piecewise pulse from dictionary format."""
    pulse_dict = {
        'type': 'piecewise',
        'pulses': [
            {'type': 'constant', 'value': 2.0, 'duration': 2.0},
            {'type': 'ramp', 'initial': 2.0, 'final': 0.0, 'duration': 3.0}
        ]
    }
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        pulse_dict, 
        num_samples=200,
        ax=ax,
        title="Dict Piecewise Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_dict_piecewise.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    # First 2μs should be ~2.0
    first_part = omega_vals[:int(200 * 2/5)]
    assert np.allclose(first_part, 2.0, atol=0.1)


def test_plot_pulse_scalar_value(output_dir):
    """Test plotting scalar constant value."""
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        2.5,  # Scalar value
        time_grid=np.linspace(0, 5.0, 100),
        ax=ax,
        title="Scalar Constant Pulse"
    )
    
    save_path = os.path.join(output_dir, "pulse_scalar.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 100
    assert np.allclose(omega_vals, 2.5)


def test_sample_pulse_waveform_dict():
    """Test sample_pulse_waveform with dictionary input."""
    times = np.linspace(0, 5, 100)

    # Test constant
    pulse_const = {'type': 'constant', 'value': 2.0}
    vals_const = sample_pulse_waveform(pulse_const, times)
    assert np.allclose(vals_const, 2.0)

    # Test ramp (using aliased keys initial/final supported by _sample_dict_pulse)
    pulse_ramp = {'type': 'ramp', 'initial': 0, 'final': 4, 'duration': 5}
    vals_ramp = sample_pulse_waveform(pulse_ramp, times)
    assert np.isclose(vals_ramp[0], 0.0, atol=0.1)
    assert np.isclose(vals_ramp[-1], 4.0, atol=0.1)

    # Test Gaussian — peak near center=2.5 at amplitude 3.0
    pulse_gauss = {'type': 'gaussian', 'amplitude': 3.0, 'sigma': 1.0, 'center': 2.5}
    vals_gauss = sample_pulse_waveform(pulse_gauss, times)
    peak_idx = np.argmax(vals_gauss)
    assert np.isclose(vals_gauss[peak_idx], 3.0, atol=0.1)
    peak_time = times[peak_idx]
    assert np.isclose(peak_time, 2.5, atol=0.3)


def test_sample_pulse_waveform_unsupported_type_warns():
    """Test that unsupported pulse type issues warning."""
    import warnings
    
    times = np.linspace(0, 5, 10)
    pulse_unsupported = {'type': 'unsupported_type', 'value': 1.0}
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        vals = sample_pulse_waveform(pulse_unsupported, times)
        
        # Warning is issued for each time point, so we expect len(times) warnings
        assert len(w) == len(times)
        assert all(issubclass(warning.category, UserWarning) for warning in w)
        assert all("Unsupported pulse type" in str(warning.message) for warning in w)
    
    assert np.allclose(vals, 0.0)


# Tests for real Pulse AST nodes (not mock objects)
def test_plot_pulse_real_constant_ast_node(output_dir):
    """Test plotting with real Constant AST node from sagittarius.pulse."""
    from sagittarius.pulse import Constant
    
    # Create real Constant pulse AST node
    const_pulse = Constant(value=2.5, duration=5.0)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        const_pulse, 
        num_samples=100,
        ax=ax,
        title="Real Constant AST Node"
    )
    
    save_path = os.path.join(output_dir, "pulse_real_constant.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 100
    # Should be constant value of 2.5
    assert np.allclose(omega_vals, 2.5)


def test_plot_pulse_real_ramp_ast_node(output_dir):
    """Test plotting with real Ramp AST node from sagittarius.pulse."""
    from sagittarius.pulse import Ramp
    
    # Create real Ramp pulse AST node
    ramp_pulse = Ramp(start_val=0.0, end_val=3.0, duration=5.0)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        ramp_pulse, 
        num_samples=100,
        ax=ax,
        title="Real Ramp AST Node"
    )
    
    save_path = os.path.join(output_dir, "pulse_real_ramp.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 100
    # Check ramp goes from ~0 to ~3
    assert np.isclose(omega_vals[0], 0.0, atol=0.1)
    assert np.isclose(omega_vals[-1], 3.0, atol=0.1)


def test_plot_pulse_real_gaussian_ast_node(output_dir):
    """Test plotting with real Gaussian AST node from sagittarius.pulse."""
    from sagittarius.pulse import Gaussian
    
    # Create real Gaussian pulse AST node
    gaussian_pulse = Gaussian(amplitude=3.0, sigma=1.0, duration=5.0, mu=2.5)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        gaussian_pulse, 
        num_samples=200,
        ax=ax,
        title="Real Gaussian AST Node"
    )
    
    save_path = os.path.join(output_dir, "pulse_real_gaussian.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    # Peak should be near center (mu=2.5)
    peak_idx = np.argmax(omega_vals)
    peak_time = 5.0 * peak_idx / 199  # Map index to time
    assert np.isclose(peak_time, 2.5, atol=0.3)
    # Peak value should be close to amplitude
    assert np.isclose(omega_vals[peak_idx], 3.0, atol=0.1)


def test_plot_pulse_real_piecewise_ast_node(output_dir):
    """Test plotting with real Piecewise AST node from sagittarius.pulse."""
    from sagittarius.pulse import Constant, Ramp, Piecewise
    
    # Create real Piecewise pulse with multiple segments
    p1 = Constant(value=2.0, duration=2.0)
    p2 = Ramp(start_val=2.0, end_val=0.0, duration=3.0)
    piecewise_pulse = Piecewise([p1, p2])
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        piecewise_pulse, 
        num_samples=200,
        ax=ax,
        title="Real Piecewise AST Node"
    )
    
    save_path = os.path.join(output_dir, "pulse_real_piecewise.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    # First 2μs should be ~2.0
    first_part = omega_vals[:int(200 * 2/5)]
    assert np.allclose(first_part, 2.0, atol=0.1)


def test_sample_pulse_waveform_real_ast_nodes():
    """Test sample_pulse_waveform with real AST nodes."""
    from sagittarius.pulse import Constant, Ramp, Gaussian, Piecewise

    times = np.linspace(0, 5, 100)

    # Test Constant
    const_pulse = Constant(value=2.5, duration=5.0)
    vals_const = sample_pulse_waveform(const_pulse, times)
    assert np.allclose(vals_const, 2.5)

    # Test Ramp
    ramp_pulse = Ramp(start_val=0.0, end_val=4.0, duration=5.0)
    vals_ramp = sample_pulse_waveform(ramp_pulse, times)
    assert np.isclose(vals_ramp[0], 0.0, atol=0.1)
    assert np.isclose(vals_ramp[-1], 4.0, atol=0.1)

    # Test Gaussian — peak at mu=2.5 should be close to amplitude
    gauss_pulse = Gaussian(amplitude=3.0, sigma=1.0, duration=5.0, mu=2.5)
    vals_gauss = sample_pulse_waveform(gauss_pulse, times)
    peak_idx = np.argmax(vals_gauss)
    assert np.isclose(vals_gauss[peak_idx], 3.0, atol=0.1)

    # Test Piecewise: constant 2μs then ramp down 3μs
    pw_pulse = Piecewise([Constant(value=2.0, duration=2.0),
                          Ramp(start_val=2.0, end_val=0.0, duration=3.0)])
    vals_pw = sample_pulse_waveform(pw_pulse, times)
    # First segment (t in [0,2)) should all be ~2.0
    first_segment = vals_pw[times < 2.0]
    assert np.allclose(first_segment, 2.0, atol=0.05)
    # Last point should be close to 0
    assert np.isclose(vals_pw[-1], 0.0, atol=0.1)


def test_sample_pulse_waveform_real_blackman_sinc_sinsquared():
    """Test sample_pulse_waveform with Blackman, Sinc, SinSquared AST nodes."""
    from sagittarius.pulse import Blackman, Sinc, SinSquared

    times = np.linspace(0, 5, 201)  # 201 points so t=2.5 hits exactly at index 100

    # Blackman — peak at center (x=0.5) should equal amplitude
    bk = Blackman(amplitude=2.0, duration=5.0)
    vals_bk = sample_pulse_waveform(bk, times)
    assert len(vals_bk) == 201
    # Center value: 0.42 - 0.5*cos(π) + 0.08*cos(2π) = 1.0 => amplitude * 1.0
    assert np.isclose(vals_bk[100], 2.0, atol=0.05)
    # Boundary values should be ~0 (Blackman window property)
    assert np.isclose(vals_bk[0], 0.0, atol=0.05)

    # Sinc — peak at center t=2.5 should equal amplitude
    sc = Sinc(amplitude=2.0, width=0.5, duration=5.0)
    vals_sc = sample_pulse_waveform(sc, times)
    assert len(vals_sc) == 201
    assert np.isclose(vals_sc[100], 2.0, atol=0.05)

    # SinSquared — peak at center (x=0.5) should equal amplitude
    ss = SinSquared(amplitude=2.0, duration=5.0)
    vals_ss = sample_pulse_waveform(ss, times)
    assert len(vals_ss) == 201
    assert np.isclose(vals_ss[100], 2.0, atol=0.05)
    # Boundary values should be 0 (sin²(0)=0, sin²(π)=0)
    assert np.isclose(vals_ss[0], 0.0, atol=0.05)


def test_plot_pulse_real_blackman_ast_node(output_dir):
    """Test plotting with real Blackman AST node from sagittarius.pulse."""
    from sagittarius.pulse import Blackman
    
    # Create real Blackman pulse AST node
    blackman_pulse = Blackman(amplitude=2.0, duration=5.0)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        blackman_pulse, 
        num_samples=200,
        ax=ax,
        title="Real Blackman AST Node"
    )
    
    save_path = os.path.join(output_dir, "pulse_real_blackman.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    # At center, should be close to amplitude
    mid_idx = len(omega_vals) // 2
    assert np.isclose(omega_vals[mid_idx], 2.0, atol=0.1)


def test_plot_pulse_real_sinc_ast_node(output_dir):
    """Test plotting with real Sinc AST node from sagittarius.pulse."""
    from sagittarius.pulse import Sinc
    
    # Create real Sinc pulse AST node
    sinc_pulse = Sinc(amplitude=2.0, width=0.5, duration=5.0)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        sinc_pulse, 
        num_samples=200,
        ax=ax,
        title="Real Sinc AST Node"
    )
    
    save_path = os.path.join(output_dir, "pulse_real_sinc.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    # At center (t=2.5), sinc=1, so value should be amplitude
    mid_idx = len(omega_vals) // 2
    assert np.isclose(omega_vals[mid_idx], 2.0, atol=0.1)


def test_plot_pulse_real_sin_squared_ast_node(output_dir):
    """Test plotting with real SinSquared AST node from sagittarius.pulse."""
    from sagittarius.pulse import SinSquared
    
    # Create real SinSquared pulse AST node
    sinsq_pulse = SinSquared(amplitude=2.0, duration=5.0)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    _, omega_vals = plot_pulse_waveform(
        sinsq_pulse, 
        num_samples=200,
        ax=ax,
        title="Real SinSquared AST Node"
    )
    
    save_path = os.path.join(output_dir, "pulse_real_sin_squared.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    # At half period (t=2.5), sin^2(pi/2)=1, so value should be amplitude
    mid_idx = len(omega_vals) // 2
    assert np.isclose(omega_vals[mid_idx], 2.0, atol=0.1)


# ---------------------------------------------------------------------------
# Dictionary-format tests for Blackman, Sinc, SinSquared pulse types
# ---------------------------------------------------------------------------

def test_plot_pulse_dict_blackman(output_dir):
    """Test plotting Blackman pulse from dictionary format."""
    pulse_dict = {'type': 'blackman', 'amplitude': 2.0, 'duration': 5.0}

    fig, ax = plt.subplots(figsize=(10, 4))
    _, omega_vals = plot_pulse_waveform(
        pulse_dict,
        num_samples=200,
        ax=ax,
        title="Dict Blackman Pulse"
    )

    save_path = os.path.join(output_dir, "pulse_dict_blackman.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    # dict-format Blackman routes to _sample_dict_pulse which falls back to
    # the AST sampler; verify at least the output array is non-trivial
    assert np.max(omega_vals) > 0.0


def test_plot_pulse_dict_sinc(output_dir):
    """Test plotting Sinc pulse from dictionary format."""
    pulse_dict = {'type': 'sinc', 'amplitude': 2.0, 'width': 0.5, 'duration': 5.0}

    fig, ax = plt.subplots(figsize=(10, 4))
    _, omega_vals = plot_pulse_waveform(
        pulse_dict,
        num_samples=200,
        ax=ax,
        title="Dict Sinc Pulse"
    )

    save_path = os.path.join(output_dir, "pulse_dict_sinc.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    assert np.max(omega_vals) > 0.0


def test_plot_pulse_dict_sin_squared(output_dir):
    """Test plotting SinSquared pulse from dictionary format."""
    pulse_dict = {'type': 'sin_squared', 'amplitude': 2.0, 'duration': 5.0}

    fig, ax = plt.subplots(figsize=(10, 4))
    _, omega_vals = plot_pulse_waveform(
        pulse_dict,
        num_samples=200,
        ax=ax,
        title="Dict SinSquared Pulse"
    )

    save_path = os.path.join(output_dir, "pulse_dict_sin_squared.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

    assert os.path.exists(save_path)
    assert len(omega_vals) == 200
    assert np.max(omega_vals) > 0.0


def test_all_ast_node_types_via_plot(output_dir):
    """Smoke test: all supported PulseNode types produce non-empty valid waveforms."""
    from sagittarius.pulse import Constant, Ramp, Gaussian, Blackman, Sinc, SinSquared, Piecewise

    cases = [
        ("Constant",    Constant(value=2.0, duration=5.0)),
        ("Ramp",        Ramp(start_val=0.0, end_val=3.0, duration=5.0)),
        ("Gaussian",    Gaussian(amplitude=3.0, sigma=1.0, duration=5.0, mu=2.5)),
        ("Blackman",    Blackman(amplitude=2.0, duration=5.0)),
        ("Sinc",        Sinc(amplitude=2.0, width=0.5, duration=5.0)),
        ("SinSquared",  SinSquared(amplitude=2.0, duration=5.0)),
        ("Piecewise",   Piecewise([Constant(value=2.0, duration=2.0),
                                   Ramp(start_val=2.0, end_val=0.0, duration=3.0)])),
    ]

    fig, axes = plt.subplots(len(cases), 1, figsize=(10, 4 * len(cases)))

    for ax, (name, pulse) in zip(axes, cases):
        _, vals = plot_pulse_waveform(pulse, num_samples=100, ax=ax, title=name)
        assert len(vals) == 100, f"{name}: expected 100 samples"
        assert np.all(np.isfinite(vals)), f"{name}: waveform contains non-finite values"

    save_path = os.path.join(output_dir, "pulse_all_ast_nodes.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.close()

    assert os.path.exists(save_path)
