# Literature Review: Dijkstra, A*, JPS, and JPS4

## Scope

This project compares shortest-path algorithms on uniform-cost 4-connected grid maps:

- `Dijkstra` as the uninformed optimal baseline
- `A*` as the heuristic optimal baseline
- `JPS4` as a symmetry-pruning optimization specialized for 4-connected grids

The most relevant primary sources for this project are:

1. Dijkstra (1959): "A Note on Two Problems in Connection with Graphs"
   https://doi.org/10.1007/BF01386390
2. Hart, Nilsson, Raphael (1968): "A Formal Basis for the Heuristic Determination of Minimum Cost Paths"
   https://ieeexplore.ieee.org/document/4082128/
3. Harabor and Grastien (2011): "Online Graph Pruning for Pathfinding on Grid Maps"
   https://harabor.net/data/papers/harabor-grastien-aaai11.pdf
4. Baum (2025): "Jump Point Search Pathfinding in 4-connected Grids"
   https://arxiv.org/abs/2501.14816

## What Each Paper Contributes

### Dijkstra (1959)

Dijkstra gives the baseline shortest-path method for non-negative edge costs. In a uniform-cost grid, it expands outward in increasing distance from the start. It is guaranteed to find an optimal path, but because it has no goal direction, it tends to explore a large part of the reachable region before finishing.

Why it matters here:

- It is the clean correctness baseline.
- On a grid with unit costs, it acts like uninformed wavefront expansion.
- It gives a useful upper bound for expansions among the three algorithms in this repo.

### A* (1968)

Hart, Nilsson, and Raphael add a heuristic estimate to best-first search. With an admissible heuristic, A* still returns an optimal path while usually expanding fewer nodes than Dijkstra.

For 4-connected uniform-cost grids, Manhattan distance is the standard admissible heuristic:

- `h(n) = |x_n - x_goal| + |y_n - y_goal|`

Why it matters here:

- It is the standard optimal practical baseline.
- It should dominate Dijkstra on most goal-directed queries.
- JPS4 in this project is best understood as an optimization of A*, not a replacement for optimal graph search in general.

### Harabor and Grastien (2011): Original JPS

Harabor and Grastien introduce Jump Point Search for uniform-cost grid maps. The central idea is that many shortest grid paths are symmetric: the search does redundant work by enumerating equivalent intermediate nodes. JPS prunes dominated neighbors and "jumps" along straight-line movement until it reaches a jump point, obstacle, or the goal.

Important takeaways:

- JPS preserves optimality on the grid classes it targets.
- It is strongest when there is lots of empty space or repeated local symmetry.
- It is an online pruning method: it does not require an expensive preprocessing stage.

This original paper is mainly for 8-connected grids, so it is conceptually important but not directly identical to this repo's `JPS4`.

### Baum (2025): JPS4

Baum adapts Jump Point Search to 4-connected uniform-cost grids. The key change is a 4-direction canonical ordering and a different pruning/jump rule set than classical JPS8.

The main ideas used by this project are:

- horizontal-first canonical ordering
- horizontal moves do not prune neighbors
- vertical moves keep the forward natural neighbor and may add forced neighbors around obstacles
- jump points reset the canonical ordering when obstacles would otherwise hide relevant parts of the search space

Baum's paper also makes an important practical claim: `JPS4` is not always the fastest option. In the paper's benchmark summary, JPS4 tends to beat A* in denser, more obstacle-structured maps, while A* can still be better on open maps.

That matches the right interpretation for this project: JPS4 is a specialized optimization, not a universal winner.

## Practical Interpretation for This Repo

### When JPS4 makes sense

Use `JPS4` when:

- the world is a 4-connected grid
- all step costs are equal
- you need optimal shortest paths
- you want online search without preprocessing
- the map has enough obstacle structure or path symmetry for pruning to help

Typical examples:

- tile-based games with cardinal movement only
- warehouse-like indoor navigation on a discrete occupancy grid
- repeated path queries on changing maps where heavy preprocessing is undesirable

### When A* is usually the better default

Use `A*` when:

- the map is open enough that JPS4's extra successor logic may not pay off
- you want the simplest optimal informed baseline
- you want a method that generalizes more easily to weighted grids or variants

### When Dijkstra is still useful

Use `Dijkstra` when:

- you need an uninformed correctness baseline
- you are teaching or visualizing how heuristic search helps
- you want to validate that a heuristic method still returns the same shortest path length

## What JPS4 Is Not For

JPS4 is not a general answer for every pathfinding problem. It is a strong fit only under specific assumptions.

It is a poor fit when:

- movement is not restricted to 4 directions
- edge costs are weighted or non-uniform
- any-angle paths are needed
- the problem is multi-agent pathfinding
- you need incremental replanning methods such as D* Lite

In those settings, plain A* variants, any-angle planners, or incremental planners are often more appropriate.

## Implications for the Snake Demo

The Snake game is a good visualization tool for the pathfinder, but the complete game behavior is not just "run JPS4." A playable snake also needs recovery behavior for moments when the current food is temporarily or permanently unreachable. That is a game-control problem layered on top of pathfinding.

So the repo should treat these as separate concerns:

- `pathing_grid.py`: shortest-path correctness and efficiency
- `snake_game_jps4.py`: how to use those paths robustly inside a live game loop

That distinction matters because a snake can get stuck in a movement loop even if the pathfinder itself is perfectly correct.
