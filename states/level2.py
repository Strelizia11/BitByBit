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
BULB_SIZE = (50, 80)
BULB_CENTER = (CX, CY + 30)

# ── HUD colours ───────────────────────────────────────────────────────────────
HUD_BG = (15, 15, 15)
INSTRUCTION_COL = (220, 220, 220)
ANOMALY_COL = (220, 220, 220)
FOLLOW_COL = GREEN_BRIGHT
IGNORE_COL = BLOOD_RED

# ── Window & Door layout (centred on the switch) ─────────────────────────────
WIN_W,  WIN_H  = 250, 300         # window image size
DOOR_W, DOOR_H = 300, 500        # door image size

# Switch is at BULB_CENTER = (CX, CY+30)
# Window sits to the LEFT of the switch
WIN_X = CX - 180 - WIN_W         # 180 px gap between switch and window
WIN_Y = CY + 30 - WIN_H // 2     # vertically centred on switch

# Door sits to the RIGHT of the switch
DOOR_X = CX + 180                # 180 px gap between switch and door
DOOR_Y = CY + 30 - DOOR_H // 2 +30 # vertically centred on switch


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


        # --- light switch images ---
        self.img_on = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "light-on1.png")).convert_alpha(),
            BULB_SIZE
        )
        self.img_off = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "light-off1.png")).convert_alpha(),
            BULB_SIZE
        )
        self.img_rect = self.img_on.get_rect(center=BULB_CENTER)

        # --- background images ---
        self.bg_lights_on = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "lvl2-background-lights-on.png")).convert(),
            (SCREEN_W, SCREEN_H)
        )
        self.bg_lights_off = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "lvl2-background-lights-off.png")).convert(),
            (SCREEN_W, SCREEN_H)
        )

        # --- window images (all 4 states) — scaled to WIN_W x WIN_H ---
        self.img_window_close_on  = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "window-close-on.png")).convert_alpha(),
            (WIN_W, WIN_H))
        self.img_window_open_on   = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "window-open-on.png")).convert_alpha(),
            (WIN_W, WIN_H))
        self.img_window_open_off  = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "window-open-off.png")).convert_alpha(),
            (WIN_W, WIN_H))
        self.img_window_close_off = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "window-close-off.png")).convert_alpha(),
            (WIN_W, WIN_H))

        # --- door images (all 4 states) — scaled to DOOR_W x DOOR_H ---
        self.img_door_close_on  = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "door-close-on.png")).convert_alpha(),
            (DOOR_W, DOOR_H))
        self.img_door_open_on   = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "door-open-on.png")).convert_alpha(),
            (DOOR_W, DOOR_H))
        self.img_door_open_off  = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "door-open-off.png")).convert_alpha(),
            (DOOR_W, DOOR_H))
        self.img_door_close_off = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "door-close-off.png")).convert_alpha(),
            (DOOR_W, DOOR_H))

        # Rects — window LEFT of switch, door RIGHT of switch
        self.window_img_rect = self.img_window_close_on.get_rect(topleft=(WIN_X, WIN_Y))
        self.door_img_rect   = self.img_door_close_on.get_rect(topleft=(DOOR_X, DOOR_Y))

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

        # --- door state: START WITH CLOSED ---
        self.door_open = False
        self.door_rect = pygame.Rect(DOOR_X, DOOR_Y, DOOR_W, DOOR_H)

        # --- window state: START WITH CLOSED ---
        self.window_open = False
        # Click hitbox matches the window image position and size
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

        self.jumpscare = pygame.image.load(os.path.join("assets", "jumpscare.jpg")).convert()
        self.jumpscare = pygame.transform.scale(self.jumpscare, (SCREEN_W, SCREEN_H))

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

            # Window click
            if self.window_rect.collidepoint(event.pos):
                self.window_open = not self.window_open
                self.window_clicks_this_round += 1

                if self.window_open:
                    audio.play("window_open", channel="window")
                else:
                    audio.play("window_close", channel="window")

            # Door click (NEW)
            elif self.door_rect.collidepoint(event.pos):
                self.door_open = not self.door_open

                # Optional sounds (add if you have them)
                if self.door_open:
                    audio.play("door_open", channel="door")
                else:
                    audio.play("door_close", channel="door")

            # Switch click
            elif self.img_rect.collidepoint(event.pos):
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
                    audio.play("intense", channel="jumpscare")
            elif self.death_phase == 666:
                if self.death_timer > 4.0:
                    if "jumpscare" in audio.channels:
                        audio.channels["jumpscare"].stop()
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
        # ── Background: swap based on light state ─────────────────────────────
        bg = self.bg_lights_on if self.light_on else self.bg_lights_off
        surface.blit(bg, (0, 0))

        # ── Light switch bulb image ───────────────────────────────────────────
        img = self.img_on if self.light_on else self.img_off
        surface.blit(img, self.img_rect)

        # ── Window: all 4 states (open/close × lights on/off) ─────────────────
        if self.light_on and not self.window_open:
            surface.blit(self.img_window_close_on, self.window_img_rect)
        elif self.light_on and self.window_open:
            surface.blit(self.img_window_open_on, self.window_img_rect)
        elif not self.light_on and self.window_open:
            surface.blit(self.img_window_open_off, self.window_img_rect)
        else:  # lights off + window closed
            surface.blit(self.img_window_close_off, self.window_img_rect)

        # ── Door: all 4 states (open/close × lights on/off) ───────────────────
        # ── Door: all 4 states (FIXED - uses door_open now) ──
        if self.light_on and not self.door_open:
            surface.blit(self.img_door_close_on, self.door_img_rect)
        elif self.light_on and self.door_open:
            surface.blit(self.img_door_open_on, self.door_img_rect)
        elif not self.light_on and self.door_open:
            surface.blit(self.img_door_open_off, self.door_img_rect)
        else:
            surface.blit(self.img_door_close_off, self.door_img_rect)

        if not self.light_on:
            self._draw_flashlight(surface)
        self._draw_hud(surface)
        if not self.game_over:
            self._apply_distress_effects(surface)
            self._draw_cursor(surface)
        else:
            self._draw_game_over(surface)

            if self.death_phase == 666:
                surface.blit(self.jumpscare, (0, 0))
                if self.death_timer > 3.8:
                    surface.fill((0, 0, 0))
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

        # Round 1 of Level 2 is always this specific anomaly instruction
        if self.instr_sys.current_round == 1:
            self.current_text = "IT SAYS CLICK THE SWITCH 3 TIMES"
            self.current_is_anomaly = True
            self.current_base_rule = "SIMON SAYS CLICK THE SWITCH 3 TIMES"
        else:
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

        alpha = int(self.instr_alpha * 255)
        # ── TEXTBOX SETTINGS ─────────────────────────
        box_width = 700
        box_height = 80
        box_x = CX - box_width // 2
        box_y = HUD_H + 40

        # ── COLOR CHANGE BASED ON LIGHT ──────────────
        if self.light_on:
            text_color = BLACK
            border_color = BLACK
            fill_alpha = 0
        else:
            text_color = BLOOD_RED
            border_color = BLOOD_RED
            fill_alpha = 50

        # ── DRAW TRANSPARENT BOX ────────────────────────────────
        box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        box_surface.fill((*border_color, fill_alpha))

        # Draw border directly on the transparent surface
        pygame.draw.rect(box_surface, (*border_color, 255), (0, 0, box_width, box_height), 3, border_radius=12)

        # Blit the transparent box onto your main surface
        surface.blit(box_surface, (box_x, box_y))

        # ── TEXT INSIDE BOX ─────────────────────────
        draw_text(
            surface,
            self.current_text,
            25,
            text_color,
            CX,
            box_y + box_height // 2,
            bold=True,
            alpha=alpha
        )

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
