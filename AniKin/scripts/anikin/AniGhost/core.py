"""
AniGhost.py
Ghosting â€” wraps Maya's native ghosting features (Tier 1 MVP).

Provides:
- toggle_ghosting(): Toggles native ghosting on selected objects.
- clear_all(): Unghosts all objects globally.
- configure_ghosting(): Adjusts global pre/post frames and step size.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk


def is_ghosted(obj):
    """Check if an object is currently marked for AniGhost."""
    ghosted = cmds.ghosting(query=True, ghostedObjects=True) or []
    obj_long = cmds.ls(obj, long=True)[0]
    for g in ghosted:
        g_long = cmds.ls(g, long=True)
        if g_long and g_long[0] == obj_long:
            return True
    return False


def toggle_ghosting():
    """Toggle native ghosting on selected objects."""
    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select objects to toggle AniGhost.")
        return

    with UndoChunk("AniKin: Toggle Ghosting"):
        for obj in sel:
            if is_ghosted(obj):
                cmds.ghosting(obj, action="unghost")
                cmds.inViewMessage(
                    amg="<hl>AniKin</hl>: Unghosted {}".format(obj.split("|")[-1]),
                    pos="topCenter", fade=True, fadeStayTime=1000
                )
            else:
                cmds.ghosting(obj, action="ghost")
                cmds.inViewMessage(
                    amg="<hl>AniKin</hl>: Ghosted {}".format(obj.split("|")[-1]),
                    pos="topCenter", fade=True, fadeStayTime=1000
                )


def clear_all():
    """Unghost all objects in the scene."""
    with UndoChunk("AniKin: Clear All Ghosting"):
        cmds.ghosting(action="unghostAll")
    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Cleared all ghosting in scene",
        pos="topCenter", fade=True, fadeStayTime=1000
    )


def configure_ghosting(pre_frames=5, post_frames=5, step=1):
    """
    Set the global ghosting options.
    """
    with UndoChunk("AniKin: Configure Ghosting"):
        # Apply the parameters to the global ghosting system
        cmds.ghosting(preFrames=pre_frames, postFrames=post_frames, ghostsStep=step)
        
    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Ghost settings set to Pre: {}, Post: {}, Step: {}".format(
            pre_frames, post_frames, step
        ),
        pos="topCenter", fade=True, fadeStayTime=1500
    )

