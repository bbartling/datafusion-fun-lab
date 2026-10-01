#!/usr/bin/env python3
"""Regenerate wall-time and peak-RSS plots from bench_results.csv.

Usage (from lab root, with matplotlib available):
  ./env/bin/python tutorial-one/docs/plots/plot_bench.py

Writes:
  tutorial-one/docs/plots/wall_time_vs_size.png
  tutorial-one/docs/plots/peak_rss_vs_size.png
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "bench_results.csv"
OUT_WALL = HERE / "wall_time_vs_size.png"
OUT_RSS = HERE / "peak_rss_vs_size.png"

ENGINE_ORDER = [
    "python-stdlib",
    "python-pandas",
    "python-datafusion",
    "raw-rust",
    "rust-datafusion",
]
ENGINE_LABEL = {
    "python-stdlib": "stdlib",
    "python-pandas": "pandas",
    "python-datafusion": "py-DF",
    "raw-rust": "raw-rust",
    "rust-datafusion": "rust-DF",
}
ENGINE_COLOR = {
    "python-stdlib": "#4C78A8",
    "python-pandas": "#F58518",
    "python-datafusion": "#E45756",
    "raw-rust": "#54A24B",
    "rust-datafusion": "#B279A2",
}
ENGINE_MARKER = {
    "python-stdlib": "o",
    "python-pandas": "s",
    "python-datafusion": "D",
    "raw-rust": "^",
    "rust-datafusion": "v",
}


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def by_engine(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["engine"]].append(row)
    for eng in grouped:
        grouped[eng].sort(key=lambda r: int(r["size_bytes"]))
    return grouped


def size_tick_label(size_bytes: int) -> str:
    if size_bytes < 10_000_000:
        return "~4 MB"
    if size_bytes < 100_000_000:
        return "~25 MB"
    if size_bytes < 2_000_000_000:
        return "~1 GB"
    return "~5 GB"


def style_axes(ax, ylabel: str, title: str, sizes: list[int]) -> None:
    ax.set_xscale("log")
    ax.set_xlabel("CSV size (log scale)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.legend(loc="best", framealpha=0.92)
    ax.set_xticks(sizes)
    ax.set_xticklabels([size_tick_label(s) for s in sizes])


def plot_metric(
    grouped: dict[str, list[dict]],
    metric: str,
    ylabel: str,
    title: str,
    out: Path,
    sizes: list[int],
    log_y: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.5), dpi=140)
    for eng in ENGINE_ORDER:
        series = grouped.get(eng, [])
        if not series:
            continue
        xs = [int(r["size_bytes"]) for r in series]
        ys = [float(r[metric]) for r in series]
        ax.plot(
            xs,
            ys,
            color=ENGINE_COLOR[eng],
            marker=ENGINE_MARKER[eng],
            markersize=7,
            linewidth=2,
            label=ENGINE_LABEL[eng],
        )
    if log_y:
        ax.set_yscale("log")
    style_axes(ax, ylabel, title, sizes)
    fig.text(
        0.01,
        0.01,
        "Note: tiny data.csv uses O(n\u00b2) selection-sort median for stdlib/raw-rust; "
        "~25MB/~1GB/~5GB use O(n log n) fast-median. America/Chicago, 2026-10-01.",
        fontsize=7.5,
        color="#444444",
        ha="left",
        va="bottom",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    rows = load_rows(CSV_PATH)
    grouped = by_engine(rows)
    sizes = sorted({int(r["size_bytes"]) for r in rows})
    plot_metric(
        grouped,
        "run_s",
        "Wall time (s, log scale)",
        "Wall time vs dataset size (five engines)",
        OUT_WALL,
        sizes,
        log_y=True,
    )
    plot_metric(
        grouped,
        "peak_rss_mb",
        "Peak RSS (MB)",
        "Peak RSS vs dataset size (five engines)",
        OUT_RSS,
        sizes,
    )


if __name__ == "__main__":
    main()
