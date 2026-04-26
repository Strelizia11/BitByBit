import pygame


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
            "jumpscare": pygame.mixer.Channel(5)

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
        self.load_sound("switch_on", "assets/switch_on.wav")
        self.load_sound("switch_off", "assets/switch_off.wav")
        self.load_sound("button_click", "assets/button_click.wav")
        self.load_sound("window_open", "assets/window_open.wav")
        self.load_sound("window_close", "assets/window_close.wav")
        self.load_sound("door_open", "assets/door_open.wav")
        self.load_sound("door_close", "assets/door_close.wav")
        self.load_sound("whisper1", "assets/whisper1.wav")
        self.load_sound("whisper2", "assets/whisper2.wav")
        self.load_sound("whisper3", "assets/whisper3.wav")
        self.load_sound("jumpscare1", "assets/jumpscare1.wav")
        self.load_sound("jumpscare2", "assets/jumpscare2.wav")
        self.load_sound("breathing", "assets/breathing.wav")
        self.load_sound("ending", "assets/ending.wav")

    # ─────────────────────────────
    # AUTO LOAD MUSIC
    # ─────────────────────────────
    def _load_all_music(self):
        self.load_music("ambience", "assets/ambience.wav")
        self.load_music("menu","assets/flicker.wav")

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