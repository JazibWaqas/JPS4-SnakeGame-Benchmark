"""Dijkstra vs A* vs JPS4 on the same random grids. Dumps CSV + summary.txt."""

import argparse
import csv
import os
import random
import statistics
import sys
from collections import deque
from datetime import datetime

_CODE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "Snake Game Code")
if _CODE not in sys.path:
    sys.path.insert(0, _CODE)

from helper import Point
from pathing_grid import PathingGrid

MODES = ("dijkstra", "astar", "jps4")


def make_grid(width, height, density, rng):
    board = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if rng.random() < density:
                board[y][x] = True
    return board


def grid_to_pg(board):
    height = len(board)
    width = len(board[0])
    grid = PathingGrid(width, height, False)
    for y in range(height):
        for x in range(width):
            grid.set(x, y, board[y][x])
    return grid


def _bfs_farthest(board, source):
    height = len(board)
    width = len(board[0])
    seen = {source: 0}
    queue = deque([source])
    farthest = source
    best_dist = 0
    while queue:
        current = queue.popleft()
        dist = seen[current]
        if dist > best_dist:
            best_dist = dist
            farthest = current
        y, x = current
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width and not board[ny][nx] and (ny, nx) not in seen:
                seen[(ny, nx)] = dist + 1
                queue.append((ny, nx))
    return farthest, best_dist


def pick_start_goal(board, rng):
    # two-BFS trick: random seed -> farthest A -> farthest-from-A B
    height = len(board)
    width = len(board[0])
    free = [(y, x) for y in range(height) for x in range(width) if not board[y][x]]
    if len(free) < 2:
        return None
    seed = free[rng.randrange(len(free))]
    first, _ = _bfs_farthest(board, seed)
    second, dist = _bfs_farthest(board, first)
    if first == second or dist == 0:
        return None
    (y0, x0), (y1, x1) = first, second
    return Point(x0, y0), Point(x1, y1)


def run_mode(board, start, goal, mode):
    grid = grid_to_pg(board)
    path = grid.get_path_single_goal(start, goal, mode=mode)
    ok = path is not None and len(path) >= 2
    plen = len(path) if path else 0
    return ok, grid.last_ms, grid.last_expansions, plen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=50)
    parser.add_argument("--height", type=int, default=50)
    parser.add_argument("--density", type=float, default=0.28)
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", type=str, default="")
    args = parser.parse_args()

    proj_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = args.out_dir or os.path.join(proj_dir, "results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(out_dir, f"interim_benchmark_{stamp}")
    txt_path = base + ".txt"
    csv_path = base + ".csv"

    rng = random.Random(args.seed)
    rows = []
    skipped = 0

    for trial in range(args.trials):
        board = None
        start = None
        goal = None
        for _ in range(200):
            board = make_grid(args.width, args.height, args.density, rng)
            pair = pick_start_goal(board, rng)
            if pair is None:
                continue
            start, goal = pair
            grid = grid_to_pg(board)
            if not grid.reachable(start, goal):
                continue
            break
        else:
            skipped += 1
            continue

        for mode in MODES:
            ok, ms, expansions, plen = run_mode(board, start, goal, mode)
            rows.append({
                "trial": trial,
                "width": args.width,
                "height": args.height,
                "density": args.density,
                "seed": args.seed,
                "mode": mode,
                "ok": ok,
                "ms": round(ms, 4),
                "expansions": expansions,
                "path_cells": plen,
            })

    fieldnames = ["trial", "width", "height", "density", "seed", "mode", "ok", "ms", "expansions", "path_cells"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    by_mode = {m: {"ms": [], "exp": []} for m in MODES}
    for row in rows:
        if row["mode"] in MODES and row["ok"]:
            by_mode[row["mode"]]["ms"].append(row["ms"])
            by_mode[row["mode"]]["exp"].append(row["expansions"])

    lines = []
    lines.append("Interim benchmark (same instance per trial for all three modes)")
    lines.append(f"datetime={stamp}  width={args.width}  height={args.height}  density={args.density}")
    lines.append(f"trials_requested={args.trials}  seed={args.seed}  skipped_unreachable={skipped}")
    lines.append("")
    lines.append("Mean / stdev over successful runs (path found):")
    for mode in MODES:
        ms_list = by_mode[mode]["ms"]
        exp_list = by_mode[mode]["exp"]
        if not ms_list:
            lines.append(f"  {mode}: no successful runs")
            continue
        ms_stdev = statistics.pstdev(ms_list) if len(ms_list) > 1 else 0
        exp_stdev = statistics.pstdev(exp_list) if len(exp_list) > 1 else 0
        lines.append(f"  {mode}:  time_ms mean={statistics.mean(ms_list):.4f}  stdev={ms_stdev:.4f}")
        lines.append(f"        expansions mean={statistics.mean(exp_list):.1f}  stdev={exp_stdev:.1f}")
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
