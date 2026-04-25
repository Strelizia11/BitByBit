import pygame
from states.base import BaseState
from utils import SCREEN_W, SCREEN_H, CX, CY, NEAR_BLACK

class SplashState(BaseState):
    def on_enter(self, **kwargs):
        self.time = 0.0
        self.duration = 4.0  # Total display time (seconds)
        self.alpha = 0       
        
        # Option A: Load an actual image
        # self.image = pygame.image.load("assets/logo.png").convert_alpha()
        
        # Option B: Placeholder (A simple white box for now so you can test)
        original_image = pygame.image.load("./assets/light-on.png").convert_alpha()
    
    # 2. Define your custom size (Width, Height)
        custom_size = (400, 400) 
        
        # 3. Scale it
        # Use 'smoothscale' for better quality, or 'scale' for speed/pixel art
        self.image = pygame.transform.smoothscale(original_image, custom_size)
        
        # 4. Update the rect so it's still centered
        self.rect = self.image.get_rect(center=(CX, CY))

        self.rect = self.image.get_rect(center=(CX, CY))

    def update(self, dt):
        self.time += dt
        
        # Fade Logic: 0.0 to 1.0s (In), 1.0 to 3.0s (Stay), 3.0 to 4.0s (Out)
        if self.time < 1.0:
            self.alpha = int((self.time / 1.0) * 255)
        elif self.time < 3.0:
            self.alpha = 255
        elif self.time < 4.0:
            self.alpha = int(255 - ((self.time - 3.0) / 1.0) * 255)
        else:
            self.game.switch_state("menu")

    def draw(self, surface):
        surface.fill(NEAR_BLACK)
        
        # Create a temp surface to apply the fade alpha
        self.image.set_alpha(self.alpha)
        surface.blit(self.image, self.rect)