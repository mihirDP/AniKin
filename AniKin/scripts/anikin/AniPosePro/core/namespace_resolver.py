"""
namespace_resolver.py — Automatic Namespace Resolution for AniPose Pro V3.1.

Resolves stored control names from library files onto current scene rigs using:
- 'from_file': exact saved names
- 'from_selection': auto-detect namespace of selected viewport controls
- 'custom': user specified namespace prefix
"""

import maya.cmds as cmds


class NamespaceResolver(object):
    """
    Resolves saved control names to matching scene objects.
    """

    def __init__(self, mode: str = "from_selection", custom_ns: str = ""):
        self.mode = mode
        self.custom_ns = custom_ns
        self._cached_scene_ns = None

    def resolve(self, ctrl_name: str) -> str:
        """
        Resolves ctrl_name (e.g. 'Malcolm_01:L_foot_IK_CTL') according to mode.
        """
        stored_ns, base_name = self.split_namespace(ctrl_name)

        if self.mode == "from_file":
            return ctrl_name

        elif self.mode == "from_selection":
            scene_ns = self.detect_scene_namespace()
            if scene_ns:
                resolved = f"{scene_ns}:{base_name}"
                if cmds.objExists(resolved):
                    return resolved
            # Fallback to base_name
            if cmds.objExists(base_name):
                return base_name
            # Fallback to exact stored name if scene matches
            if cmds.objExists(ctrl_name):
                return ctrl_name
            return resolved if scene_ns else base_name

        elif self.mode == "custom":
            if self.custom_ns:
                return f"{self.custom_ns}:{base_name}"
            return base_name

        return ctrl_name

    @staticmethod
    def split_namespace(ctrl_name: str) -> tuple:
        parts = ctrl_name.rsplit(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return "", ctrl_name

    def detect_scene_namespace(self) -> str:
        """
        Detects namespace from selected objects or scene.
        """
        if self._cached_scene_ns is not None:
            return self._cached_scene_ns

        sel = cmds.ls(selection=True, long=True) or []
        for obj in sel:
            short = cmds.ls(obj, shortNames=True)[0]
            if ":" in short:
                self._cached_scene_ns = short.rsplit(":", 1)[0]
                return self._cached_scene_ns

        # Fallback to scene namespaces
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []
        skip_ns = {"UI", "shared"}
        valid_ns = [n for n in namespaces if n not in skip_ns]

        if valid_ns:
            self._cached_scene_ns = valid_ns[0]
            return self._cached_scene_ns

        self._cached_scene_ns = ""
        return ""
