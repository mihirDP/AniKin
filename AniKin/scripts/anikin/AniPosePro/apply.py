"""
apply.py — All pose apply modes for AniPose Pro.

apply_pose_full()      — apply all channels (F-PL-02/03)
apply_pose_partial()   — apply Channel Box selection only (F-PL-05)
apply_pose_mirror()    — apply to mirror side via AniMirror (F-PL-06)
apply_pose_additive()  — add delta values on top of current (F-PL-12)

All apply functions:
  • Push the pre-apply state to the history stack.
  • Wrap setAttr calls in a single undoInfo chunk → one Ctrl+Z undoes the whole op.
  • Are namespace-aware: saved namespace is stripped and the scene's namespace applied.
"""

import maya.cmds as cmds
from anikin.AniPosePro.history import get_history
from anikin.AniMirror.core import find_mirror_pair

# Attributes that must be negated when mirroring (standard character rig convention)
NEGATE_ON_MIRROR = {"translateX", "translateZ", "rotateY"}


# ── Namespace helpers ──────────────────────────────────────────────────────────

def _scene_namespace(nodes):
    """Return the namespace of the first namespaced node, or ''."""
    for n in nodes:
        short = n.split("|")[-1]
        if ":" in short:
            return short.split(":")[0]
    return ""


def _resolve_node(ctrl_no_ns, scene_ns):
    """
    Map a saved control name (no namespace) to a scene node.
    Returns the full node name if it exists, else None.
    """
    candidate = "{}:{}".format(scene_ns, ctrl_no_ns) if scene_ns else ctrl_no_ns
    return candidate if cmds.objExists(candidate) else None


# ── Core apply helpers ────────────────────────────────────────────────────────

def _set_attr_safe(full_attr, val):
    """setAttr with lock guard. Returns True on success."""
    try:
        if cmds.getAttr(full_attr, lock=True):
            return False
        cmds.setAttr(full_attr, val)
        return True
    except Exception:
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def apply_pose_full(pose_data, nodes, as_keyframe=False, key_tangent="step",
                    pose_name="pose"):
    """
    Apply all channels from pose_data to the current scene.

    Args:
        pose_data:    Loaded .pose dict (from library.load_pose_data).
        nodes:        Selected Maya nodes (long names).
        as_keyframe:  If True, setKeyframe after each setAttr (F-PL-03).
        key_tangent:  Tangent type when as_keyframe=True.
        pose_name:    Used for the history label.
    """
    scene_ns = _scene_namespace(nodes)
    history = get_history()
    history.push(nodes, label="Before applying '{}'".format(pose_name))

    applied = 0
    skipped = []

    cmds.undoInfo(openChunk=True, chunkName="AniKin_PoseApply")
    try:
        for ctrl, channels in pose_data.get("controls", {}).items():
            node = _resolve_node(ctrl, scene_ns)
            if node is None:
                skipped.append(ctrl)
                continue

            for attr, val in channels.items():
                full = "{}.{}".format(node, attr)
                if not cmds.objExists(full):
                    continue
                if _set_attr_safe(full, val):
                    if as_keyframe:
                        cmds.setKeyframe(full, inTangentType=key_tangent,
                                         outTangentType=key_tangent)
                    applied += 1
                else:
                    skipped.append("{}.{}".format(ctrl, attr))
    finally:
        cmds.undoInfo(closeChunk=True)

    _feedback(applied, skipped)


def apply_pose_partial(pose_data, nodes, channel_filter=None, pose_name="pose"):
    """
    Apply only selected channels (from Channel Box or explicit list) — F-PL-05.

    Falls back to full apply if no channel filter is active.
    """
    if channel_filter is None:
        channel_filter = (cmds.channelBox("mainChannelBox", q=True,
                                          selectedMainAttributes=True) or [])
    if not channel_filter:
        cmds.warning("AniPose Pro: No channel filter active — running full apply.")
        apply_pose_full(pose_data, nodes, pose_name=pose_name)
        return

    scene_ns = _scene_namespace(nodes)
    history  = get_history()
    history.push(nodes, label="Before partial apply '{}'".format(pose_name))

    applied = 0
    cmds.undoInfo(openChunk=True, chunkName="AniKin_PoseApplyPartial")
    try:
        for ctrl, channels in pose_data.get("controls", {}).items():
            node = _resolve_node(ctrl, scene_ns)
            if node is None:
                continue
            for attr in channel_filter:
                if attr not in channels:
                    continue
                full = "{}.{}".format(node, attr)
                if _set_attr_safe(full, channels[attr]):
                    applied += 1
    finally:
        cmds.undoInfo(closeChunk=True)

    cmds.inViewMessage(
        amg="<hl>AniPose Pro</hl>: Partial apply — {} channels".format(applied),
        pos="topCenter", fade=True, fadeStayTime=1200
    )


