import pygame
from states.base import BaseState
from utils import (
    draw_text, draw_rect_border, draw_rect_filled,
    NEAR_BLACK, DARK_GRAY, MID_GRAY, DIM_WHITE, WHITE,
    BLOOD_RED, AMBER, AMBER_DIM, BLACK,
    SCREEN_W, SCREEN_H, CX, CY, get_font
)

DISCLAIMER_LINES = [
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
    "",
    "  ...do you?",
]


class DisclaimerState(BaseState):
    REVEAL_SPEED = 18          # chars revealed per second
    LINE_DELAY   = 0.18        # seconds between lines starting

    def on_enter(self, **kwargs):
        self.time      = 0.0
        self.fade_in   = 0.0
        self.char_idx  = 0.0   # total chars revealed across all lines
        self.done      = False
        self.hovered   = False
        # Pre-count chars per line (empty line = 0)
        self.line_chars = [len(l) if l else 0 for l in DISCLAIMER_LINES]
        total = sum(self.line_chars) + len(DISCLAIMER_LINES) * 2
        self.total_chars = total
        bw, bh = 240, 44
        self.btn_rect = pygame.Rect(CX - bw // 2, SCREEN_H - 90, bw, bh)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.btn_rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.done:
                # Skip to full reveal
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

    def update(self, dt):
        self.time   += dt
        self.fade_in = min(1.0, self.fade_in + dt * 1.8)
        if not self.done:
            self.char_idx += self.REVEAL_SPEED * dt
            if self.char_idx >= self.total_chars:
                self.char_idx = float(self.total_chars)
                self.done = True

    def draw(self, surface):
        surface.fill(NEAR_BLACK)
        alpha = int(self.fade_in * 255)

        draw_text(surface, "— DISCLAIMER —", 16, AMBER_DIM, CX, 52, alpha=alpha)

        font = get_font(15)
        start_y = 100
        line_h  = 26
        remaining = int(self.char_idx)

        for i, line in enumerate(DISCLAIMER_LINES):
            y = start_y + i * line_h
            if not line:
                remaining = max(0, remaining - 2)
                continue
            shown = min(len(line), remaining)
            remaining = max(0, remaining - len(line) - 2)
            if shown <= 0:
                break
            color = DIM_WHITE if line.strip() != "...do you?" else BLOOD_RED
            txt = line[:shown]
            img = font.render(txt, True, color)
            img.set_alpha(alpha)
            surface.blit(img, (CX - img.get_width() // 2, y))

        # Left-bar accent
        if self.fade_in > 0.2:
            bar_h = len(DISCLAIMER_LINES) * line_h
            bar_x = CX - 200
            pygame.draw.line(surface, MID_GRAY, (bar_x, start_y - 4), (bar_x, start_y + bar_h), 1)

        if self.done:
            bg   = DARK_GRAY if self.hovered else BLACK
            bord = AMBER      if self.hovered else MID_GRAY
            tc   = WHITE      if self.hovered else DIM_WHITE
            draw_rect_filled(surface, bg, self.btn_rect, radius=4)
            draw_rect_border(surface, bord, self.btn_rect, radius=4)
            draw_text(surface, "I UNDERSTAND", 14, tc, self.btn_rect.centerx, self.btn_rect.centery, bold=self.hovered)

        draw_text(surface, "ESC — back to menu", 11, MID_GRAY, CX, SCREEN_H - 20, alpha=alpha)