"""
pose_blender.py — Live pose blending for AniPose Pro V3.1.

Supports:
1. Single pose live blending (Original rig state <-> Saved Pose)
2. Dual pose morphing (Pose A <-> Pose B)
3. Partial attribute filtering
4. Real-time MMB viewport dragging
"""

import maya.cmds as cmds


class PoseBlender(object):
    """
    Manages live blend state between current rig state and target pose.
    Takes snapshot on initialization and applies linear interpolation on blend(t).
    t: 0.0 (original) to 1.0 (target pose)
    """

    def __init__(self, pose_data: dict, selection: list = None,
                 namespace_resolver=None, channels_filter: dict = None):
        self._selection = selection or cmds.ls(selection=True, long=True) or []
        self._target_controls = pose_data.get("controls", {}) if pose_data else {}
        self._ns_resolver = namespace_resolver
        self._channels_filter = channels_filter or {
            "translate": True, "rotate": True, "scale": True, "custom": True
        }

        self._resolved_map = {} # saved_ctrl -> scene_node
        self._snapshot_data = self._take_snapshot()

    def _take_snapshot(self) -> dict:
        snap = {}
        if not self._target_controls:
            return snap

        for ctrl_key, attrs in self._target_controls.items():
            resolved = None
            if self._ns_resolver:
                resolved = self._ns_resolver.resolve(ctrl_key)
            else:
                # Basic resolve fallback
                if cmds.objExists(ctrl_key):
                    resolved = ctrl_key
                else:
                    # Match by shortname against selection
                    for sel in self._selection:
                        short = sel.split("|")[-1]
                        base = short.split(":")[-1] if ":" in short else short
                        if base == ctrl_key or short == ctrl_key:
                            resolved = sel
                            break

            if not resolved or not cmds.objExists(resolved):
                continue

            self._resolved_map[ctrl_key] = resolved
            snap[ctrl_key] = {}

            for attr in attrs.keys():
                if not self._is_attr_allowed(attr):
                    continue
                full_plug = f"{resolved}.{attr}"
                if cmds.objExists(full_plug):
                    try:
                        snap[ctrl_key][attr] = cmds.getAttr(full_plug)
                    except Exception:
                        pass
        return snap

    def _is_attr_allowed(self, attr: str) -> bool:
        if attr.startswith("translate"):
            return self._channels_filter.get("translate", True)
        if attr.startswith("rotate"):
            return self._channels_filter.get("rotate", True)
        if attr.startswith("scale"):
            return self._channels_filter.get("scale", True)
        return self._channels_filter.get("custom", True)

    def blend(self, t: float):
        """
        Apply blended attribute values to scene.
        t = 0.0 (original) to 1.0 (full target pose)
        """
        t = max(0.0, min(1.0, float(t)))

        for ctrl_key, target_attrs in self._target_controls.items():
            scene_node = self._resolved_map.get(ctrl_key)
            if not scene_node or not cmds.objExists(scene_node):
                continue

            orig_attrs = self._snapshot_data.get(ctrl_key, {})

            for attr, target_val in target_attrs.items():
                if not self._is_attr_allowed(attr):
                    continue
                if attr not in orig_attrs:
                    continue

                orig_val = orig_attrs[attr]
                if isinstance(target_val, (int, float)) and isinstance(orig_val, (int, float)):
                    blended = orig_val + (target_val - orig_val) * t
                    try:
                        cmds.setAttr(f"{scene_node}.{attr}", blended)
                    except Exception:
                        pass


class DualPoseBlender(object):
    """
    Morphs between Pose A and Pose B in real time.
    t = 0.0 (Pose A) to 1.0 (Pose B)
    """

    def __init__(self, pose_a: dict, pose_b: dict, selection: list = None,
                 namespace_resolver=None):
        self._pose_a = pose_a.get("controls", {}) if pose_a else {}
        self._pose_b = pose_b.get("controls", {}) if pose_b else {}
        self._selection = selection or cmds.ls(selection=True, long=True) or []
        self._ns_resolver = namespace_resolver

    def blend(self, t: float):
        t = max(0.0, min(1.0, float(t)))
        all_ctrls = set(self._pose_a.keys()).union(set(self._pose_b.keys()))

        for ctrl_key in all_ctrls:
            scene_node = ctrl_key
            if self._ns_resolver:
                scene_node = self._ns_resolver.resolve(ctrl_key)

            if not cmds.objExists(scene_node):
                continue

            attrs_a = self._pose_a.get(ctrl_key, {})
            attrs_b = self._pose_b.get(ctrl_key, {})
            all_attrs = set(attrs_a.keys()).union(set(attrs_b.keys()))

            for attr in all_attrs:
                val_a = attrs_a.get(attr)
                val_b = attrs_b.get(attr)

                if val_a is None or val_b is None:
                    continue

                if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                    blended = val_a + (val_b - val_a) * t
                    try:
                        cmds.setAttr(f"{scene_node}.{attr}", blended)
                    except Exception:
                        pass
