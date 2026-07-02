"""
AniCamLock — Viewport Camera Lock-to-Object
============================================

Locks the active **viewport** camera to follow a selected object during
animation playback.  Only the viewport's *modelPanel* look-through is
changed — no scene cameras are created or modified.

Usage:
    from anikin import AniCamLock
    AniCamLock.toggle()       # Toggle lock / unlock
    AniCamLock.is_locked()    # Query state

How it works:
    On **lock**:
    1. The current viewport camera & its transform are stored.
    2. A ``scriptJob`` (``timeChanged`` event) is created that, on every
       frame change, moves/aims the viewport camera to track the target
       object's world-space position while preserving the camera's relative
       offset from the target.
    On **unlock**:
    3. The scriptJob is killed.
    4. The viewport camera is restored to its pre-lock position/orientation.

Design decision: We manipulate the *existing* viewport camera rather than
creating a temporary one to avoid cluttering the Outliner and to keep the
user's perspective view completely intact after unlock.
"""

import maya.cmds as cmds
from anikin.core.log import log

# ── Module state ──────────────────────────────────────────
_state = {
    "locked": False,
    "target": None,
    "script_job_id": None,
    "panel": None,
    "camera": None,
    "camera_shape": None,
    # Stored pre-lock camera transform so we can restore it on unlock
    "saved_translate": None,
    "saved_rotate": None,
    # The offset between the camera and target at lock time
    "offset_translate": None,
    "offset_rotate": None,
}


def is_locked():
    """Return True if cam-lock is currently active."""
    return _state["locked"]


def toggle():
    """Toggle cam-lock on the current selection / active lock."""
    if _state["locked"]:
        unlock()
    else:
        lock()


def lock():
    """
    Lock the viewport camera to follow the first selected object.

    The camera maintains its current offset relative to the target
    so it doesn't jump to a weird position on frame change.
    """
    sel = cmds.ls(selection=True, long=True)
    if not sel:
        cmds.inViewMessage(
            amg="<hl>AniCamLock</hl>: Select an object to lock the viewport camera to.",
            pos="topCenter", fade=True, fadeStayTime=2000
        )
        return False

    target = sel[0]

    # Get the active model panel and its camera
    panel = _get_active_model_panel()
    if panel is None:
        cmds.warning("AniCamLock: No active 3D viewport found.")
        return False

    camera_shape = cmds.modelPanel(panel, query=True, camera=True)
    # camera_shape might be transform or shape — normalise to transform
    if cmds.objectType(camera_shape) == "camera":
        camera = cmds.listRelatives(camera_shape, parent=True, fullPath=True)[0]
    else:
        camera = camera_shape
        shapes = cmds.listRelatives(camera, shapes=True, fullPath=True, type="camera")
        camera_shape = shapes[0] if shapes else camera

    # Save current camera transform for restoring later
    saved_t = cmds.xform(camera, query=True, worldSpace=True, translation=True)
    saved_r = cmds.xform(camera, query=True, worldSpace=True, rotation=True)

    # Compute offset between camera and target at lock time
    target_t = cmds.xform(target, query=True, worldSpace=True,
                          rotatePivot=True)
    offset_t = [saved_t[i] - target_t[i] for i in range(3)]

    _state.update({
        "locked": True,
        "target": target,
        "panel": panel,
        "camera": camera,
        "camera_shape": camera_shape,
        "saved_translate": saved_t,
        "saved_rotate": saved_r,
        "offset_translate": offset_t,
        "offset_rotate": list(saved_r),
    })

    # Create scriptJob so camera tracks target on every frame change
    job_id = cmds.scriptJob(event=["timeChanged", _on_frame_changed])
    _state["script_job_id"] = job_id

    # Apply once immediately so the user sees the lock take effect
    _on_frame_changed()

    log("CamLock ON → tracking '{}'".format(target.split("|")[-1]))
    cmds.inViewMessage(
        amg="<hl>CamLock ON</hl>  —  tracking <hl>{}</hl>".format(
            target.split("|")[-1]
        ),
        pos="topCenter", fade=True, fadeStayTime=2000
    )
    return True


def unlock():
    """Unlock the viewport camera and restore its pre-lock position."""
    # Kill the scriptJob
    job_id = _state.get("script_job_id")
    if job_id is not None:
        try:
            if cmds.scriptJob(exists=job_id):
                cmds.scriptJob(kill=job_id, force=True)
        except Exception:
            pass

    # Restore camera position
    cam = _state.get("camera")
    if cam and cmds.objExists(cam):
        saved_t = _state.get("saved_translate")
        saved_r = _state.get("saved_rotate")
        if saved_t:
            cmds.xform(cam, worldSpace=True, translation=saved_t)
        if saved_r:
            cmds.xform(cam, worldSpace=True, rotation=saved_r)

    log("CamLock OFF — camera restored.")
    cmds.inViewMessage(
        amg="<hl>CamLock OFF</hl>  —  camera restored.",
        pos="topCenter", fade=True, fadeStayTime=2000
    )

    # Reset state
    _state.update({
        "locked": False,
        "target": None,
        "script_job_id": None,
        "panel": None,
        "camera": None,
        "camera_shape": None,
        "saved_translate": None,
        "saved_rotate": None,
        "offset_translate": None,
        "offset_rotate": None,
    })


# ── Internal helpers ─────────────────────────────────────────

def _on_frame_changed():
    """
    Called by scriptJob on every time change.
    Moves the viewport camera so it maintains its relative offset to the target.
    """
    target = _state.get("target")
    cam = _state.get("camera")
    offset_t = _state.get("offset_translate")

    if not target or not cam or offset_t is None:
        return
    if not cmds.objExists(target) or not cmds.objExists(cam):
        # Target was deleted — auto-unlock
        unlock()
        return

    # Get current target world position
    target_pos = cmds.xform(target, query=True, worldSpace=True,
                            rotatePivot=True)

    # New camera position = target position + original offset
    new_t = [target_pos[i] + offset_t[i] for i in range(3)]
    cmds.xform(cam, worldSpace=True, translation=new_t)


def _get_active_model_panel():
    """Return the name of the active modelPanel (3D viewport), or None."""
    panel = cmds.getPanel(withFocus=True)
    if panel and cmds.getPanel(typeOf=panel) == "modelPanel":
        return panel

    # Fallback: find the first visible model panel
    for p in cmds.getPanel(type="modelPanel") or []:
        if cmds.modelPanel(p, query=True, exists=True):
            return p
    return None
