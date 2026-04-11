import time
from typing import List, Tuple, Optional, Callable
from helper import Point, UnionFind, AstarContext

# Uniform movement cost (for cardinal moves)
C = 1


class PathingGrid:
    def __init__(self, width: int, height: int, default_value: bool):
        self.width = width
        self.height = height
        self.grid: List[List[bool]] = [[default_value for _ in range(width)] for _ in range(height)]
        self.components = UnionFind(width * height)
        # Start dirty: components must be rebuilt from the final grid layout
        # before the first reachable() query. Previously this was False and
        # latent-broken on grids loaded without any state changes (e.g. a fully
        # open grid populated via set(x,y,False)).
        self.components_dirty = True
        self.heuristic_factor = 1.0
        self.context = AstarContext()
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> bool:
        return self.grid[y][x]

    def set(self, x: int, y: int, blocked: bool):
        if not self.in_bounds(x, y):
            return
        old_val = self.grid[y][x]
        self.grid[y][x] = blocked
        if old_val != blocked:
            self.components_dirty = True

    def neighborhood_points(self, point: Point) -> List[Point]:
        return point.neumann_neighborhood()

    def neighborhood_points_and_cost(self, pos: Point) -> List[Tuple[Point, int]]:
        result = []
        for p in self.neighborhood_points(pos):
            if self.can_move_to(p):
                result.append((p, C))
        return result

    def heuristic(self, p1: Point, p2: Point) -> int:
        return p1.manhattan_distance(p2) * C

    def can_move_to(self, pos: Point) -> bool:
        return self.in_bounds(pos.x, pos.y) and not self.grid[pos.y][pos.x]

    # --- JPS4 (Horizontal-First Jump Point Search), per Baum 2025 ---
    # Tripwires: counted when the fallback branches fire. In a correct
    # implementation they should stay at zero; tests assert this.
    _fallback_inner_hits = 0
    _fallback_outer_hits = 0

    def jps_prune_neighbors(self, parent: Optional[Point], node: Point) -> List[Point]:
        r"""
        Baum (2025) Algorithm 2 — naturalNeighbors:
            horizontal movement: neighbors(x) \ {p}  (all 3 non-parent neighbours)
            vertical   movement: {x + direction(p,x)} (only the cell straight ahead)
        plus Algorithm 3 — forcedNeighbors (only possible for vertical movement):
            a sideways neighbour n of x is forced if the sideways cell of p is blocked.
        """
        if parent is None:
            return [n for n in node.neumann_neighborhood() if self.can_move_to(n)]

        direction = parent.direction_to(node)
        pruned: List[Point] = []

        if direction.x != 0:  # horizontal movement — keep all non-parent neighbours
            for n in node.neumann_neighborhood():
                if n != parent and self.can_move_to(n):
                    pruned.append(n)
            # Horizontal movements never produce forced neighbours (Baum §4.2).
        else:  # vertical movement — natural = cell straight ahead
            ahead = Point(node.x, node.y + direction.y)
            if self.can_move_to(ahead):
                pruned.append(ahead)
            # Forced neighbours: sideways cell of parent blocked => sideways cell of node forced
            for dx in (-1, 1):
                side_of_parent = Point(parent.x + dx, parent.y)
                side_of_node = Point(node.x + dx, node.y)
                if not self.can_move_to(side_of_parent) and self.can_move_to(side_of_node):
                    pruned.append(side_of_node)

        return pruned

    def jps_jump(self, current: Point, direction: Point, goal) -> Optional[Point]:
        """
        Baum (2025) Algorithm 5 — iterative while loop.
        Horizontal jumps return after one step; vertical jumps recurse (iteratively)
        until hitting an obstacle, the goal, or a cell with a forced neighbour.
        """
        is_goal = goal if callable(goal) else (lambda pt: pt == goal)
        p = current
        while True:
            x = Point(p.x + direction.x, p.y + direction.y)
            if not self.can_move_to(x):
                return None
            if is_goal(x):
                return x
            if direction.x != 0:  # horizontal: one step per jump
                return x
            # vertical: check forced neighbours using parent p
            for dx in (-1, 1):
                side_of_parent = Point(p.x + dx, p.y)
                side_of_x = Point(x.x + dx, x.y)
                if not self.can_move_to(side_of_parent) and self.can_move_to(side_of_x):
                    return x
            p = x

    def jps_successors(self, parent: Optional[Point], node: Point, goal: Callable[[Point], bool]) -> List[Tuple[Point, int]]:
        """Baum (2025) Algorithm 4 — Identify Successors.

        Baum's pruning rules are defined w.r.t. an *immediately adjacent* parent
        (he writes p(x) in neighbors(x), §4.2). The open-list parent stored by
        the search loop is the jump origin, which after a jump may be several
        cells away. Because JPS4 jumps are always straight, the true immediate
        parent is simply one step back along the unit direction from parent
        to node; we recompute it here before pruning.
        """
        if goal(node):
            return [(node, 0)]

        if parent is None or parent == node:
            immediate_parent = None
        else:
            d = parent.direction_to(node)
            immediate_parent = Point(node.x - d.x, node.y - d.y)

        successors: List[Tuple[Point, int]] = []
        for neighbor in self.jps_prune_neighbors(immediate_parent, node):
            direction = node.direction_to(neighbor)
            jump_result = self.jps_jump(node, direction, goal)
            if jump_result is not None:
                cost = C * node.manhattan_distance(jump_result)
                successors.append((jump_result, cost))

        # A legitimate dead end returns empty successors; the search loop
        # handles it naturally by continuing with other open-list entries.
        return successors

    def generate_components(self):
        """Rebuild the UnionFind connectivity structure from the current grid."""
        self.components = UnionFind(self.width * self.height)
        self.components_dirty = False
        for y in range(self.height):
            for x in range(self.width):
                if not self.grid[y][x]:
                    idx = y * self.width + x
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < self.width and 0 <= ny < self.height and not self.grid[ny][nx]:
                            self.components.union(idx, ny * self.width + nx)

    def reachable(self, start: Point, end: Point) -> bool:
        """Are start and end in the same free connected component?"""
        if not (self.in_bounds(start.x, start.y) and self.in_bounds(end.x, end.y)):
            return False
        if self.grid[start.y][start.x] or self.grid[end.y][end.x]:
            return False
        if self.components_dirty:
            self.generate_components()
        return self.components.equiv(start.y * self.width + start.x,
                                     end.y * self.width + end.x)

    def get_waypoints_single_goal(self, start: Point, goal: Point, mode: str = "astar") -> List[Point]:
        """Find a path from start to goal using the specified algorithm."""
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0

        if start.manhattan_distance(goal) == 1:
            self.last_path_len = 2
            return [start, goal]

        if not self.reachable(start, goal):
            return None
            
        goal_test = lambda pt: pt == goal
        heuristic = lambda point: int(self.heuristic(point, goal) * self.heuristic_factor)
        succ_astar = lambda p, n: self.standard_astar_successors(n, goal_test)
        h0 = lambda point: 0

        t0 = time.perf_counter()
        exp_sum = 0

        if mode == "jps4":
            result = self.context.astar_jps(
                start,
                lambda p, n: self.jps_successors(p, n, goal_test),
                heuristic,
                goal_test
            )
        elif mode == "dijkstra":
            result = self.context.astar_jps(start, succ_astar, h0, goal_test)
        else:
            result = self.context.astar_jps(start, succ_astar, heuristic, goal_test)
        exp_sum = self.context.expansions

        self.last_ms = (time.perf_counter() - t0) * 1000.0
        self.last_expansions = exp_sum

        if result is None:
            # Tripwire: JPS4 returned None on an instance the reachability check
            # said was solvable. In a correct implementation this cannot happen
            # (Baum 2025, Theorem 4.2). Tests assert this stays at zero.
            if mode == "jps4":
                PathingGrid._fallback_outer_hits += 1
            return None

        (path, cost) = result
        return path
    
    def find_direct_path(self, start: Point, goal: Point) -> Optional[List[Point]]:
        """
        Check if there's a direct, unobstructed path between start and goal.
        Returns a list of points forming the path if one exists, None otherwise.
        """
        # Check if they are equal or adjacent
        if start == goal:
            return [start]
        if start.manhattan_distance(goal) == 1:
            return [start, goal]
            
        # Check for horizontal line
        if start.y == goal.y:
            min_x, max_x = min(start.x, goal.x), max(start.x, goal.x)
            # Check if path is clear
            for x in range(min_x, max_x + 1):
                if x != start.x and x != goal.x and self.grid[start.y][x]:
                    return None
            # Generate the path
            path = []
            step = 1 if goal.x > start.x else -1
            for x in range(start.x, goal.x + step, step):
                path.append(Point(x, start.y))
            return path
            
        # Check for vertical line
        if start.x == goal.x:
            min_y, max_y = min(start.y, goal.y), max(start.y, goal.y)
            # Check if path is clear
            for y in range(min_y, max_y + 1):
                if y != start.y and y != goal.y and self.grid[y][start.x]:
                    return None
            # Generate the path
            path = []
            step = 1 if goal.y > start.y else -1
            for y in range(start.y, goal.y + step, step):
                path.append(Point(start.x, y))
            return path
        
        # Not a direct line path
        return None
    
    def standard_astar_successors(self, node: Point, goal: Callable[[Point], bool]) -> List[Tuple[Point, int]]:
        """Standard A*/Dijkstra successor function — all 4 free cardinal neighbours."""
        if goal(node):
            return [(node, 0)]
        return [(n, C) for n in self.neighborhood_points(node) if self.can_move_to(n)]

    def get_path_single_goal(self, start: Point, goal: Point, mode: str = "astar") -> Optional[List[Point]]:
        waypoints = self.get_waypoints_single_goal(start, goal, mode)
        if waypoints is None or len(waypoints) == 0:
            return None
        path = self.waypoints_to_path(waypoints)
        self.last_path_len = len(path) if path else 0
        if not self.validate_path(path):
            return None
        return path

    def waypoints_to_path(self, waypoints: List[Point]) -> List[Point]:
        """Expand JPS4 jump-point waypoints into an adjacent-step path."""
        if not waypoints:
            return []
        path = [waypoints[0]]
        for i in range(1, len(waypoints)):
            current = path[-1]
            target = waypoints[i]
            while current.manhattan_distance(target) > 0:
                direction = current.direction_to(target)
                current = current + direction
                path.append(current)
                if current.x == target.x and current.y == target.y:
                    break
        return path

    def validate_path(self, path: List[Point]) -> bool:
        """Verify that a path has only adjacent steps and all points are valid."""
        if not path or len(path) < 2:
            return True
        for i in range(len(path) - 1):
            if path[i].manhattan_distance(path[i+1]) > 1:
                return False
            for p in (path[i], path[i+1]):
                if not self.in_bounds(p.x, p.y) or self.grid[p.y][p.x]:
                    return False
        return True
