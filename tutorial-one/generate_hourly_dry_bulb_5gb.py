#!/usr/bin/env python3
"""Stream a deterministic, hourly dry-bulb CSV until it reaches ~5 GiB.

The generator never keeps the dataset in memory. It stops after a chunk
boundary, so the resulting CSV is valid and reproducible and is approximately
the requested size.
"""
from __future__ import annotations

import argparse
import math
from datetime import datetime, timedelta
from pathlib import Path

HEADER = "Timestamp,DryBulb_Temp_F\n"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "hourly_dry_bulb_5gb.csv"
CHUNK_ROWS = 100_000
HOURS_PER_YEAR = 365.2425 * 24.0


def temperature_f(hour: int) -> float:
    """Deterministic seasonal/daily synthetic temperature in Fahrenheit."""
    seasonal = 24.0 * math.sin(2.0 * math.pi * hour / HOURS_PER_YEAR - 0.8)
    daily = 7.0 * math.sin(2.0 * math.pi * (hour % 24) / 24.0 - 1.1)
    # A cheap deterministic pseudo-noise term, avoiding a large RNG state.
    noise = (((hour * 1103515245 + 12345) >> 16) & 0x7FFF) / 32767.0
    return 52.0 + seasonal + daily + (noise - 0.5) * 8.0


def generate(output: Path, target_bytes: int) -> tuple[int, int]:
    output.parent.mkdir(parents=True, exist_ok=True)
    # Precompute one non-leap calendar year.  The requested dataset spans
    # more hours than datetime's year-9999 limit, so simulated calendar years
    # wrap every 8,000 years while the rows remain hourly and deterministic.
    start = datetime(2000, 1, 1)
    one_hour = timedelta(hours=1)
    stamp_cycle = [
        (start + i * one_hour).strftime("%m-%dT%H:%M:%S")
        for i in range(365 * 24)
    ]
    rows = 0
    with output.open("w", encoding="utf-8", newline="") as f:
        f.write(HEADER)
        while f.tell() < target_bytes:
            lines: list[str] = []
            for _ in range(CHUNK_ROWS):
                year = 2000 + (rows // (365 * 24)) % 8000
                stamp = f"{year:04d}-{stamp_cycle[rows % (365 * 24)]}"
                lines.append(f"{stamp},{temperature_f(rows):.2f}\n")
                rows += 1
            f.write("".join(lines))
    return output.stat().st_size, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--target-gb", type=float, default=5.0, help="decimal GB target")
    args = ap.parse_args()
    size, rows = generate(args.output, int(args.target_gb * 1_000_000_000))
    print(f"output={args.output}")
    print(f"bytes={size}")
    print(f"rows={rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
