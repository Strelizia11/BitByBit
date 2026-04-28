import pygame
import os
import sys

# ── Palette ──────────────────────────────────────────────────────────────────
BLACK       = (0,   0,   0)
NEAR_BLACK  = (10,  10,  10)
DARK_GRAY   = (25,  25,  25)
MID_GRAY    = (60,  60,  60)
DIM_WHITE   = (160, 160, 160)
WHITE       = (230, 230, 230)
PURE_WHITE  = (255, 255, 255)

AMBER       = (200, 160,  30)
AMBER_DIM   = (100,  80,  15)
BLOOD_RED   = (160,  20,  20)
DARK_RED    = ( 80,  10,  10)
STEEL_BLUE  = ( 40,  70, 130)
STEEL_DIM   = ( 20,  35,  65)
GREEN_DIM   = ( 40,  90,  40)
GREEN_BRIGHT= ( 80, 180,  80)


SCREEN_W, SCREEN_H = pygame.display.get_surface().get_size() if pygame.display.get_surface() else (800, 600)
CX, CY = SCREEN_W // 2, SCREEN_H // 2

# ── Font loader ───────────────────────────────────────────────────────────────
_font_cache: dict = {}
_font_cache_secondary: dict = {}

def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Primary font for menu and UI elements"""
    key = (size, bold)
    if key not in _font_cache:
        font_path = resource_path("assets/fonts/arial.ttf")  # Path to your font file
        if os.path.exists(font_path):
            _font_cache[key] = pygame.font.Font(font_path, size)
        else:
            # Fallback to system font if custom font not found
            _font_cache[key] = pygame.font.SysFont("arial", size, bold=bold)
    return _font_cache[key]

def get_font_secondary(size: int, bold: bool = False) -> pygame.font.Font:
    """Secondary font for body text and alternative UI"""
    key = (size, bold)
    if key not in _font_cache_secondary:
        font_path = resource_path("assets/fonts/horroroid.ttf")  # Change to a different font if desired
        if os.path.exists(font_path):
            _font_cache_secondary[key] = pygame.font.Font(font_path, size)
        else:
            # Fallback to system font if custom font not found
            _font_cache_secondary[key] = pygame.font.SysFont("courier", size, bold=bold)
    return _font_cache_secondary[key]

# ── Drawing helpers ───────────────────────────────────────────────────────────
def draw_text(surface, text, size, color, cx, cy, bold=False, alpha=255):
    font = get_font(size, bold)
    img = font.render(text, True, color)
    if alpha < 255:
        img.set_alpha(alpha)
    r = img.get_rect(center=(cx, cy))
    surface.blit(img, r)
    return r

def draw_text_left(surface, text, size, color, x, y, bold=False):
    font = get_font(size, bold)
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_rect_border(surface, color, rect, width=1, radius=6):
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)

def draw_rect_filled(surface, color, rect, radius=6):
    pygame.draw.rect(surface, color, rect, border_radius=radius)




def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)