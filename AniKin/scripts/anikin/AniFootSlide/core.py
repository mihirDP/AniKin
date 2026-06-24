"""
AniFootSlide.py
Foot Slide Detector — analyzes world-space translation of feet to identify drift.
"""

import maya.cmds as cmds
import math
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.log import log_debug


def get_world_pos_at_frame(node, frame):
    """Get the world space translation of a node at a specific frame using its worldMatrix attribute."""
    try:
        matrix = cmds.getAttr("{}.worldMatrix".format(node), time=frame)
        if matrix and len(matrix) >= 16:
            return [matrix[12], matrix[13], matrix[14]]
    except Exception:
        pass
    
    # Fallback by temporarily changing time (only if worldMatrix query fails)
    orig_time = cmds.currentTime(query=True)
    try:
        cmds.currentTime(frame)
        return cmds.xform(node, query=True, worldSpace=True, translation=True)
    finally:
        cmds.currentTime(orig_time)


def detect_foot_slide(foot_controls, start_frame, end_frame, slide_threshold=0.01, plant_y_threshold=0.05):
    """
    Analyze world space positions of foot controls to detect sliding.
    
    Args:
        foot_controls: List of control names.
        start_frame: Start frame of analysis.
        end_frame: End frame of analysis.
        slide_threshold: Max allowed XZ movement per frame before being flagged as slide.
        plant_y_threshold: Height (world Y) below which the foot is considered planted.
        
    Returns:
        dict: {control_name: [(start_frame, end_frame), ...]}
    """
    results = {}

    for ctrl in foot_controls:
        if not cmds.objExists(ctrl):
            continue

        slide_events = []
        prev_xz = None
        in_slide = False
        slide_start = None

        for frame in range(int(start_frame), int(end_frame) + 1):
            world_pos = get_world_pos_at_frame(ctrl, frame)
            if not world_pos:
                continue
            x, y, z = world_pos

            # Planted check: Y coordinate must be close to the ground plane
            is_planted = y < plant_y_threshold

            if is_planted and prev_xz is not None:
                dx = x - prev_xz[0]
                dz = z - prev_xz[1]
                dist = math.sqrt(dx * dx + dz * dz)

                if dist > slide_threshold:
                    if not in_slide:
                        in_slide = True
                        slide_start = frame
                else:
                    if in_slide:
                        slide_events.append((slide_start, frame - 1))
                        in_slide = False
            elif in_slide:
                slide_events.append((slide_start, frame - 1))
                in_slide = False

            if is_planted:
                prev_xz = (x, z)
            else:
                prev_xz = None

        if in_slide:
            slide_events.append((slide_start, int(end_frame)))

        if slide_events:
            results[ctrl] = slide_events

    return results


def fix_foot_slide(ctrl, slide_start, slide_end):
    """
    Fixes a slide event by snapping foot position to the position at the start of the slide.
    
    Args:
        ctrl: Foot control name.
        slide_start: Start frame of the slide.
        slide_end: End frame of the slide.
    """
    if not cmds.objExists(ctrl):
        return False

    with UndoChunk("AniKin: Fix Foot Slide"):
        # Get start position
        start_pos = get_world_pos_at_frame(ctrl, slide_start)
        if not start_pos:
            return False
            
        tx, ty, tz = start_pos
        orig_time = cmds.currentTime(query=True)
        try:
            for frame in range(int(slide_start), int(slide_end) + 1):
                cmds.currentTime(frame)
                cmds.move(tx, ty, tz, ctrl, absolute=True, worldSpace=True)
                cmds.setKeyframe(ctrl, at=["translateX", "translateY", "translateZ"])
        finally:
            cmds.currentTime(orig_time)
            
    return True
