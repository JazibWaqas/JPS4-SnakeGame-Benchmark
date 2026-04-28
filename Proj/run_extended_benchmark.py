# extended benchmark for the final report
# 50x50 and 100x100 grids, density sweep 0.10 to 0.40 in 0.05 steps, 30 trials each
# run: python run_extended_benchmark.py

import csv
import json
import os
import random
import statistics
import sys
from datetime import datetime

_PROJ = os.path.dirname(os.path.abspath(__file__))
_CODE = os.path.join(_PROJ, "src", "Snake Game Code")
if _CODE not in sys.path:
    sys.path.insert(0, _CODE)

from benchmark_interim import (
    MODES,
    make_grid,
    grid_to_pg,
    pick_start_goal,
    run_mode,
)


def run_block(width, height, density, trials, rng):
    rows = []
    skipped = 0
    for t in range(trials):
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
            for mode in MODES:
                ok, ms, exp, plen = run_mode(g, start, goal, mode)
                outs.append((mode, ok, ms, exp, plen))
            if not all(o[1] for o in outs):
                continue
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


def aggregate(rows):
    out = {}
    for m in MODES:
        ms_list = [r["ms"] for r in rows if r["mode"] == m and r["ok"]]
        ex_list = [r["expansions"] for r in rows if r["mode"] == m and r["ok"]]
        out[m] = {
            "time_mean": round(statistics.mean(ms_list), 4) if ms_list else None,
            "time_std":  round(statistics.pstdev(ms_list), 4) if len(ms_list) > 1 else 0.0,
            "exp_mean":  round(statistics.mean(ex_list), 2) if ex_list else None,
            "exp_std":   round(statistics.pstdev(ex_list), 2) if len(ex_list) > 1 else 0.0,
            "n": len(ms_list),
        }
    return out


def main():
    configs = [
        {"width": 50,  "height": 50,  "label": "50x50"},
        {"width": 100, "height": 100, "label": "100x100"},
    ]
    densities = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    trials_per = 30
    base_seed = 99

    out_dir = os.path.join(_PROJ, "results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    all_summary = {}

    for cfg in configs:
        W, H, label = cfg["width"], cfg["height"], cfg["label"]
        print(f"\n=== Grid {label} ===")
        all_rows = []
        skipped_total = 0

        for di, d in enumerate(densities):
            rng = random.Random(base_seed + di * 7777 + W)
            print(f"  density {d:.2f} ...", end=" ", flush=True)
            rows, sk = run_block(W, H, d, trials_per, rng)
            all_rows.extend(rows)
            skipped_total += sk
            print(f"got {len(rows)//3} trials, skipped {sk}")

        csv_path = os.path.join(out_dir, f"extended_{label}_{stamp}.csv")
        fieldnames = ["trial", "width", "height", "density", "mode", "ok", "ms", "expansions", "path_cells"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            for r in all_rows:
                w.writerow({k: r.get(k) for k in fieldnames if k in r})

        per_density = {}
        for d in densities:
            block = [r for r in all_rows if abs(r["density"] - d) < 1e-9]
            per_density[str(d)] = aggregate(block)

        all_summary[label] = {
            "grid": label,
            "densities": densities,
            "trials_per_density": trials_per,
            "base_seed": base_seed,
            "skipped_total": skipped_total,
            "per_density": per_density,
        }
        print(f"  csv: {csv_path}")

    json_path = os.path.join(out_dir, f"extended_summary_{stamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"stamp": stamp, "results": all_summary}, f, indent=2)

    print(f"\nDone. Summary: {json_path}")


if __name__ == "__main__":
    main()
