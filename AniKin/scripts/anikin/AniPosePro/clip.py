"""
clip.py — Animation clip save & apply for AniPose Pro (F-PL-14).

Saves multi-frame key data (including tangent angles & types) to a .animclip
JSON file and applies it back at any target frame with Insert / Merge / Replace modes.
"""

import os
import json
import datetime
import maya.cmds as cmds


ANIMCLIP_EXT = ".animclip"
META_EXT     = ".meta.json"


# ── Save ───────────────────────────────────────────────────────────────────────

def save_clip(nodes, frame_start, frame_end, output_path, name="",
              author=None, project="", tags=None, notes=""):
    """
    Capture all keyframe data for `nodes` across [frame_start, frame_end].
    Times stored relative to frame_start so the clip is offset-independent.

    Returns the path of the saved .animclip file.
    """
    import getpass

    controls = {}
    namespace = ""

    for node in nodes:
        short = node.split("|")[-1]
        if ":" in short:
            if not namespace:
                namespace = short.split(":")[0]
            ctrl_key = ":".join(short.split(":")[1:])
        else:
            ctrl_key = short

        controls[ctrl_key] = {}
        all_keyable = cmds.listAttr(node, keyable=True) or []

        for attr in all_keyable:
            full = "{}.{}".format(node, attr)
            times = cmds.keyframe(full, q=True,
                                   time=(frame_start, frame_end),
                                   timeChange=True) or []
            if not times:
                continue
            values     = cmds.keyframe(full, q=True,
                                       time=(frame_start, frame_end),
                                       valueChange=True) or []
            in_angles  = cmds.keyTangent(full, q=True,
                                          time=(frame_start, frame_end),
                                          inAngle=True) or []
            out_angles = cmds.keyTangent(full, q=True,
                                          time=(frame_start, frame_end),
                                          outAngle=True) or []
            in_types   = cmds.keyTangent(full, q=True,
                                          time=(frame_start, frame_end),
                                          inTangentType=True) or []
            out_types  = cmds.keyTangent(full, q=True,
                                          time=(frame_start, frame_end),
                                          outTangentType=True) or []

            controls[ctrl_key][attr] = {
                "keys": [
                    {
                        "time":      t - frame_start,
                        "value":     v,
                        "in_angle":  ia,
                        "out_angle": oa,
                        "in_type":   it,
                        "out_type":  ot,
                    }
                    for t, v, ia, oa, it, ot
                    in zip(times, values, in_angles, out_angles, in_types, out_types)
                ]
            }

    clip_data = {
        "anikin_version": "2.0",
        "format":         "animclip",
        "name":           name or os.path.splitext(os.path.basename(output_path))[0],
        "captured_at":    datetime.datetime.now().isoformat(),
        "rig_namespace":  namespace,
        "frame_count":    frame_end - frame_start + 1,
        "controls":       controls,
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    _write_json_atomic(output_path, clip_data)

    # Meta sidecar
    meta_path = output_path.replace(ANIMCLIP_EXT, META_EXT)
    meta = {
        "name":    clip_data["name"],
        "author":  author or _get_user(),
        "project": project,
        "tags":    tags or [],
        "notes":   notes,
    }
    _write_json_atomic(meta_path, meta)

    return output_path


# ── Apply ──────────────────────────────────────────────────────────────────────

def apply_clip(clip_path, nodes, dest_start_frame, mode="replace",
               retime_frames=None):
    """
    Apply a saved animation clip at dest_start_frame.

    Args:
        clip_path:        Path to .animclip file.
        nodes:            Selected Maya nodes (used to detect namespace).
        dest_start_frame: Frame where the clip's time=0 will land.
        mode:             "replace" | "insert" | "merge"
        retime_frames:    If set, scale clip timing to fit this many frames (F-PL-25).
    """
    with open(clip_path, "r", encoding="utf-8") as f:
        clip_data = json.load(f)

    scene_ns = ""
    for n in nodes:
        short = n.split("|")[-1]
        if ":" in short:
            scene_ns = short.split(":")[0]
            break

    clip_len = clip_data.get("frame_count", 1)
    scale    = (retime_frames / clip_len) if retime_frames else 1.0

    cmds.undoInfo(openChunk=True, chunkName="AniKin_ClipApply")
    try:
        for ctrl, attrs in clip_data.get("controls", {}).items():
            scene_node = "{}:{}".format(scene_ns, ctrl) if scene_ns else ctrl
            if not cmds.objExists(scene_node):
                continue

            for attr, attr_data in attrs.items():
                full = "{}.{}".format(scene_node, attr)
                if not cmds.objExists(full):
                    continue

                keys = attr_data.get("keys", [])
                if not keys:
                    continue

                dest_end = dest_start_frame + int(clip_len * scale) - 1

                if mode == "insert":
                    # Push keys that are at or after dest_start_frame forward
                    shift = int(clip_len * scale)
                    cmds.keyframe(full,
                                  time=(dest_start_frame, 999999),
                                  edit=True, relative=True,
                                  timeChange=shift)

                elif mode == "replace":
                    # Delete existing keys in destination range
                    cmds.cutKey(full,
                                time=(dest_start_frame, dest_end),
                                clear=True)

                # mode == "merge" just writes keys on top (no deletion)

                for key in keys:
                    dest_t = dest_start_frame + key["time"] * scale
                    cmds.setKeyframe(full, time=dest_t, value=key["value"])
                    cmds.keyTangent(full,
                                    time=(dest_t, dest_t),
                                    inAngle=key.get("in_angle", 0),
                                    outAngle=key.get("out_angle", 0),
                                    inTangentType=key.get("in_type", "auto"),
                                    outTangentType=key.get("out_type", "auto"))
    finally:
        cmds.undoInfo(closeChunk=True)

    cmds.inViewMessage(
        amg="<hl>AniPose Pro</hl>: Clip applied ({} mode)".format(mode),
        pos="topCenter", fade=True, fadeStayTime=1500
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_json_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def _get_user():
    import getpass
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"
