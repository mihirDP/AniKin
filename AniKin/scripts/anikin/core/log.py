"""
log.py
Logging system for AniKin.
Saves logs to an external file in the system temp directory if debug mode is active.
"""

import os
import tempfile
import time
from anikin.core import settings

LOG_FILE = os.path.join(tempfile.gettempdir(), "AniKin.log")


def log_debug(message):
    """Log a debug message if debug mode is enabled in the preferences."""
    data = settings.load_settings()
    if not data.get("debug_mode", False):
        return

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = "[{}] {}\n".format(timestamp, message)
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(formatted)
    except Exception:
        pass
