"""
undo.py
Context manager for Maya undo chunks.

Wrapping tool operations in UndoChunk ensures the entire operation
can be reversed with a single Ctrl+Z, regardless of how many
individual Maya commands ran inside.

Usage:
    with UndoChunk("My Tool Operation"):
        cmds.setAttr(...)
        cmds.setKeyframe(...)
"""

import maya.cmds as cmds


class UndoChunk:
    """Context manager that opens/closes a Maya undo chunk."""

    def __init__(self, name="AniKin Operation"):
        self._name = name

    def __enter__(self):
        cmds.undoInfo(openChunk=True, chunkName=self._name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        cmds.undoInfo(closeChunk=True)
        # Don't suppress exceptions — let them propagate
        return False
