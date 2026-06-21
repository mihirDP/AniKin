"""
AniBookmarks.py
Time Bookmarks — save, navigate, and manage named time positions and ranges.
Persisted in scene as a JSON string on a network node.
"""

import json
import os
import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.log import log_debug

STORAGE_NODE = "anikin_time_bookmarks"
MAX_BOOKMARKS = 64

# Color presets (hex values matching Tailwind/standard palette)
COLORS = {
    "blue": "#3b82f6",
    "red": "#ef4444",
    "green": "#22c55e",
    "gold": "#f59e0b",
    "purple": "#8b5cf6",
    "teal": "#14b8a6",
    "pink": "#ec4899",
    "white": "#ffffff"
}

# Session cache to survive "Delete History" or "Optimize Scene"
_SESSION_CACHE = []


def _ensure_storage_node():
    """Create the storage network node if it doesn't exist, restoring from session cache if needed."""
    global _SESSION_CACHE
    if not cmds.objExists(STORAGE_NODE):
        cmds.createNode("network", name=STORAGE_NODE, skipSelect=True)
        cmds.addAttr(STORAGE_NODE, longName="data", dataType="string")
        
        # Restore from session cache if it got deleted
        if _SESSION_CACHE:
            cmds.setAttr("{}.data".format(STORAGE_NODE), json.dumps(_SESSION_CACHE), type="string")
        else:
            cmds.setAttr("{}.data".format(STORAGE_NODE), "[]", type="string")
            
    return STORAGE_NODE


def _get_bookmarks():
    """Return the list of bookmarks from the network node."""
    global _SESSION_CACHE
    _ensure_storage_node()
    try:
        raw = cmds.getAttr("{}.data".format(STORAGE_NODE)) or "[]"
        data = json.loads(raw)
        _SESSION_CACHE = data
        return data
    except Exception:
        return []


def _save_bookmarks(bookmarks):
    """Save the bookmarks list to the network node and session cache."""
    global _SESSION_CACHE
    _ensure_storage_node()
    _SESSION_CACHE = bookmarks
    try:
        cmds.setAttr("{}.data".format(STORAGE_NODE), json.dumps(bookmarks), type="string")
    except Exception as e:
        cmds.warning("AniKin: Failed to save bookmarks: {}".format(e))


def save_bookmark(name, frame=None, color="blue", range_end=None):
    """
    Save a new bookmark or range bookmark.
    
    Args:
        name: Name of the bookmark.
        frame: The start frame (defaults to current frame).
        color: Pre-defined color key from COLORS.
        range_end: Optional end frame for a range bookmark.
    """
    bookmarks = _get_bookmarks()
    
    if len(bookmarks) >= MAX_BOOKMARKS:
        cmds.warning("AniKin: Maximum limit of {} bookmarks reached. Delete old bookmarks first.".format(MAX_BOOKMARKS))
        return False
        
    if len(bookmarks) >= 60:
        cmds.warning("AniKin: Nearing bookmark limit ({} / {}).".format(len(bookmarks), MAX_BOOKMARKS))

    if frame is None:
        import maya.mel as mel
        try:
            gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
            if cmds.timeControl(gPlayBackSlider, query=True, rangeVisible=True):
                rng = cmds.timeControl(gPlayBackSlider, query=True, rangeArray=True)
                frame = rng[0]
                range_end = rng[1]
            else:
                frame = cmds.currentTime(query=True)
        except Exception:
            frame = cmds.currentTime(query=True)

    # Sanitize color
    if color not in COLORS:
        color = "blue"

    new_bookmark = {
        "name": name or "Frame {}".format(int(frame)),
        "frame": float(frame),
        "color": color,
        "range_end": float(range_end) if range_end is not None else None
    }

    with UndoChunk("AniKin: Save Bookmark '{}'".format(name)):
        bookmarks.append(new_bookmark)
        _save_bookmarks(bookmarks)
        log_debug("AniBookmarks: Saved bookmark '{}' at frame {} (range_end: {})".format(new_bookmark["name"], new_bookmark["frame"], new_bookmark["range_end"]))

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Saved bookmark '{}'".format(new_bookmark["name"]),
        pos="topCenter", fade=True, fadeStayTime=1500
    )
    return True


def goto_bookmark(bookmark_idx):
    """Jump to the bookmark and highlight/select its range if it exists."""
    bookmarks = _get_bookmarks()
    if bookmark_idx < 0 or bookmark_idx >= len(bookmarks):
        return

    b = bookmarks[bookmark_idx]
    frame = b["frame"]
    range_end = b.get("range_end")

    log_debug("AniBookmarks: Navigating to bookmark '{}' at frame {}".format(b["name"], frame))
    cmds.currentTime(frame)

    if range_end is not None:
        # Set playback range AND time slider highlight
        cmds.playbackOptions(minTime=frame, maxTime=range_end)
        # Highlight range in Maya time slider
        import maya.mel as mel
        try:
            gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
            cmds.timeControl(gPlayBackSlider, edit=True, rangeArray=(frame, range_end), rangeVisible=True)
        except Exception:
            pass

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Jumped to '{}'".format(b["name"]),
        pos="topCenter", fade=True, fadeStayTime=1000
    )


def delete_bookmark(bookmark_idx):
    """Delete a bookmark by index."""
    bookmarks = _get_bookmarks()
    if bookmark_idx < 0 or bookmark_idx >= len(bookmarks):
        return

    with UndoChunk("AniKin: Delete Bookmark"):
        deleted = bookmarks.pop(bookmark_idx)
        _save_bookmarks(bookmarks)
        log_debug("AniBookmarks: Deleted bookmark '{}'".format(deleted["name"]))

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Deleted bookmark '{}'".format(deleted["name"]),
        pos="topCenter", fade=True, fadeStayTime=1000
    )


def list_bookmarks():
    """Return list of all bookmark dicts."""
    return _get_bookmarks()


def reorder_bookmarks(from_idx, to_idx):
    """Reorder bookmarks in the list."""
    bookmarks = _get_bookmarks()
    if 0 <= from_idx < len(bookmarks) and 0 <= to_idx < len(bookmarks):
        with UndoChunk("AniKin: Reorder Bookmarks"):
            item = bookmarks.pop(from_idx)
            bookmarks.insert(to_idx, item)
            _save_bookmarks(bookmarks)


def export_bookmarks(file_path):
    """Export bookmarks to a JSON file."""
    bookmarks = _get_bookmarks()
    try:
        with open(file_path, "w") as f:
            json.dump(bookmarks, f, indent=4)
        return True
    except Exception as e:
        cmds.warning("AniKin: Export failed: {}".format(e))
        return False


def import_bookmarks(file_path):
    """Import bookmarks from a JSON file, merging with existing."""
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, "r") as f:
            imported = json.load(f)
        
        # Simple validation
        if not isinstance(imported, list):
            return False
            
        bookmarks = _get_bookmarks()
        for item in imported:
            if isinstance(item, dict) and "name" in item and "frame" in item:
                # Add if not exceeded cap
                if len(bookmarks) < MAX_BOOKMARKS:
                    bookmarks.append({
                        "name": item["name"],
                        "frame": float(item["frame"]),
                        "color": item.get("color", "blue"),
                        "range_end": float(item["range_end"]) if item.get("range_end") is not None else None
                    })
        _save_bookmarks(bookmarks)
        return True
    except Exception as e:
        cmds.warning("AniKin: Import failed: {}".format(e))
        return False
