# Tutorial one — same-column stats bake-off

Same CSV + same column, compared across:

| Engine | Directory | How it runs |
|---|---|---|
| Pure Python (stdlib `csv` + math) | `python-stdlib/` | `python main.py <csv> <col>` |
| Pandas | `python-pandas/` | `python main.py <csv> <col>` |
| Apache DataFusion (Python) | `python-datafusion/` | `python main.py <csv> <col>` |
| Raw Rust (`csv` crate) | `raw-rust/` | `cargo build --release` → `target/release/rust-fun` |
| Apache DataFusion (Rust) | `rust-datafusion/` | `cargo build --release` → `target/release/rust-fun-apache` |

Metrics printed by each engine: count, total, min, max, average, median, sample variance, sample std dev.

## One-shot parent benchmark

From the lab venv (or any env with `pandas` + `datafusion` installed for the Python DF path):

```bash
cd /home/ben/Desktop/datafusion-fun-lab
./env/bin/python tutorial-one/benchmark.py ./data.csv oa_t
```

What the parent does:

1. **Compile timers** — `py_compile` for each Python `main.py` (bytecode); `cargo build --release` for each Rust crate (cold builds include dependency compile).
2. **Run timers** — each engine as a **subprocess** with the same `<csv> <column>` so results are comparable.
3. Prints a summary table: `compile_s`, `run_s`, **peak_rss_mb** (GNU `/usr/bin/time` Max RSS per child), OK/FAIL.

Flags:

- `--quiet-runs` — hide per-engine stdout (summary only)
- `--skip-build` — do not `cargo build` (fails if release binaries missing)

For a large input (file size at least 1 GB), the harness automatically passes
`--fast-median` to the stdlib and raw-Rust programs. This selects the same
median statistic with native O(n log n) sorting instead of the deliberately
O(n²) selection sort used by the small-data teaching baseline.

Python still compiles to `.pyc` at first run even without an explicit compile step; the harness measures that via `py_compile` so you can see it next to Rust’s `cargo build --release`.

## Manual runs

```bash
# Pure Python
./env/bin/python tutorial-one/python-stdlib/main.py ./data.csv oa_t

# Pandas
./env/bin/python tutorial-one/python-pandas/main.py ./data.csv oa_t

# DataFusion (Python)
./env/bin/python tutorial-one/python-datafusion/main.py ./data.csv oa_t

# Raw Rust
cd tutorial-one/raw-rust && cargo build --release
./target/release/rust-fun ../../data.csv oa_t

# DataFusion (Rust)
cd tutorial-one/rust-datafusion && cargo build --release
./target/release/rust-fun-apache ../../data.csv oa_t
```

## Fresh benchmark (2026-10-01, America/Chicago)

Dataset: `data.csv`, column: `oa_t`, lab venv: `env/bin/python`.
The release binaries were already built; this run used `--quiet-runs --skip-build`.

| Engine | Compile (s) | Run (s) | Peak RSS (MB) | Status |
|---|---:|---:|---:|---|
| `python-stdlib` | 0.0016 | 18.1533 | 12.39 | OK |
| `python-pandas` | 0.0006 | 0.3908 | 120.32 | OK |
| `python-datafusion` | 0.0008 | 0.3714 | 185.66 | OK |
| `raw-rust` | — | 0.6996 | 2.45 | OK |
| `rust-datafusion` | — | 0.0353 | 73.74 | OK |

Compile time for Python is `py_compile`; Rust compile time is omitted here because
`--skip-build` was used after rebuilding `raw-rust` with `cargo build --release`.
Peak RSS is GNU `/usr/bin/time` Max RSS (`%M`) for each child process.

## ~5GB `DryBulb_Temp_F` experiment

The generator is chunk-streaming and keeps the CSV out of git:

```bash
./env/bin/python tutorial-one/generate_hourly_dry_bulb_5gb.py
./env/bin/python tutorial-one/benchmark.py \
  tutorial-one/data/hourly_dry_bulb_5gb.csv DryBulb_Temp_F \
  --quiet-runs --skip-build
```

Dataset and run metadata (2026-10-01, America/Chicago):

- File: `tutorial-one/data/hourly_dry_bulb_5gb.csv` (ignored; never committed)
- Rows: **192,400,000**; size: **5,002,400,025** bytes (**4.6588** GiB)
- Median: the big-file run uses native O(n log n) median paths for
  `python-stdlib` and `raw-rust`; Pandas and both DataFusion engines use their
  native aggregate implementations. This is intentionally not the small-file
  O(n²) selection-sort comparison.

| Engine | Run (s) | Peak RSS (MB) | Status |
|---|---:|---:|---|
| `python-stdlib` | 148.4826 | 9586.77 | OK |
| `python-pandas` | 41.3542 | 7016.17 | OK |
| `python-datafusion` | 6.0083 | 3678.01 | OK |
| `raw-rust` | 29.8033 | 2937.71 | OK |
| `rust-datafusion` | 9.3985 | 1715.76 | OK |

**Takeaway.** On this larger scan, DataFusion's columnar execution and
streaming/parallel planning can pay off versus Python object-heavy processing,
while raw Rust remains a low-memory baseline. The result is a scan-and-aggregate
comparison; the median algorithm is explicitly changed for scale, so it should
not be read as a selection-sort apples-to-apples result.

## Apples-to-apples scope

`python-stdlib` and `raw-rust` intentionally use the direct standard-library
container equivalents: Python `list[float]` and Rust `Vec<f64>` (not
`array.array` or NumPy). Both use the same load algorithm: read the header,
find the column index, loop over rows, parse `f64`, and skip unparseable values.
Python uses the stdlib `csv` module; Rust uses the `csv` crate because Rust has
no CSV parser in its standard library. Both use hand-coded selection sort for
the median and sample variance (`n - 1`, or `0.0` for one value).

## Notes

- Prefer the lab `env/` Python so Pandas / DataFusion bindings match.
- Raw Rust and Rust DataFusion binaries are separate crates; the parent builds both before timing runs unless `--skip-build`.
- `python-datafusion` and `rust-datafusion` both use SQL aggregates over Arrow; Pandas / stdlib / raw Rust compute in-process over parsed floats.
