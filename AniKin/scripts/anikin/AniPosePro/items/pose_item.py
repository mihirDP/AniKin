"""
pose_item.py — Pose item implementation for AniPose Pro V3.1.

Handles static pose attribute values, variant presets (A/B/C), and saving/loading of .pose files.
"""

from anikin.AniPosePro.items.base_item import BaseLibraryItem


class PoseItem(BaseLibraryItem):
    """
    Represents a static character pose (.pose).
    """

    ITEM_TYPE = "pose"
    FILE_EXTENSION = ".pose"

    def __init__(self, filepath: str = None, **kwargs):
        self.variants = [] # list of {"name": "A", "controls": {...}}
        self.active_variant_index = 0
        super(PoseItem, self).__init__(filepath=filepath, **kwargs)

    def to_dict(self) -> dict:
        d = super(PoseItem, self).to_dict()
        d["type"] = "pose"
        d["controls"] = self.data
        d["variants"] = self.variants
        return d

    def load(self, filepath: str):
        super(PoseItem, self).load(filepath)
        # Check controls field vs data
        with open(filepath, "r", encoding="utf-8") as f:
            import json
            content = json.load(f)
        if "controls" in content:
            self.data = content["controls"]
        self.variants = content.get("variants", [])

    def add_variant(self, variant_name: str, controls_data: dict):
        """Adds a named variant to this pose."""
        self.variants.append({
            "name": variant_name,
            "controls": controls_data
        })

    def get_active_controls(self) -> dict:
        if self.variants and 0 <= self.active_variant_index < len(self.variants):
            return self.variants[self.active_variant_index].get("controls", self.data)
        return self.data
