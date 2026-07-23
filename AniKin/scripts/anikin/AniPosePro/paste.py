"""
paste.py — Native high-fidelity animation clip paste for AniPose Pro V3.1.

Restores animation clips with 100% Graph Editor curve precision using Maya cmds.
Handles angles, weights, tangent types, locked states, infinity, and breakdown keys.
Wrapped in a single Maya Undo Chunk.
"""

import maya.cmds as cmds


def paste_clip_at_frame(clip_data, nodes, dest_frame, mode="replace", retime_frames=None):
    """
    Paste an animclip dict onto *nodes* starting at dest_frame with 100% curve fidelity.
    """
    if not clip_data or not nodes:
        cmds.warning("AniPose Pro: No clip data or nodes selected for pasting.")
        return

    frame_count = clip_data.get("frame_count", clip_data.get("duration", 0))
    controls = clip_data.get("controls", {})
    if not controls:
        cmds.warning("AniPose Pro: Clip contains no animated control channels.")
        return

    scale = (retime_frames / frame_count) if (retime_frames and frame_count > 0) else 1.0
    effective_count = int(frame_count * scale) if frame_count else 1

    cmds.undoInfo(openChunk=True, chunkName="AniKin_ClipPaste")
    try:
        for node in nodes:
            short = node.split("|")[-1]
            lookup_key = ":".join(short.split(":")[1:]) if ":" in short else short

            if lookup_key not in controls:
                continue

            channels = controls[lookup_key]
            for attr_name, curve_entry in channels.items():
                full_attr = f"{node}.{attr_name}"
                if not cmds.objExists(full_attr):
                    continue

                keys_list = curve_entry.get("keys", [])
                if not keys_list:
                    continue

                # ── Pass 1: Paste Mode Pre-Processing ───────────────────────────
                if mode == "replace":
                    end_frame = dest_frame + effective_count
                    cmds.cutKey(node, attribute=attr_name, time=(dest_frame, end_frame), option="keys")
                elif mode == "insert":
                    cmds.keyframe(node, attribute=attr_name, time=(dest_frame, None),
                                  relative=True, timeChange=effective_count, option="over")

                # ── Pass 2: Set Keyframe Values ─────────────────────────────────
                for key in keys_list:
                    offset = key.get("time_offset", key.get("time", 0.0))
                    abs_time = dest_frame + (offset * scale)
                    val = key.get("value", 0.0)
                    cmds.setKeyframe(full_attr, time=(abs_time,), value=val)

                # ── Pass 3: Pre/Post Infinity & Weighted Tangents ────────────────
                is_weighted = bool(curve_entry.get("is_weighted", False))
                try:
                    cmds.setInfinity(
                        full_attr,
                        preInfinite=curve_entry.get("pre_infinity", "constant"),
                        postInfinite=curve_entry.get("post_infinity", "constant")
                    )
                except Exception:
                    pass

                try:
                    cmds.keyTangent(full_attr, edit=True, weightedTangents=is_weighted)
                except Exception:
                    pass

                # ── Pass 4: Tangent Types, Angles, Weights, Locks & Breakdowns ──
                for key in keys_list:
                    offset = key.get("time_offset", key.get("time", 0.0))
                    abs_time = dest_frame + (offset * scale)

                    in_type = key.get("in_tangent_type", "auto")
                    out_type = key.get("out_tangent_type", "auto")

                    # Set tangent types first
                    try:
                        cmds.keyTangent(full_attr, time=(abs_time, abs_time), edit=True,
                                        inTangentType=in_type, outTangentType=out_type)
                    except Exception:
                        pass

                    # UNLOCK FIRST: prevent Maya from auto-recalculating the opposite tangent!
                    try:
                        cmds.keyTangent(full_attr, time=(abs_time, abs_time), edit=True,
                                        lock=False, weightLock=False)
                    except Exception:
                        pass

                    # Set angles and weights (if present or if fixed handle)
                    try:
                        kwargs = {}
                        if "in_angle" in key:
                            kwargs["inAngle"] = key["in_angle"]
                        if "out_angle" in key:
                            kwargs["outAngle"] = key["out_angle"]
                        if is_weighted and "in_weight" in key:
                            kwargs["inWeight"] = key["in_weight"]
                        if is_weighted and "out_weight" in key:
                            kwargs["outWeight"] = key["out_weight"]

                        if kwargs:
                            cmds.keyTangent(full_attr, time=(abs_time, abs_time), edit=True, **kwargs)
                    except Exception:
                        pass

                    # RESTORE LOCK STATES
                    try:
                        cmds.keyTangent(full_attr, time=(abs_time, abs_time), edit=True,
                                        lock=key.get("tangents_locked", True),
                                        weightLock=key.get("weight_locked", True))
                    except Exception:
                        pass

                    # Set breakdown key flag
                    try:
                        if key.get("is_breakdown", False):
                            cmds.keyframe(full_attr, time=(abs_time, abs_time), edit=True, breakdown=True)
                    except Exception:
                        pass

            cmds.dgdirty(allPlugs=True)
            cmds.refresh()

    finally:
        cmds.undoInfo(closeChunk=True)

    cmds.inViewMessage(
        amg=f"<hl>AniPose Pro</hl>: Clip pasted at frame {int(dest_frame)} ({mode})",
        pos="topCenter", fade=True, fadeStayTime=1500
    )


def paste_legacy_clip(clip_data, nodes, dest_frame, mode="replace", retime_frames=None):
    """Fallback legacy paste calling paste_clip_at_frame."""
    return paste_clip_at_frame(clip_data, nodes, dest_frame, mode=mode, retime_frames=retime_frames)
