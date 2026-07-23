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
        import glob
        # playblast appends frame number, padding is unpredictable
        candidates = glob.glob(base + "*.jpg")
        if candidates:
            # Get the first matching image (there should only be one)
            actual_file = candidates[0]
            os.replace(actual_file, output_path)
            # Cleanup any others if present
            for c in candidates[1:]:
                try: os.remove(c)
                except: pass
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


# ── V2: Animated GIF Thumbnail for Clips ──────────────────────────────────────

def capture_clip_thumbnail_gif(frame_start, frame_end, output_path,
                               width=256, height=256, max_frames=12):
    """
    Capture a multi-frame GIF thumbnail for an animation clip.
    Samples up to max_frames evenly across the range.
    Returns path to output .gif, or None on failure.

    Falls back to static .jpg if Pillow is not available.
    Uses offScreen=False to avoid the Maya 2024+ playblast regression.
    """
    import tempfile

    try:
        from PIL import Image
    except ImportError:
        # Pillow not available — fallback to static thumbnail
        jpg_path = output_path.replace(".gif", ".thumb.jpg")
        if capture_viewport_thumbnail(jpg_path, width, height):
            return jpg_path
        return None

    frame_count = frame_end - frame_start + 1
    step = max(1, frame_count // max_frames)
    sample_frames = list(range(int(frame_start), int(frame_end) + 1, step))
    sample_frames = sample_frames[:max_frames]

    tmp_dir = tempfile.mkdtemp(prefix="anikin_clip_thumb_")
    frame_paths = []

    for i, frame in enumerate(sample_frames):
        cmds.currentTime(frame)
        jpg_base = os.path.join(tmp_dir, "frame_{:04d}".format(i))
        try:
            cmds.playblast(
                frame=[frame], filename=jpg_base,
                format="image", compression="jpg",
                widthHeight=[width, height],
                showOrnaments=False, percent=100,
                viewer=False, offScreen=False
            )
            import glob
            # playblast appends frame number with unpredictable padding
            candidates = glob.glob(jpg_base + "*.jpg")
            if candidates:
                frame_paths.append(candidates[0])
                # Delete any extra ones just in case
                for c in candidates[1:]:
                    try: os.remove(c)
                    except: pass
        except Exception:
            pass

    if not frame_paths:
        return None

    images = [Image.open(p).convert("RGB") for p in frame_paths]
    images[0].save(
        output_path, save_all=True,
        append_images=images[1:],
        duration=80, loop=0
    )

    # Cleanup temp files
    import shutil
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass

    return output_path
