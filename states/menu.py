import pygame
from PIL import Image
from states.base import BaseState
from utils import (
    NEAR_BLACK, SCREEN_W, SCREEN_H, get_font_secondary
)

# ── Typography ────────────────────────────────────────────────────────────────
SIZE_NORMAL  = 100                   # non-hovered font size (slightly smaller for contrast)
SIZE_HOVERED = 180                   # hovered font size (bold, large)
COL_NORMAL   = (55, 55, 55)         # very dim — makes hover contrast dramatic
COL_HOVERED  = (210, 30, 30)        # blood red — horror-thematic pop

# ── Layout ────────────────────────────────────────────────────────────────────
MENU_X        = 130                  # left edge of all labels
MENU_TOP_FRAC = 0.53                # top of menu block as fraction of screen height
ROW_H         = int(SCREEN_H * 0.13)  # fixed row height / spacing (~84 px at 600p)

# ── Animation ─────────────────────────────────────────────────────────────────
HOVER_SPEED    = 12.0               # lerp speed on hover
SCANLINE_ALPHA = 18                 # scanline darkness

# ── Effects ───────────────────────────────────────────────────────────────────
SHADOW_OFFSET  = 5                  # px offset for drop shadow
SHADOW_COL     = (80, 0, 0)         # dark red shadow (only visible on hover)
INDICATOR      = "›"                # sliding hover indicator character
INDICATOR_GAP  = 10                 # gap between indicator and text


