from helper import Point, AstarContext
from pathing_grid import PathingGrid

from typing import Any, Callable, List, Optional, Tuple
from tkinter import *
from random import choice
import os

import numpy as np
import winsound

path_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep
current_path_mode = "jps4"
GAME_DEBUG = False

algo_session = {
    "dijkstra": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
    "astar": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
    "jps4": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
}


def record_algo_session(mode: str, ms: float, exp: int, steps: int):
    s = algo_session[mode]
    s["n"] += 1
    s["ms"] += ms
    s["exp"] += exp
    s["steps"] += steps


def session_line():
    parts = []
    for mode in ("dijkstra", "astar", "jps4"):
        lab = {"dijkstra": "Dij", "astar": "A*", "jps4": "JPS"}[mode]
        s = algo_session[mode]
        if s["n"] == 0:
            parts.append(f"{lab}: —")
        else:
            avg = s["ms"] / s["n"]
            parts.append(
                f"{lab} n={s['n']} avg {avg:.2f}ms tot exp {s['exp']}"
            )
    return "Session totals (this run):  " + "   |   ".join(parts)


COMPARE_ORDER = ("dijkstra", "astar", "jps4")
COMPARE_LABELS = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}
COMPARE_COLORS = ("#d48888", "#88c488", "#6a9fd4")


def run_three_way_compare(
    board: np.ndarray,
    head_rc: Tuple[int, int],
    tail_rc: Tuple[int, int],
    food_rc: Optional[Tuple[int, int]],
) -> List[dict]:
    if food_rc is None:
        return []
    pg0 = PathingGrid(board.shape[1], board.shape[0], False)
    temp = board.copy()
    temp[tail_rc] = EMPTY
    update_pathing_grid(pg0, temp)
    start = Point(head_rc[1], head_rc[0])
    goal = Point(food_rc[1], food_rc[0])
    direct = pg0.find_direct_path(start, goal)
    out = []
    if direct and len(direct) > 1:
        cells = [(p.y, p.x) for p in direct]
        for mode, fill in zip(COMPARE_ORDER, COMPARE_COLORS):
            out.append(
                {
                    "mode": mode,
                    "fill": fill,
                    "cells": cells,
                    "ms": 0.0,
                    "exp": 0,
                    "cells_n": len(direct),
                    "ok": True,
                }
            )
        return out
    for mode, fill in zip(COMPARE_ORDER, COMPARE_COLORS):
        pg = PathingGrid(board.shape[1], board.shape[0], False)
        update_pathing_grid(pg, temp)
        path = pg.get_path_single_goal(start, goal, mode=mode)
        ms = pg.last_ms
        exp = pg.last_expansions
        ncells = len(path) if path else 0
        ok = bool(path and len(path) >= 2)
        cells = [(p.y, p.x) for p in path] if path else []
        out.append(
            {
                "mode": mode,
                "fill": fill,
                "cells": cells,
                "ms": ms,
                "exp": exp,
                "cells_n": ncells,
                "ok": ok,
            }
        )
    return out


def format_compare_text(layers: List[dict]) -> str:
    if not layers:
        return "Compare: no food or no path data."
    lines = [
        "Frozen snapshot (same head, apple, map). Red=Dijkstra, green=A*, blue=JPS4.",
    ]
    for L in layers:
        name = COMPARE_LABELS[L["mode"]]
        st = "ok" if L["ok"] else "no path"
        lines.append(
            f"{name}: {L['ms']:.3f} ms   exp {L['exp']}   route cells {L['cells_n']}   ({st})"
        )
    return "\n".join(lines)


def astar_jps(start: Any,
              successors: Callable[[Optional[Any], Any], List[Tuple[Any, int]]],
              heuristic: Callable[[Any], int],
              success: Callable[[Any], bool]) -> Optional[Tuple[List[Any], int]]:

    context = AstarContext()
    return context.astar_jps(start, successors, heuristic, success)


############################
# Snake Game Integration
############################

# Colors and cell types
COLORS = ['white', 'maroon', 'red', 'yellow', 'grey', 'white']
EMPTY = 0
BODY = 1
FOOD = 2
HEAD = 3
WALL = 4

