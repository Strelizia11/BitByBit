import pygame
from utils import SCREEN_W, get_font, GREEN_BRIGHT, BLOOD_RED, AMBER, MID_GRAY


TIMER_DURATION = 10.0   # seconds per instruction


class Timer:
    """Countdown timer for each instruction."""

    def __init__(self, duration: float = TIMER_DURATION):
        self.duration    = duration
        self.remaining   = duration
        self.running     = False
        self.expired     = False

    # ── Control ───────────────────────────────────────────────────────────────
    def start(self):
        self.remaining = self.duration
        self.running   = True
        self.expired   = False

    def stop(self):
        self.running = False

    def update(self, dt: float):
        if not self.running:
            return
        self.remaining -= dt
        if self.remaining <= 0.0:
            self.remaining = 0.0
            self.running   = False
            self.expired   = True

    # ── Derived values ────────────────────────────────────────────────────────
    @property
    def pct(self) -> float:
        """1.0 = full, 0.0 = empty."""
        return self.remaining / self.duration

    @property
    def urgency(self) -> float:
        """0.0 = calm, 1.0 = time up."""
        return 1.0 - self.pct

    @property
    def bar_color(self):
        t = self.urgency
        if t < 0.5:
            return _lerp_color(GREEN_BRIGHT, AMBER, t * 2)
        return _lerp_color(AMBER, BLOOD_RED, (t - 0.5) * 2)

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surface, x: int, y: int, w: int, h: int = 7):
        """Draw timer bar at given rect."""
        # Background track
        pygame.draw.rect(surface, (30, 30, 30), (x, y, w, h), border_radius=3)
        # Filled portion
        filled_w = int(w * self.pct)
        if filled_w > 0:
            pygame.draw.rect(surface, self.bar_color, (x, y, filled_w, h), border_radius=3)
        # Seconds label
        font  = get_font(12)
        label = f"{self.remaining:.1f}s"
        img   = font.render(label, True, MID_GRAY)
        surface.blit(img, (x + w + 8, y - 2))


def _lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))