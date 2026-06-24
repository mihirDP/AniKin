"""
timeline.py
Timeline range detection utilities for AniKin.

Provides a canonical way to detect whether the user has Shift+clicked
(highlighted) a range on Maya's timeline, and to retrieve that range.

Maya stores the highlighted range on the global ``$gPlayBackSlider``
time-control.  When no range is highlighted the control reports
rangeVisible=False and we fall back to the current frame.
"""

import maya.cmds as cmds
import maya.mel as mel


def get_timeline_range():
    """
    Return the user's highlighted timeline range, or the current frame.

    Returns:
        (start_frame, end_frame, is_range) where *is_range* is True when the
        user has Shift+clicked to highlight a span of frames on the timeline.

    When ``is_range`` is False, both ``start_frame`` and ``end_frame`` equal
    the current frame.
    """
    try:
        slider = mel.eval("$tmpVar=$gPlayBackSlider")
        if cmds.timeControl(slider, query=True, rangeVisible=True):
            arr = cmds.timeControl(slider, query=True, rangeArray=True)
            # Maya returns [start, end+1] so subtract 1 from end
            start = int(arr[0])
            end = int(arr[1]) - 1
            return (start, end, True)
    except Exception:
        pass

    cur = int(cmds.currentTime(query=True))
    return (cur, cur, False)
