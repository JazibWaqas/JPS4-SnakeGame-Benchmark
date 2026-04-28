# Dijkstra / A* / JPS4 on 4-Connected Grids

Course project for Algorithm Design & Analysis. We compare three optimal shortest-path algorithms on uniform-cost 4-connected grid maps and wrap them in an interactive Snake demo.

**Authors:** Jazib Waqas · Salman Adnan · Hunain Abbas

---

## Repository Layout

```
Proj/
  README.md
  requirements.txt
  docs/
    ADA_Project_Report.pdf       # assignment rubric / template
    LITERATURE_REVIEW.md         # notes on the four primary references
  src/
    algorithms/                  # pathfinding core (no game dependency)
      pathing_grid.py            # Dijkstra, A*, JPS4 implementations
      helper.py                  # Point, UnionFind, shared A* loop
    game/                        # Snake demo
      snake_game_jps4.py         # Tkinter game loop and UI
      snake_ai.py                # food selection and recovery logic
      Assets/                    # sounds and menu image
  benchmark/
    benchmark_utils.py           # shared grid/timing utilities
    run_benchmark.py             # main benchmark runner
    generate_figures.py          # figure generator (reads results/, writes report/figures/)
  results/                       # benchmark output (CSV + JSON summary)
  tests/                         # pytest test suite
  report/
    final_report.tex             # LaTeX source
    final_report.pdf             # compiled 7-page report
    figures/                     # figures embedded in the report
```

---

## Run the Snake Demo

```
python src/game/snake_game_jps4.py
```

Three rounds play on the same frozen board, one per algorithm. The HUD shows search time, expansions, and path length for each move. Press **F11** for fullscreen, **Esc** to exit.

## Install Dependencies

```
pip install -r requirements.txt
```

## Run the Benchmark

```
python benchmark/run_benchmark.py
```

Runs Dijkstra, A*, and JPS4 on 50x50 and 100x100 grids across 7 density levels (10%-40%), 30 trials per condition. Writes raw CSVs and an aggregated JSON summary to `results/`.

## Regenerate Figures

```
python benchmark/generate_figures.py
```

Reads the latest `results/extended_summary_*.json` and writes 5 figures to `report/figures/`. Requires `matplotlib`.

## Compile the Report

```
cd report
pdflatex final_report.tex
pdflatex final_report.tex
```

Two passes resolve cross-references. Requires MiKTeX or TeX Live. The compiled PDF is already at `report/final_report.pdf`.

## Run the Tests

```
python -m pytest tests -q
```

Covers path-length agreement across all three algorithms, expansion-order invariants, reachable food selection, and the snake's unreachable-food recovery. All 7 tests pass.

---

## References

1. Dijkstra (1959) — https://doi.org/10.1007/BF01386390
2. Hart, Nilsson, Raphael (1968) — https://doi.org/10.1109/TSSC.1968.300136
3. Harabor & Grastien (2011) — https://harabor.net/data/papers/harabor-grastien-aaai11.pdf
4. Baum (2025) — https://arxiv.org/abs/2501.14816
