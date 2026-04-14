#  bencheetah

> Simple, zero-dependency benchmarking utilities for Python functions — now with scaling experiments and charts.

[![PyPI version](https://img.shields.io/pypi/v/bencheetah.svg)](https://pypi.org/project/bencheetah/)
[![Python](https://img.shields.io/pypi/pyversions/bencheetah.svg)](https://pypi.org/project/bencheetah/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/JobAlcantara/bencheetah/actions/workflows/ci.yml/badge.svg)](https://github.com/JobAlcantara/bencheetah/actions)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JobAlcantara/bencheetah/blob/main/notebooks/tutorial.ipynb)

---

## Why bencheetah?

Simple, useful and fast. **bencheetah** gives you:

- Statistical timing (mean, min, max, stdev) for a single function.
- Side-by-side comparison of multiple implementations.
- **Scaling experiments**: sweep a range of input sizes and plot execution time vs. n — ideal for empirically verifying algorithmic complexity.
- Beautiful terminal tables and matplotlib charts with a single call.

No dependencies for the core functions. `matplotlib` only needed for plotting.

---

## Installation

```bash
# Core (no dependencies)
pip install bencheetah

# With plotting support
pip install "bencheetah[plot]"
```

Requires Python ≥ 3.10.

---

## Quick Start

### Benchmark a single function

```python
from bencheetah import benchmark, format_results

result = benchmark(sum, range(1_000_000), repeats=10)
print(format_results(result))
```

```
┌──────────────────────────────────────────┐
│   bencheetah — sum                     │
├──────────────────────────────────────────┤
│  Runs                                10  │
│  Mean                           8.23 ms  │
│  Min                            7.91 ms  │
│  Max                            9.14 ms  │
│  Total                         82.32 ms  │
└──────────────────────────────────────────┘
```

### Compare multiple implementations

```python
from bencheetah import compare, format_results

def loop_sum(n):
    return sum(range(n))

def gauss_sum(n):
    return n * (n - 1) // 2

out = compare(
    {"loop": loop_sum, "gauss": gauss_sum},
    args=(1_000_000,),
    repeats=8,
)
print(format_results(out))
```

```
 bencheetah — comparison (2 functions)
────────────────────────────────────────────────────────────
  Function            Mean          Min          Max         Total
────────────────────────────────────────────────────────────
  gauss W        142.00 ns    130.00 ns    180.00 ns    1.14 µs
  loop              8.23 ms      7.91 ms      9.14 ms   65.84 ms   (57930.8x slower)
────────────────────────────────────────────────────────────

  Winner: gauss W
```

### Scaling experiment (execution time vs input size)

```python
from bencheetah import scale_benchmark, plot_scaling

def bubble_sort(lst):
    lst = lst[:]
    n = len(lst)
    for i in range(n):
        for j in range(n - i - 1):
            if lst[j] > lst[j + 1]:
                lst[j], lst[j + 1] = lst[j + 1], lst[j]
    return lst

data = scale_benchmark(
    funcs={
        "sorted() built-in": sorted,
        "bubble sort":       bubble_sort,
    },
    input_gen=lambda n: list(range(n, 0, -1)),  # worst-case: reversed list
    sizes=[100, 500, 1_000, 2_000, 5_000],
    repeats=5,
)

fig, ax = plot_scaling(data, title="Sort algorithm scaling")
```

The chart shows mean execution time (±1 stdev error bars) vs input size, one line per algorithm — perfect for comparing O(n log n) vs O(n²) empirically.

---

## Functions

### `benchmark(func, *args, repeats=5, warmup=1, **kwargs) → dict`

Runs `func(*args, **kwargs)` multiple times and returns timing statistics.

| Key | Description |
|-----|-------------|
| `name` | Function name |
| `runs` | Number of timed runs |
| `mean` | Average execution time (seconds) |
| `min` | Fastest run |
| `max` | Slowest run |
| `stdev` | Standard deviation |
| `total` | Sum of all runs |

**Parameters:**

- `func` — Callable to benchmark.
- `*args` — Positional arguments forwarded to `func`.
- `repeats` *(int)* — Number of timed runs. Default: `5`.
- `warmup` *(int)* — Un-timed warm-up runs (avoids cold-start effects). Default: `1`.
- `**kwargs` — Keyword arguments forwarded to `func`.

---

### `compare(funcs, args=None, kwargs=None, repeats=5, warmup=1) → dict`

Benchmarks multiple functions with the same inputs and ranks them by mean time.

| Key | Description |
|-----|-------------|
| `results` | Dict of benchmark dicts keyed by label |
| `winner` | Label of the fastest function |
| `ranking` | List of `{name, mean}` sorted fastest → slowest |

**Parameters:**

- `funcs` *(dict)* — `{"label": callable, ...}`.
- `args` *(tuple)* — Positional arguments shared by all functions.
- `kwargs` *(dict)* — Keyword arguments shared by all functions.
- `repeats`, `warmup` — Same as `benchmark`.

---

### `scale_benchmark(funcs, input_gen, sizes, repeats=5, warmup=1) → dict`

Runs a **scaling experiment**: benchmarks one or more functions across a range of input sizes.

**Parameters:**

- `funcs` — A single callable **or** a `{"label": callable}` dict.
- `input_gen` *(callable)* — Receives an integer `n` and returns the input for that size.
  Return a `tuple` if the function needs multiple positional arguments.
  ```python
  input_gen = lambda n: list(range(n))          # single arg
  input_gen = lambda n: (list(range(n)), True)  # multiple args → unpacked
  ```
- `sizes` *(iterable[int])* — The input sizes to sweep, e.g. `[100, 1000, 5000, 10_000]`.
- `repeats`, `warmup` — Same as `benchmark`.

**Returns** a dict keyed by function label, each value containing:
`{"sizes": [...], "means": [...], "stdevs": [...], "mins": [...], "maxs": [...]}`.

---

### `plot_scaling(scale_data, *, ...) → (Figure, Axes)`

Plots the output of `scale_benchmark()` as a line chart (mean time vs input size).

Requires `matplotlib`. Install with `pip install "bencheetah[plot]"`.

| Parameter | Default | Description |
|---|---|---|
| `title` | `"Execution time vs input size"` | Chart title |
| `xlabel` | `"Input size (n)"` | X-axis label |
| `ylabel` | auto | Y-axis label (auto-generated from time unit) |
| `time_unit` | `"auto"` | One of `"auto"`, `"s"`, `"ms"`, `"us"`, `"ns"` |
| `show_errorbars` | `True` | Draw ±1 stdev error bars |
| `show_minmax_band` | `False` | Shade the min–max range behind each line |
| `logscale` | `False` | Logarithmic Y axis |
| `figsize` | `(9, 5)` | Matplotlib figure size in inches |
| `save_path` | `None` | Save to file (`.png`, `.svg`, `.pdf`, …) |
| `show` | `True` | Call `plt.show()` |

---

### `format_results(data) → str`

Formats the output of `benchmark()` or `compare()` into a printable terminal table.
Automatically selects the most readable time unit (ns, µs, ms, s).

---

## Tutorial Notebook

A step-by-step tutorial with all four functions is available as a Jupyter notebook.
Click below to open it directly in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/JobAlcantara/bencheetah/blob/main/notebooks/tutorial.ipynb)

---

## Running with Docker

```bash
# Build the image
docker build -t bencheetah .

# Run the demo (prints tables + saves scaling_sort.png inside the container)
docker run --rm bencheetah

# Copy the chart out of the container
docker run --rm -v "$PWD":/out bencheetah \
  sh -c "python examples/demo.py && cp scaling_sort.png /out/"

# Run the test suite
docker run --rm bencheetah pytest tests/ -v
```

---

## Development

```bash
git clone https://github.com/JobAlcantara/bencheetah.git
cd bencheetah
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Project Structure

```
bencheetah/
├── src/
│   └── bencheetah/
│       ├── __init__.py
│       ├── core.py          # benchmark() and compare()
│       ├── formatters.py    # format_results()
│       └── plotter.py       # scale_benchmark() and plot_scaling()
├── tests/
│   └── test_bencheetah.py
├── examples/
│   └── demo.py
├── notebooks/
│   └── tutorial.ipynb
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## License

MIT © [JobAlcantara](https://github.com/JobAlcantara)
