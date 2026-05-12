import math
import pygame
from algorithms.astar import AStarGhost
from core.constants import TILE_SIZE, MAP_COLS, MAP_ROWS, WHITE
import systems.player_state as ps

"""
MegaGhost — Boss appears at Level 3 when Pacman has consumed 80% of the dots.
Mechanism:
- HP 3. Not frightened. Does not return to base.
- Pacman eats pellets → encounters boss → HP -1, boss stunned for 1.5s (90 frames),
game.py immediately resets frightened_timer=0 → 4 ghosts revive.
- While stunned: stands still, Pacman does NOT lose lives upon contact.
- Speed: HP3=2.0 → HP2=2.5 → HP1=3.0
- HP=0: is_dead=True, game.py processes +500 coins +1000 score → WIN.
Graphics:
- Red aura with 3 flashing rings
- Dark red body, sharp spikes at the feet
- Gold crown with 3 teeth + red stone in the center
- Yellow eyes + red pupils + furrowed brows
- White flash 0.5s when hit
- Gray flashing when stunned
- HP bar above head: green → orange → red
"""

BOSS_CORE    = (180,  20,  20)
BOSS_LIGHTER = (230,  60,  60)
BOSS_DARK    = (100,   0,   0)
BOSS_EYE     = (255, 255,   0)
BOSS_PUPIL   = (255,   0,   0)
BOSS_CROWN   = (255, 200,   0)
BOSS_CROWN_D = (180, 130,   0)
BOSS_AURA_1  = (255,  30,  30)
BOSS_AURA_2  = (255, 100,   0)


