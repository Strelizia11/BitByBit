import os
import math
import pygame
import random
from states.base import BaseState
from states.audio_manager import AudioManager
from system.instruction_system import InstructionSystem
from utils import (
    draw_text, draw_rect_border, draw_rect_filled,
    NEAR_BLACK, DARK_GRAY, MID_GRAY, DIM_WHITE, WHITE,
    BLOOD_RED, AMBER, AMBER_DIM, BLACK, GREEN_DIM, GREEN_BRIGHT,
    SCREEN_W, SCREEN_H, CX, CY, get_font, lerp_color
)

audio = AudioManager()
# ── Layout constants ───────────────────────────────────────────────────────────
HUD_H = 52
BULB_SIZE = (80, 120)
BULB_CENTER = (CX, CY + 30)

# ── HUD colours ───────────────────────────────────────────────────────────────
HUD_BG = (15, 15, 15)
INSTRUCTION_COL = (220, 220, 220)
ANOMALY_COL = (220, 220, 220)
FOLLOW_COL = GREEN_BRIGHT
IGNORE_COL = BLOOD_RED

# Window position — left of switch, vertically centred
WIN_W, WIN_H = 110, 150
WIN_X = CX - 160 - WIN_W
WIN_Y = CY - WIN_H // 2 + 30


