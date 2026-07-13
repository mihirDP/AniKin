"""
settings.py
Preferences and layout settings manager for AniKin.

Saves and loads general settings like toolbar section order and visibility.
"""

import os
import json
import maya.cmds as cmds

# Settings file path
SETTINGS_FILE = os.path.expanduser("~/maya/AniKin_settings.json")

DEFAULT_SECTIONS = [
    "Brand",
    "Selection",
    "Pose",
    "Tween Slider",
    "Tangents",
    "Playback",
    "Channels",
    "Modules",
    "Curves",
    "Setup"
]


def default_settings():
    """Return the default configuration dictionary."""
    return {
        "theme": "MayaBlue",
        "section_order": list(DEFAULT_SECTIONS),
        "visible_sections": list(DEFAULT_SECTIONS),
        "pose_library_roots": [os.path.expanduser("~/maya/anikin_poses")],
        "debug_mode": False
    }


def load_settings():
    """Load settings from JSON config file."""
    default = default_settings()
    
    if not os.path.exists(SETTINGS_FILE):
        return default
        
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Ensure all default keys exist
            for key, val in default.items():
                if key not in data:
                    data[key] = val
            
            # Migrate legacy section names to current names
            legacy_map = {
                "Transform": "Pose",
                "Timing": "Playback",
                "Workflow": "Modules"
            }
            for lst in ("section_order", "visible_sections"):
                if lst in data:
                    new_list = []
                    for sec in data[lst]:
                        mapped_sec = legacy_map.get(sec, sec)
                        if mapped_sec not in new_list:
                            new_list.append(mapped_sec)
                    data[lst] = new_list

            # Dynamically register any new sections added in updates
            for sec in DEFAULT_SECTIONS:
                if sec not in data["section_order"]:
                    data["section_order"].append(sec)
                if sec not in data["visible_sections"]:
                    data["visible_sections"].append(sec)
            return data
    except Exception as e:
        cmds.warning("AniKin: Error loading settings: {}".format(e))
        return default


def save_settings(data):
    """Save settings dict to JSON config file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        cmds.warning("AniKin: Error saving settings: {}".format(e))
        return False
