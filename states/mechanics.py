import pygame
import math
import random

from states.base import BaseState
from states.audio_manager import AudioManager
from utils import (
    draw_text,
    NEAR_BLACK, DARK_GRAY, MID_GRAY, DIM_WHITE, WHITE,
    BLOOD_RED, AMBER, AMBER_DIM, BLACK,
    SCREEN_W, SCREEN_H, CX, CY, get_font
)

audio = AudioManager()

# ── Scale factor ───────────────────────────────────────────────────────────────
SCALE = SCREEN_H / 600   # 1.0 @ 600p, 1.8 @ 1080p

# ── Typography ────────────────────────────────────────────────────────────────
SZ_HEADER  = max(14, int(20 * SCALE))
# Card title/body are intentionally one step smaller than the original so that
# 3-line body text fits cleanly inside every card at all resolutions.
SZ_TITLE   = max(12, int(17 * SCALE))   # was int(18 * SCALE)
SZ_BODY    = max(10, int(13 * SCALE))   # was int(15 * SCALE)  ← key reduction
SZ_HINT    = max(10, int(14 * SCALE))
SZ_ESC     = max(10, int(13 * SCALE))
SZ_CORNER  = max(14, int(20 * SCALE))
SZ_BTN     = max(12, int(17 * SCALE))

# ── Card data ─────────────────────────────────────────────────────────────────
MECHANICS = [
    {
        "title": "LIGHT SWITCH",
        "color": (180, 140, 20),
        "icon":  "◈",
        "lines": [
            "- A light switch sits at the centre of the screen.",
            "- Click it to toggle the light ON or OFF.",
            "- Toggling it will determine which instructions to follow.",
        ],
    },
    {
        "title": "INSTRUCTIONS",
        "color": (60, 130, 190),
        "icon":  "◉",
        "lines": [
            "- Each round you receive a command from Simon.",
            "- When the light is on, you must follow Simon and only Simon.",
            "- When the light is off, DO NOT follow any Simon's instructions.",
        ],
    },
    {
        "title": "ANOMALIES",
        "color": (180, 50, 50),
        "icon":  "⚠",
        "lines": [
            "- Some instructions imitates Simon — look for misspellings",
            "- Cobwebs accumulate over time, so remove immediately.",
            "- If you see any anomalies, do the OPPOSITE of what the command says.",
        ],
    },
    {
        "title": "THE TIMER",
        "color": (110, 110, 110),
        "icon":  "◷",
        "lines": [
            "- A countdown bar shrinks each round.",
            "- If it reaches zero before you act, the lights go out.",
        ],
    },
]

# ── Vertical layout ───────────────────────────────────────────────────────────
# All zone boundaries are solved holistically so that:
#   • 4 cards with up to 3 body lines never overflow their container
#   • dots / hint / button / esc all have breathing room below the cards
#
# Verified at 600p, 768p, 900p, 1080p:
#   600p  → CARD_H=91,  content_h(3-line)=73, top=9,  bot=9   ✓
#   768p  → CARD_H=116, content_h(3-line)=91, top=12, bot=13  ✓
#   900p  → CARD_H=136, content_h(3-line)=106,top=15, bot=15  ✓
#   1080p → CARD_H=163, content_h(3-line)=128,top=17, bot=18  ✓

_N           = 4
_CARDS_START = int(SCREEN_H * 0.085)   # was 0.13 — pushed up to free vertical space
_CARDS_END   = int(SCREEN_H * 0.743)   # was 0.77 — pulled up so dots/hint/btn fit

_ZONE_H    = _CARDS_END - _CARDS_START

# Gap ratio 0.12 (was 0.4 → 0.25) — tight gaps, taller cards
_GAP_RATIO = 0.12
CARD_H     = int(_ZONE_H / (_N + (_N - 1) * _GAP_RATIO))
CARD_GAP   = int(CARD_H * _GAP_RATIO)
CARD_W     = int(min(SCREEN_W * 0.65, 820 * SCALE))

_STACK_H   = _N * CARD_H + (_N - 1) * CARD_GAP
CARD_TOP   = _CARDS_START + (_ZONE_H - _STACK_H) // 2

