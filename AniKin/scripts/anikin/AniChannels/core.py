"""
AniChannels.py
Channel Utilities â€” lock/unlock, key/unkey, mute/unmute AniChannels.

Quick toggles for channel box operations that animators use constantly.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk


def _get_selected_channels():
    """
    Return the channels currently highlighted in the Channel Box.
    If none are highlighted, return None (meaning 'all keyable channels').
    """
    main_cb = "mainChannelBox"
    channels = cmds.channelBox(main_cb, query=True,
                                selectedMainAttributes=True) or []
    return channels if channels else None


def lock_channels():
    """Lock highlighted channels (or all keyable channels) on selected objects."""
    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select objects first.")
        return

    channels = _get_selected_channels()

    with UndoChunk("AniKin: Lock Channels"):
        for node in sel:
            attrs = channels or cmds.listAttr(node, keyable=True) or []
            for attr in attrs:
                full = "{}.{}".format(node, attr)
                if cmds.objExists(full):
                    cmds.setAttr(full, lock=True)


def unlock_channels():
    """Unlock highlighted channels (or all keyable channels) on selected objects."""
    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select objects first.")
        return

    channels = _get_selected_channels()

    with UndoChunk("AniKin: Unlock Channels"):
        for node in sel:
            attrs = channels or cmds.listAttr(node, keyable=True) or []
            for attr in attrs:
                full = "{}.{}".format(node, attr)
                if cmds.objExists(full):
                    cmds.setAttr(full, lock=False)


def key_channels():
    """Set a keyframe on highlighted channels (or all keyable) at current time."""
    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select objects first.")
        return

    channels = _get_selected_channels()

    with UndoChunk("AniKin: Key Channels"):
        for node in sel:
            if channels:
                for attr in channels:
                    cmds.setKeyframe(node, attribute=attr)
            else:
                cmds.setKeyframe(node)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Keyed channels",
        pos="topCenter", fade=True, fadeStayTime=800
    )


def delete_keys():
    """Delete keyframes on highlighted channels at the current time."""
    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select objects first.")
        return

    channels = _get_selected_channels()
    current_time = cmds.currentTime(query=True)

    with UndoChunk("AniKin: Delete Keys"):
        for node in sel:
            if channels:
                for attr in channels:
                    cmds.cutKey(node, attribute=attr,
                                time=(current_time, current_time),
                                clear=True)
            else:
                cmds.cutKey(node, time=(current_time, current_time),
                            clear=True)

