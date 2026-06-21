"""
AniMirror.py
Pose Copy/Paste/Mirror â€” clipboard-based pose management.

Provides:
- copy_pose(): Snapshot all keyable attribute values into an in-memory clipboard.
- paste_pose(): Apply stored pose values to selected objects.
- mirror_pose(): Mirror pose by negating translate X/Z and rotate Y.
- flip_pose(): Swap left/right side pose (requires naming convention).
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn

# In-memory pose clipboard: {node_short_name: {attr: value, ...}, ...}
_POSE_CLIPBOARD = {}


def copy_pose():
    """Snapshot all keyable attribute values from selected objects."""
    global _POSE_CLIPBOARD
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return

    _POSE_CLIPBOARD = {}
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

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Pose copied ({} objects)".format(len(sel)),
        pos="topCenter", fade=True, fadeStayTime=1200
    )


def paste_pose():
    """Apply the stored clipboard pose to the currently selected objects."""
    if not _POSE_CLIPBOARD:
        cmds.warning("AniKin: No pose in clipboard. Copy a pose first.")
        return

    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select objects to paste pose onto.")
        return

    with UndoChunk("AniKin: Paste Pose"):
        for node in sel:
            if node in _POSE_CLIPBOARD:
                stored = _POSE_CLIPBOARD[node]
            elif len(sel) == 1 and len(_POSE_CLIPBOARD) == 1:
                # If only one object selected and one in clipboard, apply regardless of name
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
    Mirror pose on selected objects by negating asymmetric AniChannels.
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

