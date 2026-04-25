import os
import math
import pygame
import random
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
ANOMALY_COL     = (220, 220, 220)
FOLLOW_COL      = GREEN_BRIGHT
IGNORE_COL      = BLOOD_RED

# ── Transition phases ─────────────────────────────────────────────────────────
# TRANS_IDLE      : not yet triggered
# TRANS_HAND_RISE : simon_hand.png slides up from below onto the switch   (1.2 s)
# TRANS_HAND_CLICK: hand pauses at switch, light toggles OFF               (0.4 s)
# TRANS_HAND_EXIT : hand slides back down off-screen                       (0.8 s)
# TRANS_BLACKOUT  : screen fades to pitch black                            (0.8 s)
# TRANS_TYPING    : "Simon turns the lights off for you" types out         (3.0 s)
# TRANS_TO_LVL2   : brief pause then switch to level2 state                (1.0 s)

TRANS_IDLE       = 0
TRANS_HAND_RISE  = 1
TRANS_HAND_CLICK = 2
TRANS_HAND_EXIT  = 3
TRANS_BLACKOUT   = 4
TRANS_TYPING     = 5
TRANS_TO_LVL2    = 6

CUTSCENE_MSG = "Simon turns the lights off for you"
TYPING_SPEED = 18   # characters per second


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

        # --- simon hand image for cutscene ---
        simon_hand_path = os.path.join("assets", "simon_hand.png")
        raw_hand = pygame.image.load(simon_hand_path).convert_alpha()
        self.simon_hand_img = pygame.transform.scale(raw_hand, (120, 160))

        # --- light state ---
        self.light_on   = True
        self.is_clicked = False

        self.instr_sys = InstructionSystem(total_rounds=8)
        self.instr_sys.reset()

        # --- timer & tracking ---
        self.round_time_limit  = 6.0
        self.round_timer       = 0.0
        self.clicks_this_round = 0
        self.start_light_state = self.light_on

        self.current_text    = ""
        self.current_anomaly = False
        self.game_over       = False

        self._load_next_instruction()

        self.instr_alpha       = 0.0
        self.instr_pulse       = 0.0
        self.distress_intensity = 0.0
        self.game_over         = False

        # --- death sequence ---
        self.death_timer = 0.0
        self.death_phase = 0

        self.death_img = pygame.image.load(os.path.join("assets", "girl.jpg")).convert()
        self.death_img = pygame.transform.scale(self.death_img, (SCREEN_W, SCREEN_H))

        # --- level transition cutscene ---
        self.trans_phase  = TRANS_IDLE
        self.trans_timer  = 0.0
        self.typed_chars  = 0.0        # float chars revealed so far
        self.blackout_alpha = 0        # 0-255 for the black overlay
        # simon_hand y position (screen coords); starts fully below screen
        self.hand_y_offscreen = SCREEN_H + 20
        self.hand_y = float(self.hand_y_offscreen)
        # target y when hand is at the switch
        self.hand_target_y = float(BULB_CENTER[1] - 10)

    # ── Input ─────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        # Block all player input during the transition cutscene
        if self.trans_phase != TRANS_IDLE:
            return

        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.on_enter()
                elif event.key == pygame.K_ESCAPE:
                    pygame.mouse.set_visible(True)
                    self.game.switch_state("menu")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_clicked = True
            if self.img_rect.collidepoint(event.pos):
                self.light_on = not self.light_on
                self.clicks_this_round += 1

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_clicked = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.mouse.set_visible(True)
                self.game.switch_state("menu")

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, dt):
        # ── Cutscene update ───────────────────────────────────────────────────
        if self.trans_phase != TRANS_IDLE:
            self._update_transition(dt)
            return

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

    def _update_transition(self, dt):
        self.trans_timer += dt

        if self.trans_phase == TRANS_HAND_RISE:
            # Slide hand up toward the switch over 1.2 s
            duration = 1.2
            t = min(1.0, self.trans_timer / duration)
            # ease-out cubic
            ease = 1 - (1 - t) ** 3
            self.hand_y = self.hand_y_offscreen + (self.hand_target_y - self.hand_y_offscreen) * ease
            if self.trans_timer >= duration:
                self.trans_phase = TRANS_HAND_CLICK
                self.trans_timer = 0.0

        elif self.trans_phase == TRANS_HAND_CLICK:
            # Pause briefly then toggle the light OFF
            if self.trans_timer >= 0.2:
                self.light_on = False          # Simon turns off the light
            if self.trans_timer >= 0.4:
                self.trans_phase = TRANS_HAND_EXIT
                self.trans_timer = 0.0

        elif self.trans_phase == TRANS_HAND_EXIT:
            # Slide hand back down off-screen over 0.8 s
            duration = 0.8
            t = min(1.0, self.trans_timer / duration)
            ease = t ** 2                      # ease-in
            self.hand_y = self.hand_target_y + (self.hand_y_offscreen - self.hand_target_y) * ease
            if self.trans_timer >= duration:
                self.trans_phase = TRANS_BLACKOUT
                self.trans_timer = 0.0

        elif self.trans_phase == TRANS_BLACKOUT:
            # Fade screen to pitch black over 0.8 s
            t = min(1.0, self.trans_timer / 0.8)
            self.blackout_alpha = int(t * 255)
            if self.trans_timer >= 0.8:
                self.blackout_alpha = 255
                self.trans_phase = TRANS_TYPING
                self.trans_timer = 0.0
                self.typed_chars = 0.0

        elif self.trans_phase == TRANS_TYPING:
            # Typewriter reveal of CUTSCENE_MSG
            self.typed_chars += TYPING_SPEED * dt
            if self.typed_chars >= len(CUTSCENE_MSG):
                self.typed_chars = float(len(CUTSCENE_MSG))
                if self.trans_timer >= 3.0:
                    self.trans_phase = TRANS_TO_LVL2
                    self.trans_timer = 0.0

        elif self.trans_phase == TRANS_TO_LVL2:
            # Brief pause then jump to level 2
            if self.trans_timer >= 1.0:
                pygame.mouse.set_visible(True)
                self.game.switch_state("level2")

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        # ── Cutscene drawing ──────────────────────────────────────────────────
        if self.trans_phase != TRANS_IDLE:
            self._draw_transition(surface)
            return

        # ── Normal gameplay drawing ───────────────────────────────────────────
        if not self.game_over:
            surface.fill((255, 255, 255))

            img = self.img_on if self.light_on else self.img_off
            surface.blit(img, self.img_rect)

            self._draw_hud(surface)

            if not self.light_on:
                self._draw_flashlight(surface)

            if not self.game_over:
                self._apply_distress_effects(surface)
                self._draw_cursor(surface)
            else:
                self._draw_game_over(surface)
        else:
            surface.fill((0, 0, 0))

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

    def _draw_transition(self, surface):
        # Base: still show the gameplay scene underneath until blackout
        surface.fill((255, 255, 255))
        img = self.img_on if self.light_on else self.img_off
        surface.blit(img, self.img_rect)
        self._draw_hud(surface)

        # Draw simon hand sliding in/out
        if self.trans_phase in (TRANS_HAND_RISE, TRANS_HAND_CLICK, TRANS_HAND_EXIT):
            hx = CX - self.simon_hand_img.get_width() // 2
            hy = int(self.hand_y)
            surface.blit(self.simon_hand_img, (hx, hy))

        # Black overlay growing during blackout / fully black during typing+
        if self.trans_phase in (TRANS_BLACKOUT, TRANS_TYPING, TRANS_TO_LVL2):
            overlay = pygame.Surface((SCREEN_W, SCREEN_H))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.blackout_alpha)
            surface.blit(overlay, (0, 0))

        # Typewriter text
        if self.trans_phase in (TRANS_TYPING, TRANS_TO_LVL2):
            shown = CUTSCENE_MSG[:int(self.typed_chars)]
            draw_text(surface, shown, 22, WHITE, CX, CY, bold=True)

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _load_next_instruction(self):
        result = self.instr_sys.next_instruction(self.light_on)

        if result is None:
            # All 8 rounds done successfully → trigger the cutscene
            self._start_transition()
            return

        self.current_text        = result[0]
        self.current_anomaly     = result[1]
        self.current_base_rule   = result[2]

        self.round_timer          = 0.0
        self.clicks_this_round    = 0
        self.start_light_state    = self.light_on

        self.instr_alpha = 0.0
        self.instr_pulse = 0.0

    def _start_transition(self):
        """Begin the level-1 → level-2 cutscene."""
        self.trans_phase = TRANS_HAND_RISE
        self.trans_timer = 0.0
        self.hand_y      = float(self.hand_y_offscreen)
        self.blackout_alpha = 0
        self.typed_chars = 0.0

    def _resolve_round(self):
        success = self.instr_sys.evaluate_action(
            self.current_base_rule,
            self.current_anomaly,
            self.start_light_state,
            self.clicks_this_round
        )

        if success:
            self.game.score += 1
            self._load_next_instruction()
        else:
            self.game_over   = True
            self.death_timer = 0.0

            if random.random() < 0.2:
                self.death_phase = 4
            else:
                self.death_phase = 1

            pygame.mouse.set_visible(False)

    # ── Visual helpers ────────────────────────────────────────────────────────
    def _draw_hud(self, surface):
        pygame.draw.rect(surface, HUD_BG, (0, 0, SCREEN_W, HUD_H))

        if self.game_over:
            draw_text(surface, "ROUND COMPLETE", 18, AMBER, CX, HUD_H // 2, bold=True)
            return

        # During cutscene show a neutral HUD
        if self.trans_phase != TRANS_IDLE:
            draw_text(surface, "LEVEL 1 COMPLETE", 16, AMBER, CX, HUD_H // 2, bold=True)
            return

        alpha = int(self.instr_alpha * 255)

        badge_col = AMBER if self.light_on else (50, 90, 170)
        badge_lbl = "LIGHT: ON" if self.light_on else "LIGHT: OFF"
        draw_text(surface, badge_lbl, 12, badge_col, 68, HUD_H // 2)

        pulse_t   = 0.5 + 0.5 * math.sin(self.instr_pulse * 4.0)
        base_col  = ANOMALY_COL if self.current_anomaly else INSTRUCTION_COL
        pulse_col = lerp_color(base_col, WHITE, pulse_t * 0.15)
        draw_text(surface, self.current_text, 20, pulse_col, CX, HUD_H // 2,
                  bold=True, alpha=alpha)

        time_left = max(0.0, self.round_time_limit - self.round_timer)
        time_col  = AMBER if time_left > 1.5 else BLOOD_RED

        draw_text(surface, f"TIME: {time_left:.1f}s", 14, time_col,
                  SCREEN_W - 80, HUD_H // 2 - 10)
        draw_text(surface, f"SCORE: {self.game.score}", 11, MID_GRAY,
                  SCREEN_W - 80, HUD_H // 2 + 10)

    def _draw_flashlight(self, surface):
        mx, my        = pygame.mouse.get_pos()
        radius        = 120
        inner_alpha   = 80
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

        frame        = surface.copy()
        small_frame  = pygame.transform.smoothscale(frame, (temp_w, temp_h))
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