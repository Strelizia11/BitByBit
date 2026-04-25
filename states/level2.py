import os
import pygame
from states.base import BaseState
from utils import (
    draw_text,
    SCREEN_W, SCREEN_H, CX, CY,
    AMBER, MID_GRAY, WHITE, DIM_WHITE, NEAR_BLACK
)


class Level2State(BaseState):
    """
    Level 2 opening screen.
    Fades in from black over the level2_background image.
    Press any key / click to begin (placeholder — hook up your level-2 gameplay here).
    """

    FADE_IN_DURATION = 1.5   # seconds to fade from black → full image

    def on_enter(self, **kwargs):
        self.time       = 0.0
        self.fade_alpha = 255   # start fully black, count down to 0

        # Load background; fall back to a solid colour if file is missing
        bg_path = os.path.join("assets", "girl.jpg")
        if os.path.exists(bg_path):
            raw = pygame.image.load(bg_path).convert()
            self.bg = pygame.transform.scale(raw, (SCREEN_W, SCREEN_H))
        else:
            self.bg = pygame.Surface((SCREEN_W, SCREEN_H))
            self.bg.fill((10, 10, 30))   # dark fallback

        self.faded_in = False
        pygame.mouse.set_visible(True)

    def handle_event(self, event):
        if not self.faded_in:
            return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            # TODO: switch to actual level-2 gameplay state when ready
            self.game.switch_state("menu")

    def update(self, dt):
        self.time += dt
        t = min(1.0, self.time / self.FADE_IN_DURATION)
        self.fade_alpha = int((1.0 - t) * 255)
        if t >= 1.0:
            self.faded_in = True

    def draw(self, surface):
        surface.blit(self.bg, (0, 0))

        # Black overlay for the fade-in
        if self.fade_alpha > 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.fade_alpha)
            surface.blit(overlay, (0, 0))

        # Once faded in, show a "press any key" prompt
        if self.faded_in:
            draw_text(surface, "LEVEL 2", 36, AMBER, CX, CY - 40, bold=True)
            draw_text(surface, "Press any key to continue", 16, DIM_WHITE, CX, CY + 10)