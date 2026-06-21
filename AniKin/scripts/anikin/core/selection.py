"""
selection.py
Selection utilities for AniKin tools.

Centralizes selection querying and validation so every tool
doesn't re-implement its own error checking.
"""

import maya.cmds as cmds


def get_selected(min_count=1, max_count=None, error_msg=None):
    """
    Return the current selection, raising RuntimeError if count constraints
    are not met.

    Args:
        min_count: Minimum number of objects required.
        max_count: Maximum number of objects allowed (None = no limit).
        error_msg: Custom error message. If None, a default is generated.

    Returns:
        list[str]: Selected node names.

    Raises:
        RuntimeError: If selection doesn't meet constraints.
    """
    sel = cmds.ls(selection=True, long=True) or []
    count = len(sel)

    if count < min_count:
        msg = error_msg or "Select at least {} object(s). Currently selected: {}".format(
            min_count, count
        )
        cmds.warning(msg)
        raise RuntimeError(msg)

    if max_count is not None and count > max_count:
        msg = error_msg or "Select at most {} object(s). Currently selected: {}".format(
            max_count, count
        )
        cmds.warning(msg)
        raise RuntimeError(msg)

    return sel


def get_selected_or_warn(min_count=1):
    """
    Like get_selected but returns an empty list instead of raising.
    Prints a warning to Maya's script output.
    """
    try:
        return get_selected(min_count=min_count)
    except RuntimeError:
        return []
