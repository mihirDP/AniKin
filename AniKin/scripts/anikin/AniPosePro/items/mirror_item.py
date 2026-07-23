"""
mirror_item.py — Mirror Table library item for AniPose Pro V3.1.
"""

from anikin.AniPosePro.items.base_item import BaseLibraryItem


class MirrorItem(BaseLibraryItem):
    ITEM_TYPE = "mirror"
    FILE_EXTENSION = ".mirror"

    def __init__(self, filepath: str = None, **kwargs):
        self.pairs = []
        self.center_controls = []
        super(MirrorItem, self).__init__(filepath=filepath, **kwargs)

    def to_dict(self) -> dict:
        d = super(MirrorItem, self).to_dict()
        d["type"] = "mirror"
        d["pairs"] = self.pairs
        d["center_controls"] = self.center_controls
        return d

    def load(self, filepath: str):
        super(MirrorItem, self).load(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            import json
            content = json.load(f)
        self.pairs = content.get("pairs", [])
        self.center_controls = content.get("center_controls", [])
