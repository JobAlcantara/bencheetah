"""
bencheetah.plotter
==================
Scaling-experiment utilities: run a function (or several) across a range of
input sizes and plot mean execution time vs. n.

Public API
----------
scale_benchmark(func_or_funcs, input_gen, sizes, repeats, warmup)
    Run the experiment and return raw data.

plot_scaling(scale_data, ...)
    Draw the chart from the data returned by scale_benchmark().
"""

from __future__ import annotations

import time
import statistics
from typing import Callable, Dict, Iterable, List, Optional, Union

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
FuncMap = Dict[str, Callable]          # {"label": callable, ...}
ScaleData = Dict[str, Dict]            # output of scale_benchmark()


# ---------------------------------------------------------------------------
# Core experiment runner
# ---------------------------------------------------------------------------

def scale_benchmark(
    funcs: Union[Callable, FuncMap],
    input_gen: Callable[[int], object],
    sizes: Iterable[int],
    repeats: int = 5,
    warmup: int = 1,
) -> ScaleData:
    """
    Benchmark one or more functions across a range of input sizes.

    Parameters
    ----------
    funcs : callable or dict[str, callable]
        A single function **or** a ``{"label": callable}`` dict to compare
        multiple implementations on the same inputs.
    input_gen : callable(n) -> input
        A function that receives an integer *n* and returns the argument(s)
        that will be passed to every benchmarked function for that size.
        Return a ``tuple`` if the function expects multiple positional args,
        otherwise return a single value.

        Examples::

            input_gen = lambda n: list(range(n))          # single arg
            input_gen = lambda n: (list(range(n)), True)  # multiple args
    sizes : iterable[int]
        The input sizes to sweep (e.g. ``[100, 500, 1000, 5000, 10_000]``).
    repeats : int
        Number of timed runs per (function, size) pair (default: 5).
    warmup : int
        Un-timed warm-up runs before measurement (default: 1).

    Returns
    -------
    dict
        ``{"func_label": {"sizes": [...], "means": [...], "stdevs": [...],
        "mins": [...], "maxs": [...]}, ...}``

    Examples
    --------
    >>> from bencheetah import scale_benchmark
    >>> data = scale_benchmark(sorted, lambda n: list(range(n, 0, -1)),
    ...                        sizes=[100, 500, 1000], repeats=3)
    >>> list(data.keys())
    ['sorted']
    """
    # Normalise to a dict of {label: callable}
    if callable(funcs):
        funcs = {funcs.__name__: funcs}

    sizes = list(sizes)
    result: ScaleData = {name: {"sizes": [], "means": [], "stdevs": [],
                                "mins": [], "maxs": []} for name in funcs}

    for n in sizes:
        raw_input = input_gen(n)
        call_args = raw_input if isinstance(raw_input, tuple) else (raw_input,)

        for name, func in funcs.items():
            # warm-up
            for _ in range(warmup):
                func(*call_args)

            times: List[float] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                func(*call_args)
                t1 = time.perf_counter()
                times.append(t1 - t0)

            entry = result[name]
            entry["sizes"].append(n)
            entry["means"].append(statistics.mean(times))
            entry["stdevs"].append(statistics.stdev(times) if len(times) > 1 else 0.0)
            entry["mins"].append(min(times))
            entry["maxs"].append(max(times))

    return result


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_scaling(
    scale_data: ScaleData,
    *,
    title: str = "Execution time vs input size",
    xlabel: str = "Input size (n)",
    ylabel: Optional[str] = None,
    time_unit: str = "auto",
    show_errorbars: bool = True,
    show_minmax_band: bool = False,
    logscale: bool = False,
    figsize: tuple = (9, 5),
    save_path: Optional[str] = None,
    show: bool = True,
):
    """
    Plot mean execution time vs input size for one or more functions.

    Parameters
    ----------
    scale_data : dict
        Output of :func:`scale_benchmark`.
    title : str
        Chart title.
    xlabel : str
        X-axis label.
    ylabel : str, optional
        Y-axis label. Auto-generated from *time_unit* if omitted.
    time_unit : {"auto", "s", "ms", "us", "ns"}
        Unit for the Y axis.  ``"auto"`` picks the most readable unit based
        on the largest mean in the data.
    show_errorbars : bool
        Draw ±1 stdev error bars on each point (default: ``True``).
    show_minmax_band : bool
        Shade the min–max range behind each line (default: ``False``).
    logscale : bool
        Use a logarithmic Y axis (default: ``False``).
    figsize : tuple
        Matplotlib figure size in inches (default: ``(9, 5)``).
    save_path : str, optional
        If given, save the figure to this path (e.g. ``"chart.png"``).
        Supports any format matplotlib understands (.png, .svg, .pdf, …).
    show : bool
        Call ``plt.show()`` at the end (default: ``True``). Set to
        ``False`` when saving without displaying (e.g. in scripts).

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
        The figure and axes objects so the caller can customise further.

    Examples
    --------
    >>> from bencheetah import scale_benchmark, plot_scaling
    >>> data = scale_benchmark(sorted, lambda n: list(range(n, 0, -1)),
    ...                        sizes=[100, 500, 1000], repeats=3)
    >>> fig, ax = plot_scaling(data, show=False)
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.ticker as ticker
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required for plot_scaling(). "
            "Install it with:  pip install matplotlib"
        ) from exc

    # ── choose time unit ────────────────────────────────────────────────────
    all_means = [m for entry in scale_data.values() for m in entry["means"]]
    max_mean = max(all_means) if all_means else 1.0

    _units = {"s": 1.0, "ms": 1e3, "us": 1e6, "ns": 1e9}
    _labels = {"s": "seconds (s)", "ms": "milliseconds (ms)",
               "us": "microseconds (µs)", "ns": "nanoseconds (ns)"}

    if time_unit == "auto":
        if max_mean >= 1.0:
            time_unit = "s"
        elif max_mean >= 1e-3:
            time_unit = "ms"
        elif max_mean >= 1e-6:
            time_unit = "us"
        else:
            time_unit = "ns"

    scale = _units[time_unit]
    y_label = ylabel or f"Mean time ({_labels[time_unit]})"

    # ── colour cycle (accessible palette) ───────────────────────────────────
    _COLORS = [
        "#1D9E75",  # teal
        "#E85D24",  # coral/orange
        "#534AB7",  # purple
        "#BA7517",  # amber
        "#185FA5",  # blue
        "#993556",  # pink
        "#3B6D11",  # green
        "#A32D2D",  # red
    ]

    fig, ax = plt.subplots(figsize=figsize)

    for idx, (label, entry) in enumerate(scale_data.items()):
        sizes  = entry["sizes"]
        means  = [m * scale for m in entry["means"]]
        stdevs = [s * scale for s in entry["stdevs"]]
        mins   = [m * scale for m in entry["mins"]]
        maxs   = [m * scale for m in entry["maxs"]]

        color = _COLORS[idx % len(_COLORS)]

        if show_minmax_band:
            ax.fill_between(sizes, mins, maxs, alpha=0.12, color=color)

        if show_errorbars:
            ax.errorbar(
                sizes, means,
                yerr=stdevs,
                label=label,
                color=color,
                marker="o",
                markersize=5,
                linewidth=1.8,
                capsize=4,
                capthick=1.2,
                elinewidth=1.0,
            )
        else:
            ax.plot(sizes, means, label=label, color=color,
                    marker="o", markersize=5, linewidth=1.8)

    # ── axes styling ─────────────────────────────────────────────────────────
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(y_label, fontsize=11)

    if logscale:
        ax.set_yscale("log")

    ax.xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda x, _: f"{int(x):,}"
    ))
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.5)
    ax.grid(axis="x", linestyle=":",  linewidth=0.4, alpha=0.35)
    ax.spines[["top", "right"]].set_visible(False)

    if len(scale_data) > 1:
        ax.legend(fontsize=10, framealpha=0.85, edgecolor="#cccccc")

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    if show:
        plt.show()

    return fig, ax
