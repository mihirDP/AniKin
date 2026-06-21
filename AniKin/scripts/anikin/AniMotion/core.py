"""
AniMotion.py
Motion Trail â€” wraps Maya's native motionTrail/snapshot system.

Provides:
- toggle_motion_trail(): Toggles a motion trail for selected object(s).
- clear_all(): Deletes all motion trails in the scene.
- configure_trail(): Sets visual attributes of selected motion trails.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk


def get_motion_trail_for_object(obj):
    """
    Find any motion trail nodes associated with the given object.
    Returns (trail_node, handle_node) or (None, None).
    """
    # Look for connections of type 'snapshot' or 'motionTrail'
    connections = cmds.listConnections(obj, source=False, destination=True) or []
    for node in connections:
        node_type = cmds.nodeType(node)
        if node_type in ["snapshot", "motionTrail"]:
            # Find the handle node (transform) connected to this trail node
            outputs = cmds.listConnections(node, source=False, destination=True) or []
            for out in outputs:
                if cmds.nodeType(out) == "motionTrailShape":
                    parent = cmds.listRelatives(out, parent=True)
                    if parent:
                        return node, parent[0]
                elif "motionTrail" in out and cmds.nodeType(out) == "transform":
                    return node, out
    return None, None


def toggle_motion_trail(pre_color=(0.0, 0.7, 0.85), key_color=(1.0, 0.5, 0.0), thickness=2.0, show_frames=True):
    """
    Toggle motion trail on/off for selected object(s).
    """
    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select an object to toggle motion trail.")
        return

    with UndoChunk("AniKin: Toggle Motion Trail"):
        for obj in sel:
            trail, handle = get_motion_trail_for_object(obj)
            if trail and handle:
                # Toggle off: delete the trail and its handle
                if cmds.objExists(trail):
                    cmds.delete(trail)
                if cmds.objExists(handle):
                    cmds.delete(handle)
                cmds.inViewMessage(
                    amg="<hl>AniKin</hl>: Removed motion trail for {}".format(obj.split("|")[-1]),
                    pos="topCenter", fade=True, fadeStayTime=1000
                )
            else:
                # Toggle on: create new motion trail
                start = cmds.playbackOptions(q=True, minTime=True)
                end = cmds.playbackOptions(q=True, maxTime=True)
                
                # Create the motion trail using snapshot
                # In modern Maya, cmds.snapshot(motionTrail=True) creates the editable motion trail
                res = cmds.snapshot(obj, motionTrail=True, startTime=start, endTime=end, increment=1, constructionHistory=True)
                if res:
                    handle_node = res[1]
                    shapes = cmds.listRelatives(handle_node, shapes=True) or []
                    if shapes:
                        shape = shapes[0]
                        try:
                            # Apply color tokens/customization
                            cmds.setAttr("{}.trailColor".format(shape), pre_color[0], pre_color[1], pre_color[2], type="double3")
                            cmds.setAttr("{}.keyframeColor".format(shape), key_color[0], key_color[1], key_color[2], type="double3")
                            cmds.setAttr("{}.showFrames".format(shape), show_frames)
                            cmds.setAttr("{}.trailThickness".format(shape), thickness)
                        except Exception:
                            pass
                            
                cmds.inViewMessage(
                    amg="<hl>AniKin</hl>: Created motion trail for {}".format(obj.split("|")[-1]),
                    pos="topCenter", fade=True, fadeStayTime=1000
                )


def clear_all():
    """Delete all motion trails in the scene."""
    # Find all motionTrail and snapshot nodes
    snapshots = cmds.ls(type="snapshot") or []
    trails = cmds.ls(type="motionTrail") or []
    shapes = cmds.ls(type="motionTrailShape") or []
    
    handles = []
    for s in shapes:
        parent = cmds.listRelatives(s, parent=True)
        if parent:
            handles.append(parent[0])

    with UndoChunk("AniKin: Clear All Motion Trails"):
        # Delete visual handles
        for h in list(set(handles)):
            if cmds.objExists(h):
                cmds.delete(h)
        # Delete evaluation nodes
        nodes_to_del = list(set(snapshots + trails))
        for n in nodes_to_del:
            if cmds.objExists(n):
                cmds.delete(n)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Cleared all motion trails in scene",
        pos="topCenter", fade=True, fadeStayTime=1000
    )

