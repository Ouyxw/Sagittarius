"""
Test pulse dictionary conversion and parsing functionality.

Tests for dict_to_pulse_node() and parse_pulse_config() functions.
"""

import pytest
import numpy as np
from sagittarius.pulse import (
    Constant, Ramp, Gaussian, Piecewise, Blackman, Sinc, SinSquared,
    dict_to_pulse_node, parse_pulse_config
)


# Test dict_to_pulse_node
def test_dict_to_constant():
    """Test converting constant pulse dictionary."""
    pulse_dict = {'type': 'constant', 'value': 2.5, 'duration': 5.0}
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, Constant)
    assert pulse.value == 2.5
    assert pulse.duration == 5.0


def test_dict_to_ramp():
    """Test converting ramp pulse dictionary."""
    pulse_dict = {
        'type': 'ramp',
        'start_val': 0.0,
        'end_val': 3.0,
        'duration': 5.0
    }
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, Ramp)
    assert pulse.start_val == 0.0
    assert pulse.end_val == 3.0
    assert pulse.duration == 5.0


def test_dict_to_gaussian():
    """Test converting gaussian pulse dictionary."""
    pulse_dict = {
        'type': 'gaussian',
        'amplitude': 3.0,
        'sigma': 1.0,
        'duration': 5.0,
        'mu': 2.5
    }
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, Gaussian)
    assert pulse.amplitude == 3.0
    assert pulse.sigma == 1.0
    assert pulse.duration == 5.0
    assert pulse.mu == 2.5


def test_dict_to_gaussian_without_mu():
    """Test converting gaussian pulse without mu (should default to duration/2)."""
    pulse_dict = {
        'type': 'gaussian',
        'amplitude': 3.0,
        'sigma': 1.0,
        'duration': 5.0
    }
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, Gaussian)
    # When mu is not provided, it defaults to duration/2 in the constructor
    assert pulse.mu == 2.5


def test_dict_to_blackman():
    """Test converting blackman pulse dictionary."""
    pulse_dict = {
        'type': 'blackman',
        'amplitude': 2.0,
        'duration': 5.0
    }
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, Blackman)
    assert pulse.amplitude == 2.0
    assert pulse.duration == 5.0


def test_dict_to_sinc():
    """Test converting sinc pulse dictionary."""
    pulse_dict = {
        'type': 'sinc',
        'amplitude': 2.0,
        'width': 0.5,
        'duration': 5.0
    }
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, Sinc)
    assert pulse.amplitude == 2.0
    assert pulse.width == 0.5
    assert pulse.duration == 5.0


def test_dict_to_sin_squared():
    """Test converting sin_squared pulse dictionary."""
    pulse_dict = {
        'type': 'sin_squared',
        'amplitude': 2.0,
        'duration': 5.0
    }
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, SinSquared)
    assert pulse.amplitude == 2.0
    assert pulse.duration == 5.0


def test_dict_to_piecewise():
    """Test converting piecewise pulse dictionary."""
    pulse_dict = {
        'type': 'piecewise',
        'pulses': [
            {'type': 'constant', 'value': 2.0, 'duration': 2.0},
            {'type': 'ramp', 'start_val': 2.0, 'end_val': 0.0, 'duration': 3.0}
        ]
    }
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, Piecewise)
    assert len(pulse.pulses) == 2
    assert isinstance(pulse.pulses[0], Constant)
    assert isinstance(pulse.pulses[1], Ramp)


def test_dict_to_piecewise_nested():
    """Test converting nested piecewise pulse dictionary."""
    pulse_dict = {
        'type': 'piecewise',
        'pulses': [
            {'type': 'constant', 'value': 1.0, 'duration': 1.0},
            {
                'type': 'piecewise',
                'pulses': [
                    {'type': 'ramp', 'start_val': 1.0, 'end_val': 2.0, 'duration': 2.0},
                    {'type': 'constant', 'value': 2.0, 'duration': 1.0}
                ]
            },
            {'type': 'gaussian', 'amplitude': 2.0, 'sigma': 0.5, 'duration': 2.0}
        ]
    }
    pulse = dict_to_pulse_node(pulse_dict)
    
    assert isinstance(pulse, Piecewise)
    assert len(pulse.pulses) == 3
    assert isinstance(pulse.pulses[0], Constant)
    assert isinstance(pulse.pulses[1], Piecewise)
    assert isinstance(pulse.pulses[2], Gaussian)


