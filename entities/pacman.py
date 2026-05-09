import math
import random
import pygame
from core.constants import *
from core.entity import Entity
import systems.player_state as ps

"""Player-controlled Pacman entity with equipment and animation support."""

class Pacman(Entity):
    """Player character with mouth animation, directional eye, and full equipment support.

    Pacman's speed each frame is:
        speed = base_speed + bike_bonus + weapon_bonus
    where bike_bonus is 0.5 (Vespa) or 0.75 (Sport), and weapon_bonus
    is 0.5 for the Dagger while powered.

    Attributes:
        mouth_open (float): Oscillating angle value (0-1.5) driving the mouth animation.
        mouth_change (int): +1 while mouth is opening, -1 while closing.
        eye_offset_x (int): Horizontal eye offset relative to body center.
        eye_offset_y (int): Vertical eye offset relative to body center.
        last_face_dir (int): Last non-zero facing angle in degrees
                             (0=right, 180=left, 90=up, -90=down).
                             Used to keep the mouth pointing the right way when stationary.
    """
    def __init__(self, c, r):
        super().__init__(c, r, speed=2)
        self.mouth_open   = 0
        self.mouth_change = 1
        self.eye_offset_x = 0
        self.eye_offset_y = -6
        self.last_face_dir = 0 # 0=Right, 180=Left, 90=Up, -90=Down

    def update(self, game_map, is_powered):
        """Recalculate speed, animate the mouth, and move Pacman one frame.

        Speed bonuses from bikes and the Dagger weapon are recalculated
        every frame so equip/unequip changes take effect immediately.
        When Pacman reaches a tile center the queued direction (next_dir)
        is applied if the resulting tile is not a wall; the current direction
        is cancelled if the next tile ahead is a wall.

        Args:
            game_map (Map): Used for wall checks.
            is_powered (bool): True while a power pellet effect is active.
        """
        # EQUIPMENTS AND VEHICLES
        bike_bonus = 0
        if ps.equipped_bike == "VESPA": bike_bonus = 0.5
        elif ps.equipped_bike == "SPORT": bike_bonus = 0.75
        
        weapon_bonus = 0
        # DAGGER: INCREASE SPEED
        if is_powered and ps.equipped_weapon == "DAGGER":
            weapon_bonus = 0.5
            
        self.speed = self.base_speed + bike_bonus + weapon_bonus

        self.mouth_open += self.mouth_change * 0.2
        if self.mouth_open > 1.5 or self.mouth_open < 0:
            self.mouth_change *= -1

        if self.is_at_center():
            self.snap_to_center()
            self.c = int(self.x) // TILE_SIZE
            self.r = int(self.y) // TILE_SIZE

            if self.next_dir_x != 0 or self.next_dir_y != 0:
                if not game_map.is_wall(self.c + self.next_dir_x, self.r + self.next_dir_y):
                    self.dir_x, self.dir_y = self.next_dir_x, self.next_dir_y

            if game_map.is_wall(self.c + self.dir_x, self.r + self.dir_y):
                self.dir_x, self.dir_y = 0, 0

        self.x += self.dir_x * self.speed
        self.y += self.dir_y * self.speed
        self.wrap_around()

        if   self.dir_x ==  1: 
            self.eye_offset_x, self.eye_offset_y =  0, -6
            self.last_face_dir = 0
        elif self.dir_x == -1: 
            self.eye_offset_x, self.eye_offset_y =  0, -6
            self.last_face_dir = 180
        elif self.dir_y == -1: 
            self.eye_offset_x, self.eye_offset_y = -6,  0
            self.last_face_dir = 90
        elif self.dir_y ==  1: 
            self.eye_offset_x, self.eye_offset_y =  6,  0
            self.last_face_dir = -90

    def draw(self, surface, is_powered=False):
        """Render Pacman together with any equipped bike and weapon.

        Drawing order (back to front):
            1. Bike wheels and body (if a bike is equipped).
            2. Power glow ring (if powered).
            3. Pacman body on a dedicated surface with a transparent mouth cutout,
               plus highlight sphere and directional eye.
            4. Weapon animation on top of the body (if powered and weapon equipped):
               - DAGGER : short thrusting blade that pulses forward.
               - FIRE/ICE: long sweeping sword with motion-blur trail circles.
               - AXE     : heavy blade swinging in a wide arc.

        Args:
            surface (pygame.Surface): Render target.
            is_powered (bool): Controls body colour and whether the weapon is drawn.
        """
        draw_angle = 0
        if   self.dir_x ==  1: draw_angle = 0
        elif self.dir_x == -1: draw_angle = 180
        elif self.dir_y ==  1: draw_angle = 270
        elif self.dir_y == -1: draw_angle = 90
        else:
            d = {0: 0, 180: 180, 90: 90, -90: 270}
            draw_angle = d.get(self.last_face_dir, 0)

        # DRAW VEHICLES
        time_ms = pygame.time.get_ticks()
        if ps.equipped_bike:
            b_color  = BIKE_VESPA_COLOR if ps.equipped_bike == "VESPA" else BIKE_SPORT_COLOR
            dark_b   = tuple(max(0,   c - 80)  for c in b_color)
            light_b  = tuple(min(255, c + 100) for c in b_color)
            shadow_b = tuple(max(0,   c - 120) for c in b_color)
            BLK      = (0, 0, 0)
            GRY      = (80, 80, 80)
            LGRY     = (160, 160, 160)
            DGRY     = (40, 40, 40)
            CHROME   = (210, 210, 220)
            SEAT     = (30, 20, 20)
            SEAT_L   = (60, 45, 45)

            x, y = self.x, self.y

            def px(surf, col, points):
                """Draw a filled polygon with black outline for pixel-art look."""
                if len(points) >= 3:
                    pygame.draw.polygon(surf, col,   points)
                    pygame.draw.polygon(surf, BLK,   points, 1)

            def circle_px(surf, col, cx, cy, r):
                pygame.draw.circle(surf, col, (int(cx), int(cy)), r)
                pygame.draw.circle(surf, BLK, (int(cx), int(cy)), r, 1)

            def wheel(surf, wx, wy, r=9):
                """Pixel-art wheel with tyre, rim, spokes, hub."""
                circle_px(surf, (10, 10, 10), wx, wy, r)       # outer tyre
                circle_px(surf, (35, 35, 35), wx, wy, r - 2)   # tyre inner
                circle_px(surf, b_color,      wx, wy, r - 5)   # rim
                # spokes
                for ang in range(0, 360, 45):
                    rad = math.radians(ang)
                    sx  = wx + int((r - 5) * math.cos(rad))
                    sy  = wy + int((r - 5) * math.sin(rad))
                    pygame.draw.line(surf, LGRY, (int(wx), int(wy)), (sx, sy), 1)
                circle_px(surf, CHROME, wx, wy, 3)              # hub
                pygame.draw.circle(surf, WHITE, (int(wx), int(wy)), 1)  # hub shine

            if draw_angle in (0, 180):
                dm = 1 if draw_angle == 0 else -1

                if ps.equipped_bike == "VESPA":
                    # ── VESPA SIDE VIEW ──
                    # rear wheel
                    wheel(surface, x - 13*dm, y + 10)
                    # front wheel
                    wheel(surface, x + 13*dm, y + 10)

                    # lower body / footboard
                    px(surface, shadow_b, [
                        (x - 16*dm, y + 10),
                        (x -  4*dm, y +  2),
                        (x + 10*dm, y +  2),
                        (x + 14*dm, y + 10),
                    ])
                    # main body shell
                    px(surface, b_color, [
                        (x - 14*dm, y +  8),
                        (x - 10*dm, y -  4),
                        (x -  3*dm, y -  9),
                        (x +  5*dm, y -  8),
                        (x + 12*dm, y -  3),
                        (x + 14*dm, y +  3),
                        (x + 12*dm, y +  8),
                    ])
                    # body highlight strip
                    px(surface, light_b, [
                        (x -  8*dm, y -  3),
                        (x -  3*dm, y -  7),
                        (x +  4*dm, y -  6),
                        (x +  9*dm, y -  2),
                        (x +  7*dm, y +  0),
                        (x +  3*dm, y -  4),
                        (x -  2*dm, y -  5),
                        (x -  6*dm, y -  1),
                    ])
                    # dark shadow underside
                    px(surface, dark_b, [
                        (x -  6*dm, y +  5),
                        (x +  8*dm, y +  5),
                        (x + 12*dm, y +  8),
                        (x -  10*dm, y + 8),
                    ])
                    # front fork
                    pygame.draw.line(surface, DGRY,
                        (int(x + 10*dm), int(y - 1)),
                        (int(x + 13*dm), int(y +  9)), 2)
                    pygame.draw.line(surface, BLK,
                        (int(x + 10*dm), int(y - 1)),
                        (int(x + 13*dm), int(y +  9)), 1)
                    # rear mudguard
                    pygame.draw.arc(surface, dark_b,
                        pygame.Rect(int(x - 21*dm), int(y + 2), 12, 10),
                        math.pi * 0.2, math.pi * 0.9, 3)

                    # seat
                    px(surface, SEAT, [
                        (x -  9*dm, y - 12),
                        (x -  1*dm, y - 12),
                        (x +  2*dm, y -  9),
                        (x -  8*dm, y -  9),
                    ])
                    px(surface, SEAT_L, [
                        (x -  8*dm, y - 11),
                        (x -  2*dm, y - 11),
                        (x -  1*dm, y - 10),
                        (x -  8*dm, y - 10),
                    ])

                    # windshield
                    px(surface, (160, 220, 255), [
                        (x +  3*dm, y - 10),
                        (x +  7*dm, y -  9),
                        (x +  8*dm, y -  5),
                        (x +  4*dm, y -  5),
                    ])
                    # windshield shine
                    px(surface, (210, 240, 255), [
                        (x +  4*dm, y -  9),
                        (x +  6*dm, y -  9),
                        (x +  6*dm, y -  7),
                        (x +  4*dm, y -  7),
                    ])

                    # headlight
                    lx, ly = int(x + 14*dm), int(y - 2)
                    circle_px(surface, (255, 255, 180), lx, ly, 4)
                    circle_px(surface, (255, 255, 100), lx, ly, 2)
                    pygame.draw.circle(surface, WHITE, (lx, ly), 1)

                    # exhaust pipe
                    ex, ey = int(x - 15*dm), int(y + 8)
                    pygame.draw.rect(surface, GRY,  (ex - (5 if dm==1 else 0), ey, 7, 3))
                    pygame.draw.rect(surface, BLK,  (ex - (5 if dm==1 else 0), ey, 7, 3), 1)
                    pygame.draw.rect(surface, LGRY, (ex - (5 if dm==1 else 0), ey, 7, 1))
                    if random.random() > 0.55:
                        for i in range(2):
                            pygame.draw.circle(surface, (180, 180, 180),
                                (ex - (6+i)*dm + random.randint(-1,1),
                                 ey + 1 + random.randint(0, 1)),
                                random.randint(1, 3))

                    # handlebar
                    hbx = int(x + 8*dm)
                    pygame.draw.line(surface, DGRY, (hbx, int(y - 9)), (hbx, int(y - 12)), 2)
                    pygame.draw.line(surface, LGRY, (hbx - dm, int(y - 11)),
                                     (hbx + 2*dm, int(y - 11)), 2)
                    pygame.draw.line(surface, BLK,  (hbx - dm, int(y - 11)),
                                     (hbx + 2*dm, int(y - 11)), 1)

                else:  # SPORT BIKE
                    # ── SPORT BIKE SIDE VIEW ──
                    # rear wheel (bigger)
                    wheel(surface, x - 14*dm, y + 10, r=10)
                    # front wheel
                    wheel(surface, x + 14*dm, y + 10, r=10)

                    # swingarm
                    pygame.draw.line(surface, DGRY,
                        (int(x - 14*dm), int(y + 4)),
                        (int(x - 2*dm),  int(y + 6)), 3)
                    pygame.draw.line(surface, BLK,
                        (int(x - 14*dm), int(y + 4)),
                        (int(x - 2*dm),  int(y + 6)), 1)

                    # lower fairing
                    px(surface, shadow_b, [
                        (x - 17*dm, y +  8),
                        (x -  6*dm, y +  0),
                        (x + 10*dm, y +  0),
                        (x + 17*dm, y +  5),
                        (x + 14*dm, y + 10),
                        (x - 14*dm, y + 10),
                    ])
                    # upper fairing
                    px(surface, b_color, [
                        (x -  6*dm, y +  0),
                        (x -  4*dm, y - 11),
                        (x +  4*dm, y - 13),
                        (x +  9*dm, y - 12),
                        (x + 14*dm, y -  5),
                        (x + 10*dm, y +  0),
                    ])
                    # fairing highlight
                    px(surface, light_b, [
                        (x -  2*dm, y - 10),
                        (x +  4*dm, y - 12),
                        (x +  8*dm, y -  8),
                        (x +  6*dm, y -  5),
                        (x +  1*dm, y -  6),
                    ])
                    # belly pan
                    px(surface, dark_b, [
                        (x -  5*dm, y +  0),
                        (x + 10*dm, y +  0),
                        (x + 10*dm, y +  3),
                        (x -  5*dm, y +  3),
                    ])

                    # front fork
                    pygame.draw.line(surface, CHROME,
                        (int(x + 11*dm), int(y - 3)),
                        (int(x + 14*dm), int(y + 8)), 3)
                    pygame.draw.line(surface, BLK,
                        (int(x + 11*dm), int(y - 3)),
                        (int(x + 14*dm), int(y + 8)), 1)
                    pygame.draw.line(surface, WHITE,
                        (int(x + 11*dm), int(y - 2)),
                        (int(x + 12*dm), int(y + 4)), 1)

                    # seat
                    px(surface, SEAT, [
                        (x -  6*dm, y - 12),
                        (x +  2*dm, y - 14),
                        (x +  6*dm, y - 13),
                        (x +  4*dm, y - 10),
                        (x -  5*dm, y - 10),
                    ])
                    px(surface, SEAT_L, [
                        (x -  5*dm, y - 13),
                        (x +  1*dm, y - 13),
                        (x +  3*dm, y - 12),
                        (x -  4*dm, y - 11),
                    ])

                    # cockpit / windshield
                    px(surface, (80, 200, 255), [
                        (x -  1*dm, y - 12),
                        (x +  4*dm, y - 13),
                        (x +  7*dm, y -  9),
                        (x +  3*dm, y -  8),
                    ])
                    px(surface, (180, 230, 255), [
                        (x +  0*dm, y - 11),
                        (x +  3*dm, y - 12),
                        (x +  5*dm, y -  9),
                        (x +  2*dm, y -  9),
                    ])

                    # racing stripes
                    px(surface, WHITE, [
                        (x -  4*dm, y +  1),
                        (x + 10*dm, y -  3),
                        (x + 10*dm, y -  1),
                        (x -  4*dm, y +  3),
                    ])
                    px(surface, (255, 255, 0), [
                        (x -  4*dm, y +  3),
                        (x + 10*dm, y -  1),
                        (x + 10*dm, y +  1),
                        (x -  4*dm, y +  5),
                    ])

                    # headlight (angular)
                    px(surface, (255, 255, 180), [
                        (x + 15*dm, y - 4),
                        (x + 18*dm, y - 1),
                        (x + 18*dm, y + 2),
                        (x + 15*dm, y + 2),
                    ])
                    px(surface, WHITE, [
                        (x + 16*dm, y - 3),
                        (x + 17*dm, y - 1),
                        (x + 17*dm, y + 1),
                        (x + 16*dm, y + 1),
                    ])

                    # exhaust (twin pipes)
                    for pipe_y in [y + 6, y + 8]:
                        ex = int(x - 16*dm)
                        pygame.draw.rect(surface, GRY,
                            (ex - (6 if dm==1 else 0), int(pipe_y), 8, 2))
                        pygame.draw.rect(surface, BLK,
                            (ex - (6 if dm==1 else 0), int(pipe_y), 8, 2), 1)
                        pygame.draw.line(surface, LGRY,
                            (ex - (6 if dm==1 else 0), int(pipe_y)),
                            (ex - (6 if dm==1 else 0) + 8, int(pipe_y)), 1)
                    if random.random() > 0.25:
                        for i in range(3):
                            fcolor = (255, random.randint(120, 220), 0)
                            pygame.draw.circle(surface, fcolor,
                                (int(x - 17*dm) + random.randint(-1,1),
                                 int(y + 7)     + random.randint(-1,1)),
                                random.randint(2, 5))
                        pygame.draw.circle(surface, (255, 255, 150),
                            (int(x - 17*dm), int(y + 7)), 2)

                    # handlebar
                    hbx = int(x + 5*dm)
                    pygame.draw.line(surface, DGRY,  (hbx, int(y-13)), (hbx, int(y-16)), 2)
                    pygame.draw.line(surface, LGRY,  (hbx-dm, int(y-15)), (hbx+3*dm, int(y-15)), 3)
                    pygame.draw.line(surface, BLK,   (hbx-dm, int(y-15)), (hbx+3*dm, int(y-15)), 1)

            else:
                # ── TOP-DOWN VIEW ──
                dm = 1 if draw_angle == 90 else -1

                if ps.equipped_bike == "VESPA":
                    # shadow
                    shadow = pygame.Surface((32, 20), pygame.SRCALPHA)
                    pygame.draw.ellipse(shadow, (0,0,0,50), (0,0,32,20))
                    surface.blit(shadow, (int(x)-16, int(y)-6))
                    # body
                    px(surface, dark_b, [
                        (x,      y - 12*dm),
                        (x - 10, y -  4*dm),
                        (x - 9,  y +  8*dm),
                        (x + 9,  y +  8*dm),
                        (x + 10, y -  4*dm),
                    ])
                    px(surface, b_color, [
                        (x,      y - 10*dm),
                        (x -  8, y -  3*dm),
                        (x -  7, y +  6*dm),
                        (x +  7, y +  6*dm),
                        (x +  8, y -  3*dm),
                    ])
                    px(surface, light_b, [
                        (x - 3, y -  9*dm),
                        (x + 3, y -  9*dm),
                        (x + 4, y -  4*dm),
                        (x - 4, y -  4*dm),
                    ])
                    # seat
                    px(surface, SEAT, [
                        (x - 5, y +  1*dm),
                        (x + 5, y +  1*dm),
                        (x + 4, y +  6*dm),
                        (x - 4, y +  6*dm),
                    ])
                    px(surface, SEAT_L, [
                        (x - 4, y +  2*dm),
                        (x + 4, y +  2*dm),
                        (x + 3, y +  4*dm),
                        (x - 3, y +  4*dm),
                    ])
                    # front wheel
                    pygame.draw.ellipse(surface, (15,15,15),
                        (int(x)-5, int(y - 14*dm)-3, 10, 6))
                    pygame.draw.ellipse(surface, (35,35,35),
                        (int(x)-4, int(y - 14*dm)-2, 8,  4))
                    pygame.draw.ellipse(surface, b_color,
                        (int(x)-3, int(y - 14*dm)-1, 6,  3))
                    pygame.draw.ellipse(surface, (15,15,15),
                        (int(x)-5, int(y + 10*dm)-3, 10, 6))
                    pygame.draw.ellipse(surface, (35,35,35),
                        (int(x)-4, int(y + 10*dm)-2, 8,  4))
                    pygame.draw.ellipse(surface, b_color,
                        (int(x)-3, int(y + 10*dm)-1, 6,  3))
                    # headlight
                    circle_px(surface, (255,255,180), x, y - 13*dm, 3)
                    pygame.draw.circle(surface, WHITE, (int(x), int(y - 13*dm)), 1)

                else:  # SPORT top-down
                    shadow = pygame.Surface((32, 22), pygame.SRCALPHA)
                    pygame.draw.ellipse(shadow, (0,0,0,60), (0,0,32,22))
                    surface.blit(shadow, (int(x)-16, int(y)-7))
                    # lower body
                    px(surface, shadow_b, [
                        (x,      y - 15*dm),
                        (x - 11, y -  3*dm),
                        (x - 10, y +  9*dm),
                        (x + 10, y +  9*dm),
                        (x + 11, y -  3*dm),
                    ])
                    # upper fairing
                    px(surface, b_color, [
                        (x,      y - 13*dm),
                        (x -  9, y -  2*dm),
                        (x -  8, y +  7*dm),
                        (x +  8, y +  7*dm),
                        (x +  9, y -  2*dm),
                    ])
                    # highlight
                    px(surface, light_b, [
                        (x - 3, y - 11*dm),
                        (x + 3, y - 11*dm),
                        (x + 4, y -  5*dm),
                        (x - 4, y -  5*dm),
                    ])
                    # racing stripes
                    px(surface, WHITE, [
                        (x - 2, y -  2*dm),
                        (x + 2, y -  2*dm),
                        (x + 2, y +  5*dm),
                        (x - 2, y +  5*dm),
                    ])
                    px(surface, (255,255,0), [
                        (x - 4, y -  1*dm),
                        (x - 2, y -  1*dm),
                        (x - 2, y +  5*dm),
                        (x - 4, y +  5*dm),
                    ])
                    px(surface, (255,255,0), [
                        (x + 2, y -  1*dm),
                        (x + 4, y -  1*dm),
                        (x + 4, y +  5*dm),
                        (x + 2, y +  5*dm),
                    ])
                    # seat
                    px(surface, SEAT, [
                        (x - 4, y +  2*dm),
                        (x + 4, y +  2*dm),
                        (x + 3, y +  7*dm),
                        (x - 3, y +  7*dm),
                    ])
                    # cockpit
                    px(surface, (80,200,255), [
                        (x - 4, y - 12*dm),
                        (x + 4, y - 12*dm),
                        (x + 3, y -  8*dm),
                        (x - 3, y -  8*dm),
                    ])
                    px(surface, (200,235,255), [
                        (x - 2, y - 11*dm),
                        (x + 2, y - 11*dm),
                        (x + 2, y -  9*dm),
                        (x - 2, y -  9*dm),
                    ])
                    # wheels
                    for wy_off in [-14, 10]:
                        pygame.draw.ellipse(surface, (15,15,15),
                            (int(x)-6, int(y + wy_off*dm)-3, 12, 6))
                        pygame.draw.ellipse(surface, (35,35,35),
                            (int(x)-5, int(y + wy_off*dm)-2, 10, 4))
                        pygame.draw.ellipse(surface, b_color,
                            (int(x)-3, int(y + wy_off*dm)-1, 6,  3))
                    # headlight
                    px(surface, (255,255,180),
                       [(x-3, y-14*dm),(x+3, y-14*dm),(x+3, y-11*dm),(x-3, y-11*dm)])
                    pygame.draw.line(surface, WHITE,
                        (int(x)-2, int(y-13*dm)), (int(x)+2, int(y-13*dm)), 1)

        # DRAW PACMAN
        current_color = YELLOW
        if is_powered:
            if   ps.equipped_weapon == "FIRE":   current_color = SWORD_FIRE_COLOR
            elif ps.equipped_weapon == "ICE":    current_color = SWORD_ICE_COLOR
            elif ps.equipped_weapon == "DAGGER": current_color = DAGGER_COLOR
            elif ps.equipped_weapon == "AXE":    current_color = AXE_COLOR
            else:                             current_color = YELLOW 

        radius   = TILE_SIZE // 2 - 2
        y_offset = -4 if ps.equipped_bike else 0
        px, py   = int(self.x), int(self.y + y_offset)

        if is_powered:
            glow_surf = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
            glow_col  = (current_color[0], current_color[1], current_color[2], 60)
            pygame.draw.circle(glow_surf, glow_col, (radius*2, radius*2), radius*2)
            surface.blit(glow_surf, (px - radius*2, py - radius*2))

        cut_radius = radius + 5
        pac_surf = pygame.Surface((cut_radius * 2, cut_radius * 2))
        
        COLORKEY = (255, 0, 255) 
        pac_surf.fill(COLORKEY)
        pac_surf.set_colorkey(COLORKEY)

        cx, cy = cut_radius, cut_radius

        inner_color = tuple(min(255, ch + 60) for ch in current_color)
        dark_color = tuple(max(0, ch - 80) for ch in current_color)
        
        pygame.draw.circle(pac_surf, inner_color, (cx, cy), radius)
        pygame.draw.circle(pac_surf, dark_color, (cx, cy + 2), radius - 2)
        pygame.draw.circle(pac_surf, current_color, (cx, cy), radius - 1)

        hl_x = cx - radius // 3
        hl_y = cy - radius // 3
        pygame.draw.circle(pac_surf, inner_color, (hl_x, hl_y), radius // 4)

        eye_x = cx + self.eye_offset_x
        eye_y = cy + self.eye_offset_y
        pygame.draw.circle(pac_surf, BLACK, (eye_x, eye_y), 4)        
        pygame.draw.circle(pac_surf, WHITE, (eye_x + 1, eye_y - 1), 1)

        mouth_angle = 30 * abs(math.sin(self.mouth_open))
        
        pygame.draw.polygon(pac_surf, COLORKEY, [
            (cx, cy),
            (cx + cut_radius * math.cos(math.radians(draw_angle - mouth_angle)),
             cy - cut_radius * math.sin(math.radians(draw_angle - mouth_angle))),
            (cx + cut_radius * math.cos(math.radians(draw_angle + mouth_angle)),
             cy - cut_radius * math.sin(math.radians(draw_angle + mouth_angle)))
        ])

        surface.blit(pac_surf, (px - cx, py - cy))

        # WEAPONS
        if is_powered and ps.equipped_weapon:
            p_y = self.y + y_offset
            base_angle_rad = math.radians(draw_angle)

            if ps.equipped_weapon == "DAGGER":
                w_length = 8
                if draw_angle == 0:  
                    hand_x, hand_y = self.x, p_y + 6
                elif draw_angle == 180: 
                    hand_x, hand_y = self.x, p_y + 6
                elif draw_angle == 90:
                    hand_x, hand_y = self.x + 6, p_y
                else:          
                    hand_x, hand_y = self.x - 6, p_y
                thrust_dist = 2.5 + abs(math.sin(time_ms * 0.05)) * 6
                
                start_x = hand_x + thrust_dist * math.cos(base_angle_rad)
                start_y = hand_y - thrust_dist * math.sin(base_angle_rad)
                tip_x = start_x + w_length * math.cos(base_angle_rad)
                tip_y = start_y - w_length * math.sin(base_angle_rad)
                
                pygame.draw.circle(surface, (50, 50, 50), (int(start_x), int(start_y)), 3)
                pygame.draw.line(surface, DAGGER_COLOR, (start_x, start_y), (tip_x, tip_y), 3)
                pygame.draw.circle(surface, WHITE, (int(tip_x), int(tip_y)), 2)

            elif ps.equipped_weapon in ["FIRE", "ICE"]:
                w_length = 26
                w_color  = SWORD_FIRE_COLOR if ps.equipped_weapon == "FIRE" else SWORD_ICE_COLOR
                sweep_offset = math.sin(time_ms * 0.02) * 45
                final_angle_rad = math.radians(draw_angle + sweep_offset)
                tip_x = self.x + w_length * math.cos(final_angle_rad)
                tip_y = p_y - w_length * math.sin(final_angle_rad)
                for i in range(1, 4):
                    delay_sweep = math.sin((time_ms - i*30) * 0.02) * 45
                    trail_angle = math.radians(draw_angle + delay_sweep)
                    tx = self.x + w_length * math.cos(trail_angle)
                    ty = p_y - w_length * math.sin(trail_angle)
                    pygame.draw.circle(surface, w_color, (int(tx), int(ty)), max(1, 4-i))
                pygame.draw.line(surface, w_color, (self.x, p_y), (tip_x, tip_y), 5)
                pygame.draw.line(surface, WHITE, (self.x, p_y), (tip_x, tip_y), 2)
                pygame.draw.circle(surface, (80, 80, 80), (int(self.x), int(p_y)), 4)

            elif ps.equipped_weapon == "AXE":
                w_length = 25
                swing_offset = (abs(math.sin(time_ms * 0.006)) ** 3) * 110
                final_angle_rad = math.radians(draw_angle + 90 - swing_offset)
                tip_x = self.x + w_length * math.cos(final_angle_rad)
                tip_y = p_y - w_length * math.sin(final_angle_rad)
                pygame.draw.line(surface, (139, 69, 19), (self.x, p_y), (tip_x, tip_y), 4)
                hx = tip_x + 3 * math.cos(final_angle_rad)
                hy = tip_y - 3 * math.sin(final_angle_rad)
                a1 = final_angle_rad + math.pi/2
                a2 = final_angle_rad - math.pi/2
                bw = 18
                p1 = (hx + bw/2*math.cos(a1), hy - bw/2*math.sin(a1))
                p2 = (hx + bw/2*math.cos(a2), hy - bw/2*math.sin(a2))
                p3 = (tip_x + bw/2*math.cos(a2), tip_y - bw/2*math.sin(a2))
                p4 = (tip_x + bw/2*math.cos(a1), tip_y - bw/2*math.sin(a1))
                pygame.draw.polygon(surface, (180, 180, 180), [p1, p2, p3, p4])
                pygame.draw.polygon(surface, AXE_COLOR, [p1, p2, p3, p4], 2)
