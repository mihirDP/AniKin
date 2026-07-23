"""
clip_item.py — AniCapture Clip item for AniPose Pro V3.1.
"""

from anikin.AniPosePro.items.base_item import BaseLibraryItem


class ClipItem(BaseLibraryItem):
    """
    Represents an animation clip (.clip or .animclip_v2).
    """

    ITEM_TYPE = "animclip"
    FILE_EXTENSION = ".clip"

    def __init__(self, filepath: str = None, **kwargs):
        self.start_frame = 1.0
        self.end_frame = 24.0
        self.duration = 24.0
        self.fps = 24.0
        super(ClipItem, self).__init__(filepath=filepath, **kwargs)

    def to_dict(self) -> dict:
        d = super(ClipItem, self).to_dict()
        d["type"] = "animclip"
        d["start"] = self.start_frame
        d["end"] = self.end_frame
        d["duration"] = self.duration
        d["fps"] = self.fps
        d["controls"] = self.data
        return d

    def load(self, filepath: str):
        super(ClipItem, self).load(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            import json
            content = json.load(f)
        self.start_frame = content.get("start", 1.0)
        self.end_frame = content.get("end", 24.0)
        self.duration = content.get("duration", content.get("frame_count", 24.0))
        self.fps = content.get("fps", 24.0)
        if "controls" in content:
            self.data = content["controls"]
