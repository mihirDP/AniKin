"""
AniCheck.py
Curve Health Diagnostics — scans selected controllers' animation curves for errors.
Detects:
- Gimbal flips / extreme rotation jumps
- Non-integer keyframe times (subframe keys)
- Redundant / duplicate keys (flat islands)
- Non-constant infinity settings
- Zero-length keys (duplicate keys on the same frame)
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.log import log_debug


class Issue(object):
    """Represents a curve diagnostic issue."""
    def __init__(self, category, severity, description, plug, time=None, fix_fn=None):
        self.category = category  # "Gimbal", "Subframe", "Duplicate", "Infinity", "ZeroLength"
        self.severity = severity  # "Critical", "High", "Medium", "Low"
        self.description = description
        self.plug = plug  # e.g. "ctrl.translateX"
        self.time = time
        self.fix_fn = fix_fn

    def fix(self):
        """Execute the automated fix."""
        if self.fix_fn:
            try:
                log_debug("AniCheck: Applying auto-fix for category '{}' on plug '{}' at time '{}'".format(self.category, self.plug, self.time))
                self.fix_fn()
                return True
            except Exception as e:
                cmds.warning("AniCheck: Fix failed: {}".format(e))
                return False
        return False


def _get_animated_plugs(scope="selected"):
    """
    Get animated plugs based on the scope:
    - "selected": Plugs on selected nodes.
    - "all": Plugs on all keyframeable nodes in the scene.
    """
    if scope == "selected":
        nodes = cmds.ls(selection=True)
        if not nodes:
            return []
    else:
        # All transforms in the scene
        nodes = cmds.ls(type="transform")

    plugs = []
    for node in nodes:
        conns = cmds.listConnections(node, type="animCurve", plugs=False,
                                     connections=True, destination=False) or []
        for i in range(0, len(conns), 2):
            plugs.append(conns[i])
    return list(set(plugs))


def run_diagnostics(scope="selected"):
    """
    Scans animation curves based on the selected scope.
    Returns a list of Issue objects.
    """
    log_debug("AniCheck: Running diagnostics (scope: {})".format(scope))
    plugs = _get_animated_plugs(scope)
    issues = []

    start = int(cmds.playbackOptions(query=True, minTime=True))
    end = int(cmds.playbackOptions(query=True, maxTime=True))
    total_frames = end - start + 1

    for plug in plugs:
        # Get matching curve node
        curves = cmds.listConnections(plug, type="animCurve")
        if not curves:
            continue
        curve = curves[0]

        # Query keyframes
        times = cmds.keyframe(plug, query=True, timeChange=True) or []
        values = cmds.keyframe(plug, query=True, valueChange=True) or []
        
        if not times:
            continue

        # 4. Infinite Curves Check
        pre_inf = cmds.setInfinity(curve, query=True, preInfinite=True)[0]
        post_inf = cmds.setInfinity(curve, query=True, postInfinite=True)[0]
        if pre_inf != "constant" or post_inf != "constant":
            def make_inf_fn(c=curve):
                return lambda: fix_infinity(c)
            issues.append(Issue(
                category="Infinity",
                severity="Low",
                description="Infinity is not constant (Pre: {}, Post: {})".format(pre_inf, post_inf),
                plug=plug,
                time=None,
                fix_fn=make_inf_fn()
            ))

        # Key Density Check
        if total_frames > 5:
            key_count = cmds.keyframe(plug, query=True, keyframeCount=True, time=(start, end)) or 0
            density = float(key_count) / total_frames
            if density > 0.9 and key_count > 10:
                issues.append(Issue(
                    category="Density",
                    severity="Medium",
                    description="High key density ({:.0%}) — potential baked curves".format(density),
                    plug=plug,
                    time=None,
                    fix_fn=None
                ))

        for i in range(len(times)):
            t = times[i]
            v = values[i]

            # 1. Non-integer keyframe time (Subframe Key)
            if not float(t).is_integer():
                def make_snap_fn(p=plug, tm=t):
                    return lambda: snap_key_to_integer(p, tm)
                issues.append(Issue(
                    category="Subframe",
                    severity="High",
                    description="Keyframe at subframe {}".format(t),
                    plug=plug,
                    time=t,
                    fix_fn=make_snap_fn()
                ))

            # Look at changes from previous keyframe
            if i > 0:
                prev_t = times[i-1]
                prev_v = values[i-1]
                delta_v = abs(v - prev_v)

                # 5. Zero-length key check (same time, different values)
                if abs(t - prev_t) < 0.0001:
                    def make_zerolen_fn(p=plug, tm=t):
                        return lambda: fix_zero_length_key(p, tm)
                    issues.append(Issue(
                        category="ZeroLength",
                        severity="High",
                        description="Duplicate keyframe at same frame (zero-length)",
                        plug=plug,
                        time=t,
                        fix_fn=make_zerolen_fn()
                    ))

                # 2. Extreme rotation delta (Gimbal Flip)
                elif "rotate" in plug.lower() and delta_v > 170.0:
                    def make_euler_fn(p=plug):
                        return lambda: apply_euler_filter(p)
                    issues.append(Issue(
                        category="Gimbal",
                        severity="Critical",
                        description="Extreme rotation jump of {:.1f}°".format(delta_v),
                        plug=plug,
                        time=t,
                        fix_fn=make_euler_fn()
                    ))

            # 3. Duplicate / dead keyframes (redundant keys)
            if 0 < i < len(times) - 1:
                prev_v = values[i-1]
                next_v = values[i+1]
                if abs(v - prev_v) < 0.0001 and abs(v - next_v) < 0.0001:
                    def make_delete_fn(p=plug, tm=t):
                        return lambda: delete_key(p, tm)
                    issues.append(Issue(
                        category="Duplicate",
                        severity="Medium",
                        description="Redundant keyframe inside flat island",
                        plug=plug,
                        time=t,
                        fix_fn=make_delete_fn()
                    ))

    # Foot Slide Check
    nodes = cmds.ls(selection=True) if scope == "selected" else cmds.ls(type="transform")
    foot_controls = [n for n in nodes if any(term in n.lower() for term in ["foot", "ankle", "heel", "ik"])]
    if foot_controls:
        try:
            from anikin import AniFootSlide
            slide_results = AniFootSlide.detect_foot_slide(foot_controls, start, end)
            for ctrl, events in slide_results.items():
                for start_f, end_f in events:
                    def make_fix_slide_fn(c=ctrl, s=start_f, e=end_f):
                        return lambda: AniFootSlide.fix_foot_slide(c, s, e)
                    issues.append(Issue(
                        category="FootSlide",
                        severity="High",
                        description="Foot slide detected between frames {} and {}".format(start_f, end_f),
                        plug=ctrl,
                        time=start_f,
                        fix_fn=make_fix_slide_fn()
                    ))
        except Exception as e:
            log_debug("AniCheck: Failed to run foot slide detection: {}".format(e))

    return issues



# —— Automated Fix Functions ————————————————————————————————

def snap_key_to_integer(plug, time_val):
    """Snap a specific key to the nearest integer frame."""
    target_time = round(time_val)
    with UndoChunk("AniCheck: Snap Key to Integer"):
        cmds.keyframe(plug, time=(time_val, time_val), edit=True, timeChange=target_time)


def apply_euler_filter(plug):
    """Apply Maya's Euler Filter to the curve."""
    with UndoChunk("AniCheck: Apply Euler Filter"):
        cmds.filterCurve(plug)


def delete_key(plug, time_val):
    """Delete key at a specific time."""
    with UndoChunk("AniCheck: Delete Redundant Key"):
        cmds.cutKey(plug, time=(time_val, time_val), clear=True)


def fix_infinity(curve):
    """Reset curve pre/post infinity to Constant."""
    with UndoChunk("AniCheck: Fix Infinity"):
        cmds.setInfinity(curve, preInfinite="constant", postInfinite="constant")


def fix_zero_length_key(plug, time_val):
    """Resolve zero-length key by keeping the last key at the frame."""
    with UndoChunk("AniCheck: Resolve Zero-length Key"):
        # cutKey clears duplicate keys at that exact time index
        # We can also keyframe query index and delete the redundant index
        # Maya cutKey with index query does the job perfectly
        cmds.cutKey(plug, time=(time_val, time_val))
        # Drop a single key at that frame with the latest attribute value
        val = cmds.getAttr(plug)
        cmds.setKeyframe(plug, time=time_val, value=val)
