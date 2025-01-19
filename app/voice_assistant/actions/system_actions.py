import os
import webbrowser
import subprocess


# Open websites and applications
def open_generic(command):
    target = command.lower().replace("open", "").strip().strip('"').strip("'")
    print(target)
    if not target:
        return "No target specified. Please specify what to open."


    website_urls = {
        "youtube": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "google": "https://www.google.com",
        "linkedin": "https://www.linkedin.com",
        "instagram": "https://www.instagram.com",
        "github": "https://www.github.com",
        "stackoverflow": "https://stackoverflow.com",
        "w3schools": "https://www.w3schools.com",
        "geeksforgeeks": "https://www.geeksforgeeks.org",
        "coursera": "https://www.coursera.org",
        "udemy": "https://www.udemy.com",
        "codeforces": "https://codeforces.com",
        "leetcode": "https://leetcode.com",
        "amazon": "https://www.amazon.com",
        "reddit": "https://www.reddit.com",
        "netflix": "https://www.netflix.com",
    }


    # Check if it's an application
    applications = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "vscode": "C:\\Users\\SAMI\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Visual Studio Code\\Code.exe",
        "pycharm": "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\JetBrains\\bin\\pycharm64.exe",
        "word": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
        "powerpoint": "C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE",
        "excel": "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
        "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    }

    if target in website_urls:
            url_or_app = website_urls[target]
            if url_or_app.startswith("http"):
                webbrowser.open(url_or_app)
            else:
                subprocess.Popen(url_or_app)
            return f"Opening {target}."

    if target in applications:
        subprocess.Popen(applications[target])
        return f"Opening {target}."

    return f"'{target}' not recognized as a website or application."