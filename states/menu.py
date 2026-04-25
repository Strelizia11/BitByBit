import pygame
import math
from states.base import BaseState
from utils import (
    draw_text, draw_rect_border, draw_rect_filled,
    NEAR_BLACK, DARK_GRAY, MID_GRAY, DIM_WHITE, WHITE, AMBER, AMBER_DIM,
    BLOOD_RED, BLACK, SCREEN_W, SCREEN_H, CX, CY, get_font
)


class MenuState(BaseState):
    BUTTONS = [
        ("START",  "disclaimer"),
        ("HOW TO PLAY", "mechanics"),
        ("EXIT",   None),
    ]

    def on_enter(self, **kwargs):
        self.time   = 0.0
        self.hovered = -1
        self.fade_in = 0.0          # 0→1 alpha fade
        bw, bh = 260, 46
        start_y = CY + 30
        self.btn_rects = [
            pygame.Rect(CX - bw // 2, start_y + i * 64, bw, bh)
            for i in range(len(self.BUTTONS))
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = next(
                (i for i, r in enumerate(self.btn_rects) if r.collidepoint(mx, my)), -1
            )
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered >= 0:
                _, target = self.BUTTONS[self.hovered]
                if target is None:
                    self.game.running = False
                else:
                    self.game.switch_state(target)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.game.switch_state("disclaimer")
            if event.key == pygame.K_ESCAPE:
                self.game.running = False

    def update(self, dt):
        self.time    += dt
        self.fade_in  = min(1.0, self.fade_in + dt * 1.4)

    def draw(self, surface):
        surface.fill(NEAR_BLACK)
        self._draw_scanlines(surface)
        alpha = int(self.fade_in * 255)

        # Flicker for title
        flicker = 0.93 + 0.07 * math.sin(self.time * 9.1)
        title_col = tuple(int(c * flicker) for c in AMBER)

        draw_text(surface, "Title", 38, title_col, CX, CY - 110, bold=True, alpha=alpha)
        draw_text(surface, "ung catchy line if balak nyo lagyan", 14, AMBER_DIM, CX, CY - 72, alpha=alpha)

        # Divider
        if self.fade_in > 0.3:
            lw = int(340 * min(1.0, (self.fade_in - 0.3) / 0.5))
            pygame.draw.line(surface, MID_GRAY, (CX - lw // 2, CY - 48), (CX + lw // 2, CY - 48), 1)

        # Buttons
        for i, (label, _) in enumerate(self.BUTTONS):
            rect   = self.btn_rects[i]
            is_hov = (i == self.hovered)
            is_exit= (label == "EXIT")
            bg     = DARK_GRAY if is_hov else BLACK
            border = (BLOOD_RED if is_exit else AMBER) if is_hov else MID_GRAY
            text_c = (BLOOD_RED if is_exit else WHITE) if is_hov else DIM_WHITE
            draw_rect_filled(surface, bg, rect, radius=4)
            draw_rect_border(surface, border, rect, width=1, radius=4)
            draw_text(surface, label, 15, text_c, rect.centerx, rect.centery, bold=is_hov, alpha=alpha)

        # Footer hint
        draw_text(surface, "press ENTER to start", 12, MID_GRAY, CX, SCREEN_H - 28, alpha=alpha)

    def _draw_scanlines(self, surface):
        sl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 4):
            pygame.draw.line(sl, (0, 0, 0, 18), (0, y), (SCREEN_W, y))
        surface.blit(sl, (0, 0))