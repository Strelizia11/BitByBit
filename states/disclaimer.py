import pygame
import math
import random
from states.base import BaseState
from utils import (
    draw_text,
    NEAR_BLACK, DARK_GRAY, MID_GRAY, DIM_WHITE, WHITE,
    BLOOD_RED, AMBER, AMBER_DIM, BLACK,
    SCREEN_W, SCREEN_H, CX, CY, get_font
)

# ── All layout derived from screen size at import time ────────────────────────
#    (utils.py resolves SCREEN_W/H after pygame.display.set_mode, so these
#     are the real fullscreen dimensions — same guarantee as game.py / menu.py)

SCALE        = SCREEN_H / 600          # 1.0 at 600p → 1.8 at 1080p, etc.

# Typography — scale with SCREEN_H so text fills the screen
SZ_TITLE     = max(18, int(28 * SCALE))
SZ_BODY      = max(14, int(22 * SCALE))
SZ_BODY_SM   = max(13, int(20 * SCALE))
SZ_HINT      = max(11, int(16 * SCALE))
SZ_ESC       = max(10, int(14 * SCALE))
SZ_CORNER    = max(14, int(20 * SCALE))

# Vertical layout — expressed as fractions of SCREEN_H
TITLE_Y      = int(SCREEN_H * 0.07)
BODY_START_Y = int(SCREEN_H * 0.14)
LINE_H       = int(SCREEN_H * 0.048)
BTN_Y        = int(SCREEN_H * 0.83)
BTN_W        = int(SCREEN_W * 0.18)
BTN_H        = int(SCREEN_H * 0.07)
HINT_Y       = int(SCREEN_H * 0.82)
ESC_Y        = int(SCREEN_H * 0.94)

# Horizontal accent bar
BAR_X        = int(CX - SCREEN_W * 0.22)

# Corner ornament inset
CORNER_PAD   = int(SCREEN_W * 0.012)


# ── Flicker helper ────────────────────────────────────────────────────────────
def _flicker(t, seed=0.0):
    return 0.85 + 0.15 * abs(
        math.sin(t * 7.3 + seed) * math.sin(t * 13.1 + seed * 2.7)
    )


# ── Disclaimer lines ──────────────────────────────────────────────────────────
DISCLAIMER_LINES = [
    "",
    "This game is designed to unsettle you.",
    "",
    "You will receive instructions.",
    "Some are true.  Some are traps.",
    "The lights will lie.",
    "Your instincts may betray you.",
    "",
    "There are no second chances",
    "once the time runs out.",
    "",
    "Proceed only if you trust",
    "your own judgment.",
]


