import random
from entities.ghost import Ghost

"""Depth-First Search pathfinding ghost implementation."""

class DFSGhost(Ghost):
    """Ghost that chases Pacman using a randomised Depth-First Search.

    DFS explores as far as possible along one branch before backtracking,
    which does not guarantee the shortest path. Shuffling the neighbour
    list before each push randomises the traversal order, making the
    ghost's route unpredictable and hard to avoid even though it may
    take long detours. In Game.update this ghost also retreats to a
    corner when Pacman is within 8 tiles, adding a hide-and-ambush pattern.

    Data structures:
        stack    (list used as LIFO): Nodes to expand next.
        visited  (set): Nodes already pushed (prevents cycles).
        came_from (dict): Maps each node to (parent_node, direction).
    """

    def get_path(self, game_map, target_c, target_r):
        """Return the first step toward (target_c, target_r) via randomised DFS.

        Neighbours are shuffled with random.shuffle before being pushed onto
        the stack, so the path varies between calls even for identical inputs.
        Reconstructs the path via came_from once the goal is reached.
        Falls back to random_move if start equals goal or no path is found.
        """
        start = (self.c, self.r)
        goal = (target_c, target_r)
        if start == goal:
            return self.random_move(game_map)
        
        stack = [start]
        visited = {start}
        came_from = {}
        
        while stack:
            current = stack.pop()
            if current == goal:
                node = current
                while came_from.get(node, (None, ))[0] != start and came_from.get(node) is not None:
                    node = came_from[node][0]
                if node in came_from:
                    return came_from[node][1]
                return self.random_move(game_map)
            neighbors = self.get_neighbors(current[0], current[1], game_map)
            random.shuffle(neighbors)
            for neighbor, direction in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    came_from[neighbor] = (current, direction)
                    stack.append(neighbor)
        return self.random_move(game_map)

                