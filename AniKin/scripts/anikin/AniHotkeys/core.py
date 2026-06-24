"""
AniHotkeys.py
Hotkey management for AniKin tools.

Handles:
- Loading and saving custom hotkey assignments to user preferences.
- Registering runTimeCommands, nameCommands, and hotkey bindings in Maya.
- Querying and resetting AniHotkeys.
"""

import os
import json
import maya.cmds as cmds
from anikin.core.undo import UndoChunk

# Config file path: stored in Maya user preferences directory
CONFIG_FILE = os.path.expanduser("~/maya/AniKin_hotkeys.json")

# Define all bindable tools in AniKin
BINDABLE_TOOLS = [
    {
        "id": "align_all",
        "name": "Align All (Translate + Rotate)",
        "category": "Transform",
        "command": "import anikin.AniAlign as al; al.execute(True, True)"
    },
    {
        "id": "align_t",
        "name": "Align Translation Only",
        "category": "Transform",
        "command": "import anikin.AniAlign as al; al.execute(True, False)"
    },
    {
        "id": "align_r",
        "name": "Align Rotation Only",
        "category": "Transform",
        "command": "import anikin.AniAlign as al; al.execute(False, True)"
    },
    {
        "id": "nudge_left_1",
        "name": "Nudge Left 1 Frame",
        "category": "Timing",
        "command": "import anikin.AniNudge as nd; nd.execute(-1)"
    },
    {
        "id": "nudge_right_1",
        "name": "Nudge Right 1 Frame",
        "category": "Timing",
        "command": "import anikin.AniNudge as nd; nd.execute(1)"
    },
    {
        "id": "nudge_left_5",
        "name": "Nudge Left 5 Frames",
        "category": "Timing",
        "command": "import anikin.AniNudge as nd; nd.execute(-5)"
    },
    {
        "id": "nudge_right_5",
        "name": "Nudge Right 5 Frames",
        "category": "Timing",
        "command": "import anikin.AniNudge as nd; nd.execute(5)"
    },
    {
        "id": "anim_offset",
        "name": "Stagger Keys (Anim Offset)",
        "category": "Timing",
        "command": "import anikin.AniOffset as ao; ao.execute(2)"
    },
    {
        "id": "tangent_auto",
        "name": "Set Tangent Auto",
        "category": "Tangents",
        "command": "import anikin.AniTangents as tg; tg.set_tangent('auto')"
    },
    {
        "id": "tangent_flat",
        "name": "Set Tangent Flat",
        "category": "Tangents",
        "command": "import anikin.AniTangents as tg; tg.set_tangent('flat')"
    },
    {
        "id": "tangent_linear",
        "name": "Set Tangent Linear",
        "category": "Tangents",
        "command": "import anikin.AniTangents as tg; tg.set_tangent('linear')"
    },
    {
        "id": "tangent_step",
        "name": "Set Tangent Stepped",
        "category": "Tangents",
        "command": "import anikin.AniTangents as tg; tg.set_tangent('step')"
    },
    {
        "id": "tangent_spline",
        "name": "Set Tangent Spline",
        "category": "Tangents",
        "command": "import anikin.AniTangents as tg; tg.set_tangent('spline')"
    },
    {
        "id": "bake_to_loc",
        "name": "Smart Bake to Locator",
        "category": "Workflow",
        "command": "import anikin.AniBake as sb; sb.bake_to_locator()"
    },
    {
        "id": "bake_from_loc",
        "name": "Smart Bake from Locator",
        "category": "Workflow",
        "command": "import anikin.AniBake as sb; sb.bake_from_locator()"
    },
    {
        "id": "toggle_motion_trail",
        "name": "Toggle Motion Trail",
        "category": "Visualization",
        "command": "import anikin.AniMotion as mt; mt.toggle_motion_trail()"
    },
    {
        "id": "toggle_ghosting",
        "name": "Toggle Ghosting",
        "category": "Visualization",
        "command": "import anikin.AniGhost as gh; gh.toggle_ghosting()"
    },
    {
        "id": "euler_filter",
        "name": "Euler Filter",
        "category": "Curves",
        "command": "import anikin.AniSmooth as sm; sm.euler_filter()"
    },
    {
        "id": "smooth_curves",
        "name": "Smooth Curves",
        "category": "Curves",
        "command": "import anikin.AniSmooth as sm; sm.smooth_curves()"
    },
    {
        "id": "copy_pose",
        "name": "Copy Pose",
        "category": "Pose",
        "command": "import anikin.AniMirror as mr; mr.copy_pose()"
    },
    {
        "id": "paste_pose",
        "name": "Paste Pose",
        "category": "Pose",
        "command": "import anikin.AniMirror as mr; mr.paste_pose()"
    },
    {
        "id": "mirror_pose",
        "name": "Mirror Pose",
        "category": "Pose",
        "command": "import anikin.AniMirror as mr; mr.mirror_pose()"
    },
    {
        "id": "flip_pose",
        "name": "Flip Pose",
        "category": "Pose",
        "command": "import anikin.AniMirror as mr; mr.flip_pose()"
    }
]


