"""
AniKeyNav.py
Keyframe Navigation â€” jump to previous/next keyframes.

Provides one-click buttons to navigate the timeline to the
nearest keyframe on the selected object's animation curves.
"""

import maya.cmds as cmds


def goto_prev_key():
    """Jump the playhead to the previous keyframe of the selected objects."""
    current = cmds.currentTime(query=True)
    sel = cmds.ls(selection=True) or []

    if sel:
        prev = cmds.findKeyframe(sel[0], which="previous",
                                  time=(current, current))
        if prev is not None and prev != current:
            cmds.currentTime(prev, edit=True)
            return

    # Fallback: use playbackOptions
    cmds.currentTime(current - 1, edit=True)


def goto_next_key():
    """Jump the playhead to the next keyframe of the selected objects."""
    current = cmds.currentTime(query=True)
    sel = cmds.ls(selection=True) or []

    if sel:
        nxt = cmds.findKeyframe(sel[0], which="next",
                                 time=(current, current))
        if nxt is not None and nxt != current:
            cmds.currentTime(nxt, edit=True)
            return

    # Fallback: advance one frame
    cmds.currentTime(current + 1, edit=True)


def goto_first_key():
    """Jump to the first keyframe of the selected objects."""
    sel = cmds.ls(selection=True) or []
    if sel:
        times = cmds.keyframe(sel[0], query=True, timeChange=True) or []
        if times:
            cmds.currentTime(min(times), edit=True)
            return
    # Fallback: go to playback start
    cmds.currentTime(cmds.playbackOptions(query=True, minTime=True), edit=True)


def goto_last_key():
    """Jump to the last keyframe of the selected objects."""
    sel = cmds.ls(selection=True) or []
    if sel:
        times = cmds.keyframe(sel[0], query=True, timeChange=True) or []
        if times:
            cmds.currentTime(max(times), edit=True)
            return
    # Fallback: go to playback end
    cmds.currentTime(cmds.playbackOptions(query=True, maxTime=True), edit=True)

