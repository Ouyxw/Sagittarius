module Program

export PulseNode, ConstantPulse, RampPulse, PiecewisePulse, compile_pulse

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

end # module Program
