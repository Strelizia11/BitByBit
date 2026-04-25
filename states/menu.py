import pygame
import math
from PIL import Image
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

        # Load GIF background
        self.gif_frames = []
        self.frame_durations = []
        self.current_frame = 0
        self.frame_timer = 0.0
        try:
            gif_path = "assets/GameMenu.gif"
            with Image.open(gif_path) as gif:
                # Composite each frame properly onto a running canvas.
                # GIF is delta-based: frames are partial updates, not full images.
                # tobytes() on a raw seek gives incomplete frames with white gaps.
                canvas = Image.new("RGBA", gif.size, (0, 0, 0, 255))
                for frame in range(gif.n_frames):
                    gif.seek(frame)
                    # Convert to RGBA so paste handles transparency correctly
                    frame_rgba = gif.convert("RGBA")
                    canvas.paste(frame_rgba, (0, 0), frame_rgba)

                    # Convert the composited canvas to a pygame surface
                    frame_surface = pygame.image.fromstring(
                        canvas.tobytes(), canvas.size, "RGBA"
                    ).convert()
                    scaled_surface = pygame.transform.scale(frame_surface, (SCREEN_W, SCREEN_H))
                    self.gif_frames.append(scaled_surface)

                    duration = gif.info.get('duration', 100) / 1000.0
                    self.frame_durations.append(max(0.05, duration))
        except Exception as e:
            print(f"Failed to load GIF: {e}")
            self.gif_frames = []
            self.frame_durations = []

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

        # Update GIF animation with per-frame timing
        if self.gif_frames:
            self.frame_timer += dt
            current_duration = self.frame_durations[self.current_frame]
            
            if self.frame_timer >= current_duration:
                self.frame_timer -= current_duration  # Carry over remaining time for smooth looping
                self.current_frame = (self.current_frame + 1) % len(self.gif_frames)

    def draw(self, surface):
        # Draw GIF background - scale to match actual surface size (fullscreen or windowed)
        if self.gif_frames:
            surface.blit(self.gif_frames[self.current_frame], (0, 0))
        else:
            surface.fill(NEAR_BLACK)

        self._draw_scanlines(surface)
        alpha = int(self.fade_in * 255)

        # Flicker for title
        flicker = 0.93 + 0.07 * math.sin(self.time * 9.1)
        title_col = tuple(int(c * flicker) for c in AMBER)



        # Footer hint
        _, height = surface.get_size()
        draw_text(surface, "press ENTER to start", 12, MID_GRAY, CX, height - 28, alpha=alpha)

    def _draw_scanlines(self, surface):
        width, height = surface.get_size()
        sl = pygame.Surface((width, height), pygame.SRCALPHA)
        for y in range(0, height, 4):
            pygame.draw.line(sl, (0, 0, 0, 18), (0, y), (width, y))
        surface.blit(sl, (0, 0))