"""
align.py
Align Tool — matches translation/rotation of selected objects.

Select two or more objects: all selected objects (except the last)
will be aligned to the LAST selected object's world-space transform.

This is the simplest tool and a good warm-up for the architecture.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected


def align_translation(source, target):
    """Copy world-space translation from target to source."""
    pos = cmds.xform(target, query=True, worldSpace=True, translation=True)
    cmds.xform(source, worldSpace=True, translation=pos)


def align_rotation(source, target):
    """Copy world-space rotation from target to source."""
    rot = cmds.xform(target, query=True, worldSpace=True, rotation=True)
    cmds.xform(source, worldSpace=True, rotation=rot)


def align_all(source, target):
    """Copy both translation and rotation from target to source."""
    align_translation(source, target)
    align_rotation(source, target)


def execute(translate=True, rotate=True):
    """
    Align all selected objects to the last selected object.

    Args:
        translate: If True, match translation.
        rotate: If True, match rotation.
    """
    try:
        sel = get_selected(min_count=2,
                           error_msg="Align: Select at least 2 objects (sources → target).")
    except RuntimeError:
        return

    target = sel[-1]
    sources = sel[:-1]

    with UndoChunk("AniKin: Align Objects"):
        for src in sources:
            if translate and rotate:
                align_all(src, target)
            elif translate:
                align_translation(src, target)
            elif rotate:
                align_rotation(src, target)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Aligned {} object(s) to {}".format(len(sources), target),
        pos="topCenter", fade=True, fadeStayTime=1500
    )
