import math
import random
import pygame
from core.constants import DOT_COLOR, YELLOW

"""Particle system providing visual feedback for dot collection, bursts, and death."""
class Particle:
    """A single screen-space particle driven by velocity, gravity, and fade-out.
    Visual fade: both radius and brightness scale linearly with
    (1 - age / lifetime), so the particle shrinks and darkens as it ages.
    """
    def __init__(self, x, y, color, vx = None, vy = None, size = None, lifetime = None):
        """Create a particle at pixel position (x, y).
        x (float): Current horizontal pixel position.
        y (float): Current vertical pixel position.
        color (tuple[int,int,int]): Base RGB colour before fade is applied.
        vx (float): Horizontal velocity in pixels per frame.
        vy (float): Vertical velocity (negative = upward at spawn).
        size (int): Starting radius in pixels.
        lifetime (int): Total frames the particle lives.
        age (int): Frames elapsed since creation.
        """
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-4, -0.5)
        self.size = size if size is not None else random.randint(2, 5)
        self.lifetime = lifetime if lifetime is not None else random.randint(20, 45)
        self.age = 0
    
    def update(self):
        """Advance physics by one frame: apply velocity, gravity, and friction."""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.18
        self.vx *= 0.95
        self.age += 1

    def draw(self, surface):
        """Render a circle whose size and brightness fade with age.
        Radius   = max(1, int(size * ratio))
        Colour   = base_color * (0.4 + 0.6 * ratio)   (never fully black)
        where ratio = max(0, 1 - age / lifetime).
        """
        ratio = max(0.0, 1 - self.age / self.lifetime)
        r = max(1, int(self.size * ratio))
        c = tuple(min(255, int(ch * (0.4 + 0.6 * ratio))) for ch in self.color)
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), r)
 
    @property
    def dead(self):
        return self.age >= self.lifetime
    

def spawn_dot_particles(plist, x, y, count = 5):
    """Append small upward-drifting particles at (x, y) to represent a eaten dot.

    Particles use DOT_COLOR and have tighter velocity and size ranges than
    a full burst, keeping the effect subtle.

    Args:
        plist (list[Particle]): Active particle list to append to.
        x (float): Spawn x in pixels (typically the dot's pixel center).
        y (float): Spawn y in pixels.
        count (int): Number of particles to create. Defaults to 5.
    """
    for i in range(count):
        plist.append(Particle(x, y, DOT_COLOR,
                              vx = random.uniform(-2, 2),
                              vy = random.uniform(-3, -0.5),
                              size = random.randint(2, 4),
                              lifetime = random.randint(15, 30)))    


def spawn_burst(plist, x, y, colors, count = 20):
    """Append an omnidirectional explosion of particles at (x, y).
    Each particle is launched at a random angle with a random speed between
    2 and 6 px/frame, creating a circular spray effect. Used for power pellet
    collection and ghost kills.
    Args:
        plist (list[Particle]): Active particle list to append to.
        x (float): Burst origin x in pixels.
        y (float): Burst origin y in pixels.
        colors (list[tuple]): Pool of RGB colours; each particle picks one at random.
        count (int): Number of particles. Defaults to 20.
    """
    for i in range(count):
        color = random.choice(colors)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        plist.append(Particle(x, y, color,
                              vx = math.cos(angle) * speed,
                              vy = math.sin(angle) * speed,
                              size = random.randint(3, 7),
                              lifetime = random.randint(30, 60)))
        

def spawn_death_particles(plist, x, y, count=30):
    """Append a large YELLOW burst at (x, y) when Pacman is killed.
    Larger particle sizes (3–8 px) and longer lifetimes (30–70 frames) than
    spawn_burst to emphasise the death moment.
    Args:
        plist (list[Particle]): Active particle list to append to.
        x (float): Death position x in pixels.
        y (float): Death position y in pixels.
        count (int): Number of particles. Defaults to 30.
    """
    for i in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        plist.append(Particle(x, y, YELLOW,
                              vx = math.cos(angle) * speed,
                              vy = math.sin(angle) * speed,
                              size = random.randint(3, 8),
                              lifetime = random.randint(30, 70)))
