import time
import statistics
from typing import Callable, Any, Dict, Tuple, Optional


def benchmark(
    func: Callable,
    *args,
    repeats: int = 5,
    warmup: int = 1,
    **kwargs,
) -> Dict[str, Any]:
    """
    Benchmark a single function by running it multiple times.

    Parameters
    ----------
    func : Callable
        The function to benchmark.
    *args :
        Positional arguments forwarded to `func`.
    repeats : int, optional
        Number of timed runs (default: 5).
    warmup : int, optional
        Number of un-timed warm-up runs before measurement (default: 1).
    **kwargs :
        Keyword arguments forwarded to `func`.

    Returns
    -------
    dict with keys: name, runs, mean, min, max, stdev, total.

    Examples
    --------
    >>> from bencheetah import benchmark
    >>> result = benchmark(sum, range(10_000), repeats=10)
    >>> result["mean"] > 0
    True
    """
    for _ in range(warmup):
        func(*args, **kwargs)

    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        func(*args, **kwargs)
        t1 = time.perf_counter()
        times.append(t1 - t0)

    return {
        "name": func.__name__,
        "runs": repeats,
        "mean": statistics.mean(times),
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "total": sum(times),
    }


def compare(
    funcs: Dict[str, Callable],
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict] = None,
    repeats: int = 5,
    warmup: int = 1,
) -> Dict[str, Any]:
    """
    Compare multiple functions using the same arguments.

    Parameters
    ----------
    funcs : dict
        Mapping of ``{label: callable}`` for each function to compare.
    args : tuple, optional
        Positional arguments forwarded to every function.
    kwargs : dict, optional
        Keyword arguments forwarded to every function.
    repeats : int, optional
        Number of timed runs per function (default: 5).
    warmup : int, optional
        Number of un-timed warm-up runs per function (default: 1).

    Returns
    -------
    dict with keys: results, winner, ranking.

    Examples
    --------
    >>> from bencheetah import compare
    >>> data = list(range(10_000))
    >>> out = compare({"sorted": sorted, "list": list}, args=(data,))
    >>> "winner" in out
    True
    """
    call_args = args or ()
    call_kwargs = kwargs or {}

    results: Dict[str, Dict] = {}
    for name, func in funcs.items():
        res = benchmark(func, *call_args, repeats=repeats, warmup=warmup, **call_kwargs)
        res["name"] = name
        results[name] = res

    winner = min(results, key=lambda n: results[n]["mean"])

    ranking = sorted(
        [{"name": n, "mean": results[n]["mean"]} for n in results],
        key=lambda x: x["mean"],
    )

    return {
        "results": results,
        "winner": winner,
        "ranking": ranking,
    }
