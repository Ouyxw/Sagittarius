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
