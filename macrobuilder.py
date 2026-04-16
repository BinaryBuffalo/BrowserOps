import random
import time

# ===========================
# Configuration Variables
# ===========================

# Number of macro actions to generate
NUM_ACTIONS = 15  # Adjust as needed (e.g., 80-150)

# Sleep time range between each complete movement (in seconds)
SLEEP_BETWEEN_MIN = 0.5    # Minimum sleep time
SLEEP_BETWEEN_MAX = 2      # Maximum sleep time

# Probability settings
SHIFT_PROBABILITY = 0.50    # 50% chance to hold 'SHIFT' when applicable

# Hold time range for holding down keys (in seconds)
HOLD_TIME_MIN = 2.3         # Minimum hold time
HOLD_TIME_MAX = 5.5         # Maximum hold time

# Delay range after each key event to mimic human behavior (in seconds)
KEY_EVENT_DELAY_MIN = 0.002  # Minimum delay
KEY_EVENT_DELAY_MAX = 0.09    # Maximum delay

# Mapping of special keys to their corresponding Keys constants
SPECIAL_KEYS = {
    'SHIFT': 'Keys.SHIFT'
}

# ===========================
# List of Valid Actions
# ===========================

VALID_ACTIONS = [
    ['w'],
    ['a'],
    ['s'],
    ['d'],
    ['w', 'a'],
    ['a', 'w'],
    ['w', 'd'],
    ['d', 'w'],
    ['s', 'a'],
    ['a', 's'],
    ['d', 's'],
    ['s', 'd'],
    ['SHIFT', 'w'],
    ['SHIFT', 'w', 'a'],
    ['SHIFT', 'a', 'w'],
    ['SHIFT', 'w', 'd'],
    ['SHIFT', 'd', 'w']
]

# ===========================
# Macro Generation Function
# ===========================

def generate_macro(num_actions=NUM_ACTIONS, output_file='macro.txt'):
    """
    Generates a macro script and writes it to 'macro.txt'.

    Parameters:
    - num_actions (int): Number of macro actions to generate.
    - output_file (str): Name of the output file to write the macro.
    """
    with open(output_file, 'w') as f:
        # Iterate over the number of actions to generate
        for _ in range(num_actions):
            action_lines = []

            # Select a valid action randomly
            action = random.choice(VALID_ACTIONS)

            # Separate special keys from regular keys
            special_keys = [key for key in action if key.upper() in SPECIAL_KEYS]
            regular_keys = [key for key in action if key.upper() not in SPECIAL_KEYS]

            # ================================
            # Key Down Actions
            # ================================
            # Handle special keys first
            for key in special_keys:
                key_constant = SPECIAL_KEYS[key.upper()]
                action_lines.append(f"actions.key_down({key_constant}).perform()\n")
                # Small random delay after key_down
                delay = round(random.uniform(KEY_EVENT_DELAY_MIN, KEY_EVENT_DELAY_MAX), 3)
                action_lines.append(f"time.sleep({delay})  # Delay after key_down({key_constant})\n")

            # Handle regular keys
            for key in regular_keys:
                action_lines.append(f"actions.key_down('{key}').perform()\n")
                # Small random delay after key_down
                delay = round(random.uniform(KEY_EVENT_DELAY_MIN, KEY_EVENT_DELAY_MAX), 3)
                action_lines.append(f"time.sleep({delay})  # Delay after key_down('{key}')\n")

            # ================================
            # Hold the keys for a random duration
            # ================================
            hold_time = round(random.uniform(HOLD_TIME_MIN, HOLD_TIME_MAX), 3)
            action_lines.append(f"time.sleep({hold_time})  # Hold keys for {hold_time} seconds\n")

            # ================================
            # Key Up Actions
            # ================================
            # Handle regular keys first (reverse order)
            for key in reversed(regular_keys):
                action_lines.append(f"actions.key_up('{key}').perform()\n")
                # Small random delay after key_up
                delay = round(random.uniform(KEY_EVENT_DELAY_MIN, KEY_EVENT_DELAY_MAX), 3)
                action_lines.append(f"time.sleep({delay})  # Delay after key_up('{key}')\n")

            # Handle special keys last (reverse order)
            for key in reversed(special_keys):
                key_constant = SPECIAL_KEYS[key.upper()]
                action_lines.append(f"actions.key_up({key_constant}).perform()\n")
                # Small random delay after key_up
                delay = round(random.uniform(KEY_EVENT_DELAY_MIN, KEY_EVENT_DELAY_MAX), 3)
                action_lines.append(f"time.sleep({delay})  # Delay after key_up({key_constant})\n")

            # ================================
            # Sleep between actions
            # ================================
            sleep_time = round(random.uniform(SLEEP_BETWEEN_MIN, SLEEP_BETWEEN_MAX), 3)
            action_lines.append(f"time.sleep({sleep_time})  # Sleep before next action\n\n")

            # Write the action lines to the file
            f.writelines(action_lines)
        
        # After all actions, hold 'G' for 7 seconds
        f.write("# Hold 'G' for 7 seconds at the end of the macro\n")
        f.write("actions.key_down('g').perform()\n")
        f.write("time.sleep(0.01)  # Slight delay after key_down('g')\n")
        f.write("actions.perform()\n")
        f.write("time.sleep(7)  # Hold 'G' for 7 seconds\n")
        f.write("actions.key_up('g').perform()\n")
        f.write("time.sleep(0.01)  # Slight delay after key_up('g')\n")
        f.write("actions.perform()\n\n")

    print(f"'{output_file}' has been generated with {num_actions} actions.")

# ===========================
# Main Execution
# ===========================

if __name__ == "__main__":
    generate_macro()
