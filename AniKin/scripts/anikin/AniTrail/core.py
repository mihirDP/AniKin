"""
AniTrail — Editable Motion Trails (productized wrapper around Maya's motionTrail node).

This is NOT a custom manipulator — Maya's native editable motion trail already
lets animators drag vertices to edit keyframes in the viewport.  AniTrail adds:

  1. One-click creation from selection, auto-scoped to the keyframe range.
  2. Batch creation across entire selection sets with per-node color coding.
  3. Style presets — increment, pre/post frame trim, past/future/both modes.
  4. Auto-cleanup on tool close / scene save to prevent outliner pollution.
  5. Toggle sync with AniGhost so both systems don't visually collide.
  6. Registry tracking so trails are idempotent (no duplicates on re-click).
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2
from anikin.core.undo import UndoChunk

# ── Module-level registry ──────────────────────────────────────────────────────
# Maps {source_node_long_name: {"trail": trailNodeName, "handle": handleTransformName}}
_TRAIL_REGISTRY = {}

# Scene-save callback ID — registered lazily on first trail creation
_SAVE_CALLBACK_ID = None


# ── Public API ────────────────────────────────────────────────────────────────

def create_trail(increment=1, pre_frames=None, post_frames=None,
                 color=None, show_frames=True, thickness=2.0):
    """
    Create editable motion trails for selected objects.

    Args:
        increment:   Trail point density (1 = every frame, 2 = every other, etc.)
        pre_frames:  Frames before current to show trail (None = full range start)
        post_frames: Frames after current to show trail (None = full range end)
        color:       (r, g, b) float tuple for trail color
        show_frames: Show frame numbers along trail
        thickness:   Trail line width
    """
    sel = cmds.ls(selection=True, long=True) or []
    if not sel:
        cmds.warning("AniTrail: Select objects to create motion trails.")
        return

    _ensure_save_callback()

    created = 0
    with UndoChunk("AniKin: Create Editable Trail"):
        for obj in sel:
            # Idempotent — skip if trail already exists for this object
            if obj in _TRAIL_REGISTRY:
                entry = _TRAIL_REGISTRY[obj]
                if cmds.objExists(entry.get("handle", "")):
                    continue
                else:
                    # Stale entry — clean it up
                    del _TRAIL_REGISTRY[obj]

            # Determine frame range
            start, end = _get_trail_range(obj, pre_frames, post_frames)

            try:
                result = cmds.snapshot(
                    obj,
                    motionTrail=True,
                    startTime=start,
                    endTime=end,
                    increment=increment,
                    constructionHistory=True,
                )
            except Exception as exc:
                cmds.warning("AniTrail: Failed on '{}' — {}".format(
                    obj.split("|")[-1], exc))
                continue

            if not result or len(result) < 2:
                continue

            handle_node = result[1]

            # Style the trail shape
            shapes = cmds.listRelatives(handle_node, shapes=True) or []
            if shapes:
                shape = shapes[0]
                _style_trail(shape, color=color, show_frames=show_frames,
                             thickness=thickness)

            # Register
            _TRAIL_REGISTRY[obj] = {
                "trail": result[0] if len(result) > 0 else "",
                "handle": handle_node,
            }
            created += 1

    if created:
        cmds.inViewMessage(
            amg="<hl>AniTrail</hl>: Created {} editable trail(s)".format(created),
            pos="topCenter", fade=True, fadeStayTime=1200
        )


def remove_trail():
    """Remove motion trails for selected objects (or all if nothing selected)."""
    sel = cmds.ls(selection=True, long=True) or []

    with UndoChunk("AniKin: Remove Trail"):
        if sel:
            for obj in sel:
                _delete_trail_for(obj)
        else:
            # No selection — clear all registered trails
            for obj in list(_TRAIL_REGISTRY.keys()):
                _delete_trail_for(obj)

    cmds.inViewMessage(
        amg="<hl>AniTrail</hl>: Trails removed",
        pos="topCenter", fade=True, fadeStayTime=1000
    )


def clear_all():
    """Nuclear option — delete ALL trail nodes in the scene, registered or not."""
    with UndoChunk("AniKin: Clear All Trails"):
        # Clear registry first
        _TRAIL_REGISTRY.clear()

        # Then find and delete every motionTrail + snapshot node in the scene
        for node_type in ["motionTrailShape", "motionTrail", "snapshot"]:
            nodes = cmds.ls(type=node_type) or []
            for n in nodes:
                # Get parent transforms of shapes
                if node_type == "motionTrailShape":
                    parents = cmds.listRelatives(n, parent=True) or []
                    for p in parents:
                        if cmds.objExists(p):
                            cmds.delete(p)
                if cmds.objExists(n):
                    cmds.delete(n)

    cmds.inViewMessage(
        amg="<hl>AniTrail</hl>: All scene trails cleared",
        pos="topCenter", fade=True, fadeStayTime=1000
    )


def toggle_trail(increment=1, color=None, show_frames=True, thickness=2.0):
    """
    Toggle: if any selected object already has a trail, remove it.
    Otherwise create one.
    """
    sel = cmds.ls(selection=True, long=True) or []
    if not sel:
        cmds.warning("AniTrail: Select objects to toggle trail.")
        return

    has_trail = any(
        obj in _TRAIL_REGISTRY and cmds.objExists(_TRAIL_REGISTRY[obj].get("handle", ""))
        for obj in sel
    )

    if has_trail:
        remove_trail()
    else:
        create_trail(increment=increment, color=color,
                     show_frames=show_frames, thickness=thickness)


def set_trail_mode(mode="both"):
    """
    Change what portion of the trail is visible for selected objects.

    Args:
        mode: "past" | "future" | "both"
    """
    sel = cmds.ls(selection=True, long=True) or []
    current_time = cmds.currentTime(q=True)

    for obj in sel:
        entry = _TRAIL_REGISTRY.get(obj)
        if not entry:
            continue
        handle = entry.get("handle", "")
        if not cmds.objExists(handle):
            continue

        shapes = cmds.listRelatives(handle, shapes=True) or []
        if not shapes:
            continue

        # We control visibility via startTime/endTime on the snapshot node
        trail_node = entry.get("trail", "")
        if not cmds.objExists(trail_node):
            continue

        start_min = cmds.playbackOptions(q=True, minTime=True)
        end_max = cmds.playbackOptions(q=True, maxTime=True)

        if mode == "past":
            cmds.setAttr("{}.startTime".format(trail_node), start_min)
            cmds.setAttr("{}.endTime".format(trail_node), current_time)
        elif mode == "future":
            cmds.setAttr("{}.startTime".format(trail_node), current_time)
            cmds.setAttr("{}.endTime".format(trail_node), end_max)
        else:  # "both"
            cmds.setAttr("{}.startTime".format(trail_node), start_min)
            cmds.setAttr("{}.endTime".format(trail_node), end_max)


def configure_trail(increment=None, color=None, show_frames=None, thickness=None):
    """Update visual style on all existing registered trails."""
    for obj, entry in _TRAIL_REGISTRY.items():
        handle = entry.get("handle", "")
        if not cmds.objExists(handle):
            continue
        shapes = cmds.listRelatives(handle, shapes=True) or []
        if shapes:
            _style_trail(shapes[0], color=color, show_frames=show_frames,
                         thickness=thickness)


def get_trail_count():
    """Return number of active trails (for UI display)."""
    count = 0
    for obj, entry in list(_TRAIL_REGISTRY.items()):
        if cmds.objExists(entry.get("handle", "")):
            count += 1
        else:
            del _TRAIL_REGISTRY[obj]
    return count


# ── Private helpers ────────────────────────────────────────────────────────────

def _get_trail_range(obj, pre_frames, post_frames):
    """
    Determine the frame range for the trail.
    If pre/post frames are None, use the object's own keyframe range
    (better than the full playback range — scoped to the animation).
    Falls back to playback range if no keys exist.
    """
    obj_keys = cmds.keyframe(obj, q=True, timeChange=True) or []

    if obj_keys:
        key_start = min(obj_keys)
        key_end = max(obj_keys)
    else:
        key_start = cmds.playbackOptions(q=True, minTime=True)
        key_end = cmds.playbackOptions(q=True, maxTime=True)

    if pre_frames is not None:
        current = cmds.currentTime(q=True)
        start = current - pre_frames
    else:
        start = key_start

    if post_frames is not None:
        current = cmds.currentTime(q=True)
        end = current + post_frames
    else:
        end = key_end

    return start, end


def _style_trail(shape_node, color=None, show_frames=None, thickness=None):
    """Apply visual styling to a motionTrailShape node."""
    try:
        if color is not None:
            cmds.setAttr("{}.trailColor".format(shape_node),
                         color[0], color[1], color[2], type="double3")
        if show_frames is not None:
            cmds.setAttr("{}.showFrames".format(shape_node), show_frames)
        if thickness is not None:
            cmds.setAttr("{}.trailThickness".format(shape_node), thickness)
    except Exception:
        pass


def _delete_trail_for(obj):
    """Delete trail nodes for a specific object and remove from registry."""
    entry = _TRAIL_REGISTRY.pop(obj, None)
    if entry is None:
        return

    for key in ["handle", "trail"]:
        node = entry.get(key, "")
        if node and cmds.objExists(node):
            try:
                cmds.delete(node)
            except Exception:
                pass


def _on_scene_save(*args, **kwargs):
    """
    Callback fired before scene save.
    Purges all trail nodes from the scene so they don't pollute saved files.
    Studios hate leftover snapshot groups in their outliner.
    """
    for obj in list(_TRAIL_REGISTRY.keys()):
        _delete_trail_for(obj)
    _TRAIL_REGISTRY.clear()


def _ensure_save_callback():
    """Register the before-save callback exactly once."""
    global _SAVE_CALLBACK_ID
    if _SAVE_CALLBACK_ID is not None:
        return
    try:
        _SAVE_CALLBACK_ID = om2.MSceneMessage.addCallback(
            om2.MSceneMessage.kBeforeSave, _on_scene_save
        )
    except Exception:
        pass


def cleanup_callbacks():
    """Remove any registered callbacks (call on plugin unload)."""
    global _SAVE_CALLBACK_ID
    if _SAVE_CALLBACK_ID is not None:
        try:
            om2.MMessage.removeCallback(_SAVE_CALLBACK_ID)
        except Exception:
            pass
        _SAVE_CALLBACK_ID = None
