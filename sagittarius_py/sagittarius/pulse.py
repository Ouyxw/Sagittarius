from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from .runtime import get_julia



class ExplicitPulse:
    """Base class for explicit pulse addressing wrappers."""


class GlobalPulse(ExplicitPulse):
    """Apply one scalar or PulseNode value to every atom."""

    def __init__(self, value: Any):
        self.value = value


class LocalPulseVector(ExplicitPulse):
    """Apply per-atom pulse values in Register.atoms order or sparse atom-index form."""

    def __init__(self, values: Union[Sequence[Any], Dict[int, Any]]):
        if isinstance(values, dict):
            self.values = values
        elif isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
            self.values = list(values)
        else:
            self.values = values


class CallablePulse(ExplicitPulse):
    """Apply a callable t -> per-atom numeric vector."""

    def __init__(self, func: Callable[[float], Sequence[float]]):
        self.func = func

    def __call__(self, t: float):
        return self.func(t)

class PulseNode:
    """Base class for Pulse AST nodes."""
    @property
    def jl_obj(self):
        raise NotImplementedError

class Constant(PulseNode):
    def __init__(self, value: float, duration: float):
        self.value = float(value)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        _, sgr = get_julia()
        return sgr.ConstantPulse(self.value, self.duration)

class Ramp(PulseNode):
    def __init__(self, start_val: float, end_val: float, duration: float):
        self.start_val = float(start_val)
        self.end_val = float(end_val)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        _, sgr = get_julia()
        return sgr.RampPulse(self.start_val, self.end_val, self.duration)

class Piecewise(PulseNode):
    def __init__(self, pulses: List[PulseNode]):
        self.pulses = pulses
        
    @property
    def jl_obj(self):
        # Convert to a Julia Vector of PulseNode
        jl, sgr = get_julia()
        jl_pulses = jl.Vector[sgr.PulseNode]([p.jl_obj for p in self.pulses])
        return sgr.PiecewisePulse(jl_pulses)

class Gaussian(PulseNode):
    def __init__(self, amplitude: float, sigma: float, duration: float, mu: Optional[float] = None):
        self.amplitude = float(amplitude)
        self.sigma = float(sigma)
        self.duration = float(duration)
        self.mu = float(mu if mu is not None else duration / 2.0)
        
    @property
    def jl_obj(self):
        _, sgr = get_julia()
        return sgr.GaussianPulse(self.amplitude, self.sigma, self.mu, self.duration)

class Blackman(PulseNode):
    def __init__(self, amplitude: float, duration: float):
        self.amplitude = float(amplitude)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        _, sgr = get_julia()
        return sgr.BlackmanPulse(self.amplitude, self.duration)

class Sinc(PulseNode):
    def __init__(self, amplitude: float, width: float, duration: float):
        self.amplitude = float(amplitude)
        self.width = float(width)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        _, sgr = get_julia()
        return sgr.SincPulse(self.amplitude, self.width, self.duration)

class SinSquared(PulseNode):
    def __init__(self, amplitude: float, duration: float):
        self.amplitude = float(amplitude)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        _, sgr = get_julia()
        return sgr.SinSquaredPulse(self.amplitude, self.duration)

class Pulse:
    """Factory class for pulse shapes and explicit addressing wrappers."""

    @staticmethod
    def global_(value: Any) -> GlobalPulse:
        return GlobalPulse(value)

    @staticmethod
    def local(values: Union[Sequence[Any], Dict[int, Any]]) -> LocalPulseVector:
        return LocalPulseVector(values)

    @staticmethod
    def callable(func: Callable[[float], Sequence[float]]) -> CallablePulse:
        return CallablePulse(func)

    @staticmethod
    def constant(value: float, duration: float) -> Constant:
        return Constant(value, duration)
    
    @staticmethod
    def ramp(start: float, end: float, duration: float) -> Ramp:
        return Ramp(start, end, duration)
    
    @staticmethod
    def piecewise(pulses: List[PulseNode]) -> Piecewise:
        return Piecewise(pulses)
    
    @staticmethod
    def gaussian(amplitude: float, sigma: float, duration: float, mu: Optional[float] = None) -> Gaussian:
        return Gaussian(amplitude, sigma, duration, mu)
    
    @staticmethod
    def blackman(amplitude: float, duration: float) -> Blackman:
        return Blackman(amplitude, duration)
    
    @staticmethod
    def sinc(amplitude: float, width: float, duration: float) -> Sinc:
        return Sinc(amplitude, width, duration)

    @staticmethod
    def sin_squared(amplitude: float, duration: float) -> SinSquared:
        return SinSquared(amplitude, duration)

def compile_pulse(pulse: PulseNode):
    """Compiles a Python Pulse AST into a Julia callable function."""
    _, sgr = get_julia()
    return sgr.compile_pulse(pulse.jl_obj)

def is_pulse(obj):
    return isinstance(obj, PulseNode)

def is_explicit_pulse(obj):
    return isinstance(obj, ExplicitPulse)


