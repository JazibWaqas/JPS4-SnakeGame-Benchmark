import numpy as np

from snake_ai import choose_reachable_food, search_path


EMPTY = 0
BODY = 1
FOOD = 2
HEAD = 3
WALL = 4


def make_partitioned_board():
    board = np.full((7, 7), EMPTY, dtype=int)
    board[0, :] = WALL
    board[-1, :] = WALL
    board[:, 0] = WALL
    board[:, -1] = WALL
    board[1:6, 4] = WALL
    board[3, 4] = WALL
    return board


def test_choose_reachable_food_avoids_unreachable_cells():
    board = make_partitioned_board()
    head = (3, 2)
    tail = (3, 1)
    board[head] = HEAD
    board[tail] = BODY

    food = choose_reachable_food(
        board,
        head,
        empty_value=EMPTY,
        blocked_values=(WALL, BODY),
        clear_cells=(tail,),
    )

    assert food is not None
    assert food[1] < 4

    path, _metrics = search_path(
        board,
        head,
        food,
        "jps4",
        blocked_values=(WALL, BODY),
        clear_cells=(tail,),
    )
    assert path is not None

