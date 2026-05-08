import pygame
from core.constants import *
from maps.levels import ALL_LEVELS

"""Game map: grid storage, dot/pellet tracking, and rendering."""

class Map:
    """Loads and manages one level's tile grid, collectibles, and visual output.

    The grid is a deep copy of the matching ALL_LEVELS entry so that
    eating dots does not corrupt the source data between rounds.

    Attributes:
        grid (list[list[int]]): 21 × 28 live tile matrix for this session.
        level_color (tuple[int,int,int]): RGB wall colour for the current level.
        dots (set[tuple[int,int]]): (c, r) pairs of dots not yet eaten.
        power_pellets (set[tuple[int,int]]): (c, r) pairs of power pellets not yet eaten.
        total_items (int): Sum of dots and power pellets at level start;
            used by Game to evaluate the 80 % win condition.
        blink_timer (int): Incremented every frame to drive the power-pellet blink animation.
    """

    def __init__(self, level):
        """Initialise the map for the given 1-based level number.

        Selects the correct ALL_LEVELS entry via modular indexing so that
        levels beyond the list length cycle back to the start.

        Args:
            level (int): 1-based level number.
        """
        idx = (level - 1) % len(ALL_LEVELS)
        self.grid = [row[:] for row in ALL_LEVELS[idx]]
        self.level_color = MAP_COLORS[idx]
        self.dots = set()
        self.power_pellets = set()
        self.blink_timer = 0
        self._init_items()

    def _init_items(self):
        """Scan the grid and populate dots, power_pellets, and total_items.

        Cells with value 0 become dots; cells with value 4 become power pellets.
        Called once by __init__.
        """
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                if self.grid[r][c] == 0:
                    self.dots.add((c, r))
                elif self.grid[r][c] == 4:
                    self.power_pellets.add((c, r))
        self.total_items = len(self.dots) + len(self.power_pellets)

    def draw(self, surface):
        """Render walls, dots, and power pellets onto surface each frame.

        Walls are drawn with a dark fill and a coloured border.
        Dots are small two-layer squares.
        Power pellets blink every 15 frames and display a soft glow when visible.

        Args:
            surface (pygame.Surface): The render target.
        """
        self.blink_timer += 1
        lc = self.level_color
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                if self.grid[r][c] == 1:
                    rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    shadow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    shadow.fill((lc[0]//5, lc[1]//5, lc[2]//5, 120))
                    surface.blit(shadow, rect.topleft)
                    pygame.draw.rect(surface, lc, rect, 2, border_radius=4)

        for (c, r) in self.dots:
            cx = c * TILE_SIZE + TILE_SIZE // 2
            cy = r * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.circle(surface, (180, 130, 120), (cx, cy), 3)
            pygame.draw.rect(surface, DOT_COLOR, (cx - 2, cy - 2, 4, 4))

        show = (self.blink_timer // 15) % 2 == 0
        for (c, r) in self.power_pellets:
            cx = c * TILE_SIZE + TILE_SIZE // 2
            cy = r * TILE_SIZE + TILE_SIZE // 2
            if show:
                glow = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 184, 174, 60), (15, 15), 14)
                surface.blit(glow, (cx - 15, cy - 15))
                pygame.draw.circle(surface, (255, 220, 210), (cx, cy), 9)
                pygame.draw.circle(surface, DOT_COLOR, (cx, cy), 7)
            else:
                pygame.draw.circle(surface, DOT_COLOR, (cx, cy), 6)
        
    def is_wall(self, c, r):
        """Check whether cell (c, r) blocks movement.

        Out-of-bounds coordinates return False (treated as open tunnel edges).

        Args:
            c (int): Column to test.
            r (int): Row to test.

        Returns:
            bool: True if the cell contains a wall (value 1).
        """
        if c < 0 or c >= MAP_COLS or r < 0 or r >= MAP_ROWS:
            return False
        return self.grid[r][c] == 1

    def get_open_cells(self):
        """Return all walkable grid positions suitable for bonus-item spawning.

        Includes cells with value 0 (path) or 2 (open corridor).

        Returns:
            list[tuple[int,int]]: List of (c, r) tuples.
        """
        cells = []
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                if self.grid[r][c] in (0, 2):
                    cells.append((c, r))
        return cells
 