class MegaGhost(AStarGhost):
    """Boss ghost inherits AStarGhost — A* chases away Pacman. 
       Overrides get_neighbors() to allow U-turns freely, unlike normal ghosts. 
       This lets A* always find the true shortest path without getting trapped 
       in narrow corridors, making movement feel deliberate and threatening. """

    def __init__(self, c, r):
        super().__init__(c, r, color=BOSS_CORE)
        self.max_hp     = 3
        self.hp         = 3
        self.is_stunned = False
        self.stun_timer = 0
        self.aura_tick  = 0
        self.hit_flash  = 0
        self.speed      = 2.0

    def get_neighbors(self, c, r, game_map):
        """Return all reachable neighbours of (c, r) with no U-turn restriction.
        Normal ghosts forbid reversing direction to avoid zigzag behaviour.
        The boss always considers all four cardinal directions so A* can
        compute the true optimal path, including doubling back when needed.
        Handles horizontal wrap-around for tunnel tiles at column edges.
        """
        neighbors = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nc, nr = c + dx, r + dy
            if nc < 0:        nc = MAP_COLS - 1
            elif nc >= MAP_COLS: nc = 0
            if not game_map.is_wall(nc, nr):
                neighbors.append(((nc, nr), (dx, dy)))
        return neighbors

    def take_hit(self):
        """Minus 1 HP, activates stun for 1.5 seconds.
        Returns:
        bool: True if boss just died (HP == 0), False if still alive.
        """ 
        if self.is_stunned or self.is_dead:
            return False
        self.hp        -= 1
        self.hit_flash  = 30         
        self.is_stunned = True
        self.stun_timer = 90       
        if self.hp <= 0:
            self.is_dead = True
            return True
        self.speed = {2: 2.5, 1: 3.0}.get(self.hp, 3.0)
        return False

    def update(self, game_map, target_c, target_r, frightened_timer):
        """Advance the boss by one frame.

        When Pacman is powered (frightened_timer > 0), the boss flees toward
        the map corner furthest from Pacman instead of chasing, forcing the
        player to actively pursue rather than standing still for a free hit.
        When Pacman is not powered, the boss chases normally via A*.
        The boss is never frightened — no blue state, no speed reduction.

        Args:
            game_map (Map): Used for wall checks and pathfinding.
            target_c (int): Pacman's current column.
            target_r (int): Pacman's current row.
            frightened_timer (int): Remaining powered frames from game.py.
        """
        self.aura_tick += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.is_stunned:
            self.stun_timer -= 1
            if self.stun_timer <= 0:
                self.is_stunned = False
                self.stun_timer = 0
            return
        if self.is_dead:
            return
        self.is_frightened = False

        if frightened_timer > 0:
            # Pacman powered → boss flees to the furthest corner
            flee_c, flee_r = self._flee_target(target_c, target_r)
            super().update(game_map, flee_c, flee_r, 0)
        else:
            # Normal → chase Pacman via A*
            super().update(game_map, target_c, target_r, 0)

    def _flee_target(self, pacman_c, pacman_r):
        """Return the map corner furthest from Pacman's current tile.

        Chooses among the four playable corners so the boss always flees
        to a meaningful position rather than a random walkable cell.
        Uses Manhattan distance to pick the furthest corner.

        Args:
            pacman_c (int): Pacman's current column.
            pacman_r (int): Pacman's current row.

        Returns:
            tuple[int, int]: (col, row) of the furthest corner.
        """
        corners = [
            (1,            1),
            (MAP_COLS - 2, 1),
            (1,            MAP_ROWS - 2),
            (MAP_COLS - 2, MAP_ROWS - 2),
        ]
        return max(corners, key=lambda p: abs(p[0] - pacman_c) + abs(p[1] - pacman_r))

    def draw(self, surface, frightened_timer):
        """Render the boss sprite with all visual effects.

        Rendering layers (back to front):
            1. Three pulsing aura rings (red/orange, alpha animated via sin).
            2. Body — dome + rectangle; colour switches to WHITE on hit flash,
               grey flicker when stunned, BOSS_CORE otherwise.
            3. Arc highlight on the dome.
            4. Four animated spike segments at the bottom (sharper than normal ghosts).
            5. Yellow eye whites + red pupils that shift in the direction of travel.
            6. Furrowed brow lines above each eye.
            7. Gold crown with three teeth and a red gemstone at the centre peak.
            8. HP bar above the crown: green (3/3) → orange (2/3) → red (1/3).
        Args:
            surface (pygame.Surface): Target surface to draw onto.
            frightened_timer (int): Passed in from game.py (unused visually for
                the boss, but kept for interface consistency with Ghost.draw).
        """
        if self.is_dead:
            return
        x, y = int(self.x), int(self.y)
        r    = TILE_SIZE // 2 - 2
        t    = self.aura_tick

        for aura_col, aura_r, phase in [
            (BOSS_AURA_1, r + 10, 0.0),
            (BOSS_AURA_2, r + 17, 1.2),
            (BOSS_AURA_1, r + 24, 2.4),
        ]:
            alpha = int(55 + 45 * math.sin(t * 0.13 + phase))
            s = pygame.Surface((aura_r * 2 + 4, aura_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*aura_col, alpha), (aura_r + 2, aura_r + 2), aura_r)
            surface.blit(s, (x - aura_r - 2, y - aura_r - 2))

        if self.hit_flash > 0 and (self.hit_flash // 5) % 2 == 0:
            body_color = WHITE
        elif self.is_stunned:
            body_color = (150, 150, 150) if (self.stun_timer // 8) % 2 == 0 else BOSS_CORE
        else:
            body_color = BOSS_CORE

        pygame.draw.circle(surface, body_color, (x, y - 2), r)
        pygame.draw.rect(surface, body_color, (x - r, y - 2, r * 2, r + 2))
        if body_color == BOSS_CORE:
            pygame.draw.arc(surface, BOSS_LIGHTER,
                            pygame.Rect(x - r, y - 2 - r, r * 2, r * 2), 0, math.pi, 3)

        seg_w = (r * 2) / 4
        for i in range(4):
            sx    = x - r + i * seg_w
            spike = math.sin(t / 180.0 + i * 1.3) * 5
            pygame.draw.polygon(surface, body_color, [
                (sx,             y + r),
                (sx + seg_w / 2, y + r - 8 + spike),
                (sx + seg_w,     y + r),
                (sx + seg_w,     y),
                (sx,             y),
            ])

        pygame.draw.ellipse(surface, BOSS_EYE,  (x - 10, y - 10, 8, 10))
        pygame.draw.ellipse(surface, BOSS_EYE,  (x +  2, y - 10, 8, 10))
        px, py = self.dir_x * 2, self.dir_y * 2
        pygame.draw.circle(surface, BOSS_PUPIL, (x - 6 + px, y - 5 + py), 3)
        pygame.draw.circle(surface, BOSS_PUPIL, (x + 6 + px, y - 5 + py), 3)
        pygame.draw.circle(surface, WHITE,      (x - 5 + px, y - 6 + py), 1)
        pygame.draw.circle(surface, WHITE,      (x + 7 + px, y - 6 + py), 1)

        pygame.draw.line(surface, BOSS_DARK, (x - 10, y - 13), (x - 3, y - 10), 2)
        pygame.draw.line(surface, BOSS_DARK, (x + 10, y - 13), (x + 3, y - 10), 2)

        base_y = y - r - 2
        pygame.draw.rect(surface, BOSS_CROWN, (x - r + 3, base_y - 4, (r - 3) * 2, 5))
        for cx2, h in [(x - 8, 8), (x, 13), (x + 8, 8)]:
            pts = [(cx2 - 4, base_y - 2), (cx2, base_y - h), (cx2 + 4, base_y - 2)]
            pygame.draw.polygon(surface, BOSS_CROWN,   pts)
            pygame.draw.polygon(surface, BOSS_CROWN_D, pts, 1)
        pygame.draw.circle(surface, (255, 50, 50), (x, base_y - 10), 3)
        pygame.draw.circle(surface, WHITE,          (x + 1, base_y - 11), 1)

        bar_w, bar_h = 40, 5
        bx = x - bar_w // 2
        by = y - r - 32
        pygame.draw.rect(surface, (0, 0, 0),        (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        fill_w = int(bar_w * self.hp / self.max_hp)
        hp_col = {3: (50, 220, 50), 2: (255, 160, 0), 1: (255, 30, 30)}
        pygame.draw.rect(surface, hp_col.get(self.hp, (255, 0, 0)), (bx, by, fill_w, bar_h))
        pygame.draw.rect(surface, (200, 200, 200),  (bx - 1, by - 1, bar_w + 2, bar_h + 2), 1)