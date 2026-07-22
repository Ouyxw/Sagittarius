"""Batch verification for MWIS-on-UDG AQC runs.

The verifier compares Sagittarius AQC outputs against exact ILP solutions on
randomly generated unit-disk graph instances.  The public functions are kept
backend-friendly: tests and offline checks can inject a deterministic solver,
while the default path uses :class:`MWIS_AQC`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
import warnings
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np

try:  # Script execution from this directory.
    from mwis_solver import MWIS_AQC
    from solution_verify import calculate_weight, verify_independent_set
except ImportError:  # Package-style imports in tests or notebooks.
    from .mwis_solver import MWIS_AQC
    from .solution_verify import calculate_weight, verify_independent_set


@dataclass(frozen=True)
class MWISInstanceResult:
    """Verification metrics for one randomized MWIS instance."""

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
    """Aggregate report for a batch of randomized MWIS verifications."""

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
        payload = asdict(self)
        payload["instances"] = [asdict(instance) for instance in self.instances]
        return payload


MWIS_BATCH_SCHEMA_VERSION = "mwis-batch-verification/v1"
MWIS_BATCH_ARTIFACT_TYPE = "sagittarius.mwis_batch_verification"


def generate_random_udg(
    n_nodes: int,
    *,
    density: float = 0.5,
    blockade_radius: float = 1.0,
    weight_range: Tuple[float, float] = (1.0, 1.5),
    seed: Optional[int] = None,
) -> nx.Graph:
    """Generate a deterministic weighted unit-disk graph instance."""
    if n_nodes <= 0:
        raise ValueError("n_nodes must be positive")
    if density <= 0:
        raise ValueError("density must be positive")
    low, high = weight_range
    if low <= 0 or high < low:
        raise ValueError("weight_range must be positive and ordered")

    rng = np.random.default_rng(seed)
    side = float(np.sqrt(n_nodes / density))
    graph = nx.Graph()
    for node in range(n_nodes):
        position = (float(rng.uniform(0.0, side)), float(rng.uniform(0.0, side)))
        weight = float(rng.uniform(low, high))
        graph.add_node(node, pos=position, weight=weight)

    nodes = list(graph.nodes())
    for i, u in enumerate(nodes):
        ux, uy = graph.nodes[u]["pos"]
        for v in nodes[i + 1 :]:
            vx, vy = graph.nodes[v]["pos"]
            if float(np.hypot(ux - vx, uy - vy)) <= blockade_radius:
                graph.add_edge(u, v)
    return graph


def solve_mwis_ilp(graph: nx.Graph) -> Tuple[List[int], float, str]:
    """Solve MWIS exactly with PuLP/CBC and return bitstring, weight, status."""
    try:
        import pulp
    except ImportError as exc:  # pragma: no cover - dependency is declared.
        raise RuntimeError("PuLP is required for MWIS ILP verification") from exc

    nodes = list(graph.nodes())
    weights = {node: float(graph.nodes[node].get("weight", 1.0)) for node in nodes}
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="pulp.*")
        problem = pulp.LpProblem("Sagittarius_MWIS_Verification", pulp.LpMaximize)
        variables = {node: pulp.LpVariable(f"x_{node}", cat="Binary") for node in nodes}

        problem += pulp.lpSum(weights[node] * variables[node] for node in nodes)
        for u, v in graph.edges():
            problem += variables[u] + variables[v] <= 1

        problem.solve(pulp.PULP_CBC_CMD(msg=False))
        status = pulp.LpStatus[problem.status]
        if status != "Optimal":
            raise RuntimeError(f"MWIS ILP did not find an optimal solution: {status}")

        bitstring = [1 if float(pulp.value(variables[node]) or 0.0) > 0.5 else 0 for node in nodes]
    weight = float(sum(weights[node] for node, bit in zip(nodes, bitstring) if bit))
    return bitstring, weight, status


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
    n_nodes = graph.number_of_nodes()
    total = 0.0
    for probability, basis_value in zip(probabilities, basis):
        bitstring = np.array([(int(basis_value) >> bit) & 1 for bit in range(n_nodes)])
        if calculate_weight(graph, bitstring) >= exact_weight - tolerance:
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
    """Compare AQC output against exact ILP solutions across random UDGs."""
    if n_instances <= 0:
        raise ValueError("n_instances must be positive")
    density_values = [float(value) for value in densities]
    if not density_values:
        raise ValueError("densities must contain at least one value")

    master_rng = np.random.default_rng(seed)
    instances: List[MWISInstanceResult] = []

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
        aqc_array = np.array(aqc_bitstring)
        aqc_valid = verify_independent_set(graph, aqc_array)
        aqc_weight = float(calculate_weight(graph, aqc_array)) if aqc_valid else 0.0
        approximation_ratio = aqc_weight / exact_weight if exact_weight > tolerance else 1.0
        exact_match = aqc_valid and aqc_weight >= exact_weight - tolerance
        p_optimal = _optimal_probability(graph, probabilities, basis, exact_weight, tolerance=tolerance)
        avg_degree = float(np.mean([degree for _, degree in graph.degree()])) if n_nodes else 0.0

        instances.append(
            MWISInstanceResult(
                instance_id=instance_id,
                seed=instance_seed,
                n_nodes=n_nodes,
                density=density,
                avg_degree=avg_degree,
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
                optimal_probability=p_optimal,
            )
        )

    success_count = sum(1 for result in instances if result.exact_match)
    valid_count = sum(1 for result in instances if result.aqc_valid_independent_set)
    ratios = [result.approximation_ratio for result in instances if result.approximation_ratio is not None]
    probabilities = [result.optimal_probability for result in instances if result.optimal_probability is not None]

    return MWISBatchReport(
        schema_version=MWIS_BATCH_SCHEMA_VERSION,
        artifact_type=MWIS_BATCH_ARTIFACT_TYPE,
        seed=seed,
        blockade_radius=blockade_radius,
        n_instances=n_instances,
        n_nodes=n_nodes,
        densities=density_values,
        duration=duration,
        success_count=success_count,
        valid_count=valid_count,
        mean_approximation_ratio=float(np.mean(ratios)) if ratios else 0.0,
        mean_optimal_probability=float(np.mean(probabilities)) if probabilities else None,
        instances=instances,
    )
