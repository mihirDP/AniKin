"""
AniCleanup.py
Auto Curve Cleanup — removes redundant keyframes while preserving curve shape.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.log import log_debug


def _get_animated_plugs(nodes):
    """Retrieve all animated plugs on the specified nodes."""
    plugs = []
    for node in nodes:
        conns = cmds.listConnections(node, type="animCurve", plugs=False,
                                     connections=True, destination=False) or []
        for i in range(0, len(conns), 2):
            plugs.append(conns[i])
    return list(set(plugs))


def _cleanup_plug(plug, tolerance, preview_only):
    """
    Remove redundant keys on a plug within the specified tolerance.
    Returns the list of removed key times.
    """
    times = cmds.keyframe(plug, query=True, timeChange=True) or []
    if len(times) < 3:
        return []

    # Get values to ensure we can check exact values
    values = cmds.keyframe(plug, query=True, valueChange=True) or []
    
    removed_times = []
    
    # We iterate backwards through times[1:-1] so that removing keys
    # doesn't mess up earlier indices, or we can just capture their state first.
    # Note: If we remove a key, the curve shape changes slightly. So we check
    # one key at a time.
    i = len(times) - 2
    while i >= 1:
        t = times[i]
        stored_val = values[i]
        
        # Query tangent properties to restore if not redundant
        in_ang = cmds.keyTangent(plug, time=(t, t), query=True, inAngle=True)[0]
        out_ang = cmds.keyTangent(plug, time=(t, t), query=True, outAngle=True)[0]
        in_type = cmds.keyTangent(plug, time=(t, t), query=True, inTangentType=True)[0]
        out_type = cmds.keyTangent(plug, time=(t, t), query=True, outTangentType=True)[0]
        w_lock = cmds.keyTangent(plug, time=(t, t), query=True, weightLock=True)[0]

        # Temporarily cut key
        cmds.cutKey(plug, time=(t, t), clear=True)
        
        # Sample value without this key
        interpolated_val = cmds.getAttr(plug, time=t)
        
        if abs(interpolated_val - stored_val) < tolerance:
            # Redundant! Keep it removed
            removed_times.append(t)
            if preview_only:
                # Restore since it's just a preview
                cmds.setKeyframe(plug, time=t, value=stored_val)
                cmds.keyTangent(plug, time=(t, t), inAngle=in_ang, outAngle=out_ang,
                                inTangentType=in_type, outTangentType=out_type, weightLock=w_lock)
        else:
            # Not redundant, restore it exactly
            cmds.setKeyframe(plug, time=t, value=stored_val)
            cmds.keyTangent(plug, time=(t, t), inAngle=in_ang, outAngle=out_ang,
                            inTangentType=in_type, outTangentType=out_type, weightLock=w_lock)
            
        i -= 1

    return sorted(removed_times)


def execute(tolerance=0.001, preview_only=False):
    """
    Remove redundant keys on animated channels of selected objects.
    
    Args:
        tolerance: Float tolerance. Keys that differ from the interpolated curve by less than this are removed.
        preview_only: If True, returns count and lists without actual deletion.
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return 0

    plugs = _get_animated_plugs(sel)
    if not plugs:
        cmds.warning("AniCleanup: No animated curves found on selection.")
        return 0

    total_removed = 0
    removed_log = {}

    with UndoChunk("AniKin: Auto Curve Cleanup"):
        for plug in plugs:
            removed = _cleanup_plug(plug, tolerance, preview_only)
            if removed:
                removed_log[plug] = removed
                total_removed += len(removed)

    if preview_only:
        msg = "Cleanup Preview: {} redundant keys detected".format(total_removed)
    else:
        msg = "Cleanup Complete: Removed {} redundant keys".format(total_removed)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: {}".format(msg),
        pos="topCenter", fade=True, fadeStayTime=1500
    )
    print("[AniKin] " + msg)
    return total_removed
