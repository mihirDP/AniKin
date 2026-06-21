"""
AniBake.py
Smart Bake â€” bake to world-space locator and back.

Two-step workflow:
1. bake_to_locator(): Creates a world-space locator, constrains it to
   the selected object, bakes the locator, then deletes the constraint.
   The locator now holds the world-space animation.
2. bake_from_locator(): Constrains the original object to the baked
   locator, bakes the object, then cleans up.

This is essential for:
- Extracting world-space motion from a constrained/parented rig control
- Re-targeting animation between rigs
- Fixing counter-animation issues
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected


def _get_bake_range():
    """Return the playback range as (start, end) floats."""
    start = cmds.playbackOptions(query=True, minTime=True)
    end = cmds.playbackOptions(query=True, maxTime=True)
    return start, end


def bake_to_locator():
    """
    Create a world-space locator that captures the selected object's
    world-space animation across the playback range.
    """
    try:
        sel = get_selected(min_count=1, max_count=1,
                           error_msg="Smart Bake: Select exactly 1 object.")
    except RuntimeError:
        return None

    source = sel[0]
    short_name = source.split("|")[-1].split(":")[-1]
    start, end = _get_bake_range()

    with UndoChunk("AniKin: Smart Bake â†’ Locator"):
        # Create the locator
        loc = cmds.spaceLocator(name="{}_AF_bake_loc".format(short_name))[0]

        # Parent-constrain locator to source (locator follows source)
        pc = cmds.parentConstraint(source, loc, maintainOffset=False)[0]

        # Bake the locator across the playback range
        cmds.bakeResults(
            loc,
            time=(start, end),
            simulation=True,
            sampleBy=1,
            oversamplingRate=1,
            disableImplicitControl=True,
            preserveOutsideKeys=True,
            sparseAnimCurveBake=False,
            removeBakedAttributeFromLayer=False,
            bakeOnOverrideLayer=False,
            minimizeRotation=True,
        )

        # Delete the constraint (locator is now freestanding with keys)
        cmds.delete(pc)

        # Select the locator so user can see it
        cmds.select(loc)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Baked world-space to '{}'".format(loc),
        pos="topCenter", fade=True, fadeStayTime=2000
    )
    return loc


def bake_from_locator():
    """
    Bake animation from an AniKin locator back onto the original object.
    Select the target object first, then the locator.
    """
    try:
        sel = get_selected(min_count=2, max_count=2,
                           error_msg="Smart Bake Back: Select target object, "
                                     "then the bake locator.")
    except RuntimeError:
        return

    target = sel[0]
    locator = sel[1]
    start, end = _get_bake_range()

    with UndoChunk("AniKin: Smart Bake â† Locator"):
        # Constrain target to locator
        pc = cmds.parentConstraint(locator, target, maintainOffset=False)[0]

        # Bake the target
        cmds.bakeResults(
            target,
            time=(start, end),
            simulation=True,
            sampleBy=1,
            oversamplingRate=1,
            disableImplicitControl=True,
            preserveOutsideKeys=True,
            sparseAnimCurveBake=False,
            removeBakedAttributeFromLayer=False,
            bakeOnOverrideLayer=False,
            minimizeRotation=True,
        )

        # Delete the constraint
        cmds.delete(pc)

        # Optionally delete the locator
        cmds.delete(locator)

        # Select the target
        cmds.select(target)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Baked back from locator to '{}'".format(target),
        pos="topCenter", fade=True, fadeStayTime=2000
    )

