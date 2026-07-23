"""
pose_library.py — Core pose library I/O for AniPose Pro.

Handles save, load, list, delete and overwrite of .pose files.
Each pose is stored as JSON + a .meta.json sidecar + a .thumb.jpg thumbnail.
All disk writes are atomic-safe (writes to temp, then os.replace).
"""

import os
import re
import json
import shutil
import datetime
import getpass

POSE_EXT      = ".pose"
META_EXT      = ".meta.json"
THUMB_EXT     = ".thumb.jpg"
ANIMCLIP_EXT  = ".animclip"
VERSIONS_DIR  = ".versions"
CONFIG_FILE   = "config.json"


class PoseLibrary:
    """
    Manages a single library root directory.
    A user can have multiple PoseLibrary instances (local + shared).
    """

    def __init__(self, root_path=None, name="Local"):
        self.name = name
        if root_path is None:
            # Default library location
            user_dir = os.path.expanduser("~")
            root_path = os.path.join(user_dir, "AniPoseLibrary")
        self.root = os.path.normpath(root_path)
        os.makedirs(self.root, exist_ok=True)
        self._ensure_config()

    # ── Config ─────────────────────────────────────────────────────────────────

    def _ensure_config(self):
        cfg_path = os.path.join(self.root, CONFIG_FILE)
        if not os.path.exists(cfg_path):
            _write_json(cfg_path, {
                "name": self.name,
                "superusers": [],
                "version": "2.0"
            })

    def get_config(self):
        cfg_path = os.path.join(self.root, CONFIG_FILE)
        return _read_json(cfg_path) if os.path.exists(cfg_path) else {}

    # ── SAVE ───────────────────────────────────────────────────────────────────

    def save_pose(self, nodes, name, folder="", tags=None, author=None,
                  project=None, notes="", is_additive=False, delta_source=None,
                  rating=0, favourite=False):
        """
        Save a pose from the current Maya scene values of `nodes`.
        """
        import maya.cmds as cmds  # deferred — so module loads without Maya

        folder_path = os.path.join(self.root, folder) if folder else self.root
        os.makedirs(folder_path, exist_ok=True)

        safe = _safe_filename(name)
        pose_path  = os.path.join(folder_path, safe + POSE_EXT)
        meta_path  = os.path.join(folder_path, safe + META_EXT)
        thumb_path = os.path.join(folder_path, safe + THUMB_EXT)

        controls, namespace = _capture_values(nodes, cmds,
                                              is_additive=is_additive,
                                              delta_source=delta_source)

        pose_data = {
            "anikin_version": "2.0",
            "format": "pose",
            "captured_at": _now_iso(),
            "rig_namespace": namespace,
            "controls": controls,
        }
        _write_json_atomic(pose_path, pose_data)

        meta_data = {
            "name": name,
            "rig": namespace,
            "author": author or _get_user(),
            "project": project or "",
            "tags": tags or [],
            "notes": notes,
            "is_additive": is_additive,
            "variant_of": None,
            "rating": rating,
            "favourite": favourite,
        }
        _write_json_atomic(meta_path, meta_data)

        # Non-fatal thumbnail capture
        try:
            from anikin.AniPosePro.core.thumbnail import capture_thumbnail
            capture_thumbnail(thumb_path, width=256, height=256)
        except Exception:
            pass

        return pose_path

    # ── OVERWRITE ─────────────────────────────────────────────────────────────

    def overwrite_pose(self, pose_path, nodes, **kwargs):
        folder = os.path.dirname(pose_path)
        versions_dir = os.path.join(folder, VERSIONS_DIR)
        os.makedirs(versions_dir, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        base = os.path.splitext(os.path.basename(pose_path))[0]
        shutil.copy2(pose_path, os.path.join(versions_dir, "{}_{}{}".format(base, ts, POSE_EXT)))

        existing_meta_path = pose_path.replace(POSE_EXT, META_EXT)
        if os.path.exists(existing_meta_path):
            existing_meta = _read_json(existing_meta_path)
            kwargs.setdefault("name", existing_meta.get("name", base))
            kwargs.setdefault("tags", existing_meta.get("tags", []))
            kwargs.setdefault("notes", existing_meta.get("notes", ""))
            kwargs.setdefault("rating", existing_meta.get("rating", 0))
            kwargs.setdefault("favourite", existing_meta.get("favourite", False))

        folder_rel = os.path.relpath(folder, self.root)
        return self.save_pose(nodes, folder=folder_rel, **kwargs)

    # ── LOAD ──────────────────────────────────────────────────────────────────

    def load_pose_data(self, pose_path):
        pose = _read_json(pose_path)
        meta_path = pose_path.replace(POSE_EXT, META_EXT)
        meta = _read_json(meta_path) if os.path.exists(meta_path) else {}
        return pose, meta

    # ── LIST ──────────────────────────────────────────────────────────────────

    def list_poses(self, folder="", search=None, tags=None,
                   sort_by="name", favourites_first=False):
        scan_root = os.path.join(self.root, folder) if folder else self.root
        results = []

        for dirpath, dirnames, files in os.walk(scan_root):
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d != VERSIONS_DIR]
            for fname in files:
                if not fname.endswith(POSE_EXT):
                    continue
                pose_path  = os.path.join(dirpath, fname)
                meta_path  = pose_path.replace(POSE_EXT, META_EXT)
                thumb_path = pose_path.replace(POSE_EXT, THUMB_EXT)

                meta = _read_json(meta_path) if os.path.exists(meta_path) else {}

                if search and search.lower() not in meta.get("name", fname).lower():
                    continue
                if tags and not any(t in meta.get("tags", []) for t in tags):
                    continue

                results.append({
                    "path":  pose_path,
                    "name":  meta.get("name", fname),
                    "thumb": thumb_path if os.path.exists(thumb_path) else None,
                    "meta":  meta,
                })

        if favourites_first:
            results.sort(key=lambda e: (not e["meta"].get("favourite", False),))
        if sort_by == "name":
            results.sort(key=lambda e: e["name"].lower())
        elif sort_by == "date":
            results.sort(key=lambda e: e["meta"].get("captured_at", ""), reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda e: e["meta"].get("rating", 0), reverse=True)

        return results

    def list_clips(self, folder=""):
        scan_root = os.path.join(self.root, folder) if folder else self.root
        results = []
        for dirpath, dirnames, files in os.walk(scan_root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fname in files:
                if not fname.endswith(ANIMCLIP_EXT) and not fname.endswith(".clip"):
                    continue
                clip_path = os.path.join(dirpath, fname)
                meta_path = clip_path.rsplit(".", 1)[0] + META_EXT
                meta = _read_json(meta_path) if os.path.exists(meta_path) else {}
                
                thumb_path = clip_path.rsplit(".", 1)[0] + ".gif"
                if not os.path.exists(thumb_path):
                    thumb_path = clip_path.rsplit(".", 1)[0] + ".jpg"
                    
                results.append({
                    "path": clip_path, 
                    "name": meta.get("name", fname), 
                    "thumb": thumb_path if os.path.exists(thumb_path) else None,
                    "meta": meta
                })
        return results

    def list_folders(self):
        folders = []
        for dirpath, dirnames, _ in os.walk(self.root):
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d != VERSIONS_DIR]
            for d in dirnames:
                rel = os.path.relpath(os.path.join(dirpath, d), self.root)
                folders.append(rel)
        return folders

    def create_folder(self, rel_path):
        os.makedirs(os.path.join(self.root, rel_path), exist_ok=True)

    def rename_folder(self, old_rel, new_rel):
        shutil.move(os.path.join(self.root, old_rel),
                    os.path.join(self.root, new_rel))

    # ── DELETE ────────────────────────────────────────────────────────────────

    def delete_pose(self, pose_path, archive=True):
        folder = os.path.dirname(pose_path)
        versions_dir = os.path.join(folder, VERSIONS_DIR)
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

        if archive:
            os.makedirs(versions_dir, exist_ok=True)
            for ext in [POSE_EXT, META_EXT, THUMB_EXT]:
                src = pose_path.replace(POSE_EXT, ext)
                if os.path.exists(src):
                    dst = os.path.join(versions_dir,
                                       "deleted_{}_{}".format(ts, os.path.basename(src)))
                    shutil.move(src, dst)
        else:
            for ext in [POSE_EXT, META_EXT, THUMB_EXT]:
                p = pose_path.replace(POSE_EXT, ext)
                if os.path.exists(p):
                    os.remove(p)

    # ── META HELPERS ──────────────────────────────────────────────────────────

    def update_meta(self, pose_path, **fields):
        meta_path = pose_path.replace(POSE_EXT, META_EXT)
        meta = _read_json(meta_path) if os.path.exists(meta_path) else {}
        meta.update(fields)
        _write_json_atomic(meta_path, meta)

    def set_favourite(self, pose_path, state):
        self.update_meta(pose_path, favourite=bool(state))

    def set_rating(self, pose_path, stars):
        self.update_meta(pose_path, rating=max(0, min(5, int(stars))))

    def rename_pose(self, pose_path, new_name):
        folder = os.path.dirname(pose_path)
        safe = _safe_filename(new_name)
        new_base = os.path.join(folder, safe)
        for ext in [POSE_EXT, META_EXT, THUMB_EXT]:
            src = pose_path.replace(POSE_EXT, ext)
            if os.path.exists(src):
                shutil.move(src, new_base + ext)
        self.update_meta(new_base + POSE_EXT, name=new_name)
        return new_base + POSE_EXT


def _safe_filename(name):
    return re.sub(r"[^\w\-]", "_", name).lower()

def _now_iso():
    return datetime.datetime.now().isoformat()

def _get_user():
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"

def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _write_json_atomic(path, data):
    tmp = path + ".tmp"
    _write_json(tmp, data)
    os.replace(tmp, path)

def _capture_values(nodes, cmds, is_additive=False, delta_source=None):
    controls = {}
    namespace = ""

    for node in nodes:
        short = node.split("|")[-1]
        if ":" in short:
            if not namespace:
                namespace = short.split(":")[0]
            ctrl_key = ":".join(short.split(":")[1:])
        else:
            ctrl_key = short

        controls[ctrl_key] = {}
        keyable = cmds.listAttr(node, keyable=True) or []

        for attr in keyable:
            full = "{}.{}".format(node, attr)
            try:
                if cmds.getAttr(full, lock=True):
                    continue
                val = cmds.getAttr(full)
                if isinstance(val, list):
                    continue
                if is_additive and delta_source:
                    base = (delta_source.get(ctrl_key) or {}).get(attr, 0.0)
                    val = val - base
                controls[ctrl_key][attr] = val
            except Exception:
                pass

    return controls, namespace
