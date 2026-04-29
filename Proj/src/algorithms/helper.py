import heapq


# 2D point with basic operations for grid navigation
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    # Add two points (vector addition)
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    # Check if two points are equal
    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    # Hash function for using Point as dictionary key
    def __hash__(self):
        return hash((self.x, self.y))

    # String representation for debugging
    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    # Manhattan distance (grid distance)
    def manhattan_distance(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    # Get 4-connected neighbors (up, right, down, left)
    def neumann_neighborhood(self):
        steps = [Point(0, -1), Point(1, 0), Point(0, 1), Point(-1, 0)]
        return [self + s for s in steps]

    # Get direction from this point to another (normalized to -1, 0, or 1)
    def direction_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        return Point(dx, dy)


# Union-Find (Disjoint Set) for fast connectivity checking
class UnionFind:
    def __init__(self, size):
        # Each element starts as its own parent
        self.parent = list(range(size))

    # Find root of element with path compression
    def find(self, item):
        while self.parent[item] != item:
            # Path compression: point directly to grandparent
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    # Union two sets by making one root point to the other
    def union(self, first, second):
        root_a = self.find(first)
        root_b = self.find(second)
        if root_a != root_b:
            self.parent[root_b] = root_a

    # Check if two elements are in the same set
    def equiv(self, first, second):
        return self.find(first) == self.find(second)


# Node in A* priority queue (fringe)
class SearchNode:
    def __init__(self, estimated_cost, cost, node, parent):
        self.estimated_cost = estimated_cost  # f = g + h (total estimated cost)
        self.cost = cost                    # g (actual cost from start)
        self.node = node                    # grid position
        self.parent = parent                # previous node in path

    # Priority queue ordering: lower estimated_cost is better
    # If equal, lower actual cost is better (tie-breaker)
    def __lt__(self, other):
        if self.estimated_cost == other.estimated_cost:
            return self.cost < other.cost
        return self.estimated_cost < other.estimated_cost


class AstarContext:
    # Shared A* search context used by all algorithms
    def __init__(self):
        self.fringe = []           # Priority queue of nodes to explore
        self.parents = {}          # Map node -> (parent, cost) for path reconstruction
        self.expansions = 0        # Count of nodes popped from queue (performance metric)
        self.last_expanded = []    # List of expanded nodes for visualization

    # Generic A* search that works with any successor function
    def astar_jps(self, start, successors, heuristic, success):
        # Reset search state
        self.fringe.clear()
        self.parents.clear()
        self.last_expanded.clear()
        self.expansions = 0
        
        # Initialize with start node
        self.parents[start] = (None, 0)
        heapq.heappush(self.fringe, SearchNode(heuristic(start), 0, start, None))

        # Main A* loop
        while self.fringe:
            # Get node with lowest estimated cost
            current = heapq.heappop(self.fringe)
            self.expansions += 1
            self.last_expanded.append((current.node.x, current.node.y))
            
            # Check if we reached the goal
            if success(current.node):
                # Reconstruct path by following parents backwards
                path = []
                node = current.node
                while node is not None:
                    path.append(node)
                    node = self.parents[node][0]
                path.reverse()
                return (path, current.cost)
            
            # Expand neighbors
            for neighbor, move_cost in successors(self.parents[current.node][0], current.node):
                new_cost = current.cost + move_cost
                # If we haven't seen this neighbor or found a better path
                if neighbor not in self.parents or self.parents[neighbor][1] > new_cost:
                    self.parents[neighbor] = (current.node, new_cost)
                    heapq.heappush(self.fringe, SearchNode(new_cost + heuristic(neighbor), new_cost, neighbor, current))
        
        # No path found
        return None
