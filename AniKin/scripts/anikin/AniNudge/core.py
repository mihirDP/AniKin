"""
AniNudge.py
Nudge Keys â€” shift selected keyframes left or right by N frames.

Works on Graph Editor key selection if available, otherwise shifts
all keys on selected objects.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk


def execute(frames=1):
    """
    Nudge keyframes by the given number of frames.

    Args:
        frames: Positive = shift right, negative = shift left.
    """
    direction = "right" if frames > 0 else "left"

    with UndoChunk("AniKin: Nudge Keys {} by {}".format(direction, abs(frames))):
        # Check for Graph Editor key selection first
        graph_sel = cmds.keyframe(query=True, selected=True, name=True) or []
        if graph_sel:
            cmds.keyframe(edit=True, relative=True, timeChange=frames)
        else:
            # Apply to all keys on selected objects
            sel = cmds.ls(selection=True) or []
            if not sel:
                cmds.warning("AniKin Nudge: Select objects or keyframes.")
                return
            for node in sel:
                cmds.keyframe(node, edit=True, relative=True,
                              timeChange=frames)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Nudged {} {}".format(direction, abs(frames)),
        pos="topCenter", fade=True, fadeStayTime=800
    )

