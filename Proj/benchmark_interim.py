"""
Interim benchmark: same random grids, Dijkstra vs A* vs JPS4.
Writes results/ for the progress report (tables + optional plots).

Run from repo root:
    python Proj/benchmark_interim.py

Or from Proj:
    python benchmark_interim.py
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import statistics
import sys
from collections import deque
from datetime import datetime
from typing import List, Optional, Tuple

_CODE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "Snake Game Code")
if _CODE not in sys.path:
    sys.path.insert(0, _CODE)

from helper import Point
from pathing_grid import PathingGrid

Grid = List[List[bool]]
MODES = ("dijkstra", "astar", "jps4")


def make_grid(width: int, height: int, p: float, rng: random.Random) -> Grid:
    g = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if rng.random() < p:
                g[y][x] = True
    return g


def grid_to_pg(g: Grid) -> PathingGrid:
    h, w = len(g), len(g[0])
    pg = PathingGrid(w, h, False)
    for y in range(h):
        for x in range(w):
            pg.set(x, y, g[y][x])
    return pg


def _bfs_farthest(g: Grid, source: Tuple[int, int]) -> Tuple[Tuple[int, int], int]:
    """BFS from source; return (farthest reachable cell, distance)."""
    h, w = len(g), len(g[0])
    dist = {source: 0}
    q = deque([source])
    far_cell, far_d = source, 0
    while q:
        cur = q.popleft()
        d = dist[cur]
        if d > far_d:
            far_d, far_cell = d, cur
        y, x = cur
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not g[ny][nx] and (ny, nx) not in dist:
                dist[(ny, nx)] = d + 1
                q.append((ny, nx))
    return far_cell, far_d


def pick_start_goal(g: Grid, rng: random.Random) -> Optional[Tuple[Point, Point]]:
    """Pick a (start, goal) pair that is close to the graph diameter of the grid.

    Uses the classic two-BFS trick: from a random seed, BFS to its farthest cell A;
    from A, BFS to its farthest cell B. (A, B) is a 2-approximation of the diameter
    of the component containing the seed. This replaces the previous
    random-Manhattan-sampling heuristic, which systematically under-sampled long
    paths on grids with many free cells.
    """
    h, w = len(g), len(g[0])
    free = [(y, x) for y in range(h) for x in range(w) if not g[y][x]]
    if len(free) < 2:
        return None
    seed = free[rng.randrange(len(free))]
    a, _ = _bfs_farthest(g, seed)
    b, d = _bfs_farthest(g, a)
    if a == b or d == 0:
        return None
    (y0, x0), (y1, x1) = a, b
    return Point(x0, y0), Point(x1, y1)


def run_mode(g: Grid, start: Point, goal: Point, mode: str) -> Tuple[bool, float, int, int]:
    pg = grid_to_pg(g)
    path = pg.get_path_single_goal(start, goal, mode=mode)
    ok = path is not None and len(path) >= 2
    plen = len(path) if path else 0
    return ok, pg.last_ms, pg.last_expansions, plen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=50)
    ap.add_argument("--height", type=int, default=50)
    ap.add_argument("--density", type=float, default=0.28, help="fraction of cells blocked")
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", type=str, default="")
    args = ap.parse_args()

    proj = os.path.dirname(os.path.abspath(__file__))
    out_dir = args.out_dir or os.path.join(proj, "results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(out_dir, f"interim_benchmark_{stamp}")
    txt_path = base + ".txt"
    csv_path = base + ".csv"

    rng = random.Random(args.seed)
    rows: List[dict] = []
    skipped = 0

    for t in range(args.trials):
        for attempt in range(200):
            g = make_grid(args.width, args.height, args.density, rng)
            sg = pick_start_goal(g, rng)
            if sg is None:
                continue
            start, goal = sg
            pg = grid_to_pg(g)
            if not pg.reachable(start, goal):
                continue
            break
        else:
            skipped += 1
            continue

        for mode in MODES:
            ok, ms, exp, plen = run_mode(g, start, goal, mode)
            rows.append(
                {
                    "trial": t,
                    "width": args.width,
                    "height": args.height,
                    "density": args.density,
                    "seed": args.seed,
                    "mode": mode,
                    "ok": ok,
                    "ms": round(ms, 4),
                    "expansions": exp,
                    "path_cells": plen,
                }
            )

    fieldnames = [
        "trial",
        "width",
        "height",
        "density",
        "seed",
        "mode",
        "ok",
        "ms",
        "expansions",
        "path_cells",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    by_mode: dict = {m: {"ms": [], "exp": []} for m in MODES}
    for r in rows:
        if r["mode"] in MODES and r["ok"]:
            by_mode[r["mode"]]["ms"].append(r["ms"])
            by_mode[r["mode"]]["exp"].append(r["expansions"])

    lines = []
    lines.append("Interim benchmark (same instance per trial for all three modes)")
    lines.append(f"datetime={stamp}  width={args.width}  height={args.height}  density={args.density}")
    lines.append(f"trials_requested={args.trials}  seed={args.seed}  skipped_unreachable={skipped}")
    lines.append("")
    lines.append("Mean / stdev over successful runs (path found):")
    for m in MODES:
        ms_list = by_mode[m]["ms"]
        ex_list = by_mode[m]["exp"]
        if not ms_list:
            lines.append(f"  {m}: no successful runs")
            continue
        lines.append(
            f"  {m}:  time_ms mean={statistics.mean(ms_list):.4f}  stdev={statistics.pstdev(ms_list) if len(ms_list) > 1 else 0:.4f}"
        )
        lines.append(
            f"        expansions mean={statistics.mean(ex_list):.1f}  stdev={statistics.pstdev(ex_list) if len(ex_list) > 1 else 0:.1f}"
        )
    lines.append("")
    lines.append(f"CSV: {csv_path}")
    lines.append("")
    lines.append("How to cite in report: synthetic 4-connected grids, uniform random obstacles,")
    lines.append(f"density p={args.density}, {args.width}x{args.height}, {args.trials} instances, seed {args.seed}.")

    report = "\n".join(lines)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\nWrote:\n  {txt_path}\n  {csv_path}")


if __name__ == "__main__":
    main()
