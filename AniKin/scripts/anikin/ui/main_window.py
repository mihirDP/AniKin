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
- v0.5.0: Redesigned 10-group toolbar layout with new icon pack,
  amber accent color system, and merged Lock/Unlock toggle.
"""

import maya.cmds as cmds

from anikin.core.qt_compat import (
    QtWidgets, QtCore, MayaQWidgetDockableMixin
)
from anikin.ui.theme import STYLESHEET
from anikin.ui.widgets import (
    SectionSeparator, ToolButton, ToggleToolButton, TweenSlider, FlowLayout
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
from anikin import AniCamLock
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
from anikin.ui import anicolor_panel
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
        
        # Sync Play/Pause toggle with Maya's playback state
        self._playback_job = cmds.scriptJob(
            conditionChange=["playingBack", self._sync_playback_state],
            parent=self.WINDOW_NAME,
            replacePrevious=True
        )

    def _sync_playback_state(self):
        if hasattr(self, '_play_btn') and self._play_btn:
            is_playing = cmds.play(query=True, state=True)
            if self._play_btn.is_toggled() != is_playing:
                self._play_btn.set_toggled(is_playing)

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

        # Horizontal layout: standard toolbar behavior, doesn't wrap unexpectedly
        self.toolbar_layout = QtWidgets.QHBoxLayout(self.toolbar_frame)
        self.toolbar_layout.setContentsMargins(4, 4, 4, 4)
        self.toolbar_layout.setSpacing(3)
        # Removing AlignLeft allows the expanding buttons to stretch and fill the space

        # Allow horizontal scrolling if tools exceed window width
        self._scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

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
        order = cfg.get("section_order", [])
        visible = cfg.get("visible_sections", [])
        
        # Update stylesheet in case theme changed
        theme_name = cfg.get("theme", "Amber")
        from anikin.ui.theme import get_stylesheet
        self.setStyleSheet(get_stylesheet(theme_name))

        first = True
        for sec in order:
            if sec not in visible:
                continue
            if not first:
                self.toolbar_layout.addWidget(SectionSeparator())
            first = False

            if sec == "Brand":
                self._add_brand_section()
            elif sec == "Selection":
                self._add_selection_section()
            elif sec == "Pose":
                self._add_pose_section()
            elif sec == "Tween Slider":
                self._add_tween_section()
            elif sec == "Tangents":
                self._add_tangents_section()
            elif sec == "Playback":
                self._add_playback_section()
            elif sec == "Channels":
                self._add_channels_section()
            elif sec == "Modules":
                self._add_modules_section()
            elif sec == "Curves":
                self._add_curves_section()
            elif sec == "Setup":
                self._add_setup_section()

    # ── Section Builder Helpers ─────────────────────────────────────────────────

    def _add_brand_section(self):
        """Group 0 — Brand Identity: AniKin logo label."""
        logo = QtWidgets.QLabel("AniKin")
        logo.setObjectName("AniKinLogo")
        logo.setFixedWidth(54)
        logo.setFixedHeight(28)
        logo.setAlignment(QtCore.Qt.AlignCenter)
        logo.setCursor(QtCore.Qt.PointingHandCursor)
        logo.mousePressEvent = lambda e: settings_panel.show_panel(
            active_tab=4, on_apply_callback=self.rebuild_toolbar
        )
        self.toolbar_layout.addWidget(logo)

    def _add_selection_section(self):
        """Group 1 — Selection Tools."""
        self.toolbar_layout.addWidget(ToolButton(
            "selection_sets", "Selection Sets — save and recall control selections",
            callback=selection_sets_panel.show_panel,
            accent=True
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "bookmark", "Time Bookmarks — manage timeline bookmarks",
            callback=bookmarks_panel.show_panel,
            accent=True
        ))

    def _add_pose_section(self):
        """Group 2 — Pose Tools."""
        self.toolbar_layout.addWidget(ToolButton(
            "reset", "Reset — return selected controls to default position",
            callback=AniMirror.reset_transform
        ))

        mirror_btn = ToolButton(
            "mirror_pose", "Mirror Pose — flip pose to opposite side\n(Right-click for options)",
            callback=AniMirror.mirror_pose
        )
        mirror_btn.set_context_menu([
            ("Mirror Pose (negate TX/TZ/RY)", AniMirror.mirror_pose),
            ("Flip Pose (L<->R Swap)", AniMirror.flip_pose)
        ])
        self.toolbar_layout.addWidget(mirror_btn)

        self.toolbar_layout.addWidget(ToolButton(
            "copy_pose", "Copy Pose to clipboard",
            callback=AniMirror.copy_pose
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "paste_pose", "Paste Pose from clipboard",
            callback=AniMirror.paste_pose
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "camera", "AniSnap — save and recall pose snapshots",
            callback=snap_panel.show_panel,
            accent=True
        ))

    def _add_tween_section(self):
        """Group 3 — Tween / Ease Sliders."""
        self.tween_slider = TweenSlider(label="TW", tooltip="Tween Slider (Linear Interpolation)")
        self.tween_slider.value_changed.connect(lambda b: self._on_tween(b, "linear"))
        self.toolbar_layout.addWidget(self.tween_slider)

        self.ease_slider = TweenSlider(label="EA", tooltip="Ease Slider (Ease-In / Ease-Out Interpolation)")
        self.ease_slider.value_changed.connect(lambda b: self._on_tween(b, "ease_in_out"))
        self.toolbar_layout.addWidget(self.ease_slider)

        smart_key_btn = ToolButton(
            "smart_key", "Smart Key — set keys only on already-animated channels",
            callback=lambda: AniTween.smart_key("all")
        )
        smart_key_btn.set_context_menu([
            ("Smart Key All", lambda: AniTween.smart_key("all")),
            ("Smart Key Translate", lambda: AniTween.smart_key("translate")),
            ("Smart Key Rotate", lambda: AniTween.smart_key("rotate")),
            ("Smart Key Scale", lambda: AniTween.smart_key("scale")),
        ])
        self.toolbar_layout.addWidget(smart_key_btn)

    def _add_tangents_section(self):
        """Group 4 — Tangent Quick-Set."""
        for ttype, icon, tip in [
            ("spline", "spline", "Spline tangents"),
            ("linear", "linear", "Linear tangents"),
            ("flat",   "flat",   "Flat tangents (hold)"),
            ("step",   "step",   "Stepped tangents (pose-to-pose)"),
            ("auto",   "auto",   "Auto tangents"),
        ]:
            self.toolbar_layout.addWidget(ToolButton(
                icon, tip,
                callback=lambda t=ttype: AniTangents.set_tangent(t),
                size=24
            ))

    def _add_playback_section(self):
        """Group 5 — Playback + Key Operations (the critical redesign group)."""
        # Step Back
        self.toolbar_layout.addWidget(ToolButton(
            "first_key", "Step Back — jump to first keyframe",
            callback=AniKeyNav.goto_first_key, size=24
        ))
        # Prev Key
        self.toolbar_layout.addWidget(ToolButton(
            "prev_key", "Previous Key — jump to previous keyframe",
            callback=AniKeyNav.goto_prev_key, size=24
        ))
        # SET KEY — accent style (primary action)
        self.toolbar_layout.addWidget(ToolButton(
            "key", "Set Keyframe — places a keyframe on selected controls\nHotkey: S",
            callback=AniChannels.key_channels,
            accent=True
        ))
        # Play / Pause toggle
        self._play_btn = ToggleToolButton(
            icon_a="play",
            icon_b="pause",
            tooltip_a="Play Animation\nHotkey: Alt+V",
            tooltip_b="Pause Animation",
            callback=self._on_play_pause_toggle,
            accent_a=False,
            accent_b=True,
        )
        self.toolbar_layout.addWidget(self._play_btn)
        # Next Key
        self.toolbar_layout.addWidget(ToolButton(
            "next_key", "Next Key — jump to next keyframe",
            callback=AniKeyNav.goto_next_key, size=24
        ))
        # Last Key / Step Forward
        self.toolbar_layout.addWidget(ToolButton(
            "last_key", "Step Forward — jump to last keyframe",
            callback=AniKeyNav.goto_last_key, size=24
        ))
        # DELETE KEY — danger style
        self.toolbar_layout.addWidget(ToolButton(
            "delkey", "Delete Keyframe — remove keyframe at current time",
            callback=AniChannels.delete_keys,
            danger=True
        ))

    def _add_channels_section(self):
        """Group 6 — Channel Utilities (merged Lock/Unlock toggle)."""
        self._lock_btn = ToggleToolButton(
            icon_a="unlock",
            icon_b="lock",
            tooltip_a="Lock Channels — click to lock selected channels",
            tooltip_b="Unlock Channels — click to unlock selected channels",
            callback=self._on_lock_toggle,
            accent_a=False,
            accent_b=True,
        )
        self.toolbar_layout.addWidget(self._lock_btn)

    def _add_modules_section(self):
        """Group 7 — AniModules Quick Access (launcher buttons for sub-panels)."""
        self.toolbar_layout.addWidget(ToolButton(
            "offset", "AniOffset — stagger keys across selection (+2 frames each)\n(Right-click for options)",
            callback=lambda: AniOffset.execute(offset_frames=2)
        ))

        # Nudge keys
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_left", "Nudge keys 1 frame earlier",
            callback=lambda: AniNudge.execute(-1), size=24
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "nudge_right", "Nudge keys 1 frame later",
            callback=lambda: AniNudge.execute(1), size=24
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

        # Smart Bake
        self.toolbar_layout.addWidget(ToolButton(
            "bake_to_locator", "Smart Bake: Bake world-space motion → locator",
            callback=AniBake.bake_to_locator
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "bake_from_locator", "Smart Bake: Paste locator motion → object",
            callback=AniBake.bake_from_locator
        ))

        # AniWave
        wave_btn = ToolButton(
            "wave_sine", "AniWave: Propagate Overlap / Follow-Through\n(Right-click for options)",
            callback=lambda: AniWave.propagate_wave(),
            accent=True
        )
        wave_btn.set_context_menu([
            ("Configure AniWave...", wave_panel.show_panel)
        ])
        self.toolbar_layout.addWidget(wave_btn)

        # AniNoise
        noise_btn = ToolButton(
            "activity", "AniNoise: Add Organic Micro-Jitter\n(Right-click for options)",
            callback=lambda: AniNoise.apply_noise(),
            accent=True
        )
        noise_btn.set_context_menu([
            ("Configure AniNoise...", noise_panel.show_panel)
        ])
        self.toolbar_layout.addWidget(noise_btn)

        # AniCheck
        self.toolbar_layout.addWidget(ToolButton(
            "stethoscope", "AniCheck: Curve Health Diagnostics",
            callback=check_panel.show_panel,
            accent=True
        ))

        # AniColor
        self.toolbar_layout.addWidget(ToolButton(
            "palette", "AniColor: Keyframe Coloring & Labeling",
            callback=anicolor_panel.show_panel,
            accent=True
        ))

        # AniCamLock
        self._cam_lock_mode = QtWidgets.QComboBox()
        self._cam_lock_mode.addItems(["Track", "Aim"])
        self._cam_lock_mode.setToolTip("Cam-Lock Mode: Track (offset) or Aim (focus)")
        self._cam_lock_mode.setFixedWidth(60)
        self._cam_lock_mode.setFixedHeight(28)
        self.toolbar_layout.addWidget(self._cam_lock_mode)

        self._cam_lock_btn = ToggleToolButton(
            icon_a="cam_unlock",
            icon_b="cam_lock",
            tooltip_a="Cam-Lock: Click to lock viewport camera on selected object",
            tooltip_b="Cam-Lock: Click to unlock and restore camera",
            callback=self._on_cam_lock_toggle,
            accent_a=False,
            accent_b=True,
        )
        self.toolbar_layout.addWidget(self._cam_lock_btn)

    def _add_curves_section(self):
        """Group 8 — Curve editing tools."""
        self.toolbar_layout.addWidget(ToolButton(
            "euler", "Euler Filter — fix rotation flips",
            callback=AniSmooth.euler_filter
        ))
        self.toolbar_layout.addWidget(ToolButton(
            "smooth", "Smooth animation curves",
            callback=lambda: AniSmooth.smooth_curves(strength=0.5, iterations=1)
        ))

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

        # Motion Trail
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

        # Ghosting
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

        # Grounding tool
        ground_btn = ToolButton(
            "ground", "AniGround: Ground selected objects\n(Right-click for options)",
            callback=lambda: AniGround.ground_objects(mode="individual")
        )
        ground_btn.set_context_menu([
            ("Ground Individually", lambda: AniGround.ground_objects(mode="individual")),
            ("Ground to Last Selected (Keep Offsets)", lambda: AniGround.ground_objects(mode="keep_offset"))
        ])
        self.toolbar_layout.addWidget(ground_btn)

    def _add_setup_section(self):
        """Group 9 — Settings / Help."""
        self.toolbar_layout.addWidget(ToolButton(
            "hotkeys", "Hotkey Manager",
            callback=hotkey_panel.show_panel
        ))

        self.toolbar_layout.addWidget(ToolButton(
            "file_export", "AniExport: Export FBX with Unreal Validation",
            callback=self._on_export
        ))

        settings_btn = ToolButton(
            "settings", "Settings & Preferences\n(Layout, Trails, Ghosting)",
            callback=lambda: settings_panel.show_panel(active_tab=0, on_apply_callback=self.rebuild_toolbar)
        )
        settings_btn.set_context_menu([
            ("Refresh Plugin (Reload)", lambda: _refresh_plugin()),
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



    # ── Play / Pause callback ───────────────────────────────────────

    def _on_play_pause_toggle(self, is_now_playing):
        """Toggle Maya playback. ``is_now_playing`` is the *new* toggled state."""
        if is_now_playing:
            cmds.play(forward=True)
        else:
            cmds.play(state=False)

    # ── Cam-Lock callback ────────────────────────────────────────

    def _on_cam_lock_toggle(self, is_now_locked):
        """Toggle viewport cam-lock on the selected object."""
        if is_now_locked:
            mode = self._cam_lock_mode.currentText().lower()
            success = AniCamLock.lock(mode=mode)
            if not success:
                # Lock failed (nothing selected, etc.) — revert the button
                self._cam_lock_btn.set_toggled(False)
        else:
            AniCamLock.unlock()

    # ── Lock/Unlock callback ─────────────────────────────────────

    def _on_lock_toggle(self, is_now_locked):
        """Merged Lock/Unlock channel toggle."""
        if is_now_locked:
            AniChannels.lock_channels()
        else:
            AniChannels.unlock_channels()

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


def _refresh_plugin():
    """
    Full purge-and-reimport of AniKin.
    Works even when the previous load failed (stale/partial module cache).
    """
    import sys
    mods_to_remove = [k for k in sys.modules if k.startswith("anikin")]
    for k in mods_to_remove:
        del sys.modules[k]
    import anikin
    anikin.launch()


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
