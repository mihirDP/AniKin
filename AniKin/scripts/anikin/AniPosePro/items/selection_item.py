"""
selection_item.py — SelectionSet item for AniPose Pro V3.1.
"""

import maya.cmds as cmds
from anikin.AniPosePro.items.base_item import BaseLibraryItem


class SelectionItem(BaseLibraryItem):
    ITEM_TYPE = "selection"
    FILE_EXTENSION = ".selection"

    def __init__(self, filepath: str = None, objects: list = None, **kwargs):
        self.objects = objects or []
        super(SelectionItem, self).__init__(filepath=filepath, **kwargs)

    def to_dict(self) -> dict:
        d = super(SelectionItem, self).to_dict()
        d["type"] = "selection"
        d["objects"] = self.objects
        return d

    def load(self, filepath: str):
        super(SelectionItem, self).load(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            import json
            content = json.load(f)
        self.objects = content.get("objects", [])

    def select(self, add: bool = False, namespace_resolver = None):
        """Recalls the selection set into Maya viewport."""
        target_nodes = []
        for obj in self.objects:
            resolved = obj
            if namespace_resolver:
                resolved = namespace_resolver.resolve(obj)
            if cmds.objExists(resolved):
                target_nodes.append(resolved)

        if target_nodes:
            cmds.select(target_nodes, add=add)
            cmds.inViewMessage(
                amg=f"<hl>AniPose Pro</hl>: Selected {len(target_nodes)} objects from '{self.name}'",
                pos="topCenter", fade=True, fadeStayTime=1500
            )
        else:
            cmds.warning(f"AniPose Pro: No matching objects found for selection set '{self.name}'.")
