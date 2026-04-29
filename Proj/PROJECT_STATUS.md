# Project Status

**Last verified:** 2026-04-29  
**Status: Complete and verified working**

---

## What is this project?

Empirical comparison of Dijkstra, A\*, and JPS4 on uniform-cost 4-connected grid maps. Implemented from scratch in Python. Wrapped in an interactive Snake demo that runs all three algorithms on the same frozen board for a direct comparison.

**Authors:** Jazib Waqas · Salman Adnan · Hunain Abbas

---

## System Health

| Component | Status | Notes |
|---|---|---|
| Algorithm implementations | ✅ Verified | `pathing_grid.py` — Dijkstra, A\*, JPS4 |
| Snake game | ✅ Running | `src/game/snake_game_jps4.py` |
| Test suite | ✅ 7/7 pass | Run: `python -m pytest tests -q` |
| Benchmark data | ✅ Generated | `results/extended_summary_20260429_000313.json` |
| Report figures | ✅ 5 figures | All generated from real data in `report/figures/` |
| LaTeX report | ✅ Compiles | `report/final_report.pdf` — 7 pages |

---

## Key Verified Behaviors

### The algorithms always agree on path length
All three find the optimal path. If route cells differ across algorithms on the same board, something is broken. In practice they are always equal.

### Expected expansion ordering
```
JPS4 expansions <= A* expansions <= Dijkstra expansions
```
This holds on every valid (reachable) instance. Verified in `tests/test_pathfinding_correctness.py`.

### Food appearing close is normal
When the snake spawns and the food is nearby, all algorithms expand very few nodes and the numbers look similar. This is correct behavior. The benchmark scripts specifically avoid this by using a double-BFS to select maximally hard start/goal pairs.

### Results scale with density
The expansion gap between algorithms *widens* as obstacle density increases. Observed live in the game:

| Density | Dijkstra exp | A\* exp | JPS4 exp | JPS4 vs Dijkstra |
|---|---|---|---|---|
| 15% (Low) | 6,264 | 987 | 552 | 8.8% |
| 28% (Medium) | 10,255 | 3,706 | 633 | 6.2% |
| 40% (High) | 31,421 | 11,313 | 1,782 | 5.7% |

Route cells are equal across all runs — all algorithms find the same optimal path.

---

## Running the Project

```bash
# From Proj/

# Run the game
python src/game/snake_game_jps4.py

# Run all tests
python -m pytest tests -q

# Run the benchmark (takes a few minutes)
python benchmark/run_benchmark.py

# Regenerate report figures
python benchmark/generate_figures.py

# Compile the report (run twice for cross-references)
cd report
pdflatex final_report.tex
pdflatex final_report.tex
```

---

## Repository Layout

```
Proj/
  README.md
  requirements.txt
  docs/
    ADA_Project_Report.pdf       # assignment rubric
    LITERATURE_REVIEW.md         # notes on 4 primary references
  src/
    algorithms/                  # pure pathfinding — no game dependency
      pathing_grid.py            # Dijkstra, A*, JPS4
      helper.py                  # Point, UnionFind, A* internals
    game/                        # Snake demo
      snake_game_jps4.py         # Tkinter game loop
      snake_ai.py                # food selection, recovery logic
      Assets/                    # sounds, menu image
  benchmark/
    benchmark_utils.py           # shared grid generation and timing utilities
    run_benchmark.py             # main benchmark runner (50x50 + 100x100)
    generate_figures.py          # figure generator
  results/
    extended_50x50_20260429_000313.csv
    extended_100x100_20260429_000313.csv
    extended_summary_20260429_000313.json   # source of truth for report figures
  tests/
    conftest.py
    test_pathfinding_correctness.py
    test_snake_ai.py
    test_snake_game_recovery.py
    test_snake_gameplay_integration.py
  report/
    final_report.tex             # LaTeX source
    final_report.pdf             # compiled report (7 pages)
    figures/                     # 5 figures, all generated from real data
      results_50x50.pdf/.png
      results_100x100.pdf/.png
      expansion_ratio.pdf/.png
      jps4_speedup.pdf/.png
      jps_concept.pdf/.png
```

---

## Known Limitations (documented in report)

- JPS4 time is occasionally *slower* than A\* in Python despite fewer expansions. This is because each JPS4 "jump" involves a tight loop in pure Python, adding constant overhead per step that doesn't exist in compiled implementations. The expansion count always favors JPS4 — the time advantage appears at higher densities where the savings are large enough to outweigh the overhead.
- The Snake game resets the full board between algorithms (same snapshot) so the comparison is fair, but accumulated score is not carried over.

---

## Benchmark Ground-Truth Data

The canonical data source for the report is:
```
results/extended_summary_20260429_000313.json
```
420 problem instances per grid size (50x50 and 100x100), 7 density levels, 30 trials each, selected via double-BFS for maximum path difficulty. Do not delete this file. If you re-run the benchmark, update `generate_figures.py` to point to the new summary file (it auto-selects the latest one).
