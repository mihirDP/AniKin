"""
AniSmooth.py
Euler Filter & Curve Smoothing utilities.

- euler_filter(): Fixes rotation gimbal flips
- smooth_curves(): Applies a simple averaging pass to reduce noise in anim curves
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk


def euler_filter():
    """
    Apply Euler filter to selected objects' rotation curves.
    Fixes gimbal lock discontinuities without changing the actual rotation.
    """
    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select animated objects for Euler filter.")
        return

    with UndoChunk("AniKin: Euler Filter"):
        # Get all rotation animation curves on selected objects
        anim_curves = []
        for node in sel:
            curves = cmds.listConnections(node, type="animCurve") or []
            for curve in curves:
                # Only filter rotation curves (TA = Timed/Angular)
                curve_type = cmds.nodeType(curve)
                if curve_type == "animCurveTA":
                    anim_curves.append(curve)

        if anim_curves:
            cmds.filterCurve(anim_curves, filter="euler")

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Euler filter applied to {} curves".format(
            len(anim_curves)
        ),
        pos="topCenter", fade=True, fadeStayTime=1500
    )


def smooth_curves(strength=0.5, iterations=1):
    """
    Smooth animation curves by averaging each key's value with its neighbors.

    Args:
        strength: Blend factor 0.0 (no change) to 1.0 (full average).
        iterations: Number of smoothing passes.
    """
    sel = cmds.ls(selection=True) or []
    if not sel:
        cmds.warning("AniKin: Select animated objects to AniSmooth.")
        return

    with UndoChunk("AniKin: Smooth Curves"):
        for node in sel:
            curves = cmds.listConnections(node, type="animCurve") or []
            for curve in curves:
                key_count = cmds.keyframe(curve, query=True,
                                          keyframeCount=True) or 0
                if key_count < 3:
                    continue

                for _iteration in range(iterations):
                    values = cmds.keyframe(curve, query=True,
                                           valueChange=True) or []
                    times = cmds.keyframe(curve, query=True,
                                          timeChange=True) or []

                    # Smooth interior keys (skip first and last)
                    for i in range(1, len(values) - 1):
                        avg = (values[i - 1] + values[i] + values[i + 1]) / 3.0
                        smoothed = values[i] + (avg - values[i]) * strength
                        cmds.keyframe(curve, edit=True,
                                      time=(times[i], times[i]),
                                      valueChange=smoothed)

    cmds.inViewMessage(
        amg="<hl>AniKin</hl>: Curves smoothed ({} passes)".format(iterations),
        pos="topCenter", fade=True, fadeStayTime=1500
    )

