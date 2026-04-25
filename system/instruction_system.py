import random


class InstructionSystem:
    def __init__(self, total_rounds: int = 8):
        self.total_rounds = total_rounds
        self.current_round = 0

    def reset(self):
        self.current_round = 0

    def next_instruction(self, is_light_on: bool):
        """Dynamically picks the next instruction based on the current light state."""
        if self.current_round >= self.total_rounds:
            return None

        self.current_round += 1

        valid_normals = [
            "CLICK THE SWITCH",
            "CLICK THE SWITCH FIVE TIMES",
            "DO NOT CLICK THE SWITCH"
        ]

        # Add context-sensitive instructions
        if is_light_on:
            valid_normals.append("TURN OFF THE LIGHT")
        else:
            valid_normals.append("TURN ON THE LIGHT")

        # Pick a random normal instruction (we'll integrate anomalies later)
        text = random.choice(valid_normals)
        is_anomaly = False

        return text, is_anomaly

    @staticmethod
    def evaluate_normal_action(text: str, light_was_on_at_start: bool, total_clicks: int) -> bool:
        """Evaluates the player's clicks against your new rules."""

        if text == "CLICK THE SWITCH":
            if light_was_on_at_start:
                return total_clicks > 0  # Proceed if they clicked at least once
            else:
                return total_clicks == 0  # Proceed if they didn't click

        elif text == "TURN ON THE LIGHT":
            # If light started OFF, an odd number of clicks means it ends up ON
            return total_clicks % 2 != 0

        elif text == "TURN OFF THE LIGHT":
            # If light started ON, an odd number of clicks means it ends up OFF
            return total_clicks % 2 != 0

        elif text == "CLICK THE SWITCH FIVE TIMES":
            if light_was_on_at_start:
                return total_clicks == 5
            else:
                return total_clicks != 5

        elif text == "DO NOT CLICK THE SWITCH":
            if light_was_on_at_start:
                return total_clicks == 0
            else:
                return total_clicks > 0

        return False