class Level2State(BaseState):
    """
    Level 2 gameplay with 8 rounds and interactive window.
    Starts with light OFF and window CLOSED.
    Players must follow instructions to click the switch or open/close the window.
    After completion, returns to menu.
    """

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def on_enter(self, **kwargs):
        audio.stop_music()
        audio.play_music("ambience", loop=True)
        # --- images ---
        self.img_on = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "light-on1.png")).convert_alpha(),
            BULB_SIZE
        )
        self.img_off = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "light-off1.png")).convert_alpha(),
            BULB_SIZE
        )
        self.img_rect = self.img_on.get_rect(center=BULB_CENTER)

        # --- cursor images ---
        self.cur_normal = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "hand.png")).convert_alpha(),
            (32, 32)
        )
        self.cur_clicked = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "hand_clicked.png")).convert_alpha(),
            (32, 32)
        )
        pygame.mouse.set_visible(False)

        # --- light state: START WITH OFF ---
        self.light_on = False
        self.is_clicked = False

        # --- window state: START WITH CLOSED ---
        self.window_open = False
        self.window_rect = pygame.Rect(WIN_X, WIN_Y, WIN_W, WIN_H)

        self.instr_sys = InstructionSystem(total_rounds=8)
        self.instr_sys.reset()

        # --- timer & tracking ---
        self.round_time_limit = 6.0
        self.round_timer = 0.0
        self.clicks_this_round = 0
        self.window_clicks_this_round = 0
        self.start_light_state = self.light_on
        self.start_window_state = self.window_open

        self.current_text = ""
        self.current_is_anomaly = False
        self.game_over = False

        self._load_next_instruction()

        self.instr_alpha = 0.0
        self.instr_pulse = 0.0
        self.distress_intensity = 0.0
        self.game_over = False

        # --- death sequence ---
        self.death_timer = 0.0
        self.death_phase = 0

        self.death_img = pygame.image.load(os.path.join("assets", "girl.jpg")).convert()
        self.death_img = pygame.transform.scale(self.death_img, (SCREEN_W, SCREEN_H))

    # ── Input ─────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    audio.stop_music()
                    audio.play("button_click", channel="button")
                    self.game.score = 0
                    self.on_enter()
                elif event.key == pygame.K_ESCAPE:
                    audio.stop_music()
                    audio.play("button_click", channel="button")
                    pygame.mouse.set_visible(True)
                    self.game.switch_state("menu")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_clicked = True
            
            # Window click - toggle open/closed state
            if self.window_rect.collidepoint(event.pos):
                self.window_open = not self.window_open
                self.window_clicks_this_round += 1
                # Play appropriate sound
                if self.window_open:
                    audio.play("window_open", channel="window")
                else:
                    audio.play("window_close", channel="window")
            
            # Switch click - toggle light
            elif self.img_rect.collidepoint(event.pos):
                self.light_on = not self.light_on
                self.clicks_this_round += 1
                # Play switch sound
                if self.light_on:
                    audio.play("switch_on", channel="switch")
                else:
                    audio.play("switch_off", channel="switch")

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_clicked = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                audio.stop_music()
                pygame.mouse.set_visible(True)
                self.game.switch_state("menu")

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, dt):
        # ── Normal gameplay update ────────────────────────────────────────────
        if not self.game_over:
            self.instr_alpha = min(1.0, self.instr_alpha + dt * 2.5)
            self.instr_pulse += dt

            time_left = max(0.0, self.round_time_limit - self.round_timer)
            if time_left < 3.0:
                self.distress_intensity = 1.0 - (time_left / 3.0)
            else:
                self.distress_intensity = 0.0

            self.round_timer += dt
            if self.round_timer >= self.round_time_limit:
                self._resolve_round()
        else:
            audio.stop_music()
            self.death_timer += dt

            if self.death_phase == 4:
                if self.death_timer > 2.0:
                    self.death_phase = 666
                    self.death_timer = 0.0

            elif self.death_phase == 666:
                if self.death_timer > 4.0:
                    pygame.mouse.set_visible(True)
                    self.game.switch_state("menu")

            elif self.death_phase == 1 and self.death_timer > 3.0:
                self.death_phase = 2
                self.death_timer = 0.0
            elif self.death_phase == 2 and self.death_timer > 3.0:
                self.death_phase = 3
                self.death_timer = 0.0
            elif self.death_phase == 3 and self.death_timer > 2.0:
                pygame.mouse.set_visible(True)
                self.game.switch_state("menu")

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        # ── Normal gameplay drawing ───────────────────────────────────────────
        surface.fill((255, 255, 255))

        img = self.img_on if self.light_on else self.img_off
        surface.blit(img, self.img_rect)

        self._draw_hud(surface)

        self._draw_window(surface)

        if not self.light_on:
            self._draw_flashlight(surface)

        if not self.game_over:
            self._apply_distress_effects(surface)
            self._draw_cursor(surface)
        else:
            self._draw_game_over(surface)

            if self.death_phase == 666:
                surface.blit(self.death_img, (0, 0))

            elif self.death_phase == 2:
                alpha = min(255, int((self.death_timer / 2.0) * 255))
                temp_img = self.death_img.copy()
                temp_img.set_alpha(alpha)
                surface.blit(temp_img, (0, 0))

            elif self.death_phase == 3:
                alpha = max(0, 255 - int((self.death_timer / 2.0) * 255))
                temp_img = self.death_img.copy()
                temp_img.set_alpha(alpha)
                surface.blit(temp_img, (0, 0))

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _load_next_instruction(self):
        result = self.instr_sys.next_instruction(self.light_on, self.window_open)

        if result is None:
            # All 8 rounds done successfully → return to menu
            self.game_over = True
            self.death_phase = 1
            self.death_timer = 0.0
            pygame.mouse.set_visible(False)
            return

        self.current_text = result[0]
        self.current_is_anomaly = result[1]
        self.current_base_rule = result[2]

        self.round_timer = 0.0
        self.clicks_this_round = 0
        self.window_clicks_this_round = 0
        self.start_light_state = self.light_on
        self.start_window_state = self.window_open
        self.instr_alpha = 0.0
        self.instr_pulse = 0.0

    def _resolve_round(self):
        success = self.instr_sys.evaluate_action(
            self.current_base_rule,
            self.current_is_anomaly,
            self.start_light_state,
            self.clicks_this_round,
            self.start_window_state,
            self.window_clicks_this_round
        )

        if success:
            self.game.score += 1
            self._load_next_instruction()
        else:
            self.game_over = True
            self.death_timer = 0.0
            self.death_phase = 4 if random.random() < 0.2 else 1
            pygame.mouse.set_visible(False)

    # ── Visual helpers ────────────────────────────────────────────────────────
    def _draw_hud(self, surface):
        pygame.draw.rect(surface, HUD_BG, (0, 0, SCREEN_W, HUD_H))

        if self.game_over:
            draw_text(surface, "LEVEL 2 COMPLETE", 18, AMBER, CX, HUD_H // 2, bold=True)
            return

        alpha = int(self.instr_alpha * 255)

        badge_col = AMBER if self.light_on else (50, 90, 170)
        badge_lbl = "LIGHT: ON" if self.light_on else "LIGHT: OFF"
        draw_text(surface, badge_lbl, 12, badge_col, 68, HUD_H // 2)

        pulse_t = 0.5 + 0.5 * math.sin(self.instr_pulse * 4.0)
        base_col = ANOMALY_COL if self.current_is_anomaly else INSTRUCTION_COL
        pulse_col = lerp_color(base_col, WHITE, pulse_t * 0.15)
        draw_text(surface, self.current_text, 20, pulse_col,
                  CX, HUD_H // 2, bold=True, alpha=alpha)

        time_left = max(0.0, self.round_time_limit - self.round_timer)
        time_col = AMBER if time_left > 1.5 else BLOOD_RED

        draw_text(surface, f"TIME: {time_left:.1f}s", 14, time_col,
                  SCREEN_W - 80, HUD_H // 2 - 10)
        draw_text(surface, f"SCORE: {self.game.score}", 11, MID_GRAY,
                  SCREEN_W - 80, HUD_H // 2 + 10)

    def _draw_window(self, surface):
        """
        Draw the window frame and panes based on open/closed state.
        Window can be clicked to open or close it.
        """
        wr = self.window_rect

        # Window frame — always drawn
        frame_color = (45, 45, 55)
        border_color = (95, 95, 110)
        
        pygame.draw.rect(surface, frame_color, wr, border_radius=4)
        pygame.draw.rect(surface, border_color, wr, 2, border_radius=4)

        if self.window_open:
            # Draw open window - panes pushed to the sides
            left_pane = pygame.Rect(wr.left + 4, wr.top + 4, wr.width // 2 - 12, wr.height - 8)
            right_pane = pygame.Rect(wr.centerx + 8, wr.top + 4, wr.width // 2 - 12, wr.height - 8)
            
            # Draw panes (slightly darker when open)
            pane_color = (30, 30, 40)
            pygame.draw.rect(surface, pane_color, left_pane, border_radius=2)
            pygame.draw.rect(surface, pane_color, right_pane, border_radius=2)
            pygame.draw.rect(surface, border_color, left_pane, 1, border_radius=2)
            pygame.draw.rect(surface, border_color, right_pane, 1, border_radius=2)
            
            # Draw opening (the gap in the middle showing "outside")
            opening = pygame.Rect(wr.left + wr.width // 2 - 8, wr.top + 4, 16, wr.height - 8)
            night_color = (10, 15, 25)
            pygame.draw.rect(surface, night_color, opening)
            
        else:
            # Draw closed window - cross dividers in the middle
            mx, my = wr.centerx, wr.centery
            
            # Draw glass panes (semi-transparent blue-ish tint)
            glass_color = (40, 50, 70)
            pane_tl = pygame.Rect(wr.left + 4, wr.top + 4, wr.width // 2 - 6, wr.height // 2 - 6)
            pane_tr = pygame.Rect(mx + 2, wr.top + 4, wr.width // 2 - 6, wr.height // 2 - 6)
            pane_bl = pygame.Rect(wr.left + 4, my + 2, wr.width // 2 - 6, wr.height // 2 - 6)
            pane_br = pygame.Rect(mx + 2, my + 2, wr.width // 2 - 6, wr.height // 2 - 6)
            
            for pane in [pane_tl, pane_tr, pane_bl, pane_br]:
                pygame.draw.rect(surface, glass_color, pane)
            
            # Cross dividers
            pygame.draw.line(surface, border_color, (mx, wr.top + 4), (mx, wr.bottom - 4), 2)
            pygame.draw.line(surface, border_color, (wr.left + 4, my), (wr.right - 4, my), 2)

    def _draw_flashlight(self, surface):
        mx, my = pygame.mouse.get_pos()
        radius = 120
        inner_alpha = 80
        ambient_alpha = 255

        dark = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dark.fill((0, 0, 0, ambient_alpha))
        pygame.draw.circle(dark, (0, 0, 0, inner_alpha), (mx, my), radius)

        diff = ambient_alpha - inner_alpha
        for i in range(30):
            a = int(inner_alpha + (i / 30) * diff)
            pygame.draw.circle(dark, (0, 0, 0, a), (mx, my), radius + i * 3, 6)

        surface.blit(dark, (0, 0))

    def _draw_cursor(self, surface):
        mx, my = pygame.mouse.get_pos()
        cursor = self.cur_clicked if self.is_clicked else self.cur_normal
        surface.blit(cursor, (mx - 8, my - 4))

    def _draw_game_over(self, surface):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        draw_text(surface, "ALL ROUNDS COMPLETE", 28, AMBER, CX, CY - 60, bold=True)
        draw_text(surface, f"FINAL SCORE:  {self.game.score} / {self.instr_sys.total_rounds}",
                  20, WHITE, CX, CY - 10)
        draw_text(surface, "[R] Restart     [ESC] Menu", 14, DIM_WHITE, CX, CY + 40)

    def _apply_distress_effects(self, surface):
        if self.distress_intensity <= 0:
            return

        blur_factor = 1.0 - (self.distress_intensity * 0.2)
        temp_w = max(1, int(SCREEN_W * blur_factor))
        temp_h = max(1, int(SCREEN_H * blur_factor))

        frame = surface.copy()
        small_frame = pygame.transform.smoothscale(frame, (temp_w, temp_h))
        blurred_frame = pygame.transform.scale(small_frame, (SCREEN_W, SCREEN_H))
        surface.blit(blurred_frame, (0, 0))

        fade_overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        fade_overlay.fill((0, 0, 0))
        alpha = int(self.distress_intensity * 200)
        fade_overlay.set_alpha(alpha)
        surface.blit(fade_overlay, (0, 0))

        if self.distress_intensity > 0.8:
            tiny_shake = 2
            surface.blit(surface, (random.randint(-tiny_shake, tiny_shake), 0))