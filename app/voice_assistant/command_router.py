import logging
import re
import json
import os
import webbrowser
import subprocess
from .actions.system_actions import open_generic
from .actions.complex_actions import handle_send_email, handle_set_reminder, handle_search_query, handle_play_query
from rapidfuzz import fuzz

COMMAND_HANDLERS = {
    "open": open_generic,  # Single handler for websites/apps
    "send email": handle_send_email,
    "ای میل بھیجیں": handle_send_email,
    "set reminder": handle_set_reminder,
    "search": handle_search_query,
    "play": handle_play_query,
}

# Load patterns from JSON
def load_command_patterns():
    file_path = os.path.join(os.path.dirname(__file__), "command_patterns.json")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find command_patterns.json at {file_path}")

def load_simple_commands():
    """
    Load simple commands dynamically from the JSON patterns file.
    """
    patterns = load_command_patterns()
    simple_commands = []

    # Iterate over the commands in the JSON file
    for command, data in patterns["commands"].items():
        # Consider commands simple if they match specific criteria
        if command.startswith("open"):  # Adjust the logic to suit your needs
            simple_commands.append(command)

    return simple_commands


def fuzzy_match(command, target, threshold=80):
    """Checks similarity using a threshold."""
    return fuzz.partial_ratio(command, target) >= threshold


def normalize_urdu_command(command):
    patterns = load_command_patterns()
    command = command.strip().lower()

    for action, data in patterns["commands"].items():
        urdu_pattern = data["patterns"].get("urdu")
        english_pattern = data["patterns"].get("english")
        synonyms = data.get("synonyms", [])

        # Check exact matches in synonyms
        if command in synonyms or action in command:
            return action

        # Fuzzy match synonyms
        for synonym in synonyms:
            if fuzzy_match(command, synonym):
                return action

        # Check Urdu and English patterns
        if urdu_pattern and re.search(urdu_pattern, command, re.IGNORECASE):
            return action

        if english_pattern and re.search(english_pattern, command, re.IGNORECASE):
            return action

    return command  # Return original if no match is found


def execute_complex_command(command, params=""):
    if command in COMMAND_HANDLERS:
        try:
            # Pass extracted parameters (e.g., search query or song name) to handler function
            return COMMAND_HANDLERS[command](params)
        except Exception as e:
            logging.error(f"Error executing command {command}: {e}")
            return f"Error: {str(e)}"

    logging.warning(f"Command not recognized: {command}")
    return None


def execute_simple_command(command):
    try:
        return open_generic(command)
    except Exception as e:
        logging.error(f"Error executing simple command {command}: {e}")
        return f"Error opening {command}. Please try again."


def classify_command(normalized_command):
    simple_commands = load_simple_commands()

    if normalized_command in simple_commands:
        return "simple"
    elif normalized_command in COMMAND_HANDLERS.keys():
        return "complex"
    return "unknown"