def test_dict_missing_type_raises():
    """Test that missing 'type' key raises ValueError."""
    pulse_dict = {'value': 2.0, 'duration': 5.0}
    
    with pytest.raises(ValueError, match="must contain 'type'"):
        dict_to_pulse_node(pulse_dict)


def test_dict_unsupported_type_raises():
    """Test that unsupported pulse type raises ValueError."""
    pulse_dict = {'type': 'unsupported', 'value': 2.0}
    
    with pytest.raises(ValueError, match="Unsupported pulse type"):
        dict_to_pulse_node(pulse_dict)


def test_dict_constant_missing_params_raises():
    """Test that constant pulse with missing params raises ValueError."""
    pulse_dict = {'type': 'constant', 'value': 2.0}  # Missing duration
    
    with pytest.raises(ValueError, match="requires.*duration"):
        dict_to_pulse_node(pulse_dict)


def test_dict_ramp_missing_params_raises():
    """Test that ramp pulse with missing params raises ValueError."""
    pulse_dict = {'type': 'ramp', 'start_val': 0.0, 'duration': 5.0}  # Missing end_val
    
    with pytest.raises(ValueError, match="requires.*end_val"):
        dict_to_pulse_node(pulse_dict)


def test_dict_not_dict_raises():
    """Test that non-dict input raises TypeError."""
    with pytest.raises(TypeError):
        dict_to_pulse_node("not a dict")


# Test parse_pulse_config
def test_parse_pulse_config_dict():
    """Test that dict config is converted to PulseNode."""
    config = {'type': 'constant', 'value': 2.0, 'duration': 5.0}
    result = parse_pulse_config(config)
    
    assert isinstance(result, Constant)
    assert result.value == 2.0


def test_parse_pulse_config_scalar_passthrough():
    """Test that scalar config passes through unchanged."""
    result = parse_pulse_config(2.5)
    assert result == 2.5


def test_parse_pulse_config_callable_passthrough():
    """Test that callable config passes through unchanged."""
    func = lambda t: 2.0 * t
    result = parse_pulse_config(func)
    assert result is func


def test_parse_pulse_config_pulsenode_passthrough():
    """Test that PulseNode config passes through unchanged."""
    pulse = Constant(2.0, 5.0)
    result = parse_pulse_config(pulse)
    assert result is pulse


def test_parse_pulse_config_list_passthrough():
    """Test that list config passes through unchanged."""
    config = [1.0, 2.0, 3.0]
    result = parse_pulse_config(config)
    assert result == config


def test_parse_pulse_config_none_passthrough():
    """Test that None config passes through unchanged."""
    result = parse_pulse_config(None)
    assert result is None


# Integration test with sample_pulse_waveform
def test_integration_dict_pulse_sampling():
    """Test that dict pulses work with sample_pulse_waveform."""
    from sagittarius.viz import sample_pulse_waveform
    
    times = np.linspace(0, 5, 100)
    
    # Test constant
    pulse_dict = {'type': 'constant', 'value': 2.0, 'duration': 5.0}
    vals = sample_pulse_waveform(pulse_dict, times)
    assert np.allclose(vals, 2.0)
    
    # Test ramp
    pulse_dict = {'type': 'ramp', 'start_val': 0, 'end_val': 4, 'duration': 5}
    vals = sample_pulse_waveform(pulse_dict, times)
    assert np.isclose(vals[0], 0.0, atol=0.01)
    assert np.isclose(vals[-1], 4.0, atol=0.01)
    
    # Test gaussian
    pulse_dict = {'type': 'gaussian', 'amplitude': 3.0, 'sigma': 1.0, 'duration': 5.0, 'mu': 2.5}
    vals = sample_pulse_waveform(pulse_dict, times)
    peak_idx = np.argmax(vals)
    peak_time = 5.0 * peak_idx / 99
    # With 100 samples over 5μs, the time resolution is ~0.05μs
    assert np.isclose(peak_time, 2.5, atol=0.1)


def test_integration_parse_pulse_with_sampling():
    """Test that parse_pulse_config works with sample_pulse_waveform."""
    from sagittarius.viz import sample_pulse_waveform
    
    times = np.linspace(0, 5, 100)
    
    # Parse dict to PulseNode
    config = {'type': 'ramp', 'start_val': 0, 'end_val': 3, 'duration': 5}
    pulse = parse_pulse_config(config)
    
    # Sample it
    vals = sample_pulse_waveform(pulse, times)
    assert np.isclose(vals[0], 0.0, atol=0.01)
    assert np.isclose(vals[-1], 3.0, atol=0.01)
