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

- The window starts at a fraction of your screen size; you can **resize** or **maximize** it. The **20×20 grid** scales so it stays centered and as large as fits in the lower pane (HUD strip scales with window height). View → Toggle fullscreen, or **F11**; **Esc** leaves fullscreen.
- Easy / Hard: pick a map from the start screen.
- Dijkstra, A*, JPS4: choose which algorithm drives the snake during play.
- Compare 3 algos: pauses the game and runs all three on the **same** frozen snapshot (head, apple, body, walls). Draws three paths: red = Dijkstra, green = A*, blue = JPS4 (nested tints where they overlap). Metrics show per-algorithm time (ms), expansions, and route length.
- Resume play: clears the overlay and continues with the selected algorithm.

## Code layout

- `Snake Game Code/snake_game_jps4.py` — Tkinter UI, game loop, compare mode.
- `Snake Game Code/pathing_grid.py` — grid, Dijkstra/A*/JPS4, timings and expansion counts.
- `Snake Game Code/helper.py` — `Point`, `AstarContext`, heap-based search.

## Datasets / benchmarks

Grids are procedural or hand-authored layouts in code (no external URL). For the interim report, describe inputs as generated 4-connected grids with controlled obstacle density and fixed test maps. Scripted benchmark batches are planned separately from this demo.

## References

See `Algos_Project_Proposal (3) (1).pdf` and `Refrence/` for papers (e.g. Baum 2025 on 4-connected JPS).
