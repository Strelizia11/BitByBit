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
        self.round_time_limit = 6.0  # Player has 6 seconds to complete the action
        self.round_timer = 0.0
        self.clicks_this_round = 0
        self.start_light_state = self.light_on

        self.current_text = ""
        self.current_anomaly = False
        self.game_over = False

        self._load_next_instruction()

        self.instr_alpha = 0.0
        self.instr_pulse = 0.0

        self.distress_intensity = 0.0

        self.game_over = False
    
        # New sequence variables
        self.death_timer = 0.0
        self.death_phase = 0  # 0: Playing, 1: Pitch Black, 2: Image Fade In, 3: Final Fade Out
        
        # Load your "scare" or "fail" image
        self.death_img = pygame.image.load("./assets/girl.jpg").convert()
        self.death_img = pygame.transform.scale(self.death_img, (SCREEN_W, SCREEN_H))

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
        if not self.game_over:
            self.instr_alpha = min(1.0, self.instr_alpha + dt * 2.5)
            self.instr_pulse += dt

            # --- Intensity Logic ---
            time_left = max(0.0, self.round_time_limit - self.round_timer)
            
            if time_left < 3.0:
                # Ramps from 0.0 at 3s to 1.0 at 0s
                self.distress_intensity = 1.0 - (time_left / 3.0)
            else:
                self.distress_intensity = 0.0

            # Run the timer
            self.round_timer += dt
            if self.round_timer >= self.round_time_limit:
                self._resolve_round()
        else:
            self.death_timer += dt

            # --- Jumpscare Sequence Logic ---
            # Phase 4: The 2-second silence before the scare
            if self.death_phase == 4:
                if self.death_timer > 2.0:
                    self.death_phase = 666
                    self.death_timer = 0.0 # Reset for the 4-second scare
            
            # Phase 666: The actual Jumpscare
            elif self.death_phase == 666:
                if self.death_timer > 4.0: # Lasts 4 seconds
                    pygame.mouse.set_visible(True)
                    self.game.switch_state("menu")

            # --- Normal Sequence Logic (Phases 1, 2, 3) ---
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
        if not self.game_over:
            # 1. Clear background
            surface.fill((255, 255, 255))

            # 2. Draw the Lightbulb
            img = self.img_on if self.light_on else self.img_off
            surface.blit(img, self.img_rect)

            # 3. Draw the HUD (The task instructions)
            # Drawing it now means it will be affected by the flashlight layer
            self._draw_hud(surface)

            # 4. Draw the Flashlight/Darkness (Only if light is off)
            if not self.light_on:
                self._draw_flashlight(surface)

            # 5. Draw UI/Effects that should ALWAYS be visible
            if not self.game_over:
                self._apply_distress_effects(surface)
                self._draw_cursor(surface) # Cursor stays on top so player can see where they are
            else:
                self._draw_game_over(surface)
        else:
            # Drawing the Death Sequence
            surface.fill((0, 0, 0)) # Base is always black

            # --- Jumpscare Drawing ---
            if self.death_phase == 666:
                # The Jumpscare: Full brightness, no fading
                surface.blit(self.death_img, (0, 0))

            elif self.death_phase == 2:
                # Normal fade-in logic
                alpha = min(255, int((self.death_timer / 2.0) * 255))
                temp_img = self.death_img.copy()
                temp_img.set_alpha(alpha)
                surface.blit(temp_img, (0, 0))
                
            elif self.death_phase == 3:
                # Normal fade-out logic
                alpha = max(0, 255 - int((self.death_timer / 2.0) * 255))
                temp_img = self.death_img.copy()
                temp_img.set_alpha(alpha)
                surface.blit(temp_img, (0, 0))

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _load_next_instruction(self):
        result = self.instr_sys.next_instruction(self.light_on)

        if result is None:
            self.game_over = True
            return

        self.current_text = result[0]
        self.current_anomaly = result[1]
        self.current_base_rule = result[2]

        # Reset tracking for the new round
        self.round_timer = 0.0
        self.clicks_this_round = 0
        self.start_light_state = self.light_on

        self.instr_alpha = 0.0
        self.instr_pulse = 0.0

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
            self.game_over = True
            self.death_timer = 0.0

            # --- 1/5 Chance for Jumpscare Sequence ---
            if random.random() < 0.2:
                self.death_phase = 4  # Start with the 2-second silence
            else:
                self.death_phase = 1  # Start normal sequence
                
            pygame.mouse.set_visible(False)
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
        pulse_t = 0.5 + 0.5 * math.sin(self.instr_pulse * 4.0)
        base_col = ANOMALY_COL if self.current_anomaly else INSTRUCTION_COL
        pulse_col = lerp_color(base_col, WHITE, pulse_t * 0.15)
        draw_text(surface, self.current_text, 20, pulse_col, CX, HUD_H // 2, bold=True, alpha=alpha)

        # --- NEW: Timer and Score (right) ---
        time_left = max(0.0, self.round_time_limit - self.round_timer)
        time_col = AMBER if time_left > 1.5 else BLOOD_RED  # Turns red when time is almost up

        draw_text(surface, f"TIME: {time_left:.1f}s", 14, time_col, SCREEN_W - 80, HUD_H // 2 - 10)
        draw_text(surface, f"SCORE: {self.game.score}", 11, MID_GRAY, SCREEN_W - 80, HUD_H // 2 + 10)

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

        draw_text(surface, "ALL ROUNDS COMPLETE", 28, AMBER,    CX, CY - 60, bold=True)
        draw_text(surface, f"FINAL SCORE:  {self.game.score} / {self.instr_sys.total_rounds}",
                  20, WHITE, CX, CY - 10)
        draw_text(surface, "[R] Restart     [ESC] Menu", 14, DIM_WHITE, CX, CY + 40)

    import random

    def _apply_distress_effects(self, surface):
        if self.distress_intensity <= 0:
            return

        blur_factor = 1.0 - (self.distress_intensity * 0.2) 
        temp_w = int(SCREEN_W * blur_factor)
        temp_h = int(SCREEN_H * blur_factor)

        frame = surface.copy()
        small_frame = pygame.transform.smoothscale(frame, (temp_w, temp_h))
        blurred_frame = pygame.transform.scale(small_frame, (SCREEN_W, SCREEN_H))
        
        # Draw the blurred version back
        surface.blit(blurred_frame, (0, 0))

        # --- 2. THE FADE OUT ---
        # Create a black surface the size of the screen
        fade_overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        fade_overlay.fill((0, 0, 0))
        
        # Set alpha: 0 is transparent, 255 is solid black
        # We'll cap it at 200 so the player can still barely see at the last second
        alpha = int(self.distress_intensity * 200)
        fade_overlay.set_alpha(alpha)
        
        surface.blit(fade_overlay, (0, 0))

        # --- 3. REDUCED SHAKE (Optional) ---
        # If you want just a tiny "shiver" instead of a heavy shake:
        if self.distress_intensity > 0.8:
            tiny_shake = 2 
            surface.blit(surface, (random.randint(-tiny_shake, tiny_shake), 0))