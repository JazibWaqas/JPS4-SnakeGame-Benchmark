"""
Correctness & regression tests for the five fixes applied to the JPS4
Snake-Game project. Covers:

    1. Horizontal pruning rule matches Baum (2025) Algorithm 2
       - all three algorithms return the SAME path length on many random instances
       - JPS4 outer fallback tripwire stays at zero
       - JPS4 expansion count is <= A* expansion count on open-ish maps
    2. post_process_path removed — no line-of-sight smoothing
    3. jps_jump is iterative (no recursion limit)
    4. pick_start_goal uses true BFS-farthest
    5. UnionFind.find is iterative (no recursion limit on 200x200)

Also tests:
    - Known-answer small grids (4 hand-built cases)
    - Forced-neighbour rule for vertical movement
    - Snake-game integration path (run_three_way_compare)

Run:
    python -m tests.test_fixes
or:
    python tests/test_fixes.py
"""
from __future__ import annotations

import os
import random
import sys
import time
import unittest
from collections import deque
from typing import List, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
_CODE = os.path.join(_PROJ, "src", "Snake Game Code")
for p in (_PROJ, _CODE):
    if p not in sys.path:
        sys.path.insert(0, p)

from helper import Point, UnionFind
from pathing_grid import PathingGrid
from benchmark_interim import make_grid, grid_to_pg, pick_start_goal, run_mode


def _bfs_distance(grid, start, goal) -> int:
    """Ground-truth shortest path length (in cells, including endpoints)."""
    h, w = len(grid), len(grid[0])
    if grid[start[0]][start[1]] or grid[goal[0]][goal[1]]:
        return -1
    dist = {start: 0}
    q = deque([start])
    while q:
        y, x = q.popleft()
        if (y, x) == goal:
            return dist[(y, x)] + 1  # number of cells in path
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not grid[ny][nx] and (ny, nx) not in dist:
                dist[(ny, nx)] = dist[(y, x)] + 1
                q.append((ny, nx))
    return -1


# ---------------------------------------------------------------------------
class TestKnownAnswers(unittest.TestCase):
    """Hand-built small grids with a hand-computed answer."""

    def _run_all(self, grid, s_yx, g_yx, expected_cells):
        for mode in ("dijkstra", "astar", "jps4"):
            pg = grid_to_pg(grid)
            path = pg.get_path_single_goal(Point(s_yx[1], s_yx[0]),
                                           Point(g_yx[1], g_yx[0]),
                                           mode=mode)
            self.assertIsNotNone(path, f"{mode} returned None on solvable instance")
            self.assertEqual(len(path), expected_cells,
                             f"{mode} path length {len(path)} != {expected_cells}")
            # adjacency
            for i in range(len(path) - 1):
                self.assertEqual(path[i].manhattan_distance(path[i + 1]), 1,
                                 f"{mode} non-adjacent step at index {i}")

    def test_open_5x5(self):
        g = [[False] * 5 for _ in range(5)]
        self._run_all(g, (0, 0), (4, 4), 9)  # 4+4+1 = 9 cells

    def test_single_wall(self):
        g = [[False] * 5 for _ in range(5)]
        g[2][1] = g[2][2] = g[2][3] = True  # a horizontal wall segment
        self._run_all(g, (0, 2), (4, 2), 9)  # must go around

    def test_corridor(self):
        # 1-wide corridor: only one path exists
        g = [
            [False, True,  True,  True,  True],
            [False, False, False, False, True],
            [True,  True,  True,  False, True],
            [True,  True,  True,  False, False],
        ]
        self._run_all(g, (0, 0), (3, 4), 8)

    def test_unreachable(self):
        g = [[False] * 4 for _ in range(4)]
        g[1] = [True] * 4  # full-width wall
        for mode in ("dijkstra", "astar", "jps4"):
            pg = grid_to_pg(g)
            path = pg.get_path_single_goal(Point(0, 0), Point(3, 3), mode=mode)
            self.assertIsNone(path, f"{mode} should return None when unreachable")


