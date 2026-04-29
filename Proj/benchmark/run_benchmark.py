# Main benchmark runner for the final report.
# Runs Dijkstra / A* / JPS4 on 50x50 and 100x100 grids across a density sweep.
# Usage: python benchmark/run_benchmark.py

import csv
import json
import os
import random
import sys
from datetime import datetime

# Resolve project root (one level up from benchmark/)
_PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PROJ, "benchmark"))

from benchmark_utils import MODES, make_grid, grid_to_pg, pick_start_goal, run_mode, aggregate


# Run benchmark for one configuration (grid size, density, trials)
def run_block(width, height, density, trials, rng):
    rows = []
    skipped = 0
    for t in range(trials):
        # Try up to 600 times to find a valid start/goal pair
        for _ in range(600):
            g = make_grid(width, height, density, rng)
            sg = pick_start_goal(g, rng)
            if sg is None:
                continue
            start, goal = sg
            pg = grid_to_pg(g)
            if not pg.reachable(start, goal):
                continue
            outs = []
            # Run all three algorithms on the same board
            for mode in MODES:
                ok, ms, exp, plen = run_mode(g, start, goal, mode)
                outs.append((mode, ok, ms, exp, plen))
            # Only keep results if all algorithms succeeded
            if not all(o[1] for o in outs):
                continue
            # Record results for each algorithm
            for mode, ok, ms, exp, plen in outs:
                rows.append({
                    "trial": t,
                    "width": width,
                    "height": height,
                    "density": density,
                    "mode": mode,
                    "ok": ok,
                    "ms": round(ms, 6),
                    "expansions": exp,
                    "path_cells": plen,
                })
            break
        else:
            skipped += 1
    return rows, skipped


def main():
    # Grid configurations to test
    configs = [
        {"width": 50,  "height": 50,  "label": "50x50"},
        {"width": 100, "height": 100, "label": "100x100"},
    ]
    # Density levels from 10% to 40%
    densities = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    trials_per = 30
    base_seed = 99

    # Setup output directory
    out_dir = os.path.join(_PROJ, "results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    all_summary = {}

    # Run each grid configuration
    for cfg in configs:
        W, H, label = cfg["width"], cfg["height"], cfg["label"]
        print(f"\n=== Grid {label} ===")
        all_rows = []
        skipped_total = 0

        # Test each density level
        for di, d in enumerate(densities):
            rng = random.Random(base_seed + di * 7777 + W)
            print(f"  density {d:.2f} ...", end=" ", flush=True)
            rows, sk = run_block(W, H, d, trials_per, rng)
            all_rows.extend(rows)
            skipped_total += sk
            print(f"got {len(rows)//3} trials, skipped {sk}")

        # Write detailed CSV results
        csv_path = os.path.join(out_dir, f"extended_{label}_{stamp}.csv")
        fieldnames = ["trial", "width", "height", "density", "mode", "ok", "ms", "expansions", "path_cells"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            for r in all_rows:
                w.writerow({k: r.get(k) for k in fieldnames if k in r})

        # Compute aggregated statistics per density
        per_density = {}
        for d in densities:
            block = [r for r in all_rows if abs(r["density"] - d) < 1e-9]
            per_density[str(d)] = aggregate(block)

        # Store summary for this grid size
        all_summary[label] = {
            "grid": label,
            "densities": densities,
            "trials_per_density": trials_per,
            "base_seed": base_seed,
            "skipped_total": skipped_total,
            "per_density": per_density,
        }
        print(f"  csv: {csv_path}")

    # Write aggregated JSON summary
    json_path = os.path.join(out_dir, f"extended_summary_{stamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"stamp": stamp, "results": all_summary}, f, indent=2)

    print(f"\nDone. Summary written to: {json_path}")


if __name__ == "__main__":
    main()
