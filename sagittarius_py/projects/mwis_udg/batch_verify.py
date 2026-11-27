"""Seeded, exact-baseline verification for weighted MWIS unit-disk graphs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
import warnings
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np

try:
    from mwis_solver import MWIS_AQC
    from solution_verify import calculate_weight, verify_independent_set
except ImportError:
    from .mwis_solver import MWIS_AQC
    from .solution_verify import calculate_weight, verify_independent_set

MWIS_BATCH_SCHEMA_VERSION = "mwis-batch-verification/v1"
MWIS_BATCH_ARTIFACT_TYPE = "sagittarius.mwis_batch_verification"


@dataclass(frozen=True)
class MWISInstanceResult:
    instance_id: int
    seed: int
    n_nodes: int
    density: float
    avg_degree: float
    n_edges: int
    ilp_status: str
    exact_weight: float
    exact_bitstring: List[int]
    exact_solve_seconds: float
    aqc_weight: Optional[float]
    aqc_bitstring: Optional[List[int]]
    aqc_solve_seconds: Optional[float]
    aqc_valid_independent_set: Optional[bool]
    exact_match: Optional[bool]
    approximation_ratio: Optional[float]
    optimal_probability: Optional[float] = None


@dataclass(frozen=True)
class MWISBatchReport:
    schema_version: str
    artifact_type: str
    seed: int
    blockade_radius: float
    n_instances: int
    n_nodes: int
    densities: List[float]
    duration: float
    success_count: int
    valid_count: int
    mean_approximation_ratio: float
    mean_optimal_probability: Optional[float]
    instances: List[MWISInstanceResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_random_udg(
    n_nodes: int,
    *,
    density: float = 0.5,
    blockade_radius: float = 1.0,
    weight_range: Tuple[float, float] = (1.0, 1.5),
    seed: Optional[int] = None,
) -> nx.Graph:
    """Generate a deterministic weighted unit-disk graph.

    ``density`` controls spatial point density; it does not promise an exact
    edge density. The seed and graph metrics are retained by the batch report.
    """
    if n_nodes <= 0:
        raise ValueError("n_nodes must be positive")
    if density <= 0:
        raise ValueError("density must be positive")
    if blockade_radius <= 0:
        raise ValueError("blockade_radius must be positive")
    low, high = weight_range
    if low <= 0 or high < low:
        raise ValueError("weight_range must be positive and ordered")

    rng = np.random.default_rng(seed)
    side = float(np.sqrt(n_nodes / density))
    graph = nx.Graph()
    for node in range(n_nodes):
        graph.add_node(
            node,
            pos=(float(rng.uniform(0.0, side)), float(rng.uniform(0.0, side))),
            weight=float(rng.uniform(low, high)),
        )
    nodes = list(graph.nodes())
    for index, first in enumerate(nodes):
        first_x, first_y = graph.nodes[first]["pos"]
        for second in nodes[index + 1 :]:
            second_x, second_y = graph.nodes[second]["pos"]
            if float(np.hypot(first_x - second_x, first_y - second_y)) <= blockade_radius:
                graph.add_edge(first, second)
    return graph


def solve_mwis_ilp(graph: nx.Graph) -> Tuple[List[int], float, str]:
    """Solve weighted MWIS exactly using PuLP/CBC."""
    try:
        import pulp
    except ImportError as exc:  # pragma: no cover - declared project dependency
        raise RuntimeError("PuLP is required for MWIS ILP verification") from exc

    nodes = list(graph.nodes())
    weights = {node: float(graph.nodes[node].get("weight", 1.0)) for node in nodes}
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="pulp.*")
        problem = pulp.LpProblem("Sagittarius_MWIS_Verification", pulp.LpMaximize)
        variables = {node: pulp.LpVariable(f"x_{node}", cat="Binary") for node in nodes}
        problem += pulp.lpSum(weights[node] * variables[node] for node in nodes)
        for first, second in graph.edges():
            problem += variables[first] + variables[second] <= 1
        problem.solve(pulp.PULP_CBC_CMD(msg=False))
        status = str(pulp.LpStatus[problem.status])
        if status != "Optimal":
            raise RuntimeError(f"MWIS ILP did not find an optimal solution: {status}")
        bitstring = [
            1 if float(pulp.value(variables[node]) or 0.0) > 0.5 else 0
            for node in nodes
        ]
    return bitstring, calculate_weight(graph, np.asarray(bitstring, dtype=int)), status


def _coerce_bitstring(bitstring: Sequence[int], n_nodes: int) -> List[int]:
    values = [int(round(float(value))) for value in bitstring]
    if len(values) != n_nodes:
        raise ValueError(f"AQC solver returned {len(values)} bits for {n_nodes} nodes")
    if any(value not in (0, 1) for value in values):
        raise ValueError("AQC solver returned a non-binary bitstring")
    return values


def _optimal_probability(
    graph: nx.Graph,
    probabilities: Optional[Sequence[float]],
    basis: Optional[Sequence[int]],
    exact_weight: float,
    *,
    tolerance: float,
) -> Optional[float]:
    if probabilities is None or basis is None:
        return None
    if len(probabilities) != len(basis):
        raise ValueError("AQC probabilities and basis must have the same length")
    total = 0.0
    for probability, basis_value in zip(probabilities, basis):
        bitstring = np.asarray(
            [(int(basis_value) >> bit) & 1 for bit in range(graph.number_of_nodes())],
            dtype=int,
        )
        if verify_independent_set(graph, bitstring) and calculate_weight(graph, bitstring) >= exact_weight - tolerance:
            total += float(probability)
    return total


def _run_solver(
    graph: nx.Graph,
    solver_factory: Callable[..., Any],
    *,
    blockade_radius: float,
    duration: float,
    config_factory: Optional[Callable[[Any], Any]],
) -> Tuple[List[int], Optional[Sequence[float]], Optional[Sequence[int]]]:
    solver = solver_factory(graph, blockade_radius=blockade_radius)
    config = config_factory(solver) if config_factory is not None else None
    if hasattr(solver, "solve_full"):
        bitstring, probabilities, basis = solver.solve_full(config=config, duration=duration)
        return list(bitstring), probabilities, basis
    bitstring = solver.solve(config=config, duration=duration) if hasattr(solver, "solve") else solver(graph)
    return list(bitstring), None, None


def verify_mwis_batch(
    *,
    n_instances: int = 8,
    n_nodes: int = 8,
    densities: Iterable[float] = (0.4, 0.6),
    seed: int = 0,
    blockade_radius: float = 1.0,
    duration: float = 4.0,
    weight_range: Tuple[float, float] = (1.0, 1.5),
    solver_factory: Callable[..., Any] = MWIS_AQC,
    config_factory: Optional[Callable[[Any], Any]] = None,
    tolerance: float = 1e-6,
) -> MWISBatchReport:
    """Compare a seeded AQC (or injected) solver against exact weighted MWIS."""
    if n_instances <= 0:
        raise ValueError("n_instances must be positive")
    if n_nodes <= 0:
        raise ValueError("n_nodes must be positive")
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    density_values = [float(value) for value in densities]
    if not density_values or any(value <= 0 for value in density_values):
        raise ValueError("densities must contain positive values")

    master_rng = np.random.default_rng(seed)
    instances: list[MWISInstanceResult] = []
    for instance_id in range(n_instances):
        instance_seed = int(master_rng.integers(0, np.iinfo(np.int32).max))
        density = density_values[instance_id % len(density_values)]
        graph = generate_random_udg(
            n_nodes,
            density=density,
            blockade_radius=blockade_radius,
            weight_range=weight_range,
            seed=instance_seed,
        )
        exact_start = time.perf_counter()
        exact_bitstring, exact_weight, ilp_status = solve_mwis_ilp(graph)
        exact_seconds = time.perf_counter() - exact_start

        aqc_start = time.perf_counter()
        aqc_raw, probabilities, basis = _run_solver(
            graph,
            solver_factory,
            blockade_radius=blockade_radius,
            duration=duration,
            config_factory=config_factory,
        )
        aqc_seconds = time.perf_counter() - aqc_start
        aqc_bitstring = _coerce_bitstring(aqc_raw, n_nodes)
        aqc_array = np.asarray(aqc_bitstring, dtype=int)
        aqc_valid = verify_independent_set(graph, aqc_array)
        aqc_weight = calculate_weight(graph, aqc_array) if aqc_valid else 0.0
        approximation_ratio = aqc_weight / exact_weight if exact_weight > tolerance else 1.0
        exact_match = aqc_valid and aqc_weight >= exact_weight - tolerance
        average_degree = float(np.mean([degree for _, degree in graph.degree()]))
        instances.append(
            MWISInstanceResult(
                instance_id=instance_id,
                seed=instance_seed,
                n_nodes=n_nodes,
                density=density,
                avg_degree=average_degree,
                n_edges=graph.number_of_edges(),
                ilp_status=ilp_status,
                exact_weight=exact_weight,
                exact_bitstring=exact_bitstring,
                exact_solve_seconds=exact_seconds,
                aqc_weight=aqc_weight,
                aqc_bitstring=aqc_bitstring,
                aqc_solve_seconds=aqc_seconds,
                aqc_valid_independent_set=aqc_valid,
                exact_match=exact_match,
                approximation_ratio=approximation_ratio,
                optimal_probability=_optimal_probability(
                    graph,
                    probabilities,
                    basis,
                    exact_weight,
                    tolerance=tolerance,
                ),
            )
        )

    ratios = [result.approximation_ratio for result in instances if result.approximation_ratio is not None]
    optimal_probabilities = [result.optimal_probability for result in instances if result.optimal_probability is not None]
    return MWISBatchReport(
        schema_version=MWIS_BATCH_SCHEMA_VERSION,
        artifact_type=MWIS_BATCH_ARTIFACT_TYPE,
        seed=seed,
        blockade_radius=blockade_radius,
        n_instances=n_instances,
        n_nodes=n_nodes,
        densities=density_values,
        duration=duration,
        success_count=sum(result.exact_match is True for result in instances),
        valid_count=sum(result.aqc_valid_independent_set is True for result in instances),
        mean_approximation_ratio=float(np.mean(ratios)) if ratios else 0.0,
        mean_optimal_probability=float(np.mean(optimal_probabilities)) if optimal_probabilities else None,
        instances=instances,
    )
