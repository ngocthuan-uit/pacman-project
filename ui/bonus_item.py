import math
import random
import pygame
from core.constants import TILE_SIZE, FPS

"""Bonus collectibles that spawn randomly on the map and award points and coins."""
"""Catalogue of all collectible types. Each entry is a dict with keys:
    name   (str)            : Display name shown under the sprite.
    color  (tuple[int,int,int]): Primary draw colour.
    points (int)            : Score awarded on collection.
    coins  (int)            : Coins awarded on collection
                              (multiplied by 1.5 if Fire Sword is equipped).
"""

BONUS_ITEMS_DATA = [
    {"name": "Cherry",     "color": (220, 20,  60),  "points": 100,  "coins": 8 },
    {"name": "Orange",     "color": (255, 165,   0),  "points": 300,  "coins": 15},
    {"name": "Apple",      "color": ( 80, 200,  60),  "points": 500,  "coins": 25},
    {"name": "Melon",      "color": (120, 230,  80),  "points": 700,  "coins": 40},
    {"name": "Star",       "color": (255, 255,   0),  "points":1000,  "coins": 60},
]


class BonusItem:
    """A time-limited collectible fruit or star that appears on a random free tile.

    Lifetime is fixed at FPS * 10 frames (10 seconds at 60 FPS).
    The item blinks rapidly during the last 3 seconds to warn the player.

    Attributes:
        c (int): Grid column.
        r (int): Grid row.
        x (float): Pixel x of the sprite center (c * TILE_SIZE + TILE_SIZE // 2).
        y (float): Pixel y of the sprite center.
        data (dict): Entry from BONUS_ITEMS_DATA (name, color, points, coins).
        lifetime (int): Total frames the item exists before auto-removal.
        age (int): Frames elapsed since the item was created.
    """
    def __init__(self, c, r, data):
        """Place the item at grid cell (c, r) and attach its data dict.

        Args:
            c (int): Grid column.
            r (int): Grid row.
            data (dict): One entry from BONUS_ITEMS_DATA.
        """
        self.c = c
        self.r = r
        self.x = c * TILE_SIZE + TILE_SIZE // 2
        self.y = r * TILE_SIZE + TILE_SIZE // 2
        self.data = data
        self.lifetime = FPS * 10
        self.age = 0

    def update(self):
        self.age += 1

    @property
    def dead(self):
        """True when the item has reached its lifetime and should be removed.

        Returns:
            bool: age >= lifetime.
        """
        return self.age >= self.lifetime

    def draw(self, surface):
        """Render the item sprite with a bobbing motion and an expiry blink.

        Position bobs vertically using math.sin(t * 4) * 3, creating a gentle
        floating effect. During the final 3 seconds (FPS * 3 frames) the sprite
        alternates visible/invisible every 6 frames.

        Each item type has a hand-drawn sprite:
            Cherry : two red circles with green stalks and pink highlights.
            Orange : layered circles with an arc peel detail and a green stalk.
            Apple  : hexagonal polygon with a brown stem and a yellow shine dot.
            Melon  : horizontal ellipse with three vertical stripe lines.
            Star   : 5-point star (10-vertex polygon) with an orange outline.

        A small name label is drawn below each sprite in the item's colour.

        Args:
            surface (pygame.Surface): Render target.
        """
        if self.age > self.lifetime - FPS * 3:
            if (self.age // 6) % 2 == 1:
                return
        t = pygame.time.get_ticks() / 1000.0
        bob = math.sin(t * 4) * 3
        x, y = int(self.x), int(self.y + bob)
        color = self.data["color"]
        name  = self.data["name"]

        if name == "Cherry":
            pygame.draw.circle(surface, color, (x - 4, y + 2), 5)
            pygame.draw.circle(surface, color, (x + 4, y + 2), 5)
            pygame.draw.line(surface, (0, 140, 0), (x - 4, y - 3), (x, y - 8), 2)
            pygame.draw.line(surface, (0, 140, 0), (x + 4, y - 3), (x, y - 8), 2)
            pygame.draw.circle(surface, (255, 120, 120), (x - 5, y + 1), 2)
            pygame.draw.circle(surface, (255, 120, 120), (x + 3, y + 1), 2)

        elif name == "Orange":
            pygame.draw.circle(surface, color, (x, y), 7)
            pygame.draw.circle(surface, (255, 200, 60), (x, y), 5)
            pygame.draw.line(surface, (0, 140, 0), (x, y - 7), (x, y - 11), 2)
            pygame.draw.arc(surface, (200, 100, 0), (x-5, y-5, 10, 10), 0.2, 1.0, 1)

        elif name == "Apple":
            pts = [(x, y - 8), (x + 7, y - 2), (x + 6, y + 6),
                   (x, y + 8), (x - 6, y + 6), (x - 7, y - 2)]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.line(surface, (101, 67, 33), (x, y - 8), (x + 2, y - 12), 2)
            pygame.draw.circle(surface, (150, 255, 100), (x - 2, y - 3), 2)

        elif name == "Melon":
            pygame.draw.ellipse(surface, color, (x - 8, y - 5, 16, 10))
            pygame.draw.ellipse(surface, (200, 255, 150), (x - 6, y - 3, 12, 6))
            for i in range(3):
                sx = x - 4 + i * 4
                pygame.draw.line(surface, (0, 160, 0), (sx, y - 5), (sx, y + 5), 1)

        elif name == "Star":
            pts = []
            for i in range(10):
                ang = math.radians(i * 36 - 90)
                r2  = 8 if i % 2 == 0 else 4
                pts.append((x + r2 * math.cos(ang), y + r2 * math.sin(ang)))
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, (255, 200, 0), pts, 1)

        font = pygame.font.SysFont("Arial", 9, bold=True)
        label = font.render(name, True, color)
        surface.blit(label, (x - label.get_width()//2, y + 10))
        