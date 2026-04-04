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

CELL_WIDTH = 32
win_width = 20 * CELL_WIDTH
win_height = 20 * CELL_WIDTH
GRID_PX = win_height
HUD_PX = 36
CANVAS_HEIGHT = GRID_PX + HUD_PX
TOP_BAR_H = 168
WINDOW_HEIGHT = TOP_BAR_H + CANVAS_HEIGHT
WINDOW_SIZE = f"{win_width}x{WINDOW_HEIGHT}"

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
        canvas.delete('all')
        canvas.config(width=win_width, height=CANVAS_HEIGHT)
        if self.compare_layers:
            inset_seq = (2, 6, 11)
            for idx, layer in enumerate(self.compare_layers):
                ins = inset_seq[idx] if idx < len(inset_seq) else 4 + idx * 5
                for row, col in layer["cells"]:
                    if not (0 <= row < self.board.shape[0] and 0 <= col < self.board.shape[1]):
                        continue
                    x_val = col * CELL_WIDTH
                    y_val = row * CELL_WIDTH
                    canvas.create_rectangle(
                        x_val + ins,
                        y_val + ins,
                        x_val + CELL_WIDTH - ins,
                        y_val + CELL_WIDTH - ins,
                        fill=layer["fill"],
                        outline="",
                    )
        elif self.route:
            for row, col in self.route:
                if not (0 <= row < self.board.shape[0] and 0 <= col < self.board.shape[1]):
                    continue
                x_val = col * CELL_WIDTH
                y_val = row * CELL_WIDTH
                canvas.create_rectangle(
                    x_val,
                    y_val,
                    x_val + CELL_WIDTH,
                    y_val + CELL_WIDTH,
                    fill="#7eb8e8",
                    outline="#3a3a3a",
                )
        for col in range(self.board.shape[1]):
            for row in range(self.board.shape[0]):
                x_val = col * CELL_WIDTH
                y_val = row * CELL_WIDTH
                cell_val = self.board[row, col]
                color = COLORS[cell_val]
                canvas.create_rectangle(
                    x_val, y_val, x_val + CELL_WIDTH, y_val + CELL_WIDTH,
                    fill=color, outline="#3a3a3a",
                )
        alg = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}[current_path_mode]
        canvas.create_rectangle(0, GRID_PX, win_width, CANVAS_HEIGHT, fill="#252525", outline="")
        hud = f"Score {self.score}   |   Playing: {alg}"
        if self.compare_layers:
            hud += "   |   Compare mode: red/green/blue = Dijkstra / A* / JPS4"
        else:
            hud += "   |   Cyan = planned route (current algo)"
        canvas.create_text(
            14,
            GRID_PX + HUD_PX // 2,
            anchor="w",
            text=hud,
            fill="#e8e8e8",
            font=("Segoe UI", 11),
        )
        canvas.update()
        sync_metrics()

    def game_over(self, play_sound=True):
        self.cancel_tick()
        self.game_paused = True
        if play_sound:
            winsound.PlaySound(f"{path_dir}Assets/price.wav", winsound.SND_ASYNC)
        canvas.delete("all")
        canvas.create_text(
            win_width // 2,
            GRID_PX // 2,
            text=f"Game Over\nScore: {self.score}",
            font=("Arial", 28),
            fill="red",
        )
        canvas.update()

############################
# Tkinter Setup
############################

banana = Tk()
banana.title("Snake pathfinding | JPS4")
banana.resizable(False, False)

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

Label(
    top_bar,
    textvariable=compare_var,
    bg="#2b2b2b",
    fg="#a0c8e8",
    font=("Consolas", 8),
    justify=LEFT,
    anchor=W,
    wraplength=win_width - 20,
).pack(anchor=W, pady=(6, 0))

Label(
    top_bar,
    textvariable=metrics_var,
    bg="#2b2b2b",
    fg="#b8b8b8",
    font=("Consolas", 9),
    justify=LEFT,
    anchor=W,
).pack(anchor=W, pady=(8, 0))
Label(
    top_bar,
    textvariable=session_var,
    bg="#2b2b2b",
    fg="#8a8a8a",
    font=("Consolas", 8),
    justify=LEFT,
    anchor=W,
    wraplength=win_width - 20,
).pack(anchor=W, pady=(4, 0))
Label(
    top_bar,
    text="Last search = one path to apple. Expansions = heap pops. Route cells = grid squares in that path. Session = sums while playing; switch algorithms to compare.",
    bg="#2b2b2b",
    fg="#6d6d6d",
    font=("Segoe UI", 8),
    justify=LEFT,
    anchor=W,
    wraplength=win_width - 20,
).pack(anchor=W, pady=(2, 0))

