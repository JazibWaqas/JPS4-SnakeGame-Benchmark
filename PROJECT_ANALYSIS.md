# Project Analysis — JPS4 Snake Game Benchmark

**Course:** Algorithm Design & Analysis, 8th Semester, Habib University  
**Team:** Jazib Waqas (`jw08048`), Salman Adnan (`sa07885`), Hunain Abbas (`sh08466`)  
**All benchmarks ran on:** April 5, 2026  
**Stage:** Interim / Progress Report

---

## Table of Contents

1. [Repository Structure](#1-repository-structure)
2. [Refrence/ — What It Is](#2-refrence--what-it-is)
3. [Proj/ — Active Project Overview](#3-proj--active-project-overview)
4. [Core Library: helper.py](#4-core-library-helperpy-109-lines)
5. [Core Library: pathing_grid.py](#5-core-library-pathing_gridpy-572-lines)
6. [Interactive Game: snake_game_jps4.py](#6-interactive-game-snake_game_jps4py-1069-lines)
7. [Benchmark 1: benchmark_interim.py](#7-benchmark-1-benchmark_interimpy-195-lines)
8. [Benchmark 2: run_preliminary_benchmark.py](#8-benchmark-2-run_preliminary_benchmarkpy-237-lines)
9. [Figure Generation: generate_report_figures.py](#9-figure-generation-generate_report_figurespy-148-lines)
10. [Report: progress_report_acl.tex](#10-report-progress_report_acltex-245-lines)
11. [Auto-generated Numbers: generated_numbers.tex](#11-auto-generated-numbers-generated_numberstex-24-lines)
12. [Presentation: make_presentation.py](#12-presentation-make_presentationpy-400-lines)
13. [Benchmark Results Data](#13-benchmark-results-data)
14. [Refrence/ — Detailed Breakdown](#14-refrence--detailed-breakdown)
15. [What Has Been Achieved](#15-what-has-been-achieved)
16. [What Remains (Stated Future Work)](#16-what-remains-stated-future-work)
17. [Known Issues](#17-known-issues)

---

## 1. Repository Structure

```
Code/
├── Proj/                              ← Active project (all original work)
│   ├── README.md
│   ├── requirements.txt               ← numpy>=1.20, matplotlib>=3.7
│   ├── Algos_Project_Proposal.pdf     ← Binary PDF, original proposal
│   ├── src/Snake Game Code/
│   │   ├── helper.py                  ← 109 lines: data structures + search core
│   │   ├── pathing_grid.py            ← 572 lines: grid + all 3 algorithms
│   │   ├── snake_game_jps4.py         ← 1069 lines: Tkinter interactive game
│   │   └── Assets/
│   │       ├── snake_game.png         ← Splash screen image
│   │       ├── roku_snake.wav         ← Background music (loops)
│   │       └── price.wav              ← Game-over sound
│   ├── benchmark_interim.py           ← 195 lines: single-density benchmark
│   ├── run_preliminary_benchmark.py   ← 237 lines: multi-density benchmark
│   ├── generate_report_figures.py     ← 148 lines: matplotlib figure generator
│   ├── results/                       ← 12 output files from all runs
│   │   ├── interim_benchmark_20260405_152048.{csv,txt}
│   │   ├── interim_benchmark_20260405_153807.{csv,txt}
│   │   ├── preliminary_20260405_153243.{csv,json}
│   │   ├── preliminary_20260405_153315.{csv,json}
│   │   ├── preliminary_20260405_153748.{csv,json}
│   │   └── preliminary_20260405_160433.{csv,json}  ← canonical final run
│   └── report/
│       ├── progress_report_acl.tex    ← 245 lines: ACL-format LaTeX paper
│       ├── generated_numbers.tex      ← 24 lines: auto-generated data macros
│       ├── make_presentation.py       ← ~400 lines: python-pptx slide generator
│       ├── PRESENTATION_CONTENT.txt   ← 241 lines: speaker notes
│       ├── OVERLEAF_INSTRUCTIONS.txt  ← Upload guide
│       └── figures/                   ← Generated PNG/PDF plots
└── Refrence/                          ← Reference materials from a prior team
    ├── README.md                      ← Credits: Sameer Kamani, Ibad Nadeem, Taqi
    ├── Sample Code/
    │   └── paper_jps4_rust.py         ← Python port of Baum's Rust JPS4
    ├── src/
    │   ├── Benchmarking Code/
    │   │   ├── Algorithms/{a_star.py, jump_point_search.py, helper.py}
    │   │   ├── Benchmark_Functions/{grid_and_benchmarks.py, maze_and_benchmarks.py, ...}
    │   │   ├── Helper_Functions/{plotting_helper_functions.py, report_helper_functions.py}
    │   │   └── main.py
    │   └── Snake Game Code/           ← Earlier game iteration
    ├── Research Materials/
    │   ├── Jump Point Search Pathfinding in 4-connected Grids.pdf  ← Baum 2025
    │   └── tests/
    │       ├── benchmark_report.txt   ← Earlier JPS4 vs A* results
    │       └── benchmark_results/     ← density_0.00–0.80, large_grid, maze
    └── Checkpoint 1/                  ← 4 checkpoint PDF+LaTeX report pairs
        ├── Checkpoint 1 Report.pdf + Source.tex
        ├── Checkpoint 2/ → Checkpoint 2 Report.pdf + Source.tex
        │   └── Checkpoint 4/ → Checkpoint 4 Report.pdf + Presentation.pdf + Source.tex
        └── Checkpoint 3/ → Checkpoint 3 Report.pdf + Source.tex
```

---

## 2. Refrence/ — What It Is

`Refrence/` is **not** the current team's work. Its `README.md` credits a completely different team:

- **Sameer Kamani**, **Muhammad Ibad Nadeem**, **Muhammad Taqi** — CS, Habib University  
- **Supervisor:** Dr. Waqar Saleem

The current team (Jazib/Salman/Hunain) uses this folder as a reference baseline. It contains a prior implementation of JPS4 vs A\* benchmarking, the Baum (2025) paper PDF, four checkpoint reports documenting the reference team's project progression, and the canonical Rust-to-Python JPS4 reference implementation.

The reference team's benchmark results showed a critical correctness bug: at density 0.20 their JPS4 returned paths of length 68.3 vs A\*'s 254.9. The current team's implementation fixes this — all three algorithms return equal path lengths on every trial.

---

## 3. Proj/ — Active Project Overview

**Goal:** Benchmark and compare Dijkstra, A\*, and JPS4 on 4-connected grid maps (cardinal movement only: up/down/left/right, unit cost).

**Two metrics:**
- **Node expansions** — heap pops; hardware-independent; measures algorithmic quality
- **Wall-clock time (ms)** — measures implementation cost; less reliable in Python due to interpreter overhead

**Key architectural decision:** All three algorithms share the exact same `AstarContext.astar_jps()` search loop. The only differences are:

| Algorithm | `successors` function | `heuristic` function |
|---|---|---|
| Dijkstra | `standard_astar_successors` | `h = 0` |
| A\* | `standard_astar_successors` | `h = Manhattan distance` |
| JPS4 | `jps_successors` | `h = Manhattan distance` |

Any measured difference is purely algorithmic.

---

## 4. Core Library: `helper.py` (109 lines)

### `Point`
2D coordinate class. Supports `__add__`, `__eq__`, `__hash__` (required for dict keys / set membership).

| Method | Behaviour |
|---|---|
| `manhattan_distance(other)` | `abs(dx) + abs(dy)` |
| `neumann_neighborhood()` | 4 cardinal neighbours: up `(0,-1)`, right `(1,0)`, down `(0,1)`, left `(-1,0)` |
| `direction_to(other)` | Normalises dx/dy to ±1 unit step in each axis |

### `UnionFind`
Path-compressed disjoint-set (no union-by-rank). Methods: `find(x)`, `union(x, y)`, `equiv(x, y)`.  
Used for O(α) connectivity queries: "is there any path between cell A and cell B?"

### `SearchNode`
Priority queue entry storing `estimated_cost` (f = g + h), `cost` (g), `node`, `parent`.  
`__lt__` compares `estimated_cost` first; ties broken by `cost` (favours deeper nodes).

### `AstarContext`
The single shared search loop for all three algorithms:

```python
astar_jps(start, successors, heuristic, success) → (path, cost) or None
```

- Clears fringe, parents, expansion counter on each call
- Uses Python `heapq` as open list
- Tracks `self.expansions` (heap pops = node expansions)
- Passes `self.parents[current.node][0]` (the parent `Point`) to `successors` — this is what enables JPS4 to know its movement direction
- Path reconstruction follows `parents` chain back to start

---

## 5. Core Library: `pathing_grid.py` (572 lines)

### `PathingGrid` — Fields

| Field | Type | Purpose |
|---|---|---|
| `grid` | `List[List[bool]]` | `True` = blocked |
| `components` | `UnionFind` | Connectivity tracking |
| `components_dirty` | `bool` | Lazy rebuild flag |
| `context` | `AstarContext` | Shared search loop |
| `last_ms` | `float` | Time of last search |
| `last_expansions` | `int` | Expansions of last search |
| `last_path_len` | `int` | Path length of last search |

### Grid Operations

- `set(x, y, blocked)` — sets cell; marks `components_dirty = True` if value changed
- `can_move_to(pos)` — in-bounds AND not blocked
- `generate_components()` — rebuilds `UnionFind` by scanning all free cells and unioning 4-adjacent free neighbours
- `reachable(start, end)` — lazy-rebuilds components if dirty, then `components.equiv(...)`

### Standard A\* Successors

`standard_astar_successors(node, goal)` — returns all 4 valid cardinal neighbours at cost `C=1`. Ignores the `parent` argument entirely (so Dijkstra and A\* behave identically to classic implementations).

### JPS4 — Three Interdependent Methods

#### `jps_prune_neighbors(parent, node)`

| Condition | Kept neighbours |
|---|---|
| `parent is None` (start node) | All 4 free cardinal neighbours |
| Moving horizontally (dx ≠ 0) | Continue same direction + forced vertical neighbours |
| Moving vertically (dy ≠ 0) | Continue same direction + forced horizontal neighbours |

**Forced neighbour detection:**  
When moving right at node `N` with parent `P`:  
If `(P.x, P.y+1)` is **blocked** but `(N.x, N.y+1)` is **free** → `(N.x, N.y+1)` is forced (and vice versa for dy=-1).

#### `jps_jump(current, direction, goal)`

1. Step `next_point = current + direction`
2. If blocked/out-of-bounds → return `None`
3. If `next_point == goal` → return `next_point`
4. **Horizontal (dx ≠ 0):** Check for forced vertical neighbours (for debug only), then **always return `next_point`** — this is the JPS4 horizontal-first key optimisation. Every horizontal step is immediately a candidate successor.
5. **Vertical (dy ≠ 0):** Check for forced horizontal neighbours → return if found. Otherwise **recurse**: `jps_jump(next_point, direction, goal)` — continues straight until forced neighbour, obstacle, or goal.

#### `jps_successors(parent, node, goal)`

1. If `node == goal` → return `[(node, 0)]`
2. If any adjacent cell is the goal → return `[(adj, C)]` directly
3. Call `jps_prune_neighbors(parent, node)`
4. For each pruned neighbour: compute `direction_to(neighbour)`, call `jps_jump(node, direction, goal)`
5. Successful jumps → add as successors with `cost = C * manhattan_distance(node, jump_result)`
6. **Fallback:** if no successors and `parent is not None` → add all free non-parent neighbours (standard A\* behaviour)

### Path Dispatch — `get_waypoints_single_goal(start, goal, mode)`

Executed in order:
1. Manhattan distance == 1 → return `[start, goal]` immediately (0 expansions)
2. `find_direct_path(start, goal)` → clear horizontal or vertical line → return immediately
3. `reachable(start, goal)` via UnionFind → return `None` if disconnected
4. Run search (Dijkstra / A\* / JPS4)
5. If JPS4 returns `None` → fall back to standard A\* automatically
6. Record `last_ms`, `last_expansions`
7. `post_process_path()` — line-of-sight smoothing: finds furthest waypoint reachable via straight line and skips intermediate ones
8. `validate_path()` — adjacency + bounds check; falls back to unoptimised if post-processing breaks validity

### `get_path_single_goal(start, goal, mode)`

Calls `get_waypoints_single_goal`, then `waypoints_to_path()` which fills every gap between waypoints by stepping one cell at a time. Returns a fully step-by-step adjacent path.

---

## 6. Interactive Game: `snake_game_jps4.py` (1069 lines)

> **Platform note:** Uses `winsound` (Windows-only). Will crash on Linux on import. Developed on Windows (CSV paths show `C:\Users\OMNIBOOK\...`).

### Constants

| Name | Value | Meaning |
|---|---|---|
| `GRID_N` | 20 | Board is 20×20 |
| `EMPTY` | 0 | Free cell |
| `BODY` | 1 | Snake body |
| `FOOD` | 2 | Apple |
| `HEAD` | 3 | Snake head |
| `WALL` | 4 | Obstacle |
| `HUD_MIN` | 28 | Minimum HUD height (px) |

Cell colors: `['white', 'maroon', 'red', 'yellow', 'grey', 'white']` (indexed by cell value).

### Board Layouts

**EASY:** Outer walls + sparse interior walls at a few rows (5, 8, 13, 17). Mostly open.

**HARD:** Dense maze-like layout. Obstacles on nearly every other row/column creating narrow corridors throughout the 20×20 grid.

### `Snake` Class

**`food_search()`:**
1. Copies board, removes tail cell (`EMPTY`) — tail vacates next tick so path can route through it
2. Builds `PathingGrid`: WALL and BODY are blocked; HEAD and FOOD remain free
3. Tries `find_direct_path` first (zero-cost for straight shots)
4. Calls `pg.get_path_single_goal(start, food_pt, mode=current_path_mode)`
5. Records `pf_ms`, `pf_exp`, `pf_steps`; calls `record_algo_session`
6. Validates next step is in bounds and `EMPTY` or `FOOD`
7. Returns direction lambda (`STEP_UP/DOWN/LEFT/RIGHT`)

**`find_safest_move()` (emergency fallback):**  
Scores each legal adjacent move:

```
score = (future_moves_count × 10) + (open_space_score × 2) + wall_distance
```

- `future_moves_count`: number of immediately reachable moves from new position
- `open_space_score`: flood-fill up to depth 6, weighted by `(max_depth - depth + 1)`
- `wall_distance`: sum of distances to walls in 8 directions (up to 4 cells each)

**`change_positions(direction)`:**
- Moves head, slides body, eats food (grows + spawns new apple) or drops tail
- Safety check: refuses illegal moves, falls back to a random legal move

**Game tick (`schedule_next`):**
- Runs every 200ms via `banana.after(200, ...)`
- Fallback move → reschedule after 300ms
- After 5 consecutive `no_path_count` → game over

### Compare Mode

`on_compare_click()`: Freezes game. Calls `run_three_way_compare()` which:
- Creates one board copy with tail removed
- If direct path exists → uses it identically for all 3 algorithms (avoids unnecessary search)
- Otherwise: runs each algorithm on its own fresh `PathingGrid` instance from the same board snapshot
- Returns list of `{"mode", "fill", "cells", "ms", "exp", "cells_n", "ok"}`

**Compare overlay colors:**
| Algorithm | Color |
|---|---|
| Dijkstra | `#d48888` (red-tinted) |
| A\* | `#88c488` (green-tinted) |
| JPS4 | `#6a9fd4` (blue-tinted) |

Paths drawn with nested insets so overlapping paths remain distinguishable.

### UI Layout

| Section | Details |
|---|---|
| Window | `Tk()` root, dark `#2b2b2b`, 62% × 72% of screen, resizable, min 400×460 |
| `top_bar` | Algorithm buttons, Compare/Resume buttons, compare text, per-search metrics, session totals, legend |
| `game_body/canvas` | Game rendering, dark `#141414` |
| Start menu | Splash screen with `snake_game.png` (auto-scaled), Easy/Hard buttons at `relx=0.38/0.62, rely=0.92` |

**Algorithm buttons:** Active = sunken, `#2d5a87` blue. Inactive = raised, `#404040`.

**Metrics displayed:**
- Last search: `X.XX ms | Expansions: Y | Route cells: Z`
- Session: per-algorithm running average ms + cumulative expansions

### Session Tracking

`algo_session` dict accumulates `n`, `ms`, `exp`, `steps` per algorithm. Resets on difficulty selection. `session_line()` formats these in the HUD as `"Dij n=X avg Y.YYms tot exp Z | A* ... | JPS ..."`.

### Assets

| File | Purpose |
|---|---|
| `Assets/roku_snake.wav` | Background music, loops asynchronously |
| `Assets/price.wav` | Game-over sound, async |
| `Assets/snake_game.png` | Splash screen background image |

---

## 7. Benchmark 1: `benchmark_interim.py` (195 lines)

**Purpose:** Single-density statistical benchmark.

**Default parameters:** 50×50, density=0.28, 40 trials, seed=42.

**Per-trial procedure:**
1. Generate random grid (`True` per cell with probability `p`)
2. Pick start/goal: 80 random pair attempts, maximise Manhattan distance; up to 200 retries if unreachable
3. Run all 3 modes on the **same grid instance** via fresh `PathingGrid` per mode (no state leakage)
4. Record: `trial, width, height, density, seed, mode, ok, ms, expansions, path_cells`

**Output:**
- `results/interim_benchmark_<stamp>.csv` — per-trial raw data
- `results/interim_benchmark_<stamp>.txt` — mean/population stdev summary + citation template

**Actual results (both runs, density=0.28, 50×50):**

| Run | Stamp | Trials | Dijkstra exp | Dijkstra ms | A\* exp | A\* ms | JPS4 exp | JPS4 ms |
|---|---|---|---|---|---|---|---|---|
| 1 | 152048 | 25 | 1680.8 | 5.279 | 551.3 | 1.954 | 1430.2 | 9.218 |
| 2 | 153807 | 30 | 1684.2 | 5.588 | 568.4 | 2.092 | 1430.2 | 9.184 |

JPS4 expansion count is identical across both runs (1430.2) — reproducibility confirmed.

---

## 8. Benchmark 2: `run_preliminary_benchmark.py` (237 lines)

**Purpose:** Multi-density sweep for the progress report.

**Parameters:** 50×50, densities `[0.15, 0.28, 0.40]`, 24 trials per density.  
Seeds: `42 + density_index × 1000` → 42, 1042, 2042 (independent RNG per density).

**Stricter acceptance:** A trial only counts if **all three algorithms** return a valid path. Prevents partial-comparison bias.

**Output:**
1. `results/preliminary_<stamp>.csv` — columns: density, trial, mode, ok, ms, expansions, path_cells
2. `results/preliminary_<stamp>.json` — aggregate stats: time_mean, time_std, exp_mean, exp_std, n per (density, mode)
3. `report/generated_numbers.tex` — 20 LaTeX `\newcommand` macros (see §11)
4. `report/figures/preliminary_expansions.png`, `preliminary_time_ms.png` — bar charts

**4 runs total:** 153243, 153315, 153748, 160433. Final run (160433) is canonical and used in the report.

### Canonical Results (run 160433, n=24 per cell, 0 skipped)

| Density | Algorithm | Exp mean | Exp stdev | Time mean (ms) | Time stdev (ms) |
|---|---|---|---|---|---|
| 15% | Dijkstra | 2062.2 | 56.3 | 7.067 | 0.950 |
| 15% | A\* | 1019.7 | 197.1 | 3.741 | 0.885 |
| 15% | JPS4 | **488.4** | 243.0 | 4.432 | 2.145 |
| 28% | Dijkstra | 1659.2 | 148.0 | 4.955 | 0.459 |
| 28% | A\* | **629.0** | 192.9 | 2.112 | 0.644 |
| 28% | JPS4 | 969.8 | 795.3 | 6.216 | 5.365 |
| 40% | Dijkstra | 915.0 | 172.4 | 2.729 | 0.496 |
| 40% | A\* | **513.2** | 184.1 | 1.701 | 0.714 |
| 40% | JPS4 | 681.6 | 178.2 | 3.132 | 1.098 |

**All path lengths equal across all trials — correctness fully verified.**

### Key Findings

| Finding | Detail |
|---|---|
| A\* vs Dijkstra | A\* consistently ~50% of Dijkstra's expansions at all densities |
| JPS4 at low density (15%) | 488 expansions — 76% reduction vs Dijkstra, beats A\* decisively |
| JPS4 at medium density (28%) | 970 expansions — **worse** than A\*'s 629. Short corridors reduce jump benefit. |
| JPS4 at high density (40%) | 682 expansions — still worse than A\*'s 513 but narrowing |
| JPS4 wall-clock time | Slower than A\* at all densities despite fewer nodes at 15% — Python interpreter amplifies the complex inner loop |
| Cross-over density | Not yet determined — somewhere between 15% and 28% |

---

## 9. Figure Generation: `generate_report_figures.py` (148 lines)

Hardcodes benchmark values from run 160433. Produces three files in `report/figures/`:

### Figure 1: `results_combined.pdf/png`
7.0×2.9 inches. Two side-by-side line charts:
- **(a)** Mean node expansions vs. obstacle density
- **(b)** Mean wall-clock time vs. density

Algorithm styles: Dijkstra = red `#e05c5c` circles, A\* = blue `#4d94e0` squares, JPS4 = green `#2ca02c` diamonds.

### Figure 2: `expansion_ratio.pdf/png`
3.5×2.6 inches. A\* and JPS4 as % of Dijkstra's expansions, with Dijkstra dashed at 100%.  
Shows JPS4 at ~23.7% at 15% density, crossing above A\*'s ~50% somewhere between 15% and 28%.

### Figure 3: `jps_concept.png`
3.0×2.4 inches. Schematic 9×7 grid illustrating jump points vs A\* expansion:
- Light-blue cells = A\* expanded
- Dark green diamonds = JPS4 jump points (far fewer cells)
- Red S = start, Orange G = goal, grey blocks = obstacles

---

## 10. Report: `progress_report_acl.tex` (245 lines)

ACL two-column LaTeX, 11pt, A4. Uses Times font, `microtype`, `booktabs`, `hyperref`.  
Live numbers pulled from `\input{generated_numbers}`.

### Sections

**Abstract:** Three algorithms compared. A\* halves Dijkstra. JPS4 reduces 76% at low density. Correctness verified. Visualization in development.

**§1 Problem:** 4-connected grid definition, unit-cost movement, why naive search is too slow. Two metrics justified.

**§2 Algorithms:**
- Dijkstra: no heuristic, uniform wavefront, explores entire reachable area
- A\*: Manhattan heuristic = valid lower bound on 4-connected unit-cost grids → optimality guaranteed
- JPS4: symmetry pruning (Harabor & Grastien 2011, Baum 2025); skips symmetric-cost corridors, stops at jump points only; 4-connected is harder than 8-connected (no diagonals changes where symmetry arises)
- All share the same search loop — differences are purely algorithmic

**§3 Preliminary Results:** Table 1 (exact numbers above), embedded Figure 1. Analysis:
- 15%: JPS4 488 vs A\* 1020 vs Dijkstra 2062 = 76% reduction over Dijkstra
- 28%: JPS4 970 > A\* 629 — obstacles fragment corridors, pruning overhead outweighs benefit
- Wall-clock: JPS4 slower at all densities despite fewer nodes at 15% — Python overhead
- All path lengths equal every trial ✓

**§4 Challenges:**
1. Fair timing — Python penalises JPS4's complex loop; node expansions are the reliable signal
2. Grid scale — 50×50 finishes <10ms; JPS4's advantage expected to grow at 100×100 / 200×200
3. Density boundary — cross-over point between A\* and JPS4 unknown

**§5 Next Plan:**
- Week 13: 100×100 and 200×200 benchmarks; sweep density 5%–50% in 5% steps; complete snake demo
- Week 14: Finalize data; compare to literature; polish
- Week 15: Final presentation, live demo, submission

**References:**
- Baum (2025) — arXiv:2501.14816
- Hart et al. (1968) — IEEE TSSC, foundational A\* paper
- Harabor & Grastien (2011) — AAAI-11, original JPS

---

## 11. Auto-generated Numbers: `generated_numbers.tex` (24 lines)

Generated by `run_preliminary_benchmark.py`. **Do not edit by hand.** Contains 20 macros:

```latex
\newcommand{\BenchStamp}{20260405_160433}
\newcommand{\BenchGrid}{50$\times$50}
\newcommand{\BenchTrialsPer}{24}
\newcommand{\BenchSeed}{42}
\newcommand{\DijExp0}{2062.2}   % Dijkstra expansions at 15%
\newcommand{\DijTime0}{7.067}   % Dijkstra ms at 15%
\newcommand{\DijExp1}{1659.2}   % Dijkstra expansions at 28%
\newcommand{\DijTime1}{4.955}
\newcommand{\DijExp2}{915.0}    % Dijkstra expansions at 40%
\newcommand{\DijTime2}{2.729}
\newcommand{\AstExp0}{1019.7}   % A* expansions at 15%
\newcommand{\AstTime0}{3.741}
\newcommand{\AstExp1}{629.0}
\newcommand{\AstTime1}{2.112}
\newcommand{\AstExp2}{513.2}
\newcommand{\AstTime2}{1.701}
\newcommand{\JpsExp0}{488.4}    % JPS4 expansions at 15%
\newcommand{\JpsTime0}{4.432}
\newcommand{\JpsExp1}{969.8}
\newcommand{\JpsTime1}{6.216}
\newcommand{\JpsExp2}{681.6}
\newcommand{\JpsTime2}{3.132}
```

---

## 12. Presentation: `make_presentation.py` (~400 lines)

Programmatically generates `ADA_Interim_Presentation_v2.pptx` via `python-pptx`. Dark theme (`RGB(15, 23, 42)`).

| Slide | Content |
|---|---|
| 1/5 — Title | Project title, team names, course, affiliation |
| 2/5 — Methodology | Benchmark design, fairness justification (shared loop), three-density rationale |
| 3/5 — Results | Data table + Figure 1 embedded; per-finding observations |
| 4/5 — Discussion | Three insight cards (why JPS4 wins open, loses dense, timing gap); open question: find cross-over |
| 5/5 — Next Steps | Snake demo status, Week 13–15 timeline |

`PRESENTATION_CONTENT.txt` (241 lines) provides full speaker notes, bullet points, visual suggestions, anticipated Q&A, and timing guidance for each slide.

---

## 13. Benchmark Results Data

### `results/` — All Stored Runs

| File | Type | Trials | Density | Notes |
|---|---|---|---|---|
| `interim_benchmark_20260405_152048` | interim | 25 | 0.28 | First run |
| `interim_benchmark_20260405_153807` | interim | 30 | 0.28 | Second run |
| `preliminary_20260405_153243` | preliminary | 24×3 | 0.15/0.28/0.40 | First run |
| `preliminary_20260405_153315` | preliminary | 24×3 | 0.15/0.28/0.40 | Second run |
| `preliminary_20260405_153748` | preliminary | 24×3 | 0.15/0.28/0.40 | Third run |
| `preliminary_20260405_160433` | preliminary | 24×3 | 0.15/0.28/0.40 | **Canonical — used in report** |

All interim runs: seed=42, 50×50, density=0.28. All preliminary runs: base_seed=42, 50×50, three densities.

### CSV Format

**Interim:** `trial, width, height, density, seed, mode, ok, ms, expansions, path_cells`  
**Preliminary:** `density, trial, mode, ok, ms, expansions, path_cells`

---

## 14. Refrence/ — Detailed Breakdown

### `Sample Code/paper_jps4_rust.py`

Python port of Baum (2025) Rust JPS4 reference. Key differences from the Proj implementation:

| Aspect | `paper_jps4_rust.py` | `Proj/pathing_grid.py` |
|---|---|---|
| Movement | 4-connected or 8-connected (configurable) | 4-connected only |
| Edge costs | Configurable (D=99, C=70) or unit | Unit cost only |
| Neighbour tracking | Bitmask `neighbours[y][x]` | Direct free-cell check |
| `AstarContext` bug | Iterates entire `parents` dict to find current node (O(n), fragile) | Stores `Point` directly in `SearchNode` (O(log n)) |
| Diagonal jumps | `jump_straight` + `jump` handle both axes | Cardinal only |

### `src/Benchmarking Code/Algorithms/a_star.py`

Standalone A\* (220 lines). Uses a `closed_set` (vs. Proj's cost-comparison in `parents` dict). Supports `on_node_expansion` callback for benchmarking. Has `complete_path()` to fill waypoint gaps.

### `main.py` — Benchmark Types

| Flag | Grid size | Densities | Trials |
|---|---|---|---|
| `quick` | 100×100 | 0.40, 0.60, 0.80 | 3 |
| `research` | variable | 0.00–0.80 in 0.10 steps | multiple |
| `maze` | 50–300×50–300 | maze-generated | 5 |
| `large` | 100–500 | variable | variable |
| `custom` | `--grid-size` | `--obstacle-density` | `--trials` |

### `Research Materials/tests/benchmark_report.txt` — Earlier Results

Results from reference team's implementation (JPS4 vs A\*, no Dijkstra):

| Density | JPS4 Exp | A\* Exp | Ratio | JPS4 Path | A\* Path |
|---|---|---|---|---|---|
| 0.00 | 255.9 | 254.9 | 1.00 | 254.9 | 254.9 |
| 0.20 | 938.3 | 254.9 | 3.68 | **68.3** | 254.9 ← BUG |
| 0.30 | 612.4 | 254.9 | 2.40 | **110.0** | 254.9 ← BUG |
| 0.40 | 241.4 | 254.9 | 0.95 | **65.9** | 254.9 ← BUG |
| 0.50 | 1687.8 | 1547.4 | 1.09 | 289.0 | 289.0 |
| 0.60 | 1171.4 | 1084.0 | 1.08 | 290.6 | 290.6 |
| 0.70 | 895.4 | 834.2 | 1.07 | 276.0 | 276.0 |
| 0.80 | 804.0 | 753.1 | 1.07 | 276.4 | 276.4 |

At densities 0.20–0.40, JPS4 path lengths are 4× shorter than A\* — the reference JPS4 was returning **suboptimal (shorter) paths**, indicating a correctness bug. The Proj implementation fixes this.

---

## 15. What Has Been Achieved

### Algorithmic

- [x] Full Dijkstra, A\*, JPS4 implemented sharing one search loop
- [x] JPS4 horizontal-first pruning and forced-neighbour detection
- [x] JPS4 recursive vertical jump
- [x] JPS4 fallback to A\* if it returns no path
- [x] UnionFind-based O(α) reachability short-circuit
- [x] Line-of-sight path post-processing
- [x] Path validation with adjacency + bounds checking

### Game

- [x] Complete Tkinter Snake game (Easy + Hard board layouts)
- [x] Real-time algorithm switching mid-game
- [x] Compare mode (frozen board, all 3 paths overlaid in colour)
- [x] Tail-removal trick for routing
- [x] Emergency fallback move heuristic (flood-fill scoring)
- [x] Per-search and session-cumulative metrics in HUD
- [x] Score tracking, food spawning, game-over detection
- [x] Resizable window, fullscreen support

### Benchmarking

- [x] Reproducible benchmark scripts (fixed seeds, reachability verification)
- [x] Single-density benchmark (benchmark_interim.py)
- [x] Multi-density benchmark (run_preliminary_benchmark.py)
- [x] CSV, JSON, LaTeX, PNG output
- [x] 6 benchmark runs completed and stored

### Results & Reporting

- [x] Preliminary results: 24 trials × 3 densities, 50×50 grid
- [x] Correctness verified: equal path lengths across all algorithms on all trials
- [x] ACL-format LaTeX progress report with live-injected numbers
- [x] Three publication-quality figures (combined chart, ratio chart, concept schematic)
- [x] 5-slide PowerPoint presentation (programmatically generated)
- [x] Speaker notes document (241 lines)

---

## 16. What Remains (Stated Future Work)

### Week 13
- [ ] Scale benchmarks to 100×100 and 200×200 grids
- [ ] Sweep density 5%–50% in 5% steps to find A\*/JPS4 cross-over point
- [ ] Complete Snake game as demo piece (game works; needs polish for presentation)

### Week 14
- [ ] Finalize all tables and figures with larger-grid data
- [ ] Compare results to Baum (2025) literature benchmarks
- [ ] Write full Discussion section with limitations
- [ ] Bring report to final submission quality

### Week 15
- [ ] Final presentation and live demo
- [ ] Submission

---

## 17. Known Issues

| Issue | Detail |
|---|---|
| `winsound` dependency | Windows-only; game crashes on import on Linux/macOS |
| JPS4 silent fallback | If JPS4 returns `None`, code silently falls back to A\* — some "JPS4" measurements may actually be A\* results |
| 50×50 scale | All algorithms finish <10ms; timing differences are below reliable measurement threshold |
| JPS4 wall-clock | Despite fewer nodes at 15%, JPS4 is slower than A\* at all densities — Python interpreter cost of complex inner loop |
| Unknown cross-over | JPS4 beats A\* in expansions at 15% but not 28%; exact density where they trade off is not yet measured |
