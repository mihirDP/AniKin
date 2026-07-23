"""
capture.py — Native high-fidelity animation clip capture for AniPose Pro V3.1.

Captures all curve data in Maya native user units (degrees, frames, weights):
- Tangent Types (in & out)
- Tangent Angles (in & out in degrees)
- Tangent Weights (in & out)
- Tangent & Weight Lock states
- Pre/Post Infinity
- Curve Weighted flag
- Breakdown key flags
- Relative time offsets
"""

import os
import json
import datetime
import getpass
import maya.cmds as cmds

ANIMCLIP_EXT = ".animclip"
META_EXT = ".meta.json"


def capture_anim_clip(nodes, frame_start, frame_end, graph_editor_curves=None):
    """
    Capture animation data for all animated channels of *nodes* in the range
    [frame_start, frame_end] with 100% curve fidelity in Maya user units.
    """
    clip_data = {
        "anikin_version": "3.1",
        "format": "animclip_v2",
        "captured_at": datetime.datetime.now().isoformat(),
        "frame_start": float(frame_start),
        "frame_end": float(frame_end),
        "frame_count": int(frame_end - frame_start),
        "duration": float(frame_end - frame_start),
        "fps": cmds.currentUnit(q=True, time=True),
        "controls": {},
    }

    for node in nodes:
        short = node.split("|")[-1]
        ns_key = ":".join(short.split(":")[1:]) if ":" in short else short

        # Find keyable attributes with animation curves
        keyable_attrs = cmds.listAttr(node, keyable=True, unlocked=True) or []
        node_curves = {}

        for attr in keyable_attrs:
            full_attr = f"{node}.{attr}"
            anim_curves = cmds.listConnections(full_attr, s=True, d=False, type="animCurve") or []
            if not anim_curves:
                continue

            curve_node = anim_curves[0]
            if graph_editor_curves and curve_node not in graph_editor_curves:
                continue

            # Query key times in selection range
            key_times = cmds.keyframe(full_attr, q=True, time=(frame_start, frame_end), timeChange=True) or []
            key_values = cmds.keyframe(full_attr, q=True, time=(frame_start, frame_end), valueChange=True) or []
            if not key_times:
                continue

            # Pre/post infinity
            try:
                pre_inf = cmds.getAttr(f"{full_attr}.preInfinity")
                post_inf = cmds.getAttr(f"{full_attr}.postInfinity")
                inf_map = {0: "constant", 1: "linear", 2: "cycle", 3: "cycleRelative", 4: "oscillate"}
                pre_inf_str = inf_map.get(pre_inf, "constant")
                post_inf_str = inf_map.get(post_inf, "constant")
            except Exception:
                pre_inf_str = "constant"
                post_inf_str = "constant"

            # Weighted curve flag
            try:
                is_weighted = bool(cmds.keyTangent(full_attr, q=True, weightedTangents=True)[0])
            except Exception:
                is_weighted = False

            keys_data = []
            for t, v in zip(key_times, key_values):
                try:
                    in_type = cmds.keyTangent(full_attr, t=(t,), q=True, inTangentType=True)[0]
                    out_type = cmds.keyTangent(full_attr, t=(t,), q=True, outTangentType=True)[0]
                    in_angle = cmds.keyTangent(full_attr, t=(t,), q=True, inAngle=True)[0]
                    out_angle = cmds.keyTangent(full_attr, t=(t,), q=True, outAngle=True)[0]
                    in_w = cmds.keyTangent(full_attr, t=(t,), q=True, inWeight=True)[0]
                    out_w = cmds.keyTangent(full_attr, t=(t,), q=True, outWeight=True)[0]
                    locked = cmds.keyTangent(full_attr, t=(t,), q=True, lock=True)[0]
                    wlocked = cmds.keyTangent(full_attr, t=(t,), q=True, weightLock=True)[0]
                except Exception:
                    continue

                is_bd = cmds.keyframe(full_attr, t=(t,), q=True, breakdown=True) or [False]
                is_bd = bool(is_bd[0]) if is_bd else False

                keys_data.append({
                    "time": float(t),
                    "time_offset": float(t - frame_start),
                    "value": float(v),
                    "in_tangent_type": str(in_type),
                    "out_tangent_type": str(out_type),
                    "in_angle": float(in_angle),
                    "out_angle": float(out_angle),
                    "in_weight": float(in_w),
                    "out_weight": float(out_w),
                    "tangents_locked": bool(locked),
                    "weight_locked": bool(wlocked),
                    "is_breakdown": is_bd,
                })

            if keys_data:
                node_curves[attr] = {
                    "is_weighted": is_weighted,
                    "pre_infinity": pre_inf_str,
                    "post_infinity": post_inf_str,
                    "keys": keys_data
                }

        if node_curves:
            clip_data["controls"][ns_key] = node_curves

    return clip_data


def save_clip_to_disk(clip_data, output_path, name="", author=None,
                      project="", tags=None, notes=""):
    """
    Write an animclip dict to disk as JSON, plus a .meta.json sidecar.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(clip_data, f, indent=4)

    # Meta sidecar
    meta_path = output_path.rsplit(".", 1)[0] + META_EXT
    meta = {
        "name": name or os.path.splitext(os.path.basename(output_path))[0],
        "author": author or _get_user(),
        "rig": project or "",
        "project": project,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tags": tags or [],
        "notes": notes,
        "format": "animclip_v2",
        "frame_count": clip_data.get("frame_count", 0),
        "duration": clip_data.get("duration", 0),
        "fps": clip_data.get("fps", ""),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)

    return output_path


def load_clip_data(clip_path):
    """
    Load a clip file from disk and return (clip_dict, meta_dict, is_v2).
    """
    try:
        with open(clip_path, "r", encoding="utf-8") as f:
            clip = json.load(f)
    except Exception:
        clip = {}

    meta_path = clip_path.rsplit(".", 1)[0] + META_EXT
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except Exception:
        meta = {}

    return clip, meta, True


def _get_user():
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"
