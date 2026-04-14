import pytest
from bencheetah import benchmark, compare, format_results, scale_benchmark, plot_scaling


# ── helpers ──────────────────────────────────────────────────────────────────

def slow_sum(n):
    return sum(range(n))


def fast_sum(n):
    return n * (n - 1) // 2


# ── benchmark ─────────────────────────────────────────────────────────────────

class TestBenchmark:
    def test_returns_expected_keys(self):
        result = benchmark(slow_sum, 1000, repeats=3, warmup=1)
        assert set(result.keys()) == {"name", "runs", "mean", "min", "max", "stdev", "total"}

    def test_name_is_function_name(self):
        result = benchmark(slow_sum, 1000, repeats=3)
        assert result["name"] == "slow_sum"

    def test_runs_matches_repeats(self):
        result = benchmark(slow_sum, 1000, repeats=7)
        assert result["runs"] == 7

    def test_timings_are_positive(self):
        result = benchmark(slow_sum, 1000, repeats=3)
        assert result["mean"] > 0
        assert result["min"] > 0
        assert result["max"] > 0
        assert result["total"] > 0

    def test_min_le_mean_le_max(self):
        result = benchmark(slow_sum, 1000, repeats=5)
        assert result["min"] <= result["mean"] <= result["max"]

    def test_stdev_non_negative(self):
        result = benchmark(slow_sum, 1000, repeats=5)
        assert result["stdev"] >= 0

    def test_stdev_zero_for_single_run(self):
        result = benchmark(slow_sum, 1000, repeats=1)
        assert result["stdev"] == 0.0

    def test_no_warmup(self):
        result = benchmark(slow_sum, 1000, repeats=3, warmup=0)
        assert result["runs"] == 3

    def test_kwargs_forwarded(self):
        def add(a, b=0):
            return a + b
        result = benchmark(add, 1, b=2, repeats=3)
        assert result["name"] == "add"


# ── compare ───────────────────────────────────────────────────────────────────

class TestCompare:
    def test_returns_expected_keys(self):
        out = compare({"slow": slow_sum, "fast": fast_sum}, args=(1000,), repeats=3)
        assert set(out.keys()) == {"results", "winner", "ranking"}

    def test_winner_is_fastest(self):
        out = compare({"slow": slow_sum, "fast": fast_sum}, args=(100_000,), repeats=5)
        assert out["winner"] == "fast"

    def test_ranking_is_sorted(self):
        out = compare({"slow": slow_sum, "fast": fast_sum}, args=(10_000,), repeats=3)
        means = [r["mean"] for r in out["ranking"]]
        assert means == sorted(means)

    def test_all_functions_in_results(self):
        funcs = {"a": slow_sum, "b": fast_sum}
        out = compare(funcs, args=(1000,), repeats=3)
        assert set(out["results"].keys()) == {"a", "b"}

    def test_single_function_compare(self):
        out = compare({"only": slow_sum}, args=(100,), repeats=3)
        assert out["winner"] == "only"
        assert len(out["ranking"]) == 1

    def test_kwargs_forwarded(self):
        def add(a, b=0):
            return a + b
        out = compare({"add": add}, args=(5,), kwargs={"b": 3}, repeats=3)
        assert "add" in out["results"]


# ── format_results ────────────────────────────────────────────────────────────

class TestFormatResults:
    def test_single_result_contains_name(self):
        result = benchmark(slow_sum, 1000, repeats=3)
        output = format_results(result)
        assert "slow_sum" in output

    def test_single_result_is_string(self):
        result = benchmark(slow_sum, 1000, repeats=3)
        assert isinstance(format_results(result), str)

    def test_compare_result_contains_winner(self):
        out = compare({"slow": slow_sum, "fast": fast_sum}, args=(10_000,), repeats=3)
        output = format_results(out)
        assert "fast" in output
        assert "Winner" in output

    def test_compare_result_is_string(self):
        out = compare({"slow": slow_sum, "fast": fast_sum}, args=(1000,), repeats=3)
        assert isinstance(format_results(out), str)

    def test_time_units_present(self):
        result = benchmark(lambda: None, repeats=5)
        result["name"] = "noop"
        output = format_results(result)
        assert any(unit in output for unit in ["ns", "µs", "ms", "s"])


# ── scale_benchmark ───────────────────────────────────────────────────────────

