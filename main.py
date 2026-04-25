import pygame
import sys
import os


FPS   = 60
TITLE = "Patrick Says HAHAHAHA"


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        info = pygame.display.Info()
        SCREEN_W = info.current_w
        SCREEN_H = info.current_h
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
        os.environ["SDL_RENDER_SCALE_QUALITY"]="1"
        pygame.display.set_caption(TITLE)
        self.clock   = pygame.time.Clock()
        self.running = True
        self.score   = 0
        self.states  = {}
        self.current_state = None
        self._init_states()
        self.switch_state("splash")

    def _init_states(self):
        # Imported here (after display init) so utils.py reads the real resolution
        from states.menu import MenuState
        from states.disclaimer import DisclaimerState
        from states.mechanics import MechanicsState
        from states.game import GameState
        from states.splash import SplashState
        from states.level2 import Level2State

        self.states = {
            "splash":     SplashState(self),
            "menu":       MenuState(self),
            "disclaimer": DisclaimerState(self),
            "mechanics":  MechanicsState(self),
            "game":       GameState(self),
            "level2":     Level2State(self),
        }

    def switch_state(self, name, **kwargs):
        self.current_state = self.states[name]
        self.current_state.on_enter(**kwargs)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                self.current_state.handle_event(event)
            self.current_state.update(dt)
            self.current_state.draw(self.screen)
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()