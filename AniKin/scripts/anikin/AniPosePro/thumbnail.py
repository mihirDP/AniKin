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
                               width=256, height=192, max_fps=15):
    """
    Capture a multi-frame GIF thumbnail for an animation clip.
    4:3 resolution (256x192), caps at max_fps (15), seamless ping-pong loop.
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

    # Calculate step size based on native FPS and max_fps ceiling
    native_fps = float(cmds.currentUnit(q=True, time=True).replace("fps", "")) if "fps" in cmds.currentUnit(q=True, time=True) else 24.0
    step = 1
    if native_fps > max_fps:
        step = max(1, int(round(native_fps / max_fps)))

    sample_frames = list(range(int(frame_start), int(frame_end) + 1, step))

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
            candidates = glob.glob(jpg_base + "*.jpg")
            if candidates:
                frame_paths.append(candidates[0])
                for c in candidates[1:]:
                    try: os.remove(c)
                    except: pass
        except Exception:
            pass

    if not frame_paths:
        return None

    images = [Image.open(p).convert("RGB") for p in frame_paths]
    
    # Ping-pong loop (forward then reverse, excluding first/last to avoid double-play)
    if len(images) > 2:
        ping_pong = images + images[-2:0:-1]
    else:
        ping_pong = images

    # Duration per frame in ms (1000 / fps)
    target_fps = min(native_fps, max_fps)
    frame_duration = int(1000.0 / target_fps)

    ping_pong[0].save(
        output_path, save_all=True,
        append_images=ping_pong[1:],
        duration=frame_duration, loop=0
    )

    # Cleanup temp files
    import shutil
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass

    return output_path