def apply_pose_mirror(pose_data, nodes, pose_name="pose"):
    """
    Apply pose values to the mirror-side controls — F-PL-06.
    Uses AniMirror's find_mirror_pair() and NEGATE_ON_MIRROR convention.
    """
    scene_ns = _scene_namespace(nodes)
    history  = get_history()
    history.push(nodes, label="Before mirror apply '{}'".format(pose_name))

    applied = 0
    cmds.undoInfo(openChunk=True, chunkName="AniKin_PoseMirrorApply")
    try:
        for ctrl, channels in pose_data.get("controls", {}).items():
            node = _resolve_node(ctrl, scene_ns)
            if node is None:
                continue
            mirror = find_mirror_pair(node)
            if mirror is None:
                continue
            for attr, val in channels.items():
                mirrored_val = -val if attr in NEGATE_ON_MIRROR else val
                full = "{}.{}".format(mirror, attr)
                if _set_attr_safe(full, mirrored_val):
                    applied += 1
    finally:
        cmds.undoInfo(closeChunk=True)

    cmds.inViewMessage(
        amg="<hl>AniPose Pro</hl>: Mirror apply — {} channels".format(applied),
        pos="topCenter", fade=True, fadeStayTime=1200
    )


def apply_pose_additive(pose_data, nodes, pose_name="pose"):
    """
    Add delta values stored in pose_data on top of current rig values — F-PL-12.
    Works whether the pose was saved in additive mode or not (Alt+apply).
    """
    scene_ns = _scene_namespace(nodes)
    history  = get_history()
    history.push(nodes, label="Before additive apply '{}'".format(pose_name))

    applied = 0
    cmds.undoInfo(openChunk=True, chunkName="AniKin_PoseAdditiveApply")
    try:
        for ctrl, channels in pose_data.get("controls", {}).items():
            node = _resolve_node(ctrl, scene_ns)
            if node is None:
                continue
            for attr, delta in channels.items():
                full = "{}.{}".format(node, attr)
                if not cmds.objExists(full):
                    continue
                try:
                    current = cmds.getAttr(full)
                    if _set_attr_safe(full, current + delta):
                        applied += 1
                except Exception:
                    pass
    finally:
        cmds.undoInfo(closeChunk=True)

    cmds.inViewMessage(
        amg="<hl>AniPose Pro</hl>: Additive apply — {} channels".format(applied),
        pos="topCenter", fade=True, fadeStayTime=1200
    )


# ── Blend helpers (used by the UI's MMB drag) ─────────────────────────────────

class PoseBlender:
    """
    Manages MMB drag blending between the current rig state and a library pose.
    Call begin_blend() on MMB press, update_blend(t) during drag, commit_blend() on release.
    """

    def __init__(self):
        self._snapshot  = {}
        self._pose_data = {}
        self._nodes     = []
        self._scene_ns  = ""
        self._active    = False

    def begin_blend(self, pose_data, nodes):
        self._pose_data = pose_data
        self._nodes     = nodes
        self._scene_ns  = _scene_namespace(nodes)
        self._snapshot  = {}

        for node in nodes:
            self._snapshot[node] = {}
            for attr in (cmds.listAttr(node, keyable=True) or []):
                full = "{}.{}".format(node, attr)
                try:
                    val = cmds.getAttr(full)
                    if not isinstance(val, list):
                        self._snapshot[node][attr] = val
                except Exception:
                    pass

        self._active = True
        cmds.undoInfo(openChunk=True, chunkName="AniKin_PoseBlend")

    def update_blend(self, t):
        """t: 0.0 = current pose, 1.0 = full library pose."""
        if not self._active:
            return
        for ctrl, channels in self._pose_data.get("controls", {}).items():
            node = _resolve_node(ctrl, self._scene_ns)
            if node is None or node not in self._snapshot:
                continue
            for attr, target in channels.items():
                current = self._snapshot[node].get(attr)
                if current is None:
                    continue
                blended = current + (target - current) * t
                try:
                    cmds.setAttr("{}.{}".format(node, attr), blended)
                except Exception:
                    pass

    def commit_blend(self, t):
        if not self._active:
            return
        self.update_blend(t)
        self._active = False
        cmds.undoInfo(closeChunk=True)

    def cancel_blend(self):
        if not self._active:
            return
        for node, attrs in self._snapshot.items():
            for attr, val in attrs.items():
                try:
                    cmds.setAttr("{}.{}".format(node, attr), val)
                except Exception:
                    pass
        self._active = False
        cmds.undoInfo(closeChunk=True)


# Module-level blender singleton
_blender = PoseBlender()

def begin_blend(pose_data, nodes):  _blender.begin_blend(pose_data, nodes)
def update_blend(t):                _blender.update_blend(t)
def commit_blend(t):                _blender.commit_blend(t)
def cancel_blend():                 _blender.cancel_blend()


# ── Feedback helper ────────────────────────────────────────────────────────────

def _feedback(applied, skipped):
    if skipped:
        cmds.warning("AniPose Pro: {} attr(s) skipped.".format(len(skipped)))
    cmds.inViewMessage(
        amg="<hl>AniPose Pro</hl>: Applied {} channel(s)".format(applied),
        pos="topCenter", fade=True, fadeStayTime=1200
    )


def apply_pose_sequence(poses_data_list, nodes, start_frame, interval):
    """F-NEW-02: Apply multiple poses sequentially at intervals."""
    cmds.undoInfo(openChunk=True, chunkName="AniKin_PoseSequence")
    try:
        for i, pose_data in enumerate(poses_data_list):
            frame = start_frame + i * interval
            cmds.currentTime(frame)
            # Apply as keyframe with step tangent
            apply_pose_full(pose_data, nodes, as_keyframe=True, key_tangent="step")
            
        cmds.inViewMessage(amg=f"<hl>AniPose Pro</hl>: Sequenced {len(poses_data_list)} poses.", pos="topCenter", fade=True, fadeStayTime=1200)
    finally:
        cmds.undoInfo(closeChunk=True)
