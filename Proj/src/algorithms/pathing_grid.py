import time
from helper import Point, UnionFind, AstarContext

STEP_COST = 1


class PathingGrid:
    _fallback_outer_hits = 0

    def __init__(self, width, height, default_value):
        self.width = width
        self.height = height
        self.grid = [[default_value for _ in range(width)] for _ in range(height)]
        self.components = UnionFind(width * height)
        self.components_dirty = True
        self.heuristic_factor = 1.0
        self.context = AstarContext()
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x, y):
        return self.grid[y][x]

    def set(self, x, y, blocked):
        if not self.in_bounds(x, y):
            return
        old = self.grid[y][x]
        self.grid[y][x] = blocked
        if old != blocked:
            self.components_dirty = True

    def neighborhood_points(self, point):
        return point.neumann_neighborhood()

    def neighborhood_points_and_cost(self, pos):
        result = []
        for neighbor in self.neighborhood_points(pos):
            if self.can_move_to(neighbor):
                result.append((neighbor, STEP_COST))
        return result

    def heuristic(self, first, second):
        return first.manhattan_distance(second) * STEP_COST

    def can_move_to(self, pos):
        return self.in_bounds(pos.x, pos.y) and not self.grid[pos.y][pos.x]

    def jps_prune_neighbors(self, parent, node):
        # print("prune at", node, "parent=", parent)
        if parent is None:
            return [n for n in node.neumann_neighborhood() if self.can_move_to(n)]

        direction = parent.direction_to(node)
        pruned = []

        if direction.x != 0:
            for neighbor in node.neumann_neighborhood():
                if neighbor != parent and self.can_move_to(neighbor):
                    pruned.append(neighbor)
        else:
            forward = Point(node.x, node.y + direction.y)
            if self.can_move_to(forward):
                pruned.append(forward)
            for side in (-1, 1):
                beside_parent = Point(parent.x + side, parent.y)
                beside_node = Point(node.x + side, node.y)
                if not self.can_move_to(beside_parent) and self.can_move_to(beside_node):
                    pruned.append(beside_node)

        return pruned

    def jps_jump(self, current, direction, goal):
        is_goal = goal if callable(goal) else (lambda point: point == goal)
        prev = current
        while True:
            step = Point(prev.x + direction.x, prev.y + direction.y)
            if not self.can_move_to(step):
                return None
            if is_goal(step):
                # print("jump hit goal at", step)
                return step
            if direction.x != 0:
                return step
            for side in (-1, 1):
                beside_prev = Point(prev.x + side, prev.y)
                beside_step = Point(step.x + side, step.y)
                if not self.can_move_to(beside_prev) and self.can_move_to(beside_step):
                    return step
            prev = step

    def jps_successors(self, parent, node, goal):
        if goal(node):
            return [(node, 0)]

        if parent is None or parent == node:
            immediate_parent = None
        else:
            direction = parent.direction_to(node)
            immediate_parent = Point(node.x - direction.x, node.y - direction.y)

        successors = []
        for neighbor in self.jps_prune_neighbors(immediate_parent, node):
            direction = node.direction_to(neighbor)
            found = self.jps_jump(node, direction, goal)
            if found is not None:
                cost = STEP_COST * node.manhattan_distance(found)
                successors.append((found, cost))

        return successors

    def generate_components(self):
        self.components = UnionFind(self.width * self.height)
        self.components_dirty = False
        for y in range(self.height):
            for x in range(self.width):
                if not self.grid[y][x]:
                    idx = y * self.width + x
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < self.width and 0 <= ny < self.height and not self.grid[ny][nx]:
                            self.components.union(idx, ny * self.width + nx)

    def reachable(self, start, end):
        if not (self.in_bounds(start.x, start.y) and self.in_bounds(end.x, end.y)):
            return False
        if self.grid[start.y][start.x] or self.grid[end.y][end.x]:
            return False
        if self.components_dirty:
            self.generate_components()
        return self.components.equiv(start.y * self.width + start.x,
                                     end.y * self.width + end.x)

    def get_waypoints_single_goal(self, start, goal, mode="astar"):
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0

        if start.manhattan_distance(goal) == 1:
            self.last_path_len = 2
            return [start, goal]

        if not self.reachable(start, goal):
            # print("unreachable")
            return None

        goal_test = lambda point: point == goal
        heuristic = lambda point: int(self.heuristic(point, goal) * self.heuristic_factor)
        astar_successors = lambda parent, node: self.standard_astar_successors(node, goal_test)
        zero_heuristic = lambda point: 0

        started = time.perf_counter()

        if mode == "jps4":
            result = self.context.astar_jps(
                start,
                lambda parent, node: self.jps_successors(parent, node, goal_test),
                heuristic,
                goal_test,
            )
        elif mode == "dijkstra":
            result = self.context.astar_jps(start, astar_successors, zero_heuristic, goal_test)
        else:
            result = self.context.astar_jps(start, astar_successors, heuristic, goal_test)

        self.last_ms = (time.perf_counter() - started) * 1000.0
        self.last_expansions = self.context.expansions

        if result is None:
            if mode == "jps4":
                PathingGrid._fallback_outer_hits += 1
            return None

        path, _cost = result
        return path

    def find_direct_path(self, start, goal):
        if start == goal:
            return [start]
        if start.manhattan_distance(goal) == 1:
            return [start, goal]

        if start.y == goal.y:
            lo, hi = min(start.x, goal.x), max(start.x, goal.x)
            for x in range(lo, hi + 1):
                if x != start.x and x != goal.x and self.grid[start.y][x]:
                    return None
            path = []
            step = 1 if goal.x > start.x else -1
            for x in range(start.x, goal.x + step, step):
                path.append(Point(x, start.y))
            return path

        if start.x == goal.x:
            lo, hi = min(start.y, goal.y), max(start.y, goal.y)
            for y in range(lo, hi + 1):
                if y != start.y and y != goal.y and self.grid[y][start.x]:
                    return None
            path = []
            step = 1 if goal.y > start.y else -1
            for y in range(start.y, goal.y + step, step):
                path.append(Point(start.x, y))
            return path

        return None

    def standard_astar_successors(self, node, goal):
        if goal(node):
            return [(node, 0)]
        return [(neighbor, STEP_COST) for neighbor in self.neighborhood_points(node) if self.can_move_to(neighbor)]

    def get_path_single_goal(self, start, goal, mode="astar"):
        waypoints = self.get_waypoints_single_goal(start, goal, mode)
        if waypoints is None or len(waypoints) == 0:
            return None
        path = self.waypoints_to_path(waypoints)
        self.last_path_len = len(path) if path else 0
        if not self.validate_path(path):
            # print("path validation failed")
            return None
        return path

    def waypoints_to_path(self, waypoints):
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

    def validate_path(self, path):
        if not path or len(path) < 2:
            return True
        for i in range(len(path) - 1):
            if path[i].manhattan_distance(path[i+1]) > 1:
                return False
            for point in (path[i], path[i+1]):
                if not self.in_bounds(point.x, point.y) or self.grid[point.y][point.x]:
                    return False
        return True
