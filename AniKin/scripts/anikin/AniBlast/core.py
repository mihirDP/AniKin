"""
AniBlast — Advanced Playblaster for AniKin.

One-click playblast with:
  - Custom HUD burn-ins (frame counter, focal length, animator name, shot name)
  - Image-sequence capture via cmds.playblast (reliable across all Maya versions)
  - ffmpeg-based H.264 MP4 encoding with audio support
  - Graceful degradation: falls back to image sequence if ffmpeg is not installed

Does NOT bundle ffmpeg — requires the user to have ffmpeg on PATH (or configured).
"""

import os
import subprocess
import shutil
import maya.cmds as cmds
from anikin.core.undo import UndoChunk


# ── Defaults ──────────────────────────────────────────────────────────────────

_DEFAULTS = {
    "resolution_x":  1920,
    "resolution_y":  1080,
    "quality":       100,
    "format":        "png",
    "show_frame":    True,
    "show_focal":    True,
    "show_author":   True,
    "show_scene":    True,
    "author_name":   "",     # Auto-detected from OS if empty
    "output_dir":    "",     # Auto-determined per scene if empty
    "ffmpeg_path":   "",     # Empty = search PATH
}

# HUD block IDs for cleanup
_HUD_IDS = []


# ── Public API ────────────────────────────────────────────────────────────────

def blast(output_path=None, resolution=None, show_hud=True,
          encode_mp4=True, include_audio=True, viewer=True, **overrides):
    """
    Execute a full playblast workflow:
      1. Register HUD burn-ins
      2. Playblast to image sequence
      3. Encode to MP4 via ffmpeg (if available)
      4. Clean up HUD and temp files

    Args:
        output_path:    Destination path (without extension). Auto-generates if None.
        resolution:     (width, height) tuple. Defaults to scene render settings or 1920x1080.
        show_hud:       Register HUD overlays during blast.
        encode_mp4:     Attempt ffmpeg encoding after blast.
        include_audio:  Include scene audio in the MP4 (if available).
        viewer:         Open the result in the OS default viewer.
        **overrides:    Override any key from _DEFAULTS.
    """
    cfg = dict(_DEFAULTS)
    cfg.update(overrides)

    # Resolve paths
    if output_path is None:
        output_path = _auto_output_path()

    if resolution:
        width, height = resolution
    else:
        width  = cfg["resolution_x"]
        height = cfg["resolution_y"]

    start = cmds.playbackOptions(q=True, minTime=True)
    end   = cmds.playbackOptions(q=True, maxTime=True)
    fps   = _get_scene_fps()

    # Temp directory for image sequence
    seq_dir = output_path + "_blast_seq"
    os.makedirs(seq_dir, exist_ok=True)
    seq_base = os.path.join(seq_dir, "frame")

    try:
        # Step 1: Register HUD
        if show_hud:
            _register_hud(cfg)

        # Step 2: Playblast to image sequence
        cmds.playblast(
            format="image",
            filename=seq_base,
            sequenceTime=False,
            clearCache=True,
            viewer=False,
            showOrnaments=show_hud,
            startTime=int(start),
            endTime=int(end),
            forceOverwrite=True,
            offScreen=False,
            percent=100,
            compression=cfg["format"],
            quality=cfg["quality"],
            widthHeight=[width, height],
        )

        cmds.inViewMessage(
            amg="<hl>AniBlast</hl>: Image sequence captured.",
            pos="topCenter", fade=True, fadeStayTime=1500
        )

        # Step 3: Encode to MP4
        mp4_path = output_path + ".mp4"
        if encode_mp4:
            ffmpeg = _find_ffmpeg(cfg.get("ffmpeg_path", ""))
            if ffmpeg:
                audio_path = _get_scene_audio() if include_audio else None
                success = _encode_mp4(ffmpeg, seq_dir, mp4_path,
                                      fps=fps, audio_path=audio_path,
                                      fmt=cfg["format"])
                if success:
                    cmds.inViewMessage(
                        amg="<hl>AniBlast</hl>: MP4 saved to '{}'".format(
                            os.path.basename(mp4_path)),
                        pos="topCenter", fade=True, fadeStayTime=2500
                    )
                    # Clean up image sequence
                    shutil.rmtree(seq_dir, ignore_errors=True)

                    if viewer:
                        os.startfile(mp4_path)
                    return mp4_path
                else:
                    cmds.warning("AniBlast: ffmpeg encoding failed. Image sequence preserved.")
            else:
                cmds.warning("AniBlast: ffmpeg not found on PATH. "
                             "Image sequence saved to: {}".format(seq_dir))

        # If we didn't encode, report the image sequence location
        if viewer and not encode_mp4:
            os.startfile(seq_dir)
        return seq_dir

    finally:
        # Step 4: Clean up HUD
        if show_hud:
            _remove_hud()


# ── HUD Management ────────────────────────────────────────────────────────────

