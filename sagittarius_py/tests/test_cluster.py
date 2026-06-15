import pytest

from sagittarius import ParallelSimulation


def _cluster_backend(n_workers=2):
    try:
        psim = ParallelSimulation(n_workers=n_workers)
        from sagittarius.runtime import get_julia

        jl, _ = get_julia()
    except Exception as exc:
        pytest.skip(f"Julia cluster backend unavailable: {exc}")
    return psim, jl


def test_parallel_setup():
    # Test that we can spin up workers.
    _, jl = _cluster_backend(n_workers=2)
    n = jl.Distributed.nprocs()
    print(f"Number of processes: {n}")
    assert n >= 2


def test_parallel_map():
    _, jl = _cluster_backend(n_workers=2)

    # Define a simple function on all workers.
    jl.seval("using Distributed")
    jl.seval("@everywhere square(x) = x^2")

    params = [1, 2, 3, 4, 5]
    res = list(jl.Distributed.pmap(jl.seval("square"), params))

    print(f"Results: {res}")
    assert res == [1, 4, 9, 16, 25]


def test_psim_map_method():
    psim, jl = _cluster_backend(n_workers=2)
    jl.seval("@everywhere cube(x) = x^3")
    res = psim.map("cube", [1, 2, 3])
    print(f"Cube results: {res}")
    assert res == [1, 8, 27]


if __name__ == "__main__":
    test_parallel_setup()
    test_parallel_map()
    test_psim_map_method()
    print("Clustered solver foundation verified!")
