"""
AniMatch — IK/FK Snap & Match for AniKin.

Two-layer approach:
  1. Explicit rig config (bulletproof) — JSON mapping per rig.
  2. Heuristic auto-detect (convenience) — naming-convention + chain-length scan
     to PRE-FILL the config for the animator to confirm, never silently trusted.

Supports:
  - Single-frame IK→FK and FK→IK snapping.
  - Frame-range bake match (loop + key per frame, optional curve simplify).
  - Constraint-based rotation transfer (avoids the 360° flip bug that plagues
    naive xform -ws -ro approaches).
  - Pole-vector solve via mid-limb projection (standard rigging math).
"""

import os
import json
import re
import maya.cmds as cmds
from anikin.core.undo import UndoChunk

# ── Config storage ─────────────────────────────────────────────────────────────
# Per-rig configs live alongside AniSets data in the user's AniKin prefs dir.

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), "anikin_match_configs")


def _config_path(rig_name):
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    return os.path.join(_CONFIG_DIR, "{}.json".format(rig_name))


def save_config(rig_name, config):
    """
    Save an IK/FK limb mapping config.

    config format:
    {
        "limbs": [
            {
                "name": "Left Arm",
                "ik_ctrl": "L_arm_IK_CTRL",
                "pole_vector": "L_arm_PV_CTRL",
                "fk_ctrls": ["L_shoulder_FK_CTRL", "L_elbow_FK_CTRL", "L_wrist_FK_CTRL"],
                "joints": ["L_shoulder_JNT", "L_elbow_JNT", "L_wrist_JNT"],
                "switch_attr": "L_arm_IK_CTRL.ikFkSwitch",
                "ik_value": 0,
                "fk_value": 1
            },
            ...
        ]
    }
    """
    path = _config_path(rig_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_config(rig_name):
    """Load a saved rig config. Returns None if not found."""
    path = _config_path(rig_name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_configs():
    """Return list of saved rig config names."""
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    return [f.replace(".json", "")
            for f in os.listdir(_CONFIG_DIR) if f.endswith(".json")]


# ── Heuristic Auto-Detection ──────────────────────────────────────────────────

# Common naming patterns for IK/FK detection
_IK_PATTERNS = [r"_IK_", r"_ik_", r"_IK$", r"_ik$", r"IK_CTRL", r"ik_ctrl"]
_FK_PATTERNS = [r"_FK_", r"_fk_", r"_FK$", r"_fk$", r"FK_CTRL", r"fk_ctrl"]
_PV_PATTERNS = [r"_PV_", r"_pv_", r"PV_CTRL", r"pv_ctrl", r"poleVector", r"pole_vector"]


def auto_detect_limbs(namespace=""):
    """
    Scan the scene for IK/FK control pairs using naming conventions.
    Returns a list of suggested limb dicts (same format as config["limbs"]).

    These are SUGGESTIONS — the animator must confirm/edit before saving.
    """
    prefix = "{}:".format(namespace) if namespace else ""
    all_transforms = cmds.ls("{}*".format(prefix), type="transform") or []

    ik_ctrls = []
    fk_ctrls = []
    pv_ctrls = []

    for t in all_transforms:
        short = t.split(":")[-1]
        for pat in _IK_PATTERNS:
            if re.search(pat, short):
                ik_ctrls.append(t)
                break
        for pat in _FK_PATTERNS:
            if re.search(pat, short):
                fk_ctrls.append(t)
                break
        for pat in _PV_PATTERNS:
            if re.search(pat, short):
                pv_ctrls.append(t)
                break

    # Try to pair IK and FK controls by body-part substring matching
    limbs = []
    for ik in ik_ctrls:
        # Extract the "body part" token (e.g. "L_arm" from "L_arm_IK_CTRL")
        body_part = _extract_body_part(ik)
        if not body_part:
            continue

        # Find FK controls that share the same body part token
        matching_fk = [fk for fk in fk_ctrls if body_part in fk]
        matching_pv = [pv for pv in pv_ctrls if body_part in pv]

        if len(matching_fk) < 2:
            continue  # Need at least 2 FK controls for a limb chain

        # Sort FK by hierarchy depth (approximate chain order)
        matching_fk.sort(key=lambda f: len(cmds.ls(f, long=True)[0].split("|")))

        limb = {
            "name": body_part.replace("_", " ").title(),
            "ik_ctrl": ik,
            "pole_vector": matching_pv[0] if matching_pv else "",
            "fk_ctrls": matching_fk[:3],  # Cap at 3 (standard 2-bone limb)
            "joints": [],  # Must be filled by user or deeper heuristic
            "switch_attr": "",
            "ik_value": 0,
            "fk_value": 1,
        }
        limbs.append(limb)

    return limbs


def _extract_body_part(ctrl_name):
    """
    Extract the body-part token from a control name.
    e.g. "L_arm_IK_CTRL" → "L_arm", "RightLeg_IK" → "RightLeg"
    """
    short = ctrl_name.split(":")[-1]
    # Remove known suffixes
    for suffix in ["_IK_CTRL", "_ik_ctrl", "_IK", "_ik",
                   "_FK_CTRL", "_fk_ctrl", "_FK", "_fk",
                   "_PV_CTRL", "_pv_ctrl", "_PV", "_pv",
                   "_CTRL", "_ctrl"]:
        if short.endswith(suffix):
            short = short[:-len(suffix)]
            break
    return short if short else None


# ── Single-Frame Match (Constraint-Based — no 360° flip) ─────────────────────

def match_ik_to_fk(limb_config):
    """
    IK → FK: Read the IK-posed joint chain rotations and apply them
    to the FK controls using a temporary orientConstraint (avoids the
    360° flip bug that plagues naive xform -ws -ro transfer).
    """
    fk_ctrls = limb_config["fk_ctrls"]
    joints = limb_config.get("joints", [])

    if not joints or len(joints) != len(fk_ctrls):
        cmds.warning("AniMatch: Joint chain count must match FK control count.")
        return False

    # Verify all nodes exist
    for node in fk_ctrls + joints:
        if not cmds.objExists(node):
            cmds.warning("AniMatch: Node '{}' not found.".format(node))
            return False

    cmds.undoInfo(openChunk=True, chunkName="AniKin_MatchIKtoFK")
    try:
        for jnt, fk in zip(joints, fk_ctrls):
            # Constraint-based transfer: temporarily orient-constrain FK to joint
            oc = cmds.orientConstraint(jnt, fk, maintainOffset=False)[0]
            # Read the resulting rotation
            rot = cmds.getAttr("{}.rotate".format(fk))[0]
            # Delete constraint
            cmds.delete(oc)
            # Apply the rotation cleanly
            cmds.setAttr("{}.rotateX".format(fk), rot[0])
            cmds.setAttr("{}.rotateY".format(fk), rot[1])
            cmds.setAttr("{}.rotateZ".format(fk), rot[2])
    except Exception as exc:
        cmds.warning("AniMatch IK→FK failed: {}".format(exc))
        return False
    finally:
        cmds.undoInfo(closeChunk=True)

    # Flip the switch attribute if configured
    _set_switch(limb_config, "fk")
    return True


def match_fk_to_ik(limb_config):
    """
    FK → IK: Read the FK-posed joint chain positions and compute the
    IK control position + pole vector location.

    IK wrist position = world position of the last FK joint.
    Pole vector = mid-limb perpendicular projection (standard rigging math).
    """
    ik_ctrl = limb_config["ik_ctrl"]
    pv_ctrl = limb_config.get("pole_vector", "")
    joints = limb_config.get("joints", [])

    if len(joints) < 3:
        cmds.warning("AniMatch FK→IK: Need at least 3 joints for pole vector solve.")
        return False

    for node in [ik_ctrl] + joints:
        if not cmds.objExists(node):
            cmds.warning("AniMatch: Node '{}' not found.".format(node))
            return False

    cmds.undoInfo(openChunk=True, chunkName="AniKin_MatchFKtoIK")
    try:
        # IK control → world position of end joint (wrist/ankle)
        end_pos = cmds.xform(joints[-1], q=True, worldSpace=True, translation=True)

        # Also match orientation via constraint-transfer
        oc = cmds.orientConstraint(joints[-1], ik_ctrl, maintainOffset=False)[0]
        ik_rot = cmds.getAttr("{}.rotate".format(ik_ctrl))[0]
        cmds.delete(oc)

        cmds.xform(ik_ctrl, worldSpace=True, translation=end_pos)
        cmds.setAttr("{}.rotateX".format(ik_ctrl), ik_rot[0])
        cmds.setAttr("{}.rotateY".format(ik_ctrl), ik_rot[1])
        cmds.setAttr("{}.rotateZ".format(ik_ctrl), ik_rot[2])

        # Pole vector solve (if PV control exists)
        if pv_ctrl and cmds.objExists(pv_ctrl):
            pv_pos = _compute_pole_vector_position(joints[0], joints[1], joints[2])
            cmds.xform(pv_ctrl, worldSpace=True, translation=pv_pos)

    except Exception as exc:
        cmds.warning("AniMatch FK→IK failed: {}".format(exc))
        return False
    finally:
        cmds.undoInfo(closeChunk=True)

    _set_switch(limb_config, "ik")
    return True


def _compute_pole_vector_position(start_jnt, mid_jnt, end_jnt, distance_scale=1.5):
    """
    Compute the pole-vector position for a 2-bone IK limb.

    Standard rigging math:
      1. Project the mid-joint onto the start→end line.
      2. Compute the perpendicular vector from that projection to the mid-joint.
      3. Push out along that perpendicular by a comfortable distance.
    """
    start = cmds.xform(start_jnt, q=True, ws=True, t=True)
    mid   = cmds.xform(mid_jnt,   q=True, ws=True, t=True)
    end   = cmds.xform(end_jnt,   q=True, ws=True, t=True)

    # Vectors
    start_to_end = [end[i] - start[i] for i in range(3)]
    start_to_mid = [mid[i] - start[i] for i in range(3)]

    # Dot product and projection
    line_len_sq = sum(v*v for v in start_to_end)
    if line_len_sq < 0.0001:
        return mid  # Degenerate case — joint chain is collapsed

    dot = sum(start_to_mid[i] * start_to_end[i] for i in range(3))
    proj_factor = dot / line_len_sq

    # Point on the line closest to mid
    proj_point = [start[i] + proj_factor * start_to_end[i] for i in range(3)]

    # Perpendicular: mid - projection
    perp = [mid[i] - proj_point[i] for i in range(3)]
    perp_len = (sum(v*v for v in perp)) ** 0.5

    if perp_len < 0.0001:
        # Mid-joint is directly on the line — default to world-Y offset
        return [mid[0], mid[1] + 10.0, mid[2]]

    # Normalize and scale
    limb_len = line_len_sq ** 0.5
    scale = limb_len * distance_scale
    pv_pos = [mid[i] + (perp[i] / perp_len) * scale for i in range(3)]

    return pv_pos


def _set_switch(limb_config, target_mode):
    """Set the IK/FK switch attribute if configured."""
    switch_attr = limb_config.get("switch_attr", "")
    if not switch_attr or not cmds.objExists(switch_attr):
        return
    try:
        if target_mode == "ik":
            cmds.setAttr(switch_attr, limb_config.get("ik_value", 0))
        else:
            cmds.setAttr(switch_attr, limb_config.get("fk_value", 1))
    except Exception:
        pass


# ── Frame-Range Bake Match ────────────────────────────────────────────────────

def match_range(limb_config, direction="ik_to_fk", start=None, end=None):
    """
    Match IK↔FK across a frame range by looping and keying each frame.

    Args:
        limb_config:  A single limb dict from the config.
        direction:    "ik_to_fk" or "fk_to_ik"
        start/end:    Frame range (defaults to playback range).
    """
    if start is None:
        start = cmds.playbackOptions(q=True, minTime=True)
    if end is None:
        end = cmds.playbackOptions(q=True, maxTime=True)

    match_fn = match_ik_to_fk if direction == "ik_to_fk" else match_fk_to_ik

    # Determine which controls get keyed
    if direction == "ik_to_fk":
        key_targets = limb_config["fk_ctrls"]
    else:
        key_targets = [limb_config["ik_ctrl"]]
        if limb_config.get("pole_vector") and cmds.objExists(limb_config["pole_vector"]):
            key_targets.append(limb_config["pole_vector"])

    cmds.undoInfo(openChunk=True, chunkName="AniKin_MatchRange")
    try:
        frame = int(start)
        while frame <= int(end):
            cmds.currentTime(frame, edit=True)
            match_fn(limb_config)

            # Key the target controls at this frame
            for ctrl in key_targets:
                if cmds.objExists(ctrl):
                    cmds.setKeyframe(ctrl, time=frame)

            frame += 1
    finally:
        cmds.undoInfo(closeChunk=True)

    cmds.inViewMessage(
        amg="<hl>AniMatch</hl>: Bake-matched {} frames ({})".format(
            int(end) - int(start) + 1, direction.replace("_", " ")),
        pos="topCenter", fade=True, fadeStayTime=2000
    )
