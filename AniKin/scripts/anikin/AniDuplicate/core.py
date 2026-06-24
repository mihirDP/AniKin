"""
AniDuplicate.py
Keyframe Duplicate & Slide Tool — copies a range of keyframes and shifts them to a target frame.

Uses the timeline range helper so that Shift+clicking the timeline to define
a source range works correctly.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.timeline import get_timeline_range
from anikin.core.log import log_debug


def duplicate_and_slide(start_frame=None, end_frame=None, target_frame=None,
                        mode="overwrite"):
    """
    Duplicate keyframes of selected objects from [start_frame, end_frame]
    and paste/slide them to start at target_frame.

    If start_frame/end_frame are not supplied the highlighted timeline range
    (or the current frame) is used automatically.

    Args:
        start_frame: Start of key range to copy (optional).
        end_frame:   End of key range to copy (optional).
        target_frame: Destination frame where the copied range will begin.
        mode: "overwrite" (replace existing keys in target range) or "merge".
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return False

    # Auto-detect from timeline if not explicitly provided
    if start_frame is None or end_frame is None:
        s, e, _ = get_timeline_range()
        start_frame = start_frame if start_frame is not None else s
        end_frame = end_frame if end_frame is not None else e

    # Check if there are keys in the source range
    has_keys = False
    for node in sel:
        key_count = cmds.keyframe(node, time=(start_frame, end_frame),
                                  query=True, keyframeCount=True)
        if key_count and key_count > 0:
            has_keys = True
            break

    if not has_keys:
        cmds.warning("AniDuplicate: No keyframes found in range [{}, {}].".format(
            start_frame, end_frame))
        return False

    if target_frame is None:
        cmds.warning("AniDuplicate: No target frame specified.")
        return False

    duration = end_frame - start_frame
    dest_end = target_frame + duration

    with UndoChunk("AniKin: Duplicate & Slide Keys"):
        for node in sel:
            # Copy keys in source range
            cmds.copyKey(node, time=(start_frame, end_frame))

            # If overwrite mode, clear destination range first
            if mode == "overwrite":
                cmds.cutKey(node, time=(target_frame, dest_end), option="keys", clear=True)

            # Paste keys at target time
            paste_option = "replace" if mode == "overwrite" else "merge"
            cmds.pasteKey(node, time=(target_frame, target_frame),
                          option=paste_option)

    msg = "Duplicated block [{}-{}] to frame {} (mode: {})".format(
        start_frame, end_frame, target_frame, mode)
    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: " + msg,
        pos="topCenter", fade=True, fadeStayTime=1500
    )
    print("[AniKin] " + msg)
    return True
