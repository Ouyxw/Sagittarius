import dataclasses

import numpy as np

from sagittarius import (
    Atom,
    Pulse,
    PulseSequence,
    Register,
    Simulation,
    SolverConfig,
    validate_run_manifest,
)


PARITY_RTOL = 2e-4
PARITY_ATOL = 2e-5


def _normalized_random_state(dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    state = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    return (state / np.linalg.norm(state)).astype(complex)


def _ground_state(dim: int) -> np.ndarray:
    state = np.zeros(dim, dtype=complex)
    state[0] = 1.0
    return state


def _run_parity_case(register, sequence, config, psi0, t_end, observables):
    cpu_config = dataclasses.replace(config, use_gpu=False)
    gpu_config = dataclasses.replace(config, use_gpu=True, gpu_backend="CUDA")

    cpu_result = Simulation(register, sequence, cpu_config).run(
        psi0,
        0.0,
        t_end,
        observables=observables,
    )

    # conftest already requires initialized CUDA diagnostics. Solver failures
    # after that gate are regressions, including fresh-process lazy imports.
    gpu_result = Simulation(register, sequence, gpu_config).run(
        psi0, 0.0, t_end, observables=observables,
    )

    validate_run_manifest(cpu_result.manifest)
    validate_run_manifest(gpu_result.manifest)
    assert cpu_result.diagnostics["requested_backend"] == "CPU"
    assert gpu_result.diagnostics["requested_backend"] == "CUDA"
    assert gpu_result.diagnostics["simulation"]["use_gpu"] is True

    for name in observables:
        cpu_values = np.asarray(cpu_result.data[name], dtype=float)
        gpu_values = np.asarray(gpu_result.data[name], dtype=float)
        gpu_interp = np.interp(cpu_result.t, gpu_result.t, gpu_values)

        assert np.allclose(cpu_values, gpu_interp, rtol=PARITY_RTOL, atol=PARITY_ATOL), name


def test_gpu_vs_cpu_global_drive_observable_parity():
    register = Register.chain(6, spacing=5.0, C6=80.0)
    sequence = PulseSequence(omega=2 * np.pi * 0.8, delta=2 * np.pi * 0.15)
    config = SolverConfig(reltol=1e-8, abstol=1e-8)

    _run_parity_case(
        register,
        sequence,
        config,
        _ground_state(2 ** len(register.atoms)),
        0.45,
        {"left": 0, "right": len(register.atoms) - 1},
    )


def test_gpu_vs_cpu_local_addressing_parity():
    register = Register([Atom(i * 4.5, 0.25 * (i % 2), 0.0) for i in range(5)], C6=50.0)
    sequence = PulseSequence(
        omega=[
            Pulse.constant(2 * np.pi * 0.7, duration=0.6),
            0.0,
            Pulse.ramp(2 * np.pi * 0.2, 2 * np.pi * 0.9, duration=0.6),
            2 * np.pi * 0.35,
            0.0,
        ],
        delta={0: -0.15, 2: 0.05, 4: 0.25},
    )
    config = SolverConfig(reltol=1e-8, abstol=1e-8)

    _run_parity_case(
        register,
        sequence,
        config,
        _ground_state(2 ** len(register.atoms)),
        0.6,
        {"a0": 0, "a2": 2, "a4": 4},
    )


def test_gpu_vs_cpu_reduced_basis_parity_with_seeded_state():
    register = Register.chain(5, spacing=0.55, C6=25.0)
    sequence = PulseSequence(omega=[0.18, 0.27, 0.21, 0.24, 0.16], delta=[-0.05, 0.0, 0.03, 0.02, -0.01])
    config = SolverConfig(blockade_radius=0.7, reltol=1e-8, abstol=1e-8)
    basis_size = Simulation(register, sequence, config).validate()

    _run_parity_case(
        register,
        sequence,
        config,
        _normalized_random_state(basis_size, seed=90210),
        0.5,
        {"a1": 1, "a3": 3},
    )


def test_gpu_diagonal_observables_match_cpu_at_shared_times():
    register = Register.chain(4, spacing=2., C6=100.)
    sequence = PulseSequence(omega=1.2, delta=-.1)
    config = SolverConfig(reltol=1e-8, abstol=1e-10, saveat=np.linspace(0., .2, 11).tolist())
    observables = {
        'pop0': 0,
        'total': {'type': 'total_rydberg_population'},
        'pair': {'type': 'pair_correlation', 'atoms': [0, 2]},
        'connected': {'type': 'connected_pair_correlation', 'atoms': [0, 2]},
        'z': {'type': 'pauli_z', 'atom': 1},
        'zz': {'type': 'pauli_zz', 'atoms': [0, 2]},
        'parity': {'type': 'parity', 'atoms': [0, 1, 2]},
    }
    _run_parity_case(register, sequence, config, _normalized_random_state(16, 90211), .2, observables)
