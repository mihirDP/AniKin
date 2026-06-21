"""
AniWave.py
Overlap / Follow-Through Propagator — propagates animation down a joint/control chain
with automated time offset, amplitude decay, tip damping, and reverse propagation options.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn


def _get_animated_channels(node, mask=None):
    """Return animated attribute names on the node, optionally filtered by prefix list (mask)."""
    connections = cmds.listConnections(node, type="animCurve", plugs=False,
                                       connections=True, destination=False) or []
    attrs = []
    for i in range(0, len(connections), 2):
        plug = connections[i]
        attr = plug.split(".")[-1]
        
        # Apply mask filter (e.g. "rotate", "translate", "scale")
        if mask:
            matched = False
            for m in mask:
                if attr.lower().startswith(m.lower()):
                    matched = True
                    break
            if not matched:
                continue
                
        attrs.append(attr)
    return list(set(attrs))


def propagate_wave(offset_frames=2.0, amplitude_falloff=0.8, channels_mask=["translate", "rotate"], tip_damping=False, reverse_mode=False):
    """
    Copy animation from the source end of the selection to the targets,
    applying time offsets and amplitude scale decay.
    
    Args:
        offset_frames: Frame delay per step (positive staggers downstream/upstream).
        amplitude_falloff: Decay multiplier per step (0.5 to 1.5).
        channels_mask: List of channel prefixes to propagate (e.g. ["rotate"]).
        tip_damping: If True, applies extra 50% falloff to the last two joints in the chain.
        reverse_mode: If True, propagates animation from tip to root (end to start of selection).
    """
    sel = get_selected_or_warn(min_count=2)
    if not sel:
        return

    # In reverse mode, the source is the last object, targets are the preceding ones reversed
    if reverse_mode:
        source = sel[-1]
        targets = list(reversed(sel[:-1]))
    else:
        source = sel[0]
        targets = sel[1:]
        
    animated_attrs = _get_animated_channels(source, mask=channels_mask)
    if not animated_attrs:
        cmds.warning("AniWave: Source object '{}' has no animated channels matching filter {}.".format(source, channels_mask))
        return

    with UndoChunk("AniKin: AniWave Propagate"):
        for i, target in enumerate(targets):
            step = i + 1
            curr_offset = step * offset_frames
            
            # Calculate falloff multiplier
            curr_scale = amplitude_falloff ** step
            if tip_damping and i >= len(targets) - 2:
                # Extra 50% decay for tip damping on the final 2 joints
                curr_scale *= 0.5

            for attr in animated_attrs:
                target_attr = "{}.{}".format(target, attr)
                if not cmds.objExists(target_attr) or cmds.getAttr(target_attr, lock=True):
                    continue
                
                # Copy keyframes from source
                cmds.copyKey(source, attribute=attr)
                # Paste keyframes to target (replacing existing)
                cmds.pasteKey(target, attribute=attr, option="replace")
                
                # Shift time offset
                cmds.keyframe(target, attribute=attr, edit=True, timeChange=curr_offset)
                
                # Decay keyframe values (scale keys around 0)
                cmds.scaleKey(target, attribute=attr, valueScale=curr_scale, valuePivot=0.0)
                
                # Re-run tangent auto to prevent linear snapping issues
                try:
                    cmds.keyTangent(target, attribute=attr, outTangentType="auto")
                except Exception:
                    pass

    msg = "AniWave propagated (offset: {}, decay: {:.0%})".format(offset_frames, amplitude_falloff)
    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: " + msg,
        pos="topCenter", fade=True, fadeStayTime=2000
    )
    print("[AniKin] " + msg)
