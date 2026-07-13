"""
AniRetime.py
Advanced curve scaling and time-warping with collision-aware integer snapping.

Native Maya scaling produces fractional keys (e.g. frame 12.4), breaking snapping.
This tool implements a two-pass approach:
  1. Native maya scale (preserves tangents correctly).
  2. Collision-aware rounding pass: snaps remaining fractional keys to nearest 
     integers, ensuring keys don't merge/collapse (data loss).
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk


def snap_to_integers(mode="selection"):
    """
    Snap fractional keys to whole frames using collision-aware rounding.
    
    Args:
        mode: "selection" (selected curves/keys) or "all" (all scene keys).
    """
    if mode == "selection":
        # Get all selected curves or curves of selected objects
        curves = cmds.keyframe(query=True, name=True, selected=True)
        if not curves:
            # Fallback to all animated channels on selected objects
            sel = cmds.ls(selection=True) or []
            if sel:
                curves = cmds.keyframe(sel, query=True, name=True)
    else:
        curves = cmds.ls(type="animCurve")

    if not curves:
        cmds.warning("AniRetime: No animation curves found to snap.")
        return

    snapped_count = 0
    with UndoChunk("AniKin: Snap Keys to Integers"):
        for curve in set(curves):
            # Query all keyframe times
            times = cmds.keyframe(curve, query=True, timeChange=True) or []
            if not times:
                continue

            # Need to process them sorted, keeping track of original indices
            # keyframe query returns them in order
            
            # Map of old_time -> new_time
            time_map = {}
            used_frames = set()
            
            for t in times:
                rounded = round(t)
                
                # Collision handling: if two fractional keys round to the same
                # integer frame, push the later one forward by 1 frame.
                while rounded in used_frames:
                    rounded += 1
                    
                used_frames.add(rounded)
                
                # Only edit if it actually moved
                if abs(t - rounded) > 0.001:
                    time_map[t] = rounded
            
            # Apply edits back to the curve
            # Process in reverse order to avoid shifting keys over each other during edit
            for old_time in sorted(time_map.keys(), reverse=True):
                new_time = time_map[old_time]
                cmds.keyframe(curve, edit=True, time=(old_time, old_time), timeChange=new_time)
                snapped_count += 1

    cmds.inViewMessage(
        amg="<hl>AniRetime</hl>: Snapped {} keys to whole frames.".format(snapped_count),
        pos="topCenter", fade=True, fadeStayTime=2000
    )


def retime_range(scale_factor, pivot_mode="start", snap=True):
    """
    Scale selected animation keys and optionally snap them to whole frames.
    
    Args:
        scale_factor: Multiplier (e.g., 2.0 = double length/slowmo, 0.5 = double speed).
        pivot_mode:   "start" (scale from first key), "end" (scale from last key).
        snap:         Whether to run the collision-aware snap pass after scaling.
    """
    curves = cmds.keyframe(query=True, name=True, selected=True)
    if not curves:
        sel = cmds.ls(selection=True) or []
        if sel:
            curves = cmds.keyframe(sel, query=True, name=True)
            
    if not curves:
        cmds.warning("AniRetime: Select animated objects or keys to retime.")
        return

    with UndoChunk("AniKin: Retime Animation (x{})".format(scale_factor)):
        for curve in set(curves):
            times = cmds.keyframe(curve, query=True, timeChange=True) or []
            if not times:
                continue
                
            start_time = min(times)
            end_time = max(times)
            
            pivot = start_time if pivot_mode == "start" else end_time
            
            # Pass 1: Native Maya scale (handles tangents and value scaling natively)
            # We only scale time, not value
            cmds.scaleKey(curve, time=(start_time, end_time), timeScale=scale_factor, timePivot=pivot)
            
        # Pass 2: Snap leftovers to integers
        if snap:
            # We have to run snap over the scaled curves
            snap_to_integers(mode="selection")

    cmds.inViewMessage(
        amg="<hl>AniRetime</hl>: Animation scaled by {:.2f}x".format(scale_factor),
        pos="topCenter", fade=True, fadeStayTime=2000
    )