# Define two boards: EASY and HARD
EASY_BOARD_LAYOUT = [
    [4]*20,
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4,0,0,0,4,4,4,0,0,0,4,0,0,0,0,0,0,0,0,4],
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4],
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4,0,0,0,0,0,4,0,0,0,0,0,4,0,0,0,0,0,0,4],
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4] + [0]*18 + [4],
    [4,0,0,4,4,4,0,0,0,0,0,0,0,0,0,0,4,0,0,4],
    [4] + [0]*18 + [4],
    [4]*20
]

HARD_BOARD_LAYOUT = [
    [4]*20,
    [4, 0, 4, 0, 0, 4, 0, 4, 0, 0, 4, 0, 4, 0, 0, 4, 0, 4, 0, 4],
    [4, 0, 0, 4, 0, 0, 4, 0, 0, 4, 0, 0, 4, 0, 0, 4, 0, 0, 0, 4],
    [4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 4],
    [4, 0, 0, 0, 4, 4, 4, 0, 0, 0, 4, 4, 4, 0, 0, 0, 4, 0, 0, 4],
    [4, 0, 4, 0, 0, 0, 0, 4, 0, 4, 0, 0, 0, 0, 4, 0, 4, 0, 0, 4],
    [4, 0, 0, 0, 4, 0, 4, 0, 4, 0, 4, 0, 0, 0, 4, 0, 0, 0, 0, 4],
    [4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 4],
    [4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 4, 0, 0, 0, 0, 4, 0, 0, 4],
    [4, 0, 4, 0, 4, 0, 4, 0, 0, 0, 4, 0, 4, 0, 4, 0, 4, 0, 0, 4],
    [4, 0, 0, 0, 4, 4, 0, 0, 0, 4, 0, 0, 0, 4, 4, 0, 0, 0, 0, 4],
    [4, 0, 4, 0, 0, 0, 4, 0, 4, 0, 0, 0, 4, 0, 0, 0, 4, 0, 4, 4],
    [4, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4],
    [4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 4],
    [4, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 4],
    [4, 0, 4, 0, 0, 0, 4, 0, 0, 0, 4, 0, 4, 0, 0, 0, 4, 0, 4, 4],
    [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
    [4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 4],
    [4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 4],
    [4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 4],
    [4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 4],
    [4]*20
]

# Global references for the board and snake
BOARD = None
main_snake = None

# Place the initial food at a random free cell.
food = (10, 10)

# Direction functions (using (row, col))
STEP_LEFT = lambda pos: (pos[0], pos[1] - 1)
STEP_RIGHT = lambda pos: (pos[0], pos[1] + 1)
STEP_UP = lambda pos: (pos[0] - 1, pos[1])
STEP_DOWN = lambda pos: (pos[0] + 1, pos[1])

GRID_N = 20
HUD_MIN = 28


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
    return {
        "cell": cell,
        "grid_px": grid_px,
        "hud_px": hud_px,
        "ox": ox,
        "oy": oy,
        "W": W,
        "H": H,
        "hud_y0": hud_y0,
    }

# Default snake spawn in a free area
default_location = [(2,2), (2,3)]

def update_pathing_grid(pg: PathingGrid, board: np.ndarray):
    height, width = board.shape
    for row in range(height):
        for col in range(width):
            # Treat WALL and BODY as blocked; HEAD and FOOD remain free.
            blocked = (board[row, col] in [WALL, BODY])
            pg.set(col, row, blocked)

class Snake:
    def __init__(self, board: np.ndarray, locations=default_location, virtual=False):
        self.locations = locations
        self.board = board
        self.virtual = virtual
        self.score = 0
        self.no_path_count = 0
        self.pf_ms = -1.0
        self.pf_exp = 0
        self.pf_steps = 0
        self.route = None
        self.after_job = None
        self.game_paused = False
        self.compare_layers = None

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
            if GAME_DEBUG:
                print("No path found to food; attempting emergency movement.")
            movement = self.find_safest_move()
            if movement is None:
                if GAME_DEBUG:
                    print("No safe moves available; skipping move this turn.")
                if self.no_path_count >= 5:
                    self.game_over()
                    return
                self.after_job = banana.after(300, self.schedule_next)
                return
            if GAME_DEBUG:
                print(f"Emergency move chosen: {movement.__name__}")
        else:
            self.no_path_count = 0
        self.change_positions(movement)
        self.after_job = banana.after(200, self.schedule_next)

    def food_search(self):
        """Find a path to the food using current_path_mode (dijkstra, astar, or jps4)."""
        # Get the current state
        head_loc = self.head()
        tail_loc = self.tail()
        
        # Create a PathingGrid
        pg = PathingGrid(self.board.shape[1], self.board.shape[0], False)
        
        # Temporarily remove tail so it doesn't block the path
        temp_board = self.board.copy()
        temp_board[tail_loc] = EMPTY
        
        # Update the pathing grid
        update_pathing_grid(pg, temp_board)
        
        # Convert locations to Point objects
        start = Point(head_loc[1], head_loc[0])  # Convert (row, col) to (x, y)
        goal_pt = Point(food[1], food[0])        # Convert (row, col) to (x, y)
        
        # First, check for a direct path to food (fastest option)
        direct_path = pg.find_direct_path(start, goal_pt)
        if direct_path and len(direct_path) > 1:
            self.pf_ms = 0.0
            self.pf_exp = 0
            self.pf_steps = len(direct_path)
            self.route = [(p.y, p.x) for p in direct_path]
            record_algo_session(current_path_mode, 0.0, 0, len(direct_path))
            sync_metrics()
            next_pt = direct_path[1]
            new_pos = (next_pt.y, next_pt.x)
            return self.get_direction(head_loc, new_pos)
        
        path = pg.get_path_single_goal(start, goal_pt, mode=current_path_mode)
        self.pf_ms = pg.last_ms
        self.pf_exp = pg.last_expansions
        self.pf_steps = len(path) if path else 0
        sync_metrics()
        
        if not path or len(path) < 2:
            self.route = None
            return None
        
        self.route = [(p.y, p.x) for p in path]
        record_algo_session(current_path_mode, self.pf_ms, self.pf_exp, len(path))
        
        # The next step is the second point in the path (first point is current position)
        next_pt = path[1]
        new_pos = (next_pt.y, next_pt.x)  # Convert back to (row, col)
        
        # Validate the next position to ensure it's a legal move
        if (not 0 <= new_pos[0] < self.board.shape[0] or 
            not 0 <= new_pos[1] < self.board.shape[1] or
            self.board[new_pos] not in [EMPTY, FOOD]):
            print(f"WARNING: Pathfinding suggested illegal move to {new_pos}. Falling back to emergency movement.")
            self.route = None
            return None
            
        return self.get_direction(head_loc, new_pos)
        
    def get_direction(self, current_pos: Tuple[int, int], next_pos: Tuple[int, int]):
        """Determine which direction to move based on current and next positions."""
        if next_pos[0] < current_pos[0]:
            return STEP_UP
        elif next_pos[0] > current_pos[0]:
            return STEP_DOWN
        elif next_pos[1] < current_pos[1]:
            return STEP_LEFT
        elif next_pos[1] > current_pos[1]:
            return STEP_RIGHT
        
        # Should never reach here
        print(f"ERROR: Unable to determine direction from {current_pos} to {next_pos}")
        return None

    def validate_path(self, path: List[Point]) -> Optional[List[Point]]:
        """Ensure the path is valid for the snake by checking each step"""
        if not path or len(path) < 2:
            return None
            
        # Start from the head position
        head_loc = self.head()
        current_pos = (head_loc[0], head_loc[1])
        
        # Create a copy of the board to simulate movement
        sim_board = self.board.copy()
        
        # Build a new path starting from the current position
        valid_path = [path[0]]  # First point is the start (head position)
        
        for i in range(1, len(path)):
            next_pt = path[i]
            next_pos = (next_pt.y, next_pt.x)
            
            # Check if this is a valid move (adjacent and not blocked)
            is_adjacent = False
            for d in [STEP_LEFT, STEP_RIGHT, STEP_UP, STEP_DOWN]:
                if d(current_pos) == next_pos:
                    is_adjacent = True
                    break
                    
            if not is_adjacent:
                print(f"WARNING: Path contains non-adjacent move from {current_pos} to {next_pos}")
                return None
                
            # Check if the position is valid (not blocked)
            if (not 0 <= next_pos[0] < sim_board.shape[0] or 
                not 0 <= next_pos[1] < sim_board.shape[1] or
                (sim_board[next_pos] not in [EMPTY, FOOD] and next_pos != self.tail())):
                print(f"WARNING: Path contains blocked position at {next_pos}")
                return None
                
            # Add this point to the validated path
            valid_path.append(next_pt)
            
            # Update for next iteration
            current_pos = next_pos
            
        return valid_path

    def find_safest_move(self):
        """When no path to food exists, find a move that keeps the most future options open."""
        head_loc = self.head()
        # Get only VALID possible moves
        possible_moves = []
        for d in [STEP_LEFT, STEP_RIGHT, STEP_UP, STEP_DOWN]:
            new_loc = d(head_loc)
            if (0 <= new_loc[0] < self.board.shape[0] and 
                0 <= new_loc[1] < self.board.shape[1] and
                self.board[new_loc] in [EMPTY, FOOD]):
                possible_moves.append(d)
        
        if not possible_moves:
            return None
            
        # Evaluate each move with a more sophisticated scoring system
        best_move = None
        best_score = -1
        
        for move in possible_moves:
            # Simulate the move
            new_head = move(head_loc)
            
            # Double-check this is a valid move (should always be true due to the filtering above)
            if not (0 <= new_head[0] < self.board.shape[0] and 
                   0 <= new_head[1] < self.board.shape[1] and
                   self.board[new_head] in [EMPTY, FOOD]):
                print(f"WARNING: Skipping invalid move to {new_head}")
                continue
            
            # 1. Count immediate moves available (basic freedom)
            future_moves_count = 0
            future_moves = []
            for d in [STEP_LEFT, STEP_RIGHT, STEP_UP, STEP_DOWN]:
                future_pos = d(new_head)
                if 0 <= future_pos[0] < self.board.shape[0] and 0 <= future_pos[1] < self.board.shape[1]:
                    # Check if this position would be valid after the move
                    # (excluding the current tail which will move)
                    if future_pos != self.tail() and self.board[future_pos] in [EMPTY, FOOD]:
                        future_moves_count += 1
                        future_moves.append(future_pos)
            
            # 2. Evaluate open space - avoid corners and narrow corridors
            # Count empty spaces in a larger area around the new position
            open_space_score = 0
            visited = set()
            if future_moves_count > 0:  # Only bother if there's at least one immediate move
                # Use a simple flood fill to measure open space
                to_visit = [new_head]
                visited.add(new_head)
                depth = 0
                max_depth = 6  # Limit search depth to avoid too much computation
                
                while to_visit and depth < max_depth:
                    depth += 1
                    next_to_visit = []
                    for pos in to_visit:
                        for d in [STEP_LEFT, STEP_RIGHT, STEP_UP, STEP_DOWN]:
                            neighbor = d(pos)
                            if (neighbor not in visited and 
                                0 <= neighbor[0] < self.board.shape[0] and 
                                0 <= neighbor[1] < self.board.shape[1] and
                                self.board[neighbor] in [EMPTY, FOOD]):
                                visited.add(neighbor)
                                next_to_visit.append(neighbor)
                                # Give higher score to spaces found earlier in the search
                                open_space_score += (max_depth - depth + 1)
                    to_visit = next_to_visit
            
            # 3. Prefer moves away from walls and the snake's body
            wall_distance = 0
            # Check distance to walls/obstacles in each direction
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue  # Skip the center
                    
                    # Look outward in this direction
                    r, c = new_head
                    distance = 0
                    while (0 <= r < self.board.shape[0] and 
                           0 <= c < self.board.shape[1] and
                           self.board[(r, c)] in [EMPTY, FOOD, HEAD] and
                           distance < 4):  # Limit distance check
                        distance += 1
                        r += dr
                        c += dc
                    
                    wall_distance += distance
            
            # Calculate overall score with weighted components
            # Weight immediate freedom more heavily
            score = (future_moves_count * 10) + (open_space_score * 2) + wall_distance
            
            # Debug output
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move

    def change_positions(self, direction: Callable[[Tuple[int, int]], Tuple[int, int]]):
        head_loc = self.head()
        new_head = direction(head_loc)
        
        # Safety check: make sure we're not moving into a wall or our own body
        if (not 0 <= new_head[0] < self.board.shape[0] or 
            not 0 <= new_head[1] < self.board.shape[1] or
            self.board[new_head] in [WALL, BODY]):
            print(f"ERROR: Attempted illegal move to {new_head} which contains: {self.board[new_head] if 0 <= new_head[0] < self.board.shape[0] and 0 <= new_head[1] < self.board.shape[1] else 'out of bounds'}")
            # Choose a random legal move instead
            legal_moves = self.possible_moves_list(head_loc)
            if legal_moves:
                return self.change_positions(legal_moves[0])
            else:
                # No legal moves left
                return
                
        tail_loc = self.tail()
        self.board[tail_loc] = EMPTY
        self.locations = [new_head] + self.locations[:-1]
        if new_head == food:
            self.locations.append(tail_loc)
            self.score += 1
            self.make_food()
        self.update_board()

    def make_food(self):
        global food
        free_cells = []
        for r in range(self.board.shape[0]):
            for c in range(self.board.shape[1]):
                if self.board[r, c] == EMPTY:
                    free_cells.append((r, c))
        if free_cells:
            food = choice(free_cells)
        else:
            food = None

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
            if 0 <= new_loc[0] < self.board.shape[0] and 0 <= new_loc[1] < self.board.shape[1]:
                if self.board[new_loc] in [EMPTY, FOOD]:
                    moves.append(d)
        return moves

    def update_board(self):
        self.board[self.board == BODY] = EMPTY
        self.board[self.board == HEAD] = EMPTY
        for i, pos in enumerate(self.locations):
            if i == 0:
                self.board[pos] = HEAD
            else:
                self.board[pos] = BODY
        if food is not None:
            self.board[food] = FOOD
        if not self.virtual:
            self.update_canvas()

    def update_canvas(self):
        L = compute_game_layout(canvas)
        cw = L["cell"]
        ox, oy = L["ox"], L["oy"]
        canvas.delete("all")
        if self.compare_layers:
            for idx, layer in enumerate(self.compare_layers):
                ins = max(1, min(14, cw // 4 + idx * 2))
                for row, col in layer["cells"]:
                    if not (0 <= row < self.board.shape[0] and 0 <= col < self.board.shape[1]):
                        continue
                    x0 = ox + col * cw + ins
                    y0 = oy + row * cw + ins
                    x1 = ox + (col + 1) * cw - ins
                    y1 = oy + (row + 1) * cw - ins
                    canvas.create_rectangle(x0, y0, x1, y1, fill=layer["fill"], outline="")
        elif self.route:
            for row, col in self.route:
                if not (0 <= row < self.board.shape[0] and 0 <= col < self.board.shape[1]):
                    continue
                x0 = ox + col * cw
                y0 = oy + row * cw
                canvas.create_rectangle(
                    x0,
                    y0,
                    x0 + cw,
                    y0 + cw,
                    fill="#7eb8e8",
                    outline="#3a3a3a",
                )
        for col in range(self.board.shape[1]):
            for row in range(self.board.shape[0]):
                x0 = ox + col * cw
                y0 = oy + row * cw
                cell_val = self.board[row, col]
                color = COLORS[cell_val]
                canvas.create_rectangle(
                    x0, y0, x0 + cw, y0 + cw, fill=color, outline="#3a3a3a"
                )
        alg = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}[current_path_mode]
        canvas.create_rectangle(
            0, L["hud_y0"], L["W"], L["H"], fill="#252525", outline=""
        )
        hud = f"Score {self.score}   |   Playing: {alg}"
        if self.compare_layers:
            hud += "   |   Compare: red / green / blue = Dijkstra / A* / JPS4"
        else:
            hud += "   |   Cyan = planned route"
        fs = max(9, min(18, cw // 2))
        canvas.create_text(
            12,
            L["hud_y0"] + L["hud_px"] // 2,
            anchor="w",
            text=hud,
            fill="#e8e8e8",
            font=("Segoe UI", fs),
        )
        canvas.update()
        sync_metrics()

    def game_over(self, play_sound=True):
        self.cancel_tick()
        self.game_paused = True
        if play_sound:
            winsound.PlaySound(f"{path_dir}Assets/price.wav", winsound.SND_ASYNC)
        canvas.delete("all")
        L = compute_game_layout(canvas)
        cx = L["ox"] + L["grid_px"] // 2
        cy = L["oy"] + L["grid_px"] // 2
        gfs = max(16, min(36, L["cell"] * 2))
        canvas.create_text(
            cx,
            cy,
            text=f"Game Over\nScore: {self.score}",
            font=("Arial", gfs),
            fill="red",
        )
        canvas.update()

############################
# Tkinter Setup
############################

banana = Tk()
banana.title("Snake pathfinding | JPS4")
_scr_w = banana.winfo_screenwidth()
_scr_h = banana.winfo_screenheight()
banana.geometry(f"{max(520, int(_scr_w * 0.62))}x{max(580, int(_scr_h * 0.72))}")
banana.minsize(400, 460)
banana.maxsize(_scr_w, _scr_h)
banana.resizable(True, True)
banana.configure(bg="#2b2b2b")


def toggle_fullscreen(event=None):
    fs = not bool(banana.attributes("-fullscreen"))
    banana.attributes("-fullscreen", fs)
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

metrics_var = StringVar(
    value="Last search: —   |   Expansions: —   |   Route cells: —"
)
session_var = StringVar(value=session_line())
algo_btns = {}

top_bar = Frame(banana, bg="#2b2b2b", padx=10, pady=8)
top_row = Frame(top_bar, bg="#2b2b2b")
top_row.pack(anchor=W)
Label(
    top_row,
    text="Algorithm:",
    bg="#2b2b2b",
    fg="#e8e8e8",
    font=("Segoe UI", 10, "bold"),
).pack(side=LEFT, padx=(0, 8))


def _algo_button(mode: str, label: str):
    b = Button(
        top_row,
        text=label,
        font=("Segoe UI", 10),
        padx=12,
        pady=5,
        cursor="hand2",
        command=lambda m=mode: on_path_key(m),
    )
    b.pack(side=LEFT, padx=3)
    algo_btns[mode] = b


_algo_button("dijkstra", "Dijkstra")
_algo_button("astar", "A*")
_algo_button("jps4", "JPS4")

compare_row = Frame(top_bar, bg="#2b2b2b")
compare_row.pack(anchor=W, pady=(8, 0))

COMPARE_HINT = (
    'Compare: click “Compare 3 algos” to freeze the board and draw Dijkstra (red), A* (green), JPS4 (blue). '
    "Same head, apple, and walls for all three."
)
compare_var = StringVar(value=COMPARE_HINT)


def on_compare_click():
    if main_snake is None:
        compare_var.set("Start a game from the menu first.")
        return
    if food is None:
        compare_var.set("No apple on the board.")
        return
    main_snake.cancel_tick()
    main_snake.game_paused = True
    main_snake.route = None
    layers = run_three_way_compare(
        main_snake.board,
        main_snake.head(),
        main_snake.tail(),
        food,
    )
    main_snake.compare_layers = layers
    compare_var.set(format_compare_text(layers))
    main_snake.update_canvas()


def on_resume_click():
    if main_snake is None:
        return
    main_snake.compare_layers = None
    compare_var.set(COMPARE_HINT)
    if not main_snake.alive():
        main_snake.game_paused = True
        main_snake.game_over(play_sound=False)
        return
    main_snake.game_paused = False
    main_snake.update_canvas()
    main_snake.schedule_next()


Button(
    compare_row,
    text="Compare 3 algos",
    font=("Segoe UI", 10),
    padx=10,
    pady=4,
    cursor="hand2",
    command=on_compare_click,
).pack(side=LEFT, padx=(0, 8))
Button(
    compare_row,
    text="Resume play",
    font=("Segoe UI", 10),
    padx=10,
    pady=4,
    cursor="hand2",
    command=on_resume_click,
).pack(side=LEFT)

wrap_labels = []

lbl_compare = Label(
    top_bar,
    textvariable=compare_var,
    bg="#2b2b2b",
    fg="#a0c8e8",
    font=("Consolas", 8),
    justify=LEFT,
    anchor=W,
    wraplength=700,
)
lbl_compare.pack(anchor=W, pady=(6, 0))
wrap_labels.append(lbl_compare)

Label(
    top_bar,
    textvariable=metrics_var,
    bg="#2b2b2b",
    fg="#b8b8b8",
    font=("Consolas", 9),
    justify=LEFT,
    anchor=W,
).pack(anchor=W, pady=(8, 0))
lbl_sess = Label(
    top_bar,
    textvariable=session_var,
    bg="#2b2b2b",
    fg="#8a8a8a",
    font=("Consolas", 8),
    justify=LEFT,
    anchor=W,
    wraplength=700,
)
lbl_sess.pack(anchor=W, pady=(4, 0))
wrap_labels.append(lbl_sess)

lbl_leg = Label(
    top_bar,
    text="Last search = one path to apple. Expansions = heap pops. Route cells = grid squares in that path. Session = sums while playing; switch algorithms to compare.",
    bg="#2b2b2b",
    fg="#6d6d6d",
    font=("Segoe UI", 8),
    justify=LEFT,
    anchor=W,
    wraplength=700,
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
    if event.widget != canvas:
        return
    if event.width < 24 or event.height < 24:
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
    on_bg = "#2d5a87"
    off_bg = "#404040"
    for mode, btn in algo_btns.items():
        if mode == current_path_mode:
            btn.config(relief=SUNKEN, bg=on_bg, fg="white", activebackground=on_bg)
        else:
            btn.config(
                relief=RAISED,
                bg=off_bg,
                fg="#ececec",
                activebackground="#505050",
            )


def sync_metrics():
    session_var.set(session_line())
    if main_snake is None:
        metrics_var.set(
            "Last search: —   |   Expansions: —   |   Route cells: —"
        )
        return
    m = main_snake
    if m.pf_ms < 0:
        metrics_var.set(
            "Last search: —   |   Expansions: —   |   Route cells: —"
        )
        return
    metrics_var.set(
        f"Last search: {m.pf_ms:.2f} ms   |   Expansions: {m.pf_exp}   |   Route cells: {m.pf_steps}"
    )


def on_path_key(mode: str):
    global current_path_mode
    current_path_mode = mode
    labels = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}
    banana.title(f"Snake pathfinding | {labels[mode]}")
    refresh_algo_buttons()
    sync_metrics()
    if main_snake is not None:
        main_snake.update_canvas()


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
    """Splash: fills window; image and buttons refit on resize."""
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
            menu_canvas.create_text(
                W // 2,
                H // 2,
                text="Snake pathfinding",
                fill="#e0e0e0",
                font=("Segoe UI", max(14, H // 28)),
            )

    def schedule_splash(event=None):
        nonlocal splash_job
        menu_canvas.update_idletasks()
        W = menu_canvas.winfo_width()
        H = menu_canvas.winfo_height()
        if W == splash_wh[0] and H == splash_wh[1]:
            return
        splash_wh[0], splash_wh[1] = W, H
        if splash_job is not None:
            banana.after_cancel(splash_job)
        splash_job = banana.after(50, redraw_splash)

    menu_canvas.bind("<Configure>", schedule_splash)

    def choose_easy():
        menu_frame.destroy()
        banana.minsize(400, 460)
        banana.maxsize(sw, sh)
        top_bar.pack(side=TOP, fill=X)
        game_body.pack(fill=BOTH, expand=True)
        update_wraplengths()
        on_difficulty_chosen(EASY_BOARD_LAYOUT)

    def choose_hard():
        menu_frame.destroy()
        banana.minsize(400, 460)
        banana.maxsize(sw, sh)
        top_bar.pack(side=TOP, fill=X)
        game_body.pack(fill=BOTH, expand=True)
        update_wraplengths()
        on_difficulty_chosen(HARD_BOARD_LAYOUT)

    easy_button = Button(
        menu_frame,
        text="Easy",
        font=("Arial", 16, "bold"),
        fg="white",
        bg="green",
        command=choose_easy,
    )
    hard_button = Button(
        menu_frame,
        text="Hard",
        font=("Arial", 16, "bold"),
        fg="white",
        bg="red",
        command=choose_hard,
    )
    easy_button.place(relx=0.38, rely=0.92, anchor="center")
    hard_button.place(relx=0.62, rely=0.92, anchor="center")
    easy_button.lift(menu_canvas)
    hard_button.lift(menu_canvas)
    banana.after(80, redraw_splash)


def on_difficulty_chosen(board_layout):
    global BOARD, main_snake, current_path_mode, algo_session
    algo_session = {
        "dijkstra": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
        "astar": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
        "jps4": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
    }
    current_path_mode = "jps4"
    on_path_key("jps4")
    BOARD = np.array(board_layout)
    main_snake = Snake(BOARD.copy(), locations=default_location)
    main_snake.update_board()
    main_snake.play()

# Show the start menu first
start_menu()

banana.mainloop()
