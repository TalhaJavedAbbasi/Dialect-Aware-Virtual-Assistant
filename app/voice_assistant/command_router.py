from .actions.web_actions import open_website
from .actions.system_actions import open_generic
from .actions.complex_actions import handle_send_email, handle_set_reminder, handle_search_query, handle_play_query

COMMAND_HANDLERS = {
    "open": open_generic,  # Single command handler for both websites and applications
    "send email": handle_send_email,
    "set reminder": handle_set_reminder,
    "search": handle_search_query,
    "play": handle_play_query,
}


def execute_complex_command(command):
    """
    Executes both simple and complex commands using a handler-based approach.
    Args:
        command (str): The user-provided command string.

    Returns:
        str: The result or response after executing the command.
    """
    for key, handler in COMMAND_HANDLERS.items():
        if command.lower().startswith(key):  # Match the command keyword
            try:
                # Pass the full command to the handler (no need for the conditional check)
                return handler(command)
            except ValueError as ve:
                return f"Error: {str(ve)}"
    return None


