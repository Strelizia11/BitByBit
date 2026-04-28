import pygame
import random
import math
import subprocess
import os
from states.base import BaseState
from states.audio_manager import AudioManager
from utils import (
    draw_text,
    NEAR_BLACK, DIM_WHITE, MID_GRAY,
    BLOOD_RED, BLACK,
    SCREEN_W, SCREEN_H, CX, CY, get_font
)

SCALE = SCREEN_H / 600

audio = AudioManager()




SZ_MAIN = max(24, int(42 * SCALE))
SZ_SUB  = max(16, int(26 * SCALE))


def _flicker(t, seed=0.0):
    return 0.85 + 0.15 * abs(
        math.sin(t * 7.3 + seed) * math.sin(t * 13.1 + seed * 2.7)
    )


class EndingState(BaseState):

    def on_enter(self, **kwargs):
        pygame.mouse.set_visible(False)
        audio.play("ending", channel="ending", duration=6.5, fadeout=0.5)
        self.time = 0.0
        self.phase_time = 0.0

        self.base_text = "SIMON SAYS YOU CANNOT LEAVE"
        self.alt_text = "YOU CANNOT LEAVE"

        self.current_text = self.base_text
        self.intensity = 0.0

        self.exit_attempts = 0
        self.exit_block_timer = 0.0
        self.show_block_msg = False
        self.allow_exit = False

        # ── CMD spawn tracking ───────────────────────────────────
        self.cmd_spawned = False
        self.cmd_timer = 0.0
        self.CMD_DURATION = 5.0

        self._vignette = self._build_vignette()
        self._scanlines = self._build_scanlines()
        self.cracks = self._gen_cracks(20)

    def _spawn_terminal_message(self):
        """Opens a maximized cmd window, then returns focus to pygame (Windows only)."""

        ascii_art = r"""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣶⣿⣿⣿⣿⣯⣿⣷⣦⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼⣿⣿⣿⠿⡿⣿⣿⣿⣿⣿⣿⣿⣿⢿⡿⣿⣿⠿⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠾⠋⠀⢀⣠⠀⠀⠙⠛⣿⣿⡿⠋⠁⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠆⠀⠀⢀⣿⣿⠄⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣶⣤⣤⣤⣦⣶⠀⢠⣿⣿⣧⣶⣤⣄⣤⣤⣴⣶⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⠆⠐⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿⣿⣿⡿⠀⠈⢿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣿⣿⣿⡿⠁⠀⠀⠈⠟⠛⣳⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⡿⠿⠁⠀⠀⠀⠀⣀⣴⣿⣿⣿⢿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠿⠿⠿⠟⠛⠉⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠐⠈⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⢠⠰⣭⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⡭⢀⢹⡞⡵⠁⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣿⣿⣿⡇⣌⣾⣿⡃⡐⢴⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣞⣿⣿⣿⡜⣶⣿⣿⡷⣙⡾⣷⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""

        message = "SIMON IS WATCHING YOU\n" + ascii_art

        import ctypes
        hwnd_pygame = pygame.display.get_wm_info()["window"]

        script_lines = [
            "import sys, time, ctypes, os",
            "os.system('chcp 65001 > nul')",
            "hwnd = ctypes.windll.kernel32.GetConsoleWindow()",
            "ctypes.windll.user32.ShowWindow(hwnd, 3)",
            "ctypes.windll.user32.SetForegroundWindow(hwnd)",
            "ctypes.windll.user32.BringWindowToTop(hwnd)",
            f"msg = {repr(message)}",
            "lines = msg.split('\\n')",
            "first_line = lines[0]",
            "for ch in first_line:",
            "    sys.stdout.write(ch)",
            "    sys.stdout.flush()",
            "    time.sleep(0.10)",
            "sys.stdout.write('\\n')",
            "sys.stdout.write('\\n'.join(lines[1:]))",
            "sys.stdout.flush()",
            "time.sleep(4)",
            "time.sleep(0.3)",
            f"hwnd_game = {hwnd_pygame}",
            "ctypes.windll.user32.ShowWindow(hwnd_game, 3)",
            "ctypes.windll.user32.SetForegroundWindow(hwnd_game)",
            "ctypes.windll.user32.BringWindowToTop(hwnd_game)",
            "ctypes.windll.user32.SetFocus(hwnd_game)",
        ]

        try:
            tmp = os.path.join(os.environ.get("TEMP", "."), "_simon_msg.py")
            with open(tmp, "w", encoding="utf-8") as f:  # ← utf-8 required for braille chars
                f.write("\n".join(script_lines))
            subprocess.Popen(
                f'start cmd /c "chcp 65001 & python \"{tmp}\""',
                shell=True
            )
        except Exception as e:
            print(f"[EndingState] Terminal spawn failed: {e}")

    # ── Distortion ───────────────────────────────────────────
    def distort_text(self, text, intensity):
        replacements = {
            "A": ["4", "@"],
            "E": ["3"],
            "O": ["0"],
            "I": ["1", "!"],
            "S": ["5", "$"]
        }

        result = ""
        for ch in text:
            if ch.upper() in replacements and random.random() < intensity:
                result += random.choice(replacements[ch.upper()])
            elif random.random() < intensity * 0.08:
                continue
            else:
                result += ch
        return result

    # ── Exit block trigger ───────────────────────────────────
    def _trigger_exit_block(self):
        self.exit_attempts += 1
        self.exit_block_timer = 1.2
        self.show_block_msg = True

        self.intensity = min(1.0, self.intensity + 0.2)

        if self.exit_attempts >= 3:
            self.allow_exit = True

    # ── Events ───────────────────────────────────────────────
    def handle_event(self, event):

        if event.type == pygame.QUIT:
            if not self.allow_exit:
                self._trigger_exit_block()
            else:
                pygame.quit()
                exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if not self.allow_exit:
                    self._trigger_exit_block()
                else:
                    pygame.mouse.set_visible(True)
                    self.game.switch_state("menu")
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)


    # ── Update ───────────────────────────────────────────────
    def update(self, dt):
        self.time += dt
        self.phase_time += dt

        if self.exit_block_timer > 0:
            self.exit_block_timer -= dt
        else:
            self.show_block_msg = False

        t = self.phase_time

        if t < 2:
            self.intensity = 0.0
            self.current_text = self.base_text

        elif t < 6:
            self.intensity = (t - 2) / 4
            self.current_text = self.distort_text(self.base_text, self.intensity)

        elif t < 9:
            self.intensity = 0.6 + (t - 6) / 3 * 0.4
            if int(t * 2) % 2 == 0:
                self.current_text = "SIMON SAYS"
            else:
                self.current_text = self.alt_text

        elif t < 12:
            self.intensity = 1.0
            self.current_text = self.distort_text(self.alt_text, 0.9)

            if not self.cmd_spawned:
                self._spawn_terminal_message()
                self.cmd_spawned = True

        if self.cmd_spawned:
            self.cmd_timer += dt
            if self.cmd_timer >= self.CMD_DURATION:
                pygame.event.set_grab(False)
                pygame.mouse.set_visible(True)  # or True if menu needs it
                pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)  # re-assert fullscreen
                self.game.switch_state("menu")


    # ── Draw ─────────────────────────────────────────────────
    def draw(self, surface):
        base_surface = pygame.Surface((SCREEN_W, SCREEN_H))
        base_surface.fill((5, 0, 0))

        self._draw_cracks(base_surface)
        base_surface.blit(self._vignette, (0, 0))
        base_surface.blit(self._scanlines, (0, 0))

        jitter_x = int(random.randint(-6, 6) * self.intensity)
        jitter_y = int(random.randint(-3, 3) * self.intensity)

        flk = _flicker(self.time, 2.2)
        color = (
            int(BLOOD_RED[0] * flk),
            int(BLOOD_RED[1] * flk),
            int(BLOOD_RED[2] * flk)
        )

        font = get_font(SZ_MAIN, bold=True)
        img = font.render(self.current_text, True, color)

        alpha = int(255 * (0.6 + random.random() * 0.4))
        img.set_alpha(alpha)

        base_surface.blit(
            img,
            (CX - img.get_width() // 2 + jitter_x,
             CY - img.get_height() // 2 + jitter_y)
        )

        if self.intensity > 0.4 and random.random() < 0.3:
            ghost = font.render(self.current_text, True, (120, 20, 20))
            ghost.set_alpha(80)
            base_surface.blit(
                ghost,
                (CX - ghost.get_width() // 2 - jitter_x,
                 CY - ghost.get_height() // 2)
            )

        # ── BLOCK MESSAGE ────────────────────────────────────
        if self.show_block_msg:
            font2 = get_font(SZ_SUB, bold=True)

            msg1 = "SIMON SAYS:"
            msg2 = "YOU CANNOT LEAVE"

            flk2 = _flicker(self.time * 3.0, 5.5)
            col2 = (
                int(BLOOD_RED[0] * flk2),
                int(BLOOD_RED[1] * flk2),
                int(BLOOD_RED[2] * flk2)
            )

            img1 = font2.render(msg1, True, col2)
            img2 = font2.render(msg2, True, col2)

            base_surface.blit(img1, (CX - img1.get_width() // 2, CY - 80))
            base_surface.blit(img2, (CX - img2.get_width() // 2, CY - 30))

        # ── FLASH FRAME ──────────────────────────────────────
        if self.show_block_msg and random.random() < 0.3:
            flash = pygame.Surface((SCREEN_W, SCREEN_H))
            flash.fill((120, 0, 0))
            flash.set_alpha(60)
            base_surface.blit(flash, (0, 0))

        # ── SCREEN SHAKE ─────────────────────────────────────
        if self.show_block_msg:
            shake_x = random.randint(-10, 10)
            shake_y = random.randint(-6, 6)
        else:
            shake_x = 0
            shake_y = 0

        surface.blit(base_surface, (shake_x, shake_y))

    # ── Visual builders ──────────────────────────────────────
    def _build_scanlines(self):
        sl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        step = max(2, int(3 * SCALE))
        for y in range(0, SCREEN_H, step):
            pygame.draw.line(sl, (0, 0, 0, 30), (0, y), (SCREEN_W, y))
        return sl

    def _build_vignette(self):
        vig = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        max_r = int(math.hypot(cx, cy)) + 10

        for i in range(32, 0, -1):
            frac = i / 32
            r = int(max_r * frac)
            alpha = int((1.0 - frac) ** 2.2 * 220)
            pygame.draw.circle(vig, (0, 0, 0, alpha), (cx, cy), r)

        return vig

    def _gen_cracks(self, n):
        rng = random.Random(99)
        cracks = []

        for _ in range(n):
            x = rng.randint(0, SCREEN_W)
            y = rng.randint(0, SCREEN_H)

            segs = []
            cx2, cy2 = x, y
            angle = rng.uniform(0, math.pi * 2)

            for _ in range(rng.randint(3, 7)):
                length = rng.uniform(20, 80)
                angle += rng.uniform(-0.6, 0.6)

                nx = cx2 + math.cos(angle) * length
                ny = cy2 + math.sin(angle) * length

                segs.append(((int(cx2), int(cy2)), (int(nx), int(ny))))
                cx2, cy2 = nx, ny

            cracks.append(segs)

        return cracks

    def _draw_cracks(self, surface):
        crack_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        for crack in self.cracks:
            col = (120, 10, 10, 90)
            for seg in crack:
                pygame.draw.line(crack_surf, col, seg[0], seg[1], 1)

        surface.blit(crack_surf, (0, 0))