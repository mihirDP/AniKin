"""
AniGround.py
Ground Tool — drops selected objects to Maya's world ground plane (Y=0).

Supports:
- Grounding each object individually.
- Grounding all objects to the last selected object's ground (keeping relative offsets).
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn


def get_world_ymin(node):
    """Retrieve the minimum world Y coordinate of the object's bounding box."""
    try:
        bbox = cmds.exactWorldBoundingBox(node, calculateExactly=True)
        return bbox[1]
    except Exception:
        try:
            bbox = cmds.xform(node, query=True, worldSpace=True, boundingBox=True)
            return bbox[1]
        except Exception:
            # Fallback to world translation (pivot)
            return cmds.xform(node, query=True, worldSpace=True, translation=True)[1]


def ground_objects(mode="individual"):
    """
    Ground selected objects.
    
    Args:
        mode: "individual" to ground each object relative to its own bounding box.
              "keep_offset" to ground all objects based on the last selected object's ground height.
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return

    with UndoChunk("AniKin: Ground Objects"):
        if mode == "keep_offset" and len(sel) > 1:
            target = sel[-1]
            ymin = get_world_ymin(target)
            delta_y = -ymin
            
            # Ground all of them by the same delta
            for node in sel:
                # We move relative to keep offsets
                cmds.move(0, delta_y, 0, node, relative=True, worldSpace=True)
        else:
            # Individual mode
            for node in sel:
                ymin = get_world_ymin(node)
                delta_y = -ymin
                cmds.move(0, delta_y, 0, node, relative=True, worldSpace=True)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Grounded {} object(s) (mode: {})".format(len(sel), mode),
        pos="topCenter", fade=True, fadeStayTime=1500
    )
