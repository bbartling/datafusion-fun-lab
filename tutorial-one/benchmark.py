#!/usr/bin/env python3
"""
Parent harness: build (if needed) + run each tutorial-one sub-project as a
subprocess against the same CSV/column, and report compile vs run wall times.

Yes — Python still compiles source to bytecode (.pyc) on first import/run;
we time that separately via py_compile. Rust needs an explicit cargo build.
"""

from __future__ import annotations

import argparse
import py_compile
import resource
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB_ROOT = HERE.parent
DEFAULT_CSV = LAB_ROOT / "data.csv"
DEFAULT_COL = "oa_t"

# Prefer the lab venv if present
VENV_PYTHON = LAB_ROOT / "env" / "bin" / "python"
PYTHON = str(VENV_PYTHON if VENV_PYTHON.is_file() else Path(sys.executable))


@dataclass
class Result:
    name: str
    compile_s: float | None
    run_s: float
    peak_child_rss_mb: float
    ok: bool
    detail: str = ""


def rss_children_mb() -> float:
    # Linux: ru_maxrss is kilobytes
    return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0


def run_cmd(
    argv: list[str],
    *,
    cwd: Path | None = None,
    capture: bool = True,
) -> tuple[float, float, subprocess.CompletedProcess[str]]:
    """Return (wall_s, peak_rss_mb, completed_process).

    Peak RSS comes from GNU `/usr/bin/time -f %M` (kB) when available;
    otherwise falls back to getrusage(RUSAGE_CHILDREN) delta (often 0 for short bins).
    """
    time_bin = "/usr/bin/time"
    use_gnu_time = Path(time_bin).is_file()
    before = rss_children_mb()
    t0 = time.perf_counter()
    if use_gnu_time:
        # %e elapsed wall, %M max RSS in kB
        wrapped = [time_bin, "-f", "TIME_RSS_KB=%M", "--"] + argv
        proc = subprocess.run(
            wrapped,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            check=False,
        )
        elapsed = time.perf_counter() - t0
        # GNU time writes stats to stderr; child stderr is mixed — peel our marker
        rss_mb = 0.0
        err_lines = (proc.stderr or "").splitlines()
        kept: list[str] = []
        for line in err_lines:
            if line.startswith("TIME_RSS_KB="):
                try:
                    rss_mb = int(line.split("=", 1)[1]) / 1024.0
                except ValueError:
                    pass
            else:
                kept.append(line)
        proc.stderr = "\n".join(kept)
        if rss_mb <= 0.0:
            rss_mb = max(0.0, rss_children_mb() - before)
        return elapsed, rss_mb, proc

    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=capture,
        check=False,
    )
    elapsed = time.perf_counter() - t0
    rss_mb = max(0.0, rss_children_mb() - before)
    return elapsed, rss_mb, proc


def compile_python(path: Path) -> float:
    t0 = time.perf_counter()
    py_compile.compile(str(path), doraise=True)
    return time.perf_counter() - t0


def cargo_build_release(crate_dir: Path) -> tuple[float, bool, str]:
    cargo = shutil.which("cargo")
    if not cargo:
        return 0.0, False, "cargo not found on PATH"
    elapsed, _rss, proc = run_cmd([cargo, "build", "--release"], cwd=crate_dir)
    ok = proc.returncode == 0
    detail = (proc.stderr or proc.stdout or "")[-800:]
    return elapsed, ok, detail


def binary_path(crate_dir: Path, package_name: str) -> Path:
    return crate_dir / "target" / "release" / package_name


