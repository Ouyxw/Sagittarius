from juliacall import Main as jl
from typing import List, Optional

# Ensure Sagittarius is loaded in Main before accessing sgr
try:
    sgr = jl.Sagittarius
except AttributeError:
    # If not loaded yet (e.g. imported directly), we fall back to api.py's loading
    from .api import sgr

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
        return sgr.ConstantPulse(self.value, self.duration)

class Ramp(PulseNode):
    def __init__(self, start_val: float, end_val: float, duration: float):
        self.start_val = float(start_val)
        self.end_val = float(end_val)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        return sgr.RampPulse(self.start_val, self.end_val, self.duration)

class Piecewise(PulseNode):
    def __init__(self, pulses: List[PulseNode]):
        self.pulses = pulses
        
    @property
    def jl_obj(self):
        # Convert to a Julia Vector of PulseNode
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
        return sgr.GaussianPulse(self.amplitude, self.sigma, self.mu, self.duration)

class Blackman(PulseNode):
    def __init__(self, amplitude: float, duration: float):
        self.amplitude = float(amplitude)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        return sgr.BlackmanPulse(self.amplitude, self.duration)

class Sinc(PulseNode):
    def __init__(self, amplitude: float, width: float, duration: float):
        self.amplitude = float(amplitude)
        self.width = float(width)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        return sgr.SincPulse(self.amplitude, self.width, self.duration)

class SinSquared(PulseNode):
    def __init__(self, amplitude: float, duration: float):
        self.amplitude = float(amplitude)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        return sgr.SinSquaredPulse(self.amplitude, self.duration)

class Pulse:
    """Factory class for all pulse forms used in cold atom experiments."""
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
    return sgr.compile_pulse(pulse.jl_obj)

def is_pulse(obj):
    return isinstance(obj, PulseNode)
