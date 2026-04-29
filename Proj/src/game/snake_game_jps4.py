from collections import deque
import os
import sys

# Make src/algorithms/ importable (helper, pathing_grid)
_GAME_DIR = os.path.dirname(os.path.abspath(__file__))
_ALGO_DIR = os.path.join(_GAME_DIR, "..", "algorithms")
for _p in (_GAME_DIR, _ALGO_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from snake_ai import best_safe_move, choose_reachable_food, search_path

from tkinter import *
from random import choice

import numpy as np
# Handle Windows sound support gracefully
try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False
    class _Winsound:
        SND_LOOP = SND_ASYNC = SND_PURGE = 0
        def PlaySound(self, *a, **k): pass
    winsound = _Winsound()

# Path to game assets
path_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep
GAME_DEBUG = False

# Demo sequence: run all 3 algorithms on same board
DEMO_SEQUENCE = ("dijkstra", "astar", "jps4")
demo_round = 0
demo_results = {}
# Store board state so all algorithms run on identical snapshots
snapshot_board = None
snapshot_food = None
snapshot_locations = None
current_path_mode = DEMO_SEQUENCE[0]
# Game generation counter to handle delayed callbacks
game_generation = 0

# Algorithm colors and labels for UI
ALGO_COLORS = {"dijkstra": "#d48888", "astar": "#88c488", "jps4": "#6a9fd4"}
ALGO_LABELS = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}

# Grid cell types
COLORS = ["white", "maroon", "red", "yellow", "grey", "white"]
EMPTY = 0
BODY = 1
FOOD = 2
HEAD = 3
WALL = 4

import random as _rnd

# Generate game board with walls and obstacle clusters
def make_board(density: float) -> list:
    """
    Build a 40x40 grid with outer walls and rectangular obstacle clusters.
    density: approx fraction of interior cells blocked (0.0 - 1.0).
    Snake spawn area (rows 1-4, cols 1-5) always kept clear.
    Row 1 and col 1 kept as open corridors for connectivity.
    """
    N = 40
    W, E = 4, 0
    grid = [[E]*N for _ in range(N)]
    # Add outer walls
    for i in range(N):
        grid[0][i] = grid[N-1][i] = W
        grid[i][0] = grid[i][N-1] = W

    interior = (N-2) * (N-2)
    target = int(interior * density)

    rng = _rnd.Random(int(density * 1000))

    placed = 0
    attempts = 0
    # Place rectangular obstacle clusters
    while placed < target and attempts < 8000:
        attempts += 1
        h = rng.randint(1, 4)  # Height
        w = rng.randint(2, 7)  # Width
        r = rng.randint(1, N - 2 - h)
        c = rng.randint(1, N - 2 - w)
        # Keep spawn zone and border corridors clear
        if r <= 4 and c <= 5:
            continue
        if r == 1 or c == 1:
            continue
        # Place obstacle if cells are empty
        for dr in range(h):
            for dc in range(w):
                if grid[r+dr][c+dc] == E:
                    grid[r+dr][c+dc] = W
                    placed += 1

    return grid

# Global game state
BOARD = None
main_snake = None
food = (10, 10)

# Movement direction functions
STEP_LEFT  = lambda pos: (pos[0], pos[1] - 1)
STEP_RIGHT = lambda pos: (pos[0], pos[1] + 1)
STEP_UP    = lambda pos: (pos[0] - 1, pos[1])
STEP_DOWN  = lambda pos: (pos[0] + 1, pos[1])

# Grid and UI constants
GRID_N = 40
HUD_MIN = 28
default_location = [(2, 2), (2, 3)]


