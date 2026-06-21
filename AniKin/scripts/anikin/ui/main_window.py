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
"""

import maya.cmds as cmds

from anikin.core.qt_compat import (
    QtWidgets, QtCore, MayaQWidgetDockableMixin
)
from anikin.ui.theme import STYLESHEET
from anikin.ui.widgets import (
    SectionSeparator, SectionLabel, ToolButton, TweenSlider
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
        self.toolbar_layout.setSpacing(4)

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
        self.toolbar_layout.addWidget(SectionLabel("Transform"))
        self.toolbar_layout.addWidget(ToolButton(
            "Align", "Align selected objects to the last selected\n(Translate + Rotate)",
            callback=lambda: align.execute(translate=True, rotate=True)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "AlignT", "Align Translation only",
            callback=lambda: align.execute(translate=True, rotate=False)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "AlignR", "Align Rotation only",
            callback=lambda: align.execute(translate=False, rotate=True)
        ))

    def _add_tangents_section(self):
        self.toolbar_layout.addWidget(SectionLabel("Tangents"))
        for ttype, tip in [
            ("auto", "Set tangent to Auto"),
            ("flat", "Set tangent to Flat (holds)"),
            ("linear", "Set tangent to Linear"),
            ("step", "Set tangent to Stepped (pose-to-pose)"),
            ("spline", "Set tangent to Spline"),
        ]:
            self.toolbar_layout.addWidget(ToolButton(
                ttype.capitalize(), tip,
                callback=lambda t=ttype: tangents.set_tangent(t)
            ))

    def _add_timing_section(self):
        self.toolbar_layout.addWidget(SectionLabel("Timing"))
        self.toolbar_layout.addWidget(ToolButton(
            "◀", "Nudge keyframes 1 frame left",
            callback=lambda: nudge.execute(-1)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "▶", "Nudge keyframes 1 frame right",
            callback=lambda: nudge.execute(1)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "◀◀", "Nudge keyframes 5 frames left",
            callback=lambda: nudge.execute(-5)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "▶▶", "Nudge keyframes 5 frames right",
            callback=lambda: nudge.execute(5)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "Offset", "Stagger keys across selection by 2 frames\n(Select 2+ animated objects)",
            callback=lambda: anim_offset.execute(offset_frames=2)
        ))

    def _add_tween_section(self):
        self.tween_slider = TweenSlider()
        self.tween_slider.value_changed.connect(self._on_tween)
        self.toolbar_layout.addWidget(self.tween_slider)

    def _add_workflow_section(self):
        self.toolbar_layout.addWidget(SectionLabel("Workflow"))
        self.toolbar_layout.addWidget(ToolButton(
            "Bake→Loc", "Smart Bake: Bake selected object's world-space\nmotion to a locator",
            callback=smart_bake.bake_to_locator
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "Loc→Obj", "Smart Bake Back: Select target then locator,\nbake locator motion onto target",
            callback=smart_bake.bake_from_locator
        ))

    def _add_channels_section(self):
        self.toolbar_layout.addWidget(SectionLabel("Channels"))
        self.toolbar_layout.addWidget(ToolButton(
            "🔒", "Lock highlighted channels\n(or all keyable if none highlighted)",
            callback=channels.lock_channels
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "🔓", "Unlock highlighted channels",
            callback=channels.unlock_channels
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "Key", "Set keyframe on highlighted channels",
            callback=channels.key_channels,
            accent=True
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "DelKey", "Delete keyframe at current time\non highlighted channels",
            callback=channels.delete_keys
        ))

    def _add_curves_section(self):
        self.toolbar_layout.addWidget(SectionLabel("Curves"))
        self.toolbar_layout.addWidget(ToolButton(
            "Euler", "Fix rotation gimbal flips (Euler Filter)",
            callback=smooth.euler_filter
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "Smooth", "Smooth animation curves (reduce noise)",
            callback=lambda: smooth.smooth_curves(strength=0.5, iterations=1)
        ))

    def _add_vis_section(self):
        self.toolbar_layout.addWidget(SectionLabel("Vis"))
        trail_btn = ToolButton(
            "Trail", "Toggle Motion Trail for selected object\n(Right-click for options)",
            callback=motion_trail.toggle_motion_trail
        )
        trail_btn.set_context_menu([
            ("Clear All Motion Trails", motion_trail.clear_all),
            (None, None),
            ("Configure Motion Trail...", lambda: settings_panel.show_panel(active_tab=1, on_apply_callback=self.rebuild_toolbar))
        ])
        self.toolbar_layout.addWidget(trail_btn)

        ghost_btn = ToolButton(
            "Ghost", "Toggle Ghosting for selected object\n(Right-click for options)",
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
            "Sel Sets", "Open Selection Sets panel\n(Save/recall named selection groups)",
            callback=selection_sets_panel.show_panel,
            accent=True
        ))

    def _add_setup_section(self):
        self.toolbar_layout.addWidget(SectionLabel("Setup"))
        
        self.toolbar_layout.addWidget(ToolButton(
            "Hotkeys", "Open Hotkey Manager\n(Bind custom keyboard shortcuts to AniKin actions)",
            callback=hotkey_panel.show_panel
        ))

        settings_btn = ToolButton(
            "⚙", "Open Settings & Preferences\n(Customize Layout, Motion Trails, and Ghosting)",
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
