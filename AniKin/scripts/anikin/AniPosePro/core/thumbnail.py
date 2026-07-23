"""
thumbnail.py — Viewport Snapshot & Animated GIF Thumbnail Generation for AniPose Pro V3.1.
"""

import os
import glob
import shutil
import maya.cmds as cmds


def capture_thumbnail(output_path: str, width: int = 256, height: int = 256) -> bool:
    """
    Captures the active viewport as a JPEG thumbnail.
    Temporarily hides grid and display ornaments for a clean capture.
    """
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

    # Store display states
    grid_vis = cmds.modelEditor(panel, q=True, grid=True)
    heads_up_vis = cmds.modelEditor(panel, q=True, headsUpDisplay=True)

    cmds.modelEditor(panel, e=True, grid=False, headsUpDisplay=False)

    base = os.path.splitext(output_path)[0]
    frame = int(cmds.currentTime(q=True))

    success = False
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

        candidates = glob.glob(base + "*.jpg")
        if candidates:
            actual_file = candidates[0]
            os.replace(actual_file, output_path)
            for c in candidates[1:]:
                try: os.remove(c)
                except Exception: pass
            success = True
    except Exception as exc:
        cmds.warning(f"AniPose Pro: Thumbnail capture failed — {exc}")
    finally:
        cmds.modelEditor(panel, e=True, grid=grid_vis, headsUpDisplay=heads_up_vis)

    return success


def capture_clip_thumbnail(start: int, end: int, output_path: str,
                           width: int = 120, height: int = 120, fps: int = 8) -> str:
    """
    Creates an animated GIF thumbnail for a clip by:
    1. Playblasting a frame range to JPEG sequence
    2. Converting with Pillow to animated GIF
    Falls back to static JPEG if Pillow is unavailable.
    """
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    tmp_dir = os.path.join(out_dir, "_tmp_thumb_frames")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_base = os.path.join(tmp_dir, "frame")

    try:
        cmds.playblast(
            startTime=start, endTime=end,
            format="image", compression="jpg", quality=75,
            widthHeight=[width, height],
            filename=tmp_base,
            offScreen=False, viewer=False, percent=100,
            showOrnaments=False
        )

        # Convert JPEG sequence to GIF using Pillow
        try:
            from PIL import Image
            frames = []
            jpg_files = sorted(glob.glob(tmp_base + "*.jpg"))
            for fpath in jpg_files:
                frames.append(Image.open(fpath))

            if frames:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    loop=0,
                    duration=int(1000 / fps)
                )
                return output_path
        except ImportError:
            # Fallback to static JPG
            jpg_files = sorted(glob.glob(tmp_base + "*.jpg"))
            if jpg_files:
                static_jpg = output_path.replace(".gif", ".thumb.jpg")
                shutil.copy(jpg_files[0], static_jpg)
                return static_jpg
    except Exception as e:
        cmds.warning(f"AniPose Pro: Animated GIF thumbnail capture failed — {e}")
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

    return output_path
