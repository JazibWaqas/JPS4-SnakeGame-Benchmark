from helper import Point, AstarContext
from pathing_grid import PathingGrid

from typing import Callable, List, Optional, Tuple
from tkinter import *
from random import choice
import os

import numpy as np
try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False
    class _Winsound:
        SND_LOOP = SND_ASYNC = SND_PURGE = 0
        def PlaySound(self, *a, **k): pass
    winsound = _Winsound()

path_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep
GAME_DEBUG = False

DEMO_SEQUENCE = ("dijkstra", "astar", "jps4")
demo_round = 0
demo_results = {}
snapshot_board = None
snapshot_food = None
snapshot_locations = None
current_path_mode = DEMO_SEQUENCE[0]
game_generation = 0  # increments each new game/round; delayed callbacks check this

ALGO_COLORS = {"dijkstra": "#d48888", "astar": "#88c488", "jps4": "#6a9fd4"}
ALGO_LABELS = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}

COLORS = ["white", "maroon", "red", "yellow", "grey", "white"]
EMPTY = 0
BODY = 1
FOOD = 2
HEAD = 3
WALL = 4

import random as _rnd

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
    for i in range(N):
        grid[0][i] = grid[N-1][i] = W
        grid[i][0] = grid[i][N-1] = W

    interior = (N-2) * (N-2)
    target = int(interior * density)

    rng = _rnd.Random(int(density * 1000))

    placed = 0
    attempts = 0
    while placed < target and attempts < 8000:
        attempts += 1
        h = rng.randint(1, 4)
        w = rng.randint(2, 7)
        r = rng.randint(1, N - 2 - h)
        c = rng.randint(1, N - 2 - w)
        # Keep spawn zone and border corridors clear
        if r <= 4 and c <= 5:
            continue
        if r == 1 or c == 1:
            continue
        for dr in range(h):
            for dc in range(w):
                if grid[r+dr][c+dc] == E:
                    grid[r+dr][c+dc] = W
                    placed += 1

    return grid

BOARD = None
main_snake = None
food = (10, 10)

STEP_LEFT  = lambda pos: (pos[0], pos[1] - 1)
STEP_RIGHT = lambda pos: (pos[0], pos[1] + 1)
STEP_UP    = lambda pos: (pos[0] - 1, pos[1])
STEP_DOWN  = lambda pos: (pos[0] + 1, pos[1])

GRID_N = 40
HUD_MIN = 28
default_location = [(2, 2), (2, 3)]


