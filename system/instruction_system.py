import random


class InstructionSystem:
    def __init__(self, total_rounds: int = 8):
        self.total_rounds = total_rounds
        self.current_round = 0

    def reset(self):
        self.current_round = 0

    def next_instruction(self, is_light_on: bool):
        """Returns (display_text, is_anomaly, base_rule)"""
        if self.current_round >= self.total_rounds:
            return None

        self.current_round += 1

        # Pairs of (Normal Text, Anomaly Text)
        valid_pairs = [
            ("SIMON SAYS CLICK THE SWITCH", "SIM0N SAYS CL1CK THE SWITCH"),
            ("SIMON SAYS CLICK THE SWITCH FIVE TIMES", "HE SAID CLICK THE SWITCH FIVE TIM3S"),
            ("SIMON SAYS DO NOT CLICK THE SWITCH!!!", "S1MON SAYS DONT CLICK THE SWITCH")
        ]

        if is_light_on:
            valid_pairs.append(("SIMON SAYS TURN OFF THE LIGHT", "SIMON WANTS YOU TO TURN OFF THE L1GHT"))
        else:
            valid_pairs.append(("SIMON SAYS TURN ON THE LIGHT", "SIMON S4YS TURN ON THE LIHGT"))

        # Pick a random instruction pair
        normal_text, anomaly_text = random.choice(valid_pairs)

        # 30% chance to be an anomaly
        is_anomaly = random.random() < 0.30
        display_text = anomaly_text if is_anomaly else normal_text

        # We return the base "normal_text" so the evaluator knows what rule to check
        return display_text, is_anomaly, normal_text

    @staticmethod
    def evaluate_action(base_rule: str, is_anomaly: bool, light_was_on_at_start: bool, total_clicks: int) -> bool:
        """Evaluates if the player survived based on clicks, light state, and anomalies."""

        # CORE LOGIC: Should the player Follow or Invert the instruction?
        should_follow = (light_was_on_at_start and not is_anomaly) or (not light_was_on_at_start and is_anomaly)

        # ── SPECIAL EXCEPTION: The "WITCH" Wordplay ──
        if base_rule == "SIMON SAYS DO NOT CLICK THE SWITCH!!!":
            if not is_anomaly:
                # Normal: "DO NOT CLICK THE SWITCH"
                if light_was_on_at_start:
                    return total_clicks == 0  # Light ON: Follow it (don't click)
                else:
                    return total_clicks > 0  # Light OFF: Opposite (click)
            else:
                # Anomaly: "DONT CLICK THE WITCH"
                # Because there is no witch, the player clicks the switch in both light states!
                if light_was_on_at_start:
                    return total_clicks > 0
                else:
                    return total_clicks == 0

                    # ── STANDARD RULES ──
        elif base_rule == "SIMON SAYS CLICK THE SWITCH":
            if should_follow:
                return total_clicks > 0  # Follow: click at least once
            else:
                return total_clicks == 0  # Invert: don't click at all

        elif base_rule == "SIMON SAYS TURN OFF THE LIGHT":
            if should_follow:
                return total_clicks % 2 != 0  # Follow: odd clicks turns it ON
            else:
                return total_clicks % 2 == 0  # Invert: even clicks keeps it OFF

        elif base_rule == "SIMON SAYS TURN ON THE LIGHT":
            if should_follow:
                return total_clicks % 2 != 0  # Follow: odd clicks turns it OFF
            else:
                return total_clicks % 2 == 0  # Invert: even clicks keeps it ON

        elif base_rule == "SIMON SAYS CLICK THE SWITCH FIVE TIMES":
            if should_follow:
                return total_clicks == 5
            else:
                return total_clicks != 5

        return False