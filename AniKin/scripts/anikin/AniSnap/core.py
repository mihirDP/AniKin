"""
AniSnap.py
Visual Pose Library — saves and applies poses with namespace-stripped controls,
blending, viewport snapshots, L/R mirroring support, multiple library roots, and sub-folders.
"""

import os
import json
import time
import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core import settings
from anikin.core.log import log_debug

DEFAULT_ROOT = os.path.expanduser("~/maya/anikin_poses")


def get_library_roots():
    """Retrieve all configured pose library roots from settings."""
    data = settings.load_settings()
    roots = data.get("pose_library_roots", [DEFAULT_ROOT])
    # Ensure they are absolute paths
    return [os.path.abspath(r) for r in roots]


def get_rig_name():
    """Determine the active rig name based on selection namespace."""
    sel = cmds.ls(selection=True)
    if not sel:
        return "default_rig"
    parts = sel[0].split(":")
    if len(parts) > 1:
        return parts[0]
    return "default_rig"


def get_pose_directory(root_path, rig_name, folder=""):
    """Get path to a specific folder in a library root."""
    path = os.path.join(root_path, rig_name)
    if folder:
        path = os.path.join(path, folder)
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception:
            pass
    return path


def list_subfolders(root_path, rig_name):
    """List all user-created subfolder sets/directories inside the active rig folder."""
    rig_dir = os.path.join(root_path, rig_name)
    if not os.path.exists(rig_dir):
        return []
    
    subfolders = []
    for item in os.listdir(rig_dir):
        full_path = os.path.join(rig_dir, item)
        if os.path.isdir(full_path):
            subfolders.append(item)
    return sorted(subfolders)


