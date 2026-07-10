"""
AniColor — frames.py
Frame assignment: assign, remove, and query labels on individual frames
and frame ranges.

Frame labels are editorial notes — intentionally decoupled from animation
keyframes.  Moving a keyframe does not auto-move the color mark.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.log import log_debug
from anikin.core.timeline import get_timeline_range
from anikin.AniColor.core import (
    load_payload, save_payload,
    add_key_to_marker, remove_key_from_marker,
)


def assign_frame(frame, palette_id, label="", notes=""):
    """Assign a color category to a single frame."""
    data = load_payload()
    frame_str = str(int(frame))

    old_entry = data.get("frames", {}).get(frame_str)
    if old_entry and old_entry.get("palette_id") != palette_id:
        remove_key_from_marker(old_entry["palette_id"], frame)

    data.setdefault("frames", {})[frame_str] = {
        "palette_id": palette_id,
        "label": label,
        "notes": notes,
    }

    with UndoChunk("AniColor: Assign Frame {}".format(int(frame))):
        add_key_to_marker(palette_id, frame)
        save_payload(data)


def assign_selection_to_palette(palette_id, label=""):
    """Assign the current timeline selection to a palette slot."""
    start, end, is_range = get_timeline_range()
    if is_range:
        assign_range(start, end, palette_id, label=label)
    else:
        assign_frame(start, palette_id, label=label)


def remove_frame(frame):
    """Remove a frame's color assignment and label."""
    data = load_payload()
    frame_str = str(int(frame))
    entry = data.get("frames", {}).get(frame_str)
    if not entry:
        return
    with UndoChunk("AniColor: Remove Frame {}".format(int(frame))):
        remove_key_from_marker(entry["palette_id"], frame)
        del data["frames"][frame_str]
        save_payload(data)


def update_frame_label(frame, label="", notes=None):
    """Update the label and/or notes on an already-assigned frame."""
    data = load_payload()
    frame_str = str(int(frame))
    entry = data.get("frames", {}).get(frame_str)
    if not entry:
        return False
    if label is not None:
        entry["label"] = label
    if notes is not None:
        entry["notes"] = notes
    data["frames"][frame_str] = entry
    save_payload(data)
    return True


def get_frame_data(frame):
    """Return the label dict for a frame, or None."""
    data = load_payload()
    return data.get("frames", {}).get(str(int(frame)))


def get_all_frames():
    """Return the full frames dict."""
    data = load_payload()
    return data.get("frames", {})


def _next_range_id(ranges):
    existing = set(ranges.keys())
    for i in range(1, 1000):
        rid = "r{:03d}".format(i)
        if rid not in existing:
            return rid
    return "r999"


def assign_range(start, end, palette_id, label="", notes=""):
    """Assign a color category to a frame range (block marking)."""
    data = load_payload()
    rid = _next_range_id(data.get("ranges", {}))
    data.setdefault("ranges", {})[rid] = {
        "palette_id": palette_id,
        "start": int(start), "end": int(end),
        "label": label, "notes": notes,
    }
    with UndoChunk("AniColor: Assign Range {}-{}".format(int(start), int(end))):
        for f in range(int(start), int(end) + 1):
            add_key_to_marker(palette_id, f)
        save_payload(data)
    cmds.inViewMessage(
        amg="<hl>AniColor</hl>: Colored frames {}-{}".format(int(start), int(end)),
        pos="topCenter", fade=True, fadeStayTime=1500)


def remove_range(range_id):
    """Remove a range assignment and its marker keys."""
    data = load_payload()
    rng = data.get("ranges", {}).get(range_id)
    if not rng:
        return
    pid = rng["palette_id"]
    with UndoChunk("AniColor: Remove Range"):
        for f in range(int(rng["start"]), int(rng["end"]) + 1):
            if str(f) not in data.get("frames", {}):
                remove_key_from_marker(pid, f)
        del data["ranges"][range_id]
        save_payload(data)


def get_all_ranges():
    """Return the full ranges dict."""
    data = load_payload()
    return data.get("ranges", {})


def search_frames(query="", palette_ids=None, frame_min=None, frame_max=None):
    """Search across all frame labels and notes."""
    data = load_payload()
    results = []
    query_lower = query.lower() if query else ""
    for frame_str, entry in data.get("frames", {}).items():
        frame = int(frame_str)
        if frame_min is not None and frame < frame_min:
            continue
        if frame_max is not None and frame > frame_max:
            continue
        if palette_ids and entry.get("palette_id") not in palette_ids:
            continue
        if query_lower:
            searchable = entry.get("label", "").lower() + entry.get("notes", "").lower()
            if query_lower not in searchable:
                continue
        results.append((frame, entry))
    results.sort(key=lambda x: x[0])
    return results
