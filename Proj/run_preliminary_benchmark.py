"""
Preliminary benchmark for progress report: multiple obstacle densities,
Dijkstra / A* / JPS4 via PathingGrid. Writes CSV, summary JSON, LaTeX snippet, and PNG plots.

Run: python run_preliminary_benchmark.py
"""

from __future__ import annotations

import csv
import json
import os
import random
import statistics
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

_PROJ = os.path.dirname(os.path.abspath(__file__))
_CODE = os.path.join(_PROJ, "src", "Snake Game Code")
if _CODE not in sys.path:
    sys.path.insert(0, _CODE)

from helper import Point
from pathing_grid import PathingGrid

from benchmark_interim import (
    MODES,
    Grid,
    make_grid,
    grid_to_pg,
    pick_start_goal,
    run_mode,
)

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def run_density_block(
    width: int,
    height: int,
    density: float,
    trials: int,
    rng: random.Random,
) -> Tuple[List[dict], int]:
    rows: List[dict] = []
    skipped = 0
    for t in range(trials):
        for _ in range(400):
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
                rows.append(
                    {
                        "trial": t,
                        "density": density,
                        "mode": mode,
                        "ok": ok,
                        "ms": round(ms, 6),
                        "expansions": exp,
                        "path_cells": plen,
                    }
                )
            break
        else:
            skipped += 1
    return rows, skipped


def aggregate(rows: List[dict]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for m in MODES:
        ms_list = [r["ms"] for r in rows if r["mode"] == m and r["ok"]]
        ex_list = [r["expansions"] for r in rows if r["mode"] == m and r["ok"]]
        out[m] = {
            "time_mean": statistics.mean(ms_list) if ms_list else None,
            "time_std": statistics.pstdev(ms_list) if len(ms_list) > 1 else 0.0,
            "exp_mean": statistics.mean(ex_list) if ex_list else None,
            "exp_std": statistics.pstdev(ex_list) if len(ex_list) > 1 else 0.0,
            "n": len(ms_list),
        }
    return out


def plot_bars(
    densities: List[float],
    series: Dict[str, Dict[float, float]],
    ylabel: str,
    outfile: str,
    title: str,
) -> None:
    if plt is None:
        return
    x = list(range(len(densities)))
    w = 0.25
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, mode in enumerate(MODES):
        vals = [series[mode].get(d, 0.0) for d in densities]
        offset = (i - 1) * w
        ax.bar([xi + offset for xi in x], vals, width=w, label=mode)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d:.2f}" for d in densities])
    ax.set_xlabel("Obstacle density")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)


def main() -> None:
    width, height = 50, 50
    densities = [0.15, 0.28, 0.40]
    trials_per = 24
    base_seed = 42
    out_dir = os.path.join(_PROJ, "results")
    fig_dir = os.path.join(_PROJ, "report", "figures")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(fig_dir, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_rows: List[dict] = []
    skipped_total = 0

    for di, d in enumerate(densities):
        rng = random.Random(base_seed + di * 1000)
        rows, sk = run_density_block(width, height, d, trials_per, rng)
        all_rows.extend(rows)
        skipped_total += sk

    csv_path = os.path.join(out_dir, f"preliminary_{stamp}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["density", "trial", "mode", "ok", "ms", "expansions", "path_cells"]
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k) for k in fieldnames if k in r})

    by_density: Dict[float, List[dict]] = {d: [] for d in densities}
    for r in all_rows:
        by_density[r["density"]].append(r)

    summary: Dict[str, Any] = {
        "stamp": stamp,
        "grid": f"{width}x{height}",
        "densities": densities,
        "trials_per_density": trials_per,
        "base_seed": base_seed,
        "skipped_unreachable": skipped_total,
        "per_density": {},
    }

    exp_series = {m: {} for m in MODES}
    time_series = {m: {} for m in MODES}

    for d in densities:
        agg = aggregate(by_density[d])
        summary["per_density"][str(d)] = agg
        for m in MODES:
            if agg[m]["exp_mean"] is not None:
                exp_series[m][d] = agg[m]["exp_mean"]
                time_series[m][d] = agg[m]["time_mean"]

    json_path = os.path.join(out_dir, f"preliminary_{stamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if plt is not None:
        plot_bars(
            densities,
            exp_series,
            "Mean expansions (heap pops)",
            os.path.join(fig_dir, "preliminary_expansions.png"),
            "Preliminary: mean expansions vs obstacle density",
        )
        plot_bars(
            densities,
            time_series,
            "Mean time (ms)",
            os.path.join(fig_dir, "preliminary_time_ms.png"),
            "Preliminary: mean search time vs obstacle density",
        )

    tex_path = os.path.join(_PROJ, "report", "generated_numbers.tex")
    lines = [
        "% auto-generated by run_preliminary_benchmark.py — do not edit by hand",
        f"\\newcommand{{\\BenchStamp}}{{{stamp}}}",
        f"\\newcommand{{\\BenchGrid}}{{{width}$\\times${height}}}",
        f"\\newcommand{{\\BenchTrialsPer}}{{{trials_per}}}",
        f"\\newcommand{{\\BenchSeed}}{{{base_seed}}}",
    ]
    for m in MODES:
        key = {"dijkstra": "Dij", "astar": "Ast", "jps4": "Jps"}[m]
        for i, d in enumerate(densities):
            a = summary["per_density"][str(d)][m]
            em = a["exp_mean"]
            tm = a["time_mean"]
            lines.append(
                f"\\newcommand{{\\{key}Exp{i}}}{{{em:.1f}}}" if em is not None else f"\\newcommand{{\\{key}Exp{i}}}{{--}}"
            )
            lines.append(
                f"\\newcommand{{\\{key}Time{i}}}{{{tm:.3f}}}" if tm is not None else f"\\newcommand{{\\{key}Time{i}}}{{--}}"
            )
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("Preliminary benchmark complete.")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}")
    print(f"  LaTeX numbers: {tex_path}")
    if plt:
        print(f"  Figures: {fig_dir}/preliminary_expansions.png, preliminary_time_ms.png")
    else:
        print("  (matplotlib not installed — skipped plots; pip install matplotlib)")


if __name__ == "__main__":
    main()
