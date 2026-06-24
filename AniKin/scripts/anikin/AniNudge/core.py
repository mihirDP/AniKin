"""
AniNudge.py
Nudge Keys — shift selected keyframes left or right by N frames.

Priority order:
1. Graph Editor key selection (if keys are selected there).
2. Timeline highlighted range (Shift+click on the timeline).
3. All keys on the selected objects (fallback).
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.timeline import get_timeline_range


def execute(frames=1):
    """
    Nudge keyframes by the given number of frames.

    Args:
        frames: Positive = shift right, negative = shift left.
    """
    direction = "right" if frames > 0 else "left"

    with UndoChunk("AniKin: Nudge Keys {} by {}".format(direction, abs(frames))):
        # 1. Graph Editor key selection
        graph_sel = cmds.keyframe(query=True, selected=True, name=True) or []
        if graph_sel:
            cmds.keyframe(edit=True, relative=True, timeChange=frames)
        else:
            sel = cmds.ls(selection=True) or []
            if not sel:
                cmds.warning("AniKin Nudge: Select objects or keyframes.")
                return

            # 2. Timeline highlighted range
            start, end, is_range = get_timeline_range()

            for node in sel:
                if is_range:
                    cmds.keyframe(node, edit=True, relative=True,
                                  timeChange=frames,
                                  time=(start, end))
                else:
                    # 3. Fallback: all keys on the object
                    cmds.keyframe(node, edit=True, relative=True,
                                  timeChange=frames)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Nudged {} {}".format(direction, abs(frames)),
        pos="topCenter", fade=True, fadeStayTime=800
    )
