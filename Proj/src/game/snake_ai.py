import os
import sys
from random import choice as random_choice

_GAME_DIR = os.path.dirname(os.path.abspath(__file__))
_ALGO_DIR = os.path.join(_GAME_DIR, "..", "algorithms")
for _p in (_GAME_DIR, _ALGO_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from helper import Point
from pathing_grid import PathingGrid


def update_pathing_grid(grid, board, blocked_values):
    blocked = set(blocked_values)
    for row in range(board.shape[0]):
        for col in range(board.shape[1]):
            grid.set(col, row, board[row, col] in blocked)


def search_path(board, start_loc, goal_loc, mode, blocked_values, clear_cells=()):
    grid = PathingGrid(board.shape[1], board.shape[0], False)
    temp_board = board.copy()
    for row, col in clear_cells:
        if 0 <= row < temp_board.shape[0] and 0 <= col < temp_board.shape[1]:
            temp_board[row, col] = 0

    update_pathing_grid(grid, temp_board, blocked_values)
    start = Point(start_loc[1], start_loc[0])
    goal = Point(goal_loc[1], goal_loc[0])
    path = grid.get_path_single_goal(start, goal, mode=mode)
    return path, {
        "ms": grid.last_ms,
        "expansions": grid.last_expansions,
        "steps": len(path) if path else 0,
    }


def choose_reachable_food(board, head_loc, empty_value, blocked_values, min_dist=10, clear_cells=(), chooser=None):
    chooser = chooser or random_choice

    grid = PathingGrid(board.shape[1], board.shape[0], False)
    temp_board = board.copy()
    for row, col in clear_cells:
        if 0 <= row < temp_board.shape[0] and 0 <= col < temp_board.shape[1]:
            temp_board[row, col] = empty_value

    update_pathing_grid(grid, temp_board, blocked_values)
    start = Point(head_loc[1], head_loc[0])

    ranked = []
    for row in range(temp_board.shape[0]):
        for col in range(temp_board.shape[1]):
            if temp_board[row, col] != empty_value:
                continue
            target = Point(col, row)
            if grid.reachable(start, target):
                dist = abs(row - head_loc[0]) + abs(col - head_loc[1])
                ranked.append((dist, row, col))

    if not ranked:
        return None

    ranked.sort(reverse=True)
    far_candidates = [(row, col) for dist, row, col in ranked if dist >= min_dist]
    if far_candidates:
        return chooser(far_candidates)
    return (ranked[0][1], ranked[0][2])


def best_safe_move(board, head_loc, tail_loc, empty_values):
    moves = []
    for new_loc in orthogonal_neighbors(head_loc):
        if _is_traversable(board, new_loc, empty_values):
            moves.append(new_loc)

    if not moves:
        return None

    best_move = None
    best_score = -1
    for move in moves:
        score = 0
        for follow_up in orthogonal_neighbors(move):
            if follow_up == tail_loc:
                continue
            if _is_traversable(board, follow_up, empty_values):
                score += 1
        if score > best_score:
            best_score = score
            best_move = move
    return best_move


def orthogonal_neighbors(pos):
    row, col = pos
    return (
        (row, col - 1),
        (row, col + 1),
        (row - 1, col),
        (row + 1, col),
    )


def _is_traversable(board, pos, allowed_values):
    row, col = pos
    return (
        0 <= row < board.shape[0]
        and 0 <= col < board.shape[1]
        and board[row, col] in allowed_values
    )
