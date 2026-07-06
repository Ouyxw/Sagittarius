"""
Pulse waveform visualization utilities.

Provides deterministic pulse sampling and plotting helpers for PulseSequence
objects. These functions extract omega/delta waveforms over explicit time grids
without initializing Julia, supporting global pulses, local addressing vectors,
callable pulse definitions, dictionary format, and Pulse AST nodes.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from typing import Optional, Union, Callable
import warnings


def _sample_dict_pulse(
    pulse_dict: dict,
    t: float,
    atom_index: Optional[int] = None
) -> float:
    """
    Sample pulse amplitude at a single time point from dictionary-formatted pulse definition.
    Pure Python numerical evaluation, no Julia backend initialization.
    Supports 7 standard pulse types, nested piecewise pulses, and dual alias parameter naming.

    Supported pulse types:
    1. constant    Constant fixed amplitude pulse
    2. ramp        Linear ramp pulse (supports dual aliases: initial/start_val, final/end_val)
    3. gaussian    Gaussian pulse (supports dual center aliases: center/mu)
    4. piecewise   Composite piecewise pulse, supports nested sub-pulses
    5. blackman    Blackman window pulse
    6. sinc        Sinc function pulse
    7. sin_squared Sin-squared envelope pulse sin²(πt/T)

    Args:
        pulse_dict: dict
            Pulse configuration dict. Must contain a "type" key to identify pulse shape,
            plus shape-specific configuration parameters.
        t: float
            Absolute sampling time in microseconds (μs). For piecewise pulses,
            internal logic automatically converts to segment-local relative time.
        atom_index: Optional[int], default=None
            Atom index for local addressing. Unused in current dict pulse logic,
            retained for unified API compatibility with AST sampling functions.

    Returns:
        float
        Pulse amplitude at the given time point (unit: rad/μs for Ω Rabi / Δ detuning fields)

    """

    pulse_type = pulse_dict.get('type', '').lower()
    
    if pulse_type == 'constant':
        value = pulse_dict.get('value', 0.0)
        return float(value)
    
    elif pulse_type == 'ramp':
        # Support both naming conventions: start_val/end_val and initial/final
        initial = pulse_dict.get('start_val', pulse_dict.get('initial', 0.0))
        final = pulse_dict.get('end_val', pulse_dict.get('final', 0.0))
        duration = pulse_dict.get('duration', 1.0)
        
        if duration <= 0:
            return float(final)
        
        # Linear interpolation
        progress = min(max(t / duration, 0.0), 1.0)
        return float(initial + progress * (final - initial))
    
    elif pulse_type == 'gaussian':
        amplitude = pulse_dict.get('amplitude', 1.0)
        sigma = pulse_dict.get('sigma', 1.0)
        # Support both naming conventions: center and mu
        center = pulse_dict.get('center', pulse_dict.get('mu', 0.0))
        
        # Gaussian formula: A * exp(-(t - center)^2 / (2 * sigma^2))
        exponent = -((t - center) ** 2) / (2 * sigma ** 2)
        return float(amplitude * np.exp(exponent))
    
    elif pulse_type == 'piecewise':
        pulses = pulse_dict.get('pulses', [])
        if not pulses:
            return 0.0
        
        # Find which sub-pulse applies at time t
        current_time = 0.0
        for sub_pulse in pulses:
            sub_duration = sub_pulse.get('duration', 0.0)
            if t < current_time + sub_duration:
                # Sample this sub-pulse at relative time
                relative_t = t - current_time
                return _sample_dict_pulse(sub_pulse, relative_t, atom_index)
            current_time += sub_duration
        
        # If t is beyond all pulses, return last value
        if pulses:
            last_pulse = pulses[-1]
            last_duration = last_pulse.get('duration', 0.0)
            return _sample_dict_pulse(last_pulse, last_duration, atom_index)
        return 0.0
    
    elif pulse_type == 'blackman':
        amplitude = pulse_dict.get('amplitude', 1.0)
        duration = pulse_dict.get('duration', 1.0)
        if duration <= 0:
            return 0.0
        x = min(max(t / duration, 0.0), 1.0)
        return float(amplitude * (0.42 - 0.5 * np.cos(2 * np.pi * x) + 0.08 * np.cos(4 * np.pi * x)))

    elif pulse_type == 'sinc':
        amplitude = pulse_dict.get('amplitude', 1.0)
        width = pulse_dict.get('width', 1.0)
        duration = pulse_dict.get('duration', 1.0)
        center = duration / 2.0
        # np.sinc is normalized: sinc(x) = sin(πx)/(πx)
        arg = (t - center) / width if width != 0 else 0.0
        return float(amplitude * np.sinc(arg))

    elif pulse_type in ('sin_squared', 'sinsquared'):
        amplitude = pulse_dict.get('amplitude', 1.0)
        duration = pulse_dict.get('duration', 1.0)
        if duration <= 0:
            return 0.0
        x = min(max(t / duration, 0.0), 1.0)
        return float(amplitude * (np.sin(np.pi * x) ** 2))

    else:
        warnings.warn(
            f"Unsupported pulse type '{pulse_type}' in dictionary format. "
            f"Returning 0.0. Supported types: 'constant', 'ramp', 'gaussian', "
            f"'blackman', 'sinc', 'sin_squared', 'piecewise'",
            UserWarning
        )
        return 0.0


def _sample_ast_node(
    ast_node,
    t: float,
    atom_index: Optional[int] = None
) -> float:
    """
    Sample a pulse from AST node representation.
    
    This function handles Sagittarius Pulse AST nodes by extracting their
    parameters and evaluating them at time t.
    
    Args:
        ast_node: AST node object (e.g., Constant, Ramp, Gaussian, Piecewise)
        t: Time point to sample
        atom_index: Atom index for local addressing
        
    Returns:
        Float value at time t
    """
    # Get the node type
    node_type = getattr(ast_node, '__class__', type(ast_node)).__name__.lower()
    
    # Map common AST node names to sampling logic
    if 'constant' in node_type:
        # Extract value attribute
        if hasattr(ast_node, 'value'):
            return float(ast_node.value)
        elif hasattr(ast_node, 'omega') or hasattr(ast_node, 'delta'):
            # Some implementations store value in omega/delta
            val = getattr(ast_node, 'omega', None) or getattr(ast_node, 'delta', 0.0)
            return float(val) if not callable(val) else 0.0
    
    elif 'ramp' in node_type:
        # Extract ramp parameters (support both naming conventions)
        initial = getattr(ast_node, 'start_val', getattr(ast_node, 'initial', 0.0))
        final = getattr(ast_node, 'end_val', getattr(ast_node, 'final', 0.0))
        duration = getattr(ast_node, 'duration', 1.0)
        
        if callable(initial):
            initial = initial(t) if atom_index is None else initial(t, atom_index)
        if callable(final):
            final = final(t) if atom_index is None else final(t, atom_index)
        
        if duration <= 0:
            return float(final)
        
        progress = min(max(t / duration, 0.0), 1.0)
        return float(initial + progress * (final - initial))
    
    elif 'gaussian' in node_type:
        # Extract Gaussian parameters; real Gaussian AST node uses 'mu' for center
        amplitude = getattr(ast_node, 'amplitude', 1.0)
        sigma = getattr(ast_node, 'sigma', 1.0)
        # Support both attribute names: 'mu' (real AST node) and 'center' (dict / mock)
        center = getattr(ast_node, 'mu', getattr(ast_node, 'center', 0.0))

        if callable(amplitude):
            amplitude = amplitude(t) if atom_index is None else amplitude(t, atom_index)

        exponent = -((t - center) ** 2) / (2 * sigma ** 2)
        return float(amplitude * np.exp(exponent))
    
    elif 'piecewise' in node_type:
        # Handle piecewise pulses
        if hasattr(ast_node, 'pulses'):
            pulses = ast_node.pulses
            current_time = 0.0
            
            for sub_pulse in pulses:
                sub_duration = getattr(sub_pulse, 'duration', 0.0)
                if t < current_time + sub_duration:
                    relative_t = t - current_time
                    return _sample_ast_node(sub_pulse, relative_t, atom_index)
                current_time += sub_duration
            
            # Beyond all pulses
            if pulses:
                return _sample_ast_node(pulses[-1], 
                                       getattr(pulses[-1], 'duration', 0.0), 
                                       atom_index)
        return 0.0
    
    elif 'blackman' in node_type:
        # Blackman window: A * (0.42 - 0.5*cos(2π*t/T) + 0.08*cos(4π*t/T))
        amplitude = getattr(ast_node, 'amplitude', 1.0)
        duration = getattr(ast_node, 'duration', 1.0)
        if duration <= 0:
            return 0.0
        x = t / duration
        x = min(max(x, 0.0), 1.0)
        return float(amplitude * (0.42 - 0.5 * np.cos(2 * np.pi * x) + 0.08 * np.cos(4 * np.pi * x)))

    elif 'sinc' in node_type:
        # Sinc pulse: A * sinc(π * (t - T/2) / width)  where sinc(x) = sin(x)/x
        amplitude = getattr(ast_node, 'amplitude', 1.0)
        width = getattr(ast_node, 'width', 1.0)
        duration = getattr(ast_node, 'duration', 1.0)
        center = duration / 2.0
        arg = np.pi * (t - center) / width if width != 0 else 0.0
        sinc_val = np.sinc(arg / np.pi)  # np.sinc uses normalized sinc: sinc(x)=sin(πx)/(πx)
        return float(amplitude * sinc_val)

    elif 'sinsquared' in node_type or 'sin_squared' in node_type:
        # SinSquared: A * sin²(π * t / T)
        amplitude = getattr(ast_node, 'amplitude', 1.0)
        duration = getattr(ast_node, 'duration', 1.0)
        if duration <= 0:
            return 0.0
        x = min(max(t / duration, 0.0), 1.0)
        return float(amplitude * (np.sin(np.pi * x) ** 2))

    # Fallback: try to call as callable or extract value
    if callable(ast_node):
        try:
            if atom_index is not None:
                return float(ast_node(t, atom_index))
            else:
                return float(ast_node(t))
        except TypeError:
            return float(ast_node(t))

    # Last resort: return 0.0 with warning
    warnings.warn(
        f"Unsupported AST node type '{node_type}'. Returning 0.0.",
        UserWarning
    )
    return 0.0


def _sample_pulse_value(
    pulse_component,
    t: float,
    atom_index: Optional[int] = None
) -> float:
    """
    Sample a single pulse component value at time t.
    
    Handles different pulse component types:
    - Scalar/constant values
    - Callable functions: f(t) or f(t, atom_index)
    - List/array values (interpolated)
    - Dictionary format: {'type': 'constant'|'ramp'|'gaussian', ...}
    - Pulse AST nodes: Piecewise, Constant, Ramp, Gaussian, etc.
    - ExplicitPulse wrappers: GlobalPulse, LocalPulseVector, CallablePulse
    
    Args:
        pulse_component: The pulse value (scalar, callable, array, dict, AST node, or ExplicitPulse)
        t: Time point to sample
        atom_index: Atom index for local addressing (0-based)
        
    Returns:
        Float value of the pulse component at time t
        
    Raises:
        ValueError: If pulse_component type is not supported
        UserWarning: If AST node type is unsupported (returns 0.0 with warning)
    """
    # Import here to avoid circular dependency
    from sagittarius.pulse import ExplicitPulse, GlobalPulse, LocalPulseVector, CallablePulse, PulseNode
    
    # Handle ExplicitPulse wrappers
    if isinstance(pulse_component, ExplicitPulse):
        if isinstance(pulse_component, GlobalPulse):
            # GlobalPulse: apply same value to all atoms
            return _sample_pulse_value(pulse_component.value, t, atom_index)
        
        elif isinstance(pulse_component, LocalPulseVector):
            # LocalPulseVector: get value for specific atom
            values = pulse_component.values
            if isinstance(values, dict):
                # Sparse dict format: get value for atom_index, default to 0.0
                if atom_index is not None:
                    pulse_val = values.get(atom_index, 0.0)
                else:
                    # If no atom_index specified, use first value or 0.0
                    pulse_val = next(iter(values.values()), 0.0) if values else 0.0
                return _sample_pulse_value(pulse_val, t, atom_index)
            elif isinstance(values, (list, tuple)):
                # List format: get value by index
                if atom_index is not None and 0 <= atom_index < len(values):
                    pulse_val = values[atom_index]
                else:
                    # Default to first value or 0.0
                    pulse_val = values[0] if values else 0.0
                return _sample_pulse_value(pulse_val, t, atom_index)
            else:
                return 0.0
        
        elif isinstance(pulse_component, CallablePulse):
            # CallablePulse: call the function
            result = pulse_component(t)
            if isinstance(result, (list, tuple)):
                # Returns per-atom values
                if atom_index is not None and 0 <= atom_index < len(result):
                    return float(result[atom_index])
                else:
                    return float(result[0]) if result else 0.0
            else:
                # Returns scalar
                return float(result)
    
    # Handle Pulse AST nodes
    if isinstance(pulse_component, PulseNode):
        return _sample_ast_node(pulse_component, t, atom_index)
    
    # Handle dictionary format (AST-like representation)
    if isinstance(pulse_component, dict):
        return _sample_dict_pulse(pulse_component, t, atom_index)
    
    # Handle callable functions
    if callable(pulse_component):
        # Try calling with atom_index first (for local pulses)
        if atom_index is not None:
            try:
                return float(pulse_component(t, atom_index))
            except TypeError:
                # Fallback: callable doesn't accept atom_index
                return float(pulse_component(t))
        else:
            return float(pulse_component(t))
    
    # Handle list/array values
    elif isinstance(pulse_component, (list, np.ndarray)):
        # For array-based pulses, return constant value or interpolate
        if len(pulse_component) > 0:
            return float(pulse_component[0])  # Return first value as constant
        else:
            return 0.0
    
    # Handle scalar constants
    else:
        return float(pulse_component)


def sample_pulse_waveform(
    pulse_sequence,
    time_grid: np.ndarray,
    field: str = 'omega',
    atom_index: Optional[int] = None
) -> np.ndarray:
    """
    Sample a pulse waveform over a time grid without plotting.
    
    This is a data extraction helper that returns pure NumPy arrays,
    suitable for custom plotting or analysis. Supports multiple input formats:
    - Object with .omega/.delta attributes
    - Dictionary format: {'type': 'constant'|'ramp'|'gaussian', ...}
    - Pulse AST nodes (Constant, Ramp, Gaussian, Piecewise, etc.)
    - Callable functions
    - Scalar constants
    
    The function does NOT initialize Julia unless the pulse_sequence itself
    requires it for evaluation.
    
    Args:
        pulse_sequence: Sagittarius PulseSequence, Pulse object, dict, or AST node
        time_grid: Array of time points to sample (in μs)
        field: 'omega' (Rabi frequency) or 'delta' (detuning). 
              Ignored if pulse_sequence is a dict or AST node.
        atom_index: Atom index for local addressing (0-based). 
                   If None, samples global pulse.
                   
    Returns:
        NumPy array of pulse values at each time point
        
    Raises:
        ValueError: If pulse_sequence type cannot be handled
        
    Example:
        >>> times = np.linspace(0, 10, 100)
        >>> # Object with attributes
        >>> omega_vals = sample_pulse_waveform(pulse, times, field='omega')
        >>> # Dictionary format
        >>> pulse_dict = {'type': 'ramp', 'initial': 0, 'final': 3, 'duration': 5}
        >>> omega_vals = sample_pulse_waveform(pulse_dict, times)
        >>> # With atom index
        >>> delta_vals = sample_pulse_waveform(pulse, times, field='delta', atom_index=2)
    """
    # Handle dictionary format directly
    if isinstance(pulse_sequence, dict):
        # For dict, we don't use 'field' parameter
        values = np.array([
            _sample_dict_pulse(pulse_sequence, t, atom_index) 
            for t in time_grid
        ])
        return values
    
    # Handle scalar constants (int, float)
    if isinstance(pulse_sequence, (int, float)):
        # Return constant value for all time points
        return np.full(len(time_grid), float(pulse_sequence))
    
    # Handle AST-like objects (check for common AST node attributes)
    # Be more specific to avoid matching mock objects
    node_type = getattr(pulse_sequence, '__class__', type(pulse_sequence)).__name__.lower()
    ast_keywords = ['constant', 'ramp', 'gaussian', 'piecewise', 'blackman', 'sinc', 'sinsquared']

    # Only treat as AST node if it has typical AST node characteristics
    is_ast_node = any(keyword in node_type for keyword in ast_keywords)
    
    # Additional check: real AST nodes typically have specific attributes
    if is_ast_node:
        has_ast_attrs = (
            hasattr(pulse_sequence, 'duration') or
            hasattr(pulse_sequence, 'amplitude') or
            hasattr(pulse_sequence, 'sigma') or
            hasattr(pulse_sequence, 'center') or
            hasattr(pulse_sequence, 'initial') or
            hasattr(pulse_sequence, 'final') or
            hasattr(pulse_sequence, 'pulses') or
            hasattr(pulse_sequence, 'value')
        )
        
        if not has_ast_attrs:
            # Probably a mock object, not a real AST node
            is_ast_node = False
    
    if is_ast_node:
        # Try to extract the appropriate field or use the object directly
        if hasattr(pulse_sequence, field):
            pulse_component = getattr(pulse_sequence, field)
            # If the field is also an AST node, sample it
            if isinstance(pulse_component, dict) or hasattr(pulse_component, '__class__'):
                comp_type = getattr(pulse_component, '__class__', type(pulse_component)).__name__.lower()
                if any(kw in comp_type for kw in ast_keywords):
                    values = np.array([
                        _sample_ast_node(pulse_component, t, atom_index) 
                        for t in time_grid
                    ])
                    return values
        
        # Otherwise treat the whole object as the pulse
        values = np.array([
            _sample_ast_node(pulse_sequence, t, atom_index) 
            for t in time_grid
        ])
        return values
    
    # Handle object with field attributes (original behavior)
    if hasattr(pulse_sequence, field):
        pulse_component = getattr(pulse_sequence, field)
    else:
        raise ValueError(f"Pulse sequence does not have field '{field}'. "
                        f"Available fields: {[attr for attr in dir(pulse_sequence) if not attr.startswith('_')]}")
    
    # Sample at each time point using the enhanced sampler
    values = np.array([
        _sample_pulse_value(pulse_component, t, atom_index) 
        for t in time_grid
    ])
    
    return values


def plot_pulse_waveform(
    pulse_sequence,
    time_grid: Optional[np.ndarray] = None,
    field: str = 'omega',
    atom_index: Optional[int] = None,
    ax: Optional[Axes] = None,
    num_samples: int = 200,
    title: Optional[str] = None,
) -> tuple:
    """
    Plot the waveform of a pulse sequence (omega or delta).
    
    This function deterministically samples the pulse waveform over a time grid
    and plots it using matplotlib. It supports multiple input formats:
    
    **Supported Input Formats:**
    1. **Object with attributes**: Objects with `.omega` or `.delta` fields
    2. **Dictionary format**: `{'type': 'constant'|'ramp'|'gaussian'|'piecewise', ...}`
    3. **Pulse AST nodes**: Constant, Ramp, Gaussian, Piecewise, etc.
    4. **Callable functions**: `f(t)` or `f(t, atom_index)` for local addressing
    5. **Scalar constants**: Single numeric value
    
    **Backend Behavior:**
    - Does NOT initialize Julia for standard pulse shapes (constant, ramp, gaussian)
    - Only triggers Julia if the pulse_sequence itself requires it (e.g., complex callable pulses)
    
    Args:
        pulse_sequence: The pulse definition in any supported format
        time_grid: Explicit time points to sample (in μs). 
                  If None, automatically generates grid from pulse duration.
        field: Which field to plot: 'omega' (Rabi frequency) or 'delta' (detuning).
              Ignored for dict/AST inputs that don't have separate omega/delta.
        atom_index: For local addressing, specify the atom index (0-based).
                   If None, plots global pulse.
        ax: Matplotlib axes to plot on. If None, creates new figure.
        num_samples: Number of sample points if time_grid is auto-generated.
        title: Custom plot title. If None, uses default.
        
    Returns:
        Tuple of (Axes, ndarray):
        - Axes: The matplotlib Axes object
        - ndarray: Sampled y-values at each time point
        
    Raises:
        ValueError: If pulse_sequence type cannot be handled or time_grid invalid
        
    Example:
        >>> from sagittarius.viz import plot_pulse_waveform
        >>> import numpy as np
        >>> 
        >>> # Global constant pulse
        >>> ax, omega_vals = plot_pulse_waveform(2.0, duration=5.0, field='omega')
        >>> 
        >>> # Dictionary format - ramp pulse
        >>> pulse_dict = {'type': 'ramp', 'initial': 0, 'final': 3, 'duration': 5}
        >>> ax, vals = plot_pulse_waveform(pulse_dict, field='omega')
        >>> 
        >>> # Local pulse for specific atom
        >>> def local_omega(t, idx): return 2.0 + 0.5 * idx
        >>> ax, vals = plot_pulse_waveform(local_omega, duration=5.0, atom_index=2)
        >>> 
        >>> # Custom time grid
        >>> times = np.linspace(0, 10, 500)
        >>> ax, vals = plot_pulse_waveform(pulse, time_grid=times, field='delta')
        >>> 
        >>> # Gaussian pulse
        >>> gaussian = {'type': 'gaussian', 'amplitude': 3.0, 'sigma': 1.0, 'center': 2.5}
        >>> ax, vals = plot_pulse_waveform(gaussian, duration=5.0)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
    
    # Determine time grid
    if time_grid is None:
        # Try to get duration from various sources
        t_max = None
        
        if hasattr(pulse_sequence, 'duration'):
            t_max = float(pulse_sequence.duration)
        elif isinstance(pulse_sequence, dict) and 'duration' in pulse_sequence:
            t_max = float(pulse_sequence['duration'])
        elif isinstance(pulse_sequence, dict) and pulse_sequence.get('type') == 'piecewise':
            # Calculate total duration from piecewise pulses
            pulses = pulse_sequence.get('pulses', [])
            t_max = sum(p.get('duration', 0.0) for p in pulses)
        elif hasattr(pulse_sequence, '__class__'):
            node_type = pulse_sequence.__class__.__name__.lower()
            if 'piecewise' in node_type and hasattr(pulse_sequence, 'pulses'):
                t_max = sum(getattr(p, 'duration', 0.0) for p in pulse_sequence.pulses)
            elif hasattr(pulse_sequence, 'duration'):
                t_max = float(pulse_sequence.duration)
        
        if t_max is None or t_max <= 0:
            raise ValueError(
                "Cannot determine time grid from pulse_sequence. "
                "Either provide explicit time_grid or ensure pulse has .duration attribute."
            )
        
        time_grid = np.linspace(0, t_max, num_samples)
    
    # Validate time grid
    if len(time_grid) < 2:
        raise ValueError("time_grid must have at least 2 points")
    
    # Sample the waveform
    y_values = sample_pulse_waveform(pulse_sequence, time_grid, field, atom_index)
    
    # Plot
    label_parts = [field.upper()]
    if atom_index is not None:
        label_parts.append(f"atom {atom_index}")
    
    ax.plot(time_grid, y_values, 'b-', linewidth=2, label=' - '.join(label_parts))
    ax.fill_between(time_grid, y_values, alpha=0.1, color='blue')
    
    # Labels and formatting
    ax.set_xlabel("Time (μs)", fontsize=11)
    
    if field == 'omega':
        ax.set_ylabel("Ω (rad/μs)", fontsize=11)
        ylabel_full = "Rabi Frequency Ω (rad/μs)"
    else:
        ax.set_ylabel("Δ (rad/μs)", fontsize=11)
        ylabel_full = "Detuning Δ (rad/μs)"
    
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')
    else:
        ax.set_title(ylabel_full, fontsize=12, fontweight='bold')
    
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # Add zero line for reference
    ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
    
    return ax, y_values


