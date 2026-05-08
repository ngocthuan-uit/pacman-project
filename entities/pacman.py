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
            b_color = BIKE_VESPA_COLOR if ps.equipped_bike == "VESPA" else BIKE_SPORT_COLOR
            wheel_glow = (min(255, b_color[0]+60), min(255, b_color[1]+60), min(255, b_color[2]+60))
            
            if draw_angle in (0, 180):
                dm = 1 if draw_angle == 0 else -1
                wd = 16 if ps.equipped_bike == "SPORT" else 13

                for wx in [self.x - wd*dm, self.x + wd*dm]:
                    pygame.draw.circle(surface, (20, 20, 20), (int(wx), int(self.y+12)), 9)
                    pygame.draw.circle(surface, (50, 50, 50), (int(wx), int(self.y+12)), 7)
                    rim = b_color if ps.equipped_bike == "SPORT" else (210, 210, 210)
                    pygame.draw.circle(surface, rim, (int(wx), int(self.y+12)), 4)
                    pygame.draw.circle(surface, WHITE, (int(wx), int(self.y+12)), 2)
                
                if ps.equipped_bike == "VESPA":
                    body_pts = [
                        (self.x - 20*dm, self.y + 8),
                        (self.x - 14*dm, self.y - 4),
                        (self.x - 4*dm,  self.y - 8),
                        (self.x + 12*dm, self.y - 6),
                        (self.x + 16*dm, self.y + 2),
                        (self.x + 14*dm, self.y + 10),
                        (self.x - 18*dm, self.y + 10),
                    ]
                    pygame.draw.polygon(surface, b_color, body_pts)
                    pygame.draw.polygon(surface, wheel_glow, body_pts, 1)

                    pygame.draw.ellipse(surface, (40, 40, 40), (self.x - 10*dm, self.y - 11, 16, 6))
                    
                    lx = int(self.x + 14*dm)
                    pygame.draw.circle(surface, (255, 255, 180), (lx, int(self.y - 4)), 4)
                    pygame.draw.circle(surface, WHITE, (lx, int(self.y - 4)), 2)
                  
                    ex = int(self.x - 19*dm)
                    pygame.draw.rect(surface, (80,80,80), (ex - 4 if dm==1 else ex, int(self.y+7), 6, 3))
                    if random.random() > 0.5:
                        pygame.draw.circle(surface, (160,160,160),
                                           (ex - 6*dm + random.randint(-1,1),
                                            int(self.y+9) + random.randint(-1,1)),
                                           random.randint(2,4))
                else:
                    body_pts = [
                        (self.x - 20*dm, self.y + 4),
                        (self.x - 10*dm, self.y - 9),
                        (self.x +  2*dm, self.y - 7),
                        (self.x + 20*dm, self.y + 0),
                        (self.x + 14*dm, self.y + 11),
                        (self.x - 14*dm, self.y + 11),
                    ]
                    pygame.draw.polygon(surface, b_color, body_pts)
                    pygame.draw.polygon(surface, (100, 220, 255), [
                        (self.x + 2*dm, self.y - 7),
                        (self.x + 18*dm, self.y - 1),
                        (self.x + 14*dm, self.y + 4),
                        (self.x + 4*dm,  self.y - 4),
                    ])
                    pygame.draw.polygon(surface, wheel_glow, body_pts, 1)

                    pygame.draw.ellipse(surface, (30,30,30), (self.x - 12*dm, self.y - 12, 18, 6))
                    lx = int(self.x + 18*dm)
                    pygame.draw.polygon(surface, (255, 255, 180), [
                        (lx, int(self.y - 3)),
                        (lx + 4*dm, int(self.y)),
                        (lx, int(self.y + 3)),
                    ])
                    ex = int(self.x - 20*dm)
                    pygame.draw.rect(surface, (70,70,70), (ex - 4 if dm==1 else ex, int(self.y+7), 7, 4))
                    if random.random() > 0.3:
                        fcolor = (255, random.randint(80, 180), 0)
                        pygame.draw.circle(surface, fcolor,
                                           (ex - 7*dm, int(self.y+9)), random.randint(3,6))
            else:
                dm = 1 if draw_angle == 90 else -1
                if ps.equipped_bike == "VESPA":
                    pygame.draw.ellipse(surface, b_color, (int(self.x)-13, int(self.y)-8, 26, 16))
                    pygame.draw.ellipse(surface, wheel_glow, (int(self.x)-13, int(self.y)-8, 26, 16), 1)
                    pygame.draw.circle(surface, (200,200,200), (int(self.x)-11, int(self.y)-12), 4)
                    pygame.draw.circle(surface, (200,200,200), (int(self.x)+11, int(self.y)-12), 4)
                    pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y - 6*dm)), 5)
                else:
                    pts = [
                        (self.x,      self.y - 17*dm),
                        (self.x - 12, self.y +  3*dm),
                        (self.x -  6, self.y + 12*dm),
                        (self.x +  6, self.y + 12*dm),
                        (self.x + 12, self.y +  3*dm),
                    ]
                    pygame.draw.polygon(surface, b_color, pts)
                    pygame.draw.polygon(surface, (100,220,255), [
                        (self.x, self.y - 15*dm),
                        (self.x - 6, self.y - 2*dm),
                        (self.x + 6, self.y - 2*dm),
                    ])
                    pygame.draw.polygon(surface, wheel_glow, pts, 1)

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