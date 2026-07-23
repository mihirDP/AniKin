"""
mirror_table.py — Mirror Table Management and Auto-Detection for AniPose Pro V3.1.

Defines L/R control mappings and mirror axes for rigs.
Saves to .mirror files.
"""

import os
import json
import maya.cmds as cmds


DEFAULT_LR_PATTERNS = [
    ("_L", "_R"), ("_R", "_L"),
    ("_L_", "_R_"), ("_R_", "_L_"),
    ("Left", "Right"), ("Right", "Left"),
    ("left", "right"), ("right", "left"),
    ("l_", "r_"), ("r_", "l_"),
    ("Lft", "Rgt"), ("Rgt", "Lft"),
    (":L_", ":R_"), (":R_", ":L_"),
]


class MirrorTable(object):
    """
    Manages mirror table data for a rig.
    """

    def __init__(self, filepath: str = None):
        self.filepath = filepath
        self.rig_hint = ""
        self.pairs = []          # list of dicts: {"left": str, "right": str, "mirror_axis": "X", "invert_rotate": [...], "invert_translate": [...]}
        self.center_controls = [] # list of str
        self.center_axis = "X"

        if filepath and os.path.exists(filepath):
            self.load(filepath)

    def auto_detect(self, nodes: list = None) -> int:
        """
        Auto-detects L/R pairs from scene or given node list based on naming conventions.
        Returns number of pairs found.
        """
        all_nodes = nodes or cmds.ls(type="transform") or []
        short_names = [n.split("|")[-1] for n in all_nodes]
        unbound = set(short_names)

        found_pairs = []
        center_ctrls = []

        for name in list(unbound):
            if name not in unbound:
                continue

            matched = False
            for p_left, p_right in DEFAULT_LR_PATTERNS:
                if p_left in name:
                    opposite = name.replace(p_left, p_right)
                    if opposite in unbound and opposite != name:
                        found_pairs.append({
                            "left": name,
                            "right": opposite,
                            "mirror_axis": "X",
                            "invert_rotate": ["rotateY", "rotateZ"],
                            "invert_translate": ["translateX"]
                        })
                        unbound.remove(name)
                        unbound.remove(opposite)
                        matched = True
                        break

            if not matched:
                if any(c in name.lower() for c in ["spine", "head", "neck", "hip", "root", "cog"]):
                    center_ctrls.append(name)

        self.pairs = found_pairs
        self.center_controls = center_ctrls
        return len(found_pairs)

    def get_mirrored_control(self, ctrl_name: str) -> tuple:
        """
        Returns (mirrored_ctrl_name, pair_dict).
        If ctrl_name is a center control, returns (ctrl_name, center_dict).
        If no pair found, returns (None, None).
        """
        short = ctrl_name.split("|")[-1]
        base = short.split(":")[-1] if ":" in short else short
        ns = short.rsplit(":", 1)[0] if ":" in short else ""

        for pair in self.pairs:
            l_base = pair["left"].rsplit(":", 1)[-1]
            r_base = pair["right"].rsplit(":", 1)[-1]

            if base == l_base:
                opp = f"{ns}:{r_base}" if ns else r_base
                return opp, pair
            elif base == r_base:
                opp = f"{ns}:{l_base}" if ns else l_base
                return opp, pair

        if base in [c.rsplit(":", 1)[-1] for c in self.center_controls]:
            return ctrl_name, {"is_center": True, "mirror_axis": self.center_axis}

        return None, None

    def mirror_pose(self, pose_controls: dict) -> dict:
        """
        Transforms a pose_controls dict to its mirrored equivalent.
        """
        mirrored_pose = {}
        for ctrl_key, attrs in pose_controls.items():
            opp_ctrl, pair_info = self.get_mirrored_control(ctrl_key)
            target_key = opp_ctrl if opp_ctrl else ctrl_key
            mirrored_attrs = {}

            inv_trans = pair_info.get("invert_translate", ["translateX"]) if pair_info else ["translateX"]
            inv_rot = pair_info.get("invert_rotate", ["rotateY", "rotateZ"]) if pair_info else ["rotateY", "rotateZ"]

            for attr, val in attrs.items():
                if isinstance(val, (int, float)):
                    if attr in inv_trans or attr in inv_rot:
                        mirrored_attrs[attr] = -val
                    else:
                        mirrored_attrs[attr] = val
                else:
                    mirrored_attrs[attr] = val

            mirrored_pose[target_key] = mirrored_attrs

        return mirrored_pose

    def save(self, filepath: str):
        self.filepath = filepath
        data = {
            "version": 1,
            "rig_hint": self.rig_hint,
            "pairs": self.pairs,
            "center_controls": self.center_controls,
            "center_axis": self.center_axis
        }
        out_dir = os.path.dirname(filepath)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    def load(self, filepath: str):
        self.filepath = filepath
        with open(filepath, "r") as f:
            data = json.load(f)
        self.rig_hint = data.get("rig_hint", "")
        self.pairs = data.get("pairs", [])
        self.center_controls = data.get("center_controls", [])
        self.center_axis = data.get("center_axis", "X")