def compute_game_layout(cv) -> dict:
    cv.update_idletasks()
    W = max(cv.winfo_width(), 1)
    H = max(cv.winfo_height(), 1)
    hud_px = max(HUD_MIN, min(64, H // 11))
    avail_h = max(H - hud_px, hud_px + 10)
    cell = min(W // GRID_N, avail_h // GRID_N)
    cell = max(5, cell)
    grid_px = GRID_N * cell
    ox = (W - grid_px) // 2
    oy = (avail_h - grid_px) // 2
    hud_y0 = oy + grid_px
    return {"cell": cell, "grid_px": grid_px, "hud_px": hud_px,
            "ox": ox, "oy": oy, "W": W, "H": H, "hud_y0": hud_y0}


def update_pathing_grid(grid, board):
    for row in range(board.shape[0]):
        for col in range(board.shape[1]):
            grid.set(col, row, board[row, col] in [WALL, BODY])


class Snake:
    def __init__(self, board: np.ndarray, locations=None):
        self.locations = list(locations or default_location)
        self.board = board
        self.score = 0
        self.no_path_count = 0
        self.pf_ms = -1.0       # time for last individual search call
        self.pf_exp = 0         # expansions for last individual search call
        self.pf_steps = 0       # path length for last individual search call
        self.round_ms = 0.0     # accumulated time for this apple
        self.round_exp = 0      # accumulated expansions for this apple
        self.round_path = 0     # path length on first search of this apple (head→food)
        self.route = None
        self.after_job = None
        self.game_paused = False

    def play(self):
        winsound.PlaySound(f"{path_dir}Assets/roku_snake.wav", winsound.SND_LOOP + winsound.SND_ASYNC)
        self.schedule_next()

    def cancel_tick(self):
        if self.after_job is not None:
            try:
                banana.after_cancel(self.after_job)
            except Exception:
                pass
            self.after_job = None

    def schedule_next(self):
        if self.game_paused:
            return
        if not self.alive():
            self.game_over()
            return
        movement = self.food_search()
        if movement is None:
            self.no_path_count += 1
            movement = self.find_safest_move()
            if movement is None:
                if self.no_path_count >= 5:
                    self.game_over()
                    return
                self.after_job = banana.after(300, self.schedule_next)
                return
        else:
            self.no_path_count = 0
        self.change_positions(movement)
        self.after_job = banana.after(200, self.schedule_next)

    def food_search(self):
        head_loc = self.head()
        tail_loc = self.tail()

        grid = PathingGrid(self.board.shape[1], self.board.shape[0], False)
        temp_board = self.board.copy()
        temp_board[tail_loc] = EMPTY
        update_pathing_grid(grid, temp_board)

        start = Point(head_loc[1], head_loc[0])
        goal_pt = Point(food[1], food[0])
        # print("searching", start, "->", goal_pt)
        path = grid.get_path_single_goal(start, goal_pt, mode=current_path_mode)
        self.pf_ms = grid.last_ms
        self.pf_exp = grid.last_expansions
        self.pf_steps = len(path) if path else 0
        self.round_ms += grid.last_ms
        self.round_exp += grid.last_expansions
        if self.round_path == 0 and path:
            self.round_path = len(path)
        sync_metrics()

        if not path or len(path) < 2:
            self.route = None
            return None

        self.route = [(p.y, p.x) for p in path]

        next_pt = path[1]
        new_pos = (next_pt.y, next_pt.x)

        if (not 0 <= new_pos[0] < self.board.shape[0] or
                not 0 <= new_pos[1] < self.board.shape[1] or
                self.board[new_pos] not in [EMPTY, FOOD]):
            self.route = None
            return None

        return self.get_direction(head_loc, new_pos)

    def get_direction(self, current_pos, next_pos):
        if next_pos[0] < current_pos[0]:
            return STEP_UP
        elif next_pos[0] > current_pos[0]:
            return STEP_DOWN
        elif next_pos[1] < current_pos[1]:
            return STEP_LEFT
        return STEP_RIGHT

    def find_safest_move(self):
        head_loc = self.head()
        possible_moves = []
        for d in [STEP_LEFT, STEP_RIGHT, STEP_UP, STEP_DOWN]:
            new_loc = d(head_loc)
            if (0 <= new_loc[0] < self.board.shape[0] and
                    0 <= new_loc[1] < self.board.shape[1] and
                    self.board[new_loc] in [EMPTY, FOOD]):
                possible_moves.append(d)
        if not possible_moves:
            return None
        best_move, best_score = None, -1
        for move in possible_moves:
            new_head = move(head_loc)
            count = 0
            for d in [STEP_LEFT, STEP_RIGHT, STEP_UP, STEP_DOWN]:
                fp = d(new_head)
                if (0 <= fp[0] < self.board.shape[0] and
                        0 <= fp[1] < self.board.shape[1] and
                        fp != self.tail() and
                        self.board[fp] in [EMPTY, FOOD]):
                    count += 1
            if count > best_score:
                best_score = count
                best_move = move
        return best_move

    def change_positions(self, direction):
        head_loc = self.head()
        new_head = direction(head_loc)

        if (not 0 <= new_head[0] < self.board.shape[0] or
                not 0 <= new_head[1] < self.board.shape[1] or
                self.board[new_head] in [WALL, BODY]):
            legal = self.possible_moves_list(head_loc)
            if legal:
                return self.change_positions(legal[0])
            return

        tail_loc = self.tail()
        self.board[tail_loc] = EMPTY
        ate = (new_head == food)
        self.locations = [new_head] + self.locations[:-1]
        if ate:
            self.locations.append(tail_loc)
            self.score += 1
        self.update_board()
        if ate:
            on_apple_eaten(self)

    def make_food(self):
        global food
        free = [(r, c) for r in range(self.board.shape[0])
                for c in range(self.board.shape[1]) if self.board[r, c] == EMPTY]
        if not free:
            food = None
            return
        head = self.head()
        # Prefer cells at least 10 steps away; fall back to furthest available
        far = [(abs(r - head[0]) + abs(c - head[1]), r, c) for r, c in free]
        far.sort(reverse=True)
        min_dist = 10
        candidates = [(r, c) for d, r, c in far if d >= min_dist]
        if not candidates:
            candidates = [(far[0][1], far[0][2])]
        food = choice(candidates)

    def alive(self):
        return len(self.possible_moves_list(self.head())) > 0

    def head(self):
        return self.locations[0]

    def tail(self):
        return self.locations[-1]

    def possible_moves_list(self, location):
        moves = []
        for d in [STEP_LEFT, STEP_RIGHT, STEP_UP, STEP_DOWN]:
            new_loc = d(location)
            if (0 <= new_loc[0] < self.board.shape[0] and
                    0 <= new_loc[1] < self.board.shape[1] and
                    self.board[new_loc] in [EMPTY, FOOD]):
                moves.append(d)
        return moves

    def update_board(self):
        self.board[self.board == BODY] = EMPTY
        self.board[self.board == HEAD] = EMPTY
        self.board[self.board == FOOD] = EMPTY  # clear any stale food before repainting
        for i, pos in enumerate(self.locations):
            self.board[pos] = HEAD if i == 0 else BODY
        if food is not None:
            self.board[food] = FOOD
        self.update_canvas()

    def update_canvas(self):
        L = compute_game_layout(canvas)
        cw = L["cell"]
        ox, oy = L["ox"], L["oy"]
        canvas.delete("all")

        for col in range(self.board.shape[1]):
            for row in range(self.board.shape[0]):
                x0 = ox + col * cw
                y0 = oy + row * cw
                canvas.create_rectangle(x0, y0, x0 + cw, y0 + cw,
                                        fill=COLORS[self.board[row, col]], outline="#3a3a3a")

        if self.route:
            color = ALGO_COLORS[current_path_mode]
            ins = max(1, cw // 5)
            for row, col in self.route:
                if not (0 <= row < self.board.shape[0] and 0 <= col < self.board.shape[1]):
                    continue
                if self.board[row, col] in (HEAD, BODY, FOOD):
                    continue
                canvas.create_rectangle(
                    ox + col * cw + ins, oy + row * cw + ins,
                    ox + (col + 1) * cw - ins, oy + (row + 1) * cw - ins,
                    fill=color, outline="",
                )

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

    def game_over(self, play_sound=True):
        self.cancel_tick()
        self.game_paused = True
        if play_sound:
            winsound.PlaySound(f"{path_dir}Assets/price.wav", winsound.SND_ASYNC)
        show_summary_or_restart("no_path")


############################
# Tkinter window
############################

banana = Tk()
banana.title("Snake pathfinding | Dijkstra")
_scr_w = banana.winfo_screenwidth()
_scr_h = banana.winfo_screenheight()
banana.geometry(f"{max(520, int(_scr_w * 0.62))}x{max(580, int(_scr_h * 0.72))}")
banana.minsize(400, 460)
banana.maxsize(_scr_w, _scr_h)
banana.resizable(True, True)
banana.configure(bg="#2b2b2b")


def toggle_fullscreen(event=None):
    banana.attributes("-fullscreen", not bool(banana.attributes("-fullscreen")))
    return "break"


def exit_fullscreen(event=None):
    if bool(banana.attributes("-fullscreen")):
        banana.attributes("-fullscreen", False)
    return "break"


menubar = Menu(banana)
view_menu = Menu(menubar, tearoff=0)
view_menu.add_command(label="Toggle fullscreen", accelerator="F11", command=toggle_fullscreen)
menubar.add_cascade(label="View", menu=view_menu)
banana.config(menu=menubar)
banana.bind("<F11>", toggle_fullscreen)
banana.bind("<Escape>", exit_fullscreen)

metrics_var = StringVar(value="Last search: -   |   Expansions: -   |   Route cells: -")
results_var = StringVar(value="Dijkstra: -     A*: -     JPS4: -")
algo_btns = {}

top_bar = Frame(banana, bg="#2b2b2b", padx=10, pady=8)
top_row = Frame(top_bar, bg="#2b2b2b")
top_row.pack(anchor=W)
Label(top_row, text="Algorithm:", bg="#2b2b2b", fg="#e8e8e8",
      font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=(0, 8))


def _algo_button(mode: str, label: str):
    b = Button(top_row, text=label, font=("Segoe UI", 10), padx=12, pady=5,
               cursor="hand2", command=lambda m=mode: on_path_key(m))
    b.pack(side=LEFT, padx=3)
    algo_btns[mode] = b


_algo_button("dijkstra", "Dijkstra")
_algo_button("astar", "A*")
_algo_button("jps4", "JPS4")

wrap_labels = []

Label(top_bar, textvariable=metrics_var, bg="#2b2b2b", fg="#b8b8b8",
      font=("Consolas", 9), justify=LEFT, anchor=W).pack(anchor=W, pady=(8, 0))

lbl_results = Label(top_bar, textvariable=results_var, bg="#2b2b2b", fg="#c8c8c8",
                    font=("Consolas", 9), justify=LEFT, anchor=W)
lbl_results.pack(anchor=W, pady=(2, 0))
wrap_labels.append(lbl_results)

lbl_leg = Label(
    top_bar,
    text="Same apple, same board for all 3 rounds. Dijkstra first, then A*, then JPS4. "
         "Last search = current move. Results row = apple-to-apple comparison.",
    bg="#2b2b2b", fg="#6d6d6d", font=("Segoe UI", 8),
    justify=LEFT, anchor=W, wraplength=700,
)
lbl_leg.pack(anchor=W, pady=(2, 0))
wrap_labels.append(lbl_leg)

game_body = Frame(banana, bg="#141414")
canvas = Canvas(game_body, bg="#141414", highlightthickness=0)
canvas.pack(fill=BOTH, expand=True)

_canvas_after = None


def update_wraplengths(event=None):
    banana.update_idletasks()
    w = max(banana.winfo_width() - 28, 220)
    for lb in wrap_labels:
        lb.config(wraplength=w)


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

top_bar.pack_forget()
game_body.pack_forget()


def refresh_algo_buttons():
    on_bg, off_bg = "#2d5a87", "#404040"
    for mode, btn in algo_btns.items():
        if mode == current_path_mode:
            btn.config(relief=SUNKEN, bg=on_bg, fg="white", activebackground=on_bg)
        else:
            btn.config(relief=RAISED, bg=off_bg, fg="#ececec", activebackground="#505050")


def sync_metrics():
    if main_snake is None or main_snake.pf_ms < 0:
        metrics_var.set("Last search: -   |   Expansions: -   |   Route cells: -")
        return
    m = main_snake
    metrics_var.set(
        f"Last search: {m.pf_ms:.2f} ms   |   Expansions: {m.pf_exp}   |   Route cells: {m.pf_steps}"
    )


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


def _restart_to_menu():
    if main_snake is not None:
        main_snake.cancel_tick()
    start_menu()


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


def on_apple_eaten(snake):
    mode = current_path_mode
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
    banana.after(1400, advance_demo_round)


def advance_demo_round():
    global demo_round, current_path_mode, main_snake, food, game_generation

    demo_round += 1
    if demo_round >= len(DEMO_SEQUENCE):
        show_summary_or_restart("done")
        return

    mode = DEMO_SEQUENCE[demo_round]
    current_path_mode = mode
    food = snapshot_food
    main_snake = Snake(snapshot_board.copy(), locations=list(snapshot_locations))
    main_snake.update_board()

    refresh_algo_buttons()
    sync_metrics()
    banana.title(f"Snake pathfinding | {ALGO_LABELS[mode]}")

    game_generation += 1
    gen = game_generation
    snake_ref = main_snake
    def start_if_current():
        if game_generation == gen and main_snake is snake_ref:
            snake_ref.play()
    banana.after(700, start_if_current)


def show_summary_or_restart(reason: str):
    canvas.delete("all")
    L = compute_game_layout(canvas)
    cx = L["ox"] + L["grid_px"] // 2
    cy = L["oy"] + L["grid_px"] // 2
    cw = L["cell"]
    fs_title = max(13, min(22, cw * 2))
    fs_row = max(10, min(16, cw))
    fs_btn = max(10, min(14, cw))

    title = "Results - Same Apple, Same Board" if reason == "done" else "Snake got stuck - partial results"
    canvas.create_text(cx, cy - fs_title * 5, text=title,
                       font=("Segoe UI", fs_title, "bold"),
                       fill="#e8e8e8" if reason == "done" else "#cc4444",
                       justify="center")

    headers = ["Algorithm", "Time (ms)", "Expansions", "Route cells"]
    col_x = [cx - 200, cx - 60, cx + 70, cx + 190]
    header_y = cy - fs_row * 3
    for h, x in zip(headers, col_x):
        canvas.create_text(x, header_y, text=h,
                           font=("Segoe UI", fs_row, "bold"), fill="#aaaaaa",
                           anchor="center")

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

    btn = Button(canvas, text="Play Again", font=("Segoe UI", fs_btn, "bold"),
                 bg="#2d5a87", fg="white", padx=16, pady=7,
                 cursor="hand2", relief=FLAT, command=_restart_to_menu)
    canvas.create_window(cx, cy + fs_title * 4, window=btn)
    canvas.update()


refresh_algo_buttons()


def photo_fit_inside(src: PhotoImage, max_w: int, max_h: int) -> PhotoImage:
    img = src
    for _ in range(40):
        if img.width() <= max_w and img.height() <= max_h:
            break
        img = img.subsample(2)
    for _ in range(20):
        if img.width() * 2 > max_w or img.height() * 2 > max_h:
            break
        img = img.zoom(2)
    return img


def start_menu():
    game_body.pack_forget()
    top_bar.pack_forget()

    sw = banana.winfo_screenwidth()
    sh = banana.winfo_screenheight()
    banana.geometry(f"{max(480, int(sw * 0.52))}x{max(520, int(sh * 0.62))}")
    banana.minsize(380, 420)
    banana.maxsize(sw, sh)

    menu_frame = Frame(banana, bg="#1e1e1e")
    menu_frame.pack(fill=BOTH, expand=True)

    bg_src = None
    try:
        bg_src = PhotoImage(file=f"{path_dir}Assets/snake_game.png")
    except Exception as e:
        print("Could not load 'snake_game.png':", e)

    menu_canvas = Canvas(menu_frame, bg="#1e1e1e", highlightthickness=0)
    menu_canvas.pack(fill=BOTH, expand=True)

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
            fit = photo_fit_inside(bg_src, W - 8, H - 100)
            menu_canvas.create_image(W // 2, H // 2, image=fit, anchor="center")
            menu_canvas._splash_img = fit
        else:
            menu_canvas.create_text(W // 2, H // 2, text="Snake pathfinding",
                                    fill="#e0e0e0", font=("Segoe UI", max(14, H // 28)))

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

    def launch(density: float):
        menu_frame.destroy()
        banana.minsize(400, 460)
        banana.maxsize(sw, sh)
        top_bar.pack(side=TOP, fill=X)
        game_body.pack(fill=BOTH, expand=True)
        update_wraplengths()
        on_difficulty_chosen(density)

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

    Label(
        menu_frame,
        text="Select obstacle density",
        bg="#1e1e1e", fg="#888888",
        font=("Segoe UI", 10),
    ).place(relx=0.5, rely=0.83, anchor="center")

    banana.after(80, redraw_splash)


def on_difficulty_chosen(density: float):
    global BOARD, main_snake, current_path_mode, demo_round, demo_results
    global snapshot_board, snapshot_food, snapshot_locations, food, game_generation

    game_generation += 1
    demo_round = 0
    demo_results = {}
    current_path_mode = DEMO_SEQUENCE[0]
    results_var.set("Dijkstra: -     A*: -     JPS4: -")

    BOARD = np.array(make_board(density))
    board_copy = BOARD.copy()
    # Mark snake body on the board before make_food so it won't land on the snake
    for i, pos in enumerate(default_location):
        board_copy[pos] = HEAD if i == 0 else BODY
    main_snake = Snake(board_copy, locations=list(default_location))
    main_snake.make_food()
    main_snake.update_board()

    snapshot_board = main_snake.board.copy()
    snapshot_food = food
    snapshot_locations = list(main_snake.locations)

    refresh_algo_buttons()
    sync_metrics()
    banana.title(f"Snake pathfinding | {ALGO_LABELS[current_path_mode]}")
    main_snake.play()


if __name__ == "__main__":
    start_menu()
    banana.mainloop()
