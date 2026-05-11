import heapq
from entities.ghost import Ghost

"""A* pathfinding ghost implementation."""

class AStarGhost(Ghost):
    """Ghost that chases Pacman using the A* search algorithm.
    A* combines the actual path cost g(n) with a heuristic estimate h(n)
    to focus the search toward the goal.
    Data structures:
        open_set  (heapq min-heap): Nodes ordered by f = g + h.
        g_score   (dict): Best known cost from start to each visited node.
        came_from (dict): Maps each node to (parent_node, direction) for
                          path reconstruction.
        closed_set (set): Nodes whose optimal cost is confirmed.

    Heuristic:
        Manhattan distance |nc - target_c| + |nr - target_r|, which is
        admissible on a grid where diagonal movement is not allowed.
    """
    def get_path(self, game_map, target_c, target_r):
        """Return the first step of the A*-optimal path to (target_c, target_r).
        Reconstructs the full path via came_from and returns only the
        direction of the first step from the starting tile.
        Falls back to random_move if start equals goal or no path exists.
        """
        start = (self.c, self.r)
        goal = (target_c, target_r)
        if start == goal:
            return self.random_move(game_map)
    
        open_set = []
        heapq.heappush(open_set, (0, 0, start))  # (f_score, g_score, node)

        g_score = {start: 0}
        came_from = {}   # node -> (parent_node, direction)
        closed_set = set()

        while open_set:
            f, g, current = heapq.heappop(open_set)

            if current in closed_set:
                continue
            closed_set.add(current)

            if current == goal:
                node = current
                while came_from.get(node, (None, ))[0] != start and came_from.get(node) is not None:
                    node = came_from[node][0]
                if node in came_from:
                    return came_from[node][1]
                return self.random_move(game_map)

            for neighbor, direction in self.get_neighbors(current[0], current[1], game_map):
                if neighbor in closed_set:
                    continue
                next_g = g + 1
                if neighbor not in g_score or next_g < g_score[neighbor]:
                    g_score[neighbor] = next_g
                    came_from[neighbor] = (current, direction)
                    h = abs(neighbor[0] - target_c) + abs(neighbor[1] - target_r)
                    heapq.heappush(open_set, (h + g_score[neighbor], g_score[neighbor], neighbor))
                
        return self.random_move(game_map)
 


        
