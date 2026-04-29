# Shared utilities for benchmark scripts.
# Provides grid generation, start/goal selection, and per-mode timing.

import csv
import os
import random
import statistics
import sys
from collections import deque
from datetime import datetime

_PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ALGO = os.path.join(_PROJ, "src", "algorithms")
if _ALGO not in sys.path:
    sys.path.insert(0, _ALGO)

from helper import Point
from pathing_grid import PathingGrid

# Three algorithms to benchmark
MODES = ("dijkstra", "astar", "jps4")


# Generate random grid with specified obstacle density
def make_grid(width, height, density, rng):
    board = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if rng.random() < density:
                board[y][x] = True
    return board


# Convert boolean grid to PathingGrid object
def grid_to_pg(board):
    height = len(board)
    width = len(board[0])
    grid = PathingGrid(width, height, False)
    for y in range(height):
        for x in range(width):
            grid.set(x, y, board[y][x])
    return grid


# BFS to find farthest point from source (used for start/goal selection)
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
        # Explore 4 neighbors
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width and not board[ny][nx] and (ny, nx) not in seen:
                seen[(ny, nx)] = dist + 1
                queue.append((ny, nx))
    return farthest, best_dist


# Double-BFS: picks a start/goal pair that maximises path length
def pick_start_goal(board, rng):
    height = len(board)
    width = len(board[0])
    free = [(y, x) for y in range(height) for x in range(width) if not board[y][x]]
    if len(free) < 2:
        return None
    # Start from random free cell
    seed = free[rng.randrange(len(free))]
    # Find farthest point from seed
    first, _ = _bfs_farthest(board, seed)
    # Find farthest point from first point (this maximizes distance)
    second, dist = _bfs_farthest(board, first)
    if first == second or dist == 0:
        return None
    (y0, x0), (y1, x1) = first, second
    return Point(x0, y0), Point(x1, y1)


# Run one algorithm on one board, return (ok, ms, expansions, path_len)
def run_mode(board, start, goal, mode):
    grid = grid_to_pg(board)
    path = grid.get_path_single_goal(start, goal, mode=mode)
    ok = path is not None and len(path) >= 2
    plen = len(path) if path else 0
    return ok, grid.last_ms, grid.last_expansions, plen


# Compute mean/stdev for time and expansions per algorithm
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