def _register_hud(cfg):
    """Register custom HUD elements for the playblast."""
    global _HUD_IDS
    _remove_hud()  # Clean any leftover HUDs

    section = 7   # Top-right area

    if cfg.get("show_frame"):
        hud_name = "AniBlast_Frame"
        free_block = cmds.headsUpDisplay(nextFreeBlock=section)
        cmds.headsUpDisplay(
            hud_name,
            section=section, block=free_block,
            label="Frame:",
            command=lambda: int(cmds.currentTime(q=True)),
            event="timeChanged",
            dataFontSize="large",
        )
        _HUD_IDS.append(hud_name)

    if cfg.get("show_focal"):
        hud_name = "AniBlast_Focal"
        free_block = cmds.headsUpDisplay(nextFreeBlock=section)
        cmds.headsUpDisplay(
            hud_name,
            section=section, block=free_block,
            label="Focal:",
            command=_get_focal_length,
            event="timeChanged",
            dataFontSize="small",
        )
        _HUD_IDS.append(hud_name)

    if cfg.get("show_author"):
        hud_name = "AniBlast_Author"
        author = cfg.get("author_name") or _get_user()
        free_block = cmds.headsUpDisplay(nextFreeBlock=5)
        cmds.headsUpDisplay(
            hud_name,
            section=5, block=free_block,
            label="Animator: {}".format(author),
            dataFontSize="small",
        )
        _HUD_IDS.append(hud_name)

    if cfg.get("show_scene"):
        hud_name = "AniBlast_Scene"
        scene = os.path.basename(cmds.file(q=True, sceneName=True) or "untitled")
        free_block = cmds.headsUpDisplay(nextFreeBlock=5)
        cmds.headsUpDisplay(
            hud_name,
            section=5, block=free_block,
            label="Scene: {}".format(scene),
            dataFontSize="small",
        )
        _HUD_IDS.append(hud_name)


def _remove_hud():
    """Remove all AniBlast HUD elements."""
    global _HUD_IDS
    for hud_name in _HUD_IDS:
        try:
            if cmds.headsUpDisplay(hud_name, exists=True):
                cmds.headsUpDisplay(hud_name, remove=True)
        except Exception:
            pass
    _HUD_IDS = []


# ── ffmpeg Encoding ────────────────────────────────────────────────────────────

def _find_ffmpeg(user_path=""):
    """Locate ffmpeg binary. User path > PATH search."""
    if user_path and os.path.isfile(user_path):
        return user_path
    return shutil.which("ffmpeg")


def _encode_mp4(ffmpeg, seq_dir, output_mp4, fps=24, audio_path=None, fmt="png"):
    """
    Encode an image sequence to H.264 MP4 using ffmpeg subprocess.
    pix_fmt=yuv420p is required for Windows Media Player / QuickTime compatibility.
    """
    # Find the image sequence pattern
    ext = fmt
    images = sorted([f for f in os.listdir(seq_dir) if f.endswith(".{}".format(ext))])
    if not images:
        return False

    # Determine the naming pattern: frame.NNNN.png
    input_pattern = os.path.join(seq_dir, "frame.%04d.{}".format(ext))

    # Determine start number from first image filename
    # Pattern: frame.0001.png → start_number = 1
    try:
        first_num = int(images[0].replace("frame.", "").replace(".{}".format(ext), ""))
    except (ValueError, IndexError):
        first_num = 0

    cmd = [
        ffmpeg, "-y",
        "-framerate", str(int(fps)),
        "-start_number", str(first_num),
        "-i", input_pattern,
    ]

    # Audio (optional)
    if audio_path and os.path.isfile(audio_path):
        cmd.extend(["-i", audio_path, "-shortest"])

    cmd.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        output_mp4
    ])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=300,   # 5 min timeout for long sequences
        )
        return result.returncode == 0
    except Exception as exc:
        cmds.warning("AniBlast ffmpeg error: {}".format(exc))
        return False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _auto_output_path():
    """Generate a default output path based on the scene name."""
    scene = cmds.file(q=True, sceneName=True) or ""
    if scene:
        base = os.path.splitext(scene)[0]
        return base + "_playblast"
    else:
        import tempfile
        return os.path.join(tempfile.gettempdir(), "anikin_playblast")


def _get_scene_fps():
    """Return the scene's FPS as an integer."""
    unit = cmds.currentUnit(q=True, time=True)
    fps_map = {
        "game": 15, "film": 24, "pal": 25, "ntsc": 30, "show": 48,
        "palf": 50, "ntscf": 60, "23.976fps": 24, "29.97fps": 30,
        "29.97df": 30, "47.952fps": 48, "59.94fps": 60,
        "44100fps": 44100, "48000fps": 48000,
    }
    return fps_map.get(unit, 24)


def _get_scene_audio():
    """Find the first audio node's file path in the scene, or None."""
    audio_nodes = cmds.ls(type="audio") or []
    if not audio_nodes:
        return None
    try:
        return cmds.getAttr("{}.filename".format(audio_nodes[0]))
    except Exception:
        return None


def _get_focal_length():
    """Return the active camera's focal length for HUD display."""
    try:
        panel = cmds.getPanel(withFocus=True) or ""
        if cmds.getPanel(typeOf=panel) == "modelPanel":
            cam = cmds.modelPanel(panel, q=True, camera=True)
            cam_shape = cmds.listRelatives(cam, shapes=True)
            if cam_shape:
                return round(cmds.getAttr("{}.focalLength".format(cam_shape[0])), 1)
    except Exception:
        pass
    return 0.0


def _get_user():
    import getpass
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"
