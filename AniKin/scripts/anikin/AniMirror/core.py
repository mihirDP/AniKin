"""
AniMirror.py
Pose Copy/Paste/Mirror — clipboard-based pose management.

Provides:
- copy_pose(): Snapshot all keyable attribute values into an in-memory clipboard.
- paste_pose(): Apply stored pose values to selected objects.
- mirror_pose(): Mirror pose by negating translate X/Z and rotate Y.
- flip_pose(): Swap left/right side pose (requires naming convention).

When the user has Shift+clicked a timeline range, copy/paste operations
work across the full range of keyframes, not just the current frame.
"""

import re
import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.timeline import get_timeline_range

# In-memory pose clipboard
# Single-frame: {node_short_name: {attr: value, ...}, ...}
# Range:        {node_short_name: {attr: {frame: value, ...}, ...}, ...}
_POSE_CLIPBOARD = {}
_CLIPBOARD_IS_RANGE = False
_CLIPBOARD_RANGE = (0, 0)


def copy_pose():
    """
    Snapshot all keyable attribute values from selected objects.
    If a timeline range is highlighted, copies keyframed values across
    that entire range (preserving the timing).  Otherwise copies a
    single-frame snapshot.
    """
    global _POSE_CLIPBOARD, _CLIPBOARD_IS_RANGE, _CLIPBOARD_RANGE
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return

    start, end, is_range = get_timeline_range()
    _CLIPBOARD_IS_RANGE = is_range
    _CLIPBOARD_RANGE = (start, end)
    _POSE_CLIPBOARD = {}

    if is_range:
        for node in sel:
            _POSE_CLIPBOARD[node] = {}
            attrs = cmds.listAttr(node, keyable=True) or []
            for attr in attrs:
                full = "{}.{}".format(node, attr)
                key_times = cmds.keyframe(full, query=True,
                                          time=(start, end),
                                          timeChange=True) or []
                key_vals = cmds.keyframe(full, query=True,
                                         time=(start, end),
                                         valueChange=True) or []
                if key_times:
                    _POSE_CLIPBOARD[node][attr] = dict(zip(key_times, key_vals))
        label = "Pose range [{}-{}] copied ({} objects)".format(start, end, len(sel))
    else:
        for node in sel:
            attrs = cmds.listAttr(node, keyable=True) or []
            _POSE_CLIPBOARD[node] = {}
            for attr in attrs:
                full = "{}.{}".format(node, attr)
                try:
                    val = cmds.getAttr(full)
                    _POSE_CLIPBOARD[node][attr] = val
                except Exception:
                    pass
        label = "Pose copied ({} objects)".format(len(sel))

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: {}".format(label),
        pos="topCenter", fade=True, fadeStayTime=1200
    )


def paste_pose():
    """
    Apply the stored clipboard pose to the currently selected objects.
    If a range was copied, the keys are pasted at their original relative
    offsets from the current frame.
    """
    if not _POSE_CLIPBOARD:
        cmds.warning("AniKin: No pose in clipboard. Copy a pose first.")
        return

    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select objects to paste pose onto.")
        return

    with UndoChunk("AniKin: Paste Pose"):
        if _CLIPBOARD_IS_RANGE:
            # Paste range — offset keys relative to the current frame
            src_start = _CLIPBOARD_RANGE[0]
            cur = cmds.currentTime(query=True)
            offset = cur - src_start

            for node in sel:
                if node in _POSE_CLIPBOARD:
                    stored = _POSE_CLIPBOARD[node]
                elif len(sel) == 1 and len(_POSE_CLIPBOARD) == 1:
                    stored = list(_POSE_CLIPBOARD.values())[0]
                else:
                    continue

                for attr, frame_vals in stored.items():
                    if not isinstance(frame_vals, dict):
                        continue
                    full = "{}.{}".format(node, attr)
                    if not cmds.objExists(full) or cmds.getAttr(full, lock=True):
                        continue
                    for frame, val in frame_vals.items():
                        try:
                            cmds.setKeyframe(node, attribute=attr,
                                             time=frame + offset, value=val)
                        except Exception:
                            pass
        else:
            # Single-frame paste (original behaviour)
            for node in sel:
                if node in _POSE_CLIPBOARD:
                    stored = _POSE_CLIPBOARD[node]
                elif len(sel) == 1 and len(_POSE_CLIPBOARD) == 1:
                    stored = list(_POSE_CLIPBOARD.values())[0]
                else:
                    continue

                for attr, val in stored.items():
                    full = "{}.{}".format(node, attr)
                    try:
                        if not cmds.getAttr(full, lock=True):
                            cmds.setAttr(full, val)
                    except Exception:
                        pass

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Pose pasted",
        pos="topCenter", fade=True, fadeStayTime=1200
    )


