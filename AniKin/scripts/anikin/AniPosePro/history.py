"""
history.py — In-session pose history stack for AniPose Pro.

Every time a pose is applied, the previous rig state is pushed here.
Up to MAX_HISTORY entries are kept. On Maya close the stack is gone
(intentional — history is a session safety net, not long-term storage).
"""

import datetime
import maya.cmds as cmds

MAX_HISTORY = 20

# ── Module-level singleton ─────────────────────────────────────────────────────
_history_stack = None


def get_history():
    """Return the module-level PoseHistoryStack singleton."""
    global _history_stack
    if _history_stack is None:
        _history_stack = PoseHistoryStack()
    return _history_stack


class PoseHistoryStack:
    """
    Stores full keyable-attribute snapshots of rig states.
    Each push() call captures the live values of `nodes` before a pose is applied.
    pop() / restore_index() writes those values back via an undoable chunk.
    """

    def __init__(self):
        self._stack = []

    # ── Write ──────────────────────────────────────────────────────────────────

    def push(self, nodes, label="State"):
        """Snapshot current attribute values of `nodes` and push to stack."""
        snapshot = {}
        for node in nodes:
            if not cmds.objExists(node):
                continue
            snapshot[node] = {}
            for attr in (cmds.listAttr(node, keyable=True) or []):
                full = "{}.{}".format(node, attr)
                try:
                    val = cmds.getAttr(full)
                    if not isinstance(val, list):
                        snapshot[node][attr] = val
                except Exception:
                    pass

        self._stack.append({
            "label":     label,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "data":      snapshot,
        })

        # Trim to cap
        while len(self._stack) > MAX_HISTORY:
            self._stack.pop(0)

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_entries(self):
        """[(index, label, timestamp), ...] newest last."""
        return [(i, e["label"], e["timestamp"])
                for i, e in enumerate(self._stack)]

    def __len__(self):
        return len(self._stack)

    # ── Restore ────────────────────────────────────────────────────────────────

    def pop(self):
        """Restore & remove the most recent entry (true undo)."""
        if not self._stack:
            cmds.warning("AniPose Pro: No pose history to restore.")
            return
        self.restore_index(len(self._stack) - 1)
        self._stack.pop()

    def restore_index(self, index):
        """Restore to a specific history entry (non-destructive — entry stays)."""
        if index < 0 or index >= len(self._stack):
            return
        entry = self._stack[index]
        cmds.undoInfo(openChunk=True, chunkName="AniKin_PoseHistoryRestore")
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
            amg="<hl>AniPose Pro</hl>: Restored — {}".format(entry["label"]),
            pos="topCenter", fade=True, fadeStayTime=1200
        )

    def clear(self):
        self._stack.clear()
