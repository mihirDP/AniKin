"""
main_window.py
AniKin Main Dockable Window.

This is the primary UI â€” a horizontal toolbar that docks to the bottom
of Maya's viewport (above the timeline), similar in layout to professional
animator toolbelts.

Architecture notes:
- Uses MayaQWidgetDockableMixin for native Maya docking
- Global reference (_INSTANCE) prevents Python GC from destroying the UI
- Workspace control names are carefully managed to avoid Maya's notorious
  "name is not unique" error
- All tool callbacks are connected here â€” the window is the "wiring" layer
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
    SectionSeparator, ToolButton, TweenSlider, FlowLayout
)

# Tool imports
from anikin import AniAlign
from anikin import AniTween
from anikin import AniOffset
from anikin import AniTangents
from anikin import AniBake
from anikin import AniNudge
from anikin import AniChannels
from anikin import AniSmooth
from anikin import AniMotion
from anikin import AniGhost
from anikin import AniMirror
from anikin import AniKeyNav
from anikin import AniBookmarks
from anikin import AniWave
from anikin import AniNoise
from anikin import AniCheck
from anikin import AniSnap
from anikin import AniGround
from anikin import AniCleanup
from anikin import AniDuplicate
from anikin import AniExport
from anikin.ui import selection_sets_panel
from anikin.ui import bookmarks_panel
from anikin.ui import check_panel
from anikin.ui import snap_panel
from anikin.ui import wave_panel
from anikin.ui import noise_panel
from anikin.ui import settings_panel
from anikin.ui import hotkey_panel
from anikin.core import settings



# ──────────────────────────────────────────────────────────────────────────────────
# Window class
# ──────────────────────────────────────────────────────────────────────────────────

class AniKinWindow(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """Main AniKin dockable toolbar window."""

    WINDOW_NAME = "AniKinToolbar"
    WINDOW_TITLE = "AniKin"

    def __init__(self, parent=None):
        super(AniKinWindow, self).__init__(parent)

        self.setObjectName(self.WINDOW_NAME)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumHeight(52)

        self._build_ui()
        self.setStyleSheet(STYLESHEET)

    # ── UI Construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        """Setup the outer structures and prepare the layout."""
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Scroll area allows the toolbar to wrap to two rows without clipping
        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; }")
        outer.addWidget(self._scroll)

        self.toolbar_frame = QtWidgets.QWidget()
        self.toolbar_frame.setObjectName("AniKinToolbar")
        self._scroll.setWidget(self.toolbar_frame)

        # FlowLayout: buttons wrap to next row automatically
        self.toolbar_layout = FlowLayout(self.toolbar_frame, margin=4, spacing=3)

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
            elif sec == "Bookmarks":
                self._add_bookmarks_section()
            elif sec == "Poses":
                self._add_poses_section()
            elif sec == "Diagnostics":
                self._add_diagnostics_section()
            elif sec == "Pipeline":
                self._add_pipeline_section()
            elif sec == "Setup":
                self._add_setup_section()

    # ── Section Builder Helpers ─────────────────────────────────────────────────

    def _add_transform_section(self):
        # Reset transform (first so it's the "undo" position)
        self.toolbar_layout.addWidget(ToolButton(
            "reset", "Reset Pose (zero out translations/rotations)",
            callback=AniMirror.reset_transform
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "align_all", "Align selected â†’ last (Translate + Rotate)",
            callback=lambda: AniAlign.execute(translate=True, rotate=True)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "align_translate", "Align Translation only",
            callback=lambda: AniAlign.execute(translate=True, rotate=False)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "align_rotate", "Align Rotation only",
            callback=lambda: AniAlign.execute(translate=False, rotate=True)
        ))
        # Grounding tool
        ground_btn = ToolButton(
            "ground", "AniGround: Ground selected objects (lowest bbox point to Y=0)\n(Right-click for options)",
            callback=lambda: AniGround.ground_objects(mode="individual")
        )
        ground_btn.set_context_menu([
            ("Ground Individually", lambda: AniGround.ground_objects(mode="individual")),
            ("Ground to Last Selected (Keep Offsets)", lambda: AniGround.ground_objects(mode="keep_offset"))
        ])
        self.toolbar_layout.addWidget(ground_btn)

        # Pose tools (copy/paste/mirror)
        self.toolbar_layout.addWidget(ToolButton(
            "copy_pose", "Copy Pose to clipboard",
            callback=AniMirror.copy_pose
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "paste_pose", "Paste Pose from clipboard",
            callback=AniMirror.paste_pose
        ))
        
        mirror_btn = ToolButton(
            "mirror_pose", "Mirror Pose (negate TX/TZ/RY)\n(Right-click for options)",
            callback=AniMirror.mirror_pose
        )
        mirror_btn.set_context_menu([
            ("Mirror Pose (negate TX/TZ/RY)", AniMirror.mirror_pose),
            ("Flip Pose (L<->R Swap)", AniMirror.flip_pose)
        ])
        self.toolbar_layout.addWidget(mirror_btn)

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
                callback=lambda t=ttype: AniTangents.set_tangent(t)
            ))

    def _add_timing_section(self):
        # Play/Pause Animation
        self.toolbar_layout.addWidget(ToolButton(
            "play_pause", "Play / Pause Animation",
            callback=lambda: cmds.play(state=not cmds.play(query=True, state=True))
        ))
        
        # Key navigation: prev/next key, first/last key
        self.toolbar_layout.addWidget(ToolButton(
            "first_key", "Jump to first keyframe",
            callback=AniKeyNav.goto_first_key
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "prev_key", "Jump to previous keyframe",
            callback=AniKeyNav.goto_prev_key
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "next_key", "Jump to next keyframe",
            callback=AniKeyNav.goto_next_key
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "last_key", "Jump to last keyframe",
            callback=AniKeyNav.goto_last_key
        ))
        # Nudge keys
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_left", "Nudge keys 1 frame earlier",
            callback=lambda: AniNudge.execute(-1)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_right", "Nudge keys 1 frame later",
            callback=lambda: AniNudge.execute(1)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_left_fast", "Nudge keys 5 frames earlier",
            callback=lambda: AniNudge.execute(-5)
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_right_fast", "Nudge keys 5 frames later",
            callback=lambda: AniNudge.execute(5)
        ))
        # Anim offset
        self.toolbar_layout.addWidget(ToolButton(
            "offset", "Stagger keys across selection (+2 frames each)",
            callback=lambda: AniOffset.execute(offset_frames=2)
        ))

        # Duplicate & Slide
        duplicate_btn = ToolButton(
            "duplicate", "AniDuplicate: Duplicate & Slide Keys\n(Right-click for options)",
            callback=lambda: self._on_duplicate(mode="overwrite")
        )
        duplicate_btn.set_context_menu([
            ("Duplicate (Overwrite Mode)", lambda: self._on_duplicate(mode="overwrite")),
            ("Duplicate (Merge Mode)", lambda: self._on_duplicate(mode="merge"))
        ])
        self.toolbar_layout.addWidget(duplicate_btn)

    def _add_tween_section(self):
        self.tween_slider = TweenSlider(label="TW", tooltip="Tween Slider (Linear Interpolation)")
        self.tween_slider.value_changed.connect(lambda b: self._on_tween(b, "linear"))
        self.toolbar_layout.addWidget(self.tween_slider)

        self.ease_slider = TweenSlider(label="EA", tooltip="Ease Slider (Ease-In / Ease-Out Interpolation)")
        self.ease_slider.value_changed.connect(lambda b: self._on_tween(b, "ease_in_out"))
        self.toolbar_layout.addWidget(self.ease_slider)

        smart_key_btn = ToolButton(
            "wand", "Smart Key — set keys only on already-animated channels",
            callback=lambda: AniTween.smart_key("all")
        )
        smart_key_btn.set_context_menu([
            ("Smart Key All", lambda: AniTween.smart_key("all")),
            ("Smart Key Translate", lambda: AniTween.smart_key("translate")),
            ("Smart Key Rotate", lambda: AniTween.smart_key("rotate")),
            ("Smart Key Scale", lambda: AniTween.smart_key("scale")),
        ])
        self.toolbar_layout.addWidget(smart_key_btn)

    def _add_workflow_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "bake_to_locator", "Smart Bake: Bake world-space motion → locator",
            callback=AniBake.bake_to_locator
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "bake_from_locator", "Smart Bake: Paste locator motion → object",
            callback=AniBake.bake_from_locator
        ))
        wave_btn = ToolButton(
            "wave_sine", "AniWave: Propagate Overlap / Follow-Through\n(Right-click for options)",
            callback=lambda: AniWave.propagate_wave(),
            accent=True
        )
        wave_btn.set_context_menu([
            ("Configure AniWave...", wave_panel.show_panel)
        ])
        self.toolbar_layout.addWidget(wave_btn)

    def _add_channels_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "lock", "Lock channels",
            callback=AniChannels.lock_channels
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "unlock", "Unlock channels",
            callback=AniChannels.unlock_channels
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "key", "Set keyframe on channels",
            callback=AniChannels.key_channels,
            accent=True
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "delkey", "Delete keyframe at current time",
            callback=AniChannels.delete_keys
        ))

    def _add_curves_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "euler", "Euler Filter â€” fix rotation flips",
            callback=AniSmooth.euler_filter
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "smooth", "Smooth animation curves",
            callback=lambda: AniSmooth.smooth_curves(strength=0.5, iterations=1)
        ))
        noise_btn = ToolButton(
            "activity", "AniNoise: Add Organic Micro-Jitter\n(Right-click for options)",
            callback=lambda: AniNoise.apply_noise(),
            accent=True
        )
        noise_btn.set_context_menu([
            ("Configure AniNoise...", noise_panel.show_panel)
        ])
        self.toolbar_layout.addWidget(noise_btn)

        # Cleanup curve
        cleanup_btn = ToolButton(
            "cleanup", "AniCleanup: Reduce redundant keyframes\n(Right-click for options)",
            callback=lambda: self._on_cleanup(tolerance=0.01)
        )
        cleanup_btn.set_context_menu([
            ("Clean Redundant (Tolerance: 0.01)", lambda: self._on_cleanup(tolerance=0.01)),
            ("Clean Redundant (Tolerance: 0.05)", lambda: self._on_cleanup(tolerance=0.05)),
            ("Clean Redundant (Tolerance: 0.1)", lambda: self._on_cleanup(tolerance=0.1)),
        ])
        self.toolbar_layout.addWidget(cleanup_btn)

    def _add_vis_section(self):
        trail_btn = ToolButton(
            "trail", "Toggle Motion Trail\n(Right-click for options)",
            callback=AniMotion.toggle_motion_trail
        )
        trail_btn.set_context_menu([
            ("Clear All Motion Trails", AniMotion.clear_all),
            (None, None),
            ("Configure Motion Trail...", lambda: settings_panel.show_panel(active_tab=1, on_apply_callback=self.rebuild_toolbar))
        ])
        self.toolbar_layout.addWidget(trail_btn)

        ghost_btn = ToolButton(
            "ghost", "Toggle Ghosting\n(Right-click for options)",
            callback=AniGhost.toggle_ghosting
        )
        ghost_btn.set_context_menu([
            ("Clear All Ghosting", AniGhost.clear_all),
            (None, None),
            ("Configure AniGhost...", lambda: settings_panel.show_panel(active_tab=2, on_apply_callback=self.rebuild_toolbar))
        ])
        self.toolbar_layout.addWidget(ghost_btn)

    def _add_sets_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "selection_sets", "Selection Sets panel",
            callback=selection_sets_panel.show_panel,
            accent=True
        ))

    def _add_bookmarks_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "bookmark", "Time Bookmarks panel",
            callback=bookmarks_panel.show_panel,
            accent=True
        ))

    def _add_poses_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "camera", "AniSnap: Visual Pose Library",
            callback=snap_panel.show_panel,
            accent=True
        ))

    def _add_diagnostics_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "stethoscope", "AniCheck: Curve Health Diagnostics",
            callback=check_panel.show_panel,
            accent=True
        ))

    def _add_pipeline_section(self):
        self.toolbar_layout.addWidget(ToolButton(
            "file_export", "AniExport: Export FBX with Unreal Validation",
            callback=self._on_export
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
        settings_btn.set_context_menu([
            ("Refresh Plugin (Reload)", lambda: __import__("anikin").reload_and_launch()),
            ("Uninstall AniKin", self._uninstall_plugin)
        ])
        self.toolbar_layout.addWidget(settings_btn)

    def _uninstall_plugin(self):
        import os
        result = cmds.confirmDialog(
            title="Uninstall AniKin",
            message="Are you sure you want to permanently uninstall AniKin?\nThis will remove it from Maya's startup files.",
            button=["Yes", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Cancel",
            dismissString="Cancel"
        )
        if result == "Yes":
            # 1. Close UI
            cmds.evalDeferred("import maya.cmds as cmds; cmds.deleteUI('{}', control=True) if cmds.workspaceControl('{}', exists=True) else None".format(self.WINDOW_NAME, self.WINDOW_NAME))
            
            # 2. Locate and delete anikin.mod
            maya_app_dir = os.path.normpath(cmds.internalVar(userAppDir=True))
            mod_file = os.path.join(maya_app_dir, "modules", "anikin.mod")
            if os.path.exists(mod_file):
                try:
                    os.remove(mod_file)
                except Exception:
                    pass
            
            # 3. Clean userSetup.py
            user_setup_path = os.path.join(maya_app_dir, "scripts", "userSetup.py")
            if os.path.exists(user_setup_path):
                try:
                    with open(user_setup_path, "r") as f:
                        lines = f.readlines()
                    
                    new_lines = []
                    in_block = False
                    for line in lines:
                        if "# —— AniKin Startup Launch ——" in line:
                            in_block = True
                            continue
                        if "# ———————————————————————————" in line and in_block:
                            in_block = False
                            continue
                        if not in_block:
                            new_lines.append(line)
                            
                    with open(user_setup_path, "w") as f:
                        f.writelines(new_lines)
                except Exception:
                    pass

            cmds.inViewMessage(amg="AniKin uninstalled successfully.", pos="topCenter", fade=True, fadeStayTime=3000)



    # ── Tween callback ──────────────────────────────────────────

    def _on_tween(self, bias, easing="linear"):
        """Called as the tween slider is dragged."""
        AniTween.apply_tween(bias, easing=easing)

    def _on_duplicate(self, mode="overwrite"):
        import maya.mel as mel
        gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
        if cmds.timeControl(gPlayBackSlider, query=True, rangeVisible=True):
            time_range = cmds.timeControl(gPlayBackSlider, query=True, rangeArray=True)
            start_frame = int(time_range[0])
            end_frame = int(time_range[1])
        else:
            start_frame = int(cmds.currentTime(query=True))
            end_frame = start_frame
            
        res = cmds.promptDialog(
            title="Duplicate & Slide",
            message="Enter target start frame:",
            button=["OK", "Cancel"],
            defaultButton="OK",
            cancelButton="Cancel",
            dismissString="Cancel",
            text=str(end_frame + 1)
        )
        if res == "OK":
            target_frame_str = cmds.promptDialog(query=True, text=True)
            try:
                target_frame = int(target_frame_str)
                from anikin import AniDuplicate
                AniDuplicate.duplicate_and_slide(start_frame, end_frame, target_frame, mode=mode)
            except ValueError:
                cmds.warning("AniDuplicate: Invalid frame number.")

    def _on_cleanup(self, tolerance=0.01):
        from anikin import AniCleanup
        AniCleanup.cleanup_curves(tolerance=tolerance)

    def _on_export(self):
        import os
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export FBX", os.path.expanduser("~"), "FBX Files (*.fbx)"
        )
        if path:
            from anikin import AniExport
            AniExport.export_fbx(path)


# ──────────────────────────────────────────────────────────────────────────────────
# Launch / cleanup
# ──────────────────────────────────────────────────────────────────────────────────

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
        height=52,
        width=900,
        label=AniKinWindow.WINDOW_TITLE,
    )

    # Load and register user hotkeys
    try:
        from anikin import AniHotkeys
        AniHotkeys.load_hotkeys()
    except Exception as e:
        cmds.warning("AniKin: Error loading hotkeys: {}".format(e))

    print("[AniKin] Toolbar launched. v{}".format(
        __import__("anikin").__version__
    ))
