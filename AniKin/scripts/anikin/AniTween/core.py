"""
AniTween.py
Tween/Breakdown Slider â€” interpolates between neighboring keyframes.

The core animator workflow tool: drag a slider to blend between
the previous and next keyframe values on all animated channels
of the selected objects.

- bias = 0.0  â†’ value at previous key
- bias = 0.5  â†’ midpoint (default Maya interpolation)
- bias = 1.0  â†’ value at next key
- bias < 0.0  â†’ overshoot past previous key
- bias > 1.0  â†’ overshoot past next key
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.log import log_debug


def _get_animated_channels(node):
    """Return a list of (node.attr) strings that have animation curves."""
    connections = cmds.listConnections(node, type="animCurve", plugs=False,
                                       connections=True, destination=False) or []
    # listConnections returns pairs: [plug, curveNode, plug, curveNode, ...]
    attrs = []
    for i in range(0, len(connections), 2):
        plug = connections[i]
        attrs.append(plug)
    return attrs


def _get_prev_next_keys(attr, current_time):
    """
    Find the previous and next keyframe times for a given attribute
    relative to current_time.

    Returns:
        (prev_time, next_time) or (None, None) if not enough keys exist.
    """
    prev = cmds.findKeyframe(attr, time=(current_time, current_time),
                             which="previous")
    nxt = cmds.findKeyframe(attr, time=(current_time, current_time),
                            which="next")

    # findKeyframe returns the same time if there's no prev/next
    if prev == nxt:
        return None, None

    # If we're sitting on a key, prev == current_time, so look further back
    if prev == current_time:
        prev = cmds.findKeyframe(attr, time=(current_time, current_time),
                                 which="previous")
        if prev == current_time:
            return None, None

    if nxt == current_time:
        nxt = cmds.findKeyframe(attr, time=(current_time, current_time),
                                which="next")
        if nxt == current_time:
            return None, None

    return prev, nxt


def _apply_easing(bias, mode="linear"):
    """Apply easing curve to the bias."""
    if mode == "linear":
        return bias
    
    # Clamp between 0 and 1 for strict easing, but we allow overshoot
    # by extending the tangents linearly if needed, or just applying math.
    if mode == "ease_in":
        # Accelerate from prev key (t^2)
        return bias * bias if bias >= 0 else -(-bias * -bias)
    elif mode == "ease_out":
        # Decelerate to next key t*(2-t)
        return bias * (2 - bias)
    elif mode == "ease_in_out":
        # Smoothstep
        t = max(0.0, min(1.0, bias))
        eased = t * t * (3.0 - 2.0 * t)
        if bias < 0: return bias # Linear overshoot
        if bias > 1: return bias
        return eased
    return bias

def apply_tween(bias=0.5, easing="linear"):
    """
    Apply tween at the given bias to all animated channels of selected objects.

    Args:
        bias: Float from -0.5 to 1.5 (0.0 = prev key, 1.0 = next key).
              Values outside 0-1 produce overshoot.
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return

    current_time = cmds.currentTime(query=True)

    with UndoChunk("AniKin: Tween ({:.0%})".format(bias)):
        for node in sel:
            channels = _get_animated_channels(node)
            for attr in channels:
                prev_time, next_time = _get_prev_next_keys(attr, current_time)
                if prev_time is None or next_time is None:
                    continue

                # Get values at prev and next keys using keyframe evaluation (respects layers better)
                try:
                    prev_val = cmds.keyframe(attr, time=(prev_time, prev_time), query=True, eval=True)[0]
                    next_val = cmds.keyframe(attr, time=(next_time, next_time), query=True, eval=True)[0]
                except (TypeError, IndexError):
                    # Fallback if evaluation fails
                    prev_val = cmds.getAttr(attr, time=prev_time)
                    next_val = cmds.getAttr(attr, time=next_time)

                # Apply Easing Math
                eased_bias = _apply_easing(bias, mode=easing)

                # Interpolation (with overshoot support)
                tweened = prev_val + (next_val - prev_val) * eased_bias

                # Set the key at current time
                # Extract node and attribute name from the full plug path
                parts = attr.split(".")
                node_name = parts[0]
                attr_name = ".".join(parts[1:])
                cmds.setKeyframe(node_name, attribute=attr_name,
                                 time=current_time, value=tweened)


def smart_key(mode="all"):
    """
    Set keys on selected objects only on channels that already have animation.
    
    Args:
        mode: "all", "translate", "rotate", "scale"
    """
    from anikin import AniSmartKey
    # Delegate to the standalone AniSmartKey with threshold=0.0 to key all animated channels
    AniSmartKey.execute(mode=mode, threshold=0.0)




