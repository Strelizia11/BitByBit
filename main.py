import pygame
import sys
import os


FPS        = 60
TITLE      = "Flicker"
WINDOW_W   = 800
WINDOW_H   = 600


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        info = pygame.display.Info()
        self.native_w = info.current_w
        self.native_h = info.current_h

        os.environ["SDL_RENDER_SCALE_QUALITY"] = "1"

        # Start fullscreen
        self.fullscreen = True
        self.screen = pygame.display.set_mode(
            (self.native_w, self.native_h), pygame.FULLSCREEN
        )
        pygame.display.set_caption(TITLE)

        # All game states draw into this fixed virtual surface (native resolution).
        # In fullscreen it is blitted 1:1; in windowed mode it is scaled to 800x600.
        self.virtual_screen = pygame.Surface((self.native_w, self.native_h))

        self.clock         = pygame.time.Clock()
        self.running       = True
        self.score         = 0
        self.states        = {}
        self.current_state = None
        self._init_states()
        self.switch_state("splash")

    # ── Toggle called by MenuState on ESC ─────────────────────────────────────
    def toggle_fullscreen(self):
        if self.fullscreen:
            # Switch to an 800x600 resizable window
            self.screen = pygame.display.set_mode(
                (WINDOW_W, WINDOW_H), pygame.RESIZABLE
            )
            self.fullscreen = False
        else:
            # Switch back to fullscreen at native resolution
            self.screen = pygame.display.set_mode(
                (self.native_w, self.native_h), pygame.FULLSCREEN
            )
            self.fullscreen = True

    # ── State management ──────────────────────────────────────────────────────
    def _init_states(self):
        # Imported here (after display init) so utils.py reads the real resolution
        from states.menu import MenuState
        from states.disclaimer import DisclaimerState
        from states.mechanics import MechanicsState
        from states.game import GameState
        from states.splash import SplashState
        from states.level2 import Level2State
        from states.ending import EndingState

        self.states = {
            "splash":     SplashState(self),
            "menu":       MenuState(self),
            "disclaimer": DisclaimerState(self),
            "mechanics":  MechanicsState(self),
            "game":       GameState(self),
            "level2":     Level2State(self),
            "ending":     EndingState(self),
        }

    def switch_state(self, name, **kwargs):
        self.current_state = self.states[name]
        self.current_state.on_enter(**kwargs)

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            win_w, win_h = self.screen.get_size()

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

                # ── Pause/resume music on window focus ──
                if event.type == pygame.WINDOWFOCUSLOST:
                    pygame.mixer.music.pause()
                if event.type == pygame.WINDOWFOCUSGAINED:
                    pygame.mixer.music.unpause()

                # ── Remap mouse coords to virtual surface space ──────────────
                # When windowed, mouse events come in window-pixel coords
                # (800x600). We scale them up so all states see native coords.
                if not self.fullscreen and event.type in (
                    pygame.MOUSEMOTION,
                    pygame.MOUSEBUTTONDOWN,
                    pygame.MOUSEBUTTONUP,
                ):
                    scale_x = self.native_w / win_w
                    scale_y = self.native_h / win_h
                    mx = int(event.pos[0] * scale_x)
                    my = int(event.pos[1] * scale_y)
                    # Rebuild event with remapped position
                    if event.type == pygame.MOUSEMOTION:
                        event = pygame.event.Event(
                            pygame.MOUSEMOTION,
                            pos=(mx, my),
                            rel=event.rel,
                            buttons=event.buttons,
                        )
                    else:
                        event = pygame.event.Event(
                            event.type,
                            pos=(mx, my),
                            button=event.button,
                        )

                self.current_state.handle_event(event)

            # ── Draw into virtual surface ─────────────────────────────────────
            self.current_state.update(dt)
            self.current_state.draw(self.virtual_screen)

            # ── Blit virtual surface → real window ───────────────────────────
            if self.fullscreen:
                # 1-to-1 blit in fullscreen
                self.screen.blit(self.virtual_screen, (0, 0))
            else:
                # Scale down to 800x600 window, preserving aspect ratio with
                # black letterboxes if needed
                virt_aspect = self.native_w / self.native_h
                win_aspect  = win_w / win_h

                if virt_aspect >= win_aspect:
                    scaled_w = win_w
                    scaled_h = int(win_w / virt_aspect)
                else:
                    scaled_h = win_h
                    scaled_w = int(win_h * virt_aspect)

                offset_x = (win_w - scaled_w) // 2
                offset_y = (win_h - scaled_h) // 2

                scaled = pygame.transform.smoothscale(
                    self.virtual_screen, (scaled_w, scaled_h)
                )
                self.screen.fill((0, 0, 0))          # letterbox fill
                self.screen.blit(scaled, (offset_x, offset_y))

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()