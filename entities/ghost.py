import random
import collections
import pygame
from core.constants import *
from core.entity import Entity
import systems.player_state as ps
import math

"""Ghost entity with three behavioural states and pluggable pathfinding."""

class Ghost(Entity):
    """Represents one ghost with frightened, dead, and normal AI states.

    Subclasses override get_path() to implement different search algorithms.
    The base class handles state transitions, speed selection, and rendering;
    subclasses only need to provide pathfinding logic.

    State machine:
        normal     → is_frightened=False, is_dead=False  (chases Pacman via get_path)
        frightened → is_frightened=True,  is_dead=False  (wanders randomly at low speed)
        dead       → is_dead=True                        (rushes home via bfs_to_home at speed 3.5;
                                                           reverts to normal on arrival)

    Attributes:
        color (tuple[int,int,int]): Body colour in normal state.
        is_frightened (bool): Set True when Pacman eats a power pellet;
            cleared when frightened_timer reaches zero or ghost is eaten.
        is_dead (bool): Set True when Pacman eats this ghost while frightened;
            cleared automatically when the ghost reaches its spawn tile.
        start_c (int): Spawn column; doubles as the home target for bfs_to_home.
        start_r (int): Spawn row.
    """

    def __init__(self, c, r, color):
        super().__init__(c, r, speed=2)
        self.color         = color
        self.is_frightened = False
        self.is_dead       = False 
        self.start_c       = c    
        self.start_r       = r
    
    def update(self, game_map, target_c, target_r, frightened_timer):
        """Advance the ghost by one frame.

        Speed selection:
            is_dead      → 3.5 px/frame (always, regardless of equipment)
            is_frightened → 0.5 if ICE sword equipped, else 1.0
            normal        → self.speed (set by Game based on level)

        Direction is only re-evaluated when the ghost reaches a tile center.
        The chosen (dx, dy) is applied only if the resulting cell is not a wall;
        otherwise the ghost continues in its current direction, or picks a random
        valid direction if it has stopped completely.

        Args:
            game_map (Map): Used for wall checks and neighbor queries.
            target_c (int): Target column (Pacman or strategic position).
            target_r (int): Target row.
            frightened_timer (int): Remaining frightened frames (unused here,
                passed through from Game for subclass use if needed).
        """
        
        if self.is_dead:
            current_speed = 3.5
        elif self.is_frightened:
            current_speed = 0.5 if ps.equipped_weapon == "ICE" else 1.0
        else:
            current_speed = self.speed
 
        if self.is_at_center(current_speed):
            self.snap_to_center()
            self.c = int(self.x) // TILE_SIZE
            self.r = int(self.y) // TILE_SIZE

            if self.is_dead:
                if self.c == self.start_c and self.r == self.start_r:
                    self.is_dead = False
                dx, dy = self.bfs_to_home(game_map)
            elif self.is_frightened:
                dx, dy = self.random_move(game_map)
            else:
                dx, dy = self.get_path(game_map, target_c, target_r)
 
            nc, nr = self.c + dx, self.r + dy
            if nc < 0: nc = MAP_COLS - 1
            elif nc >= MAP_COLS: nc = 0
            
            if not game_map.is_wall(nc, nr):
                self.dir_x, self.dir_y = dx, dy
            elif self.dir_x == 0 and self.dir_y == 0:
                self.dir_x, self.dir_y = self.random_move(game_map)

        self.x += self.dir_x * current_speed
        self.y += self.dir_y * current_speed
        self.wrap_around()

    def bfs_to_home(self, game_map):
        """Compute the shortest path from the current tile to the spawn tile using BFS.

        Unlike get_neighbors (which forbids U-turns), this search considers all
        four cardinal directions at every step, so the ghost always takes the
        geometrically shortest route even if that means reversing direction.

        Returns (0, 0) when the ghost is already at the spawn tile or no path exists.

        Args:
            game_map (Map): Used to check walls.

        Returns:
            tuple[int,int]: (dx, dy) direction to move this frame.
        """
        start = (self.c, self.r)
        goal  = (self.start_c, self.start_r)
        if start == goal:
            return (0, 0)

        queue    = collections.deque([start])
        visited  = {start}
        came_from = {}       # node -> (parent_node, direction)

        while queue:
            current = queue.popleft()
            if current == goal:
                node = current
                while came_from.get(node, (None,))[0] != start and came_from.get(node) is not None:
                    node = came_from[node][0]
                return came_from[node][1] if node in came_from else (0, 0)

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nc, nr = current[0] + dx, current[1] + dy
                if nc < 0: nc = MAP_COLS - 1
                elif nc >= MAP_COLS: nc = 0
                neighbor = (nc, nr)
                if neighbor not in visited and not game_map.is_wall(nc, nr):
                    visited.add(neighbor)
                    came_from[neighbor] = (current, (dx, dy))
                    queue.append(neighbor)

        return (0, 0)
    
    def get_neighbors(self, c, r, game_map):
        """Return reachable neighbours of (c, r), preferring forward movement.

        Primary pass: excludes the reverse of the current direction to prevent
        unnecessary U-turns during normal play.
        Fallback pass: if the primary pass yields no results (dead end), all
        four directions are considered regardless of the current heading.

        Handles horizontal wrap-around for tunnel tiles at column edges.

        Args:
            c (int): Column to expand from.
            r (int): Row to expand from.
            game_map (Map): Used to check walls.

        Returns:
            list[tuple[tuple[int,int], tuple[int,int]]]:
                Each element is ((nc, nr), (dx, dy)) where (nc, nr) is the
                neighbour position and (dx, dy) is the direction to reach it.
        """
        neighbors = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nc, nr = c + dx, r + dy
            if nc < 0: nc = MAP_COLS - 1
            elif nc >= MAP_COLS: nc = 0

            if not game_map.is_wall(nc, nr):
                if (dx, dy) != (-self.dir_x, -self.dir_y) or (self.dir_x == 0 and self.dir_y == 0):
                    neighbors.append(((nc, nr), (dx, dy)))
            
        if not neighbors:
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nc, nr = c + dx, r + dy
                if nc < 0: nc = MAP_COLS - 1
                elif nc >= MAP_COLS: nc = 0
                if not game_map.is_wall(nc, nr):
                    neighbors.append(((nc, nr), (dx, dy)))
        return neighbors
    
    def random_move(self, game_map):
        """Choose a uniformly random valid direction from the current tile.

        Uses get_neighbors (so U-turns are still avoided when possible).
        Falls back to the current direction if no neighbours are available.
        """
        moves = [d for _, d in self.get_neighbors(self.c, self.r, game_map)]
        return random.choice(moves) if moves else (self.dir_x, self.dir_y)
    
    def get_path(self, game_map, target_c, target_r):
        """Return the next direction toward (target_c, target_r).
        Base implementation is a random move; subclasses replace this with
        A*, BFS, Dijkstra, or DFS logic.
        """
        return self.random_move(game_map)
    
    def draw(self, surface, frightened_timer):
        """Render the ghost sprite appropriate to its current state.

        Dead state:
            Draws two floating eyes (white ellipses with blue pupils that
            shift in the direction of travel). No body is drawn.

        Frightened state:
            Solid blue body. Flashes between SCARED_COLOR and SCARED_FLASH
            when fewer than 120 frames remain on the frightened timer.
            Sad-face eye dots and a downward arc mouth.

        Normal state:
            Coloured body with a soft glow ring, bright arc highlight on the
            dome, an animated wave skirt, and directional pupils.
        """
        r  = TILE_SIZE // 2 - 2
        x, y = int(self.x), int(self.y)

        if getattr(self, 'is_dead', False):
            px_off = self.dir_x * 2
            py_off = self.dir_y * 2
            pygame.draw.ellipse(surface, WHITE, (x - 8, y - 8, 6, 8))
            pygame.draw.ellipse(surface, WHITE, (x + 2, y - 8, 6, 8))
            pygame.draw.circle(surface, (0, 0, 180), (x - 5 + px_off, y - 4 + py_off), 3)
            pygame.draw.circle(surface, (0, 0, 180), (x + 5 + px_off, y - 4 + py_off), 3)
            pygame.draw.circle(surface, WHITE, (x - 4 + px_off, y - 5 + py_off), 1)
            pygame.draw.circle(surface, WHITE, (x + 6 + px_off, y - 5 + py_off), 1)
            return

        if self.is_frightened:
            draw_color = SCARED_FLASH if (frightened_timer < 120 and (frightened_timer // 15) % 2 == 0) else SCARED_COLOR
        else:
            draw_color = self.color

        if not self.is_frightened:
            glow = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
            glow_c = (draw_color[0], draw_color[1], draw_color[2], 40)
            pygame.draw.circle(glow, glow_c, (r*2, r*2), r*2)
            surface.blit(glow, (x - r*2, y - r*2 - 2))

        pygame.draw.circle(surface, draw_color, (x, y - 2), r)
        pygame.draw.rect(surface, draw_color, (x - r, y - 2, r * 2, r + 2))

        lighter = tuple(min(255, ch + 70) for ch in draw_color)
        pygame.draw.arc(surface, lighter,
                        pygame.Rect(x - r, y - 2 - r, r*2, r*2),
                        0, math.pi, 2)

        wave_t = pygame.time.get_ticks() / 300.0
        seg_w = (r * 2) / 4
        for i in range(4):
            sx = x - r + i * seg_w
            wave = math.sin(wave_t + i * 1.0) * 2
            pts = [
                (sx, y + r),
                (sx + seg_w / 2, y + r - 4 + wave),
                (sx + seg_w, y + r),
                (sx + seg_w, y),
                (sx, y),
            ]
            pygame.draw.polygon(surface, draw_color, pts)

        if self.is_frightened:
            pygame.draw.circle(surface, WHITE, (x - 4, y - 3), 3)
            pygame.draw.circle(surface, WHITE, (x + 4, y - 3), 3)
            pygame.draw.arc(surface, WHITE,
                            pygame.Rect(x - 6, y + 1, 12, 6), math.pi, 2*math.pi, 2)
        else:
            pygame.draw.ellipse(surface, WHITE, (x - 8, y - 8, 6, 8))
            pygame.draw.ellipse(surface, WHITE, (x + 2, y - 8, 6, 8))
            px_off = self.dir_x * 2
            py_off = self.dir_y * 2
            pygame.draw.circle(surface, (0, 0, 180), (x - 5 + px_off, y - 4 + py_off), 3)
            pygame.draw.circle(surface, (0, 0, 180), (x + 5 + px_off, y - 4 + py_off), 3)
            pygame.draw.circle(surface, WHITE, (x - 4 + px_off, y - 5 + py_off), 1)
            pygame.draw.circle(surface, WHITE, (x + 6 + px_off, y - 5 + py_off), 1)
