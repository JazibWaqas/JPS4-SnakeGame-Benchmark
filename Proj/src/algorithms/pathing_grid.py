import time
from helper import Point, UnionFind, AstarContext

# Cost of moving one step on the grid
STEP_COST = 1


class PathingGrid:
    # Counter for when JPS4 falls back to regular search
    _fallback_outer_hits = 0

    def __init__(self, width, height, default_value):
        self.width = width
        self.height = height
        # 2D grid: False = empty, True = blocked
        self.grid = [[default_value for _ in range(width)] for _ in range(height)]
        # Union-Find for fast connectivity checks
        self.components = UnionFind(width * height)
        self.components_dirty = True  # Need to rebuild when grid changes
        # Heuristic scaling factor (usually 1.0)
        self.heuristic_factor = 1.0
        # Shared A* search context
        self.context = AstarContext()
        # Performance metrics from last search
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0
        # Nodes expanded in last search (for visualization)
        self.last_explored = []

    # Check if coordinates are within grid bounds
    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    # Get grid value at coordinates
    def get(self, x, y):
        return self.grid[y][x]

    # Set grid value and mark components as dirty if changed
    def set(self, x, y, blocked):
        if not self.in_bounds(x, y):
            return
        old = self.grid[y][x]
        self.grid[y][x] = blocked
        if old != blocked:
            self.components_dirty = True

    # Get 4-connected neighbors (up, right, down, left)
    def neighborhood_points(self, point):
        return point.neumann_neighborhood()

    # Get valid neighbors with movement cost
    def neighborhood_points_and_cost(self, pos):
        result = []
        for neighbor in self.neighborhood_points(pos):
            if self.can_move_to(neighbor):
                result.append((neighbor, STEP_COST))
        return result

    # Manhattan distance heuristic (admissible for 4-connected grids)
    def heuristic(self, first, second):
        return first.manhattan_distance(second) * STEP_COST

    # Check if a position can be moved to (in bounds and not blocked)
    def can_move_to(self, pos):
        return self.in_bounds(pos.x, pos.y) and not self.grid[pos.y][pos.x]

    # JPS4: Prune neighbors that don't need to be explored
    def jps_prune_neighbors(self, parent, node):
        # At start node, explore all 4 directions
        if parent is None:
            return [n for n in node.neumann_neighborhood() if self.can_move_to(n)]

        direction = parent.direction_to(node)
        pruned = []

        # Horizontal movement: don't prune any neighbors
        if direction.x != 0:
            for neighbor in node.neumann_neighborhood():
                if neighbor != parent and self.can_move_to(neighbor):
                    pruned.append(neighbor)
        # Vertical movement: only keep forward and forced neighbors
        else:
            forward = Point(node.x, node.y + direction.y)
            if self.can_move_to(forward):
                pruned.append(forward)
            # Check for forced neighbors on left/right of obstacles
            for side in (-1, 1):
                beside_parent = Point(parent.x + side, parent.y)
                beside_node = Point(node.x + side, node.y)
                if not self.can_move_to(beside_parent) and self.can_move_to(beside_node):
                    pruned.append(beside_node)

        return pruned

    # JPS4: Jump along a direction until hitting goal, obstacle, or jump point
    def jps_jump(self, current, direction, goal):
        is_goal = goal if callable(goal) else (lambda point: point == goal)
        prev = current
        
        while True:
            step = Point(prev.x + direction.x, prev.y + direction.y)
            # Hit obstacle: no path in this direction
            if not self.can_move_to(step):
                return None
            # Reached goal: return goal position
            if is_goal(step):
                return step
            # Horizontal jumps: stop immediately (no pruning for horizontal)
            if direction.x != 0:
                return step
            # Vertical jumps: check for forced neighbors that create jump points
            for side in (-1, 1):
                beside_prev = Point(prev.x + side, prev.y)
                beside_step = Point(step.x + side, step.y)
                # Found forced neighbor: this is a jump point
                if not self.can_move_to(beside_prev) and self.can_move_to(beside_step):
                    return step
            prev = step

    # JPS4: Find successor nodes by jumping from pruned neighbors
    def jps_successors(self, parent, node, goal):
        # At goal: only goal itself as successor
        if goal(node):
            return [(node, 0)]

        # Calculate immediate parent for direction finding
        if parent is None or parent == node:
            immediate_parent = None
        else:
            direction = parent.direction_to(node)
            immediate_parent = Point(node.x - direction.x, node.y - direction.y)

        successors = []
        # For each pruned neighbor, jump to find jump point
        for neighbor in self.jps_prune_neighbors(immediate_parent, node):
            direction = node.direction_to(neighbor)
            found = self.jps_jump(node, direction, goal)
            if found is not None:
                # Cost is Manhattan distance to jump point
                cost = STEP_COST * node.manhattan_distance(found)
                successors.append((found, cost))

        return successors

    # Build Union-Find components for fast reachability checks
    def generate_components(self):
        self.components = UnionFind(self.width * self.height)
        self.components_dirty = False
        
        # Connect all adjacent empty cells
        for y in range(self.height):
            for x in range(self.width):
                if not self.grid[y][x]:  # Empty cell
                    idx = y * self.width + x
                    # Check 4 neighbors
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < self.width and 0 <= ny < self.height and not self.grid[ny][nx]:
                            self.components.union(idx, ny * self.width + nx)

    # Check if two positions are in the same connected component
    def reachable(self, start, end):
        if not (self.in_bounds(start.x, start.y) and self.in_bounds(end.x, end.y)):
            return False
        if self.grid[start.y][start.x] or self.grid[end.y][end.x]:
            return False
        if self.components_dirty:
            self.generate_components()
        return self.components.equiv(start.y * self.width + start.x,
                                     end.y * self.width + end.x)

    # Main pathfinding interface - returns waypoints (not full path)
    def get_waypoints_single_goal(self, start, goal, mode="astar"):
        # Reset performance metrics
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0

        # Adjacent cells: direct path without search
        if start.manhattan_distance(goal) == 1:
            self.last_path_len = 2
            return [start, goal]

        # Quick reject if unreachable
        if not self.reachable(start, goal):
            return None

        # Setup goal test and heuristics
        goal_test = lambda point: point == goal
        heuristic = lambda point: int(self.heuristic(point, goal) * self.heuristic_factor)
        astar_successors = lambda parent, node: self.standard_astar_successors(node, goal_test)
        zero_heuristic = lambda point: 0  # For Dijkstra

        started = time.perf_counter()

        # Run selected algorithm
        if mode == "jps4":
            result = self.context.astar_jps(
                start,
                lambda parent, node: self.jps_successors(parent, node, goal_test),
                heuristic,
                goal_test,
            )
        elif mode == "dijkstra":
            result = self.context.astar_jps(start, astar_successors, zero_heuristic, goal_test)
        else:  # A*
            result = self.context.astar_jps(start, astar_successors, heuristic, goal_test)

        # Record performance metrics
        self.last_ms = (time.perf_counter() - started) * 1000.0
        self.last_expansions = self.context.expansions
        self.last_explored = list(self.context.last_expanded)

        if result is None:
            if mode == "jps4":
                PathingGrid._fallback_outer_hits += 1
            return None

        path, _cost = result
        return path

    # Try to find direct straight-line path (no obstacles)
    def find_direct_path(self, start, goal):
        if start == goal:
            return [start]
        if start.manhattan_distance(goal) == 1:
            return [start, goal]

        # Horizontal line: check all cells between start and goal
        if start.y == goal.y:
            lo, hi = min(start.x, goal.x), max(start.x, goal.x)
            for x in range(lo, hi + 1):
                if x != start.x and x != goal.x and self.grid[start.y][x]:
                    return None  # Obstacle in the way
            # Build path step by step
            path = []
            step = 1 if goal.x > start.x else -1
            for x in range(start.x, goal.x + step, step):
                path.append(Point(x, start.y))
            return path

        # Vertical line: check all cells between start and goal
        if start.x == goal.x:
            lo, hi = min(start.y, goal.y), max(start.y, goal.y)
            for y in range(lo, hi + 1):
                if y != start.y and y != goal.y and self.grid[y][start.x]:
                    return None  # Obstacle in the way
            # Build path step by step
            path = []
            step = 1 if goal.y > start.y else -1
            for y in range(start.y, goal.y + step, step):
                path.append(Point(start.x, y))
            return path

        return None

    # Standard A* successor function (for Dijkstra and A*)
    def standard_astar_successors(self, node, goal):
        if goal(node):
            return [(node, 0)]
        return [(neighbor, STEP_COST) for neighbor in self.neighborhood_points(node) if self.can_move_to(neighbor)]

    # Get complete path (all intermediate cells) from waypoints
    def get_path_single_goal(self, start, goal, mode="astar"):
        waypoints = self.get_waypoints_single_goal(start, goal, mode)
        if waypoints is None or len(waypoints) == 0:
            return None
        path = self.waypoints_to_path(waypoints)
        self.last_path_len = len(path) if path else 0
        if not self.validate_path(path):
            return None
        return path

    # Convert waypoints to full path by filling in intermediate cells
    def waypoints_to_path(self, waypoints):
        if not waypoints:
            return []
        path = [waypoints[0]]
        for i in range(1, len(waypoints)):
            current = path[-1]
            target = waypoints[i]
            # Move step by step toward target
            while current.manhattan_distance(target) > 0:
                direction = current.direction_to(target)
                current = current + direction
                path.append(current)
                if current.x == target.x and current.y == target.y:
                    break
        return path

    # Verify path is valid (connected, in bounds, not blocked)
    def validate_path(self, path):
        if not path or len(path) < 2:
            return True
        for i in range(len(path) - 1):
            # Check consecutive cells are adjacent
            if path[i].manhattan_distance(path[i+1]) > 1:
                return False
            # Check cells are valid (in bounds and not blocked)
            for point in (path[i], path[i+1]):
                if not self.in_bounds(point.x, point.y) or self.grid[point.y][point.x]:
                    return False
        return True
