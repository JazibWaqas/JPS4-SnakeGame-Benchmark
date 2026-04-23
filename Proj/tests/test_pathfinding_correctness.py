import random

from benchmark_interim import grid_to_pg, make_grid, pick_start_goal


def run_modes(board, start, goal):
    results = {}
    for mode in ("dijkstra", "astar", "jps4"):
        grid = grid_to_pg(board)
        path = grid.get_path_single_goal(start, goal, mode=mode)
        results[mode] = {
            "path": path,
            "length": len(path) if path else None,
            "expansions": grid.last_expansions,
        }
    return results


def test_algorithms_match_path_lengths_on_random_grids():
    rng = random.Random(42)
    checked = 0

    for density in (0.00, 0.15, 0.28, 0.40):
        for _ in range(20):
            board = make_grid(40, 40, density, rng)
            pair = pick_start_goal(board, rng)
            if pair is None:
                continue
            start, goal = pair
            results = run_modes(board, start, goal)
            if any(results[mode]["path"] is None for mode in results):
                continue
            lengths = {results[mode]["length"] for mode in results}
            assert len(lengths) == 1, results
            checked += 1

    assert checked >= 40


def test_jps4_expands_no_more_than_astar_in_sampled_cases():
    rng = random.Random(7)
    checked = 0

    for density in (0.10, 0.15, 0.28, 0.35, 0.40):
        for _ in range(16):
            board = make_grid(40, 40, density, rng)
            pair = pick_start_goal(board, rng)
            if pair is None:
                continue
            start, goal = pair
            results = run_modes(board, start, goal)
            if any(results[mode]["path"] is None for mode in results):
                continue
            assert results["astar"]["expansions"] <= results["dijkstra"]["expansions"], results
            assert results["jps4"]["expansions"] <= results["astar"]["expansions"], results
            checked += 1

    assert checked >= 40