# ---------------------------------------------------------------------------
class TestThreeWayEquality(unittest.TestCase):
    """All three algorithms must return the same path length on random grids.
    Run many trials across several densities; any disagreement is a hard failure.
    """

    def _trial(self, rng, size, density):
        g = make_grid(size, size, density, rng)
        sg = pick_start_goal(g, rng)
        if sg is None:
            return None
        start, goal = sg
        pg0 = grid_to_pg(g)
        if not pg0.reachable(start, goal):
            return None
        lens = {}
        exps = {}
        for mode in ("dijkstra", "astar", "jps4"):
            pg = grid_to_pg(g)
            path = pg.get_path_single_goal(start, goal, mode=mode)
            self.assertIsNotNone(path, f"{mode} returned None on reachable grid")
            lens[mode] = len(path)
            exps[mode] = pg.last_expansions
        return lens, exps

    def test_equality_many_trials(self):
        rng = random.Random(12345)
        PathingGrid._fallback_outer_hits = 0
        densities = (0.00, 0.10, 0.15, 0.22, 0.28, 0.35, 0.40)
        per_density = 12
        total = 0
        astar_wins_or_ties = 0
        jps_le_astar = 0
        for d in densities:
            for _ in range(per_density):
                r = self._trial(rng, 30, d)
                if r is None:
                    continue
                lens, exps = r
                self.assertEqual(lens["dijkstra"], lens["astar"],
                                 f"dijkstra vs astar len mismatch at d={d}: {lens}")
                self.assertEqual(lens["astar"], lens["jps4"],
                                 f"astar vs jps4 len mismatch at d={d}: {lens}")
                self.assertLessEqual(exps["astar"], exps["dijkstra"] + 1,
                                     f"A* expansions > Dijkstra at d={d}: {exps}")
                if exps["jps4"] <= exps["astar"]:
                    jps_le_astar += 1
                total += 1
        self.assertGreater(total, 0, "No valid trials ran")
        self.assertEqual(PathingGrid._fallback_outer_hits, 0,
                         "JPS4 returned None on a reachable instance (outer fallback fired)")
        # On the mixed density sweep, JPS4 should be better-or-equal in
        # expansions on the majority of instances (open maps benefit most).
        self.assertGreaterEqual(jps_le_astar, total // 2,
                                f"JPS4 beat A* on only {jps_le_astar}/{total} trials; "
                                f"pruning rules may still be wrong")


# ---------------------------------------------------------------------------
class TestPruningRules(unittest.TestCase):
    """Direct unit tests on jps_prune_neighbors matching Baum Alg. 2."""

    def _pg(self, grid):
        return grid_to_pg(grid)

    def test_horizontal_movement_keeps_3_non_parent_neighbours_open(self):
        # Open 5x5, move right from (1,2) to (2,2). Parent = (1,2), node = (2,2).
        # Expected natural neighbours: (3,2) forward, (2,1) up, (2,3) down.
        g = [[False] * 5 for _ in range(5)]
        pg = self._pg(g)
        parent = Point(1, 2)
        node = Point(2, 2)
        pruned = pg.jps_prune_neighbors(parent, node)
        self.assertEqual(set(pruned), {Point(3, 2), Point(2, 1), Point(2, 3)})

    def test_vertical_movement_only_forward_on_open(self):
        g = [[False] * 5 for _ in range(5)]
        pg = self._pg(g)
        # Moving up from (2,3) to (2,2). Expected: only (2,1) (straight ahead up).
        parent = Point(2, 3)
        node = Point(2, 2)
        pruned = pg.jps_prune_neighbors(parent, node)
        self.assertEqual(pruned, [Point(2, 1)])

    def test_vertical_movement_forced_neighbour_on_wall(self):
        # A wall to the LEFT of the parent should turn the LEFT-of-node into a forced neighbour.
        g = [[False] * 5 for _ in range(5)]
        g[3][1] = True   # wall at (x=1,y=3) -- this is to the left of parent (2,3)
        pg = self._pg(g)
        parent = Point(2, 3)
        node = Point(2, 2)  # moving up
        pruned = pg.jps_prune_neighbors(parent, node)
        self.assertIn(Point(1, 2), pruned)
        self.assertIn(Point(2, 1), pruned)  # forward still there

    def test_no_forced_neighbour_when_no_wall(self):
        g = [[False] * 5 for _ in range(5)]
        pg = self._pg(g)
        parent = Point(2, 3)
        node = Point(2, 2)
        pruned = pg.jps_prune_neighbors(parent, node)
        # On fully open grid, only the forward vertical is natural.
        self.assertEqual(set(pruned), {Point(2, 1)})

    def test_horizontal_movement_no_forced_neighbours(self):
        """Baum §4.2: 'Horizontal movements never produce forced neighbours.'"""
        # Even with walls arranged like the vertical-case trigger,
        # horizontal movement should just return all 3 non-parent free neighbours.
        g = [[False] * 5 for _ in range(5)]
        g[1][1] = True  # wall above parent
        pg = self._pg(g)
        parent = Point(1, 2)
        node = Point(2, 2)
        pruned = pg.jps_prune_neighbors(parent, node)
        # Expected: (3,2), (2,1), (2,3)  — all free, no special forced logic
        self.assertEqual(set(pruned), {Point(3, 2), Point(2, 1), Point(2, 3)})


