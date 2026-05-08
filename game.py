import math
import pygame
from core.constants import *
from ui.bonus_item import BONUS_ITEMS_DATA, BonusItem
from core.map import Map
from entities.pacman import Pacman
from algorithms.astar import AStarGhost
from algorithms.bfs import BFSGhost
from algorithms.dijkstra import DijkstraGhost
from algorithms.dfs import DFSGhost
from systems.sound import SoundManager
from ui.hud import FloatingText
from systems.highscore import *
import systems.player_state as ps
import random
from ui.particles import *

"""Main game controller: event loop, state machine, update logic, and rendering."""

class Game:
    """Top-level controller for Pacman Arcade.

    Owns the pygame display, clock, font cache, sound manager, and all
    game-world objects. Drives a finite state machine with the following states:

        START      - animated title screen; 'S' opens the shop, any other key starts.
        SHOP       - Black Market purchase interface; ESC returns to START.
        READY_WAIT - 2-second countdown after level/life reset before PLAYING begins.
        PLAYING    - active gameplay; ESC returns to START (saving high score).
        GAMEOVER   - overlay shown when lives reach 0; any key → START.
        WIN        - overlay shown when ≥ 80 % of items are eaten; any key → START.

    Attributes:
        screen (pygame.Surface): Main display surface.
        clock (pygame.time.Clock): Frame-rate limiter.
        level (int): Current 1-based level number (max 3).
        score (int): Points accumulated this session.
        high_score (int): All-time best score loaded from disk at startup.
        lives (int): Remaining lives (starts at 3).
        state (str): Current FSM state label.
        frightened_timer (int): Frames remaining on the current power-pellet effect.
        ghost_combo (int): Consecutive ghosts eaten during one power-up (resets at 0).
        bonus_items (list[BonusItem]): Currently active bonus collectibles.
        bonus_spawn_timer (int): Countdown frames until the next bonus spawn attempt.
        particles (list[Particle]): Live particle effects.
        floats (list[FloatingText]): Live floating score notifications.
        equip_hint_timer (int): Frames the equip-change HUD confirmation stays visible.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PACMAN ARCADE")
        self.clock      = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("Impact", 100)
        self.font_large = pygame.font.SysFont("Arial", 50, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 25, bold=True)
        self.font_hud   = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_tiny  = pygame.font.SysFont("Arial", 14, bold=True)
        self.sound      = SoundManager()

        self.level      = 1
        self.max_level  = 3
        self.score      = 0
        self.high_score = load_high_score()
        self.lives      = 3
        self.state      = "START"
        self.frightened_timer = 0
        self.blink_title      = 0
        self.floats           = []
        self.particles        = []
        self.ghost_combo      = 0
        self.bonus_items      = []
        self.bonus_spawn_timer = 0
        self.equip_hint_timer = 0
    
    def _update_high_score(self):
        """Replace high_score with score if score is greater, then persist to disk."""
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)
    
    def reset_positions(self):
        """Return Pacman and all ghosts to their spawn tiles and transition to READY_WAIT.

        Clears is_frightened on every ghost, resets frightened_timer and
        ghost_combo, and starts a 2-second (FPS * 2 frame) wait timer.
        """
        self.pacman.reset_position()
        for ghost in self.ghosts:
            ghost.reset_position()
            ghost.is_frightened = False
        self.frightened_timer = 0
        self.ghost_combo      = 0
        self.state     = "READY_WAIT"
        self.wait_timer = FPS * 2

    def init_level(self):
        """Construct a fresh Map, Pacman, and four ghosts for self.level.

        Ghost base speed increases by 0.25 per level:
            speed = 2 + (level - 1) * 0.25

        Ghost roles and algorithms:
            AStarGhost    (red,   col 13, row  9) - Blinky; always targets Pacman directly.
            BFSGhost      (pink,  col 14, row  9) - Pinky;  targets 4 tiles ahead of Pacman.
            DijkstraGhost (cyan,  col 13, row 10) - Inky;   targets 2 tiles behind Pacman.
            DFSGhost      (orange,col 14, row 10) - Clyde;  retreats when within 8 tiles.

        Also resets items_eaten, particle/float lists, bonus item state,
        and calls reset_positions() to enter READY_WAIT.
        """
        self.map    = Map(self.level)
        self.pacman = Pacman(14, 16)
        ghost_speed = 2 + (self.level - 1) * 0.25
        self.ghosts = [
            AStarGhost   (13,  9, (255,   0,   0)),
            BFSGhost     (14,  9, (255, 184, 255)),
            DijkstraGhost(13, 10, (  0, 255, 255)),
            DFSGhost     (14, 10, (255, 184,  81)),
        ]
        for g in self.ghosts:
            g.base_speed = ghost_speed
            g.speed      = ghost_speed
        self.items_eaten      = 0
        self.floats           = []
        self.particles        = []
        self.ghost_combo      = 0
        self.bonus_items      = []
        self.bonus_spawn_timer = FPS * 8 
        self.reset_positions()

    def add_float(self, text, x, y, color=WHITE, size=22):
        """Append a FloatingText notification at pixel position (x, y).

        Args:
            text (str): Label string.
            x (float): Horizontal center in pixels.
            y (float): Initial vertical position in pixels.
            color (tuple): RGB text colour. Defaults to WHITE.
            size (int): Font size in points. Defaults to 22.
        """
        self.floats.append(FloatingText(text, x, y, color, size))
    
    def _try_buy_weapon(self, w_name, cost):
        """Purchase or equip a weapon from the shop.

        If the weapon is already owned, equips it immediately (no cost).
        Otherwise deducts cost from player_coins if affordable, appends
        w_name to owned_weapons, and sets equipped_weapon.
        Does nothing if the player cannot afford the weapon.
        """
        if w_name in ps.owned_weapons:
            ps.equipped_weapon = w_name
        elif ps.player_coins >= cost:
            ps.player_coins -= cost
            ps.owned_weapons.append(w_name)
            ps.equipped_weapon = w_name
 
    def _try_buy_bike(self, b_name, cost):
        """Purchase or equip a bike from the shop (identical logic to _try_buy_weapon).

        Args:
            b_name (str): Bike identifier ('VESPA', 'SPORT').
            cost (int): Purchase price in coins.
        """
        if b_name in ps.owned_bikes:
            ps.equipped_bike = b_name
        elif ps.player_coins >= cost:
            ps.player_coins -= cost
            ps.owned_bikes.append(b_name)
            ps.equipped_bike = b_name

    def _equip_weapon_ingame(self, w_name):
        """Toggle a purchased weapon on or off during gameplay.

        If w_name matches the currently equipped weapon, unequips it (sets to None).
        Otherwise equips it. Only works for weapons already in owned_weapons.
        Resets equip_hint_timer to FPS * 2 to show the HUD confirmation briefly.
        """
        if w_name in ps.owned_weapons:
            if ps.equipped_weapon == w_name:
                ps.equipped_weapon = None
            else:
                ps.equipped_weapon = w_name
            self.equip_hint_timer = FPS * 2

    def _equip_bike_ingame(self, b_name):
        """Toggle a purchased bike on or off during gameplay (same logic as _equip_weapon_ingame)."""
        if b_name in ps.owned_bikes:
            if ps.equipped_bike == b_name:
                ps.equipped_bike = None
            else:
                ps.equipped_bike = b_name
            self.equip_hint_timer = FPS * 2

    def _try_spawn_bonus(self):
        """Attempt to place one BonusItem on a randomly chosen free tile.

        A tile is considered free if it is walkable (get_open_cells) and not
        currently occupied by Pacman, any ghost, or an existing bonus item.
        If no free tile exists the spawn is skipped silently.

        Item type is sampled from the first (level + 1) entries of
        BONUS_ITEMS_DATA, so higher levels can produce rarer, higher-value items.
        """
        open_cells = self.map.get_open_cells()
        occupied = {(self.pacman.c, self.pacman.r)}
        for g in self.ghosts:
            occupied.add((g.c, g.r))
        for bi in self.bonus_items:
            occupied.add((bi.c, bi.r))
        cells = [c for c in open_cells if c not in occupied]
        if not cells:
            return
        c, r = random.choice(cells)
        max_idx = min(len(BONUS_ITEMS_DATA)-1, self.level)
        data = random.choice(BONUS_ITEMS_DATA[:max_idx+1])
        self.bonus_items.append(BonusItem(c, r, data))
    
    def run(self):
        """Start and maintain the main game loop until the window is closed.

        Each iteration:
            1. Poll all pygame events; route key presses to the active state handler.
            2. Call update() when state is PLAYING.
            3. Decrement wait_timer and transition to PLAYING when state is READY_WAIT.
            4. Call draw() and flip the display.
            5. Tick the clock to cap at FPS.
        """
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.state == "START":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_s:
                            self.state = "SHOP"
                        else:
                            self.level = 1
                            self.score = 0
                            self.lives = 3
                            self.init_level() 

                elif self.state == "SHOP":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = "START"
                            
                        if event.key == pygame.K_1: self._try_buy_weapon("DAGGER", 50)
                        elif event.key == pygame.K_2: self._try_buy_weapon("FIRE", 150)
                        elif event.key == pygame.K_3: self._try_buy_weapon("ICE", 300)
                        elif event.key == pygame.K_4: self._try_buy_weapon("AXE", 500)
                        elif event.key == pygame.K_5: self._try_buy_bike("VESPA", 400)
                        elif event.key == pygame.K_6: self._try_buy_bike("SPORT", 800)

                elif self.state in ("GAMEOVER", "WIN"):
                    if event.type == pygame.KEYDOWN:
                        self.state = "START"

                elif self.state == "PLAYING":
                    if event.type == pygame.KEYDOWN:
                        k = event.key
                        if   k in (pygame.K_UP,    pygame.K_w): self.pacman.next_dir_x, self.pacman.next_dir_y =  0, -1
                        elif k in (pygame.K_DOWN,  pygame.K_s): self.pacman.next_dir_x, self.pacman.next_dir_y =  0,  1
                        elif k in (pygame.K_LEFT,  pygame.K_a): self.pacman.next_dir_x, self.pacman.next_dir_y = -1,  0
                        elif k in (pygame.K_RIGHT, pygame.K_d): self.pacman.next_dir_x, self.pacman.next_dir_y =  1,  0
                        elif k == pygame.K_ESCAPE:
                            self._update_high_score()
                            self.state = "START"
                            pygame.mixer.stop()
                            pygame.mixer.music.stop()
                        elif k == pygame.K_q: self._equip_weapon_ingame("DAGGER")
                        elif k == pygame.K_e: self._equip_weapon_ingame("FIRE")
                        elif k == pygame.K_r: self._equip_weapon_ingame("ICE")
                        elif k == pygame.K_t: self._equip_weapon_ingame("AXE")
                        elif k == pygame.K_z: self._equip_bike_ingame("VESPA")
                        elif k == pygame.K_x: self._equip_bike_ingame("SPORT")

                elif self.state == "READY_WAIT":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self._update_high_score()
                            self.state = "START"
                    
            if self.state == "PLAYING":
                if self.pacman.dir_x != 0 or self.pacman.dir_y != 0:
                    self.sound.play('waka')
                else:
                    self.sound.stop('waka')
                self.update()

            elif self.state in ("READY_WAIT", "GAMEOVER", "WIN"):
                self.sound.stop('waka')
                if self.state == "READY_WAIT":
                    self.wait_timer -= 1
                    if self.wait_timer <= 0:
                        self.state = "PLAYING"

            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

    def update(self):
        """Advance all game-world logic by exactly one frame.

        Execution order:
            1. Decrement frightened_timer; at zero clear is_frightened on all ghosts
               and reset ghost_combo.
            2. Update Pacman (speed, direction, position).
            3. For each ghost, compute its strategic target then call ghost.update().
               Targets:
                   AStarGhost    → Pacman's current tile.
                   BFSGhost      → 4 tiles ahead of Pacman.
                   DijkstraGhost → 2 tiles behind Pacman.
                   DFSGhost      → Pacman's tile normally; corner (1, MAP_ROWS-2)
                                   when within 8 tiles of Pacman.
            4. Age and cull FloatingText, Particle, and BonusItem lists.
            5. Decrement equip_hint_timer and bonus_spawn_timer; spawn a bonus
               item when the timer reaches zero, then reset it to 8-15 seconds.
            6. Check Pacman's grid tile against dots and power_pellets:
                   dot         → +10 score, +1 coin, dot particles.
                   power pellet → +50 score, +5 coins, frightened_timer=600,
                                  reverse all ghosts, POWER! float and burst.
            7. Check Pacman's tile against each BonusItem:
                   collect     → add points (x2 with FIRE) and coins (x1.5 with FIRE),
                                  floating text, particle burst.
            8. Win check: if items_eaten >= total_items * 0.8, advance level or show WIN.
            9. Ghost collision (distance < TILE_SIZE * 0.8):
                   frightened ghost → ghost_combo++, pts=200*2^(combo-1),
                                      set is_dead=True, CRIT! float, burst.
                   normal ghost     → lose a life, death particles, 1.5 s pause,
                                      reset or GAMEOVER.
        """
        if self.frightened_timer > 0:
            self.frightened_timer -= 1
            if self.frightened_timer == 0:
                for ghost in self.ghosts:
                    ghost.is_frightened = False
                self.ghost_combo = 0

        self.pacman.update(self.map, is_powered = (self.frightened_timer > 0))

        # LOGIC FOR GHOSTS
        for ghost in self.ghosts:
            t_c, t_r = self.pacman.c, self.pacman.r # The default target is Pacman (AStar - Blinky).

            if isinstance(ghost, BFSGhost): # Pinky: Block 4 squares
                t_c = self.pacman.c + self.pacman.dir_x * 4
                t_r = self.pacman.r + self.pacman.dir_y * 4
            elif isinstance(ghost, DijkstraGhost): # Inky: Go around to the back
                t_c = self.pacman.c - self.pacman.dir_x * 2
                t_r = self.pacman.r - self.pacman.dir_y * 2
            elif isinstance(ghost, DFSGhost): # Cycle: Hide if too close
                dist = math.hypot(ghost.c - self.pacman.c, ghost.r - self.pacman.r)
                if dist < 8:
                    t_c, t_r = 1, MAP_ROWS - 2
                
            # Push target to update
            ghost.update(self.map, t_c, t_r, self.frightened_timer)
        
        # Update floats, particles
        for ft in self.floats:
            ft.update()
        self.floats = [ft for ft in self.floats if not ft.dead]

        for pt in self.particles:
            pt.update()
        self.particles = [pt for pt in self.particles if not pt.dead]

        # Update bonus items
        for bi in self.bonus_items:
            bi.update()
        self.bonus_items = [bi for bi in self.bonus_items if not bi.dead]

        # Equip hint timer
        if self.equip_hint_timer > 0:
            self.equip_hint_timer -= 1

        # Spawn bonus item timer
        self.bonus_spawn_timer -= 1
        if self.bonus_spawn_timer <= 0:
            self._try_spawn_bonus()
            self.bonus_spawn_timer = FPS * random.randint(8, 15)

        pacman_grid = (self.pacman.c, self.pacman.r)

        if pacman_grid in self.map.dots:
            self.map.dots.remove(pacman_grid)
            self.score        += 10
            self.items_eaten  += 1
            ps.player_coins   += 1
            spawn_dot_particles(self.particles, int(self.pacman.x), int(self.pacman.y), count=4)

        if pacman_grid in self.map.power_pellets:
            self.map.power_pellets.remove(pacman_grid)
            self.score       += 50
            self.items_eaten += 1
            ps.player_coins     += 5
            self.frightened_timer = 600
            self.ghost_combo      = 0
            self.sound.play('power')
            for ghost in self.ghosts:
                ghost.is_frightened = True
                ghost.dir_x *= -1
                ghost.dir_y *= -1
            self.add_float("POWER!", int(self.pacman.x), int(self.pacman.y) - 20,
                           color=(0, 200, 255), size=26)
            spawn_burst(self.particles, int(self.pacman.x), int(self.pacman.y),
                        [(0,200,255),(255,255,255),(0,100,255)], count=20)
            
        for bi in list(self.bonus_items):
            if (bi.c, bi.r) == pacman_grid:
                self.bonus_items.remove(bi)
                pts   = bi.data["points"]
                coins = bi.data["coins"]
                name  = bi.data["name"]
                if ps.equipped_weapon == "FIRE":
                    pts   *= 2
                    coins = int(coins * 1.5)
                self.score      += pts
                ps.player_coins += coins
                self._update_high_score()
                self.add_float(f"{name}! +{pts}pts", int(self.pacman.x), int(self.pacman.y) - 25,
                               color=bi.data["color"], size=22)
                self.add_float(f"+{coins} coins", int(self.pacman.x), int(self.pacman.y) - 45,
                               color=COIN_COLOR, size=18)
                spawn_burst(self.particles, int(self.pacman.x), int(self.pacman.y),
                            [bi.data["color"], YELLOW, WHITE], count=25)
        
        # Win condition
        if self.items_eaten >= self.map.total_items * 0.8:
            pygame.mixer.stop()
            if self.level < self.max_level:
                self.level += 1
                self.init_level()
            else:
                self._update_high_score()
                self.state = "WIN"
        
        # Ghost Collision
        for ghost in self.ghosts:
            if getattr(ghost, 'is_dead', False):
                continue
            dist = math.hypot(self.pacman.x - ghost.x, self.pacman.y - ghost.y)
            if dist < TILE_SIZE * 0.8:
                if ghost.is_frightened:
                    self.ghost_combo += 1
                    pts = 200 * (2 ** (self.ghost_combo - 1))

                    # FIRE SWORD: Double points/money when killing ghosts
                    if ps.equipped_weapon == "FIRE":
                        pts *= 2
                        ps.player_coins += 5
                        self.add_float("BURN x2!", int(ghost.x), int(ghost.y) - 50,
                                       color=SWORD_FIRE_COLOR, size=24)
                    # AXE: Increase the power-up time
                    if ps.equipped_weapon == "AXE":
                        self.frightened_timer = min(self.frightened_timer + 90, 600) # Add 1 second
                        self.add_float("+TIME!", int(ghost.x), int(ghost.y) - 50, color=AXE_COLOR, size=24)
                        
                    self.score += pts
                    self._update_high_score()
                    self.sound.play('eat_ghost')

                    spawn_burst(self.particles, int(ghost.x), int(ghost.y),
                                [ghost.color, WHITE, YELLOW], count=25)
                    ghost.is_dead = True
                    ghost.is_frightened = False
                    self.add_float("CRIT!", int(ghost.x), int(ghost.y) - 30,
                                   color=(255, 0, 0), size=30)
                    self.add_float(f"+{pts}", int(ghost.x), int(ghost.y) - 10,
                                   color=YELLOW, size=28)
                else:
                    self.sound.stop('waka')
                    self.sound.play('die')
                    spawn_death_particles(self.particles, int(self.pacman.x), int(self.pacman.y), 30)
                    pygame.display.flip()
                    pygame.time.wait(1500)
                    self.lives -= 1
                    self._update_high_score()
                    if self.lives > 0:
                        self.reset_positions()
                    else:
                        self.state = "GAMEOVER"
                    break
    
    def _draw_ghost_preview(self, surface, x, y, color, radius=22):
        """Draw a static ghost sprite at pixel position (x, y) for the title screen.

        Renders the full body shape (dome, rectangle, wave skirt) and eyes
        without any animation, glow, or frightened state.

        Args:
            surface (pygame.Surface): Render target.
            x (float): Horizontal center.
            y (float): Vertical center.
            color (tuple): Ghost body colour.
            radius (int): Sprite radius in pixels. Defaults to 22.
        """
        r = radius
        pygame.draw.circle(surface, color, (int(x), int(y-2)), r)
        pygame.draw.rect(surface, color, (x-r, y-2, r*2, r+2))
        lighter = tuple(min(255, ch+70) for ch in color)
        pygame.draw.arc(surface, lighter, pygame.Rect(x-r, y-2-r, r*2, r*2), 0, math.pi, 2)
        points = [(x-r, y+r),(x-r//2, y+r-5),(x, y+r),(x+r//2, y+r-5),(x+r, y+r),(x+r, y),(x-r, y)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.ellipse(surface, WHITE, (x-10, y-10, 8, 10))
        pygame.draw.ellipse(surface, WHITE, (x+2,  y-10, 8, 10))
        pygame.draw.circle(surface, (0,0,180), (int(x-6), int(y-6)), 3)
        pygame.draw.circle(surface, (0,0,180), (int(x+6), int(y-6)), 3)
        pygame.draw.circle(surface, WHITE, (int(x-5), int(y-7)), 1)
        pygame.draw.circle(surface, WHITE, (int(x+7), int(y-7)), 1)
    
    def _draw_pacman_preview(self, surface, x, y, mouth_angle, radius=28):
        """Draw a static Pacman sprite at pixel position (x, y) for the title screen.

        Uses the same layered-circle technique as Pacman.draw but always faces
        right and scales the eye and highlight offsets with the given radius so
        the preview looks correct at any size.

        Args:
            surface (pygame.Surface): Render target.
            x (float): Horizontal center.
            y (float): Vertical center.
            mouth_angle (float): Half-angle of the mouth opening in degrees.
            radius (int): Sprite radius. Defaults to 28.
        """
        surf_size = int(radius * 2 + 4)
        pac_surf = pygame.Surface((surf_size, surf_size))
        COLORKEY = (255, 0, 255) 
        pac_surf.fill(COLORKEY)
        pac_surf.set_colorkey(COLORKEY)
        cx, cy = surf_size // 2, surf_size // 2
        inner = tuple(min(255, ch+60) for ch in YELLOW)
        dark  = tuple(max(0, ch-80)  for ch in YELLOW)   
        pygame.draw.circle(pac_surf, inner, (cx, cy), radius)
        pygame.draw.circle(pac_surf, dark, (cx, cy + int(radius*0.15)), radius - int(radius*0.15))
        pygame.draw.circle(pac_surf, YELLOW, (cx, cy), radius - max(1, int(radius*0.07)))
        hl_x = cx - radius // 3
        hl_y = cy - radius // 3
        pygame.draw.circle(pac_surf, inner, (hl_x, hl_y), radius // 4)
        scale = radius / 14.0 
        eye_offset_x = int(-2 * scale)
        eye_offset_y = int(-7 * scale)
        eye_x = cx + eye_offset_x
        eye_y = cy + eye_offset_y
        pygame.draw.circle(pac_surf, BLACK, (eye_x, eye_y), max(2, int(4 * scale)))          
        pygame.draw.circle(pac_surf, WHITE, (eye_x + max(1, int(1*scale)), eye_y - max(1, int(1*scale))), max(1, int(1.5 * scale)))  
        ext = radius * 2 
        pygame.draw.polygon(pac_surf, COLORKEY, [
            (cx, cy),
            (cx + ext * math.cos(math.radians(-mouth_angle)),
             cy - ext * math.sin(math.radians(-mouth_angle))),
            (cx + ext * math.cos(math.radians(mouth_angle)),
             cy - ext * math.sin(math.radians(mouth_angle)))])
        surface.blit(pac_surf, (int(x - cx), int(y - cy)))
        
    def draw_shop(self):
        """Render the Black Market purchase screen.

        Layout:
            - Gradient dark background.
            - "BLACK MARKET" title with drop shadow.
            - Coin balance centered below the title.
            - Vertical divider splitting the screen into WEAPONS (left) and VEHICLES (right).
            - Each item row shows: name (coloured), description, and one of:
                [ EQUIPPED ] / [ RIDING ] in gold (active item, highlighted background row),
                [ OWNED ]                in green (purchased but not active),
                Cost: X coins            in grey  (not yet purchased).
            - "Press ESC to return Menu" hint at the bottom.
        """
        self.screen.fill(BLACK)
        for i in range(SCREEN_HEIGHT):
            val = int(20 * (1 - i/SCREEN_HEIGHT))
            pygame.draw.line(self.screen, (val, val//2, 0), (0, i), (SCREEN_WIDTH, i))

        title  = self.font_title.render("BLACK MARKET", True, YELLOW)
        shadow = self.font_title.render("BLACK MARKET", True, (100,80,0))
        self.screen.blit(shadow, (SCREEN_WIDTH//2 - title.get_width()//2 + 3, 53))
        self.screen.blit(title,  (SCREEN_WIDTH//2 - title.get_width()//2,     50))

        money_txt = self.font_small.render(f"Your Coins: {ps.player_coins}", True, COIN_COLOR)
        self.screen.blit(money_txt, (SCREEN_WIDTH//2 - money_txt.get_width()//2, 160))

        mid_x = SCREEN_WIDTH // 2
        pygame.draw.line(self.screen, (60,60,60), (mid_x, 190), (mid_x, 530), 1)

        col1_title = self.font_hud.render("--- WEAPONS ---", True, WHITE)
        col2_title = self.font_hud.render("--- VEHICLES ---", True, WHITE)
        self.screen.blit(col1_title, (mid_x//2 - col1_title.get_width()//2, 195))
        self.screen.blit(col2_title, (mid_x + mid_x//2 - col2_title.get_width()//2, 195))

        fn  = pygame.font.SysFont("Arial", 22, bold=True)
        fsb = pygame.font.SysFont("Arial", 16, bold=False)

        weapons_list = [
            ("DAGGER", "[1] Silver Dagger", "+Speed",  50, DAGGER_COLOR),
            ("FIRE",   "[2] Fire Sword",    "x2 Points & Coins",  150, SWORD_FIRE_COLOR),
            ("ICE",    "[3] Ice Sword",     "Slow Ghosts",        300, SWORD_ICE_COLOR),
            ("AXE",    "[4] Battle Axe",    "+Time Buff",         500, AXE_COLOR),
        ]
        sy = 228
        row_h = 70
        for w_id, w_name, w_desc, cost, color in weapons_list:
            is_equipped = (ps.equipped_weapon == w_id)
            is_owned    = (w_id in ps.owned_weapons)
            if is_equipped:
                bg = pygame.Surface((mid_x - 20, 62), pygame.SRCALPHA)
                bg.fill((color[0]//5, color[1]//5, color[2]//5, 140))
                self.screen.blit(bg, (10, sy - 4))
            self.screen.blit(fn.render(w_name, True, color), (20, sy))
            self.screen.blit(fsb.render(w_desc, True, (200,200,200)), (20, sy + 26))
            if is_equipped:
                st, sc = "[ EQUIPPED ]", (255,255,100)
            elif is_owned:
                st, sc = "[ OWNED ]", (150,255,150)
            else:
                st, sc = f"Cost: {cost} coins", (180,180,180)
            self.screen.blit(fsb.render(st, True, sc), (20, sy + 45))
            sy += row_h

        bikes_list = [
            ("VESPA", "[5] Vespa",      "+0.5 Speed",  400, BIKE_VESPA_COLOR),
            ("SPORT", "[6] Sport Bike", "+0.75 Speed", 800, BIKE_SPORT_COLOR),
        ]
        sy = 228
        c2 = mid_x + 10
        for b_id, b_name, b_desc, cost, color in bikes_list:
            is_riding = (ps.equipped_bike == b_id)
            is_owned  = (b_id in ps.owned_bikes)
            if is_riding:
                bg = pygame.Surface((mid_x - 20, 62), pygame.SRCALPHA)
                bg.fill((color[0]//5, color[1]//5, color[2]//5, 140))
                self.screen.blit(bg, (c2, sy - 4))
            self.screen.blit(fn.render(b_name, True, color), (c2 + 10, sy))
            self.screen.blit(fsb.render(b_desc, True, (200,200,200)), (c2 + 10, sy + 26))
            if is_riding:
                st, sc = "[ RIDING ]", (255,255,100)
            elif is_owned:
                st, sc = "[ OWNED ]", (150,255,150)
            else:
                st, sc = f"Cost: {cost} coins", (180,180,180)
            self.screen.blit(fsb.render(st, True, sc), (c2 + 10, sy + 45))
            sy += row_h

        sub = self.font_small.render("Press ESC to return Menu", True, (150,150,150))
        self.screen.blit(sub, (SCREEN_WIDTH//2 - sub.get_width()//2, 560))
 
    def draw_start_screen(self):
        """Render the animated title/character-select screen.

        Content:
            - "PACMAN" title with drop shadow and blinking BEST score.
            - Four ghost previews on the left with algorithm labels.
            - Pacman preview on the right with animated mouth.
            - Vertical divider between the two sides.
            - Control hints and shop prompt at the bottom.
            - Blinking "PRESS ANY KEY TO START" text.
        """
        self.screen.fill(BLACK)
        self.blink_title += 1

        title_shadow = self.font_title.render("PACMAN", True, (100, 100, 0))
        title        = self.font_title.render("PACMAN", True, YELLOW)
        self.screen.blit(title_shadow, (SCREEN_WIDTH//2 - title.get_width()//2 + 4, 34))
        self.screen.blit(title,        (SCREEN_WIDTH//2 - title.get_width()//2,     30))

        if self.high_score > 0:
            hs = self.font_small.render(f"BEST: {self.high_score}", True, (200, 200, 0))
            self.screen.blit(hs, (SCREEN_WIDTH//2 - hs.get_width()//2, 140))

        ghost_info = [
            ("Blinky ",  (255,   0,   0)),
            ("Pinky  ",  (255, 184, 255)),
            ("Inky   ",  (  0, 255, 255)),
            ("Clyde  ",  (255, 184,  81)),
        ]
        mid            = SCREEN_WIDTH // 2
        pac_x          = mid + 170
        ghost_center_x = mid - 170
        left_x         = ghost_center_x - 30
        name_x         = ghost_center_x + 5
        start_y        = 240
        row_h          = 60

        for i, (name, color) in enumerate(ghost_info):
            cy = start_y + i * row_h
            self._draw_ghost_preview(self.screen, left_x, cy, color, radius=20)
            text_name = self.font_small.render(name, True, color)
            self.screen.blit(text_name, (name_x, cy - text_name.get_height()//2))

        mouth_angle = 30 * abs(math.sin(self.blink_title * 0.08))
        pac_y = start_y + 1.5 * row_h
        self._draw_pacman_preview(self.screen, pac_x, pac_y, mouth_angle, radius=58)

        lbl_font   = pygame.font.SysFont("Arial", 18, bold=True)
        lbl_ghosts = lbl_font.render("GHOSTS", True, (180, 180, 180))
        lbl_pac    = lbl_font.render("PACMAN", True, (180, 180, 180))
        self.screen.blit(lbl_ghosts, (ghost_center_x - lbl_ghosts.get_width()//2, start_y - 70))
        self.screen.blit(lbl_pac,    (pac_x          - lbl_pac.get_width()//2,    start_y - 70))

        pygame.draw.line(self.screen, (60, 60, 60),
                         (mid, start_y - 60),
                         (mid, start_y + len(ghost_info) * row_h - 10), 2)

        ctrl      = self.font_hud.render("Arrow Keys / WASD to move", True, (120, 120, 120))
        shop_hint = self.font_hud.render("Press 'S' to enter Shop (Weapons & Vehicles)", True, COIN_COLOR)
        key_hint  = self.font_hud.render("Q/E/R/T = Weapon  |  Z/X = Bike  |  ESC = Menu", True, (160, 160, 80))
        self.screen.blit(ctrl,      (SCREEN_WIDTH//2 - ctrl.get_width()//2,      480))
        self.screen.blit(shop_hint, (SCREEN_WIDTH//2 - shop_hint.get_width()//2, 505))
        self.screen.blit(key_hint,  (SCREEN_WIDTH//2 - key_hint.get_width()//2,  530))

        if (self.blink_title // 30) % 2 == 0:
            start_txt = self.font_large.render("PRESS ANY KEY TO START", True, WHITE)
            self.screen.blit(start_txt, (SCREEN_WIDTH//2 - start_txt.get_width()//2, 565))

    def _draw_equip_hud(self):
        """Draw a compact equipment overlay in the top-left corner during play.

        Lists only owned weapons and bikes, one per line, showing:
            [hotkey] ItemName        in the item's colour.
            [hotkey] ItemName [ON]   with a tinted highlight row when equipped.

        The overlay is hidden entirely if the player owns nothing.
        """
        if not ps.owned_weapons and not ps.owned_bikes:
            return
        lines = []
        wmap = [
            ("DAGGER", "Q", "Dagger",   DAGGER_COLOR),
            ("FIRE",   "E", "FireSword",SWORD_FIRE_COLOR),
            ("ICE",    "R", "IceSword", SWORD_ICE_COLOR),
            ("AXE",    "T", "Axe",      AXE_COLOR),
        ]
        bmap = [
            ("VESPA",  "Z", "Vespa",    BIKE_VESPA_COLOR),
            ("SPORT",  "X", "SportBike",BIKE_SPORT_COLOR),
        ]
        for wid, key, name, color in wmap:
            if wid in ps.owned_weapons:
                equipped_mark = " [ON]" if ps.equipped_weapon == wid else ""
                lines.append((f"[{key}] {name}{equipped_mark}", color, ps.equipped_weapon == wid))
        for bid, key, name, color in bmap:
            if bid in ps.owned_bikes:
                equipped_mark = " [ON]" if ps.equipped_bike == bid else ""
                lines.append((f"[{key}] {name}{equipped_mark}", color, ps.equipped_bike == bid))
        if not lines:
            return

        pad = 5
        line_h = 17
        box_w = 140
        box_h = len(lines)*line_h + pad*2 + 2
        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        self.screen.blit(bg, (3, 3))
        for i, (txt, col, is_on) in enumerate(lines):
            if is_on:
                hl = pygame.Surface((box_w - 4, line_h), pygame.SRCALPHA)
                hl.fill((col[0]//4, col[1]//4, col[2]//4, 180))
                self.screen.blit(hl, (5, 3 + pad + i*line_h))
            s = self.font_tiny.render(txt, True, col)
            self.screen.blit(s, (3+pad+2, 3+pad + i*line_h))

    def draw(self):
        """Render the complete current frame to self.screen.

        Delegates entirely to draw_start_screen() or draw_shop() when not in
        an active play state. During play, draws in this order:
            1. Black background fill.
            2. Map (walls, dots, power pellets).
            3. Bonus items.
            4. Particles (behind entities).
            5. Ghosts.
            6. Pacman.
            7. Floating texts.
            8. Equipment HUD overlay (top-left).
            9. HUD bar: score, coins, level, lives (pacman icons), ESC hint.
           10. Best score badge (top-right corner).
           11. Frightened timer bar (thin coloured strip above HUD).
           12. State overlays: READY! banner, GAME OVER screen, or YOU WIN! screen.
        """
        if self.state == "START":
            self.draw_start_screen()
            return
        if self.state == "SHOP":
            self.draw_shop()
            return

        self.screen.fill(BLACK)
        self.map.draw(self.screen)

        for bi in self.bonus_items:
            bi.draw(self.screen)

        for pt in self.particles:
            pt.draw(self.screen)

        for ghost in self.ghosts:
            ghost.draw(self.screen, self.frightened_timer)

        self.pacman.draw(self.screen, is_powered=(self.frightened_timer > 0))

        for ft in self.floats:
            ft.draw(self.screen)

        self._draw_equip_hud()

        hud_y = MAP_ROWS * TILE_SIZE
        pygame.draw.rect(self.screen, HUD_BG, (0, hud_y, SCREEN_WIDTH, 80))

        score_txt = self.font_hud.render(f"SCORE: {self.score}", True, WHITE)
        coin_txt  = self.font_hud.render(f"COINS: {ps.player_coins}", True, COIN_COLOR)
        level_txt = self.font_hud.render(f"LEVEL: {self.level}", True, (100, 200, 255))

        self.screen.blit(score_txt, (10,  hud_y + 10))
        self.screen.blit(coin_txt,  (150, hud_y + 10))
        self.screen.blit(level_txt, (SCREEN_WIDTH//2 - level_txt.get_width()//2, hud_y + 10))

        for i in range(self.lives):
            lx = SCREEN_WIDTH - 40 - i * 30
            ly = hud_y + 20
            pygame.draw.circle(self.screen, YELLOW, (lx, ly), 10)
            pygame.draw.polygon(self.screen, BLACK, [(lx, ly), (lx+12, ly-6), (lx+12, ly+6)])
        esc_hint = self.font_tiny.render("ESC = Menu", True, (70,70,70))
        self.screen.blit(esc_hint, (10, hud_y + 58))
        hs_surf = self.font_tiny.render(f"BEST: {self.high_score}", True, (220, 200, 0))
        self.screen.blit(hs_surf, (SCREEN_WIDTH - hs_surf.get_width() - 6, 4))
        if self.frightened_timer > 0:
            bar_w = int(SCREEN_WIDTH * self.frightened_timer / 600)
            bar_color = (0, 80, 255) if (self.frightened_timer//15)%2==0 else (180,180,255)
            pygame.draw.rect(self.screen, (0,0,80), (0, hud_y-6, SCREEN_WIDTH, 6))
            pygame.draw.rect(self.screen, bar_color, (0, hud_y-6, bar_w, 6))

        if self.state == "READY_WAIT":
            ready_txt = self.font_large.render("READY!", True, YELLOW)
            self.screen.blit(ready_txt, (SCREEN_WIDTH//2 - ready_txt.get_width()//2, 330))
            esc_txt = self.font_hud.render("ESC to return Menu", True, (150,150,150))
            self.screen.blit(esc_txt, (SCREEN_WIDTH//2 - esc_txt.get_width()//2, 390))

        elif self.state == "GAMEOVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            text = self.font_title.render("GAME OVER", True, (255,0,0))
            shadow = self.font_title.render("GAME OVER", True, (100,0,0))
            self.screen.blit(shadow, (SCREEN_WIDTH//2 - text.get_width()//2 + 4, 224))
            self.screen.blit(text,   (SCREEN_WIDTH//2 - text.get_width()//2,     220))
            hs_line = self.font_small.render(f"High Score: {self.high_score}", True, COIN_COLOR)
            sc_line = self.font_small.render(f"Your Score: {self.score}", True, YELLOW)
            sub     = self.font_small.render("Press ANY KEY to return Menu", True, WHITE)
            self.screen.blit(hs_line, (SCREEN_WIDTH//2 - hs_line.get_width()//2, 330))
            self.screen.blit(sc_line, (SCREEN_WIDTH//2 - sc_line.get_width()//2, 365))
            self.screen.blit(sub,     (SCREEN_WIDTH//2 - sub.get_width()//2,     420))

        elif self.state == "WIN":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            text = self.font_title.render("YOU WIN!", True, (0,255,0))
            shadow = self.font_title.render("YOU WIN!", True, (0,100,0))
            self.screen.blit(shadow, (SCREEN_WIDTH//2 - text.get_width()//2 + 4, 224))
            self.screen.blit(text,   (SCREEN_WIDTH//2 - text.get_width()//2,     220))
            hs_line = self.font_small.render(f"High Score: {self.high_score}", True, COIN_COLOR)
            sc_line = self.font_small.render(f"Your Score: {self.score}", True, YELLOW)
            sub     = self.font_small.render("Press ANY KEY to return Menu", True, WHITE)
            self.screen.blit(hs_line, (SCREEN_WIDTH//2 - hs_line.get_width()//2, 330))
            self.screen.blit(sc_line, (SCREEN_WIDTH//2 - sc_line.get_width()//2, 365))
            self.screen.blit(sub,     (SCREEN_WIDTH//2 - sub.get_width()//2,     420))