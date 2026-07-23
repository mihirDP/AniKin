"""
base_item.py — Base item class for AniPose Pro V3.1 library elements.
"""

import os
import json
import datetime


class BaseLibraryItem(object):
    """
    Base representation of any item in the AniPose Pro library.
    """

    ITEM_TYPE = "base"
    FILE_EXTENSION = ".meta"

    def __init__(self, filepath: str = None, name: str = "", tags: list = None,
                 color: str = "#3a9e6e", rating: int = 0, notes: str = "",
                 author: str = "", rig_hint: str = ""):
        self.filepath = filepath or ""
        self.name = name or (os.path.splitext(os.path.basename(filepath))[0] if filepath else "")
        self.tags = tags or []
        self.color = color or "#3a9e6e"
        self.rating = int(rating)
        self.notes = notes or ""
        self.author = author or ""
        self.rig_hint = rig_hint or ""
        self.is_favorite = False
        self.created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.data = {}

        if filepath and os.path.exists(filepath):
            self.load(filepath)

    @property
    def thumbnail_path(self) -> str:
        if not self.filepath:
            return ""
        base = os.path.splitext(self.filepath)[0]
        for ext in [".gif", ".jpg", ".png", ".thumb.jpg"]:
            cand = base + ext
            if os.path.exists(cand):
                return cand
        return ""

    def to_dict(self) -> dict:
        return {
            "version": 2,
            "type": self.ITEM_TYPE,
            "name": self.name,
            "author": self.author,
            "rig_hint": self.rig_hint,
            "created": self.created_at,
            "tags": self.tags,
            "color": self.color,
            "rating": self.rating,
            "notes": self.notes,
            "favorite": self.is_favorite,
            "data": self.data
        }

    def save(self, filepath: str = None):
        target_path = filepath or self.filepath
        if not target_path:
            raise ValueError("No filepath specified for save.")

        self.filepath = target_path
        out_dir = os.path.dirname(target_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)

    def load(self, filepath: str):
        self.filepath = filepath
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)

        self.name = content.get("name", self.name)
        self.author = content.get("author", self.author)
        self.rig_hint = content.get("rig_hint", self.rig_hint)
        self.created_at = content.get("created", self.created_at)
        self.tags = content.get("tags", self.tags)
        self.color = content.get("color", self.color)
        self.rating = content.get("rating", self.rating)
        self.notes = content.get("notes", self.notes)
        self.is_favorite = content.get("favorite", False)
        self.data = content.get("data", content.get("controls", {}))
