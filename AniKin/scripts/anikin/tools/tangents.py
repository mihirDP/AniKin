"""
tangents.py
Tangent Shortcuts — one-click tangent type application.

Applies tangent types (auto, flat, linear, step, spline) to selected
keyframes in the Graph Editor, or to all keyframes of selected objects
if nothing is selected in the Graph Editor.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk


# Valid tangent types in Maya
TANGENT_TYPES = {
    "auto": "auto",
    "flat": "flat",
    "linear": "linear",
    "step": "step",
    "spline": "spline",
    "clamped": "clamped",
    "plateau": "plateau",
}


def set_tangent(tangent_type="auto"):
    """
    Set the in/out tangent type on selected keys or selected objects' keys.

    Args:
        tangent_type: One of 'auto', 'flat', 'linear', 'step', 'spline',
                      'clamped', 'plateau'.
    """
    maya_type = TANGENT_TYPES.get(tangent_type.lower())
    if maya_type is None:
        cmds.warning("AniKin: Unknown tangent type '{}'. Use one of: {}".format(
            tangent_type, ", ".join(TANGENT_TYPES.keys())
        ))
        return

    with UndoChunk("AniKin: Set Tangent ({})".format(maya_type)):
        # Try Graph Editor selection first
        graph_sel = cmds.keyframe(query=True, selected=True, name=True) or []
        if graph_sel:
            # Apply to specifically selected keyframes
            cmds.keyTangent(inTangentType=maya_type, outTangentType=maya_type)
        else:
            # Apply to all keys on selected objects
            sel = cmds.ls(selection=True) or []
            if not sel:
                cmds.warning("AniKin: Select objects or keyframes first.")
                return
            for node in sel:
                cmds.keyTangent(node, inTangentType=maya_type,
                                outTangentType=maya_type)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Tangent → {}".format(maya_type.capitalize()),
        pos="topCenter", fade=True, fadeStayTime=1000
    )