class DisclaimerState(BaseState):
    REVEAL_SPEED = 18
    LINE_DELAY   = 0.18

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def on_enter(self, **kwargs):
        self.time      = 0.0
        self.fade_in   = 0.0
        self.char_idx  = 0.0
        self.done      = False
        self.hovered   = False

        self.line_chars = [len(l) if l else 0 for l in DISCLAIMER_LINES]
        total = sum(self.line_chars) + len(DISCLAIMER_LINES) * 2
        self.total_chars = total

        self.btn_rect = pygame.Rect(CX - BTN_W // 2, BTN_Y, BTN_W, BTN_H)

        self.cracks     = self._gen_cracks(18)
        self._scanlines = self._build_scanlines()
        self._vignette  = self._build_vignette()

        rng = random.Random(42)
        self._specks = [
            (rng.randint(0, SCREEN_W), rng.randint(0, SCREEN_H),
             rng.uniform(0.4, 1.0), rng.uniform(0, math.pi * 2))
            for _ in range(120)
        ]

    # ── Static builders ───────────────────────────────────────────────────────
    @staticmethod
    def _gen_cracks(n):
        rng    = random.Random(99)
        margin = int(SCREEN_H * 0.10)
        cracks = []
        for _ in range(n):
            side = rng.randint(0, 3)
            if side == 0:
                x, y = rng.randint(0, SCREEN_W), rng.randint(0, margin)
            elif side == 1:
                x, y = rng.randint(0, SCREEN_W), rng.randint(SCREEN_H - margin, SCREEN_H)
            elif side == 2:
                x, y = rng.randint(0, margin), rng.randint(0, SCREEN_H)
            else:
                x, y = rng.randint(SCREEN_W - margin, SCREEN_W), rng.randint(0, SCREEN_H)

            segs  = []
            cx2, cy2 = float(x), float(y)
            angle = rng.uniform(0, math.pi * 2)
            seg_len = int(40 * SCALE)
            for _ in range(rng.randint(3, 8)):
                length = rng.uniform(seg_len * 0.5, seg_len * 1.3)
                angle += rng.uniform(-0.6, 0.6)
                nx = cx2 + math.cos(angle) * length
                ny = cy2 + math.sin(angle) * length
                segs.append(((int(cx2), int(cy2)), (int(nx), int(ny))))
                cx2, cy2 = nx, ny
            cracks.append(segs)
        return cracks

    @staticmethod
    def _build_scanlines():
        sl   = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        step = max(2, int(3 * SCALE))
        for y in range(0, SCREEN_H, step):
            pygame.draw.line(sl, (0, 0, 0, 22), (0, y), (SCREEN_W, y))
        return sl

    @staticmethod
    def _build_vignette():
        vig   = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        max_r  = int(math.hypot(cx, cy)) + 10
        for i in range(32, 0, -1):
            frac  = i / 32
            r     = int(max_r * frac)
            alpha = int((1.0 - frac) ** 2.2 * 210)
            pygame.draw.circle(vig, (0, 0, 0, alpha), (cx, cy), r)
        return vig

    # ── Events ────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.btn_rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.done:
                self.char_idx = float(self.total_chars)
                self.done = True
            elif self.hovered:
                self.game.switch_state("mechanics")

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if not self.done:
                    self.char_idx = float(self.total_chars)
                    self.done = True
                else:
                    self.game.switch_state("mechanics")
            if event.key == pygame.K_ESCAPE:
                self.game.switch_state("menu")

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, dt):
        self.time    += dt
        self.fade_in  = min(1.0, self.fade_in + dt * 1.4)
        if not self.done:
            self.char_idx += self.REVEAL_SPEED * dt
            if self.char_idx >= self.total_chars:
                self.char_idx = float(self.total_chars)
                self.done = True

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        surface.fill((6, 4, 4))

        self._draw_specks(surface)
        self._draw_cracks(surface)
        surface.blit(self._vignette, (0, 0))
        surface.blit(self._scanlines, (0, 0))

        global_alpha = int(self.fade_in * 255)

        self._draw_corners(surface, global_alpha)
        self._draw_title(surface, global_alpha)
        self._draw_body(surface, global_alpha)
        

        if self.done:
            self._draw_button(surface, global_alpha)
        else:
            self._draw_hint(surface, global_alpha)

        draw_text(surface, "ESC — back to menu", SZ_ESC, MID_GRAY,
                  CX, ESC_Y, alpha=global_alpha)

    # ── Sub-draw helpers ──────────────────────────────────────────────────────
    def _draw_specks(self, surface):
        t = self.time
        for sx, sy, intensity, phase in self._specks:
            v = _flicker(t * 0.6, phase)
            a = int(v * intensity * 28)
            if a > 0:
                pygame.draw.circle(surface, (a, a // 2, a // 2), (sx, sy), 1)

    def _draw_cracks(self, surface):
        alpha = int(self.fade_in * 80)
        if alpha <= 0:
            return
        crack_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for crack in self.cracks:
            flk = _flicker(self.time * 0.4, id(crack) % 100 * 0.1)
            col = (int(120 * flk), int(8 * flk), int(8 * flk), alpha)
            for seg in crack:
                pygame.draw.line(crack_surf, col, seg[0], seg[1], 1)
        surface.blit(crack_surf, (0, 0))

    def _draw_corners(self, surface, alpha):
        if alpha < 10:
            return
        font      = get_font(SZ_CORNER, bold=True)
        flicker_a = int(_flicker(self.time, 3.3) * alpha * 0.6)
        p         = CORNER_PAD
        positions = [
            (p, p, False, False),
            (SCREEN_W - p, p, True, False),
            (p, SCREEN_H - p, False, True),
            (SCREEN_W - p, SCREEN_H - p, True, True),
        ]
        for cx2, cy2, flip_x, flip_y in positions:
            img = font.render("✦", True, BLOOD_RED)
            img.set_alpha(flicker_a)
            rx = cx2 - img.get_width()  if flip_x else cx2
            ry = cy2 - img.get_height() if flip_y else cy2
            surface.blit(img, (rx, ry))

    def _draw_title(self, surface, alpha):
        flk        = _flicker(self.time, 1.1)
        title_col  = (int(BLOOD_RED[0]*flk), int(BLOOD_RED[1]*flk), int(BLOOD_RED[2]*flk))
        title_font = get_font(SZ_TITLE, bold=True)
        title_img  = title_font.render(" DISCLAIMER ", True, title_col)
        title_img.set_alpha(alpha)
        surface.blit(title_img, (CX - title_img.get_width() // 2, TITLE_Y))

        # Flickering red lines on both sides of the title
        line_a   = int(_flicker(self.time * 1.3, 5.5) * alpha * 0.7)
        line_h   = max(1, int(2 * SCALE))
        gap      = int(12 * SCALE)
        line_len = int(SCREEN_W * 0.12)
        mid_y    = TITLE_Y + title_img.get_height() // 2 - line_h // 2
        half_w   = title_img.get_width() // 2

        for lx in [CX - half_w - gap - line_len, CX + half_w + gap]:
            seg = pygame.Surface((line_len, line_h), pygame.SRCALPHA)
            seg.fill((*BLOOD_RED, line_a))
            surface.blit(seg, (lx, mid_y))

    def _draw_body(self, surface, global_alpha):
        remaining = int(self.char_idx)

        for i, line in enumerate(DISCLAIMER_LINES):
            y = BODY_START_Y + i * LINE_H
            if not line:
                remaining = max(0, remaining - 2)
                continue
            shown = min(len(line), remaining)
            remaining = max(0, remaining - len(line) - 2)
            if shown <= 0:
                break

            is_final = line.strip().startswith("...")
            is_key   = any(k in line for k in ("lie", "betray", "traps", "no second"))

            if is_final:
                color = BLOOD_RED
                font  = get_font(SZ_BODY, bold=True)
            elif is_key:
                color = (180, 90, 90)
                font  = get_font(SZ_BODY_SM)
            else:
                color = DIM_WHITE
                font  = get_font(SZ_BODY_SM)

            txt = line[:shown]
            img = font.render(txt, True, color)

            base_alpha = global_alpha
            if shown < len(line):
                blink      = 255 if int(self.time * 6) % 2 == 0 else 160
                base_alpha = min(global_alpha, blink)

            img.set_alpha(base_alpha)
            surface.blit(img, (CX - img.get_width() // 2, y))

            # Typing cursor on active line
            if shown < len(line) and int(self.time * 5) % 2 == 0:
                cursor_x = CX - img.get_width() // 2 + img.get_width() + 2
                cursor_w = max(2, int(2 * SCALE))
                cursor_h = img.get_height() - int(4 * SCALE)
                pygame.draw.rect(surface, BLOOD_RED,
                                 (cursor_x, y + int(2 * SCALE), cursor_w, cursor_h))

    def _draw_button(self, surface, alpha):
        r = self.btn_rect

        if self.hovered:
            glow = pygame.Surface((r.w + 40, r.h + 40), pygame.SRCALPHA)
            for gi in range(14, 0, -1):
                ga = int((gi / 14) * 45)
                pygame.draw.rect(glow, (160, 20, 20, ga),
                                 (20 - gi, 20 - gi, r.w + gi * 2, r.h + gi * 2),
                                 border_radius=6 + gi)
            surface.blit(glow, (r.x - 20, r.y - 20))

        bg_col  = (25, 8, 8)     if self.hovered else (10, 4, 4)
        brd_col = BLOOD_RED       if self.hovered else (80, 20, 20)
        txt_col = (230, 200, 200) if self.hovered else (160, 100, 100)
        brd_w   = max(1, int(2 * SCALE)) if self.hovered else 1

        pygame.draw.rect(surface, bg_col, r, border_radius=4)
        pygame.draw.rect(surface, brd_col, r, brd_w, border_radius=4)

        if self.hovered:
            scan_y    = r.y + int((self.time * 60) % r.h)
            scan_h    = max(1, int(2 * SCALE))
            scan_surf = pygame.Surface((r.w, scan_h), pygame.SRCALPHA)
            scan_surf.fill((200, 50, 50, 30))
            surface.blit(scan_surf, (r.x, scan_y))

        lbl_flk  = _flicker(self.time * 2.0, 9.9) if self.hovered else 1.0
        lbl_col  = tuple(int(c * lbl_flk) for c in txt_col)
        lbl_font = get_font(SZ_BODY_SM, bold=self.hovered)
        lbl_img  = lbl_font.render("I UNDERSTAND", True, lbl_col)
        lbl_img.set_alpha(alpha)
        surface.blit(lbl_img, lbl_img.get_rect(center=r.center))

    def _draw_hint(self, surface, alpha):
        hint_a   = int(_flicker(self.time * 2.5, 2.2) * alpha * 0.55)
        hint_img = get_font(SZ_HINT).render("CLICK or SPACE to reveal", True, MID_GRAY)
        hint_img.set_alpha(hint_a)
        surface.blit(hint_img, hint_img.get_rect(center=(CX, HINT_Y)))