# ---------------------------------------------------------------------------
class TestJumpIterative(unittest.TestCase):
    """Fix 3: vertical jump is iterative; must handle long corridors without
    hitting Python's recursion limit."""

    def test_long_vertical_jump(self):
        N = 500  # much deeper than Python's default recursion limit of 1000/2
        g = [[False] for _ in range(N)]  # 1 column x N rows, all open
        pg = grid_to_pg(g)
        old_limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(200)  # force any recursion to blow up fast
            start = Point(0, N - 1)
            goal = Point(0, 0)
            # Manually invoke the jump function in the up direction
            result = pg.jps_jump(start, Point(0, -1), goal)
            self.assertEqual(result, goal)
        finally:
            sys.setrecursionlimit(old_limit)

    def test_full_jps4_on_long_corridor(self):
        # full search end-to-end over a long corridor
        N = 500
        g = [[False] for _ in range(N)]
        pg = grid_to_pg(g)
        old_limit = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(200)
            path = pg.get_path_single_goal(Point(0, 0), Point(0, N - 1), mode="jps4")
            self.assertIsNotNone(path)
            self.assertEqual(len(path), N)
        finally:
            sys.setrecursionlimit(old_limit)


# ---------------------------------------------------------------------------
class TestUnionFind(unittest.TestCase):
    """Fix 5: iterative path-halving."""

    def test_basic_equivalence(self):
        uf = UnionFind(6)
        uf.union(0, 1); uf.union(1, 2); uf.union(3, 4)
        self.assertTrue(uf.equiv(0, 2))
        self.assertTrue(uf.equiv(3, 4))
        self.assertFalse(uf.equiv(0, 5))
        self.assertFalse(uf.equiv(2, 3))

    def test_no_recursion_limit(self):
        N = 50_000
        uf = UnionFind(N)
        for i in range(N - 1):
            uf.union(i, i + 1)  # long chain
        old = sys.getrecursionlimit()
        try:
            sys.setrecursionlimit(200)
            # Would blow up a recursive find()
            self.assertTrue(uf.equiv(0, N - 1))
        finally:
            sys.setrecursionlimit(old)

    def test_on_large_grid(self):
        # 200x200 fully-open grid => 40k free cells, one big component
        W = H = 200
        g = [[False] * W for _ in range(H)]
        pg = grid_to_pg(g)
        self.assertTrue(pg.reachable(Point(0, 0), Point(W - 1, H - 1)))


