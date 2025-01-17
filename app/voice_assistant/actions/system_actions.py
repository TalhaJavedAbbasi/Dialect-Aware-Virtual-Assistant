import os
import webbrowser
import subprocess
def open_generic(command):
    """
    Determines whether to open a website or an application based on the command.
    Args:
        command (str): The user-provided command (e.g., "open YouTube").

    Returns:
        str: Response message after performing the action.
    """
    # Extract the argument (e.g., "YouTube" or "Notepad")
    target = command.lower().replace("open", "").strip()

    # Check if it's a website
    website_urls = {
        "youtube": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "google": "https://www.google.com",
        "twitter": "https://www.twitter.com",
    }
    if target in website_urls:
        webbrowser.open(website_urls[target])
        return f"Opening {target} website."

    # Check if it's an application
    applications = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
    }
    if target in applications:
        subprocess.Popen(applications[target])  # Open asynchronously
        return f"Opening {target} application."

    # If neither, return an error message
    return f"'{target}' not recognized as a website or application."