def mirror_pose():
    """
    Mirror pose on selected objects by negating asymmetric channels.
    Negates translateX, translateZ, rotateY for a standard character rig.
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return

    negate_attrs = ["translateX", "translateZ", "rotateY"]

    with UndoChunk("AniKin: Mirror Pose"):
        for node in sel:
            for attr in negate_attrs:
                full = "{}.{}".format(node, attr)
                if cmds.objExists(full) and not cmds.getAttr(full, lock=True):
                    try:
                        val = cmds.getAttr(full)
                        cmds.setAttr(full, -val)
                    except Exception:
                        pass

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Pose mirrored",
        pos="topCenter", fade=True, fadeStayTime=1200
    )


# ─── Flip Pose (L ↔ R naming swap) ─────────────────────────────────────────

MIRROR_PATTERNS = [
    (r"_L_", "_R_"),    # _L_ / _R_
    (r"_L$", "_R"),     # suffix _L / _R
    (r"Left", "Right"), # camelCase
    (r"left", "right"), # lowercase
    (r":L_", ":R_"),    # namespace:L_
]


def find_mirror_pair(node):
    """Returns the mirror counterpart of a node, or None if not found."""
    for pat_l, pat_r in MIRROR_PATTERNS:
        # Try L -> R
        mirrored = re.sub(pat_l, pat_r, node)
        if mirrored != node and cmds.objExists(mirrored):
            return mirrored
        # Try R -> L
        mirrored = re.sub(pat_r, pat_l, node)
        if mirrored != node and cmds.objExists(mirrored):
            return mirrored
    return None


def flip_pose():
    """
    Swap poses between left/right symmetric pairs of selected controls.
    If control has no pair (e.g. Center/Spine), mirror its asymmetric channels.
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return

    negate_attrs = ["translateX", "translateZ", "rotateY"]

    pairs = []
    processed = set()
    singletons = []

    for node in sel:
        if node in processed:
            continue
        pair = find_mirror_pair(node)
        if pair:
            pairs.append((node, pair))
            processed.add(node)
            processed.add(pair)
        else:
            singletons.append(node)

    with UndoChunk("AniKin: Flip Pose"):
        for node_a, node_b in pairs:
            attrs_a = cmds.listAttr(node_a, keyable=True) or []
            attrs_b = cmds.listAttr(node_b, keyable=True) or []

            vals_a = {}
            for attr in attrs_a:
                full = "{}.{}".format(node_a, attr)
                try:
                    vals_a[attr] = cmds.getAttr(full)
                except Exception:
                    pass

            vals_b = {}
            for attr in attrs_b:
                full = "{}.{}".format(node_b, attr)
                try:
                    vals_b[attr] = cmds.getAttr(full)
                except Exception:
                    pass

            for attr, val in vals_b.items():
                full = "{}.{}".format(node_a, attr)
                if cmds.objExists(full) and not cmds.getAttr(full, lock=True):
                    try:
                        final_val = -val if attr in negate_attrs else val
                        cmds.setAttr(full, final_val)
                    except Exception:
                        pass

            for attr, val in vals_a.items():
                full = "{}.{}".format(node_b, attr)
                if cmds.objExists(full) and not cmds.getAttr(full, lock=True):
                    try:
                        final_val = -val if attr in negate_attrs else val
                        cmds.setAttr(full, final_val)
                    except Exception:
                        pass

        for node in singletons:
            for attr in negate_attrs:
                full = "{}.{}".format(node, attr)
                if cmds.objExists(full) and not cmds.getAttr(full, lock=True):
                    try:
                        val = cmds.getAttr(full)
                        cmds.setAttr(full, -val)
                    except Exception:
                        pass

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Pose flipped",
        pos="topCenter", fade=True, fadeStayTime=1200
    )


def reset_transform():
    """
    Reset all keyable transform attributes to their default values (0, except scale=1).
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return

    scale_attrs = {"scaleX", "scaleY", "scaleZ"}

    with UndoChunk("AniKin: Reset Transform"):
        for node in sel:
            attrs = cmds.listAttr(node, keyable=True) or []
            for attr in attrs:
                full = "{}.{}".format(node, attr)
                if cmds.objExists(full) and not cmds.getAttr(full, lock=True):
                    try:
                        default_val = 1.0 if attr in scale_attrs else 0.0
                        cmds.setAttr(full, default_val)
                    except Exception:
                        pass

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Transform reset",
        pos="topCenter", fade=True, fadeStayTime=1200
    )