def plot_pulse_both_fields(
    pulse_sequence,
    time_grid: Optional[np.ndarray] = None,
    atom_index: Optional[int] = None,
    ax: Optional[Axes] = None,
    num_samples: int = 200,
) -> tuple:
    """
    Plot both omega and delta waveforms on the same axes.
    
    Convenience function for comparing Rabi frequency and detuning profiles.
    Supports the same input formats as plot_pulse_waveform.
    
    Args:
        pulse_sequence: The pulse definition in any supported format
        time_grid: Time points to sample. Auto-generated if None.
        atom_index: Atom index for local addressing (0-based).
        ax: Matplotlib axes. Creates new if None.
        num_samples: Number of samples for auto-generated grid.
        
    Returns:
        Tuple of (Axes, omega_vals, delta_vals):
        - Axes: The matplotlib Axes object
        - omega_vals: Sampled omega values
        - delta_vals: Sampled delta values
        
    Raises:
        ValueError: If time_grid cannot be determined or pulse lacks required fields
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    # Determine time grid
    if time_grid is None:
        t_max = None
        
        if hasattr(pulse_sequence, 'duration'):
            t_max = float(pulse_sequence.duration)
        elif isinstance(pulse_sequence, dict) and 'duration' in pulse_sequence:
            t_max = float(pulse_sequence['duration'])
        elif isinstance(pulse_sequence, dict) and pulse_sequence.get('type') == 'piecewise':
            pulses = pulse_sequence.get('pulses', [])
            t_max = sum(p.get('duration', 0.0) for p in pulses)
        elif hasattr(pulse_sequence, '__class__'):
            node_type = pulse_sequence.__class__.__name__.lower()
            if 'piecewise' in node_type and hasattr(pulse_sequence, 'pulses'):
                t_max = sum(getattr(p, 'duration', 0.0) for p in pulse_sequence.pulses)
            elif hasattr(pulse_sequence, 'duration'):
                t_max = float(pulse_sequence.duration)
        
        if t_max is None or t_max <= 0:
            raise ValueError("Cannot determine time grid. Provide explicit time_grid.")
        
        time_grid = np.linspace(0, t_max, num_samples)
    
    # Sample both fields
    omega_vals = sample_pulse_waveform(pulse_sequence, time_grid, 'omega', atom_index)
    delta_vals = sample_pulse_waveform(pulse_sequence, time_grid, 'delta', atom_index)
    
    # Plot both
    ax.plot(time_grid, omega_vals, 'b-', linewidth=2, label='Ω (Rabi)')
    ax.fill_between(time_grid, omega_vals, alpha=0.1, color='blue')
    
    ax.plot(time_grid, delta_vals, 'r-', linewidth=2, label='Δ (Detuning)')
    ax.fill_between(time_grid, delta_vals, alpha=0.1, color='red')
    
    ax.set_xlabel("Time (μs)", fontsize=11)
    ax.set_ylabel("Amplitude (rad/μs)", fontsize=11)
    ax.set_title("Pulse Waveforms: Ω and Δ", fontsize=12, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
    
    return ax, omega_vals, delta_vals
