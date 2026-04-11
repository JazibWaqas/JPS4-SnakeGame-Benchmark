import time
from typing import List, Tuple, Optional, Callable
from helper import Point, UnionFind, AstarContext

# Uniform movement cost (for cardinal moves)
C = 1

PATH_DEBUG = False


def _pd(*args, **kwargs):
    if PATH_DEBUG:
        print(*args, **kwargs)


class PathingGrid:
    def __init__(self, width: int, height: int, default_value: bool):
        self.width = width
        self.height = height
        self.grid: List[List[bool]] = [[default_value for _ in range(width)] for _ in range(height)]
        self.components = UnionFind(width * height)
        self.components_dirty = False
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

    # --- JPS4-specific methods ---
    def jps_prune_neighbors(self, parent: Optional[Point], node: Point) -> List[Point]:
        """
        Prune neighbors according to JPS4 (Horizontal-First Jump Point Search) rules.
        Returns a list of neighbors that should be considered for jumping.
        """
        # Without a parent, return all 4-connected neighbors that are not blocked
        if parent is None:
            return [n for n in node.neumann_neighborhood() if self.can_move_to(n)]
            
        # Get the direction from parent to current node
        direction = parent.direction_to(node)
        
        # Horizontal movement only allows horizontal continuation and forced neighbors
        # Vertical movement only allows vertical continuation and forced neighbors
        pruned = []
        
        # JPS4 always prioritizes horizontal movement first if possible 
        if direction.x != 0:  # We're moving horizontally
            # Continue in same horizontal direction
            next_horizontal = Point(node.x + direction.x, node.y)
            if self.can_move_to(next_horizontal):
                pruned.append(next_horizontal)
                
            # Check for forced neighbors in vertical directions
            for dy in [-1, 1]:
                # A neighbor is forced if the cell adjacent to parent is blocked
                # but the neighbor is not blocked
                adjacent_to_parent = Point(parent.x, parent.y + dy)
                candidate = Point(node.x, node.y + dy)
                if not self.can_move_to(adjacent_to_parent) and self.can_move_to(candidate):
                    pruned.append(candidate)
                    
        else:  # We're moving vertically
            # Continue in same vertical direction
            next_vertical = Point(node.x, node.y + direction.y)
            if self.can_move_to(next_vertical):
                pruned.append(next_vertical)
                
            # Check for forced neighbors in horizontal directions
            for dx in [-1, 1]:
                # A neighbor is forced if the cell adjacent to parent is blocked
                # but the neighbor is not blocked
                adjacent_to_parent = Point(parent.x + dx, parent.y)
                candidate = Point(node.x + dx, node.y)
                if not self.can_move_to(adjacent_to_parent) and self.can_move_to(candidate):
                    pruned.append(candidate)
                    
        return pruned

    def jps_jump_horizontal(self, start: Point, dx: int, goal: Callable) -> Optional[Point]:
        """Scan horizontally from start. Return the first jump point or None."""
        x, y = start.x + dx, start.y
        while True:
            if not self.can_move_to(Point(x, y)):
                return None
            p = Point(x, y)
            if goal(p):
                return p
            # Forced neighbor: obstacle above/below at previous x but open at current x
            prev_x = x - dx
            for dy in [-1, 1]:
                if not self.can_move_to(Point(prev_x, y + dy)) and self.can_move_to(Point(x, y + dy)):
                    return p
            x += dx

    def jps_jump_vertical(self, start: Point, dy: int, goal: Callable) -> Optional[Point]:
        """Scan vertically from start. At each row check horizontal jumps. Return jump point or None."""
        x, y = start.x, start.y + dy
        while True:
            if not self.can_move_to(Point(x, y)):
                return None
            p = Point(x, y)
            if goal(p):
                return p
            # Forced neighbor: obstacle left/right at previous y but open at current y
            prev_y = y - dy
            for dx in [-1, 1]:
                if not self.can_move_to(Point(x + dx, prev_y)) and self.can_move_to(Point(x + dx, y)):
                    return p
            # Recursive horizontal check: if a horizontal jump from here finds a jump point, this is a jump point
            for dx in [-1, 1]:
                if self.jps_jump_horizontal(p, dx, goal) is not None:
                    return p
            y += dy

    def jps_jump(self, current: Point, direction: Point, goal) -> Optional[Point]:
        if direction.x != 0 and direction.y == 0:
            return self.jps_jump_horizontal(current, direction.x, goal)
        if direction.y != 0 and direction.x == 0:
            return self.jps_jump_vertical(current, direction.y, goal)
        return None

    def jps_successors(self, parent: Optional[Point], node: Point, goal: Callable[[Point], bool]) -> List[Tuple[Point, int]]:
        """
        Generate successors according to JPS4 algorithm.
        
        Args:
            parent: The parent node (None for starting node)
            node: The current node
            goal: A function that returns True if a node is a goal
            
        Returns:
            List of (successor, cost) tuples
        """
        _pd(f"DEBUG: Finding successors for {node} with parent {parent}")
        successors = []
        
        # Special case: if this is the goal node, return it immediately
        if goal(node):
            _pd(f"DEBUG: Current node {node} is the goal")
            return [(node, 0)]
            
        # Check if we're adjacent to the goal - direct path is preferred
        for adj in node.neumann_neighborhood():
            if self.can_move_to(adj) and goal(adj):
                _pd(f"DEBUG: Found goal {adj} adjacent to {node}")
                return [(adj, C)]
        
        # Get pruned neighbors according to JPS4 rules
        pruned = self.jps_prune_neighbors(parent, node)
        _pd(f"DEBUG: Pruned neighbors for {node}: {pruned}")
        
        # For each pruned neighbor, try to jump
        for neighbor in pruned:
            # Calculate the direction from current node to neighbor
            direction = node.direction_to(neighbor)
            
            # Try to jump in that direction
            jump_result = self.jps_jump(node, direction, goal)
            
            # If we found a jump point, add it to successors
            if jump_result is not None:
                cost = C * node.manhattan_distance(jump_result)
                _pd(f"DEBUG: Jump from {node} found successor {jump_result} with cost {cost}")
                successors.append((jump_result, cost))
                
        # Fallback: if JPS pruning produced no successors, add all valid neighbors
        # This prevents dead-ends in areas where obstacles fully suppress jump points
        if not successors:
            for adj in node.neumann_neighborhood():
                if self.can_move_to(adj) and adj != parent:
                    successors.append((adj, C))
                    
        _pd(f"DEBUG: Final successors for {node}: {[s[0] for s in successors]}")
        return successors

    def can_potentially_reach_goal(self, node: Point, goal: Callable[[Point], bool]) -> bool:
        """Check if this node has potential to reach the goal (simple heuristic check)"""
        # Check a few sample points to see if the goal is potentially reachable
        to_visit = [node]
        visited = {node}
        depth = 0
        max_depth = 5  # Limit the depth to avoid excessive computation
        
        while to_visit and depth < max_depth:
            depth += 1
            next_to_visit = []
            for current in to_visit:
                if goal(current):
                    return True
                for neighbor in self.neighborhood_points(current):
                    if neighbor not in visited and self.can_move_to(neighbor):
                        visited.add(neighbor)
                        next_to_visit.append(neighbor)
            to_visit = next_to_visit
                
        return False

    def generate_components(self):
        """Reset and regenerate the UnionFind components to check connectivity between cells."""
        self.components = UnionFind(self.width * self.height)
        self.components_dirty = False
        
        # For each free cell, connect it to its free neighbors
        for y in range(self.height):
            for x in range(self.width):
                if not self.grid[y][x]:  # If this cell is free
                    idx = y * self.width + x
                    # Check all 4-connected neighbors
                    for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
                        if 0 <= nx < self.width and 0 <= ny < self.height and not self.grid[ny][nx]:
                            nidx = ny * self.width + nx
                            self.components.union(idx, nidx)
        
        # Print debug information about connectivity
        _pd("DEBUG: Updated UnionFind components for connectivity")

    def reachable(self, start: Point, end: Point) -> bool:
        """
        Check if there is a path from start to end using the UnionFind connectivity components.
        
        Args:
            start: The starting point
            end: The ending point
            
        Returns:
            bool: True if there's a path, False otherwise
        """
        # First check if both points are in bounds and not blocked
        if not (self.in_bounds(start.x, start.y) and self.in_bounds(end.x, end.y)):
            return False
            
        if self.grid[start.y][start.x] or self.grid[end.y][end.x]:
            return False
            
        # If the components are dirty, regenerate them
        if self.components_dirty:
            self.generate_components()
            
        # Check if start and end are in the same connected component
        start_idx = start.y * self.width + start.x
        end_idx = end.y * self.width + end.x
        
        are_connected = self.components.equiv(start_idx, end_idx)
        _pd(f"DEBUG: Testing reachability from {start} to {end}: {are_connected}")
        return are_connected

    def get_waypoints_single_goal(self, start: Point, goal: Point, mode: str = "astar") -> List[Point]:
        """Find a path from start to goal using the specified algorithm."""
        self.last_ms = 0.0
        self.last_expansions = 0
        self.last_path_len = 0

        _pd("\nDEBUG: Printing Path Grid (X=blocked, .=free):")
        for row in range(self.height):
            _pd("".join("X" if self.grid[row][col] else "." for col in range(self.width)))
        _pd(f"DEBUG: Searching path from {start} to {goal} (approx={mode})")
        
        if not self.reachable(start, goal):
            _pd("DEBUG: Not reachable (UnionFind check)!")
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
            exp_sum += self.context.expansions
        elif mode == "dijkstra":
            result = self.context.astar_jps(start, succ_astar, h0, goal_test)
            exp_sum += self.context.expansions
        else:
            result = self.context.astar_jps(start, succ_astar, heuristic, goal_test)
            exp_sum += self.context.expansions
        
        if result is None and mode == "jps4":
            _pd("DEBUG: JPS4 failed, falling back to standard A*")
            result = self.context.astar_jps(
                start,
                lambda p, n: self.standard_astar_successors(n, goal_test),
                heuristic,
                goal_test
            )
            exp_sum += self.context.expansions
            
        self.last_ms = (time.perf_counter() - t0) * 1000.0
        self.last_expansions = exp_sum

        if result is None:
            _pd("DEBUG: No path found!")
            return None
            
        (waypoints, cost) = result
        _pd(f"DEBUG: Raw waypoints: {waypoints}")

        # Ensure goal is included
        if waypoints and waypoints[-1] != goal:
            waypoints.append(goal)

        # Expand jump-point waypoints into a fully adjacent path
        path = self.waypoints_to_path(waypoints)
        _pd(f"DEBUG: Expanded path: {path}")

        if not self.validate_path(path):
            _pd("DEBUG: Path validation failed after expansion")
            return None

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
    
    def post_process_path(self, path: List[Point]) -> List[Point]:
        """
        Post-process the path to find a more optimal route while maintaining adjacency.
        Uses a combination of line-of-sight checks and path smoothing.
        """
        if len(path) <= 2:
            return path
            
        # Create a new optimized path starting with the first point
        optimized = [path[0]]
        current_idx = 0
        
        while current_idx < len(path) - 1:
            current = optimized[-1]
            
            # Try to find the furthest point in the path that has a direct line of sight
            furthest_idx = current_idx + 1
            for i in range(len(path) - 1, current_idx, -1):
                direct_path = self.find_direct_path(current, path[i])
                if direct_path:
                    furthest_idx = i
                    break
            
            # If we found a furthest visible point
            if furthest_idx > current_idx + 1:
                # Add the direct path (skipping the current point which is already added)
                direct_path = self.find_direct_path(current, path[furthest_idx])
                if direct_path:
                    optimized.extend(direct_path[1:])  # Skip the first point as it's already in the path
                current_idx = furthest_idx
            else:
                # Just add the next point
                optimized.append(path[current_idx + 1])
                current_idx += 1
        
        return optimized

    def standard_astar_successors(self, node: Point, goal: Callable[[Point], bool]) -> List[Tuple[Point, int]]:
        """Standard A* successor function that returns all valid neighbors."""
        successors = []
        
        # If this is the goal node, return it immediately
        if goal(node):
            return [(node, 0)]
            
        # Return all valid neighbors
        for neighbor in self.neighborhood_points(node):
            if self.can_move_to(neighbor):
                successors.append((neighbor, C))
                
        return successors

    def get_path_single_goal(self, start: Point, goal: Point, mode: str = "astar") -> Optional[List[Point]]:
        waypoints = self.get_waypoints_single_goal(start, goal, mode)
        if waypoints is None or len(waypoints) == 0:
            return None
            
        self.last_path_len = len(waypoints) if waypoints else 0
        return waypoints

    def waypoints_to_path(self, waypoints: List[Point]) -> List[Point]:
        """Convert waypoints to a path where each step is adjacent (4-connected) to the previous."""
        if not waypoints:
            return []

        path = [waypoints[0]]

        for i in range(1, len(waypoints)):
            current = path[-1]
            target = waypoints[i]
            # Walk one axis at a time to stay 4-connected (never diagonal)
            # Horizontal first, then vertical
            while current.x != target.x:
                step = 1 if target.x > current.x else -1
                current = Point(current.x + step, current.y)
                path.append(current)
            while current.y != target.y:
                step = 1 if target.y > current.y else -1
                current = Point(current.x, current.y + step)
                path.append(current)

        return path

    def optimize_path(self, path: List[Point]) -> List[Point]:
        """
        Optimize the path by removing unnecessary waypoints while ensuring all steps are adjacent.
        
        Args:
            path: List of Points representing the path
            
        Returns:
            List[Point]: Optimized path where each point is adjacent to the previous point
        """
        # Just delegate to the new post_process_path method
        return self.post_process_path(path)

    def validate_optimized_path(self, path: List[Point]) -> bool:
        """Verify that an optimized path has only adjacent steps."""
        if not path or len(path) < 2:
            return True
            
        for i in range(len(path) - 1):
            if path[i].manhattan_distance(path[i+1]) > 1:
                return False
                
        return True

    def validate_path(self, path: List[Point]) -> bool:
        """Verify that a path has only adjacent steps and all points are valid."""
        if not path or len(path) < 2:
            return True
            
        for i in range(len(path) - 1):
            # Check adjacency
            if path[i].manhattan_distance(path[i+1]) > 1:
                _pd(f"DEBUG: Non-adjacent points in path: {path[i]} -> {path[i+1]}")
                return False
                
            # Check that both points are valid (in bounds and not blocked)
            for p in [path[i], path[i+1]]:
                if not self.in_bounds(p.x, p.y) or self.grid[p.y][p.x]:
                    _pd(f"DEBUG: Invalid point in path: {p}")
                    return False
                    
        return True
