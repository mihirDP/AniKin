"""
index_cache.py — Fast Library Index Cache for AniPose Pro V3.1.

Scans the library root for .pose, .clip, .animclip, .mirror, .aniscript, .selection
files and builds a searchable in-memory index. Also reads .meta.json sidecars
for metadata (name, tags, rating, author, etc.) and locates thumbnails.
"""

import os
import json
import time


INDEX_FILE_NAME = ".anipose_library_meta.json"


class LibraryIndexCache(object):
    """
    Builds, loads, and updates the fast search index cache.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.index_path = os.path.join(root_dir, INDEX_FILE_NAME) if root_dir else ""
        self.items = []  # list of dicts

    def build_or_load(self, force_rebuild: bool = False) -> list:
        if not self.root_dir or not os.path.exists(self.root_dir):
            self.items = []
            return self.items

        if not force_rebuild and os.path.exists(self.index_path):
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.items = data.get("items", [])
                    return self.items
            except Exception:
                pass

        return self.rebuild()

    def rebuild(self) -> list:
        """Scans disk recursively and builds index."""
        if not self.root_dir or not os.path.exists(self.root_dir):
            self.items = []
            return self.items

        valid_exts = {".pose", ".clip", ".animclip_v2", ".animclip", ".mirror", ".aniscript", ".selection"}
        found_items = []

        for root, dirs, files in os.walk(self.root_dir):
            # Skip hidden, version, and temp directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != ".versions" and "_tmp_" not in d]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_exts:
                    full_path = os.path.join(root, file)
                    entry = self._extract_item_summary(full_path)
                    if entry:
                        found_items.append(entry)

        self.items = found_items
        self.save()
        return self.items

    def save(self):
        if not self.index_path:
            return
        data = {
            "version": 2,
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(self.items),
            "items": self.items
        }
        try:
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _extract_item_summary(self, filepath: str) -> dict:
        """
        Read an item file AND its .meta.json sidecar to build a unified
        index entry. The sidecar takes priority for display metadata.
        """
        try:
            # Read the main data file
            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
        except Exception:
            content = {}

        # Determine item type from extension
        ext = os.path.splitext(filepath)[1].lower()
        if ext in [".clip", ".animclip_v2", ".animclip"]:
            itype = "clip"
        elif ext == ".pose":
            itype = "pose"
        elif ext == ".mirror":
            itype = "mirror"
        elif ext == ".aniscript":
            itype = "script"
        elif ext == ".selection":
            itype = "selection"
        else:
            itype = content.get("type", "pose")

        # Read the .meta.json sidecar (contains name, tags, rating, author, etc.)
        base_no_ext = os.path.splitext(filepath)[0]
        meta = {}
        for meta_ext in [".meta.json", ".meta"]:
            meta_path = base_no_ext + meta_ext
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass
                break

        # Merge: sidecar metadata takes priority, then main file content
        merged = {}
        merged.update(content)
        merged.update(meta)

        rel_path = os.path.relpath(filepath, self.root_dir)

        # Find thumbnail: try .gif, .thumb.gif, .jpg, .thumb.jpg, .png
        thumb = ""
        for t_ext in [".thumb.gif", ".gif", ".thumb.jpg", ".jpg", ".png"]:
            cand = base_no_ext + t_ext
            if os.path.exists(cand):
                thumb = cand
                break

        # Extract name: sidecar > content > filename
        basename_clean = os.path.splitext(os.path.basename(filepath))[0]
        name = merged.get("name", basename_clean)

        return {
            "name": name,
            "type": itype,
            "path": filepath,
            "rel_path": rel_path,
            "folder": os.path.dirname(rel_path),
            "author": merged.get("author", ""),
            "rig_hint": merged.get("rig_hint", merged.get("rig", merged.get("rig_namespace", ""))),
            "tags": merged.get("tags", []),
            "rating": merged.get("rating", 0),
            "color": merged.get("color", "#3a9e6e"),
            "notes": merged.get("notes", ""),
            "favorite": merged.get("favorite", merged.get("favourite", False)),
            "created": merged.get("captured_at", merged.get("date", merged.get("created", ""))),
            "duration": merged.get("frame_count", merged.get("duration", 0)),
            "fps": merged.get("fps", ""),
            "thumbnail": thumb,
            "meta": merged,
        }
