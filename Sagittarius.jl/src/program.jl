module Program

export PulseNode, ConstantPulse, RampPulse, PiecewisePulse, GaussianPulse, BlackmanPulse, SincPulse, SinSquaredPulse, compile_pulse, create_vec_func, create_const_vec_func

abstract type PulseNode end

struct ConstantPulse <: PulseNode
    value::Float64
    duration::Float64
end

struct RampPulse <: PulseNode
    start_val::Float64
    end_val::Float64
    duration::Float64
end

struct PiecewisePulse <: PulseNode
    pulses::Vector{PulseNode}
end

struct GaussianPulse <: PulseNode
    amplitude::Float64
    sigma::Float64
    mu::Float64
    duration::Float64
end

struct BlackmanPulse <: PulseNode
    amplitude::Float64
    duration::Float64
end

struct SincPulse <: PulseNode
    amplitude::Float64
    width::Float64
    duration::Float64
end

struct SinSquaredPulse <: PulseNode
    amplitude::Float64
    duration::Float64
end

"""
    compile_pulse(pulse::PulseNode)

Compiles a PulseNode AST into a fast callable function `f(t)`.
Returns a function that takes time `t` and returns the pulse value at that time.
"""
function compile_pulse(pulse::ConstantPulse)
    v = pulse.value
    d = pulse.duration
    return t -> (0 <= t <= d) ? v : 0.0
end

function compile_pulse(pulse::RampPulse)
    v0 = pulse.start_val
    v1 = pulse.end_val
    d = pulse.duration
    rate = (v1 - v0) / d
    return t -> (0 <= t <= d) ? (v0 + rate * t) : 0.0
end

function compile_pulse(pulse::GaussianPulse)
    a = pulse.amplitude
    s = pulse.sigma
    m = pulse.mu
    d = pulse.duration
    return t -> (0 <= t <= d) ? a * exp(-(t - m)^2 / (2 * s^2)) : 0.0
end

function compile_pulse(pulse::BlackmanPulse)
    a = pulse.amplitude
    d = pulse.duration
    return t -> (0 <= t <= d) ? a * (0.42 - 0.5 * cos(2π * t / d) + 0.08 * cos(4π * t / d)) : 0.0
end

function compile_pulse(pulse::SincPulse)
    a = pulse.amplitude
    w = pulse.width
    d = pulse.duration
    mid = d / 2.0
    return t -> begin
        if 0 <= t <= d
            x = (t - mid) / w
            return x == 0 ? a : a * sin(π * x) / (π * x)
        end
        return 0.0
    end
end

function compile_pulse(pulse::SinSquaredPulse)
    a = pulse.amplitude
    d = pulse.duration
    return t -> (0 <= t <= d) ? a * sin(π * t / d)^2 : 0.0
end

function compile_pulse(seq::PiecewisePulse)
    # Precompute start and end times for each pulse to avoid loop overhead during integration
    N = length(seq.pulses)
    start_times = zeros(N)
    end_times = zeros(N)
    funcs = []
    
    current_time = 0.0
    for i in 1:N
        p = seq.pulses[i]
        start_times[i] = current_time
        current_time += p.duration
        end_times[i] = current_time
        push!(funcs, compile_pulse(p))
    end
    
    # The compiled function
    return t -> begin
        for i in 1:N
            if start_times[i] <= t <= end_times[i]
                # Shift time to the local frame of the pulse
                return funcs[i](t - start_times[i])
            end
        end
        return 0.0
    end
end

"""
    create_vec_func(funcs)
Returns a function `t -> Vector{Float64}` by evaluating each function in `funcs`.
"""
function create_vec_func(funcs)
    return t -> Float64[f(t) for f in funcs]
end

"""
    create_const_vec_func(v, N)
Returns a function `t -> Vector{Float64}` that always returns a vector of length `N` with value `v`.
"""
function create_const_vec_func(v, N)
    return t -> fill(Float64(v), N)
end

end # module Program