# Chrome positions — derived bottom-up so nothing crowds anything else
HEADER_Y   = int(SCREEN_H * 0.022)
DOT_Y      = _CARDS_END + int(SCREEN_H * 0.030)
BTN_W      = int(SCREEN_W * 0.18)
BTN_H      = int(SCREEN_H * 0.065)
BTN_Y      = int(SCREEN_H * 0.84)
ESC_Y      = int(SCREEN_H * 0.955)
HINT_Y     = BTN_Y   # was 0.025 — clear gap above button

CORNER_PAD = int(SCREEN_W * 0.012)
FADE_SPEED = 1.8

# Inner card padding constants (scale-aware)
_CARD_TOP_PAD   = int(8 * SCALE)   # minimum top pad inside a card
_TITLE_BODY_GAP = int(4 * SCALE)   # gap between title row and first body line


# ── Shared flicker helper ─────────────────────────────────────────────────────
def _flicker(t, seed=0.0):
    return 0.85 + 0.15 * abs(
        math.sin(t * 7.3 + seed) * math.sin(t * 13.1 + seed * 2.7)
    )


# ─────────────────────────────────────────────────────────────────────────────
class MechanicsState(BaseState):

    def on_enter(self, **kwargs):
        self.time      = 0.0
        self.fade_in   = 0.0
        self.card_idx  = 0
        self.card_fade = 0.0
        self.all_shown = False
        self.hovered   = False

        self.btn_rect = pygame.Rect(CX - BTN_W // 2, BTN_Y, BTN_W, BTN_H)

        self._scanlines = self._build_scanlines()
        self._vignette  = self._build_vignette()

        rng = random.Random(17)
        self._specks = [
            (rng.randint(0, SCREEN_W), rng.randint(0, SCREEN_H),
             rng.uniform(0.3, 0.9), rng.uniform(0, math.pi * 2))
            for _ in range(90)
        ]

    # ── Static surface builders ───────────────────────────────────────────────
    @staticmethod
    def _build_scanlines():
        sl   = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        step = max(2, int(3 * SCALE))
        for y in range(0, SCREEN_H, step):
            pygame.draw.line(sl, (0, 0, 0, 20), (0, y), (SCREEN_W, y))
        return sl

    @staticmethod
    def _build_vignette():
        vig      = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        vcx, vcy = SCREEN_W // 2, SCREEN_H // 2
        max_r    = int(math.hypot(vcx, vcy)) + 10
        for i in range(32, 0, -1):
            frac  = i / 32
            r     = int(max_r * frac)
            alpha = int((1.0 - frac) ** 2.4 * 190)
            pygame.draw.circle(vig, (0, 0, 0, alpha), (vcx, vcy), r)
        return vig

    # ── Events ────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.btn_rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.all_shown and self.hovered:
                audio.play("button_click", channel="button")
                self.game.switch_state("game")
            elif not self.all_shown:
                audio.play("button_click", channel="button")
                self._advance()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.all_shown:
                    audio.play("button_click", channel="button")
                    self.game.switch_state("game")
                else:
                    audio.play("button_click", channel="button")
                    self._advance()
            if event.key == pygame.K_ESCAPE:
                audio.play("button_click", channel="button")
                self.game.switch_state("disclaimer")

    def _advance(self):
        if self.card_idx < len(MECHANICS) - 1:
            self.card_idx += 1
            self.card_fade = 0.0
        else:
            self.all_shown = True

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, dt):
        self.time     += dt
        self.fade_in   = min(1.0, self.fade_in + dt * 1.6)
        self.card_fade = min(1.0, self.card_fade + dt * FADE_SPEED)

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        surface.fill((6, 4, 4))

        self._draw_specks(surface)
        surface.blit(self._vignette,  (0, 0))
        surface.blit(self._scanlines, (0, 0))

        ga = int(self.fade_in * 255)

        self._draw_corners(surface, ga)
        self._draw_header(surface, ga)
        self._draw_cards(surface, ga)
        self._draw_dots(surface, ga)

        if self.all_shown:
            self._draw_button(surface, ga)
        else:
            self._draw_hint(surface, ga)

        draw_text(surface, "ESC — back", SZ_ESC, MID_GRAY, CX, ESC_Y, alpha=ga)

    # ── Atmosphere ────────────────────────────────────────────────────────────
    def _draw_specks(self, surface):
        t = self.time
        for sx, sy, intensity, phase in self._specks:
            v = _flicker(t * 0.5, phase)
            a = int(v * intensity * 22)
            if a > 0:
                pygame.draw.circle(surface, (a, a // 2, a // 2), (sx, sy), 1)

    def _draw_corners(self, surface, alpha):
        if alpha < 10:
            return
        font      = get_font(SZ_CORNER, bold=True)
        flicker_a = int(_flicker(self.time, 3.3) * alpha * 0.55)
        p         = CORNER_PAD
        for cx2, cy2, flip_x, flip_y in [
            (p, p, False, False),
            (SCREEN_W - p, p, True, False),
            (p, SCREEN_H - p, False, True),
            (SCREEN_W - p, SCREEN_H - p, True, True),
        ]:
            img = font.render("✦", True, BLOOD_RED)
            img.set_alpha(flicker_a)
            rx = cx2 - img.get_width()  if flip_x else cx2
            ry = cy2 - img.get_height() if flip_y else cy2
            surface.blit(img, (rx, ry))

    # ── Header ────────────────────────────────────────────────────────────────
    def _draw_header(self, surface, alpha):
        flk  = _flicker(self.time, 1.1)
        col  = (int(BLOOD_RED[0]*flk), int(BLOOD_RED[1]*flk), int(BLOOD_RED[2]*flk))
        font = get_font(SZ_HEADER, bold=True)
        img  = font.render(" HOW IT WORKS ", True, col)
        img.set_alpha(alpha)
        surface.blit(img, (CX - img.get_width() // 2, HEADER_Y))

        line_a = int(_flicker(self.time * 1.3, 5.5) * alpha * 0.65)
        lh     = max(1, int(2 * SCALE))
        gap    = int(10 * SCALE)
        llen   = int(SCREEN_W * 0.10)
        mid_y  = HEADER_Y + img.get_height() // 2 - lh // 2
        half_w = img.get_width() // 2
        for lx in [CX - half_w - gap - llen, CX + half_w + gap]:
            seg = pygame.Surface((llen, lh), pygame.SRCALPHA)
            seg.fill((*BLOOD_RED, line_a))
            surface.blit(seg, (lx, mid_y))

    # ── Cards ─────────────────────────────────────────────────────────────────
    def _draw_cards(self, surface, global_alpha):
        bar_pad  = int(14 * SCALE)
        bar_w    = max(2, int(3 * SCALE))
        text_pad = bar_pad + bar_w + int(12 * SCALE)

        title_font = get_font(SZ_TITLE, bold=True)
        body_font  = get_font(SZ_BODY)
        title_h    = title_font.get_linesize()
        body_h     = body_font.get_linesize()

        for i, mech in enumerate(MECHANICS):
            if i > self.card_idx:
                continue

            fa = int((self.card_fade if i == self.card_idx else 1.0) * 255)
            fa = min(fa, global_alpha)
            if fa <= 0:
                continue

            card_y = CARD_TOP + i * (CARD_H + CARD_GAP)
            rect   = pygame.Rect(CX - CARD_W // 2, card_y, CARD_W, CARD_H)
            col    = mech["color"]

            # ── Background ────────────────────────────────────────────────────
            bg = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            bg.fill((18, 10, 10, fa))
            surface.blit(bg, rect.topleft)

            # ── Border ────────────────────────────────────────────────────────
            bd = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            pygame.draw.rect(bd, (*col, fa), bd.get_rect(), 1, border_radius=5)
            surface.blit(bd, rect.topleft)

            # ── Left accent bar ───────────────────────────────────────────────
            bar_h    = int(CARD_H * 0.60)
            bar_surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
            bar_surf.fill((*col, fa))
            surface.blit(bar_surf,
                         (rect.x + bar_pad, rect.y + (CARD_H - bar_h) // 2))

            # ── Per-card content geometry ─────────────────────────────────────
            # content_h is computed from THIS card's actual line count so that
            # both tall cards (3 lines) and short cards (2 lines) centre
            # correctly and NEVER overflow the container rect.
            n_lines     = len(mech["lines"])
            content_h   = title_h + _TITLE_BODY_GAP + body_h * n_lines
            # Ideal: vertically centre inside card
            content_top = (CARD_H - content_h) // 2
            # Clamp: never push text off the top or bottom edge
            content_top = max(_CARD_TOP_PAD,
                              min(content_top, CARD_H - content_h - _CARD_TOP_PAD))

            # ── Title row (icon + text) ───────────────────────────────────────
            ty        = rect.y + content_top
            icon_font = get_font(SZ_TITLE)
            icon_img  = icon_font.render(mech["icon"], True, col)
            icon_img.set_alpha(fa)
            title_img = title_font.render(mech["title"], True, col)
            title_img.set_alpha(fa)

            surface.blit(icon_img,  (rect.x + text_pad, ty))
            surface.blit(title_img, (rect.x + text_pad
                                     + icon_img.get_width() + int(7 * SCALE), ty))

            # ── Body lines ────────────────────────────────────────────────────
            by = ty + title_h + _TITLE_BODY_GAP
            for j, line in enumerate(mech["lines"]):
                li = body_font.render(line, True, (175, 155, 155))
                li.set_alpha(fa)
                surface.blit(li, (rect.x + text_pad, by + j * body_h))

    # ── Progress dots ─────────────────────────────────────────────────────────
    def _draw_dots(self, surface, alpha):
        n      = len(MECHANICS)
        dot_r  = max(3, int(4 * SCALE))
        dot_sp = int(20 * SCALE)
        start  = CX - (n - 1) * dot_sp // 2

        for i in range(n):
            if i < self.card_idx:
                col = BLOOD_RED
            elif i == self.card_idx:
                pulse = 0.72 + 0.28 * math.sin(self.time * 5)
                col   = tuple(int(v * pulse) for v in MECHANICS[i]["color"])
            else:
                col = (45, 30, 30)

            ds = pygame.Surface((dot_r * 2 + 2, dot_r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ds, (*col, alpha), (dot_r + 1, dot_r + 1), dot_r)
            surface.blit(ds, (start + i * dot_sp - dot_r - 1, DOT_Y - dot_r - 1))

    # ── BEGIN button ──────────────────────────────────────────────────────────
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

        bg_col  = (25, 8, 8)      if self.hovered else (10, 4, 4)
        brd_col = BLOOD_RED        if self.hovered else (80, 20, 20)
        txt_col = (230, 200, 200)  if self.hovered else (160, 100, 100)
        brd_w   = max(1, int(2 * SCALE)) if self.hovered else 1

        pygame.draw.rect(surface, bg_col,  r, border_radius=4)
        pygame.draw.rect(surface, brd_col, r, brd_w, border_radius=4)

        if self.hovered:
            scan_y = r.y + int((self.time * 60) % r.h)
            scan_h = max(1, int(2 * SCALE))
            ss     = pygame.Surface((r.w, scan_h), pygame.SRCALPHA)
            ss.fill((200, 50, 50, 30))
            surface.blit(ss, (r.x, scan_y))

        lbl_flk = _flicker(self.time * 2.0, 9.9) if self.hovered else 1.0
        lbl_col = tuple(int(c * lbl_flk) for c in txt_col)
        lbl_img = get_font(SZ_BTN, bold=self.hovered).render("BEGIN", True, lbl_col)
        lbl_img.set_alpha(alpha)
        surface.blit(lbl_img, lbl_img.get_rect(center=r.center))

    # ── Hint text ─────────────────────────────────────────────────────────────
    def _draw_hint(self, surface, alpha):
        hint_a = int(_flicker(self.time * 2.5, 2.2) * alpha * 0.50)
        text   = ("CLICK or SPACE to start"
                  if self.card_idx == len(MECHANICS) - 1
                  else "CLICK or SPACE to continue")
        img = get_font(SZ_HINT).render(text, True, MID_GRAY)
        img.set_alpha(hint_a)
        surface.blit(img, img.get_rect(center=(CX, HINT_Y)))