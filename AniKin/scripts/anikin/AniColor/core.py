"""
AniColor — core.py
Data layer for AniColor: scene-persistent storage via a hidden network node,
marker animCurve creation, and JSON payload management.

All color/label data lives in a single hidden 'network' node as a JSON string
attribute.  Marker curves (animCurveTU) provide the colored timeline ticks
via Maya's native curveColor renderer.
"""

import json
import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.log import log_debug

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

STORAGE_NODE = "anikin_color_data"
MAX_PALETTE_SLOTS = 20  # Maya curveColor renderer budget

# Default palette shipped with AniColor (8 slots)
DEFAULT_PALETTE = [
    {"id": "p01", "name": "Gold Poses",     "color": [1.0, 0.85, 0.0],   "visible": True},
    {"id": "p02", "name": "Breakdowns",     "color": [0.2, 0.8, 1.0],    "visible": True},
    {"id": "p03", "name": "Contacts",       "color": [0.27, 0.73, 0.27], "visible": True},
    {"id": "p04", "name": "Head Lead",      "color": [0.67, 0.33, 1.0],  "visible": True},
    {"id": "p05", "name": "Overshoots",     "color": [1.0, 0.27, 0.27],  "visible": True},
    {"id": "p06", "name": "Settle",         "color": [0.0, 0.8, 0.67],   "visible": True},
    {"id": "p07", "name": "Anticipation",   "color": [1.0, 0.6, 0.0],    "visible": True},
    {"id": "p08", "name": "Custom",         "color": [0.8, 0.8, 0.8],    "visible": True},
]

_EMPTY_PAYLOAD = {
    "version": 1,
    "palettes": [],
    "frames": {},
    "ranges": {},
}

# Session cache (survives "Optimize Scene" deleting the node)
_SESSION_CACHE = None


# ──────────────────────────────────────────────────────────────
# Storage node management
# ──────────────────────────────────────────────────────────────

def ensure_storage_node():
    """Create the hidden network storage node if it doesn't exist."""
    global _SESSION_CACHE
    if not cmds.objExists(STORAGE_NODE):
        cmds.createNode("network", name=STORAGE_NODE, skipSelect=True)
        cmds.addAttr(STORAGE_NODE, longName="anikin_payload", dataType="string")

        # Restore from session cache if the node was deleted
        if _SESSION_CACHE is not None:
            cmds.setAttr(STORAGE_NODE + ".anikin_payload",
                         json.dumps(_SESSION_CACHE), type="string")
        else:
            cmds.setAttr(STORAGE_NODE + ".anikin_payload",
                         json.dumps(_EMPTY_PAYLOAD), type="string")

        # Hide in Outliner
        try:
            cmds.setAttr(STORAGE_NODE + ".hiddenInOutliner", True)
        except Exception:
            pass
    return STORAGE_NODE


def load_payload():
    """Load and return the AniColor JSON payload from the scene."""
    global _SESSION_CACHE
    ensure_storage_node()
    try:
        raw = cmds.getAttr(STORAGE_NODE + ".anikin_payload") or "{}"
        data = json.loads(raw)
        # Ensure required keys exist
        for key in ("version", "palettes", "frames", "ranges"):
            if key not in data:
                data[key] = _EMPTY_PAYLOAD[key]
        _SESSION_CACHE = data
        return data
    except Exception:
        return dict(_EMPTY_PAYLOAD)


def save_payload(data):
    """Persist the AniColor JSON payload to the scene node."""
    global _SESSION_CACHE
    ensure_storage_node()
    _SESSION_CACHE = data
    try:
        cmds.setAttr(STORAGE_NODE + ".anikin_payload",
                     json.dumps(data), type="string")
    except Exception as e:
        cmds.warning("AniColor: Failed to save payload: {}".format(e))


# ──────────────────────────────────────────────────────────────
# Marker AnimCurve management
# ──────────────────────────────────────────────────────────────

def _marker_curve_name(palette_id):
    """Return the Maya node name for a palette's marker curve."""
    return "anikin_cm_{}".format(palette_id)