def main() -> int:
    ap = argparse.ArgumentParser(description="Build+run tutorial-one engines side by side.")
    ap.add_argument("csv", nargs="?", default=str(DEFAULT_CSV), help="CSV path")
    ap.add_argument("column", nargs="?", default=DEFAULT_COL, help="Column name")
    ap.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not cargo-build; fail if release binaries missing",
    )
    ap.add_argument(
        "--quiet-runs",
        action="store_true",
        help="Hide child stdout/stderr (default shows a short tail on failure)",
    )
    args = ap.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    col = args.column
    if not csv_path.is_file():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 1

    results: list[Result] = []
    # Selection sort remains the small-data teaching baseline. For large
    # inputs, use each implementation's O(n log n) native sort instead.
    big_data = csv_path.stat().st_size >= 1_000_000_000
    median_flag = ["--fast-median"] if big_data else []

    # --- Pure Python (stdlib only) ---
    stdlib_main = HERE / "python-stdlib" / "main.py"
    try:
        c_s = compile_python(stdlib_main)
        r_s, peak, proc = run_cmd([PYTHON, str(stdlib_main), str(csv_path), col, *median_flag])
        results.append(
            Result(
                "python-stdlib",
                c_s,
                r_s,
                peak,
                proc.returncode == 0,
                (proc.stderr or "")[-400:] if proc.returncode else "",
            )
        )
        if not args.quiet_runs and proc.returncode == 0:
            print(proc.stdout)
    except Exception as e:
        results.append(Result("python-stdlib", None, 0.0, 0.0, False, str(e)))

    # --- Python Pandas ---
    pandas_main = HERE / "python-pandas" / "main.py"
    try:
        c_s = compile_python(pandas_main)
        r_s, peak, proc = run_cmd([PYTHON, str(pandas_main), str(csv_path), col])
        results.append(
            Result(
                "python-pandas",
                c_s,
                r_s,
                peak,
                proc.returncode == 0,
                (proc.stderr or "")[-400:] if proc.returncode else "",
            )
        )
        if not args.quiet_runs and proc.returncode == 0:
            print(proc.stdout)
    except Exception as e:
        results.append(Result("python-pandas", None, 0.0, 0.0, False, str(e)))

    # --- Python DataFusion ---
    df_main = HERE / "python-datafusion" / "main.py"
    try:
        c_s = compile_python(df_main)
        r_s, peak, proc = run_cmd([PYTHON, str(df_main), str(csv_path), col])
        results.append(
            Result(
                "python-datafusion",
                c_s,
                r_s,
                peak,
                proc.returncode == 0,
                (proc.stderr or "")[-400:] if proc.returncode else "",
            )
        )
        if not args.quiet_runs and proc.returncode == 0:
            print(proc.stdout)
    except Exception as e:
        results.append(Result("python-datafusion", None, 0.0, 0.0, False, str(e)))

    # --- Raw Rust ---
    raw_dir = HERE / "raw-rust"
    raw_bin = binary_path(raw_dir, "rust-fun")
    compile_s: float | None = None
    if not args.skip_build or not raw_bin.is_file():
        compile_s, ok, detail = cargo_build_release(raw_dir)
        if not ok:
            results.append(Result("raw-rust", compile_s, 0.0, 0.0, False, detail))
        else:
            r_s, peak, proc = run_cmd([str(raw_bin), str(csv_path), col, *median_flag])
            results.append(
                Result(
                    "raw-rust",
                    compile_s,
                    r_s,
                    peak,
                    proc.returncode == 0,
                    (proc.stderr or "")[-400:] if proc.returncode else "",
                )
            )
            if not args.quiet_runs and proc.returncode == 0:
                print(proc.stdout)
    else:
        r_s, peak, proc = run_cmd([str(raw_bin), str(csv_path), col, *median_flag])
        results.append(
            Result("raw-rust", None, r_s, peak, proc.returncode == 0, (proc.stderr or "")[-400:])
        )

    # --- Rust DataFusion ---
    rdf_dir = HERE / "rust-datafusion"
    rdf_bin = binary_path(rdf_dir, "rust-fun-apache")
    if not args.skip_build or not rdf_bin.is_file():
        compile_s, ok, detail = cargo_build_release(rdf_dir)
        if not ok:
            results.append(Result("rust-datafusion", compile_s, 0.0, 0.0, False, detail))
        else:
            r_s, peak, proc = run_cmd([str(rdf_bin), str(csv_path), col])
            results.append(
                Result(
                    "rust-datafusion",
                    compile_s,
                    r_s,
                    peak,
                    proc.returncode == 0,
                    (proc.stderr or "")[-400:] if proc.returncode else "",
                )
            )
            if not args.quiet_runs and proc.returncode == 0:
                print(proc.stdout)
    else:
        r_s, peak, proc = run_cmd([str(rdf_bin), str(csv_path), col])
        results.append(
            Result(
                "rust-datafusion",
                None,
                r_s,
                peak,
                proc.returncode == 0,
                (proc.stderr or "")[-400:],
            )
        )

    print("====================================")
    print(f"Dataset:       {csv_path}")
    print(f"Column:        {col}")
    print(f"Python:        {PYTHON}")
    print(f"Median mode:   {'native O(n log n)' if big_data else 'selection sort (small-data baseline)'}")
    print("------------------------------------")
    print(f"{'engine':<20} {'compile_s':>10} {'run_s':>10} {'peak_rss_mb':>12}  status")
    for r in results:
        c = f"{r.compile_s:.4f}" if r.compile_s is not None else "—"
        status = "OK" if r.ok else "FAIL"
        print(f"{r.name:<20} {c:>10} {r.run_s:10.4f} {r.peak_child_rss_mb:12.2f}  {status}")
        if not r.ok and r.detail:
            print(f"  detail: {r.detail.strip()[:300]}")
    print("====================================")
    print(
        "Notes: compile_s for Python is py_compile (bytecode); for Rust is "
        "`cargo build --release` (includes dependency compile when cold)."
    )
    print(
        "peak_rss_mb is Max RSS from GNU /usr/bin/time (%M) for each child process."
    )

    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