# Calculate canvas layout based on window size
def compute_game_layout(cv) -> dict:
    cv.update_idletasks()
    W = max(cv.winfo_width(), 1)
    H = max(cv.winfo_height(), 1)
    # Reserve space for HUD at bottom
    hud_px = max(HUD_MIN, min(64, H // 11))
    avail_h = max(H - hud_px, hud_px + 10)
    # Calculate cell size to fit grid in available space
    cell = min(W // GRID_N, avail_h // GRID_N)
    cell = max(5, cell)
    grid_px = GRID_N * cell
    # Center the grid
    ox = (W - grid_px) // 2
    oy = (avail_h - grid_px) // 2
    hud_y0 = oy + grid_px
    return {"cell": cell, "grid_px": grid_px, "hud_px": hud_px,
            "ox": ox, "oy": oy, "W": W, "H": H, "hud_y0": hud_y0}


class Snake:
    def __init__(self, board: np.ndarray, locations=None):
        self.locations = list(locations or default_location)
        self.board = board
        self.score = 0
        self.no_path_count = 0  # Count consecutive failures to find path
        # Performance metrics for last search
        self.pf_ms = -1.0       # time for last individual search call
        self.pf_exp = 0         # expansions for last individual search call
        self.pf_steps = 0       # path length for last individual search call
        # Accumulated metrics for current apple
        self.round_ms = 0.0     # accumulated time for this apple
        self.round_exp = 0      # accumulated expansions for this apple
        self.round_path = 0     # path length on first search of this apple (head→food)
        # Path and visualization state
        self.route = None       # Current planned path
        self.explored = []      # nodes expanded in last search — for visualisation
        self.after_job = None   # Tkinter after callback handle
        self.game_paused = False
        self.state_history = deque(maxlen=16)  # Detect repetitive states
        self.remember_state()

    # Start the game loop
    def play(self):
        # winsound.PlaySound(f"{path_dir}Assets/roku_snake.wav", winsound.SND_LOOP + winsound.SND_ASYNC)
        self.schedule_next()

    # Cancel scheduled move
    def cancel_tick(self):
        if self.after_job is not None:
            try:
                banana.after_cancel(self.after_job)
            except Exception:
                pass
            self.after_job = None

    # Schedule next game tick (200ms delay)
    def schedule_next(self):
        if self.game_paused:
            return
        # Check if snake is still alive
        if not self.alive():
            self.game_over()
            return
        
        # Try to find path to food
        movement = self.food_search()
        if movement is None:
            # No path to food: try recovery strategies
            self.no_path_count += 1
            movement = self.tail_search()
            if movement is not None and self.no_path_count >= 8:
                # Stuck for too long: relocate food
                if self.rehome_food():
                    movement = self.food_search() or movement
                    self.no_path_count = 0
            if movement is None and self.no_path_count >= 6:
                # Try relocating food again
                if self.rehome_food():
                    movement = self.food_search()
            if movement is None:
                # Still no path: try safest move
                movement = self.find_safest_move()
            if movement is None:
                # Completely stuck: end game after 5 failures
                if self.no_path_count >= 5:
                    self.game_over()
                    return
                self.after_job = banana.after(300, self.schedule_next)
                return
        else:
            # Found path: reset failure counter
            self.no_path_count = 0
        
        # Execute the movement
        self.change_positions(movement)
        self.remember_state()
        
        # Check for repetitive loops and relocate food if needed
        if self.no_path_count >= 8 and self.is_repeating_state() and self.rehome_food():
            self.no_path_count = 0
        
        # Schedule next tick
        self.after_job = banana.after(200, self.schedule_next)

    # Try to find path from head to current food
    def food_search(self):
        if food is None:
            self.route = None
            return None

        path = self.search_to(food, count_for_round_path=True)
        if not path or len(path) < 2:
            self.route = None
            return None

        return self.path_to_direction(path)

    # Try to find path from head to tail (follow own body)
    def tail_search(self):
        path = self.search_to(self.tail(), count_for_round_path=False)
        if not path or len(path) < 2:
            self.route = None
            return None
        return self.path_to_direction(path)

    # Generic path search using selected algorithm
    def search_to(self, target_loc, count_for_round_path):
        path, metrics = search_path(
            self.board,
            self.head(),
            target_loc,
            current_path_mode,
            blocked_values=(WALL, BODY),
            clear_cells=(self.tail(),),  # Treat tail as empty (will move)
        )
        self.record_search(metrics, path, count_for_round_path=count_for_round_path)

        if not path or len(path) < 2:
            return path

        self.route = [(p.y, p.x) for p in path]
        return path

    # Record search performance metrics
    def record_search(self, metrics, path, count_for_round_path):
        self.pf_ms = metrics["ms"]
        self.pf_exp = metrics["expansions"]
        self.pf_steps = metrics["steps"]
        self.explored = metrics.get("explored", [])
        self.round_ms += metrics["ms"]
        self.round_exp += metrics["expansions"]
        # Record path length for first search of this apple
        if count_for_round_path and self.round_path == 0 and path:
            self.round_path = len(path)
        sync_metrics()

    # Convert path to movement direction function
    def path_to_direction(self, path):
        next_pt = path[1]
        new_pos = (next_pt.y, next_pt.x)
        tail_loc = self.tail()
        # Validate the move is legal
        if (not 0 <= new_pos[0] < self.board.shape[0] or
                not 0 <= new_pos[1] < self.board.shape[1] or
                (self.board[new_pos] not in [EMPTY, FOOD] and new_pos != tail_loc)):
            self.route = None
            return None
        return self.get_direction(self.head(), new_pos)

    # Get movement function from current to next position
    def get_direction(self, current_pos, next_pos):
        if next_pos[0] < current_pos[0]:
            return STEP_UP
        elif next_pos[0] > current_pos[0]:
            return STEP_DOWN
        elif next_pos[1] < current_pos[1]:
            return STEP_LEFT
        return STEP_RIGHT

    # Find safest move when no path is available
    def find_safest_move(self):
        next_pos = best_safe_move(self.board, self.head(), self.tail(), empty_values=(EMPTY, FOOD))
        if next_pos is None:
            return None
        return self.get_direction(self.head(), next_pos)

    # Execute one movement step
    def change_positions(self, direction):
        head_loc = self.head()
        new_head = direction(head_loc)

        # Check if move is legal
        if (not 0 <= new_head[0] < self.board.shape[0] or
                not 0 <= new_head[1] < self.board.shape[1] or
                self.board[new_head] in [WALL, BODY]):
            # Try any legal move as fallback
            legal = self.possible_moves_list(head_loc)
            if legal:
                return self.change_positions(legal[0])
            return

        tail_loc = self.tail()
        # Clear tail position (will move)
        self.board[tail_loc] = EMPTY
        ate = (new_head == food)
        # Move snake: add new head, remove tail (unless eating)
        self.locations = [new_head] + self.locations[:-1]
        if ate:
            # Grow snake: keep tail position
            self.locations.append(tail_loc)
            self.score += 1
        self.update_board()
        if ate:
            on_apple_eaten(self)

    # Place new food on the board
    def make_food(self):
        global food
        food = choose_reachable_food(
            self.board,
            self.head(),
            empty_value=EMPTY,
            blocked_values=(WALL, BODY),
            min_dist=10,  # Minimum distance from snake head
            clear_cells=(self.tail(),),
            chooser=choice,
        )

    # Check if snake has any legal moves
    def alive(self):
        return len(self.possible_moves_list(self.head())) > 0

    # Get snake head position
    def head(self):
        return self.locations[0]

    # Get snake tail position
    def tail(self):
        return self.locations[-1]

    # List all legal moves from current position
    def possible_moves_list(self, location):
        moves = []
        for d in [STEP_LEFT, STEP_RIGHT, STEP_UP, STEP_DOWN]:
            new_loc = d(location)
            if (0 <= new_loc[0] < self.board.shape[0] and
                    0 <= new_loc[1] < self.board.shape[1] and
                    self.board[new_loc] in [EMPTY, FOOD]):
                moves.append(d)
        return moves

    # Update board array with current snake and food positions
    def update_board(self):
        # Clear old snake and food positions
        self.board[self.board == BODY] = EMPTY
        self.board[self.board == HEAD] = EMPTY
        self.board[self.board == FOOD] = EMPTY
        # Draw new snake positions
        for i, pos in enumerate(self.locations):
            self.board[pos] = HEAD if i == 0 else BODY
        # Draw food
        if food is not None:
            self.board[food] = FOOD
        self.update_canvas()

    # Remember current state for loop detection
    def remember_state(self):
        self.state_history.append((tuple(self.locations), food))

    # Check if current state has repeated multiple times
    def is_repeating_state(self):
        current = (tuple(self.locations), food)
        return sum(1 for state in self.state_history if state == current) >= 3

    # Relocate food to new reachable position
    def rehome_food(self):
        global food
        old_food = food
        self.make_food()
        if food is None or food == old_food:
            return False
        self.route = None
        self.update_board()
        return True

    # Draw the game board, snake, path, and HUD
    def update_canvas(self):
        L = compute_game_layout(canvas)
        cw = L["cell"]
        ox, oy = L["ox"], L["oy"]
        canvas.delete("all")

        # --- Layer 1: board tiles (walls and empty spaces) ---
        for col in range(self.board.shape[1]):
            for row in range(self.board.shape[0]):
                x0 = ox + col * cw
                y0 = oy + row * cw
                canvas.create_rectangle(x0, y0, x0 + cw, y0 + cw,
                                        fill=COLORS[self.board[row, col]], outline="#3a3a3a")

        algo_color = ALGO_COLORS[current_path_mode]

        # --- Layer 2: faint search footprint (nodes algorithm examined) ---
        # This shows the algorithm's search pattern visually:
        # Dijkstra = large circular blob, A* = focused cone, JPS4 = sparse points
        if self.explored:
            route_set = set(self.route) if self.route else set()
            ins_exp = max(1, cw // 4)
            for ex, ey in self.explored:   # stored as (x, y)
                col, row = ex, ey
                if not (0 <= row < self.board.shape[0] and 0 <= col < self.board.shape[1]):
                    continue
                if self.board[row, col] in (HEAD, BODY, FOOD, WALL):
                    continue
                if (row, col) in route_set:
                    continue   # will be drawn brighter in next layer
                canvas.create_rectangle(
                    ox + col * cw + ins_exp, oy + row * cw + ins_exp,
                    ox + (col + 1) * cw - ins_exp, oy + (row + 1) * cw - ins_exp,
                    fill=algo_color, outline="", stipple="gray25",
                )

        # --- Layer 3: bright planned path (head → food) ---
        if self.route:
            ins = max(1, cw // 5)
            for row, col in self.route:
                if not (0 <= row < self.board.shape[0] and 0 <= col < self.board.shape[1]):
                    continue
                if self.board[row, col] in (HEAD, BODY, FOOD):
                    continue
                canvas.create_rectangle(
                    ox + col * cw + ins, oy + row * cw + ins,
                    ox + (col + 1) * cw - ins, oy + (row + 1) * cw - ins,
                    fill=algo_color, outline="",
                )

        # --- Layer 4: HUD with algorithm info and score ---
        alg = ALGO_LABELS[current_path_mode]
        step = demo_round + 1
        canvas.create_rectangle(0, L["hud_y0"], L["W"], L["H"], fill="#252525", outline="")
        fs = max(9, min(18, cw // 2))
        canvas.create_text(
            12, L["hud_y0"] + L["hud_px"] // 2,
            anchor="w",
            text=f"Round {step}/3  -  {alg}   |   Score {self.score}",
            fill="#e8e8e8", font=("Segoe UI", fs),
        )
        canvas.update()
        sync_metrics()

    # Handle game over condition
    def game_over(self, play_sound=True):
        self.cancel_tick()
        self.game_paused = True
        if play_sound:
            # winsound.PlaySound(f"{path_dir}Assets/price.wav", winsound.SND_ASYNC)
            pass
        show_summary_or_restart("no_path")


############################
# Tkinter window setup
############################

# Main window
banana = Tk()
banana.title("Snake pathfinding | Dijkstra")
# Set initial size to 62% of screen
_scr_w = banana.winfo_screenwidth()
_scr_h = banana.winfo_screenheight()
banana.geometry(f"{max(520, int(_scr_w * 0.62))}x{max(580, int(_scr_h * 0.72))}")
banana.minsize(400, 460)
banana.maxsize(_scr_w, _scr_h)
banana.resizable(True, True)
banana.configure(bg="#2b2b2b")

# Toggle fullscreen mode
def toggle_fullscreen(event=None):
    banana.attributes("-fullscreen", not bool(banana.attributes("-fullscreen")))
    return "break"

# Exit fullscreen mode
def exit_fullscreen(event=None):
    if bool(banana.attributes("-fullscreen")):
        banana.attributes("-fullscreen", False)
    return "break"

# Create menu bar with fullscreen option
menubar = Menu(banana)
view_menu = Menu(menubar, tearoff=0)
view_menu.add_command(label="Toggle fullscreen", accelerator="F11", command=toggle_fullscreen)
menubar.add_cascade(label="View", menu=view_menu)
banana.config(menu=menubar)
# Bind keyboard shortcuts
banana.bind("<F11>", toggle_fullscreen)
banana.bind("<Escape>", exit_fullscreen)

# UI variables for displaying metrics
metrics_var = StringVar(value="Last search: -   |   Expansions: -   |   Route cells: -")
results_var = StringVar(value="Dijkstra: -     A*: -     JPS4: -")
algo_btns = {}

# Top control panel
top_bar = Frame(banana, bg="#2b2b2b", padx=10, pady=8)
top_row = Frame(top_bar, bg="#2b2b2b")
top_row.pack(anchor=W)
Label(top_row, text="Algorithm:", bg="#2b2b2b", fg="#e8e8e8",
      font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 8))

# Create algorithm selection buttons
def _algo_button(mode: str, label: str):
    b = Button(top_row, text=label, font=("Segoe UI", 10), padx=12, pady=5,
               cursor="hand2", command=lambda m=mode: on_path_key(m))
    b.pack(side=LEFT, padx=3)
    algo_btns[mode] = b

_algo_button("dijkstra", "Dijkstra")
_algo_button("astar", "A*")
_algo_button("jps4", "JPS4")

# Labels that need text wrapping on resize
wrap_labels = []

# Display current search metrics
Label(top_bar, textvariable=metrics_var, bg="#2b2b2b", fg="#b8b8b8",
      font=("Consolas", 9), justify=LEFT, anchor=W).pack(anchor=W, pady=(8, 0))

# Display comparison results across all algorithms
lbl_results = Label(top_bar, textvariable=results_var, bg="#2b2b2b", fg="#c8c8c8",
                    font=("Consolas", 9), justify=LEFT, anchor=W)
lbl_results.pack(anchor=W, pady=(2, 0))
wrap_labels.append(lbl_results)

# Help text explaining the demo
lbl_leg = Label(
    top_bar,
    text="Same apple, same board for all 3 rounds. Dijkstra first, then A*, then JPS4. "
         "Last search = current move. Results row = apple-to-apple comparison.",
    bg="#2b2b2b", fg="#6d6d6d", font=("Segoe UI", 8),
    justify=LEFT, anchor=W, wraplength=700,
)
lbl_leg.pack(anchor=W, pady=(2, 0))
wrap_labels.append(lbl_leg)

# Game canvas area
game_body = Frame(banana, bg="#141414")
canvas = Canvas(game_body, bg="#141414", highlightthickness=0)
canvas.pack(fill=BOTH, expand=True)

# Handle canvas resize events
_canvas_after = None


# Update text wrapping when window resizes
def update_wraplengths(event=None):
    banana.update_idletasks()
    w = max(banana.winfo_width() - 28, 220)
    for lb in wrap_labels:
        lb.config(wraplength=w)

# Handle canvas resize events (debounced)
def on_canvas_configure(event):
    global _canvas_after
    if event.widget != canvas or event.width < 24 or event.height < 24:
        return
    if _canvas_after is not None:
        banana.after_cancel(_canvas_after)

    def tick():
        global _canvas_after
        _canvas_after = None
        update_wraplengths()
        if main_snake is not None:
            main_snake.update_canvas()

    _canvas_after = banana.after(48, tick)

canvas.bind("<Configure>", on_canvas_configure)

# Hide UI elements initially (shown in menu)
top_bar.pack_forget()
game_body.pack_forget()


# Update algorithm button appearance to show active selection
def refresh_algo_buttons():
    on_bg, off_bg = "#2d5a87", "#404040"
    for mode, btn in algo_btns.items():
        if mode == current_path_mode:
            btn.config(relief=SUNKEN, bg=on_bg, fg="white", activebackground=on_bg)
        else:
            btn.config(relief=RAISED, bg=off_bg, fg="#ececec", activebackground="#505050")

# Update metrics display with current search results
def sync_metrics():
    if main_snake is None or main_snake.pf_ms < 0:
        metrics_var.set("Last search: -   |   Expansions: -   |   Route cells: -")
        return
    m = main_snake
    metrics_var.set(
        f"Last search: {m.pf_ms:.2f} ms   |   Expansions: {m.pf_exp}   |   Route cells: {m.pf_steps}"
    )

# Update results comparison bar across all algorithms
def sync_results_bar():
    parts = []
    for mode in DEMO_SEQUENCE:
        label = ALGO_LABELS[mode]
        r = demo_results.get(mode)
        if r is None:
            parts.append(f"{label}: -")
        else:
            parts.append(f"{label}: {r['ms']:.2f}ms  {r['exp']}exp  {r['steps']}cells")
    results_var.set("     ".join(parts))

# Return to main menu
def _restart_to_menu():
    if main_snake is not None:
        main_snake.cancel_tick()
    start_menu()

# Handle algorithm selection button click
def on_path_key(mode: str):
    global current_path_mode
    current_path_mode = mode
    banana.title(f"Snake pathfinding | {ALGO_LABELS[mode]}")
    refresh_algo_buttons()
    if main_snake is not None:
        main_snake.pf_ms = -1.0
        main_snake.pf_exp = 0
        main_snake.pf_steps = 0
    sync_metrics()
    if main_snake is not None:
        main_snake.update_canvas()


# Called when snake eats an apple - records metrics and advances demo
def on_apple_eaten(snake):
    mode = current_path_mode
    # Save performance metrics for this algorithm
    demo_results[mode] = {
        "ms": round(snake.round_ms, 2),
        "exp": snake.round_exp,
        "steps": snake.round_path,
    }
    sync_results_bar()
    snake.cancel_tick()
    snake.game_paused = True
    snake.route = None
    snake.update_canvas()
    # Wait 1.4 seconds then advance to next algorithm
    banana.after(1400, advance_demo_round)

# Advance to next algorithm in demo sequence
def advance_demo_round():
    global demo_round, current_path_mode, main_snake, food, game_generation

    demo_round += 1
    if demo_round >= len(DEMO_SEQUENCE):
        # All algorithms completed: show results
        show_summary_or_restart("done")
        return

    # Switch to next algorithm
    mode = DEMO_SEQUENCE[demo_round]
    current_path_mode = mode
    # Restore original board and food positions
    food = snapshot_food
    main_snake = Snake(snapshot_board.copy(), locations=list(snapshot_locations))
    main_snake.update_board()

    refresh_algo_buttons()
    sync_metrics()
    banana.title(f"Snake pathfinding | {ALGO_LABELS[mode]}")

    game_generation += 1
    gen = game_generation
    snake_ref = main_snake
    # Start game after short delay to ensure UI updates
    def start_if_current():
        if game_generation == gen and main_snake is snake_ref:
            snake_ref.play()
    banana.after(700, start_if_current)


# Display results summary or game over screen
def show_summary_or_restart(reason: str):
    canvas.delete("all")
    L = compute_game_layout(canvas)
    cx = L["ox"] + L["grid_px"] // 2
    cy = L["oy"] + L["grid_px"] // 2
    cw = L["cell"]
    # Font sizes based on cell size
    fs_title = max(13, min(22, cw * 2))
    fs_row = max(10, min(16, cw))
    fs_btn = max(10, min(14, cw))

    title = "Results - Same Apple, Same Board" if reason == "done" else "Snake got stuck - partial results"
    canvas.create_text(cx, cy - fs_title * 5, text=title,
                       font=("Segoe UI", fs_title, "bold"),
                       fill="#e8e8e8" if reason == "done" else "#cc4444",
                       justify="center")

    # Table headers
    headers = ["Algorithm", "Time (ms)", "Expansions", "Route cells"]
    col_x = [cx - 200, cx - 60, cx + 70, cx + 190]
    header_y = cy - fs_row * 3
    for h, x in zip(headers, col_x):
        canvas.create_text(x, header_y, text=h,
                           font=("Segoe UI", fs_row, "bold"), fill="#aaaaaa",
                           anchor="center")

    # Results rows for each algorithm
    for i, mode in enumerate(DEMO_SEQUENCE):
        r = demo_results.get(mode)
        row_y = header_y + (i + 1) * (fs_row + 10)
        color = ALGO_COLORS[mode]
        vals = [ALGO_LABELS[mode],
                f"{r['ms']:.2f}" if r else "-",
                str(r["exp"]) if r else "-",
                str(r["steps"]) if r else "-"]
        for val, x in zip(vals, col_x):
            canvas.create_text(x, row_y, text=val,
                               font=("Consolas", fs_row), fill=color,
                               anchor="center")

    # Play again button
    btn = Button(canvas, text="Play Again", font=("Segoe UI", fs_btn, "bold"),
                 bg="#2d5a87", fg="white", padx=16, pady=7,
                 cursor="hand2", relief=FLAT, command=_restart_to_menu)
    canvas.create_window(cx, cy + fs_title * 4, window=btn)
    canvas.update()

# Initialize algorithm button states
refresh_algo_buttons()


# Scale photo to fit within max dimensions while preserving aspect ratio
def photo_fit_inside(src: PhotoImage, max_w: int, max_h: int) -> PhotoImage:
    img = src
    # Subsample (make smaller) until it fits
    for _ in range(40):
        if img.width() <= max_w and img.height() <= max_h:
            break
        img = img.subsample(2)
    # Zoom (make larger) if too small
    for _ in range(20):
        if img.width() * 2 > max_w or img.height() * 2 > max_h:
            break
        img = img.zoom(2)
    return img

# Create and display main menu
def start_menu():
    game_body.pack_forget()
    top_bar.pack_forget()

    # Set window size for menu
    sw = banana.winfo_screenwidth()
    sh = banana.winfo_screenheight()
    banana.geometry(f"{max(480, int(sw * 0.52))}x{max(520, int(sh * 0.62))}")
    banana.minsize(380, 420)
    banana.maxsize(sw, sh)

    # Create menu frame
    menu_frame = Frame(banana, bg="#1e1e1e")
    menu_frame.pack(fill=BOTH, expand=True)

    # Load background image if available
    bg_src = None
    try:
        bg_src = PhotoImage(file=f"{path_dir}Assets/snake_game.png")
    except Exception as e:
        print("Could not load 'snake_game.png':", e)

    # Create canvas for background
    menu_canvas = Canvas(menu_frame, bg="#1e1e1e", highlightthickness=0)
    menu_canvas.pack(fill=BOTH, expand=True)

    # Handle background image drawing
    splash_job = None
    splash_wh = [0, 0]

    def redraw_splash():
        nonlocal splash_job
        splash_job = None
        menu_canvas.delete("all")
        menu_canvas.update_idletasks()
        W = max(menu_canvas.winfo_width(), 2)
        H = max(menu_canvas.winfo_height(), 2)
        if W < 16 or H < 16:
            return
        if bg_src:
            # Scale and draw background image
            fit = photo_fit_inside(bg_src, W - 8, H - 100)
            menu_canvas.create_image(W // 2, H // 2, image=fit, anchor="center")
            menu_canvas._splash_img = fit
        else:
            # Fallback: draw text title
            menu_canvas.create_text(W // 2, H // 2, text="Snake pathfinding",
                                    fill="#e0e0e0", font=("Segoe UI", max(14, H // 28)))

    # Schedule background redraw with debouncing
    def schedule_splash(event=None):
        nonlocal splash_job
        menu_canvas.update_idletasks()
        W, H = menu_canvas.winfo_width(), menu_canvas.winfo_height()
        if W == splash_wh[0] and H == splash_wh[1]:
            return
        splash_wh[0], splash_wh[1] = W, H
        if splash_job is not None:
            banana.after_cancel(splash_job)
        splash_job = banana.after(50, redraw_splash)

    menu_canvas.bind("<Configure>", schedule_splash)

    # Launch game with selected density
    def launch(density: float):
        menu_frame.destroy()
        banana.minsize(400, 460)
        banana.maxsize(sw, sh)
        top_bar.pack(side=TOP, fill=X)
        game_body.pack(fill=BOTH, expand=True)
        update_wraplengths()
        on_difficulty_chosen(density)

    # Difficulty selection buttons
    densities = [
        ("Low  (15%)",    0.15, "#4a8f4a"),
        ("Medium  (28%)", 0.28, "#8f7a2a"),
        ("High  (40%)",   0.40, "#8f3a3a"),
    ]
    for i, (label, d, color) in enumerate(densities):
        btn = Button(
            menu_frame, text=label,
            font=("Segoe UI", 14, "bold"),
            fg="white", bg=color,
            padx=20, pady=10,
            cursor="hand2", relief=FLAT,
            command=lambda den=d: launch(den),
        )
        btn.place(relx=0.22 + i * 0.28, rely=0.90, anchor="center")
        btn.lift(menu_canvas)

    # Help text
    Label(
        menu_frame,
        text="Select obstacle density",
        bg="#1e1e1e", fg="#888888",
        font=("Segoe UI", 10),
    ).place(relx=0.5, rely=0.83, anchor="center")

    # Initial background draw
    banana.after(80, redraw_splash)


# Start game with selected difficulty
def on_difficulty_chosen(density: float):
    global BOARD, main_snake, current_path_mode, demo_round, demo_results
    global snapshot_board, snapshot_food, snapshot_locations, food, game_generation

    game_generation += 1
    demo_round = 0
    demo_results = {}
    current_path_mode = DEMO_SEQUENCE[0]
    results_var.set("Dijkstra: -     A*: -     JPS4: -")

    # Generate game board with obstacles
    BOARD = np.array(make_board(density))
    board_copy = BOARD.copy()
    # Mark snake body on board before placing food
    for i, pos in enumerate(default_location):
        board_copy[pos] = HEAD if i == 0 else BODY
    main_snake = Snake(board_copy, locations=list(default_location))
    main_snake.make_food()
    main_snake.update_board()

    # Save board state for all algorithms to use
    snapshot_board = main_snake.board.copy()
    snapshot_food = food
    snapshot_locations = list(main_snake.locations)

    refresh_algo_buttons()
    sync_metrics()
    banana.title(f"Snake pathfinding | {ALGO_LABELS[current_path_mode]}")
    main_snake.play()

# Start the application
if __name__ == "__main__":
    start_menu()
    banana.mainloop()
