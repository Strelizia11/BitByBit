import random
from typing import Optional


class InstructionSystem:
    def __init__(self, total_rounds: int = 8):
        self.total_rounds = total_rounds
        self.current_round = 0

    def reset(self):
        self.current_round = 0

    def next_instruction(self, is_light_on: bool, is_window_open: Optional[bool] = None, is_door_open: Optional[bool] = None):
        """Returns (display_text, is_anomaly, base_rule).

        Window and door instructions are only added when the caller explicitly
        passes those states (level 2)."""

        if self.current_round >= self.total_rounds:
            return None

        self.current_round += 1

        # ── Round 8: special cinematic instruction ────────────────────────────
        # Goal: ensure light is ON when round ends (so the cutscene makes sense)
        # Light ON  → "DO NOT CLICK" (keep it on)
        # Light OFF → "CLICK THE SWITCH" (turn it on with one click)
        if self.current_round == self.total_rounds:
            if is_light_on:
                text = "SIMON SAYS DO NOT CLICK THE SWITCH!!!"
                base_rule = "SIMON SAYS DO NOT CLICK THE SWITCH"
            else:
                text = "CL1CK THE SW1TCH"
                base_rule = "CL1CK THE SW1TCH"
            # Round 8 is never an anomaly – always meant to be followed literally
            return text, False, base_rule

        # ── Rounds 1-7: normal random pool ───────────────────────────────────
        valid_pairs = [
            ("SIMON SAYS CLICK THE SWITCH", "CL1CK THE SW1TCH"),
            ("SIMON SAYS CLICK THE SWITCH FIVE TIMES", "HE SAID CLICK THE SWITCH FIVE TIM3S"),
            ("SIMON SAYS DO NOT CLICK THE SWITCH", "S1MON SAYS DONT CLICK THE SWITCH"),
            ("SIMON SAYS CLICK THE SWITCH 2 TIMES", "FL1ICK THE SWITCH 2 TIMES"),
            ("SIMON SAYS CLICK THE SWITCH 3 TIMES", "IT SAYS CLICK THE SWITCH 3 TIMES"),
        ]

        if is_light_on:
            valid_pairs.append(("SIMON SAYS TURN OFF THE LIGHT",
                                "SIMON WANTS YOU TO TURN OFF THE L1GHT"))
        else:
            valid_pairs.append(("SIMON SAYS TURN ON THE LIGHT",
                                "TURN ON THE LIGHT"))

        # ── Build weighted pool for level 2 (window/door appear 3x more) ──
        # Each entry is (normal_text, anomaly_text, weight).
        # Switch rules get weight 1; window/door rules get weight 3 so they
        # dominate level 2 rounds while still occasionally giving switch tasks.
        weighted_pairs = [(n, a, 1) for n, a in valid_pairs]

        if is_window_open is not None:
            if is_window_open:
                weighted_pairs.append(("SIMON SAYS CLOSE THE WINDOW",
                                       "CL0SE THE WINDOW", 3))
            else:
                weighted_pairs.append(("SIMON SAYS OPEN THE WINDOW",
                                       "0PEN THE WINDOW", 3))

        if is_door_open is not None:
            if is_door_open:
                weighted_pairs.append(("SIMON SAYS CLOSE THE DOOR",
                                       "CL0SE THE DOOR", 3))
            else:
                weighted_pairs.append(("SIMON SAYS OPEN THE DOOR",
                                       "0PEN THE DOOR", 3))

        # ── Extra DOOR anomaly instructions ─────────────────────────
        if is_door_open is not None:
            if not is_door_open:
                weighted_pairs.extend([
                    ("SIMON SAYS CHECK THE OUTSIDE BY THE DOOR",
                     "I SAID OPEN THE DOOR!!!", 2),
                    ("SIMON SAYS CHECK THE OUTSIDE BY THE DOOR",
                     "SIMOUN SAYS OPEN THE DOOR", 2),
                ])
            else:
                weighted_pairs.extend([
                    ("SIMON SAYS DO NOT LET WIND COME IN BY THE DOOR",
                     "SIMN SA1D CLOSE THE DOOR", 2),
                    ("SIMON SAYS DO NOT LET WIND COME IN BY THE DOOR",
                     "I SAID CLOSE IT DOOR", 2),
                ])
        # ── Extra WINDOW anomaly instructions ───────────────────────
        if is_window_open is not None:
            if not is_window_open:
                weighted_pairs.extend([
                    ("SIMON SAYS CHECK THE OUTSIDE BY THE WINDOW",
                     "I SAID OPEN THE WINDOW!!!", 2),
                    ("SIMON SAYS CHECK THE OUTSIDE BY THE WINDOW",
                     "SIMOUN SAYS OPEN THE WINDOW", 2),
                ])
            else:
                weighted_pairs.extend([
                    ("SIMON SAYS DO NOT LET WIND COME IN BY THE WINDOW",
                     "SIMN SA1D CLOSE THE WINDOW", 2),
                    ("SIMON SAYS DO NOT LET WIND COME IN BY THE WINDOW",
                     "I SAID CLOSE THE WINDOW", 2),
                ])

        population = [(n, a) for n, a, w in weighted_pairs for _ in range(w)]
        normal_text, anomaly_text = random.choice(population)
        is_anomaly = random.random() < 0.30
        display_text = anomaly_text if is_anomaly else normal_text

        return display_text, is_anomaly, normal_text

    @staticmethod
    def evaluate_action(base_rule: str, is_anomaly: bool,
                        light_was_on_at_start: bool, total_clicks: int,
                        window_was_open_at_start: bool = False,
                        window_clicks: int = 0,
                        door_was_open_at_start: bool = False,
                        door_clicks: int = 0) -> bool:
        """Evaluates if the player survived based on clicks, light state, and anomalies."""

        should_follow = (light_was_on_at_start and not is_anomaly) or \
                        (not light_was_on_at_start and is_anomaly)

        # ── "DO NOT CLICK THE SWITCH" (also used for round 8 light-on case) ──
        if base_rule == "SIMON SAYS DO NOT CLICK THE SWITCH":
            if not is_anomaly:
                if light_was_on_at_start:
                    return total_clicks == 0  # follow → don't click
                else:
                    return total_clicks > 0  # invert → click
            else:
                if light_was_on_at_start:
                    return total_clicks > 0
                else:
                    return total_clicks == 0

        elif base_rule == "SIMON SAYS CLICK THE SWITCH":
            if should_follow:
                return total_clicks > 0
            else:
                return total_clicks == 0
        elif base_rule == "CL1CK THE SW1TCH":
            if not light_was_on_at_start:
                return total_clicks == 1
            else:
                return total_clicks == 0

        elif base_rule == "SIMON SAYS TURN OFF THE LIGHT":
            if should_follow:
                return total_clicks % 2 != 0
            else:
                return total_clicks % 2 == 0

        elif base_rule == "SIMON SAYS TURN ON THE LIGHT":
            if should_follow:
                return total_clicks % 2 != 0
            else:
                return total_clicks % 2 == 0

        elif base_rule == "SIMON SAYS CLICK THE SWITCH FIVE TIMES":
            if should_follow:
                return total_clicks == 5
            else:
                return total_clicks != 5

        elif base_rule == "SIMON SAYS CLICK THE SWITCH 2 TIMES":
            if should_follow:
                return total_clicks == 2
            else:
                return total_clicks != 2

        elif base_rule == "SIMON SAYS CLICK THE SWITCH 3 TIMES":
            if should_follow:
                return total_clicks == 3
            else:
                return total_clicks != 3

        # ── Window tasks ──
        elif base_rule == "SIMON SAYS OPEN THE WINDOW":
            if should_follow:
                # Must click window when it's closed (window_clicks should be odd to open)
                return window_clicks % 2 != 0
            else:
                # Anomaly: don't open the window
                return window_clicks % 2 == 0

        elif base_rule == "SIMON SAYS CLOSE THE WINDOW":
            if should_follow:
                # Must click window when it's open (window_clicks should be odd to close)
                return window_clicks % 2 != 0
            else:
                # Anomaly: don't close the window
                return window_clicks % 2 == 0
        elif base_rule == "SIMON SAYS CHECK THE OUTSIDE BY THE WINDOW":
            if should_follow:
                return window_clicks % 2 != 0
            else:
                return window_clicks % 2 == 0

        elif base_rule == "SIMON SAYS DO NOT LET WIND COME IN BY THE WINDOW":
            if should_follow:
                return window_clicks % 2 != 0
            else:
                return window_clicks % 2 == 0

        # ── Door tasks ──
        elif base_rule == "SIMON SAYS OPEN THE DOOR":
            if should_follow:
                return door_clicks % 2 != 0
            else:
                return door_clicks % 2 == 0

        elif base_rule == "SIMON SAYS CLOSE THE DOOR":
            if should_follow:
                return door_clicks % 2 != 0
            else:
                return door_clicks % 2 == 0
        elif base_rule == "SIMON SAYS CHECK THE OUTSIDE BY THE DOOR":
            if should_follow:
                return door_clicks % 2 != 0  # open door
            else:
                return door_clicks % 2 == 0

        elif base_rule == "SIMON SAYS DO NOT LET WIND COME IN BY THE DOOR":
            if should_follow:
                return door_clicks % 2 != 0  # close door
            else:
                return door_clicks % 2 == 0
        elif base_rule == "FORCE_CLOSE_DOOR":
            return door_clicks % 2 != 0  # must close

        elif base_rule == "FORCE_CLOSE_WINDOW":
            return window_clicks % 2 != 0
        elif base_rule == "FORCE_LIGHT_ON":
            return total_clicks % 2 != 0  # must turn light back on

        return False