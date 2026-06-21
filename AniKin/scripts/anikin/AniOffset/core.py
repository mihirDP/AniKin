"""
AniOffset.py
Anim Offset â€” stagger keyframes across a selection by N frames.

Select multiple animated objects: their keyframes will be shifted
progressively so each subsequent object's animation starts N frames
later than the previous, creating a natural stagger/overlap effect.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn


def execute(offset_frames=2, reverse=False):
    """
    Stagger keyframes across selected objects.

    Args:
        offset_frames: Number of frames to offset each successive object.
        reverse: If True, apply offset in reverse selection order.
    """
    sel = get_selected_or_warn(min_count=2)
    if not sel:
        return

    if reverse:
        sel = list(reversed(sel))

    with UndoChunk("AniKin: Anim Offset ({} frames)".format(offset_frames)):
        for i, node in enumerate(sel):
            if i == 0:
                continue  # First object stays put

            frame_shift = offset_frames * i

            # Get all keyframe times for this node
            keys = cmds.keyframe(node, query=True, timeChange=True) or []
            if not keys:
                continue

            # Shift all keys â€” move from last to first to avoid collisions
            unique_times = sorted(set(keys), reverse=(frame_shift > 0))
            for t in unique_times:
                cmds.keyframe(node, edit=True,
                              time=(t, t),
                              relative=True,
                              timeChange=frame_shift)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Offset {} objects by {} frame steps".format(
            len(sel), offset_frames
        ),
        pos="topCenter", fade=True, fadeStayTime=1500
    )

