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
    Returns (imported_poses_count, imported_clips_count).
    """
    if not os.path.exists(src_folder):
        cmds.warning(f"Studio Library Importer: Directory not found — {src_folder}")
        return 0, 0

    os.makedirs(dest_folder, exist_ok=True)

    pose_count = 0
    clip_count = 0

    for root, dirs, files in os.walk(src_folder):
        rel = os.path.relpath(root, src_folder)
        target_dir = os.path.join(dest_folder, rel) if rel != "." else dest_folder
        os.makedirs(target_dir, exist_ok=True)

        for file in files:
            full_src = os.path.join(root, file)
            base, ext = os.path.splitext(file)

            if ext == ".pose" or file.endswith(".pose.json") or (ext == ".json" and "pose" in file.lower()):
                if convert_sl_pose(full_src, target_dir):
                    pose_count += 1
            elif ext in [".anim", ".clip"] or file.endswith(".anim.json"):
                if convert_sl_anim(full_src, target_dir):
                    clip_count += 1
            elif ext in [".jpg", ".png", ".gif"]:
                shutil.copy(full_src, os.path.join(target_dir, file))

    cmds.inViewMessage(
        amg=f"<hl>Studio Library Importer</hl>: Imported {pose_count} poses, {clip_count} clips.",
        pos="topCenter", fade=True, fadeStayTime=2000
    )
    return pose_count, clip_count


def convert_sl_pose(src_path: str, dest_dir: str) -> bool:
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        name = data.get("name", os.path.splitext(os.path.basename(src_path))[0])
        out_path = os.path.join(dest_dir, f"{name}.pose")

        controls = data.get("objects", data.get("controls", {}))

        anipose_data = {
            "version": 2,
            "type": "pose",
            "name": name,
            "author": data.get("author", "Studio Library Import"),
            "created": data.get("created", ""),
            "tags": data.get("tags", ["studiolibrary"]),
            "color": "#3a9e6e",
            "rating": 0,
            "notes": data.get("comment", ""),
            "controls": controls
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(anipose_data, f, indent=4)
        return True
    except Exception as e:
        cmds.warning(f"Studio Library Importer: Failed converting {src_path} — {e}")
        return False


def convert_sl_anim(src_path: str, dest_dir: str) -> bool:
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        name = data.get("name", os.path.splitext(os.path.basename(src_path))[0])
        out_path = os.path.join(dest_dir, f"{name}.clip")

        controls = data.get("objects", data.get("controls", {}))
        start = data.get("start", 1.0)
        end = data.get("end", 24.0)

        anipose_data = {
            "version": 2,
            "type": "animclip",
            "name": name,
            "start": start,
            "end": end,
            "duration": end - start + 1,
            "frame_count": int(end - start + 1),
            "fps": data.get("fps", 24.0),
            "tags": data.get("tags", ["studiolibrary"]),
            "color": "#d4860a",
            "controls": controls
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(anipose_data, f, indent=4)
        return True
    except Exception as e:
        cmds.warning(f"Studio Library Importer: Failed converting anim {src_path} — {e}")
        return False
