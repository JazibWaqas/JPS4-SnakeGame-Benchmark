import numpy as np

import snake_game_jps4 as game


EMPTY = game.EMPTY
BODY = game.BODY
FOOD = game.FOOD
HEAD = game.HEAD
WALL = game.WALL


def make_loop_board():
    board = np.full((7, 7), EMPTY, dtype=int)
    board[0, :] = WALL
    board[-1, :] = WALL
    board[:, 0] = WALL
    board[:, -1] = WALL
    board[1:6, 4] = WALL
    board[3, 4] = WALL
    return board


def test_snake_rehomes_unreachable_food_instead_of_looping(monkeypatch):
    game.banana.withdraw()
    monkeypatch.setattr(game.Snake, "update_canvas", lambda self: None)
    monkeypatch.setattr(game, "sync_metrics", lambda: None)
    monkeypatch.setattr(game, "show_summary_or_restart", lambda reason: None)
    monkeypatch.setattr(game.banana, "after", lambda delay, callback: None)
    monkeypatch.setattr(game.banana, "after_cancel", lambda job: None)

    board = make_loop_board()
    locations = [(3, 2), (3, 1)]
    for index, pos in enumerate(locations):
        board[pos] = HEAD if index == 0 else BODY

    original_food = (3, 5)
    game.food = original_food
    board[original_food] = FOOD

    snake = game.Snake(board.copy(), locations=list(locations))

    seen_states = []
    for _ in range(10):
        snake.schedule_next()
        seen_states.append(tuple(snake.locations))

    assert game.food != original_food
    assert len(set(seen_states)) > 4
    assert not snake.game_paused
