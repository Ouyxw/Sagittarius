"""Run the plan-v2 CPU local-noise matrix (source/editable installation)."""
import argparse
from sagittarius.open_system_benchmark import benchmark_open_system

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",default="benchmark-output/open-system-v2")
    parser.add_argument("--tier",choices=["all","performance","correctness"],default="all")
    parser.add_argument("--scenario",action="append",dest="scenario_ids")
    parser.add_argument("--warmups",type=int,default=2)
    parser.add_argument("--repeat-count",type=int,default=5)
    parser.add_argument("--timeout-seconds",type=float,default=1800.)
    parser.add_argument("--memory-limit-mb",type=float,default=4096.)
    parser.add_argument("--max-density-dimension",type=int,default=256)
    parser.add_argument("--max-state-dimension",type=int,default=1024)
    parser.add_argument("--accuracy-atol",type=float,default=1e-6)
    parser.add_argument("--reference-stability-atol",type=float,default=1e-9)
    parser.add_argument("--stochastic-alpha",type=float,default=1e-6)
    paths=benchmark_open_system(**vars(parser.parse_args()))
    print(paths["json"])
    raise SystemExit(0 if all(r["status"] in ("passed","skipped") for r in paths["artifact"]["timings"]) else 1)
