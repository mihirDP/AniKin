"""
AniNoise.py
Organic Micro-Jitter Generator — layers procedural Perlin noise onto selected anim curves.
Operates additively to preserve underlying animation.
"""

import math
import random
import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.log import log_debug


def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def lerp(a, b, t):
    return a + t * (b - a)


class Perlin1D:
    """Deterministic 1D Perlin noise generator matching spec."""
    def __init__(self, seed=None):
        rng = random.Random(seed)
        self.p = list(range(256))
        rng.shuffle(self.p)
        self.p *= 2   # double for overflow safety

    def noise(self, x):
        X = int(math.floor(x)) & 255
        x -= math.floor(x)
        u = fade(x)
        a = self.p[X]
        b = self.p[X+1]
        return lerp(self._grad(a, x), self._grad(b, x-1), u)

    def _grad(self, h, x):
        return x if h & 1 else -x


def _get_target_curves(selected_nodes):
    """
    Finds the animCurve nodes to modify.
    Prioritizes active selection in the Graph Editor,
    falling back to all animCurves on the selected objects.
    """
    # Query selected curves in Graph Editor
    ge_curves = cmds.keyframe(query=True, selected=True, name=True) or []
    if ge_curves:
        return list(set(ge_curves))

    # Fallback to all animated channels on selected nodes
    curves = []
    for node in selected_nodes:
        conns = cmds.listConnections(node, type="animCurve", plugs=False) or []
        curves.extend(conns)
    return list(set(curves))


def apply_noise(amplitude=0.3, frequency=0.05, seed=None, step=1, channels_mask=["translate", "rotate", "scale"]):
    """
    Apply organic Perlin noise additively to targets.
    
    Args:
        amplitude: Size of noise.
        frequency: Speed of noise.
        seed: Random seed or integer.
        step: Key frame step (default 1).
        channels_mask: List of channel prefixes to apply noise onto (e.g. ["translate", "rotate"]).
    """
    sel = cmds.ls(selection=True)
    if not sel:
        # Check if we have selected curves directly in Graph Editor
        ge_curves = cmds.keyframe(query=True, selected=True, name=True) or []
        if not ge_curves:
            cmds.warning("AniNoise: Select objects or Graph Editor curves first.")
            return

    curves = _get_target_curves(sel)
    if not curves:
        # If no curves exist on selected objects, we warn and create keys for translation/rotation
        cmds.warning("AniNoise: No animation curves found to add noise onto.")
        return

    # Determine frame range (highlighted region or fallback to playback range)
    import maya.mel as mel
    start, end = None, None
    try:
        gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
        if cmds.timeControl(gPlayBackSlider, query=True, rangeVisible=True):
            rng = cmds.timeControl(gPlayBackSlider, query=True, rangeArray=True)
            start, end = int(rng[0]), int(rng[1])
    except Exception:
        pass

    if start is None:
        start = int(cmds.playbackOptions(query=True, minTime=True))
        end = int(cmds.playbackOptions(query=True, maxTime=True))

    total_frames = end - start
    if total_frames > 500:
        # Warn before operating on ranges > 500 frames
        res = cmds.confirmDialog(
            title="Large Frame Range",
            message="You are about to bake noise across {} frames. This might cause a brief pause. Continue?".format(total_frames),
            button=["Yes", "No"],
            defaultButton="Yes",
            cancelButton="No"
        )
        if res == "No":
            return

    noise_gen = Perlin1D(seed=seed)
    log_debug("AniNoise: Applying Perlin noise (amplitude: {}, frequency: {}, seed: {}, mask: {}) to {} curves".format(
        amplitude, frequency, seed, channels_mask, len(curves)
    ))

    applied_curves_count = 0
    with UndoChunk("AniKin: Apply AniNoise"):
        for curve in curves:
            # Determine the plug/attribute name from curve connection
            plugs = cmds.listConnections(curve, plugs=True, source=False, destination=True) or []
            if not plugs:
                continue
                
            plug = plugs[0] # e.g. "character:ctrl.translateX"
            parts = plug.split(".")
            node_name = parts[0]
            attr_name = ".".join(parts[1:])

            # Verify attribute matches channels_mask
            matched = False
            for m in channels_mask:
                if attr_name.lower().startswith(m.lower()):
                    matched = True
                    break
            if not matched:
                continue

            # Verify attribute exists and is not locked
            if cmds.getAttr(plug, lock=True):
                continue

            applied_curves_count += 1

            for frame in range(start, end + 1, step):
                # Query current value at this frame (using eval=True respects existing keys/tangents)
                try:
                    val = cmds.keyframe(plug, time=(frame, frame), query=True, eval=True)[0]
                except (TypeError, IndexError):
                    val = cmds.getAttr(plug, time=frame)

                # Generate Perlin noise value
                noise_val = noise_gen.noise(frame * frequency) * amplitude
                new_val = val + noise_val

                # Write it back additively
                cmds.setKeyframe(node_name, attribute=attr_name, time=frame, value=new_val)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Added organic noise to {} curves (amp: {}, freq: {})".format(
            applied_curves_count, amplitude, frequency
        ),
        pos="topCenter", fade=True, fadeStayTime=1500
    )