def dict_to_pulse_node(pulse_dict: Dict[str, Any]) -> 'PulseNode':
    """
    Convert a dictionary pulse definition to a Pulse AST node.
    
    This factory function automatically converts JSON-style dictionary definitions
    into the corresponding Pulse AST nodes (Constant, Ramp, Gaussian, Piecewise, etc.).
    
    Args:
        pulse_dict: Dictionary with 'type' key and pulse-specific parameters
        
    Returns:
        Corresponding PulseNode instance
        
    Raises:
        ValueError: If pulse type is not supported or required parameters are missing
        
    Example:
        >>> from sagittarius.pulse import dict_to_pulse_node
        >>> 
        >>> # Constant pulse
        >>> const = dict_to_pulse_node({'type': 'constant', 'value': 2.0, 'duration': 5.0})
        >>> 
        >>> # Ramp pulse
        >>> ramp = dict_to_pulse_node({
        ...     'type': 'ramp',
        ...     'start_val': 0.0,
        ...     'end_val': 3.0,
        ...     'duration': 5.0
        ... })
        >>> 
        >>> # Gaussian pulse
        >>> gaussian = dict_to_pulse_node({
        ...     'type': 'gaussian',
        ...     'amplitude': 3.0,
        ...     'sigma': 1.0,
        ...     'duration': 5.0,
        ...     'mu': 2.5
        ... })
        >>> 
        >>> # Piecewise pulse
        >>> piecewise = dict_to_pulse_node({
        ...     'type': 'piecewise',
        ...     'pulses': [
        ...         {'type': 'constant', 'value': 2.0, 'duration': 2.0},
        ...         {'type': 'ramp', 'start_val': 2.0, 'end_val': 0.0, 'duration': 3.0}
        ...     ]
        ... })
    """
    if not isinstance(pulse_dict, dict):
        raise TypeError(f"Expected dict, got {type(pulse_dict).__name__}")
    
    pulse_type = pulse_dict.get('type', '').lower()
    
    if not pulse_type:
        raise ValueError("Dictionary must contain 'type' key specifying pulse type")
    
    # Constant pulse
    if pulse_type == 'constant':
        if 'value' not in pulse_dict or 'duration' not in pulse_dict:
            raise ValueError("Constant pulse requires 'value' and 'duration' keys")
        return Constant(
            value=pulse_dict['value'],
            duration=pulse_dict['duration']
        )
    
    # Ramp pulse
    elif pulse_type == 'ramp':
        required = ['start_val', 'end_val', 'duration']
        for key in required:
            if key not in pulse_dict:
                raise ValueError(f"Ramp pulse requires '{key}' key")
        return Ramp(
            start_val=pulse_dict['start_val'],
            end_val=pulse_dict['end_val'],
            duration=pulse_dict['duration']
        )
    
    # Gaussian pulse
    elif pulse_type == 'gaussian':
        required = ['amplitude', 'sigma', 'duration']
        for key in required:
            if key not in pulse_dict:
                raise ValueError(f"Gaussian pulse requires '{key}' key")
        mu = pulse_dict.get('mu', None)
        return Gaussian(
            amplitude=pulse_dict['amplitude'],
            sigma=pulse_dict['sigma'],
            duration=pulse_dict['duration'],
            mu=mu
        )
    
    # Blackman pulse
    elif pulse_type == 'blackman':
        if 'amplitude' not in pulse_dict or 'duration' not in pulse_dict:
            raise ValueError("Blackman pulse requires 'amplitude' and 'duration' keys")
        return Blackman(
            amplitude=pulse_dict['amplitude'],
            duration=pulse_dict['duration']
        )
    
    # Sinc pulse
    elif pulse_type == 'sinc':
        required = ['amplitude', 'width', 'duration']
        for key in required:
            if key not in pulse_dict:
                raise ValueError(f"Sinc pulse requires '{key}' key")
        return Sinc(
            amplitude=pulse_dict['amplitude'],
            width=pulse_dict['width'],
            duration=pulse_dict['duration']
        )
    
    # SinSquared pulse
    elif pulse_type == 'sin_squared':
        if 'amplitude' not in pulse_dict or 'duration' not in pulse_dict:
            raise ValueError("SinSquared pulse requires 'amplitude' and 'duration' keys")
        return SinSquared(
            amplitude=pulse_dict['amplitude'],
            duration=pulse_dict['duration']
        )
    
    # Piecewise pulse (recursive)
    elif pulse_type == 'piecewise':
        if 'pulses' not in pulse_dict:
            raise ValueError("Piecewise pulse requires 'pulses' key containing list of sub-pulses")
        
        pulses_list = pulse_dict['pulses']
        if not isinstance(pulses_list, list):
            raise TypeError("'pulses' must be a list of pulse dictionaries")
        
        # Recursively convert each sub-pulse
        converted_pulses = [dict_to_pulse_node(sub_pulse) for sub_pulse in pulses_list]
        return Piecewise(converted_pulses)
    
    else:
        raise ValueError(
            f"Unsupported pulse type: '{pulse_type}'. "
            f"Supported types: 'constant', 'ramp', 'gaussian', 'blackman', "
            f"'sinc', 'sin_squared', 'piecewise'"
        )


def parse_pulse_config(config: Any) -> Any:
    """
    Parse a pulse configuration that may be a dict, scalar, callable, or PulseNode.
    
    If config is a dictionary, it will be automatically converted to a PulseNode.
    Otherwise, returns the config unchanged.
    
    Args:
        config: Pulse configuration (dict, scalar, callable, or PulseNode)
        
    Returns:
        Parsed pulse object (PulseNode, scalar, callable, or wrapper)
        
    Example:
        >>> from sagittarius.pulse import parse_pulse_config
        >>> 
        >>> # Dictionary auto-conversion
        >>> pulse = parse_pulse_config({
        ...     'type': 'ramp',
        ...     'start_val': 0,
        ...     'end_val': 3,
        ...     'duration': 5
        ... })
        >>> print(type(pulse))  # <class 'sagittarius.pulse.Ramp'>
        >>> 
        >>> # Pass-through for other types
        >>> scalar = parse_pulse_config(2.0)
        >>> assert scalar == 2.0
    """
    if isinstance(config, dict):
        return dict_to_pulse_node(config)
    return config