class TestScaleBenchmark:
    SIZES = [100, 500, 1000]

    def test_single_func_returns_dict(self):
        data = scale_benchmark(slow_sum, lambda n: n, sizes=self.SIZES, repeats=2)
        assert isinstance(data, dict)
        assert "slow_sum" in data

    def test_keys_present(self):
        data = scale_benchmark(slow_sum, lambda n: n, sizes=self.SIZES, repeats=2)
        entry = data["slow_sum"]
        assert set(entry.keys()) == {"sizes", "means", "stdevs", "mins", "maxs"}

    def test_sizes_match(self):
        data = scale_benchmark(slow_sum, lambda n: n, sizes=self.SIZES, repeats=2)
        assert data["slow_sum"]["sizes"] == self.SIZES

    def test_lengths_match(self):
        data = scale_benchmark(slow_sum, lambda n: n, sizes=self.SIZES, repeats=2)
        entry = data["slow_sum"]
        assert len(entry["means"]) == len(self.SIZES)
        assert len(entry["stdevs"]) == len(self.SIZES)

    def test_means_are_positive(self):
        data = scale_benchmark(slow_sum, lambda n: n, sizes=self.SIZES, repeats=2)
        assert all(m > 0 for m in data["slow_sum"]["means"])

    def test_multiple_funcs(self):
        data = scale_benchmark(
            {"slow": slow_sum, "fast": fast_sum},
            lambda n: n,
            sizes=self.SIZES,
            repeats=2,
        )
        assert set(data.keys()) == {"slow", "fast"}

    def test_tuple_input_gen(self):
        def add(a, b):
            return a + b
        data = scale_benchmark(
            add,
            lambda n: (n, n),   # returns a tuple -> unpacked as *args
            sizes=[10, 20],
            repeats=2,
        )
        assert "add" in data

    def test_stdev_zero_for_single_repeat(self):
        data = scale_benchmark(slow_sum, lambda n: n, sizes=[100], repeats=1)
        assert data["slow_sum"]["stdevs"][0] == 0.0

    def test_min_le_mean_le_max(self):
        data = scale_benchmark(slow_sum, lambda n: n, sizes=self.SIZES, repeats=3)
        entry = data["slow_sum"]
        for lo, mean, hi in zip(entry["mins"], entry["means"], entry["maxs"]):
            assert lo <= mean <= hi


# ── plot_scaling ──────────────────────────────────────────────────────────────

class TestPlotScaling:
    """
    Tests run with show=False and no save_path so no GUI or files are created.
    We verify the return types and that the axes contain the expected data.
    """
    SIZES = [100, 500, 1000]

    def _data(self):
        return scale_benchmark(
            {"slow": slow_sum, "fast": fast_sum},
            lambda n: n,
            sizes=self.SIZES,
            repeats=2,
        )

    def test_returns_fig_and_ax(self):
        import matplotlib
        matplotlib.use("Agg")
        fig, ax = plot_scaling(self._data(), show=False)
        import matplotlib.figure
        import matplotlib.axes
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)

    def test_legend_has_both_labels(self):
        import matplotlib
        matplotlib.use("Agg")
        _, ax = plot_scaling(self._data(), show=False)
        labels = [t.get_text() for t in ax.get_legend().get_texts()]
        assert "slow" in labels
        assert "fast" in labels

    def test_title_is_set(self):
        import matplotlib
        matplotlib.use("Agg")
        _, ax = plot_scaling(self._data(), title="My title", show=False)
        assert ax.get_title() == "My title"

    def test_save_path_creates_file(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        out = tmp_path / "chart.png"
        plot_scaling(self._data(), save_path=str(out), show=False)
        assert out.exists() and out.stat().st_size > 0

    def test_logscale_option(self):
        import matplotlib
        matplotlib.use("Agg")
        _, ax = plot_scaling(self._data(), logscale=True, show=False)
        assert ax.get_yscale() == "log"

    def test_time_unit_auto(self):
        import matplotlib
        matplotlib.use("Agg")
        _, ax = plot_scaling(self._data(), time_unit="auto", show=False)
        assert ax.get_ylabel() != ""

    def test_missing_matplotlib_raises(self, monkeypatch):
        import builtins
        real_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == "matplotlib.pyplot":
                raise ImportError("no matplotlib")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", mock_import)
        from bencheetah.plotter import plot_scaling as _ps
        with pytest.raises(ImportError, match="matplotlib"):
            _ps(self._data(), show=False)
