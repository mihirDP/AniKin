"""
thumbnail.py — Viewport thumbnail capture for AniPose Pro.

Uses cmds.playblast with offScreen=False (Maya 2024+ regression workaround).
Falls back to thumbnailCaptureComponent on Maya 2025+.
"""

import os
import maya.cmds as cmds


def capture_viewport_thumbnail(output_path, width=256, height=256):
    """
    Capture the active viewport as a JPEG at output_path.
    Returns True on success, False on failure (pose still saved without thumb).
    
    Dev note: offScreen=True causes "Unable to allocate offscreen buffer" in
    Maya 2024+ when a camera was recently manipulated programmatically.
    offScreen=False is intentional and reliable across Maya 2022–2026.
    """
    # Ensure directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    panel = cmds.getPanel(withFocus=True) or ""
    if cmds.getPanel(typeOf=panel) != "modelPanel":
        panels = [p for p in (cmds.getPanel(type="modelPanel") or [])
                  if cmds.modelPanel(p, q=True, exists=True)]
        panel = panels[0] if panels else None

    if panel is None:
        cmds.warning("AniPose Pro: No viewport available for thumbnail capture.")
        return False

    base = os.path.splitext(output_path)[0]
    frame = int(cmds.currentTime(q=True))

    try:
        cmds.playblast(
            format="image",
            filename=base,
            sequenceTime=False,
            clearCache=True,
            viewer=False,
            showOrnaments=False,
            startTime=frame,
            endTime=frame,
            forceOverwrite=True,
            offScreen=False,
            percent=100,
            compression="jpg",
            quality=85,
            widthHeight=[width, height],
        )
        # playblast appends frame number: base.0001.jpg
        candidate = "{}.{:04d}.jpg".format(base, frame)
        if not os.path.exists(candidate):
            candidate = "{}.0000.jpg".format(base)
        if os.path.exists(candidate):
            os.replace(candidate, output_path)
            return True
    except Exception as exc:
        cmds.warning("AniPose Pro: Thumbnail capture failed — {}".format(exc))

    # Maya 2025+ fallback
    try:
        return _capture_thumbnail_component(output_path, frame)
    except Exception:
        pass

    return False


def _capture_thumbnail_component(output_path, frame):
    """Alternative via thumbnailCaptureComponent (Maya 2025+)."""
    cmds.thumbnailCaptureComponent(capture=True, startFrame=frame, endFrame=frame)
    preview = cmds.thumbnailCaptureComponent(q=True, previewPath=True)
    if preview and os.path.exists(preview):
        import shutil
        shutil.copy2(preview, output_path)
        cmds.thumbnailCaptureComponent(delete=True)
        return True
    return False
