import importlib.util
import json
from pathlib import Path

from sagittarius import BENCHMARK_ARTIFACT_SCHEMA_VERSION, PulseSequence, Register
from sagittarius.ablation import ABLATION_BENCHMARK_MODES, benchmark_ablation_modes


def _load_benchmark_script():
    script_path = Path(__file__).parent / "test_performance" / "benchmark_ablation.py"
    spec = importlib.util.spec_from_file_location("benchmark_ablation_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_ablation_mode_contract_lists_required_execution_paths():
    modes = [item["mode"] for item in ABLATION_BENCHMARK_MODES]

    assert modes == [
        "full_dense",
        "full_sparse",
        "reduced_matrix_free",
        "reduced_sparse",
        "reduced_sparse_gpu_cached",
    ]


def test_benchmark_ablation_modes_records_cpu_paths_and_gpu_skip():
    register = Register.chain(4, spacing=0.6, C6=10.0)
    sequence = PulseSequence(omega=0.5, delta=[0.0, 0.1, -0.1, 0.2])

    rows, run_manifests = benchmark_ablation_modes(
        register,
        sequence,
        blockade_radius=0.8,
        repeats=3,
        warmups=1,
        include_gpu=False,
    )

    by_mode = {row["mode"]: row for row in rows}
    assert set(by_mode) == {item["mode"] for item in ABLATION_BENCHMARK_MODES}
    assert by_mode["full_dense"]["status"] == "ok"
    assert by_mode["full_sparse"]["status"] == "ok"
    assert by_mode["full_dense"]["reference_relative_error"] < 1e-12
    assert by_mode["full_sparse"]["reference_relative_error"] < 1e-12
    assert by_mode["reduced_matrix_free"]["status"] == "ok"
    assert by_mode["reduced_sparse"]["status"] == "ok"
    assert by_mode["reduced_sparse_gpu_cached"]["status"] == "skipped"
    assert by_mode["reduced_matrix_free"]["reference_error"] < 1e-10
    assert by_mode["reduced_sparse"]["reference_error"] < 1e-10
    assert run_manifests == []


def test_ablation_benchmark_script_writes_artifact(tmp_path):
    paths = _load_benchmark_script().benchmark_ablation(
        atom_count=4,
        spacing=0.6,
        blockade_radius=0.8,
        repeats=2,
        include_gpu=False,
        output_dir=tmp_path,
    )

    with open(paths["json"], encoding="utf-8") as fh:
        payload = json.load(fh)

    assert payload["schema_version"] == BENCHMARK_ARTIFACT_SCHEMA_VERSION
    assert payload["parameters"]["include_gpu"] is False
    assert {row["mode"] for row in payload["timings"]} == {item["mode"] for item in ABLATION_BENCHMARK_MODES}
    assert "reduced_sparse_gpu_cached" in payload["markdown_table"]


def test_fixed_input_batch_never_composes_hamiltonian():
    import numpy as np
    from sagittarius.ablation import _time_repeated_matvec
    state = np.array([1., 0.], dtype=complex)
    seen = []
    def apply(vector):
        seen.append(vector.copy())
        return 1000 * vector
    _, output = _time_repeated_matvec(apply, state, repeats=50, warmups=2)
    assert len(seen) == 52
    assert all(np.array_equal(vector, state) for vector in seen)
    assert np.array_equal(output, 1000 * state)


def test_outer_repeats_and_workload_identity_are_explicit():
    from sagittarius.ablation import WORKLOAD_VERSION
    register = Register.chain(4, spacing=2., C6=100.)
    rows, _ = benchmark_ablation_modes(register, PulseSequence(omega=6., delta=.3),
        blockade_radius=3., repeats=7, repeat_count=5, warmups=2)
    for row in rows[:-1]:
        assert row['measurement_status'] == 'passed'
        assert row['workload_version'] == WORKLOAD_VERSION
        assert row['implementation'] == 'Python/NumPy/SciPy'
        assert row['statistics']['eligible'] == 5
        assert len(row['warmups']) == 2
        assert len(row['measurements']) == 5
        assert row['total_time_s'] == row['measurements'][0]['runtime_seconds']
        assert all(r['operation_count'] == 7 for r in row['measurements'])
        assert all(r['time_per_operation_s'] == r['runtime_seconds'] / 7 for r in row['measurements'])
        assert abs(row['input']['norm'] - 1.) < 1e-14
    assert rows[0]['input']['sha256'] == rows[1]['input']['sha256']
    assert rows[2]['input']['sha256'] == rows[3]['input']['sha256']


def test_independent_dense_reference_detects_shared_full_builder_bug(monkeypatch):
    import numpy as np
    import sagittarius.ablation as ablation
    monkeypatch.setattr(ablation, '_dense_hamiltonian_matrix', lambda *args: np.zeros((16, 16), complex))
    rows, _ = benchmark_ablation_modes(Register.chain(4), PulseSequence(omega=1., delta=.2),
        blockade_radius=1., repeats=1, repeat_count=1, modes=['full_dense', 'full_sparse'])
    assert all(r['status'] == 'failed' for r in rows)
    assert all(r['failure']['code'] == 'BENCHMARK_REFERENCE_MISMATCH' for r in rows)
    assert all(r['statistics']['eligible'] == 0 for r in rows)


def test_nonfinite_measured_output_is_retained_and_ineligible(monkeypatch, tmp_path):
    import numpy as np
    import sagittarius.ablation as ablation
    calls = 0
    def corrupt(register, omega, delta, basis):
        def apply(vector):
            nonlocal calls
            calls += 1
            return ablation.independent_reference(register, omega, delta, basis, vector,
                reduced=True, radius=3.)[0] if calls == 1 else np.full_like(vector, np.nan)
        return apply
    monkeypatch.setattr(ablation, '_reduced_matrix_free_callable', corrupt)
    rows, _ = benchmark_ablation_modes(Register.chain(4, spacing=2.), PulseSequence(omega=1., delta=0.),
        blockade_radius=3., repeats=1, repeat_count=2, warmups=0, modes=['reduced_matrix_free'], directory=tmp_path)
    row = rows[0]
    assert row['status'] == 'failed'
    assert row['measurements'][0]['finite'] is False
    assert row['measurements'][0]['eligible'] is False
    assert row['statistics']['completed'] == 1 and row['statistics']['eligible'] == 0
    assert np.isnan(np.load(row['measurements'][0]['artifacts']['output_array'])).all()


def test_full_guard_and_memory_preflight_do_not_construct_operator(monkeypatch):
    import sagittarius.ablation as ablation
    def forbidden(*args):
        raise RuntimeError('operator must not be constructed')
    monkeypatch.setattr(ablation, '_dense_hamiltonian_matrix', forbidden)
    monkeypatch.setattr(ablation, '_reduced_hamiltonian_matrix', forbidden)
    rows, _ = benchmark_ablation_modes(Register.chain(4), PulseSequence(omega=1., delta=0.),
        blockade_radius=1., repeats=1, repeat_count=1, max_full_dim=1, memory_limit_mb=1)
    assert all(r['status'] == 'skipped' for r in rows)
    assert 'max_full_dim' in rows[0]['reason']
    assert 'memory budget' in rows[3]['reason']


def test_cuda_requires_both_opt_ins_before_diagnostics(monkeypatch):
    import sagittarius.ablation as ablation
    monkeypatch.delenv('SAGITTARIUS_ENABLE_GPU_TESTS', raising=False)
    monkeypatch.setattr(ablation, 'doctor', lambda **kwargs: (_ for _ in ()).throw(RuntimeError('must not run')))
    rows, _ = benchmark_ablation_modes(Register.chain(4), PulseSequence(omega=1., delta=0.),
        blockade_radius=1., include_gpu=True, modes=['reduced_sparse_gpu_cached'])
    assert rows[0]['status'] == 'skipped'


def test_attempted_cuda_doctor_failure_is_failed(monkeypatch):
    import sagittarius.ablation as ablation
    monkeypatch.setenv('SAGITTARIUS_ENABLE_GPU_TESTS', '1')
    monkeypatch.setattr(ablation, 'doctor', lambda **kwargs: {'available': False})
    rows, _ = benchmark_ablation_modes(Register.chain(4), PulseSequence(omega=1., delta=0.),
        blockade_radius=1., include_gpu=True, modes=['reduced_sparse_gpu_cached'])
    assert rows[0]['status'] == 'failed'
    assert 'diagnostics' in rows[0]['reason']


def test_large_reference_action_matches_small_independent_dense():
    import numpy as np
    from sagittarius.ablation import independent_reference, _seeded_state
    # The N=9 analytic branch is tested against a direct full-space Kronecker reference.
    n = 9
    register = Register.chain(n, spacing=2., C6=100.)
    initial = _seeded_state(2**n, 1234)
    omega, delta = list(np.linspace(.2, .8, n)), list(np.linspace(-.3, .4, n))
    actual, kind = independent_reference(register, omega, delta, list(range(2**n)), initial, reduced=False, radius=0.)
    def local(op, atom):
        out = np.ones((1, 1))
        for bit in reversed(range(n)):
            out = np.kron(out, op if bit == atom else np.eye(2))
        return out
    populations = [local(np.diag([0., 1.]), i) for i in range(n)]
    full = sum(omega[i]/2 * local(np.array([[0., 1.], [1., 0.]]), i) - delta[i]*populations[i] for i in range(n))
    for i in range(n):
        for j in range(i+1, n):
            full += 100. / (2.*(j-i))**6 * populations[i]*populations[j]
    assert kind == 'independent_enumerated_bit_transition_action'
    assert np.allclose(actual, full @ initial, rtol=1e-13, atol=1e-13)


def test_reference_rejects_wrong_basis_order():
    import numpy as np
    import pytest
    from sagittarius.ablation import independent_reference
    with pytest.raises(AssertionError, match='Basis'):
        independent_reference(Register.chain(2), [1., 1.], [0., 0.], [0, 2, 1, 3],
                              np.ones(4)/2, reduced=False, radius=0.)


def test_campaign_matrix_and_failure_retention():
    from sagittarius.ablation_benchmark import scenarios, campaign_row
    matrix = scenarios()
    assert len(matrix) == 25
    assert sum(s['required'] for s in matrix) == 12
    scenario = next(s for s in matrix if s['N'] == 20 and s['mode'] == 'reduced_sparse')
    assert scenario['basis_size'] == 17711
    assert scenario['estimated_peak_bytes'] > 16*17711**2
    settings = {'measurement': {'repeat_count': 5, 'repeats': 50}, 'timeout_seconds': 1., 'memory_limit_bytes': 123}
    partial = {'row': {'measurements': [{'row_id': 'partial', 'eligible': True, 'runtime_seconds': .2}]}}
    for supervision, expected in [({'reason': 'timeout'}, 'incomplete'), ({'reason': 'memory'}, 'failed'), ({'returncode': -9}, 'failed'), ({'reason': 'interrupted'}, 'incomplete')]:
        row = campaign_row(scenario, settings, partial, supervision)
        assert row['status'] == expected
        assert row['metrics']['statistics']['eligible'] == 1
        assert row['failure']['limits']['memory_limit_bytes'] == 123


def test_ablation_rejects_invalid_counts_and_limits():
    import pytest
    for options in ({'repeats': 0}, {'repeat_count': 0}, {'warmups': -1}, {'seed': True}, {'memory_limit_mb': float('inf')}, {'full_rtol': float('nan')}):
        with pytest.raises(ValueError):
            benchmark_ablation_modes(Register.chain(2), PulseSequence(omega=1., delta=0.), blockade_radius=1., **options)


def test_campaign_supervisor_retains_timeout_and_config_before_launch(monkeypatch, tmp_path):
    import sagittarius.ablation_benchmark as campaign
    def timeout(command, **kwargs):
        config = json.loads(Path(command[-2]).read_text())
        assert config['scenario']['N'] == 4
        assert config['config_sha256']
        assert (tmp_path / 'campaign.json').exists()
        return {'reason': 'timeout', 'returncode': -9, 'sampled_peak_bytes': 100}
    monkeypatch.setattr(campaign, 'supervise', timeout)
    paths = campaign.benchmark_ablation(sizes=[4], output_dir=tmp_path)
    rows = json.loads(Path(paths['json']).read_text())['timings']
    assert [r['status'] for r in rows] == ['incomplete']*4 + ['skipped']
    assert all(r['failure']['code'] == 'BENCHMARK_TIMEOUT' for r in rows[:4])
    assert all(Path(r['artifacts']['config']).is_file() for r in rows)
    import pytest
    with pytest.raises(FileExistsError):
        campaign.benchmark_ablation(sizes=[4], output_dir=tmp_path)


def test_short_campaign_is_diagnostic_and_saved_output_audit_detects_tampering(tmp_path):
    import numpy as np
    from sagittarius.ablation_benchmark import benchmark_ablation
    paths = benchmark_ablation(sizes=[4], repeats=2, repeat_count=1, warmups=1, output_dir=tmp_path)
    artifact = json.loads(Path(paths['json']).read_text())
    assert [r['status'] for r in artifact['timings']] == ['incomplete']*4 + ['skipped']
    audit_path = Path(__file__).resolve().parents[2] / 'scripts' / 'audit_ablation_campaign.py'
    spec = importlib.util.spec_from_file_location('audit_ablation', audit_path)
    audit_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit_module)
    assert audit_module.audit(tmp_path)['checked_cpu_outputs'] == 4
    output = Path(artifact['timings'][0]['metrics']['measurements'][0]['artifacts']['output_array'])
    np.save(output, np.zeros(16, complex))
    import pytest
    with pytest.raises(ValueError, match='saved output'):
        audit_module.audit(tmp_path)


def test_reduced_analytic_action_matches_projected_full_dense_at_nine():
    import numpy as np
    from sagittarius.ablation import independent_reference, _seeded_state
    from sagittarius.api import _reduced_basis_python, _dense_hamiltonian_matrix
    register = Register.chain(9, spacing=2., C6=100.)
    basis = _reduced_basis_python(register, 3.)
    initial = _seeded_state(len(basis), 1234)
    omega, delta = list(np.linspace(.2, .8, 9)), list(np.linspace(-.3, .4, 9))
    actual, _ = independent_reference(register, omega, delta, basis, initial, reduced=True, radius=3.)
    # Complement the independent Kronecker action test with projection/mapping
    # verification of the large-fixture reference branch.
    projected = _dense_hamiltonian_matrix(register, omega, delta)[np.ix_(basis, basis)]
    assert np.allclose(actual, projected @ initial, rtol=1e-13, atol=1e-13)