class MenuState(BaseState):
    MENU_ITEMS = [
        ("START",    "disclaimer"),
        ("CREDITS", "credits"),
        ("LEAVE",    "quit"),
    ]

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def on_enter(self, **kwargs):
        self.time    = 0.0
        self.fade_in = 0.0
        self.hovered = -1

        # Per-item smooth lerp: 0.0 = normal, 1.0 = hovered
        self.hover_t = [0.0] * len(self.MENU_ITEMS)

        # Hit rects rebuilt each frame
        self.item_rects = [pygame.Rect(0, 0, 1, 1)] * len(self.MENU_ITEMS)

        # GIF
        self.gif_frames      = []
        self.frame_durations = []
        self.current_frame   = 0
        self.frame_timer     = 0.0
        self._load_gif("assets/GameMenu.gif")

        # Scanlines (pre-built once)
        self._scanlines = self._build_scanlines(SCREEN_W, SCREEN_H)

        # Cursor
        try:
            self._cur_hand  = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND)
            self._cur_arrow = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)
        except Exception:
            self._cur_hand = self._cur_arrow = None
        if self._cur_arrow:
            pygame.mouse.set_cursor(self._cur_arrow)
        self._is_hand = False

        # Credits mode
        self.credits_mode = False

    def _load_gif(self, path):
        try:
            with Image.open(path) as gif:
                canvas = Image.new("RGBA", gif.size, (0, 0, 0, 255))
                for frame in range(gif.n_frames):
                    gif.seek(frame)
                    frame_rgba = gif.convert("RGBA")
                    canvas.paste(frame_rgba, (0, 0), frame_rgba)
                    surf = pygame.image.fromstring(
                        canvas.tobytes(), canvas.size, "RGBA"
                    ).convert()
                    self.gif_frames.append(
                        pygame.transform.scale(surf, (SCREEN_W, SCREEN_H))
                    )
                    dur = gif.info.get("duration", 100) / 1000.0
                    self.frame_durations.append(max(0.05, dur))
        except Exception as e:
            print(f"[Menu] GIF load failed: {e}")

    @staticmethod
    def _build_scanlines(w, h):
        sl = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 4):
            pygame.draw.line(sl, (0, 0, 0, SCANLINE_ALPHA), (0, y), (w, y))
        return sl

    # ── Events ────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if self.credits_mode:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self.credits_mode = False
            return  # Block menu interaction when in credits mode

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = next(
                (i for i, r in enumerate(self.item_rects)
                 if r.collidepoint(mx, my)), -1
            )
            self._sync_cursor()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered >= 0:
                self._activate(self.MENU_ITEMS[self.hovered][1])

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.switch_state("disclaimer")
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

    def _activate(self, target):
        if target == "quit":
            self.game.running = False
        elif target == "credits":
            self.credits_mode = True
        elif target:
            self.game.switch_state(target)

    def _sync_cursor(self):
        if not self._cur_hand:
            return
        if self.hovered >= 0 and not self._is_hand:
            pygame.mouse.set_cursor(self._cur_hand)
            self._is_hand = True
        elif self.hovered < 0 and self._is_hand:
            pygame.mouse.set_cursor(self._cur_arrow)
            self._is_hand = False

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, dt):
        self.time    += dt
        self.fade_in  = min(1.0, self.fade_in + dt * 1.6)

        k = min(HOVER_SPEED * dt, 1.0)
        for i in range(len(self.MENU_ITEMS)):
            target = 1.0 if self.hovered == i else 0.0
            self.hover_t[i] += (target - self.hover_t[i]) * k

        if self.gif_frames:
            self.frame_timer += dt
            dur = self.frame_durations[self.current_frame]
            if self.frame_timer >= dur:
                self.frame_timer -= dur
                self.current_frame = (self.current_frame + 1) % len(self.gif_frames)

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        # 1. GIF background
        if self.gif_frames:
            surface.blit(self.gif_frames[self.current_frame], (0, 0))
        else:
            surface.fill(NEAR_BLACK)

        # 2. Scanlines overlay
        surface.blit(self._scanlines, (0, 0))

        # 3. Menu items or credits
        alpha = int(self.fade_in * 255)

        if self.credits_mode:
            self._draw_credits_content(surface, alpha)
        else:
            self._draw_menu_items(surface, alpha)

    def _draw_menu_items(self, surface, alpha):
        menu_top = int(SCREEN_H * MENU_TOP_FRAC)

        # How much is the "most hovered" item — used to shrink others
        max_t = max(self.hover_t)

        for i, (label, _) in enumerate(self.MENU_ITEMS):
            t = self.hover_t[i]

            # Shrink inactive items when another is hovered
            shrink = 1.0
            if max_t > 0.25 and t < 0.1:
                shrink = 0.82 + 0.18 * (1.0 - max_t)   # lerps 0.82→1.0 as hover fades

            size = int((SIZE_NORMAL + (SIZE_HOVERED - SIZE_NORMAL) * t) * shrink)
            bold = t > 0.3
            col  = _lerp_color(COL_NORMAL, COL_HOVERED, t)

            font = get_font_secondary(size, bold=bold)

            # ── Centre text vertically in its row ─────────────────────────
            row_top    = menu_top + i * ROW_H
            row_centre = row_top + ROW_H // 2

            # ── 1. Shadow pass (offset, dark-red, fades in with hover) ───
            if t > 0.05:
                shadow_surf = font.render(label, True, SHADOW_COL)
                shadow_surf.set_alpha(int(alpha * t * 0.65))
                shadow_y = row_centre - shadow_surf.get_height() // 2
                surface.blit(shadow_surf, (MENU_X + SHADOW_OFFSET, shadow_y + SHADOW_OFFSET))

            # ── 2. Main text ──────────────────────────────────────────────
            img = font.render(label, True, col)
            y   = row_centre - img.get_height() // 2

            if alpha < 255:
                img.set_alpha(alpha)
            surface.blit(img, (MENU_X, y))

            # ── 3. Sliding › indicator (enters from the left) ─────────────
            if t > 0.02:
                ind_font = get_font_secondary(size, bold=bold)
                ind_surf = ind_font.render(INDICATOR, True, COL_HOVERED)
                ind_w    = ind_surf.get_width()
                # Slides from off-screen-left into position as t→1
                ind_target_x = MENU_X - ind_w - INDICATOR_GAP
                ind_x = int(ind_target_x * t + (ind_target_x - 60) * (1.0 - t))
                ind_surf.set_alpha(int(alpha * t))
                ind_y = row_centre - ind_surf.get_height() // 2
                surface.blit(ind_surf, (ind_x, ind_y))

            

            # ── 4. Hit rect (generous, full row height) ───────────────────
            self.item_rects[i] = pygame.Rect(
                MENU_X, row_top,
                img.get_width() + 20, ROW_H
            )

    def _draw_credits_content(self, surface, alpha):
        container_w, container_h = 700, 500
        container_x = (SCREEN_W - container_w) // 2
        container_y = (SCREEN_H - container_h) // 2
        container_rect = pygame.Rect(container_x, container_y, container_w, container_h)

        pygame.draw.rect(surface, NEAR_BLACK, container_rect, border_radius=20)
        pygame.draw.rect(surface, (100, 100, 100), container_rect, 2, border_radius=20)

        from utils import draw_text
        draw_text(surface, "CREDITS", 60, (200, 200, 200), container_x + container_w // 2, container_y + 50)

        credits_lines = [
            "Game Development: BitByBit Team",
            "Art and Design: Creative Minds",
            "Music and Sound: Audio Wizards",
            "Special Thanks: Open Source Community",
            "",
            "Click or press any key to return to menu"
        ]

        y_offset = container_y + 120
        for line in credits_lines:
            draw_text(surface, line, 28, (180, 180, 180), container_x + container_w // 2, y_offset)
            y_offset += 40


# ── Helpers ───────────────────────────────────────────────────────────────────
def _lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))