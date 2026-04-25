import os
import math
import pygame
from states.base import BaseState
from system.instruction_system import InstructionSystem
from utils import (
    draw_text, draw_rect_border, draw_rect_filled,
    NEAR_BLACK, DARK_GRAY, MID_GRAY, DIM_WHITE, WHITE,
    BLOOD_RED, AMBER, AMBER_DIM, BLACK, GREEN_DIM, GREEN_BRIGHT,
    SCREEN_W, SCREEN_H, CX, CY, get_font, lerp_color
)

# ── Layout constants ───────────────────────────────────────────────────────────
HUD_H        = 52
BULB_SIZE    = (80, 120)
BULB_CENTER  = (CX, CY + 30)

# ── HUD colours ───────────────────────────────────────────────────────────────
HUD_BG          = (15, 15, 15)
INSTRUCTION_COL = (220, 220, 220)
ANOMALY_COL     = (200,  60,  60)
FOLLOW_COL      = GREEN_BRIGHT
IGNORE_COL      = BLOOD_RED


class GameState(BaseState):

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def on_enter(self, **kwargs):
        # --- images ---
        self.img_on  = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "light-on.png")).convert_alpha(),
            BULB_SIZE
        )
        self.img_off = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "light-off.png")).convert_alpha(),
            BULB_SIZE
        )
        self.img_rect = self.img_on.get_rect(center=BULB_CENTER)

        # --- cursor images ---
        self.cur_normal  = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "hand.png")).convert_alpha(),
            (32, 32)
        )
        self.cur_clicked = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "hand_clicked.png")).convert_alpha(),
            (32, 32)
        )
        pygame.mouse.set_visible(False)

        # --- light state ---
        self.light_on = True
        self.is_clicked = False

        self.instr_sys = InstructionSystem(total_rounds=8)
        self.instr_sys.reset()

        # --- New Timer & Tracking Variables ---
        self.round_time_limit = 4.0  # Player has 4 seconds to complete the action
        self.round_timer = 0.0
        self.clicks_this_round = 0
        self.start_light_state = self.light_on

        self.current_text = ""
        self.current_anomaly = False
        self.game_over = False

        self._load_next_instruction()

        self.instr_alpha = 0.0
        self.instr_pulse = 0.0

    # ── Input ─────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.on_enter()
                elif event.key == pygame.K_ESCAPE:
                    pygame.mouse.set_visible(True) # <-- Restore the cursor
                    self.game.switch_state("menu")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_clicked = True
            if self.img_rect.collidepoint(event.pos):
                self.light_on = not self.light_on
                self.clicks_this_round += 1  # Track the click!

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_clicked = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.mouse.set_visible(True) # <-- Restore the cursor here too
                self.game.switch_state("menu")

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, dt):
        if self.game_over:
            return

        self.instr_alpha = min(1.0, self.instr_alpha + dt * 2.5)
        self.instr_pulse += dt

        # Run the timer
        self.round_timer += dt
        if self.round_timer >= self.round_time_limit:
            self._resolve_round()

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        surface.fill((255, 255, 255))

        img = self.img_on if self.light_on else self.img_off
        surface.blit(img, self.img_rect)

        if not self.light_on:
            self._draw_flashlight(surface)

        self._draw_hud(surface)

        if not self.game_over:
            self._draw_cursor(surface)
        else:
            self._draw_game_over(surface)

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _load_next_instruction(self):
        result = self.instr_sys.next_instruction()
        if result is None:
            self.game_over = True
            return
        self.current_text    = result[0]
        self.current_anomaly = result[1]
        self.correct_action  = InstructionSystem.correct_action(
            self.current_anomaly, self.light_on
        )
        self.instr_alpha = 0.0
        self.instr_pulse = 0.0

    def _resolve(self, player_action: str):
        if player_action == self.correct_action:
            self.game.score += 1
        self._load_next_instruction()

    def _load_next_instruction(self):
        # Pass the current light state to dynamically get the right instruction
        result = self.instr_sys.next_instruction(self.light_on)

        if result is None:
            self.game_over = True
            return

        self.current_text = result[0]
        self.current_anomaly = result[1]

        # Reset tracking for the new round
        self.round_timer = 0.0
        self.clicks_this_round = 0
        self.start_light_state = self.light_on

        self.instr_alpha = 0.0
        self.instr_pulse = 0.0

    def _resolve_round(self):
        # Did the player follow the normal rules correctly?
        success = self.instr_sys.evaluate_normal_action(
            self.current_text,
            self.start_light_state,
            self.clicks_this_round
        )

        if success:
            self.game.score += 1
            self._load_next_instruction()
        else:
            # You stated that failing any condition results in game over
            self.game_over = True
    # ── Visual methods ────────────────────────────────────────────────────────
    def _draw_hud(self, surface):
        pygame.draw.rect(surface, HUD_BG, (0, 0, SCREEN_W, HUD_H))

        if self.game_over:
            draw_text(surface, "ROUND COMPLETE", 18, AMBER, CX, HUD_H // 2, bold=True)
            return

        alpha = int(self.instr_alpha * 255)

        # Light state badge (left)
        badge_col = AMBER if self.light_on else (50, 90, 170)
        badge_lbl = "LIGHT: ON" if self.light_on else "LIGHT: OFF"
        draw_text(surface, badge_lbl, 12, badge_col, 68, HUD_H // 2)

        # Instruction text (centre) with pulse
        pulse_t   = 0.5 + 0.5 * math.sin(self.instr_pulse * 4.0)
        base_col  = ANOMALY_COL if self.current_anomaly else INSTRUCTION_COL
        pulse_col = lerp_color(base_col, WHITE, pulse_t * 0.15)
        draw_text(surface, self.current_text, 20, pulse_col, CX, HUD_H // 2, bold=True, alpha=alpha)

        # Key hints (right) + score

        draw_text(surface, f"SCORE: {self.game.score}", 11, MID_GRAY, SCREEN_W - 95, HUD_H // 2 + 10)

    def _draw_flashlight(self, surface):
        mx, my        = pygame.mouse.get_pos()
        radius        = 120
        inner_alpha   = 80
        ambient_alpha = 220

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

        draw_text(surface, "ALL ROUNDS COMPLETE", 28, AMBER,    CX, CY - 60, bold=True)
        draw_text(surface, f"FINAL SCORE:  {self.game.score} / {self.instr_sys.total_rounds}",
                  20, WHITE, CX, CY - 10)
        draw_text(surface, "[R] Restart     [ESC] Menu", 14, DIM_WHITE, CX, CY + 40)