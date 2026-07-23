"""
script_item.py — AniScript Python execution item for AniPose Pro V3.1.
"""

import maya.cmds as cmds
from anikin.AniPosePro.items.base_item import BaseLibraryItem


class ScriptItem(BaseLibraryItem):
    ITEM_TYPE = "aniscript"
    FILE_EXTENSION = ".aniscript"

    def __init__(self, filepath: str = None, script_code: str = "", **kwargs):
        self.script_code = script_code
        super(ScriptItem, self).__init__(filepath=filepath, **kwargs)

    def to_dict(self) -> dict:
        d = super(ScriptItem, self).to_dict()
        d["type"] = "aniscript"
        d["script"] = self.script_code
        return d

    def load(self, filepath: str):
        super(ScriptItem, self).load(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            import json
            content = json.load(f)
        self.script_code = content.get("script", "")

    def execute(self):
        """Executes the Python script code in Maya's environment."""
        if not self.script_code:
            cmds.warning("AniPose Pro: Script is empty.")
            return

        try:
            exec(self.script_code, {"cmds": cmds})
            cmds.inViewMessage(
                amg=f"<hl>AniScript</hl>: Executed '{self.name}' successfully",
                pos="topCenter", fade=True, fadeStayTime=1500
            )
        except Exception as e:
            cmds.warning(f"AniPose Pro: Script execution failed — {e}")
