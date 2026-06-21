"""
main_window.py
AniKin Main Dockable Window.

This is the primary UI — a horizontal toolbar that docks to the bottom
of Maya's viewport (above the timeline), similar in layout to professional
animator toolbelts.

Architecture notes:
- Uses MayaQWidgetDockableMixin for native Maya docking
- Global reference (_INSTANCE) prevents Python GC from destroying the UI
- Workspace control names are carefully managed to avoid Maya's notorious
  "name is not unique" error
- All tool callbacks are connected here — the window is the "wiring" layer
  between UI widgets and tool logic
- v0.2.0: Icon-only toolbar with color-coded category grouping.
  Section labels removed per UIUX 2.0 Icon Language Guide.
"""

import maya.cmds as cmds

from anikin.core.qt_compat import (
    QtWidgets, QtCore, MayaQWidgetDockableMixin
)
from anikin.ui.theme import STYLESHEET
from anikin.ui.widgets import (
    SectionSeparator, ToolButton, TweenSlider
)

# Tool imports
from anikin.tools import align
from anikin.tools import tween
from anikin.tools import anim_offset
from anikin.tools import tangents
from anikin.tools import smart_bake
from anikin.tools import nudge
from anikin.tools import channels
from anikin.tools import smooth
from anikin.tools import motion_trail
from anikin.tools import ghosting
from anikin.tools import pose
from anikin.tools import key_nav
from anikin.ui import selection_sets_panel
from anikin.ui import settings_panel
from anikin.ui import hotkey_panel
from anikin.core import settings


# ──────────────────────────────────────────────────────────────
# Window class
# ──────────────────────────────────────────────────────────────

