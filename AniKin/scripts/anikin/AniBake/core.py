"""
AniBake.py — Smart Bake v2
World-space bake, Temp-Space protection, and Dynamic Micro-Pivots.

Core workflows:
  1. bake_to_locator / bake_from_locator — original Smart Bake (single object).
  2. temp_space_unlock / temp_space_relock — multi-object world-lock
     (protect extremities while editing parents).
  3. pivot_mode_start / pivot_mode_commit — rotate from an arbitrary point
     without changing the rig's native pivot.

All operations are Maya-undo-able via undoInfo chunks.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected

# ── Registry for Temp-Space locked controls ────────────────────────────────────
# {source_node: {"locator": locName, "constraint": pcName}}
_TEMP_SPACE_LOCKS = {}

# ── Registry for Pivot-Mode ───────────────────────────────────────────────────
# {source_node: {"locator": locName, "constraint": pcName}}
_PIVOT_MODE = {}


def _get_bake_range():
    """Return the playback range as (start, end) floats."""
    start = cmds.playbackOptions(query=True, minTime=True)
    end = cmds.playbackOptions(query=True, maxTime=True)
    return start, end


def _bake_node(node, start, end):
    """Shared bake utility — bakes a node across [start, end]."""
    cmds.bakeResults(
        node,
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


# ═══════════════════════════════════════════════════════════════════════════════
# § 1 — ORIGINAL SMART BAKE (single object bake to/from locator)
# ═══════════════════════════════════════════════════════════════════════════════

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

    with UndoChunk("AniKin: Smart Bake to Locator"):
        loc = cmds.spaceLocator(name="{}_AK_bake_loc".format(short_name))[0]
        pc = cmds.parentConstraint(source, loc, maintainOffset=False)[0]
        _bake_node(loc, start, end)
        cmds.delete(pc)
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

    with UndoChunk("AniKin: Smart Bake from Locator"):
        pc = cmds.parentConstraint(locator, target, maintainOffset=False)[0]
        _bake_node(target, start, end)
        cmds.delete(pc)
        cmds.delete(locator)
        cmds.select(target)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Baked back from locator to '{}'".format(target),
        pos="topCenter", fade=True, fadeStayTime=2000
    )


# ═══════════════════════════════════════════════════════════════════════════════
# § 2 — TEMP SPACE (world-lock multiple controls while editing parents)
# ═══════════════════════════════════════════════════════════════════════════════

def temp_space_unlock():
    """
    Phase A — "Unlock": For every selected control, bake its world-space
    motion onto a temporary locator, then constrain the control to follow
    the locator (so it stays world-locked while you edit its parents).

    Supports multi-selection — lock the hand, head, and prop all at once.
    """
    sel = cmds.ls(selection=True, long=True) or []
    if not sel:
        cmds.warning("AniBake Temp Space: Select controls to world-lock.")
        return

    start, end = _get_bake_range()
    locked = 0

    with UndoChunk("AniKin: Temp Space Unlock"):
        for source in sel:
            if source in _TEMP_SPACE_LOCKS:
                cmds.warning("AniBake: '{}' is already world-locked.".format(
                    source.split("|")[-1]))
                continue

            short = source.split("|")[-1].split(":")[-1]
            loc = cmds.spaceLocator(name="{}_AK_tempspace".format(short))[0]

            # Bake world-space onto the locator
            pc_capture = cmds.parentConstraint(source, loc, maintainOffset=False)[0]
            _bake_node(loc, start, end)
            cmds.delete(pc_capture)

            # Now constrain the source to follow the locator (world-lock it)
            pc_lock = cmds.parentConstraint(loc, source, maintainOffset=True)[0]

            _TEMP_SPACE_LOCKS[source] = {
                "locator": loc,
                "constraint": pc_lock,
            }
            locked += 1

            # Visual indicator — color the locator
            try:
                cmds.setAttr("{}.overrideEnabled".format(loc), 1)
                cmds.setAttr("{}.overrideColor".format(loc), 17)  # Yellow
            except Exception:
                pass

    if locked:
        cmds.inViewMessage(
            amg="<hl>AniBake</hl>: {} control(s) world-locked. Edit parents freely.".format(locked),
            pos="topCenter", fade=True, fadeStayTime=2500
        )


def temp_space_relock():
    """
    Phase C — "Relock": Bake the world-locked motion back onto each
    control's own channels (in the new parent space), then clean up
    all temp locators and constraints.

    Call this AFTER you've finished editing parents (e.g., rotating the torso).
    """
    if not _TEMP_SPACE_LOCKS:
        cmds.warning("AniBake Temp Space: No controls are currently world-locked.")
        return

    start, end = _get_bake_range()
    relocked = 0

    with UndoChunk("AniKin: Temp Space Relock"):
        for source, data in list(_TEMP_SPACE_LOCKS.items()):
            loc = data["locator"]
            pc = data["constraint"]

            # Bake the source (which is following the locator) back to its own keys
            _bake_node(source, start, end)

            # Clean up
            if cmds.objExists(pc):
                cmds.delete(pc)
            if cmds.objExists(loc):
                cmds.delete(loc)

            relocked += 1

        _TEMP_SPACE_LOCKS.clear()

    if relocked:
        cmds.inViewMessage(
            amg="<hl>AniBake</hl>: {} control(s) relocked to local space.".format(relocked),
            pos="topCenter", fade=True, fadeStayTime=2500
        )


def temp_space_cancel():
    """Cancel a temp-space operation without baking back — restore original state."""
    if not _TEMP_SPACE_LOCKS:
        return

    with UndoChunk("AniKin: Temp Space Cancel"):
        for source, data in list(_TEMP_SPACE_LOCKS.items()):
            pc = data["constraint"]
            loc = data["locator"]
            if cmds.objExists(pc):
                cmds.delete(pc)
            if cmds.objExists(loc):
                cmds.delete(loc)
        _TEMP_SPACE_LOCKS.clear()

    cmds.inViewMessage(
        amg="<hl>AniBake</hl>: Temp Space cancelled — original animation preserved.",
        pos="topCenter", fade=True, fadeStayTime=2000
    )


def get_locked_controls():
    """Return list of currently world-locked control names (for UI display)."""
    active = []
    for source in list(_TEMP_SPACE_LOCKS.keys()):
        if cmds.objExists(source):
            active.append(source.split("|")[-1])
        else:
            del _TEMP_SPACE_LOCKS[source]
    return active


# ═══════════════════════════════════════════════════════════════════════════════
# § 3 — DYNAMIC MICRO-PIVOTS (rotate from an arbitrary point in space)
# ═══════════════════════════════════════════════════════════════════════════════

def pivot_mode_start():
    """
    Enter Pivot Mode: place a temporary locator at the current selection's
    position (or at a snapped vertex if desired), then parent-constrain
    the control to follow it. The animator rotates the LOCATOR to rotate
    the control around the locator's position as the pivot point.

    The locator acts as the pivot — rotate it, and the control orbits.
    """
    sel = cmds.ls(selection=True, long=True) or []
    if not sel:
        cmds.warning("AniPivot: Select a control to enter pivot mode.")
        return

    if len(sel) > 1:
        cmds.warning("AniPivot: Select exactly 1 control for pivot mode.")
        return

    source = sel[0]
    if source in _PIVOT_MODE:
        cmds.warning("AniPivot: '{}' is already in pivot mode.".format(
            source.split("|")[-1]))
        return

    short = source.split("|")[-1].split(":")[-1]

    with UndoChunk("AniKin: Pivot Mode Start"):
        # Create pivot locator at the source's world position
        loc = cmds.spaceLocator(name="{}_AK_pivot".format(short))[0]

        # Position the locator at the source's world position
        ws_pos = cmds.xform(source, q=True, worldSpace=True, translation=True)
        cmds.xform(loc, worldSpace=True, translation=ws_pos)

        # Parent-constrain source to follow the locator (maintain offset)
        pc = cmds.parentConstraint(loc, source, maintainOffset=True)[0]

        _PIVOT_MODE[source] = {
            "locator": loc,
            "constraint": pc,
        }

        # Visual — make the pivot locator obvious
        try:
            cmds.setAttr("{}.overrideEnabled".format(loc), 1)
            cmds.setAttr("{}.overrideColor".format(loc), 13)  # Red
            cmds.setAttr("{}.localScaleX".format(loc), 3)
            cmds.setAttr("{}.localScaleY".format(loc), 3)
            cmds.setAttr("{}.localScaleZ".format(loc), 3)
        except Exception:
            pass

        # Select the locator so the animator can immediately rotate it
        cmds.select(loc)

    cmds.inViewMessage(
        amg="<hl>AniPivot</hl>: Pivot mode ON — rotate the red locator, then commit.",
        pos="topCenter", fade=True, fadeStayTime=3000
    )


def pivot_mode_commit():
    """
    Commit Pivot Mode: bake the resulting motion back onto the control's
    own channels for the current frame range, then delete the pivot locator.
    """
    if not _PIVOT_MODE:
        cmds.warning("AniPivot: No controls are in pivot mode.")
        return

    start, end = _get_bake_range()

    with UndoChunk("AniKin: Pivot Mode Commit"):
        for source, data in list(_PIVOT_MODE.items()):
            loc = data["locator"]
            pc = data["constraint"]

            # Bake the control
            _bake_node(source, start, end)

            # Clean up
            if cmds.objExists(pc):
                cmds.delete(pc)
            if cmds.objExists(loc):
                cmds.delete(loc)

        _PIVOT_MODE.clear()

    cmds.inViewMessage(
        amg="<hl>AniPivot</hl>: Pivot committed — motion baked to control.",
        pos="topCenter", fade=True, fadeStayTime=2000
    )


def pivot_mode_cancel():
    """Cancel pivot mode without baking — restores original state."""
    if not _PIVOT_MODE:
        return

    with UndoChunk("AniKin: Pivot Mode Cancel"):
        for source, data in list(_PIVOT_MODE.items()):
            if cmds.objExists(data["constraint"]):
                cmds.delete(data["constraint"])
            if cmds.objExists(data["locator"]):
                cmds.delete(data["locator"])
        _PIVOT_MODE.clear()

    cmds.inViewMessage(
        amg="<hl>AniPivot</hl>: Pivot mode cancelled.",
        pos="topCenter", fade=True, fadeStayTime=1500
    )


