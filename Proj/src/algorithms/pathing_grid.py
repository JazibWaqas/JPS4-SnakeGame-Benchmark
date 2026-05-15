import time
from helper import Point, UnionFind, AstarContext

# how much effort each step takes
STEP_COST = 1


class PathingGrid:
    # counter for when JPS4 has to fall back to the slow way
    _fallback_outer_hits = 0

    def __init__(self, width, height, default_value):
        self.width = width
        self.height = height
        # False = empty, True = wall. simple as that.
        self.grid = [[default_value for _ in range(width)] for _ in range(height)]
        # quick way to see if two points are even connected
        self.components = UnionFind(width * height)
        self.components_dirty = True  # need to rebuild if we change the map
        
        self.heuristic_factor = 1.0
        # search context we reuse to save memory
        self.context = AstarContext()
        
        # storage for last run's stats (for the UI)
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0
        self.last_explored = []

    # make sure we aren't clicking off the map
    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    # quick getter for grid values
    def get(self, x, y):
        return self.grid[y][x]

    # update the map and mark the connectivity check as "stale"
    def set(self, x, y, blocked):
        if not self.in_bounds(x, y):
            return
        old = self.grid[y][x]
        self.grid[y][x] = blocked
        if old != blocked:
            self.components_dirty = True

    # just the 4 basic neighbors
    def neighborhood_points(self, point):
        return point.neumann_neighborhood()

    # get neighbors that aren't walls
    def neighborhood_points_and_cost(self, pos):
        result = []
        for neighbor in self.neighborhood_points(pos):
            if self.can_move_to(neighbor):
                result.append((neighbor, STEP_COST))
        return result

    # distance guesser (manhattan style)
    def heuristic(self, first, second):
        return first.manhattan_distance(second) * STEP_COST

    # simple check: is this square walkable?
    def can_move_to(self, pos):
        return self.in_bounds(pos.x, pos.y) and not self.grid[pos.y][pos.x]

    # JPS4: ignore directions that are obviously useless
    def jps_prune_neighbors(self, parent, node):
        # if we're just starting out, check everywhere
        if parent is None:
            return [n for n in node.neumann_neighborhood() if self.can_move_to(n)]

        direction = parent.direction_to(node)
        pruned = []

        # horizontal movement is a bit trickier to prune
        if direction.x != 0:
            for neighbor in node.neumann_neighborhood():
                if neighbor != parent and self.can_move_to(neighbor):
                    pruned.append(neighbor)
        # vertical: only keep forward and check for forced neighbors (corners)
        else:
            forward = Point(node.x, node.y + direction.y)
            if self.can_move_to(forward):
                pruned.append(forward)
            # check left and right for obstacles that create jump points
            for side in (-1, 1):
                beside_parent = Point(parent.x + side, parent.y)
                beside_node = Point(node.x + side, node.y)
                if not self.can_move_to(beside_parent) and self.can_move_to(beside_node):
                    pruned.append(beside_node)

        return pruned

    # JPS4 core: slide along a line until we hit something interesting
    def jps_jump(self, current, direction, goal):
        is_goal = goal if callable(goal) else (lambda point: point == goal)
        prev = current
        
        while True:
            step = Point(prev.x + direction.x, prev.y + direction.y)
            # wall? dead end.
            if not self.can_move_to(step):
                return None
            # found it!
            if is_goal(step):
                return step
            # horizontal: stop immediately (simple JPS4 rule)
            if direction.x != 0:
                return step
            # vertical: check if we just passed a corner
            for side in (-1, 1):
                beside_prev = Point(prev.x + side, prev.y)
                beside_step = Point(step.x + side, step.y)
                # found a forced neighbor! mark this as a jump point
                if not self.can_move_to(beside_prev) and self.can_move_to(beside_step):
                    return step
            prev = step

    # find the next set of nodes JPS should care about
    def jps_successors(self, parent, node, goal):
        # at the finish line?
        if goal(node):
            return [(node, 0)]

        # find where we're coming from so we know which way is "forward"
        if parent is None or parent == node:
            immediate_parent = None
        else:
            direction = parent.direction_to(node)
            immediate_parent = Point(node.x - direction.x, node.y - direction.y)

        successors = []
        # check pruned neighbors and jump from each
        for neighbor in self.jps_prune_neighbors(immediate_parent, node):
            direction = node.direction_to(neighbor)
            found = self.jps_jump(node, direction, goal)
            if found is not None:
                cost = STEP_COST * node.manhattan_distance(found)
                successors.append((found, cost))

        return successors

    # build the component map for fast reachability checks
    def generate_components(self):
        self.components = UnionFind(self.width * self.height)
        self.components_dirty = False
        
        # connect every empty cell to its neighbors
        for y in range(self.height):
            for x in range(self.width):
                if not self.grid[y][x]:  
                    idx = y * self.width + x
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < self.width and 0 <= ny < self.height and not self.grid[ny][nx]:
                            self.components.union(idx, ny * self.width + nx)

    # quick check: is the food even reachable?
    def reachable(self, start, end):
        if not (self.in_bounds(start.x, start.y) and self.in_bounds(end.x, end.y)):
            return False
        if self.grid[start.y][start.x] or self.grid[end.y][end.x]:
            return False
        if self.components_dirty:
            self.generate_components()
        # uses Union-Find to avoid expensive pathfinding on impossible maps
        return self.components.equiv(start.y * self.width + start.x,
                                     end.y * self.width + end.x)

    # main search logic - returns the key turning points
    def get_waypoints_single_goal(self, start, goal, mode="astar"):
        # reset metrics for the new run
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0

        # if it's right next to us, don't bother searching
        if start.manhattan_distance(goal) == 1:
            self.last_path_len = 2
            return [start, goal]

        # skip if Union-Find says it's impossible
        if not self.reachable(start, goal):
            return None

        # lambdas for the generic search loop
        goal_test = lambda point: point == goal
        heuristic = lambda point: int(self.heuristic(point, goal) * self.heuristic_factor)
        astar_successors = lambda parent, node: self.standard_astar_successors(node, goal_test)
        zero_heuristic = lambda point: 0  # Dijkstra doesn't guess

        started = time.perf_counter()

        # fire off the requested algorithm
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

        # save stats
        self.last_ms = (time.perf_counter() - started) * 1000.0
        self.last_expansions = self.context.expansions
        self.last_explored = list(self.context.last_expanded)

        if result is None:
            if mode == "jps4":
                PathingGrid._fallback_outer_hits += 1
            return None

        path, _cost = result
        return path

    # check if we can just walk in a straight line
    def find_direct_path(self, start, goal):
        if start == goal:
            return [start]
        if start.manhattan_distance(goal) == 1:
            return [start, goal]

        # horizontal straight line
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

        # vertical straight line
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

    # basic neighbor finder for A* and Dijkstra
    def standard_astar_successors(self, node, goal):
        if goal(node):
            return [(node, 0)]
        return [(neighbor, STEP_COST) for neighbor in self.neighborhood_points(node) if self.can_move_to(neighbor)]

    # get the full path (not just turning points)
    def get_path_single_goal(self, start, goal, mode="astar"):
        waypoints = self.get_waypoints_single_goal(start, goal, mode)
        if waypoints is None or len(waypoints) == 0:
            return None
        path = self.waypoints_to_path(waypoints)
        self.last_path_len = len(path) if path else 0
        if not self.validate_path(path):
            return None
        return path

    # fill in the squares between waypoints
    def waypoints_to_path(self, waypoints):
        if not waypoints:
            return []
        path = [waypoints[0]]
        for i in range(1, len(waypoints)):
            current = path[-1]
            target = waypoints[i]
            # step by step to the next turning point
            while current.manhattan_distance(target) > 0:
                direction = current.direction_to(target)
                current = current + direction
                path.append(current)
                if current.x == target.x and current.y == target.y:
                    break
        return path

    # make sure the path doesn't walk through walls
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
