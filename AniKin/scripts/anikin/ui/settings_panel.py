"""
settings_panel.py
Configuration panel for AniKin layout, visualization, and general preferences.
Provides:
- SettingsPanel dialog containing Layout settings, Motion Trail settings, Ghosting settings,
  and General & Pose Library path preferences.
"""

import os
import maya.cmds as cmds
from anikin.core.qt_compat import QtWidgets, QtCore, get_maya_main_window
from anikin.ui.theme import STYLESHEET
from anikin import AniGhost, AniMotion
from anikin.core import settings


class SettingsPanel(QtWidgets.QDialog):
    """AniKin Settings Panel."""

    def __init__(self, parent=None, active_tab=0, on_apply_callback=None):
        super(SettingsPanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin — Settings & Preferences")
        self.setObjectName("AniKinSettingsPanel")
        self.setMinimumSize(420, 360)
        self.setStyleSheet(STYLESHEET)
        
        self.on_apply_callback = on_apply_callback
        
        self._build_ui(active_tab)
        self._load_settings()

    def _build_ui(self, active_tab):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Tab widget
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        # —— Tab 1: Layout —————————————————————————————————
        self.layout_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.layout_tab, "Toolbar Layout")
        self._build_layout_ui()

        # —— Tab 2: General & Poses ——————————————————————————
        self.general_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.general_tab, "General & Poses")
        self._build_general_ui()

        # —— Tab 3: Motion Trail ———————————————————————————
        self.trail_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.trail_tab, "Motion Trail")
        self._build_trail_ui()

        # —— Tab 4: Ghosting ———————————————————————————————
        self.ghost_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.ghost_tab, "Ghosting")
        self._build_ghost_ui()

        # —— Tab 5: About —————————————————————————————————
        self.about_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.about_tab, "About")
        self._build_about_ui()

        # Set active tab
        self.tabs.setCurrentIndex(active_tab)

        # —— Action Buttons ————————————————————————————————
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        
        apply_btn = QtWidgets.QPushButton("Apply")
        apply_btn.setProperty("accent", True)
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

    def _build_layout_ui(self):
        layout = QtWidgets.QHBoxLayout(self.layout_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Left: List of sections
        list_container = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("<b>Section Visibility & Order:</b>")
        list_container.addWidget(label)

        self.sections_list = QtWidgets.QListWidget()
        self.sections_list.setStyleSheet("QListWidget { background-color: #1e1e1e; border: 1px solid #1a1a1a; }")
        list_container.addWidget(self.sections_list)
        layout.addLayout(list_container)

        # Right: Move buttons
        btn_container = QtWidgets.QVBoxLayout()
        btn_container.addStretch()
        
        up_btn = QtWidgets.QPushButton("▲")
        up_btn.setToolTip("Move Section Up")
        up_btn.setFixedWidth(30)
        up_btn.clicked.connect(self._move_up)
        btn_container.addWidget(up_btn)

        down_btn = QtWidgets.QPushButton("▼")
        down_btn.setToolTip("Move Section Down")
        down_btn.setFixedWidth(30)
        down_btn.clicked.connect(self._move_down)
        btn_container.addWidget(down_btn)
        
        btn_container.addStretch()
        layout.addLayout(btn_container)

    def _build_general_ui(self):
        layout = QtWidgets.QVBoxLayout(self.general_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Debug Mode
        self.debug_chk = QtWidgets.QCheckBox("Enable Debug Mode (Log output to AniKin.log)")
        self.debug_chk.setToolTip("Saves verbose execution logs to system temp directory.")
        layout.addWidget(self.debug_chk)

        # Pose Library Roots
        lbl = QtWidgets.QLabel("<b>Pose Library Paths:</b>")
        layout.addWidget(lbl)

        h_layout = QtWidgets.QHBoxLayout()
        self.lib_paths_list = QtWidgets.QListWidget()
        self.lib_paths_list.setStyleSheet("QListWidget { background-color: #1e1e1e; border: 1px solid #1a1a1a; }")
        h_layout.addWidget(self.lib_paths_list)

        v_buttons = QtWidgets.QVBoxLayout()
        v_buttons.addStretch()
        
        add_btn = QtWidgets.QPushButton("Add...")
        add_btn.setToolTip("Add new library root folder")
        add_btn.clicked.connect(self._add_library_path)
        v_buttons.addWidget(add_btn)

        remove_btn = QtWidgets.QPushButton("Del")
        remove_btn.setToolTip("Remove selected library path")
        remove_btn.clicked.connect(self._remove_library_path)
        v_buttons.addWidget(remove_btn)
        
        v_buttons.addStretch()
        h_layout.addLayout(v_buttons)

        layout.addLayout(h_layout)

    def _build_trail_ui(self):
        layout = QtWidgets.QFormLayout(self.trail_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.trail_thickness = QtWidgets.QDoubleSpinBox()
        self.trail_thickness.setRange(0.5, 10.0)
        self.trail_thickness.setSingleStep(0.5)
        self.trail_thickness.setValue(2.0)
        layout.addRow("Trail Thickness:", self.trail_thickness)

        self.show_frames = QtWidgets.QCheckBox("Display frame numbers next to keys")
        self.show_frames.setChecked(True)
        layout.addRow("", self.show_frames)

        self.color_preset = QtWidgets.QComboBox()
        self.color_preset.addItems(["Teal (Default)", "Orange", "Magenta", "Green", "White"])
        layout.addRow("Trail Color Preset:", self.color_preset)

    def _build_ghost_ui(self):
        layout = QtWidgets.QFormLayout(self.ghost_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.pre_frames = QtWidgets.QSpinBox()
        self.pre_frames.setRange(0, 100)
        self.pre_frames.setValue(5)
        layout.addRow("Pre Frames (Past):", self.pre_frames)

        self.post_frames = QtWidgets.QSpinBox()
        self.post_frames.setRange(0, 100)
        self.post_frames.setValue(5)
        layout.addRow("Post Frames (Future):", self.post_frames)

        self.ghost_step = QtWidgets.QSpinBox()
        self.ghost_step.setRange(1, 20)
        self.ghost_step.setValue(1)
        layout.addRow("Frame Step:", self.ghost_step)

    def _build_about_ui(self):
        layout = QtWidgets.QVBoxLayout(self.about_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("<b>AniKin Toolkit v0.3</b>")
        title.setStyleSheet("font-size: 14px;")
        layout.addWidget(title)
        
        desc = QtWidgets.QLabel("The intelligent animation analysis and productivity toolkit for Maya.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        credits = QtWidgets.QLabel(
            "<b>Open Source Credits & Attribution:</b><br><br>"
            "AniKin is licensed under the GPLv3.<br><br>"
            "<b>Key Machine:</b><br>"
            "The AniTween module (and concepts in AniOffset & AniSets) were inspired by and "
            "adapted from the <i>Key Machine</i> toolset, which is also licensed "
            "under the GPLv3. We extend our deep gratitude to the Key Machine project for establishing "
            "these excellent open-source animation workflows."
        )
        credits.setWordWrap(True)
        credits.setStyleSheet("color: #b0b0b0;")
        layout.addWidget(credits)
        layout.addStretch()

    def _move_up(self):
        row = self.sections_list.currentRow()
        if row > 0:
            item = self.sections_list.takeItem(row)
            self.sections_list.insertItem(row - 1, item)
            self.sections_list.setCurrentRow(row - 1)

    def _move_down(self):
        row = self.sections_list.currentRow()
        if row < self.sections_list.count() - 1:
            item = self.sections_list.takeItem(row)
            self.sections_list.insertItem(row + 1, item)
            self.sections_list.setCurrentRow(row + 1)

    def _add_library_path(self):
        """Browse and add new pose library root."""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Pose Library Root Folder", os.path.expanduser("~")
        )
        if dir_path:
            norm = os.path.abspath(dir_path)
            # Check for duplicates
            items = [self.lib_paths_list.item(i).text() for i in range(self.lib_paths_list.count())]
            if norm not in items:
                self.lib_paths_list.addItem(norm)

    def _remove_library_path(self):
        row = self.lib_paths_list.currentRow()
        if row >= 0:
            self.lib_paths_list.takeItem(row)

    def _load_settings(self):
        """Populate controls from stored configuration."""
        cfg = settings.load_settings()
        
        # 1. Populate layout list
        self.sections_list.clear()
        for sec in cfg["section_order"]:
            item = QtWidgets.QListWidgetItem(sec)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            check_state = QtCore.Qt.Checked if sec in cfg["visible_sections"] else QtCore.Qt.Unchecked
            item.setCheckState(check_state)
            self.sections_list.addItem(item)

        # 2. General Preferences
        self.debug_chk.setChecked(cfg.get("debug_mode", False))
        
        self.lib_paths_list.clear()
        for path in cfg.get("pose_library_roots", []):
            self.lib_paths_list.addItem(path)

        # 3. Query Ghosting settings
        try:
            self.pre_frames.setValue(cmds.ghosting(query=True, preFrames=True) or 5)
            self.post_frames.setValue(cmds.ghosting(query=True, postFrames=True) or 5)
            self.ghost_step.setValue(cmds.ghosting(query=True, ghostsStep=True) or 1)
        except Exception:
            pass

    def _apply_settings(self):
        """Save settings and trigger UI refresh."""
        # 1. Read layout values
        order = []
        visible = []
        for i in range(self.sections_list.count()):
            item = self.sections_list.item(i)
            name = item.text()
            order.append(name)
            if item.checkState() == QtCore.Qt.Checked:
                visible.append(name)

        # 2. Read general values
        debug_mode = self.debug_chk.isChecked()
        lib_roots = [self.lib_paths_list.item(i).text() for i in range(self.lib_paths_list.count())]

        # 3. Save settings
        cfg = {
            "section_order": order,
            "visible_sections": visible,
            "pose_library_roots": lib_roots,
            "debug_mode": debug_mode
        }
        settings.save_settings(cfg)

        # 4. Apply Ghosting Settings
        AniGhost.configure_ghosting(
            pre_frames=self.pre_frames.value(),
            post_frames=self.post_frames.value(),
            step=self.ghost_step.value()
        )

        # 5. Map Trail Color Preset to RGB
        presets = {
            0: (0.0, 0.7, 0.85),  # Teal
            1: (1.0, 0.5, 0.0),   # Orange
            2: (0.9, 0.1, 0.5),   # Magenta
            3: (0.2, 0.8, 0.2),   # Green
            4: (0.9, 0.9, 0.9)    # White
        }
        rgb = presets.get(self.color_preset.currentIndex(), (0.0, 0.7, 0.85))

        # 6. Update any active trail nodes
        sel = cmds.ls(selection=True) or []
        for obj in sel:
            trail, handle = AniMotion.get_motion_trail_for_object(obj)
            if handle:
                shapes = cmds.listRelatives(handle, shapes=True) or []
                if shapes:
                    shape = shapes[0]
                    try:
                        cmds.setAttr("{}.trailColor".format(shape), rgb[0], rgb[1], rgb[2], type="double3")
                        cmds.setAttr("{}.trailThickness".format(shape), self.trail_thickness.value())
                        cmds.setAttr("{}.showFrames".format(shape), self.show_frames.isChecked())
                    except Exception:
                        pass

        # 7. Trigger Main UI rebuild
        if self.on_apply_callback:
            self.on_apply_callback()
            
        cmds.inViewMessage(
            amg="<hl>AniKin</hl>: Settings applied successfully",
            pos="topCenter", fade=True, fadeStayTime=1500
        )


# —— Global instance —————————————————————————————————————
_PANEL_INSTANCE = None


def show_panel(active_tab=0, on_apply_callback=None):
    """Show the Settings panel."""
    global _PANEL_INSTANCE
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.close()
        except Exception:
            pass
    _PANEL_INSTANCE = SettingsPanel(active_tab=active_tab, on_apply_callback=on_apply_callback)
    _PANEL_INSTANCE.show()
