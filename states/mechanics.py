import pygame
from states.base import BaseState
from utils import (
    draw_text, draw_rect_border, draw_rect_filled,
    NEAR_BLACK, DARK_GRAY, MID_GRAY, DIM_WHITE, WHITE,
    BLOOD_RED, AMBER, AMBER_DIM, BLACK, STEEL_BLUE, GREEN_DIM, GREEN_BRIGHT,
    SCREEN_W, SCREEN_H, CX, CY, get_font
)

MECHANICS = [
    {
        "title":  "LIGHT ON",
        "color":  (180, 140, 20),
        "lines": [
            "Mechanics #1"
        ],
    },
    {
        "title":  "LIGHT OFF",
        "color":  (60, 100, 180),
        "lines": [
            "Mechanics #2"
        ],
    },
    {
        "title":  "ANOMALY  (misspelling)",
        "color":  (180, 50, 50),
        "lines": [
            "Mechanics #3"
        ],
    },
    {
        "title":  "TIMER",
        "color":  (100, 100, 100),
        "lines": [
            "Mechanics #4"
        ],
    },
]

FADE_SPEED = 1.6   # seconds per card fade


class MechanicsState(BaseState):
    def on_enter(self, **kwargs):
        self.time      = 0.0
        self.fade_in   = 0.0
        self.card_idx  = 0
        self.card_fade = 0.0
        self.all_shown = False
        self.hovered   = False
        bw, bh = 240, 44
        self.btn_rect = pygame.Rect(CX - bw // 2, SCREEN_H - 78, bw, bh)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.btn_rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.all_shown and self.hovered:
                self.game.switch_state("game")
            elif not self.all_shown:
                self._advance()
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.all_shown:
                    self.game.switch_state("game")
                else:
                    self._advance()
            if event.key == pygame.K_ESCAPE:
                self.game.switch_state("disclaimer")

    def _advance(self):
        if self.card_idx < len(MECHANICS) - 1:
            self.card_idx  += 1
            self.card_fade  = 0.0
        else:
            self.all_shown = True

    def update(self, dt):
        self.time      += dt
        self.fade_in    = min(1.0, self.fade_in + dt * 1.8)
        self.card_fade  = min(1.0, self.card_fade + dt * FADE_SPEED)
        if self.card_fade >= 1.0 and not self.all_shown:
            if self.card_idx < len(MECHANICS) - 1:
                # auto-advance slowly
                pass   # manual only; kept for potential auto mode

    def draw(self, surface):
        surface.fill(NEAR_BLACK)
        alpha = int(self.fade_in * 255)
        draw_text(surface, "— HOW IT WORKS —", 16, AMBER_DIM, CX, 42, alpha=alpha)

        card_w  = 660
        card_h  = 88
        start_y = 80
        gap     = 108

        font_sm = get_font(13)

        for i, mech in enumerate(MECHANICS):
            visible = (i <= self.card_idx)
            if not visible:
                continue
            fa = int((self.card_fade if i == self.card_idx else 1.0) * 255)
            fa = min(fa, alpha)

            rect = pygame.Rect(CX - card_w // 2, start_y + i * gap, card_w, card_h)
            bg   = DARK_GRAY
            s_bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            s_bg.fill((*bg, fa))
            surface.blit(s_bg, rect.topleft)

            border_col = (*mech["color"], fa)
            s_bd = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(s_bd, border_col, s_bd.get_rect(), 1, border_radius=5)
            surface.blit(s_bd, rect.topleft)

            # Left accent bar
            accent_s = pygame.Surface((3, card_h - 16), pygame.SRCALPHA)
            accent_s.fill((*mech["color"], fa))
            surface.blit(accent_s, (rect.x + 14, rect.y + 8))

            # Title
            tf = get_font(14, bold=True)
            ti = tf.render(mech["title"], True, mech["color"])
            ti.set_alpha(fa)
            surface.blit(ti, (rect.x + 28, rect.y + 10))

            # Body lines
            for j, line in enumerate(mech["lines"]):
                li = font_sm.render(line, True, DIM_WHITE)
                li.set_alpha(fa)
                surface.blit(li, (rect.x + 28, rect.y + 32 + j * 18))

        # Progress dots
        dot_y = start_y + len(MECHANICS) * gap - 10
        for i in range(len(MECHANICS)):
            col = WHITE if i <= self.card_idx else MID_GRAY
            pygame.draw.circle(surface, col, (CX - (len(MECHANICS) - 1) * 12 + i * 24, dot_y), 4)

        # Continue hint / button
        if self.all_shown:
            bg   = DARK_GRAY if self.hovered else BLACK
            bord = AMBER      if self.hovered else MID_GRAY
            tc   = WHITE      if self.hovered else DIM_WHITE
            draw_rect_filled(surface, bg, self.btn_rect, radius=4)
            draw_rect_border(surface, bord, self.btn_rect, radius=4)
            draw_text(surface, "BEGIN", 15, tc, self.btn_rect.centerx, self.btn_rect.centery, bold=self.hovered)
        else:
            hint = "CLICK or SPACE to continue" if self.card_idx < len(MECHANICS) - 1 else "CLICK or SPACE to start"
            draw_text(surface, hint, 12, MID_GRAY, CX, SCREEN_H - 28, alpha=alpha)

        draw_text(surface, "ESC — back", 11, MID_GRAY, CX, SCREEN_H - 12, alpha=alpha)