import collections
from entities.ghost import Ghost

"""Breadth-First Search pathfinding ghost implementation."""

class BFSGhost(Ghost):
    """Ghost that chases Pacman using Breadth-First Search.

    BFS explores tiles in order of increasing hop count, guaranteeing the
    path with the fewest steps on an unweighted grid. It is complete and
    optimal for uniform-cost movement, though it may explore more nodes
    than A* because it has no heuristic to guide it.

    Data structures:
        queue    (collections.deque): FIFO frontier of nodes to expand.
        visited  (set): Nodes already added to the queue (prevents re-visits).
        came_from (dict): Maps each node to (parent_node, direction) for
                          path reconstruction.
    """
    def get_path(self, game_map, target_c, target_r):
        """Return the first step of the shortest path to (target_c, target_r) via BFS.

        Reconstructs the path via came_from and returns only the direction
        of the immediate next step from the current tile.
        Falls back to random_move if start equals goal or no path is found.
        """
        start = (self.c, self.r)
        goal = (target_c, target_r)
        if start == goal:
            self.random_move(game_map)

        queue = collections.deque([start])
        visited = {start}
        came_from = {}     # node -> (parent, direction)

        while queue:
            current = queue.popleft()
            if current == goal:
                node = current
                while came_from.get(node, (None, ))[0] != start and came_from.get(node) is not None:
                    node = came_from[node][0]
                if node in came_from:
                    return came_from[node][1]
                return self.random_move(game_map)
            for neighbor, direction in self.get_neighbors(current[0], current[1], game_map):
                if neighbor not in visited:
                    visited.add(neighbor)
                    came_from[neighbor] = (current, direction)
                    queue.append(neighbor)
        return self.random_move(game_map)
    