def save_pose(name, root_path, folder="", tags=None):
    """
    Snapshot the current pose of selected controls, take a viewport playblast,
    and save both as namespace-stripped pose files in the target library/folder.
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return False

    rig_name = get_rig_name()
    pose_dir = get_pose_directory(root_path, rig_name, folder)
    
    json_path = os.path.join(pose_dir, "{}.json".format(name))
    image_path = os.path.join(pose_dir, "{}.png".format(name))

    # 1. Capture pose values
    controls_data = {}
    for node in sel:
        short_name = node.split(":")[-1]
        attrs = cmds.listAttr(node, keyable=True) or []
        controls_data[short_name] = {}
        
        for attr in attrs:
            full = "{}.{}".format(node, attr)
            if cmds.getAttr(full, lock=True):
                continue
            try:
                val = cmds.getAttr(full)
                controls_data[short_name][attr] = val
            except Exception:
                pass

    pose_struct = {
        "name": name,
        "controls": controls_data,
        "thumbnail_path": image_path,
        "timestamp": time.time(),
        "rig_hint": rig_name,
        "tags": tags or []
    }

    try:
        with open(json_path, "w") as f:
            json.dump(pose_struct, f, indent=4)
    except Exception as e:
        cmds.warning("AniSnap: Failed to save pose JSON: {}".format(e))
        return False

    # 2. Viewport snapshot (isolate/hide grid for clean capture)
    try:
        grid_visible = cmds.grid(toggle=True, query=True)
        cmds.grid(toggle=False)

        cmds.playblast(
            frame=cmds.currentTime(query=True),
            format="image",
            compression="png",
            viewer=False,
            showOrnaments=False,
            percent=100,
            widthHeight=(256, 256),
            completeFilename=image_path,
            forceOverwrite=True
        )
        cmds.grid(toggle=grid_visible)
    except Exception:
        pass

    log_debug("AniSnap: Saved pose '{}' ({} controls) in folder '{}'".format(name, len(sel), folder))
    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Saved pose '{}'".format(name),
        pos="topCenter", fade=True, fadeStayTime=1500
    )
    return True


def apply_pose(name, root_path, folder="", blend_factor=1.0, offset_mode=False):
    """Apply a saved pose to selected controls, matching by short names."""
    sel = cmds.ls(selection=True)
    if not sel:
        cmds.warning("AniSnap: Select controls to apply the pose onto.")
        return

    rig_name = get_rig_name()
    pose_dir = get_pose_directory(root_path, rig_name, folder)
    json_path = os.path.join(pose_dir, "{}.json".format(name))

    if not os.path.exists(json_path):
        cmds.warning("AniSnap: Pose file not found: {}".format(json_path))
        return

    try:
        with open(json_path, "r") as f:
            pose_struct = json.load(f)
        pose_data = pose_struct["controls"]
    except Exception as e:
        cmds.warning("AniSnap: Failed to load pose: {}".format(e))
        return

    ns_map = {}
    for node in sel:
        parts = node.split(":")
        short_name = parts[-1]
        ns = ":".join(parts[:-1]) if len(parts) > 1 else ""
        ns_map[short_name] = ns

    with UndoChunk("AniKin: Apply Pose '{}'".format(name)):
        for short_name, attrs in pose_data.items():
            if short_name in ns_map:
                ns = ns_map[short_name]
                node = "{}:{}".format(ns, short_name) if ns else short_name
                
                for attr, target_val in attrs.items():
                    full = "{}.{}".format(node, attr)
                    if cmds.objExists(full) and not cmds.getAttr(full, lock=True):
                        try:
                            curr_val = cmds.getAttr(full)
                            if offset_mode:
                                final_val = curr_val + (target_val * blend_factor)
                            else:
                                final_val = curr_val + (target_val - curr_val) * blend_factor
                            cmds.setAttr(full, final_val)
                        except Exception:
                            pass

    log_debug("AniSnap: Applied pose '{}' (blend: {}, offset: {})".format(name, blend_factor, offset_mode))
    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Applied pose '{}' (Blend: {:.0%})".format(name, blend_factor),
        pos="topCenter", fade=True, fadeStayTime=1200
    )


def mirror_pose(name, root_path, folder=""):
    """Apply a saved pose mirrored across the selected objects."""
    sel = cmds.ls(selection=True)
    if not sel:
        cmds.warning("AniSnap: Select controls to apply mirrored pose.")
        return

    rig_name = get_rig_name()
    pose_dir = get_pose_directory(root_path, rig_name, folder)
    json_path = os.path.join(pose_dir, "{}.json".format(name))

    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, "r") as f:
            pose_struct = json.load(f)
        pose_data = pose_struct["controls"]
    except Exception as e:
        cmds.warning("AniSnap: Failed to mirror pose: {}".format(e))
        return

    ns_map = {}
    for node in sel:
        parts = node.split(":")
        short_name = parts[-1]
        ns = ":".join(parts[:-1]) if len(parts) > 1 else ""
        ns_map[short_name] = ns

    def get_mirrored_name(ctrl_name):
        if ctrl_name.startswith("L_"):
            return "R_" + ctrl_name[2:]
        if ctrl_name.startswith("R_"):
            return "L_" + ctrl_name[2:]
        if ctrl_name.endswith("_L"):
            return ctrl_name[:-2] + "_R"
        if ctrl_name.endswith("_R"):
            return ctrl_name[:-2] + "_L"
        return ctrl_name

    with UndoChunk("AniKin: Mirror Pose '{}'".format(name)):
        for short_name, attrs in pose_data.items():
            mirrored_short_name = get_mirrored_name(short_name)
            if mirrored_short_name in ns_map:
                ns = ns_map[mirrored_short_name]
                node = "{}:{}".format(ns, mirrored_short_name) if ns else mirrored_short_name
                
                for attr, target_val in attrs.items():
                    full = "{}.{}".format(node, attr)
                    if cmds.objExists(full) and not cmds.getAttr(full, lock=True):
                        val = target_val
                        if attr in ["translateX", "rotateY", "rotateZ"]:
                            val = -target_val
                        try:
                            cmds.setAttr(full, val)
                        except Exception:
                            pass


def delete_pose(name, root_path, folder=""):
    """Delete the pose files."""
    rig_name = get_rig_name()
    pose_dir = get_pose_directory(root_path, rig_name, folder)
    json_path = os.path.join(pose_dir, "{}.json".format(name))
    image_path = os.path.join(pose_dir, "{}.png".format(name))

    if os.path.exists(json_path):
        os.remove(json_path)
    if os.path.exists(image_path):
        os.remove(image_path)
    log_debug("AniSnap: Deleted pose '{}'".format(name))


def list_poses(root_path, folder=""):
    """List all saved pose names for the current rig and folder context."""
    rig_name = get_rig_name()
    pose_dir = get_pose_directory(root_path, rig_name, folder)
    if not os.path.exists(pose_dir):
        return []
        
    poses = []
    for f in os.listdir(pose_dir):
        if f.endswith(".json"):
            poses.append(f[:-5])
    return sorted(poses)


def get_pose_image_path(name, root_path, folder=""):
    """Get the path to the thumbnail png of the pose."""
    rig_name = get_rig_name()
    path = os.path.join(get_pose_directory(root_path, rig_name, folder), "{}.png".format(name))
    if os.path.exists(path):
        return path
    return None
