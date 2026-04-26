import pygame
from states.base import BaseState
from utils import SCREEN_W, SCREEN_H, CX, CY, NEAR_BLACK


class SplashState(BaseState):
    def on_enter(self, **kwargs):
        self.time = 0.0
        self.duration = 4.0  # Total display time (seconds)
        self.alpha = 0

        # --- Logo ---
        original_image = pygame.image.load("./assets/BitByBit_Logo.png").convert_alpha()
        custom_size = (400, 400)
        self.image = pygame.transform.smoothscale(original_image, custom_size)
        self.rect = self.image.get_rect(center=(CX, CY - 30))  # Shift up slightly to make room for text

        # --- White background panel behind the logo ---
        padding = 24
        panel_w = custom_size[0] + padding * 2
        panel_h = custom_size[1] + padding * 2
        self.panel_surface = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        # Draw rounded-rect white card
        pygame.draw.rect(
            self.panel_surface,
            (255, 255, 255, 255),
            self.panel_surface.get_rect(),
            border_radius=16,
        )
        self.panel_rect = self.panel_surface.get_rect(center=(CX, CY - 30))

        # --- "presents" text ---
        font_size = 35
        try:
            # Try a clean serif/italic feel; fall back to default if unavailable
            self.font = pygame.font.SysFont("Georgia", font_size, italic=True)
        except Exception:
            self.font = pygame.font.Font(None, font_size)

        self.presents_surf = self.font.render("presents", True, (220, 220, 220))
        self.presents_rect = self.presents_surf.get_rect(
            center=(CX, self.panel_rect.bottom + 28)
        )

    def update(self, dt):
        self.time += dt

        # Fade Logic: 0–1 s (fade in), 1–3 s (hold), 3–4 s (fade out)
        if self.time < 1.0:
            self.alpha = int((self.time / 1.0) * 255)
        elif self.time < 3.0:
            self.alpha = 255
        elif self.time < 4.0:
            self.alpha = int(255 - ((self.time - 3.0) / 1.0) * 255)
        else:
            self.game.switch_state("menu")

    def draw(self, surface):
        surface.fill(NEAR_BLACK)

        # Apply shared alpha to all splash elements
        self.panel_surface.set_alpha(self.alpha)
        surface.blit(self.panel_surface, self.panel_rect)

        self.image.set_alpha(self.alpha)
        surface.blit(self.image, self.rect)

        self.presents_surf.set_alpha(self.alpha)
        surface.blit(self.presents_surf, self.presents_rect)