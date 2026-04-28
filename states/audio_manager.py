import pygame

from utils import resource_path


class AudioManager:
    def __init__(self):
        pygame.mixer.init()

        # Store sound effects
        self.sounds = {}

        # Store music tracks
        self.music_tracks = {}

        # Dedicated channels
        self.channels = {
            "switch": pygame.mixer.Channel(0),
            "window": pygame.mixer.Channel(1),
            "door": pygame.mixer.Channel(2),
            "button": pygame.mixer.Channel(3),
            "whisper": pygame.mixer.Channel(4),
            "jumpscare": pygame.mixer.Channel(5),
            "ending": pygame.mixer.Channel(6)

        }

        pygame.mixer.set_num_channels(8)

        # (ch, end_time_ms, fadeout_seconds)
        self.pending_stops = []

        self._load_all_sfx()
        self._load_all_music()

    # ─────────────────────────────
    # AUTO LOAD SFX
    # ─────────────────────────────
    def _load_all_sfx(self):
        self.load_sound("switch_on", resource_path("assets/switch_on.wav"))
        self.load_sound("switch_off", resource_path("assets/switch_off.wav"))
        self.load_sound("button_click", resource_path("assets/button_click.wav"))
        self.load_sound("window_open", resource_path("assets/window_open.wav"))
        self.load_sound("window_close", resource_path("assets/window_close.wav"))
        self.load_sound("door_open", resource_path("assets/door_open.wav"))
        self.load_sound("door_close", resource_path("assets/door_close.wav"))
        self.load_sound("whisper1", resource_path("assets/whisper1.wav"))
        self.load_sound("whisper2", resource_path("assets/whisper2.wav"))
        self.load_sound("whisper3", resource_path("assets/whisper3.wav"))
        self.load_sound("jumpscare1", resource_path("assets/jumpscare1.wav"))
        self.load_sound("jumpscare2", resource_path("assets/jumpscare2.wav"))
        self.load_sound("breathing", resource_path("assets/breathing.wav"))
        self.load_sound("ending", resource_path("assets/ending.wav"))
        self.load_sound("intense", resource_path("assets/intense.wav"))
        self.load_sound("jumpscare_sound", resource_path("assets/jumpscare_sound1.wav"))


    # ─────────────────────────────
    # AUTO LOAD MUSIC
    # ─────────────────────────────
    def _load_all_music(self):
        self.load_music("ambience", resource_path("assets/ambience.wav"))
        self.load_music("menu", resource_path("assets/flicker.wav"))

    # ─────────────────────────────
    # LOAD SFX
    # ─────────────────────────────
    def load_sound(self, name, path):
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"[AudioManager] Failed to load {name}: {e}")

    # ─────────────────────────────
    # LOAD MUSIC
    # ─────────────────────────────
    def load_music(self, name, path):
        self.music_tracks[name] = path

    # ─────────────────────────────
    # PLAY SFX
    # ─────────────────────────────
    def play(self, name, channel=None, loops=0, duration=None, fadeout=0):
        if name not in self.sounds:
            print(f"[AudioManager] Sound '{name}' not found")
            return

        sound = self.sounds[name]

        # ── Channel playback ──
        if channel and channel in self.channels:
            ch = self.channels[channel]
            ch.play(sound, loops=loops)

            # schedule stop
            if duration is not None:
                end_time = pygame.time.get_ticks() + int(duration * 1000)
                self.pending_stops.append((ch, end_time, fadeout))

        # ── Direct playback ──
        else:
            sound.play(loops=loops)

    # ─────────────────────────────
    # PLAY MUSIC
    # ─────────────────────────────
    def play_music(self, name, loop=False):
        if name not in self.music_tracks:
            print(f"[AudioManager] Music '{name}' not found")
            return

        try:
            pygame.mixer.music.load(self.music_tracks[name])
            pygame.mixer.music.play(-1 if loop else 0)
        except pygame.error as e:
            print(f"[AudioManager] Music error: {e}")

    # ─────────────────────────────
    # UPDATE (IMPORTANT)
    # ─────────────────────────────
    def update(self):
        now = pygame.time.get_ticks()

        for item in self.pending_stops[:]:
            ch, end_time, fadeout = item

            if now >= end_time:
                if fadeout > 0:
                    ch.fadeout(int(fadeout * 1000))
                else:
                    ch.stop()

                self.pending_stops.remove(item)

    # ─────────────────────────────
    # STOP SFX
    # ─────────────────────────────
    def stop(self, name=None):
        if name and name in self.sounds:
            self.sounds[name].stop()
        else:
            pygame.mixer.stop()

    # ─────────────────────────────
    # STOP MUSIC
    # ─────────────────────────────
    def stop_music(self):
        pygame.mixer.music.stop()

    # ─────────────────────────────
    # VOLUME CONTROL
    # ─────────────────────────────
    def set_volume(self, name, volume):
        if name in self.sounds:
            self.sounds[name].set_volume(volume)

    def set_music_volume(self, volume):
        pygame.mixer.music.set_volume(volume)