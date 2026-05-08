import heapq
from entities.ghost import Ghost

"""Dijkstra's algorithm pathfinding ghost implementation."""

class DijkstraGhost(Ghost):
    """Ghost that approaches Pacman from behind using Dijkstra's algorithm.

    In Game.update this ghost targets a position 2 tiles behind Pacman,
    making it attempt to cut off escape routes from the rear.

    A small turn penalty (+1 cost for changing direction) is applied so the
    ghost prefers to maintain its current heading rather than zig-zag, which
    produces smoother movement. Because all base edge costs are 1, the
    algorithm degenerates to BFS when the ghost is travelling straight.

    Data structures:
        priority_queue (heapq min-heap): Nodes ordered by cumulative cost.
        dist      (dict): Best known cost from start to each node.
        came_from (dict): Maps each node to (parent_node, direction).
        closed_set (set): Nodes whose optimal cost has been finalised.
    """

    def get_path(self, game_map, target_c, target_r):
        """Return the first step of the least-cost path to (target_c, target_r).

        Applies a turn penalty of +1 whenever the chosen direction differs
        from the previous step's direction, favouring straight movement.
        Reconstructs the path via came_from and returns only the immediate
        next direction. Falls back to random_move if no path is found.
        """
        start = (self.c, self.r)
        goal = (target_c, target_r)
        if start == goal:
            return self.random_move(game_map)
        
        priority_queue = [(0, start)]
        dist = {start : 0}
        came_from = {}    # node -> (parent, direction)
        closed_set = set()

        while priority_queue:
            cost, current = heapq.heappop(priority_queue)
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
            
            prev_dir = came_from[current][1] if current in came_from else None
            for neighbor, direction in self.get_neighbors(current[0], current[1], game_map):
                if neighbor in closed_set:
                    continue
                turn_penalty = 0 if direction == prev_dir else 1
                new_cost = cost + 1 + turn_penalty
                if neighbor not in dist or new_cost < dist[neighbor]:
                    dist[neighbor] = new_cost
                    heapq.heappush(priority_queue, (new_cost, neighbor))
                    came_from[neighbor] = (current, direction)
                    
        return self.random_move(game_map)