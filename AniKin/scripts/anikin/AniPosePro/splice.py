"""
splice.py — Clip Splicing (Trim & Join) for AniPose Pro V2 (F-NEW-01).

Pure JSON dict manipulation to trim clips or join them end-to-end without
requiring Maya scene playback or interaction.
"""

import copy

def trim_clip(clip_data, new_start, new_end):
    """
    Returns a new clip_data dict containing only keys between new_start and new_end.
    Time offsets are re-zeroed to new_start.
    """
    if clip_data.get("format") != "animclip_v2":
        return None  # Only V2 clips supported for splicing

    trimmed = copy.deepcopy(clip_data)
    trimmed["frame_start"] = new_start
    trimmed["frame_end"] = new_end
    trimmed["frame_count"] = new_end - new_start
    
    # Original clip's relative start
    # new_start and new_end are relative to the original clip's 0 offset
    
    for ctrl, attrs in trimmed.get("controls", {}).items():
        for attr_name, curve_entry in attrs.items():
            valid_keys = []
            for key_entry in curve_entry.get("keys", []):
                t = key_entry["time_offset"]
                if new_start <= t <= new_end:
                    # Re-zero to the new start
                    key_entry["time_offset"] = t - new_start
                    valid_keys.append(key_entry)
            curve_entry["keys"] = valid_keys

    return trimmed


def join_clips(clip_a, clip_b):
    """
    Returns a new clip_data dict where clip_b is appended immediately after clip_a.
    Requires both to be animclip_v2.
    """
    if clip_a.get("format") != "animclip_v2" or clip_b.get("format") != "animclip_v2":
        return None

    joined = copy.deepcopy(clip_a)
    offset_b = clip_a.get("frame_count", 0) + 1  # Start clip B right after clip A ends
    
    joined["frame_end"] = joined["frame_start"] + offset_b + clip_b.get("frame_count", 0)
    joined["frame_count"] = offset_b + clip_b.get("frame_count", 0)
    
    # Merge controls
    controls_a = joined.get("controls", {})
    controls_b = clip_b.get("controls", {})
    
    # All controls in B need to be merged into A
    for ctrl, attrs_b in controls_b.items():
        if ctrl not in controls_a:
            # Entire control is missing in A, just copy it and shift all its keys
            shifted_attrs = copy.deepcopy(attrs_b)
            for attr_name, curve_entry in shifted_attrs.items():
                for key_entry in curve_entry.get("keys", []):
                    key_entry["time_offset"] += offset_b
            controls_a[ctrl] = shifted_attrs
        else:
            # Control exists in both
            for attr_name, curve_entry_b in attrs_b.items():
                if attr_name not in controls_a[ctrl]:
                    shifted_curve = copy.deepcopy(curve_entry_b)
                    for key_entry in shifted_curve.get("keys", []):
                        key_entry["time_offset"] += offset_b
                    controls_a[ctrl][attr_name] = shifted_curve
                else:
                    # Attribute exists in both, append B's keys to A's
                    shifted_keys = copy.deepcopy(curve_entry_b.get("keys", []))
                    for key_entry in shifted_keys:
                        key_entry["time_offset"] += offset_b
                    controls_a[ctrl][attr_name]["keys"].extend(shifted_keys)
                    
    return joined