# ---------------------------------------------------------------------------
class TestPickStartGoal(unittest.TestCase):
    """Fix 4: true BFS-farthest pair."""

    def test_returns_far_pair_on_open_grid(self):
        rng = random.Random(7)
        g = [[False] * 20 for _ in range(20)]
        s, t = pick_start_goal(g, rng)
        # On a 20x20 open grid the true diameter is 38 (|0-19|+|0-19|).
        # The two-BFS trick is a 2-approximation so must get >= 19 here, but
        # in practice on grids it lands on or near the true diameter.
        d = s.manhattan_distance(t)
        self.assertGreaterEqual(d, 30, f"pair too close: d={d}")

    def test_returns_connected_pair(self):
        rng = random.Random(11)
        g = make_grid(30, 30, 0.25, rng)
        result = pick_start_goal(g, rng)
        if result is None:
            self.skipTest("degenerate grid")
        s, t = result
        pg = grid_to_pg(g)
        self.assertTrue(pg.reachable(s, t))

    def test_small_grid_degenerate(self):
        g = [[False]]
        self.assertIsNone(pick_start_goal(g, random.Random(0)))


# ---------------------------------------------------------------------------
class TestNoPostProcessSmoothing(unittest.TestCase):
    """Fix 2: post_process_path must be gone; path equality across algos is
    already tested elsewhere, but we also verify the dead method is removed."""

    def test_post_process_path_removed(self):
        self.assertFalse(hasattr(PathingGrid, "post_process_path"),
                         "post_process_path should have been deleted")
        self.assertFalse(hasattr(PathingGrid, "optimize_path"),
                         "optimize_path should have been deleted")
        self.assertFalse(hasattr(PathingGrid, "validate_optimized_path"),
                         "validate_optimized_path should have been deleted")
        self.assertFalse(hasattr(PathingGrid, "can_potentially_reach_goal"),
                         "can_potentially_reach_goal should have been deleted")


