"""
AniRootMotion.py
Root Motion Inspector — analyzes root bone motion for pipeline and game engine compliance.
"""

import maya.cmds as cmds
import math
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.log import log_debug


def get_world_pos_at_frame(node, frame):
    """Get world-space translation at a specific frame."""
    try:
        matrix = cmds.getAttr("{}.worldMatrix".format(node), time=frame)
        if matrix and len(matrix) >= 16:
            return [matrix[12], matrix[13], matrix[14]]
    except Exception:
        pass
    
    # Fallback
    orig_time = cmds.currentTime(query=True)
    try:
        cmds.currentTime(frame)
        return cmds.xform(node, query=True, worldSpace=True, translation=True)
    finally:
        cmds.currentTime(orig_time)


def inspect_root_motion(root_node, start_frame, end_frame, expected_y=0.0, y_threshold=0.01, velocity_spike_threshold=2.0):
    """
    Inspects root motion for pipeline violations.
    
    Args:
        root_node: Name of the root joint/control.
        start_frame: Start of inspection range.
        end_frame: End of inspection range.
        expected_y: Expected Y coordinate of the root (usually 0.0 for ground alignment).
        y_threshold: Threshold to trigger warning for Y offset.
        velocity_spike_threshold: Distance threshold between consecutive frames to flag a spike.
        
    Returns:
        dict: Diagnostic results containing issues, average velocity, and loop status.
    """
    if not cmds.objExists(root_node):
        return {"error": "Node does not exist", "issues": []}

    issues = []
    velocities = []
    prev_pos = None
    y_violations = 0
    spike_frames = []

    for frame in range(int(start_frame), int(end_frame) + 1):
        pos = get_world_pos_at_frame(root_node, frame)
        if not pos:
            continue
        x, y, z = pos

        # 1. Non-zero Y Check
        if abs(y - expected_y) > y_threshold:
            y_violations += 1

        # 2. Velocity spike check
        if prev_pos is not None:
            dx = x - prev_pos[0]
            dy = y - prev_pos[1]
            dz = z - prev_pos[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            velocities.append(dist)

            if dist > velocity_spike_threshold:
                spike_frames.append((frame - 1, frame, dist))
        
        prev_pos = (x, y, z)

    # Compile issues list
    if y_violations > 0:
        issues.append({
            "severity": "WARNING",
            "category": "Root Y Offset",
            "message": "Root Y is non-zero (expected {}) on {}/{} frames.".format(expected_y, y_violations, int(end_frame - start_frame + 1))
        })

    for f_start, f_end, dist in spike_frames:
        issues.append({
            "severity": "CRITICAL",
            "category": "Velocity Spike",
            "message": "Sudden root movement of {:.2f} units detected between frames {} and {}.".format(dist, f_start, f_end)
        })

    # 3. Loop point drift
    start_pos = get_world_pos_at_frame(root_node, start_frame)
    end_pos = get_world_pos_at_frame(root_node, end_frame)
    loop_drift_xz = 0.0
    if start_pos and end_pos:
        dx = end_pos[0] - start_pos[0]
        dz = end_pos[2] - start_pos[2]
        loop_drift_xz = math.sqrt(dx*dx + dz*dz)
        # Note: If it's a looping stationary animation (like idle), drift should be near 0
        if loop_drift_xz > 0.01:
            issues.append({
                "severity": "INFO",
                "category": "Loop Drift",
                "message": "XZ loop displacement is {:.3f} units (expected 0 for in-place cycles).".format(loop_drift_xz)
            })

    avg_vel = sum(velocities) / len(velocities) if velocities else 0.0

    return {
        "issues": issues,
        "avg_velocity": avg_vel,
        "loop_drift_xz": loop_drift_xz,
        "max_velocity": max(velocities) if velocities else 0.0
    }