def create_marker_curve(palette_id, r, g, b):
    """
    Create (or recreate) a hidden animCurveTU node that serves as a
    timeline visual marker for a given color palette slot.

    The curve is not connected to any attribute — it exists purely
    to render colored ticks in the timeline via Maya's curveColor.
    """
    name = _marker_curve_name(palette_id)

    if cmds.objExists(name):
        cmds.delete(name)

    curve = cmds.createNode("animCurveTU", name=name, skipSelect=True)

    # Enable custom curve color
    cmds.setAttr(curve + ".useCurveColor", True)
    cmds.setAttr(curve + ".curveColorR", r)
    cmds.setAttr(curve + ".curveColorG", g)
    cmds.setAttr(curve + ".curveColorB", b)

    # Hide from Outliner
    try:
        cmds.setAttr(curve + ".hiddenInOutliner", True)
    except Exception:
        pass

    log_debug("AniColor: Created marker curve '{}' ({}, {}, {})".format(
        name, r, g, b))
    return curve


def update_marker_curve_color(palette_id, r, g, b):
    """Update the color of an existing marker curve."""
    name = _marker_curve_name(palette_id)
    if cmds.objExists(name):
        cmds.setAttr(name + ".curveColorR", r)
        cmds.setAttr(name + ".curveColorG", g)
        cmds.setAttr(name + ".curveColorB", b)


def set_marker_curve_visibility(palette_id, visible):
    """
    Toggle visibility of a marker curve.
    When hidden, the colored ticks disappear from the timeline.
    """
    name = _marker_curve_name(palette_id)
    if cmds.objExists(name):
        cmds.setAttr(name + ".useCurveColor", visible)


def delete_marker_curve(palette_id):
    """Delete a marker curve from the scene."""
    name = _marker_curve_name(palette_id)
    if cmds.objExists(name):
        cmds.delete(name)
        log_debug("AniColor: Deleted marker curve '{}'".format(name))


def add_key_to_marker(palette_id, frame):
    """Place a step key on the marker curve at the given frame."""
    name = _marker_curve_name(palette_id)
    if not cmds.objExists(name):
        return
    cmds.setKeyframe(name, time=(frame,), value=1.0,
                     outTangentType="step")


def remove_key_from_marker(palette_id, frame):
    """Remove a key from the marker curve at the given frame."""
    name = _marker_curve_name(palette_id)
    if not cmds.objExists(name):
        return
    cmds.cutKey(name, time=(frame, frame), clear=True)


# ──────────────────────────────────────────────────────────────
# Scene lifecycle
# ──────────────────────────────────────────────────────────────

def rebuild_from_payload():
    """
    Reconstruct marker curves from the stored JSON payload.
    Called on scene open to re-acquire Python references.
    """
    data = load_payload()
    for pal in data.get("palettes", []):
        pid = pal["id"]
        r, g, b = pal["color"]
        create_marker_curve(pid, r, g, b)

        if not pal.get("visible", True):
            set_marker_curve_visibility(pid, False)

    # Re-place keys for each frame assignment
    for frame_str, entry in data.get("frames", {}).items():
        frame = float(frame_str)
        pid = entry.get("palette_id")
        if pid:
            add_key_to_marker(pid, frame)

    # Re-place keys for range assignments (start and end ticks)
    for range_id, rng in data.get("ranges", {}).items():
        pid = rng.get("palette_id")
        if pid:
            start = float(rng.get("start", 0))
            end = float(rng.get("end", 0))
            for f in range(int(start), int(end) + 1):
                add_key_to_marker(pid, f)

    log_debug("AniColor: Rebuilt marker curves from payload")


def clear_state():
    """Clear all AniColor state — called on File > New."""
    global _SESSION_CACHE
    _SESSION_CACHE = None

    # Delete all marker curves
    for node in cmds.ls("anikin_cm_*", type="animCurveTU") or []:
        try:
            cmds.delete(node)
        except Exception:
            pass

    # Delete storage node
    if cmds.objExists(STORAGE_NODE):
        try:
            cmds.delete(STORAGE_NODE)
        except Exception:
            pass

    log_debug("AniColor: State cleared")


def initialize_default_palette():
    """
    Set up the default 8-slot palette if the payload is empty.
    Called when AniColor is first opened in a scene with no data.
    """
    data = load_payload()
    if data.get("palettes"):
        return data  # Already has palette data

    data["palettes"] = []
    for slot in DEFAULT_PALETTE:
        pal_entry = {
            "id": slot["id"],
            "name": slot["name"],
            "color": list(slot["color"]),
            "visible": True,
            "marker_curve": _marker_curve_name(slot["id"]),
        }
        data["palettes"].append(pal_entry)
        create_marker_curve(slot["id"], *slot["color"])

    save_payload(data)
    log_debug("AniColor: Initialized default palette (8 slots)")
    return data
