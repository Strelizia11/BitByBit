import os
import math
import pygame
import random
from states.base import BaseState
from states.audio_manager import AudioManager
audio = AudioManager()
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
        audio.play_music("ambience", loop=True)
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

        # --- cobweb obstacle (modified) ---
        self.cobweb_visible     = True
        self.cobweb_timer       = 0.0
        self.cobweb_respawn_at  = random.uniform(2.0, 3.0)
        self.cobweb_clicks      = 0 # New tracking for 3-click health[cite: 1]
        self._randomize_cobweb_pos() # Initialize random start position[cite: 1]

        # --- level transition cutscene ---
        self.trans_phase  = TRANS_IDLE
        self.trans_timer  = 0.0
        self.typed_chars  = 0.0
        self.blackout_alpha = 0
        self.hand_y_offscreen = SCREEN_H + 20
        self.hand_y = float(self.hand_y_offscreen)
        self.hand_target_y = float(BULB_CENTER[1] - 10)

    def _randomize_cobweb_pos(self):
        """Generates a new position for the cobweb within a radius of the switch[cite: 1]"""
        offset_x = random.randint(-60, 60) # Random horizontal offset[cite: 1]
        offset_y = random.randint(-40, 40) # Random vertical offset[cite: 1]
        self.cobweb_rect = pygame.Rect(
            BULB_CENTER[0] - 45 + offset_x, 
            BULB_CENTER[1] - 35 + offset_y,
            90, 90
        )

    # ── Input ─────────────────────────────────────────────────────────────────
    def handle_event(self, event):
        if self.trans_phase != TRANS_IDLE:
            return

        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    audio.stop_music()
                    self.on_enter()
                elif event.key == pygame.K_ESCAPE:
                    audio.stop_music()                   
                    pygame.mouse.set_visible(True)
                    self.game.switch_state("menu")
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_clicked = True
            
            # Modified: Check if cobweb is clicked and handle 3-click logic[cite: 1]
            if self.cobweb_visible and self.cobweb_rect.collidepoint(event.pos):
                self.cobweb_clicks += 1
                if self.cobweb_clicks >= 3: # Requires 3 clicks to disappear[cite: 1]
                    self.cobweb_visible    = False
                    self.cobweb_timer      = 0.0
                    self.cobweb_respawn_at = random.uniform(2.0, 3.0)
                    self.cobweb_clicks     = 0 # Reset health for next respawn[cite: 1]
            
            # Only allow switch click if cobweb is removed[cite: 1]
            elif not self.cobweb_visible and self.img_rect.collidepoint(event.pos):
                self.light_on = not self.light_on
                self.clicks_this_round += 1
                
                if self.light_on:
                    audio.play("switch_on", channel="switch")
                else:
                    audio.play("switch_off", channel="switch")

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_clicked = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.mouse.set_visible(True)
                self.game.switch_state("menu")

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, dt):
        if self.trans_phase != TRANS_IDLE:
            self._update_transition(dt)
            return

        if not self.game_over:
            self.instr_alpha = min(1.0, self.instr_alpha + dt * 2.5)
            self.instr_pulse += dt

            # ── Cobweb respawn timer (modified) ────────────────────────────────
            if not self.cobweb_visible:
                self.cobweb_timer += dt
                if self.cobweb_timer >= self.cobweb_respawn_at:
                    self.cobweb_visible    = True
                    self.cobweb_timer      = 0.0
                    self.cobweb_respawn_at = random.uniform(2.0, 3.0)
                    self._randomize_cobweb_pos() # Move to a new spot near switch[cite: 1]

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
            duration = 1.2
            t = min(1.0, self.trans_timer / duration)
            ease = 1 - (1 - t) ** 3
            self.hand_y = self.hand_y_offscreen + (self.hand_target_y - self.hand_y_offscreen) * ease
            if self.trans_timer >= duration:
                self.trans_phase = TRANS_HAND_CLICK
                self.trans_timer = 0.0
        elif self.trans_phase == TRANS_HAND_CLICK:
            if self.trans_timer >= 0.2:
                self.light_on = False
            if self.trans_timer >= 0.4:
                self.trans_phase = TRANS_HAND_EXIT
                self.trans_timer = 0.0
        elif self.trans_phase == TRANS_HAND_EXIT:
            duration = 0.8
            t = min(1.0, self.trans_timer / duration)
            ease = t ** 2
            self.hand_y = self.hand_target_y + (self.hand_y_offscreen - self.hand_target_y) * ease
            if self.trans_timer >= duration:
                self.trans_phase = TRANS_BLACKOUT
                self.trans_timer = 0.0
        elif self.trans_phase == TRANS_BLACKOUT:
            t = min(1.0, self.trans_timer / 0.8)
            self.blackout_alpha = int(t * 255)
            if self.trans_timer >= 0.8:
                self.blackout_alpha = 255
                self.trans_phase = TRANS_TYPING
                self.trans_timer = 0.0
                self.typed_chars = 0.0
        elif self.trans_phase == TRANS_TYPING:
            self.typed_chars += TYPING_SPEED * dt
            if self.typed_chars >= len(CUTSCENE_MSG):
                self.typed_chars = float(len(CUTSCENE_MSG))
                if self.trans_timer >= 3.0:
                    self.trans_phase = TRANS_TO_LVL2
                    self.trans_timer = 0.0
        elif self.trans_phase == TRANS_TO_LVL2:
            if self.trans_timer >= 1.0:
                pygame.mouse.set_visible(True)
                self.game.switch_state("level2")

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surface):
        if self.trans_phase != TRANS_IDLE:
            self._draw_transition(surface)
            return

        if not self.game_over:
            surface.fill((255, 255, 255))
            img = self.img_on if self.light_on else self.img_off
            surface.blit(img, self.img_rect)

            if self.cobweb_visible:
                self._draw_cobweb(surface)

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
        surface.fill((255, 255, 255))
        img = self.img_on if self.light_on else self.img_off
        surface.blit(img, self.img_rect)
        self._draw_hud(surface)

        if self.trans_phase in (TRANS_HAND_RISE, TRANS_HAND_CLICK, TRANS_HAND_EXIT):
            hx = CX - self.simon_hand_img.get_width() // 2
            hy = int(self.hand_y)
            surface.blit(self.simon_hand_img, (hx, hy))

        if self.trans_phase in (TRANS_BLACKOUT, TRANS_TYPING, TRANS_TO_LVL2):
            overlay = pygame.Surface((SCREEN_W, SCREEN_H))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.blackout_alpha)
            surface.blit(overlay, (0, 0))

        if self.trans_phase in (TRANS_TYPING, TRANS_TO_LVL2):
            shown = CUTSCENE_MSG[:int(self.typed_chars)]
            draw_text(surface, shown, 22, WHITE, CX, CY, bold=True)

    def _load_next_instruction(self):
        result = self.instr_sys.next_instruction(self.light_on)
        if result is None:
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

    def _draw_hud(self, surface):
        pygame.draw.rect(surface, HUD_BG, (0, 0, SCREEN_W, HUD_H))
        if self.game_over:
            draw_text(surface, "ROUND COMPLETE", 18, AMBER, CX, HUD_H // 2, bold=True)
            return
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
        draw_text(surface, self.current_text, 20, pulse_col, CX, HUD_H // 2, bold=True, alpha=alpha)
        time_left = max(0.0, self.round_time_limit - self.round_timer)
        time_col  = AMBER if time_left > 1.5 else BLOOD_RED
        draw_text(surface, f"TIME: {time_left:.1f}s", 14, time_col, SCREEN_W - 80, HUD_H // 2 - 10)
        draw_text(surface, f"SCORE: {self.game.score}", 11, MID_GRAY, SCREEN_W - 80, HUD_H // 2 + 10)

    def _draw_cobweb(self, surface):
        cx, cy = self.cobweb_rect.center
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = cx + math.cos(rad) * 3
            y1 = cy + math.sin(rad) * 3
            x2 = cx + math.cos(rad) * 45
            y2 = cy + math.sin(rad) * 45
            pygame.draw.line(surface, (200, 200, 210), (x1, y1), (x2, y2), 1)
        for r in [15, 30, 45]:
            pygame.draw.circle(surface, (200, 200, 210), (cx, cy), r, 1)
        pygame.draw.circle(surface, (40, 40, 40), (cx, cy), 8)
        pygame.draw.circle(surface, (60, 60, 60), (cx, cy), 6)

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
        draw_text(surface, f"FINAL SCORE:  {self.game.score} / {self.instr_sys.total_rounds}", 20, WHITE, CX, CY - 10)
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