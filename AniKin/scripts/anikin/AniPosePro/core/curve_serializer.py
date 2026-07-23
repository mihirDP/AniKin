"""
curve_serializer.py — High-fidelity animation curve serialization & 7-pass restoration for AniPose Pro V3.2.

Employs Section 5.1 7-Pass Restore Algorithm to eliminate silent tangent recomputation on locked keys:
Pass 1: Keyframe creation
Pass 2: Infinity & Curve weighting
Pass 3: Unlock ALL key tangents & weight locks
Pass 4: Tangent Types (In/Out)
Pass 5: Tangent Angles & Weights (In/Out) while unlocked
Pass 6: Re-lock tangents & weight locks selectively based on stored lock flags
Pass 7: Breakdown Key flags
"""

import maya.cmds as cmds


def serialize_curve(ctrl: str, attr: str, start: float, end: float) -> dict:
    """
    Serializes every key on ctrl.attr between start and end to a dict in Maya user units.
    """
    full_attr = f"{ctrl}.{attr}"
    if not cmds.objExists(full_attr):
        return None

    anim_curves = cmds.listConnections(full_attr, s=True, d=False, type="animCurve") or []
    if not anim_curves:
        return None

    key_times = cmds.keyframe(full_attr, q=True, time=(start, end), timeChange=True) or []
    key_values = cmds.keyframe(full_attr, q=True, time=(start, end), valueChange=True) or []
    if not key_times:
        return None

    try:
        pre_inf = cmds.getAttr(f"{full_attr}.preInfinity")
        post_inf = cmds.getAttr(f"{full_attr}.postInfinity")
        inf_map = {0: "constant", 1: "linear", 2: "cycle", 3: "cycleRelative", 4: "oscillate"}
        pre_inf_str = inf_map.get(pre_inf, "constant")
        post_inf_str = inf_map.get(post_inf, "constant")
    except Exception:
        pre_inf_str = "constant"
        post_inf_str = "constant"

    try:
        is_weighted = bool(cmds.keyTangent(full_attr, q=True, weightedTangents=True)[0])
    except Exception:
        is_weighted = False

    curve_data = {
        "pre_infinity": pre_inf_str,
        "post_infinity": post_inf_str,
        "is_weighted": is_weighted,
        "keys": []
    }

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

        curve_data["keys"].append({
            "time": float(t),
            "time_offset": float(t - start),
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

    return curve_data


def deserialize_curve(ctrl: str, attr: str, curve_data: dict,
                      time_offset: float = 0.0, time_scale: float = 1.0):
    """
    Restores a serialized curve back onto ctrl.attr using 7-pass restore logic.
    """
    full_attr = f"{ctrl}.{attr}"
    if not cmds.objExists(full_attr):
        return

    keys = curve_data.get("keys", [])
    if not keys:
        return

    first_time = keys[0]["time"]
    is_weighted = bool(curve_data.get("is_weighted", False))

    # Pass 1: Set Keyframes
    for key in keys:
        raw_time = key.get("time", key.get("time_offset", 0.0))
        new_time = ((raw_time - first_time) * time_scale) + first_time + time_offset
        cmds.setKeyframe(full_attr, time=(new_time,), value=key["value"])

    # Pass 2: Pre/Post Infinity & Curve Weighting
    try:
        cmds.setInfinity(
            full_attr,
            preInfinite=curve_data.get("pre_infinity", "constant"),
            postInfinite=curve_data.get("post_infinity", "constant")
        )
    except Exception:
        pass

    try:
        cmds.keyTangent(full_attr, edit=True, weightedTangents=is_weighted)
    except Exception:
        pass

    # Pass 3: UNLOCK EVERY KEY (Prevents Silent Recomputation)
    for key in keys:
        raw_time = key.get("time", key.get("time_offset", 0.0))
        new_time = ((raw_time - first_time) * time_scale) + first_time + time_offset
        try:
            cmds.keyTangent(full_attr, time=(new_time, new_time), edit=True,
                            lock=False, weightLock=False)
        except Exception:
            pass

    # Pass 4: Tangent Types
    for key in keys:
        raw_time = key.get("time", key.get("time_offset", 0.0))
        new_time = ((raw_time - first_time) * time_scale) + first_time + time_offset
        in_type = key.get("in_tangent_type", "auto")
        out_type = key.get("out_tangent_type", "auto")
        try:
            cmds.keyTangent(full_attr, time=(new_time, new_time), edit=True,
                            inTangentType=in_type, outTangentType=out_type)
        except Exception:
            pass

    # Pass 5: Set Angles & Weights (Safe while unlocked!)
    for key in keys:
        raw_time = key.get("time", key.get("time_offset", 0.0))
        new_time = ((raw_time - first_time) * time_scale) + first_time + time_offset
        kwargs = {}
        if "in_angle" in key: kwargs["inAngle"] = key["in_angle"]
        if "out_angle" in key: kwargs["outAngle"] = key["out_angle"]
        if is_weighted and "in_weight" in key: kwargs["inWeight"] = key["in_weight"]
        if is_weighted and "out_weight" in key: kwargs["outWeight"] = key["out_weight"]

        if kwargs:
            try:
                cmds.keyTangent(full_attr, time=(new_time, new_time), edit=True, **kwargs)
            except Exception:
                pass

    # Pass 6: Re-lock Keys (Only where originally locked)
    for key in keys:
        raw_time = key.get("time", key.get("time_offset", 0.0))
        new_time = ((raw_time - first_time) * time_scale) + first_time + time_offset
        t_locked = key.get("tangents_locked", True)
        w_locked = key.get("weight_locked", True)
        try:
            cmds.keyTangent(full_attr, time=(new_time, new_time), edit=True,
                            lock=t_locked, weightLock=w_locked)
        except Exception:
            pass

    # Pass 7: Breakdown Flags
    for key in keys:
        raw_time = key.get("time", key.get("time_offset", 0.0))
        new_time = ((raw_time - first_time) * time_scale) + first_time + time_offset
        if key.get("is_breakdown", False):
            try:
                cmds.keyframe(full_attr, time=(new_time, new_time), edit=True, breakdown=True)
            except Exception:
                pass


def serialize_clip(nodes: list, start: float, end: float,
                   graph_editor_curves: list = None) -> dict:
    """
    Serialize all animated attributes on nodes between start and end frame.
    """
    if not nodes:
        return {}

    duration = max(1.0, end - start)
    fps_str = cmds.currentUnit(q=True, time=True)

    scene_ns = ""
    for n in nodes:
        short = n.split("|")[-1]
        if ":" in short:
            scene_ns = short.split(":")[0]
            break

    controls_data = {}
    for node in nodes:
        short = node.split("|")[-1]
        ctrl_key = short.split(":")[1] if ":" in short else short

        keyable_attrs = cmds.listAttr(node, keyable=True, unlocked=True) or []
        node_curves = {}

        for attr in keyable_attrs:
            full_attr = f"{node}.{attr}"
            anim_curves = cmds.listConnections(full_attr, s=True, d=False, type="animCurve") or []
            if not anim_curves:
                continue

            c_data = serialize_curve(node, attr, start, end)
            if c_data and c_data.get("keys"):
                node_curves[attr] = c_data

        if node_curves:
            controls_data[ctrl_key] = node_curves

    return {
        "version": 2,
        "type": "animclip",
        "start": float(start),
        "end": float(end),
        "duration": float(duration),
        "frame_count": int(duration),
        "fps": fps_str,
        "namespace": scene_ns,
        "controls": controls_data
    }


def assert_curve_fidelity(source_attr: str, target_attr: str, start: float, end: float,
                          sample_rate: float = 0.1, epsilon: float = 1e-4):
    """
    Samples source_attr and target_attr at sub-frame intervals (0.1 frames) across [start, end]
    and asserts the evaluated attribute value matches within epsilon.
    """
    t = start
    mismatches = []
    while t <= end + 1e-5:
        src_val = cmds.getAttr(source_attr, time=t)
        tgt_val = cmds.getAttr(target_attr, time=t)
        diff = abs(src_val - tgt_val)
        if diff >= epsilon:
            mismatches.append((t, src_val, tgt_val, diff))
        t += sample_rate

    if mismatches:
        first_mismatch = mismatches[0]
        raise AssertionError(
            f"Curve fidelity check failed! {len(mismatches)} mismatches found.\n"
            f"First mismatch at frame {first_mismatch[0]:.2f}: "
            f"Source={first_mismatch[1]:.6f}, Target={first_mismatch[2]:.6f}, Delta={first_mismatch[3]:.6f}"
        )
    return True
