from core.constants import *

"""Base class for all moving entities in the game."""

class Entity:
    """Abstract base for Pacman and Ghost, managing grid-aligned pixel movement.

    Movement model:
        Each entity stores both a pixel position (x, y) and a grid position
        (c, r). Direction is applied in pixels every frame. When the entity
        reaches the center of a tile (is_at_center), it may change direction
        and its grid coordinates are refreshed.
    """
    
    def __init__(self, c, r, speed):
        """
        start_c (int): Spawn column; used by reset_position and Ghost.bfs_to_home.
        start_r (int): Spawn row.
        base_speed (float): Default pixels-per-frame; restored after boosts.
        speed (float): Effective pixels-per-frame this frame (may include equipment bonus).
        x (float): Horizontal pixel position (center of sprite).
        y (float): Vertical pixel position (center of sprite).
        c (int): Current grid column derived from x.
        r (int): Current grid row derived from y.
        dir_x (int): Active horizontal direction (-1 = left, 0 = still, 1 = right).
        dir_y (int): Active vertical direction  (-1 = up,   0 = still, 1 = down).
        next_dir_x (int): Queued horizontal direction, applied when a tile center is reached.
        next_dir_y (int): Queued vertical direction.
        """
        self.start_c = c
        self.start_r = r
        self.base_speed = speed
        self.speed = speed
        self.reset_position()
    
    def reset_position(self):
        """Teleport the entity back to its spawn tile and clear all movement.
        Sets (x, y) to the pixel center of (start_c, start_r),
        resets (c, r), and zeroes both dir and next_dir vectors.
        """
        self.c = self.start_c
        self.r = self.start_r
        self.x = self.c * TILE_SIZE + TILE_SIZE // 2
        self.y = self.r * TILE_SIZE + TILE_SIZE // 2
        self.dir_x, self.dir_y = 0, 0
        self.next_dir_x, self.next_dir_y = 0, 0

    def is_at_center(self, move_speed = None):
        """Return True if the entity is within move_speed pixels of its tile center.
        Used to decide when a direction change or grid-coordinate update is safe.
        Falls back to self.speed when move_speed is not provided.
        Args:
            move_speed (float | None): Threshold distance. Defaults to self.speed.
        Returns:
            bool: True if both horizontal and vertical offsets are below the threshold.
        """
        if move_speed is None:
            move_speed = self.speed
        cx = self.x - (self.c * TILE_SIZE + TILE_SIZE // 2)
        cy = self.y - (self.r * TILE_SIZE + TILE_SIZE // 2)
        return abs(cx) < move_speed and abs(cy) < move_speed
    
    def snap_to_center(self):
        """Force pixel position to the exact center of the current tile.

        Called immediately after is_at_center returns True to prevent
        sub-pixel drift accumulating over many frames.
        """
        self.x = self.c * TILE_SIZE + TILE_SIZE // 2
        self.y = self.r * TILE_SIZE + TILE_SIZE // 2
    
    def wrap_around(self):
        """Handle horizontal tunnel teleportation at the map edges.
        When x drops below 0 the entity appears at the right edge, and vice versa.
        Also refreshes (c, r) from the current pixel position.
        """
        if self.x < 0:
            self.x = MAP_COLS * TILE_SIZE - TILE_SIZE // 2
        elif self.x >= MAP_COLS * TILE_SIZE:
            self.x = TILE_SIZE // 2
        self.c = int(self.x) // TILE_SIZE
        self.r = int(self.y) // TILE_SIZE
