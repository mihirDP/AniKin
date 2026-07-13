"""
quick_snap.py — In-session Quick Snap slots for AniPose Pro (F-PL-13).

Preserves the original AniSnap "hold my pose" workflow as 5 named in-memory
slots (A–E) with optional crash persistence via a temp JSON file.
"""

import os
import json
import datetime
import maya.cmds as cmds

MAX_SLOTS = 5
SLOT_NAMES = ["A", "B", "C", "D", "E"]
_TEMP_FILE = os.path.join(
    os.environ.get("TEMP", os.path.expanduser("~")),
    "anikin_quicksnap.json"
)


class QuickSnapManager:
    """
    Manages 5 in-memory pose slots.
    Serializes to disk on every capture so slots survive crashes.
    """

    def __init__(self):
        self._slots = {name: None for name in SLOT_NAMES}
        self._try_restore_from_disk()

    # ── Capture ────────────────────────────────────────────────────────────────

    def snap(self, slot, nodes=None):
        """
        Capture current values of `nodes` (or Maya selection) into slot.
        slot: one of "A","B","C","D","E"
        """
        if slot not in SLOT_NAMES:
            cmds.warning("AniPose Pro: Invalid Quick Snap slot '{}'".format(slot))
            return

        sel = nodes or (cmds.ls(selection=True, long=True) or [])
        if not sel:
            cmds.warning("AniPose Pro: Nothing selected to Quick Snap.")
            return

        snapshot = {}
        for node in sel:
            snapshot[node] = {}
            for attr in (cmds.listAttr(node, keyable=True) or []):
                full = "{}.{}".format(node, attr)
                try:
                    val = cmds.getAttr(full)
                    if not isinstance(val, list):
                        snapshot[node][attr] = val
                except Exception:
                    pass

        self._slots[slot] = {
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "data": snapshot,
        }
        self._persist()

        cmds.inViewMessage(
            amg="<hl>AniPose Pro</hl>: Quick Snap [{}] captured ({} objects)".format(
                slot, len(sel)),
            pos="topCenter", fade=True, fadeStayTime=1200
        )

    # ── Restore ────────────────────────────────────────────────────────────────

    def restore(self, slot):
        """Restore a Quick Snap slot to the current scene."""
        if slot not in SLOT_NAMES:
            return
        entry = self._slots.get(slot)
        if entry is None:
            cmds.warning("AniPose Pro: Quick Snap slot [{}] is empty.".format(slot))
            return

        cmds.undoInfo(openChunk=True, chunkName="AniKin_QuickSnapRestore")
        try:
            for node, attrs in entry["data"].items():
                if not cmds.objExists(node):
                    continue
                for attr, val in attrs.items():
                    full = "{}.{}".format(node, attr)
                    try:
                        if not cmds.getAttr(full, lock=True):
                            cmds.setAttr(full, val)
                    except Exception:
                        pass
        finally:
            cmds.undoInfo(closeChunk=True)

        cmds.inViewMessage(
            amg="<hl>AniPose Pro</hl>: Quick Snap [{}] restored".format(slot),
            pos="topCenter", fade=True, fadeStayTime=1200
        )

    # ── Info ───────────────────────────────────────────────────────────────────

    def get_slot_info(self, slot):
        """Returns (timestamp, node_count) or (None, 0) if empty."""
        entry = self._slots.get(slot)
        if entry is None:
            return None, 0
        return entry["timestamp"], len(entry["data"])

    def has_unsaved_snaps(self):
        return any(v is not None for v in self._slots.values())

    def clear_slot(self, slot):
        self._slots[slot] = None
        self._persist()

    def clear_all(self):
        for name in SLOT_NAMES:
            self._slots[name] = None
        self._persist()

    # ── Persistence ────────────────────────────────────────────────────────────

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
