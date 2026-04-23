import pytest

import snake_game_jps4 as game


@pytest.mark.parametrize("mode", ("dijkstra", "astar", "jps4"))
def test_gameplay_loop_reaches_food_on_live_board(monkeypatch, mode):
    game.banana.withdraw()
    game.current_path_mode = mode

    monkeypatch.setattr(game.Snake, "update_canvas", lambda self: None)
    monkeypatch.setattr(game, "sync_metrics", lambda: None)
    monkeypatch.setattr(game.banana, "after", lambda delay, callback: None)
    monkeypatch.setattr(game.banana, "after_cancel", lambda job: None)
    monkeypatch.setattr(game.winsound, "PlaySound", lambda *args, **kwargs: None)
    monkeypatch.setattr(game, "show_summary_or_restart", lambda reason: None)

    eaten = {"hit": False}

    def fake_on_apple_eaten(snake):
        eaten["hit"] = True

    monkeypatch.setattr(game, "on_apple_eaten", fake_on_apple_eaten)

    board = game.make_board(0.15)
    board_copy = game.np.array(board)
    locations = list(game.default_location)
    for i, pos in enumerate(locations):
        board_copy[pos] = game.HEAD if i == 0 else game.BODY

    snake = game.Snake(board_copy, locations=locations)
    snake.make_food()
    snake.update_board()

    assert game.food is not None

    start_score = snake.score
    for _ in range(120):
        snake.schedule_next()
        if snake.score > start_score or eaten["hit"]:
            break

    assert snake.score > start_score or eaten["hit"], {
        "mode": mode,
        "food": game.food,
        "head": snake.head(),
        "score": snake.score,
        "paused": snake.game_paused,
        "no_path_count": snake.no_path_count,
    }