# ---------------------------------------------------------------------------
class TestSnakeGameInterface(unittest.TestCase):
    """End-to-end test of the Snake-game public surface.

    The merged snake_game_jps4 module uses make_board(density) to generate
    random 40x40 obstacle layouts and update_pathing_grid(pg, board) to
    transfer that layout to a PathingGrid. We exercise the same API the
    game's own food_search method uses and assert that all three algorithms
    produce equal-length paths on the game's own board topology.
    """

    def setUp(self):
        import importlib
        import numpy as np
        self.np = np
        try:
            self.sg = importlib.import_module("snake_game_jps4")
        except Exception as e:
            self.skipTest(f"snake_game_jps4 import failed: {e}")

    def _board_to_pg(self, board):
        """Replicate exactly what snake_game_jps4.Snake.food_search does."""
        pg = PathingGrid(board.shape[1], board.shape[0], False)
        self.sg.update_pathing_grid(pg, board)
        return pg

    def _pick_head_food(self, board):
        """Pick a head near the spawn area and the farthest free food cell."""
        free = [(y, x) for y in range(board.shape[0])
                for x in range(board.shape[1]) if board[y, x] == self.sg.EMPTY]
        if len(free) < 2:
            return None
        head = (2, 2) if board[2, 2] == self.sg.EMPTY else free[0]
        food = max(free, key=lambda c: abs(c[0] - head[0]) + abs(c[1] - head[1]))
        return head, food

    def _run_all(self, board, head, food):
        """Run all three modes on the same instance; return {mode: (ok, len, exp)}."""
        out = {}
        for mode in self.sg.DEMO_SEQUENCE:
            pg = self._board_to_pg(board)
            start = Point(head[1], head[0])
            goal = Point(food[1], food[0])
            path = pg.get_path_single_goal(start, goal, mode=mode)
            out[mode] = (path is not None, len(path) if path else 0,
                         pg.last_expansions)
        return out

    def test_snake_game_module_surface(self):
        """All constants and functions the game needs are exported and the
        module is importable without blocking in mainloop."""
        for attr in ("make_board", "update_pathing_grid", "DEMO_SEQUENCE",
                     "ALGO_LABELS", "GRID_N", "HEAD", "BODY", "FOOD",
                     "WALL", "EMPTY", "Snake"):
            self.assertTrue(hasattr(self.sg, attr), f"snake_game missing {attr}")
        self.assertEqual(self.sg.GRID_N, 40)
        self.assertEqual(set(self.sg.DEMO_SEQUENCE), {"dijkstra", "astar", "jps4"})

    def test_update_pathing_grid_marks_walls_and_body(self):
        """Walls and body cells must be blocked; head/food/empty must be free.
        This is the exact contract Snake.food_search depends on."""
        np = self.np
        b = np.zeros((5, 5), dtype=int)
        b[0, 0] = self.sg.WALL
        b[1, 1] = self.sg.BODY
        b[2, 2] = self.sg.HEAD
        b[3, 3] = self.sg.FOOD
        b[4, 4] = self.sg.EMPTY
        pg = self._board_to_pg(b)
        self.assertTrue(pg.grid[0][0])   # wall blocked
        self.assertTrue(pg.grid[1][1])   # body blocked
        self.assertFalse(pg.grid[2][2])  # head passable
        self.assertFalse(pg.grid[3][3])  # food passable
        self.assertFalse(pg.grid[4][4])  # empty passable

    def test_make_board_low_density_all_three_agree(self):
        """A sparse 40x40 board must be solvable and the three algorithms
        must return equal path lengths."""
        np = self.np
        board = np.array(self.sg.make_board(0.05), dtype=int)
        self.assertEqual(board.shape, (40, 40))
        hf = self._pick_head_food(board)
        self.assertIsNotNone(hf)
        head, food = hf
        out = self._run_all(board, head, food)
        for mode, (ok, plen, exp) in out.items():
            self.assertTrue(ok, f"{mode} returned no path on low-density board ({out})")
        lens = {l for _, l, _ in out.values()}
        self.assertEqual(len(lens), 1, f"length disagreement: {out}")

    def test_make_board_medium_density_all_three_agree(self):
        np = self.np
        board = np.array(self.sg.make_board(0.15), dtype=int)
        hf = self._pick_head_food(board)
        if hf is None:
            self.skipTest("degenerate board")
        head, food = hf
        out = self._run_all(board, head, food)
        oks = {ok for ok, _, _ in out.values()}
        # Either all three succeed or all three fail (same reachability)
        self.assertEqual(len(oks), 1, f"reachability disagreement: {out}")
        if list(oks)[0]:
            lens = {l for _, l, _ in out.values()}
            self.assertEqual(len(lens), 1, f"length disagreement: {out}")

    def test_make_board_high_density_all_three_agree(self):
        np = self.np
        board = np.array(self.sg.make_board(0.30), dtype=int)
        hf = self._pick_head_food(board)
        if hf is None:
            self.skipTest("degenerate board")
        head, food = hf
        out = self._run_all(board, head, food)
        oks = {ok for ok, _, _ in out.values()}
        self.assertEqual(len(oks), 1, f"reachability disagreement: {out}")
        if list(oks)[0]:
            lens = {l for _, l, _ in out.values()}
            self.assertEqual(len(lens), 1, f"length disagreement: {out}")


# ---------------------------------------------------------------------------
class TestGroundTruthComparison(unittest.TestCase):
    """Double-check: path length from each algorithm matches a clean BFS."""

    def test_matches_bfs_on_random_grids(self):
        rng = random.Random(999)
        for trial in range(20):
            g = make_grid(25, 25, 0.25, rng)
            sg = pick_start_goal(g, rng)
            if sg is None:
                continue
            start, goal = sg
            pg0 = grid_to_pg(g)
            if not pg0.reachable(start, goal):
                continue
            bfs_len = _bfs_distance(g, (start.y, start.x), (goal.y, goal.x))
            self.assertGreater(bfs_len, 0)
            for mode in ("dijkstra", "astar", "jps4"):
                pg = grid_to_pg(g)
                path = pg.get_path_single_goal(start, goal, mode=mode)
                self.assertIsNotNone(path, f"{mode} failed trial {trial}")
                self.assertEqual(len(path), bfs_len,
                                 f"{mode} len {len(path)} != BFS {bfs_len} trial {trial}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main(verbosity=2)
