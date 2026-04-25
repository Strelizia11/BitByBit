import pygame

class AudioManager:
    def __init__(self):
        pygame.mixer.init()

        # Store sound effects
        self.sounds = {}

        # Store music tracks
        self.music_tracks = {}

        # Create dedicated channels
        self.channels = {
            "switch": pygame.mixer.Channel(0),
            "window": pygame.mixer.Channel(1),
            "door": pygame.mixer.Channel(2),
            "button": pygame.mixer.Channel(3),
            "ui": pygame.mixer.Channel(4)
        }

        pygame.mixer.set_num_channels(8)

        # Auto-load audio
        self._load_all_sfx()
        self._load_all_music()

    # ---------------------------
    # AUTO LOAD ALL SFX
    # ---------------------------
    def _load_all_sfx(self):
        self.load_sound("switch_on", "assets/switch_on.wav")
        self.load_sound("switch_off", "assets/switch_off.wav")
        self.load_sound("button_click", "assets/button_click.wav")

    # ---------------------------
    # AUTO LOAD MUSIC
    # ---------------------------
    def _load_all_music(self):
        self.load_music("ambience", "assets/ambience.wav")


    # ---------------------------
    # LOAD SFX
    # ---------------------------
    def load_sound(self, name, path):
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"[AudioManager] Failed to load {name}: {e}")

    # ---------------------------
    # LOAD MUSIC
    # ---------------------------
    def load_music(self, name, path):
        self.music_tracks[name] = path

    # ---------------------------
    # PLAY SFX
    # ---------------------------
    def play(self, name, channel=None, loops=0):
        if name not in self.sounds:
            print(f"[AudioManager] Sound '{name}' not found")
            return

        sound = self.sounds[name]

        if channel and channel in self.channels:
            self.channels[channel].play(sound, loops=loops)
        else:
            sound.play(loops=loops)

    # ---------------------------
    # PLAY MUSIC
    # ---------------------------
    def play_music(self, name, loop=False):
        if name not in self.music_tracks:
            print(f"[AudioManager] Music '{name}' not found")
            return

        try:
            pygame.mixer.music.load(self.music_tracks[name])
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops=loops)
        except pygame.error as e:
            print(f"[AudioManager] Music error: {e}")

    # ---------------------------
    # STOP SFX
    # ---------------------------
    def stop(self, name=None):
        if name and name in self.sounds:
            self.sounds[name].stop()
        else:
            pygame.mixer.stop()

    # ---------------------------
    # STOP MUSIC
    # ---------------------------
    def stop_music(self):
        pygame.mixer.music.stop()

    # ---------------------------
    # VOLUME CONTROL
    # ---------------------------
    def set_volume(self, name, volume):
        if name in self.sounds:
            self.sounds[name].set_volume(volume)

    def set_music_volume(self, volume):
        pygame.mixer.music.set_volume(volume)