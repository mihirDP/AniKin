"""
AniColor — palette.py
Palette slot management: create, edit, delete, reorder, and toggle color slots.

Each palette slot maps to a hidden animCurveTU marker node in the scene.
The curveColor of that node determines the tick color in the timeline.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.log import log_debug
from anikin.AniColor.core import (
    load_payload, save_payload,
    create_marker_curve, update_marker_curve_color,
    set_marker_curve_visibility, delete_marker_curve,
    _marker_curve_name, MAX_PALETTE_SLOTS,
)


def get_palettes():
    """Return the list of palette slot dicts."""
    data = load_payload()
    return data.get("palettes", [])


def get_palette_by_id(palette_id):
    """Return a single palette dict by ID, or None."""
    for p in get_palettes():
        if p["id"] == palette_id:
            return p
    return None


def _next_palette_id(palettes):
    """Generate the next available palette ID like 'p09', 'p10', etc."""
    existing = {p["id"] for p in palettes}
    for i in range(1, MAX_PALETTE_SLOTS + 1):
        pid = "p{:02d}".format(i)
        if pid not in existing:
            return pid
    return None


def add_palette_slot(name="New Slot", color=None):
    """
    Add a new palette slot.

    Args:
        name: Display name for the slot.
        color: [r, g, b] floats 0–1. Defaults to white.

    Returns:
        The new palette dict, or None if at max capacity.
    """
    if color is None:
        color = [0.8, 0.8, 0.8]

    data = load_payload()
    palettes = data.get("palettes", [])

    if len(palettes) >= MAX_PALETTE_SLOTS:
        cmds.warning(
            "AniColor: Maximum {} palette slots reached. "
            "Maya's curveColor renderer does not support more.".format(MAX_PALETTE_SLOTS)
        )
        return None

    pid = _next_palette_id(palettes)
    if pid is None:
        return None

    new_slot = {
        "id": pid,
        "name": name,
        "color": list(color),
        "visible": True,
        "marker_curve": _marker_curve_name(pid),
    }

    with UndoChunk("AniColor: Add Palette Slot"):
        create_marker_curve(pid, *color)
        palettes.append(new_slot)
        data["palettes"] = palettes
        save_payload(data)

    log_debug("AniColor: Added palette slot '{}' ({})".format(name, pid))
    cmds.inViewMessage(
        amg="<hl>AniColor</hl>: Added slot '{}'".format(name),
        pos="topCenter", fade=True, fadeStayTime=1500
    )
    return new_slot


def rename_palette_slot(palette_id, new_name):
    """Rename a palette slot."""
    data = load_payload()
    for p in data.get("palettes", []):
        if p["id"] == palette_id:
            p["name"] = new_name
            save_payload(data)
            log_debug("AniColor: Renamed slot {} → '{}'".format(palette_id, new_name))
            return True
    return False


def change_palette_color(palette_id, r, g, b):
    """Change the color of a palette slot and update all its marker ticks."""
    data = load_payload()
    for p in data.get("palettes", []):
        if p["id"] == palette_id:
            p["color"] = [r, g, b]
            save_payload(data)
            update_marker_curve_color(palette_id, r, g, b)
            log_debug("AniColor: Changed color of {} to ({}, {}, {})".format(
                palette_id, r, g, b))
            return True
    return False


def toggle_palette_visibility(palette_id):
    """Toggle the visibility of a palette slot's marker curve."""
    data = load_payload()
    for p in data.get("palettes", []):
        if p["id"] == palette_id:
            p["visible"] = not p["visible"]
            save_payload(data)
            set_marker_curve_visibility(palette_id, p["visible"])
            state = "visible" if p["visible"] else "hidden"
            log_debug("AniColor: Slot {} is now {}".format(palette_id, state))
            return p["visible"]
    return True


def delete_palette_slot(palette_id):
    """
    Delete a palette slot and all frame assignments associated with it.
    """
    data = load_payload()
    palettes = data.get("palettes", [])
    frames = data.get("frames", {})
    ranges = data.get("ranges", {})

    # Find and remove the palette entry
    data["palettes"] = [p for p in palettes if p["id"] != palette_id]

    # Remove all frame assignments for this palette
    frames_to_remove = [
        f for f, entry in frames.items()
        if entry.get("palette_id") == palette_id
    ]
    for f in frames_to_remove:
        del frames[f]

    # Remove all range assignments for this palette
    ranges_to_remove = [
        rid for rid, rng in ranges.items()
        if rng.get("palette_id") == palette_id
    ]
    for rid in ranges_to_remove:
        del ranges[rid]

    data["frames"] = frames
    data["ranges"] = ranges

    with UndoChunk("AniColor: Delete Palette Slot"):
        delete_marker_curve(palette_id)
        save_payload(data)

    log_debug("AniColor: Deleted palette slot {} (removed {} frames, {} ranges)".format(
        palette_id, len(frames_to_remove), len(ranges_to_remove)))


def get_frame_count_for_palette(palette_id):
    """Return the number of frames assigned to a palette slot."""
    data = load_payload()
    count = sum(
        1 for entry in data.get("frames", {}).values()
        if entry.get("palette_id") == palette_id
    )
    # Also count frames in ranges
    for rng in data.get("ranges", {}).values():
        if rng.get("palette_id") == palette_id:
            start = int(rng.get("start", 0))
            end = int(rng.get("end", 0))
            count += (end - start + 1)
    return count
