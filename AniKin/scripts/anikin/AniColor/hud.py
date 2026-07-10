"""
AniColor — hud.py
Viewport HUD display on timeline scrub.

When the user scrubs to a frame that has a color label, a HUD element
appears at the top of the viewport for 2 seconds showing:
    AniColor:  [██]  Gold Poses — Left Foot Contact   f.12

Uses cmds.headsUpDisplay with a scriptJob(event=['timeChanged', ...])
listener — appropriate here since it's UI feedback, not DG evaluation.
"""

import maya.cmds as cmds
from anikin.core.log import log_debug
from anikin.AniColor.core import load_payload

HUD_NAME = "AniColorScrubHUD"
_SCRIPT_JOB_ID = None


def _get_label_at_current_frame():
    """Return a formatted HUD string for the current frame, or empty string."""
    frame = int(cmds.currentTime(query=True))
    data = load_payload()
    entry = data.get("frames", {}).get(str(frame))
    if not entry:
        return ""

    pid = entry.get("palette_id", "")
    label = entry.get("label", "")
    slot_name = ""
    for p in data.get("palettes", []):
        if p["id"] == pid:
            slot_name = p.get("name", pid)
            break

    parts = ["AniColor:"]
    if slot_name:
        parts.append(slot_name)
    if label:
        parts.append("- {}".format(label))
    parts.append("f.{}".format(frame))

    return "  ".join(parts)


def _on_time_changed():
    """scriptJob callback — update HUD text on scrub."""
    text = _get_label_at_current_frame()
    if text:
        try:
            cmds.headsUpDisplay(HUD_NAME, edit=True, visible=True)
        except Exception:
            pass
    else:
        try:
            cmds.headsUpDisplay(HUD_NAME, edit=True, visible=False)
        except Exception:
            pass


def _hud_command():
    """HUD data provider callback."""
    return _get_label_at_current_frame()


def enable_hud():
    """Register the scrub HUD and its scriptJob listener."""
    global _SCRIPT_JOB_ID
    disable_hud()

    # Create the HUD block
    try:
        if cmds.headsUpDisplay(HUD_NAME, exists=True):
            cmds.headsUpDisplay(HUD_NAME, remove=True)
    except Exception:
        pass

    try:
        cmds.headsUpDisplay(
            HUD_NAME,
            section=2,  # Top-center area
            block=cmds.headsUpDisplay(nextFreeBlock=2),
            label="",
            labelFontSize="small",
            command=_hud_command,
            event="timeChanged",
            conditionFalse="playingBack",
        )

        # scriptJob for additional refresh
        _SCRIPT_JOB_ID = cmds.scriptJob(
            event=["timeChanged", _on_time_changed],
            protected=True
        )

        log_debug("AniColor: HUD enabled (scriptJob #{})".format(_SCRIPT_JOB_ID))
    except Exception as e:
        cmds.warning("AniColor: Could not enable scrub HUD: {}".format(e))


def disable_hud():
    """Remove the scrub HUD and its scriptJob."""
    global _SCRIPT_JOB_ID

    try:
        if cmds.headsUpDisplay(HUD_NAME, exists=True):
            cmds.headsUpDisplay(HUD_NAME, remove=True)
    except Exception:
        pass

    if _SCRIPT_JOB_ID is not None:
        try:
            cmds.scriptJob(kill=_SCRIPT_JOB_ID, force=True)
        except Exception:
            pass
        _SCRIPT_JOB_ID = None

    log_debug("AniColor: HUD disabled")
