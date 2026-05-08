"""
Global constants for the Pacman Arcade game.

Defines tile dimensions, screen resolution, frame rate, file paths,
colour palettes, and equipment colour codes used across the entire project.

Tile encoding used in level matrices:
    0 = walkable path  (dot spawns here)
    1 = wall
    2 = open corridor  (no dot)
    3 = ghost pen interior
    4 = power pellet tile
"""
TILE_SIZE = 30
MAP_COLS = 28
MAP_ROWS = 21
SCREEN_WIDTH = TILE_SIZE * MAP_COLS
SCREEN_HEIGHT = TILE_SIZE * MAP_ROWS + 80
FPS = 60
HIGH_SCORE_FILE = "highscore.json"

# --- COLORS ---
BLACK        = (0, 0, 0)
WHITE        = (255, 255, 255)
YELLOW       = (255, 255, 0)
DOT_COLOR    = (255, 184, 174)
SCARED_COLOR = (0, 50, 255)
SCARED_FLASH = (200, 200, 255)
HUD_BG       = (15, 15, 15)

# === SHOP AND EQUIPMENT SYSTEM ===
DAGGER_COLOR     = (192, 192, 192)
SWORD_FIRE_COLOR = (255, 69, 0)
SWORD_ICE_COLOR  = (0, 255, 255)
AXE_COLOR        = (255, 100, 100)
COIN_COLOR       = (255, 215, 0)

BIKE_VESPA_COLOR = (0, 200, 255)
BIKE_SPORT_COLOR = (50, 255, 50)

MAP_COLORS = [(33, 33, 255), (33, 255, 33), (255, 33, 255)]