class AniKinWindow(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """Main AniKin dockable toolbar window."""

    WINDOW_NAME = "AniKinToolbar"
    WINDOW_TITLE = "AniKin"

    def __init__(self, parent=None):
        super(AniKinWindow, self).__init__(parent)

        self.setObjectName(self.WINDOW_NAME)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumHeight(44)

        self._build_ui()
        self.setStyleSheet(STYLESHEET)

    # ── UI Construction ───────────────────────────────────────

    def _build_ui(self):
        """Setup the outer structures and prepare the layout."""
        # Outer wrapper — QVBoxLayout holds a QFrame that enforces min height
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.toolbar_frame = QtWidgets.QFrame()
        self.toolbar_frame.setObjectName("AniKinToolbar")
        self.toolbar_frame.setMinimumHeight(40)
        outer.addWidget(self.toolbar_frame)

        # Inner horizontal layout — all tools sit here
        self.toolbar_layout = QtWidgets.QHBoxLayout(self.toolbar_frame)
        self.toolbar_layout.setContentsMargins(6, 3, 6, 3)
        self.toolbar_layout.setSpacing(3)

        # Populate toolbar dynamically
        self.rebuild_toolbar()

    def _clear_layout(self, layout):
        """Recursively remove and delete all child widgets and sub-layouts."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
                else:
                    sub_layout = item.layout()
                    if sub_layout is not None:
                        self._clear_layout(sub_layout)

    def rebuild_toolbar(self):
        """Clear and rebuild the toolbar widgets dynamically based on user settings."""
        self._clear_layout(self.toolbar_layout)

        # Load layout configuration
        cfg = settings.load_settings()
        order = cfg["section_order"]
        visible = cfg["visible_sections"]

        first = True
        for sec in order:
            if sec not in visible:
                continue

            if not first:
                self.toolbar_layout.addWidget(SectionSeparator())
            first = False

            if sec == "Transform":
                self._add_transform_section()
            elif sec == "Tangents":
                self._add_tangents_section()
            elif sec == "Timing":
                self._add_timing_section()
            elif sec == "Tween Slider":
                self._add_tween_section()
            elif sec == "Workflow":
                self._add_workflow_section()
            elif sec == "Channels":
                self._add_channels_section()
            elif sec == "Curves":
                self._add_curves_section()
            elif sec == "Vis":
                self._add_vis_section()
            elif sec == "Sets":
                self._add_sets_section()
            elif sec == "Setup":
                self._add_setup_section()

        # Re-add stretch at the end
        self.toolbar_layout.addStretch()

    # ── Section Builder Helpers ───────────────────────────────

    def _add_transform_section(self):
        # Reset transform (first so it's the "undo" position)
        self.toolbar_layout.addWidget(ToolButton(
            "reset", "Reset all transforms to default (0 / scale 1)",
            callback=pose.reset_transform
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "align_all", "Align selected → last (Translate + Rotate)",
            callback=lambda: align.execute(translate=True, rotate=True)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "align_translate", "Align Translation only",
            callback=lambda: align.execute(translate=True, rotate=False)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "align_rotate", "Align Rotation only",
            callback=lambda: align.execute(translate=False, rotate=True)
        ))
        # Pose tools (copy/paste/mirror)
        self.toolbar_layout.addWidget(ToolButton(
            "copy_pose", "Copy Pose to clipboard",
            callback=pose.copy_pose
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "paste_pose", "Paste Pose from clipboard",
            callback=pose.paste_pose
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "mirror_pose", "Mirror Pose (negate TX/TZ/RY)",
            callback=pose.mirror_pose
        ))

    def _add_tangents_section(self):
        for ttype, icon, tip in [
            ("auto",   "auto",   "Auto tangent"),
            ("flat",   "flat",   "Flat tangent (hold)"),
            ("linear", "linear", "Linear tangent"),
            ("step",   "step",   "Stepped tangent (pose-to-pose)"),
            ("spline", "spline", "Spline tangent"),
        ]:
            self.toolbar_layout.addWidget(ToolButton(
                icon, tip,
                callback=lambda t=ttype: tangents.set_tangent(t)
            ))

    def _add_timing_section(self):
        # Key navigation: prev/next key, first/last key
        self.toolbar_layout.addWidget(ToolButton(
            "first_key", "Jump to first keyframe",
            callback=key_nav.goto_first_key
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "prev_key", "Jump to previous keyframe",
            callback=key_nav.goto_prev_key
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "next_key", "Jump to next keyframe",
            callback=key_nav.goto_next_key
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "last_key", "Jump to last keyframe",
            callback=key_nav.goto_last_key
        ))
        # Nudge keys
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_left", "Nudge keys 1 frame earlier",
            callback=lambda: nudge.execute(-1)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_right", "Nudge keys 1 frame later",
            callback=lambda: nudge.execute(1)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_left_fast", "Nudge keys 5 frames earlier",
            callback=lambda: nudge.execute(-5)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_right_fast", "Nudge keys 5 frames later",
            callback=lambda: nudge.execute(5)
        ))
        # Anim offset
        self.toolbar_layout.addWidget(ToolButton(
            "offset", "Stagger keys across selection (+2 frames each)",
            callback=lambda: anim_offset.execute(offset_frames=2)
        ))

    def _add_tween_section(self):
        self.tween_slider = TweenSlider()
        self.tween_slider.value_changed.connect(self._on_tween)
        self.toolbar_layout.addWidget(self.tween_slider)

    def _add_workflow_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "bake_to_locator", "Smart Bake: Bake world-space motion → locator",
            callback=smart_bake.bake_to_locator
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "bake_from_locator", "Smart Bake: Paste locator motion → object",
            callback=smart_bake.bake_from_locator
        ))

    def _add_channels_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "lock", "Lock channels",
            callback=channels.lock_channels
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "unlock", "Unlock channels",
            callback=channels.unlock_channels
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "key", "Set keyframe on channels",
            callback=channels.key_channels,
            accent=True
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "delkey", "Delete keyframe at current time",
            callback=channels.delete_keys
        ))

    def _add_curves_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "euler", "Euler Filter — fix rotation flips",
            callback=smooth.euler_filter
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "smooth", "Smooth animation curves",
            callback=lambda: smooth.smooth_curves(strength=0.5, iterations=1)
        ))

    def _add_vis_section(self):
        trail_btn = ToolButton(
            "trail", "Toggle Motion Trail\n(Right-click for options)",
            callback=motion_trail.toggle_motion_trail
        )
        trail_btn.set_context_menu([
            ("Clear All Motion Trails", motion_trail.clear_all),
            (None, None),
            ("Configure Motion Trail...", lambda: settings_panel.show_panel(active_tab=1, on_apply_callback=self.rebuild_toolbar))
        ])
        self.toolbar_layout.addWidget(trail_btn)

        ghost_btn = ToolButton(
            "ghost", "Toggle Ghosting\n(Right-click for options)",
            callback=ghosting.toggle_ghosting
        )
        ghost_btn.set_context_menu([
            ("Clear All Ghosting", ghosting.clear_all),
            (None, None),
            ("Configure Ghosting...", lambda: settings_panel.show_panel(active_tab=2, on_apply_callback=self.rebuild_toolbar))
        ])
        self.toolbar_layout.addWidget(ghost_btn)

    def _add_sets_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "selection_sets", "Selection Sets panel",
            callback=selection_sets_panel.show_panel,
            accent=True
        ))

    def _add_setup_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "hotkeys", "Hotkey Manager",
            callback=hotkey_panel.show_panel
        ))

        settings_btn = ToolButton(
            "settings", "Settings & Preferences\n(Layout, Trails, Ghosting)",
            callback=lambda: settings_panel.show_panel(active_tab=0, on_apply_callback=self.rebuild_toolbar)
        )
        self.toolbar_layout.addWidget(settings_btn)

    # ── Tween callback ────────────────────────────────────────

    def _on_tween(self, bias):
        """Called as the tween slider is dragged."""
        tween.apply_tween(bias)


# ──────────────────────────────────────────────────────────────
# Launch / cleanup
# ──────────────────────────────────────────────────────────────

# Global reference prevents Python GC from destroying the widget
_INSTANCE = None


def _cleanup_existing():
    """
    Delete any lingering workspace controls from previous launches.
    Handles Maya's notorious "name is not unique" error by checking
    all possible name variants.
    """
    possible_names = [
        AniKinWindow.WINDOW_NAME + "WorkspaceControl",
        AniKinWindow.WINDOW_NAME,
    ]
    for name in possible_names:
        try:
            if cmds.workspaceControl(name, exists=True):
                cmds.deleteUI(name)
        except Exception:
            pass
        try:
            if cmds.workspaceControl(name, exists=True):
                cmds.workspaceControlState(name, remove=True)
        except Exception:
            pass


def show_window():
    """
    Launch (or relaunch) the AniKin toolbar.
    This is the main entry point called by anikin.launch().
    """
    global _INSTANCE

    _cleanup_existing()

    _INSTANCE = AniKinWindow()
    _INSTANCE.show(
        dockable=True,
        area="bottom",
        floating=False,
        height=44,
        width=900,
        label=AniKinWindow.WINDOW_TITLE,
    )

    # Load and register user hotkeys
    try:
        from anikin.tools import hotkeys
        hotkeys.load_hotkeys()
    except Exception as e:
        cmds.warning("AniKin: Error loading hotkeys: {}".format(e))

    print("[AniKin] Toolbar launched. v{}".format(
        __import__("anikin").__version__
    ))
