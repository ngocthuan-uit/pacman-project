import pygame
from core.constants import *

"""Heads-up display helpers: floating score notifications."""

class FloatingText:
    """A short-lived text label that drifts upward and fades out.

    Used throughout the game to provide immediate visual feedback for:
        - Eating a power pellet  ("POWER!")
        - Killing a ghost        ("CRIT!", "+200", "BURN x2!", "+TIME!")
        - Collecting a bonus     (item name, point value, coin gain)

    The text moves upward at 0.6 px/frame and fades linearly from fully
    opaque to transparent over its lifetime.

    Attributes:
        text (str): The string to display.
        x (float): Horizontal center of the label in pixels.
        y (float): Current vertical position; decreases each frame.
        color (tuple[int,int,int]): RGB text colour.
        lifetime (int): Total frames before the label disappears (default 50).
        age (int): Frames elapsed since creation.
        font (pygame.font.Font): Pre-rendered font at the requested size.
    """
    def __init__(self, text, x, y, color = WHITE, size = 22, lifetime = 50):
        """Create a floating label centered at pixel position (x, y).

        Args:
            text (str): String to render.
            x (float): Horizontal center in pixels.
            y (float): Initial vertical position in pixels.
            color (tuple): RGB colour. Defaults to WHITE.
            size (int): Font size in points. Defaults to 22.
            lifetime (int): Frames until the label is removed. Defaults to 50.
        """
        self.text     = text
        self.x        = x
        self.y        = y
        self.color    = color
        self.lifetime = lifetime
        self.age      = 0
        self.font     = pygame.font.SysFont("Arial", size, bold=True)
    
    def update(self):
        """Advance the animation by one frame: increment age and move y upward."""
        self.age += 1
        self.y   -= 0.6

    def draw(self, surface):
        """Render the label with alpha proportional to remaining lifetime.

        Alpha = max(0, 255 - 255 * age / lifetime), so the text starts
        fully opaque and is invisible on its last frame.

        Args:
            surface (pygame.Surface): Render target.
        """
        alpha = max(0, 255 - int(255 * self.age / self.lifetime))
        surf  = self.font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        surface.blit(surf, (int(self.x - surf.get_width() // 2), int(self.y)))
    
    @property
    def dead(self):
        """True when age has reached or exceeded lifetime.

        Returns:
            bool: Whether this label should be removed from the active list.
        """
        return self.age >= self.lifetime