def parse_shortcut_string(seq_str):
    """
    Parse a standard shortcut string (e.g. "Ctrl+Alt+Shift+K")
    and return (key, ctl, alt, sht) for Maya's hotkey command.
    """
    if not seq_str or seq_str.lower() == "none":
        return None, False, False, False

    parts = seq_str.split("+")
    ctl = "Ctrl" in parts
    alt = "Alt" in parts
    sht = "Shift" in parts

    # Filter out modifiers to get the key name
    key_parts = [p for p in parts if p not in ["Ctrl", "Alt", "Shift"]]
    if not key_parts:
        return None, False, False, False

    key = key_parts[0]

    # Map special keys to Maya format
    special_map = {
        "Up": "Up",
        "Down": "Down",
        "Left": "Left",
        "Right": "Right",
        "Home": "Home",
        "End": "End",
        "PageUp": "Page_Up",
        "PageDown": "Page_Down",
        "PgUp": "Page_Up",
        "PgDown": "Page_Down",
        "Ins": "Insert",
        "Insert": "Insert",
        "Return": "Return",
        "Enter": "Return",
        "Space": "Space",
        "Del": "Delete",
        "Delete": "Delete",
        "Backspace": "Backspace"
    }

    key = special_map.get(key, key)
    if len(key) == 1:
        key = key.lower()

    return key, ctl, alt, sht


def apply_hotkey(tool_id, shortcut_str):
    """
    Register and bind a hotkey in Maya for a specific tool.
    """
    # 1. Find the tool config
    tool = next((t for t in BINDABLE_TOOLS if t["id"] == tool_id), None)
    if not tool:
        return False

    run_time_name = "AniKin_{}".format(tool_id)
    name_cmd_name = "{}NameCommand".format(run_time_name)

    # 2. Setup runTimeCommand
    if not cmds.runTimeCommand(run_time_name, exists=True):
        cmds.runTimeCommand(
            run_time_name,
            annotation=tool["name"],
            category="AniKin",
            command=tool["command"],
            commandLanguage="python"
        )
    else:
        # Update existing runTimeCommand
        cmds.runTimeCommand(
            run_time_name,
            edit=True,
            command=tool["command"]
        )

    # 3. Setup nameCommand
    if not cmds.nameCommand(name_cmd_name, exists=True):
        cmds.nameCommand(
            name_cmd_name,
            annotation=tool["name"],
            command=run_time_name,
            sourceType="python"
        )

    # 4. Bind the hotkey
    key, ctl, alt, sht = parse_shortcut_string(shortcut_str)
    if key:
        try:
            # First bind the hotkey
            cmds.hotkey(
                keyShortcut=key,
                ctl=ctl,
                alt=alt,
                sht=sht,
                name=name_cmd_name
            )
            return True
        except Exception as e:
            cmds.warning("AniKin: Failed to bind hotkey '{}': {}".format(shortcut_str, e))
            return False
    return False


def remove_hotkey(tool_id, shortcut_str):
    """
    Remove a hotkey binding in Maya.
    """
    key, ctl, alt, sht = parse_shortcut_string(shortcut_str)
    if key:
        try:
            cmds.hotkey(
                keyShortcut=key,
                ctl=ctl,
                alt=alt,
                sht=sht,
                name=""
            )
        except Exception:
            pass


def load_hotkeys():
    """
    Load hotkeys from config file and register them in Maya.
    """
    if not os.path.exists(CONFIG_FILE):
        return {}

    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return {}

    # Register each loaded hotkey
    for tool_id, shortcut_str in data.items():
        if shortcut_str:
            apply_hotkey(tool_id, shortcut_str)

    return data


def save_hotkeys(mappings):
    """
    Save hotkeys mapping dictionary to config file.
    """
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(mappings, f, indent=4)
        return True
    except Exception as e:
        cmds.warning("AniKin: Failed to save hotkeys: {}".format(e))
        return False

