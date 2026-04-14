"""
bencheetah demo
===============
Run this script to see all four public functions in action.

    python examples/demo.py

The scaling experiment at the end saves a PNG chart: scaling_sort.png
"""

import random
from bencheetah import benchmark, compare, format_results, scale_benchmark, plot_scaling


# 1. Benchmark a single function
print("\n=== 1. Benchmark a single function ===\n")

def bubble_sort(lst):
    lst = lst[:]
    n = len(lst)
    for i in range(n):
        for j in range(n - i - 1):
            if lst[j] > lst[j + 1]:
                lst[j], lst[j + 1] = lst[j + 1], lst[j]
    return lst

data = list(range(200, 0, -1))
result = benchmark(bubble_sort, data, repeats=10, warmup=2)
print(format_results(result))


# 2. Compare multiple sort implementations (fixed-size input)
print("\n=== 2. Compare sorting strategies (n=1 000) ===\n")

sample = random.sample(range(100_000), 1_000)

def python_sorted(lst):
    return sorted(lst)

def list_sort(lst):
    lst = lst[:]
    lst.sort()
    return lst

out = compare(
    {
        "sorted() built-in": python_sorted,
        "list.sort()":       list_sort,
        "bubble sort":       bubble_sort,
    },
    args=(sample,),
    repeats=8,
    warmup=2,
)
print(format_results(out))


# 3. Gauss sum vs loop sum
print("\n=== 3. Gauss formula vs loop sum ===\n")

def loop_sum(n):
    return sum(range(n))

def gauss_sum(n):
    return n * (n - 1) // 2

out2 = compare(
    {"loop sum": loop_sum, "gauss formula": gauss_sum},
    args=(1_000_000,),
    repeats=6,
)
print(format_results(out2))


# 4. Scaling experiment — execution time vs input size
print("\n=== 4. Scaling experiment: sort algorithms across input sizes ===\n")

SIZES = [100, 500, 1_000, 2_000, 5_000]

def insertion_sort(lst):
    lst = lst[:]
    for i in range(1, len(lst)):
        key = lst[i]
        j = i - 1
        while j >= 0 and lst[j] > key:
            lst[j + 1] = lst[j]
            j -= 1
        lst[j + 1] = key
    return lst

# input_gen produces a new reversed list for every size n
scale_data = scale_benchmark(
    funcs={
        "sorted() built-in": python_sorted,
        "insertion sort":    insertion_sort,
        "bubble sort":       bubble_sort,
    },
    input_gen=lambda n: list(range(n, 0, -1)),   # worst-case: reversed
    sizes=SIZES,
    repeats=5,
    warmup=1,
)

# Print a quick summary table
for name, entry in scale_data.items():
    print(f"  {name}")
    for n, mean in zip(entry["sizes"], entry["means"]):
        print(f"    n={n:>5,}  mean={mean*1000:.3f} ms")
    print()

# Plot and save (no interactive window in Docker/CI)
fig, ax = plot_scaling(
    scale_data,
    title="Sort algorithm scaling — worst case (reversed input)",
    show_errorbars=True,
    show_minmax_band=True,
    save_path="scaling_sort.png",
    show=False,
)
print("Chart saved to scaling_sort.png")