canvas = Canvas(
    banana,
    bg="#141414",
    width=win_width,
    height=CANVAS_HEIGHT,
    highlightthickness=0,
)
top_bar.pack_forget()
canvas.pack()


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


def start_menu():
    """Display a start menu with snake_game.png as a full-window background and two difficulty buttons."""
    canvas.pack_forget()
    top_bar.pack_forget()

    banana.geometry(WINDOW_SIZE)

    menu_frame = Frame(banana, width=win_width, height=WINDOW_HEIGHT)
    menu_frame.pack(fill="both", expand=True)

    # Attempt to load the background image
    try:
        bg_image_original = PhotoImage(file=f"{path_dir}Assets/snake_game.png")
        img_width = bg_image_original.width()
        img_height = bg_image_original.height()

        # Compute how many times we can scale the image (integer factor only).
        scale_factor_x = win_width // img_width  if img_width  else 1
        scale_factor_y = WINDOW_HEIGHT // img_height if img_height else 1
        # Pick the smaller of the two to ensure we don't exceed window boundaries.
        scale_factor = min(scale_factor_x, scale_factor_y)
        
        # If scale_factor is >= 1, we enlarge using .zoom().
        # If scale_factor is 0, we do a sub-sample using an integer factor (for smaller images).
        if scale_factor >= 1:
            bg_image = bg_image_original.zoom(scale_factor)
        else:
            # We'll invert the factor for sub-sampling (avoiding division by zero).
            # e.g., if scale_factor is 0, use at least 2 or more as sub-sample factor.
            subsample_factor = max(2, (img_width // win_width) + 1, (img_height // WINDOW_HEIGHT) + 1)
            bg_image = bg_image_original.subsample(subsample_factor)
    except Exception as e:
        print("Could not load 'snake_game.png':", e)
        bg_image = None

    # If the image loaded, create a label to hold it as a background
    if bg_image:
        bg_label = Label(menu_frame, image=bg_image)
        bg_label.image = bg_image  # Keep a reference to avoid garbage collection
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)  # Fill the frame
    else:
        # Fallback color if no image is available
        menu_frame.config(bg="lightgreen")

    # Functions for difficulty choices
    def choose_easy():
        menu_frame.destroy()
        banana.geometry(WINDOW_SIZE)
        top_bar.pack(side=TOP, fill=X)
        canvas.pack()
        on_difficulty_chosen(EASY_BOARD_LAYOUT)

    def choose_hard():
        menu_frame.destroy()
        banana.geometry(WINDOW_SIZE)
        top_bar.pack(side=TOP, fill=X)
        canvas.pack()
        on_difficulty_chosen(HARD_BOARD_LAYOUT)

    # Create buttons on top of the background
    easy_button = Button(menu_frame, text="Easy", font=("Arial", 16, "bold"), 
                         fg="white", bg="green", command=choose_easy)
    hard_button = Button(menu_frame, text="Hard", font=("Arial", 16, "bold"), 
                         fg="white", bg="red", command=choose_hard)

    # Place buttons at positions over the background
    # Adjust these relx/rely values to position them exactly where you want
    easy_button.place(relx=0.4, rely=0.9, anchor="center")
    hard_button.place(relx=0.6, rely=0.9, anchor="center")


def on_difficulty_chosen(board_layout):
    global BOARD, main_snake, current_path_mode, algo_session
    algo_session = {
        "dijkstra": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
        "astar": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
        "jps4": {"n": 0, "ms": 0.0, "exp": 0, "steps": 0},
    }
    banana.geometry(WINDOW_SIZE)
    current_path_mode = "jps4"
    on_path_key("jps4")
    BOARD = np.array(board_layout)
    main_snake = Snake(BOARD.copy(), locations=default_location)
    main_snake.update_board()
    main_snake.play()

# Show the start menu first
start_menu()

banana.mainloop()
