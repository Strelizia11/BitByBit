import random
import math
import pygame


class LightSystem:
    """
    Manages whether the light is ON or OFF for a round,
    and produces per-frame overlay surfaces for the visual effects.
    """

    # Probability light is ON at round start
    LIGHT_ON_CHANCE = 0.60

    def __init__(self, screen_w: int, screen_h: int):
        self.w = screen_w
        self.h = screen_h
        self.light_on = True
        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)

    def randomise(self):
        self.light_on = random.random() < self.LIGHT_ON_CHANCE

    # ── Per-frame effect ──────────────────────────────────────────────────────
    def build_overlay(self, timer_pct: float) -> pygame.Surface:
        """
        timer_pct: 1.0 = full time remaining, 0.0 = time expired.
        Returns an SRCALPHA surface to blit over the game scene.
        """
        self._overlay.fill((0, 0, 0, 0))

        urgency = 1.0 - timer_pct   # 0 → 1 as time runs out

        if self.light_on:
            self._apply_dim(urgency)
        else:
            self._apply_blur_vignette(urgency)

        return self._overlay

    def _apply_dim(self, urgency: float):
        """Light ON: screen dims from 50 % onward → full black at 0 %."""
        if urgency < 0.5:
            return
        t      = (urgency - 0.5) / 0.5          # 0→1 in second half
        alpha  = int(t * 230)
        self._overlay.fill((0, 0, 0, alpha))

    def _apply_blur_vignette(self, urgency: float):
        """
        Light OFF: radial blue-tinted vignette grows inward.
        True blur isn't cheap in pygame; we simulate with layered circles.
        """
        if urgency < 0.3:
            return
        t = (urgency - 0.3) / 0.7               # 0→1 in last 70 %

        cx, cy = self.w // 2, self.h // 2
        max_r  = int(math.hypot(cx, cy)) + 20

        # Dark outer fog closing in
        layers = 12
        for i in range(layers):
            frac    = i / layers
            r       = int(max_r * (1.0 - frac * t * 0.85))
            alpha   = int(frac * t * 210)
            color   = (0, 0, int(10 * t), alpha)
            pygame.draw.circle(self._overlay, color, (cx, cy), r)

        # Thin blue noise-like inner ring
        ring_alpha = int(t * 80)
        ring_r     = int(max_r * (0.4 - t * 0.3))
        if ring_r > 0:
            pygame.draw.circle(self._overlay, (20, 40, 100, ring_alpha), (cx, cy), ring_r, 6)

    # ── UI helpers ────────────────────────────────────────────────────────────
    @property
    def indicator_color(self):
        return (200, 160, 30) if self.light_on else (50, 90, 170)

    @property
    def indicator_label(self):
        return "ON" if self.light_on else "OFF"