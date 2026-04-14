from typing import Dict, Any


def _fmt_time(seconds: float) -> str:
    """Format a time value into a human-readable string."""
    if seconds >= 1:
        return f"{seconds:.4f} s"
    elif seconds >= 1e-3:
        return f"{seconds * 1e3:.4f} ms"
    elif seconds >= 1e-6:
        return f"{seconds * 1e6:.4f} µs"
    else:
        return f"{seconds * 1e9:.4f} ns"


def format_results(data: Dict[str, Any]) -> str:
    """
    Format benchmark or compare results into a human-readable table.

    Accepts the output of either `benchmark()` or `compare()`.

    Parameters
    ----------
    data : dict
        Output from `benchmark()` or `compare()`.

    Returns
    -------
    str
        A formatted string table ready to be printed.
    """
    # Detect if this is a compare() result or a benchmark() result
    if "results" in data and "ranking" in data:
        return _format_compare(data)
    else:
        return _format_single(data)


def _format_single(result: Dict[str, Any]) -> str:
    """Format a single benchmark result."""
    name = result.get("name", "unknown")
    runs = result.get("runs", "?")
    mean = result.get("mean", 0)
    min_ = result.get("min", 0)
    max_ = result.get("max", 0)
    total = result.get("total", 0)

    col = 20
    width = 42

    lines = [
        "┌" + "─" * width + "┐",
        f"│  bencheetah — {name}".ljust(width + 1) + "│",
        "├" + "─" * width + "┤",
        f"│  {'Runs':<{col}}{runs!s:>{width - col - 2}}  │",
        f"│  {'Mean':<{col}}{_fmt_time(mean):>{width - col - 2}}  │",
        f"│  {'Min':<{col}}{_fmt_time(min_):>{width - col - 2}}  │",
        f"│  {'Max':<{col}}{_fmt_time(max_):>{width - col - 2}}  │",
        f"│  {'Total':<{col}}{_fmt_time(total):>{width - col - 2}}  │",
        "└" + "─" * width + "┘",
    ]
    return "\n".join(lines)


def _format_compare(data: Dict[str, Any]) -> str:
    """Format a compare() result with a ranking table."""
    results = data["results"]
    ranking = data["ranking"]
    winner = data["winner"]

    # Determine column widths dynamically
    names = list(results.keys())
    name_w = max(len(n) for n in names) + 2
    col_w = 14
    width = name_w + col_w * 4 + 5

    header = (
        f"  {'Function':<{name_w}}"
        f"{'Mean':>{col_w}}"
        f"{'Min':>{col_w}}"
        f"{'Max':>{col_w}}"
        f"{'Total':>{col_w}}"
    )

    sep = "─" * len(header)

    lines = [
        f"\n bencheetah — comparison ({len(results)} functions)",
        sep,
        header,
        sep,
    ]

    fastest_mean = results[ranking[0]["name"]]["mean"]

    for entry in ranking:
        name = entry["name"]
        r = results[name]
        tag = " W" if name == winner else ""
        slowdown = r["mean"] / fastest_mean
        slowdown_str = "" if name == winner else f"  ({slowdown:.1f}x slower)"
        lines.append(
            f"  {name + tag:<{name_w}}"
            f"{_fmt_time(r['mean']):>{col_w}}"
            f"{_fmt_time(r['min']):>{col_w}}"
            f"{_fmt_time(r['max']):>{col_w}}"
            f"{_fmt_time(r['total']):>{col_w}}"
            f"{slowdown_str}"
        )

    lines.append(sep)
    lines.append(f"\n  Winner: {winner}")
    lines.append("")

    return "\n".join(lines)
