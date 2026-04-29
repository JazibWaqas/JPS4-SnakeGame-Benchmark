import heapq


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    def manhattan_distance(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def neumann_neighborhood(self):
        steps = [Point(0, -1), Point(1, 0), Point(0, 1), Point(-1, 0)]
        return [self + s for s in steps]

    def direction_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        return Point(dx, dy)


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))

    def find(self, item):
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, first, second):
        root_a = self.find(first)
        root_b = self.find(second)
        if root_a != root_b:
            self.parent[root_b] = root_a

    def equiv(self, first, second):
        return self.find(first) == self.find(second)


class SearchNode:
    def __init__(self, estimated_cost, cost, node, parent):
        self.estimated_cost = estimated_cost
        self.cost = cost
        self.node = node
        self.parent = parent

    def __lt__(self, other):
        if self.estimated_cost == other.estimated_cost:
            return self.cost < other.cost
        return self.estimated_cost < other.estimated_cost


class AstarContext:
    def __init__(self):
        self.fringe = []
        self.parents = {}
        self.expansions = 0
        self.last_expanded = []   # (x, y) of every node popped — used for demo visualisation

    def astar_jps(self, start, successors, heuristic, success):
        self.fringe.clear()
        self.parents.clear()
        self.last_expanded.clear()
        self.expansions = 0
        self.parents[start] = (None, 0)
        heapq.heappush(self.fringe, SearchNode(heuristic(start), 0, start, None))

        while self.fringe:
            current = heapq.heappop(self.fringe)
            self.expansions += 1
            self.last_expanded.append((current.node.x, current.node.y))
            if success(current.node):
                path = []
                node = current.node
                while node is not None:
                    path.append(node)
                    node = self.parents[node][0]
                path.reverse()
                return (path, current.cost)
            for neighbor, move_cost in successors(self.parents[current.node][0], current.node):
                new_cost = current.cost + move_cost
                if neighbor not in self.parents or self.parents[neighbor][1] > new_cost:
                    self.parents[neighbor] = (current.node, new_cost)
                    heapq.heappush(self.fringe, SearchNode(new_cost + heuristic(neighbor), new_cost, neighbor, current.node))
        return None
