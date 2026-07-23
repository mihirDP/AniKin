"""
AniPose Pro — The Complete Pose & Animation Library System.
Successor to AniSnap. Fully disk-backed, thumbnailed, and team-ready.

NOTE: All imports here are DEFERRED to avoid circular dependency chains.
The ui/ and library/ sub-packages import each other's widgets, so we must
not eagerly pull them in at package-init time.
"""

# ── Safe top-level imports (no circular risk) ─────────────────────────────────
from .apply import apply_pose_full, apply_pose_partial, apply_pose_mirror, apply_pose_additive
from .history import get_history
from .quick_snap import QuickSnapManager
from .thumbnail import capture_viewport_thumbnail

# V2 Animation Capture
from .capture import capture_anim_clip, save_clip_to_disk, load_clip_data
from .paste import paste_clip_at_frame, paste_legacy_clip
from .clip_slots import get_clip_slots
from .splice import trim_clip, join_clips
from .instancing import record_instance, get_instances_for_clip, update_all_instances
from .pose_brush import activate_pose_brush, deactivate_pose_brush


# ── Lazy accessors (break circular import chains) ────────────────────────────

def PoseLibrary(*args, **kwargs):
    """Lazy constructor for PoseLibrary to avoid circular imports."""
    from .library.pose_library import PoseLibrary as _PL
    return _PL(*args, **kwargs)


def show_panel():
    """Lazy launcher for the AniPose Pro UI panel."""
    from .ui.panel import show_panel as _sp
    return _sp()


__all__ = [
    "show_panel",
    "PoseLibrary",
    "apply_pose_full",
    "apply_pose_partial",
    "apply_pose_mirror",
    "apply_pose_additive",
    "get_history",
    "QuickSnapManager",
    "capture_viewport_thumbnail",
    "capture_anim_clip",
    "save_clip_to_disk",
    "load_clip_data",
    "paste_clip_at_frame",
    "paste_legacy_clip",
    "get_clip_slots",
    "trim_clip",
    "join_clips",
    "record_instance",
    "get_instances_for_clip",
    "update_all_instances",
    "activate_pose_brush",
    "deactivate_pose_brush",
]
