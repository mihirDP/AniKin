"""
studiolibrary_importer.py — Studio Library Compatibility Importer for AniPose Pro V3.1.
Reads Studio Library .pose and .anim folders and imports them into AniPose Pro format.
"""

import os
import json
import shutil
import maya.cmds as cmds


def import_studiolibrary_folder(src_folder: str, dest_folder: str) -> tuple:
    """
    Imports all Studio Library items from src_folder to dest_folder.
    Properly parses SL's .pose and .anim folder structures into AniPose single files.
    Returns (imported_poses_count, imported_clips_count).
    """
    if not os.path.exists(src_folder):
        cmds.warning(f"Studio Library Importer: Directory not found — {src_folder}")
        return 0, 0

    os.makedirs(dest_folder, exist_ok=True)

    pose_count = 0
    clip_count = 0

    for root, dirs, files in os.walk(src_folder):
        # We don't want to walk inside .pose or .anim folders as we process them entirely when we see them
        sl_item_dirs = [d for d in dirs if d.endswith(".pose") or d.endswith(".anim") or d.endswith(".clip")]
        dirs[:] = [d for d in dirs if d not in sl_item_dirs and not d.startswith(".")]

        rel = os.path.relpath(root, src_folder)
        target_dir = os.path.join(dest_folder, rel) if rel != "." else dest_folder
        os.makedirs(target_dir, exist_ok=True)

        for d in sl_item_dirs:
            full_src_dir = os.path.join(root, d)
            item_name = os.path.splitext(d)[0]
            
            # Find JSON and Thumbnail
            json_file = None
            thumb_file = None
            for f in os.listdir(full_src_dir):
                if f.endswith(".json"):
                    json_file = os.path.join(full_src_dir, f)
                elif f.endswith(".jpg") or f.endswith(".png") or f.endswith(".gif"):
                    if not thumb_file or "thumbnail" in f.lower():
                        thumb_file = os.path.join(full_src_dir, f)

            if not json_file:
                continue

            if d.endswith(".pose"):
                if convert_sl_pose(json_file, target_dir, item_name):
                    pose_count += 1
                    if thumb_file:
                        ext = os.path.splitext(thumb_file)[1]
                        shutil.copy(thumb_file, os.path.join(target_dir, f"{item_name}{ext}"))
            else:
                if convert_sl_anim(json_file, target_dir, item_name):
                    clip_count += 1
                    if thumb_file:
                        ext = os.path.splitext(thumb_file)[1]
                        shutil.copy(thumb_file, os.path.join(target_dir, f"{item_name}{ext}"))

    cmds.inViewMessage(
        amg=f"<hl>Studio Library Importer</hl>: Imported {pose_count} poses, {clip_count} clips.",
        pos="topCenter", fade=True, fadeStayTime=2000
    )
    return pose_count, clip_count


def convert_sl_pose(src_json: str, dest_dir: str, item_name: str) -> bool:
    try:
        with open(src_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        out_path = os.path.join(dest_dir, f"{item_name}.pose")
        controls = data.get("objects", data.get("controls", {}))

        anipose_data = {
            "version": 2,
            "type": "pose",
            "name": item_name,
            "author": data.get("author", "Studio Library Import"),
            "created": data.get("created", ""),
            "tags": data.get("tags", ["studiolibrary"]),
            "color": "#2FD3C2",
            "rating": 0,
            "notes": data.get("comment", ""),
            "controls": controls
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(anipose_data, f, indent=4)
        return True
    except Exception as e:
        cmds.warning(f"Studio Library Importer: Failed converting {src_json} — {e}")
        return False


def convert_sl_anim(src_json: str, dest_dir: str, item_name: str) -> bool:
    try:
        with open(src_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        out_path = os.path.join(dest_dir, f"{item_name}.clip")
        controls = data.get("objects", data.get("controls", {}))
        start = data.get("start", 1.0)
        end = data.get("end", 24.0)

        anipose_data = {
            "version": 2,
            "type": "animclip",
            "name": item_name,
            "start": start,
            "end": end,
            "duration": end - start + 1,
            "frame_count": int(end - start + 1),
            "fps": data.get("fps", 24.0),
            "tags": data.get("tags", ["studiolibrary"]),
            "color": "#C9A227",
            "controls": controls
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(anipose_data, f, indent=4)
        return True
    except Exception as e:
        cmds.warning(f"Studio Library Importer: Failed converting anim {src_json} — {e}")
        return False
