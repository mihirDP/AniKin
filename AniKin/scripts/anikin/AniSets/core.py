"""
AniSets.py
Selection Sets â€” save and recall custom selection groups per scene.

Stores selection sets in a hidden Maya node (network node) so they
persist with the scene file. Each set has a user-defined name and
stores the full DAG paths of its members.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk

# The network node that stores all AniKin selection sets
STORAGE_NODE = "anikin_selection_sets"
SET_PREFIX = "afset_"


def _ensure_storage_node():
    """Create the storage network node if it doesn't exist."""
    if not cmds.objExists(STORAGE_NODE):
        cmds.createNode("network", name=STORAGE_NODE, skipSelect=True)
        cmds.addAttr(STORAGE_NODE, longName="set_names", dataType="string")
        cmds.setAttr("{}.set_names".format(STORAGE_NODE), "", type="string")
    return STORAGE_NODE


def _get_set_names():
    """Return a list of saved set names."""
    _ensure_storage_node()
    raw = cmds.getAttr("{}.set_names".format(STORAGE_NODE)) or ""
    if not raw:
        return []
    return [n for n in raw.split(",") if n]


def _save_set_names(names):
    """Persist the list of set names."""
    cmds.setAttr("{}.set_names".format(STORAGE_NODE),
                 ",".join(names), type="string")


def save_set(name):
    """
    Save the current selection under the given name.

    Args:
        name: User-defined name for the selection set.
    """
    sel = cmds.ls(selection=True, long=True) or []
    if not sel:
        cmds.warning("AniKin: Select objects to save as a set.")
        return

    with UndoChunk("AniKin: Save Selection Set '{}'".format(name)):
        node = _ensure_storage_node()
        attr_name = SET_PREFIX + name

        # Create or update the attribute
        if not cmds.attributeQuery(attr_name, node=node, exists=True):
            cmds.addAttr(node, longName=attr_name, dataType="string")

        # Store as comma-separated DAG paths
        cmds.setAttr("{}.{}".format(node, attr_name),
                     ",".join(sel), type="string")

        # Update the name registry
        names = _get_set_names()
        if name not in names:
            names.append(name)
            _save_set_names(names)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Saved set '{}' ({} objects)".format(name, len(sel)),
        pos="topCenter", fade=True, fadeStayTime=1500
    )


def recall_set(name, add_to_selection=False):
    """
    Select the objects stored in the named set.

    Args:
        name: Name of the set to recall.
        add_to_selection: If True, add to current selection instead of replacing.
    """
    node = _ensure_storage_node()
    attr_name = SET_PREFIX + name

    if not cmds.attributeQuery(attr_name, node=node, exists=True):
        cmds.warning("AniKin: Selection set '{}' not found.".format(name))
        return

    raw = cmds.getAttr("{}.{}".format(node, attr_name)) or ""
    members = [m for m in raw.split(",") if m and cmds.objExists(m)]

    if not members:
        cmds.warning("AniKin: Set '{}' is empty or members no longer exist.".format(name))
        return

    if add_to_selection:
        cmds.select(members, add=True)
    else:
        cmds.select(members, replace=True)


def delete_set(name):
    """Remove a saved selection set."""
    with UndoChunk("AniKin: Delete Selection Set '{}'".format(name)):
        node = _ensure_storage_node()
        attr_name = SET_PREFIX + name

        if cmds.attributeQuery(attr_name, node=node, exists=True):
            cmds.deleteAttr("{}.{}".format(node, attr_name))

        names = _get_set_names()
        if name in names:
            names.remove(name)
            _save_set_names(names)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Deleted set '{}'".format(name),
        pos="topCenter", fade=True, fadeStayTime=1000
    )


def list_sets():
    """Return a list of all saved selection set names."""
    return _get_set_names()

