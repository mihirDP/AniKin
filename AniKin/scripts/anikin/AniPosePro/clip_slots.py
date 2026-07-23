"""
clip_slots.py — Quick Clip Slots (A-E) for AniPose Pro V2 (F-AC-06).

Temporary in-session animation clip slots for rapid capture without
disk write. The animation equivalent of Quick Snap for poses.
Slots persist via a temp JSON on session close with an option to
promote any slot to the full library.
"""

import os
import json
import datetime
import maya.cmds as cmds

MAX_SLOTS = 5
SLOT_NAMES = ["A", "B", "C", "D", "E"]
_TEMP_FILE = os.path.join(
    os.environ.get("TEMP", os.path.expanduser("~")),
    "anikin_clipslots.json"
)


class ClipSlotManager:
    """
    Manages 5 in-memory animation clip slots for rapid capture/paste.
    Each slot stores the same dict structure as a saved .animclip (V2).
    """

    def __init__(self):
        self._slots = {name: None for name in SLOT_NAMES}
        self._try_restore_from_disk()

    # ── Capture ────────────────────────────────────────────────────────────

    def capture(self, slot, nodes, frame_start, frame_end):
        """
        Capture animation from *nodes* in [frame_start, frame_end] into slot.
        Zero overhead — no playblast, no thumbnail, no disk write.
        """
        if slot not in SLOT_NAMES:
            cmds.warning(
                "AniPose Pro: Invalid clip slot '{}'".format(slot))
            return

        if not nodes:
            cmds.warning("AniPose Pro: Nothing selected to capture.")
            return

        # Deferred import to avoid circular dependency
        from anikin.AniPosePro.capture import capture_anim_clip

        clip_data = capture_anim_clip(nodes, frame_start, frame_end)

        self._slots[slot] = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "frame_range": "{}-{}".format(int(frame_start), int(frame_end)),
            "clip_data": clip_data,
        }
        self._persist()

        cmds.inViewMessage(
            amg="<hl>AniPose Pro</hl>: Clip Slot [{}] captured "
                "({}-{})".format(slot, int(frame_start), int(frame_end)),
            pos="topCenter", fade=True, fadeStayTime=1200
        )

    # ── Paste ──────────────────────────────────────────────────────────────

    def paste(self, slot, nodes, dest_frame, mode="insert",
              retime_frames=None):
        """Paste from a clip slot at dest_frame."""
        if slot not in SLOT_NAMES:
            return
        entry = self._slots.get(slot)
        if entry is None:
            cmds.warning(
                "AniPose Pro: Clip slot [{}] is empty.".format(slot))
            return

        from anikin.AniPosePro.paste import paste_clip_at_frame

        paste_clip_at_frame(
            entry["clip_data"], nodes, dest_frame,
            mode=mode, retime_frames=retime_frames
        )

    # ── Info ───────────────────────────────────────────────────────────────

    def get_slot_info(self, slot):
        """Returns (timestamp, frame_range) or (None, None) if empty."""
        entry = self._slots.get(slot)
        if entry is None:
            return None, None
        return entry.get("timestamp"), entry.get("frame_range")

    def get_slot_data(self, slot):
        """Returns the raw clip_data dict or None."""
        entry = self._slots.get(slot)
        return entry.get("clip_data") if entry else None

    def has_unsaved_slots(self):
        return any(v is not None for v in self._slots.values())

    def clear_slot(self, slot):
        self._slots[slot] = None
        self._persist()

    def clear_all(self):
        for name in SLOT_NAMES:
            self._slots[name] = None
        self._persist()

    # ── Promote to library ─────────────────────────────────────────────────

    def promote_to_library(self, slot, library, name, folder="",
                           tags=None, notes=""):
        """Save a slot's clip data to the full library on disk."""
        entry = self._slots.get(slot)
        if entry is None:
            cmds.warning(
                "AniPose Pro: Clip slot [{}] is empty.".format(slot))
            return None

        from anikin.AniPosePro.capture import (
            save_clip_to_disk, ANIMCLIP_EXT
        )
        import re

        safe = re.sub(r"[^\w\-]", "_", name).lower()
        folder_path = os.path.join(library.root, folder) if folder \
            else library.root
        os.makedirs(folder_path, exist_ok=True)
        output_path = os.path.join(folder_path, safe + ANIMCLIP_EXT)

        return save_clip_to_disk(
            entry["clip_data"], output_path, name=name,
            tags=tags, notes=notes
        )

    # ── Persistence ────────────────────────────────────────────────────────

    def _persist(self):
        try:
            with open(_TEMP_FILE, "w", encoding="utf-8") as f:
                json.dump(self._slots, f, indent=2)
        except Exception:
            pass

    def _try_restore_from_disk(self):
        if not os.path.exists(_TEMP_FILE):
            return
        try:
            with open(_TEMP_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for name in SLOT_NAMES:
                if name in saved and saved[name] is not None:
                    self._slots[name] = saved[name]
        except Exception:
            pass


# ── Module-level singleton ─────────────────────────────────────────────────

_slot_manager = None


def get_clip_slots():
    """Return the module-level ClipSlotManager singleton."""
    global _slot_manager
    if _slot_manager is None:
        _slot_manager = ClipSlotManager()
    return _slot_manager
