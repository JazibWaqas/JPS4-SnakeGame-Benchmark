import heapq


# just a basic (x, y) point on the grid
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    # move the point (vector addition)
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    # are we at the same spot?
    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    # needs to be hashable to work as a dictionary key
    def __hash__(self):
        return hash((self.x, self.y))

    # helpful for debugging
    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    # distance counting squares (up/down/left/right)
    def manhattan_distance(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    # get the 4 neighboring squares
    def neumann_neighborhood(self):
        steps = [Point(0, -1), Point(1, 0), Point(0, 1), Point(-1, 0)]
        return [self + s for s in steps]

    # normalize direction to -1, 0, or 1
    def direction_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)
        return Point(dx, dy)


# Union-Find for super fast connectivity checks
class UnionFind:
    def __init__(self, size):
        # everyone starts as their own boss
        self.parent = list(range(size))

    # find the root of the set with path compression
    def find(self, item):
        while self.parent[item] != item:
            # point to the grandparent to shorten the tree
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    # merge two sets together
    def union(self, first, second):
        root_a = self.find(first)
        root_b = self.find(second)
        if root_a != root_b:
            self.parent[root_b] = root_a

    # check if two things are in the same set
    def equiv(self, first, second):
        return self.find(first) == self.find(second)


# container for nodes in the priority queue
class SearchNode:
    def __init__(self, estimated_cost, cost, node, parent):
        self.estimated_cost = estimated_cost  # total cost (f = g + h)
        self.cost = cost                    # actual steps taken (g)
        self.node = node                    # current position
        self.parent = parent                # how we got here

    # smaller estimated cost comes first in the heap
    def __lt__(self, other):
        if self.estimated_cost == other.estimated_cost:
            return self.cost < other.cost
        return self.estimated_cost < other.estimated_cost


class AstarContext:
    # keeps track of the search state
    def __init__(self):
        self.fringe = []           # priority queue (the "to-do" list)
        self.parents = {}          # node -> (parent, cost) map
        self.expansions = 0        # how many nodes we popped
        self.last_expanded = []    # list of checked points for the UI

    # generic search loop that runs Dijkstra, A*, and JPS4
    def astar_jps(self, start, successors, heuristic, success):
        # clear out old state before starting
        self.fringe.clear()
        self.parents.clear()
        self.last_expanded.clear()
        self.expansions = 0
        
        # start at the beginning
        self.parents[start] = (None, 0)
        heapq.heappush(self.fringe, SearchNode(heuristic(start), 0, start, None))

        # keep going until we run out of options
        while self.fringe:
            # pick the most promising node
            current = heapq.heappop(self.fringe)
            self.expansions += 1
            self.last_expanded.append((current.node.x, current.node.y))
            
            # reached the goal!
            if success(current.node):
                # reconstruct the path by walking backwards
                path = []
                node = current.node
                while node is not None:
                    path.append(node)
                    node = self.parents[node][0]
                path.reverse()
                return (path, current.cost)
            
            # look at the next set of nodes
            for neighbor, move_cost in successors(self.parents[current.node][0], current.node):
                new_cost = current.cost + move_cost
                # only update if we found a better/shorter path
                if neighbor not in self.parents or self.parents[neighbor][1] > new_cost:
                    self.parents[neighbor] = (current.node, new_cost)
                    # push it onto the queue with its estimated cost
                    heapq.heappush(self.fringe, SearchNode(new_cost + heuristic(neighbor), new_cost, neighbor, current))
        
        # no path found (dead end)
        return None
