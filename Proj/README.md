# Grid pathfinding demo (Dijkstra, A*, JPS4)

Course project: compare shortest-path algorithms on 4-connected grids. This folder holds the interactive Snake demo and pathfinding core.

## Run the game

From the repository root (or from this folder), with Python 3 and NumPy installed:

```text
python "Proj/src/Snake Game Code/snake_game_jps4.py"
```

Or:

```text
cd "Proj/src/Snake Game Code"
python snake_game_jps4.py
```

Assets load from the same directory as the script (`Assets/`), so running via the path above keeps sounds and the menu image working.

## Controls

- The window starts at a fraction of your screen size; you can **resize** or **maximize** it. The **40x40 grid** scales so it stays centered and as large as fits in the lower pane (HUD strip scales with window height). View > Toggle fullscreen, or **F11**; **Esc** leaves fullscreen.
- Choose a density preset from the start screen.
- The demo runs the same frozen board through three rounds in order: `Dijkstra`, `A*`, then `JPS4`.
- The HUD shows the last search time, expansions, and route length for the current move, plus the per-round summary for the same apple / same board comparison.
- If food becomes unreachable in the live demo, the snake now tries to recover by following its tail and re-homing the food to a reachable cell instead of oscillating forever.

## Code layout

- `Snake Game Code/snake_game_jps4.py`: Tkinter UI, game loop, compare mode.
- `Snake Game Code/pathing_grid.py`: grid, Dijkstra/A*/JPS4, timings and expansion counts.
- `Snake Game Code/helper.py`: `Point`, `AstarContext`, heap-based search.

## Preliminary benchmark + report (interim)

Install dependencies:

```text
pip install -r requirements.txt
```

Run the full preliminary suite (three densities, plots, LaTeX number file):

```text
python run_preliminary_benchmark.py
```

This writes:

- `results/preliminary_*.csv` and `results/preliminary_*.json`
- `report/generated_numbers.tex` (table macros for the paper)
- `report/figures/preliminary_expansions.png`, `preliminary_time_ms.png`

Smaller single-density run:

```text
python benchmark_interim.py
```

## Tests

Run the automated checks from the repository root:

```text
python -m pytest Proj/tests -q
```

The test suite covers:

- shortest-path agreement across `Dijkstra`, `A*`, and `JPS4`
- expansion-order invariants on sampled random grids
- reachable-food selection for the snake demo
- recovery from the previously reproducible unreachable-food loop

Build the PDF (needs LaTeX: MiKTeX / TeX Live, or upload `report/` to Overleaf):

```text
cd report
pdflatex progress_report_acl.tex
```

See `report/README.txt`.

## Datasets / benchmarks

Grids are synthetic (random obstacles, controlled density). The game is for intuition; `run_preliminary_benchmark.py` produces the quantitative preliminary results used in `report/progress_report_acl.tex`.

## References

See `Algos_Project_Proposal (3) (1).pdf` and `Refrence/` for papers (e.g. Baum 2025 on 4-connected JPS).
