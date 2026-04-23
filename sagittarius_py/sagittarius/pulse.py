from juliacall import Main as jl
import sys

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
    def __init__(self, value, duration):
        self.value = float(value)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        return sgr.ConstantPulse(self.value, self.duration)

class Ramp(PulseNode):
    def __init__(self, start_val, end_val, duration):
        self.start_val = float(start_val)
        self.end_val = float(end_val)
        self.duration = float(duration)
        
    @property
    def jl_obj(self):
        return sgr.RampPulse(self.start_val, self.end_val, self.duration)

class Piecewise(PulseNode):
    def __init__(self, pulses):
        self.pulses = pulses
        
    @property
    def jl_obj(self):
        # Convert to a Julia Vector of PulseNode
        jl_pulses = jl.Vector[sgr.PulseNode]([p.jl_obj for p in self.pulses])
        return sgr.PiecewisePulse(jl_pulses)

def compile_pulse(pulse: PulseNode):
    """Compiles a Python Pulse AST into a Julia callable function."""
    return sgr.compile_pulse(pulse.jl_obj)
