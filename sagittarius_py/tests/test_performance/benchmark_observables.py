"""Run the bounded plan-v2 observable suite; CPU-only source/editable workflow."""
import argparse
from sagittarius.observable_benchmark import benchmark_observables

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="benchmark-output/observables-v2")
    parser.add_argument("--tier", choices=["all", "correctness", "performance"], default="all")
    parser.add_argument("--scenario", action="append", dest="scenario_ids")
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--repeat-count", type=int, default=5)
    parser.add_argument("--timeout-seconds", type=float, default=900.)
    parser.add_argument("--memory-limit-mb", type=float, default=4096.)
    parser.add_argument("--accuracy-atol", type=float, default=1e-8)
    parser.add_argument("--reference-stability-atol", type=float, default=1e-10)
    parser.add_argument("--stochastic-alpha", type=float, default=1e-6)
    paths = benchmark_observables(**vars(parser.parse_args()))
    print(paths["json"])
    raise SystemExit(0 if all(r["status"] == "passed" for r in paths["artifact"]["timings"]) else 1)
