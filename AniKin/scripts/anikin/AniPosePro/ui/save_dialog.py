"""
save_dialog.py — Unified Save Dialog for Poses, Clips, Scripts, and SelectionSets for AniPose Pro V3.1.
"""

import os
import maya.cmds as cmds
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui
from anikin.AniPosePro.core.thumbnail import capture_thumbnail, capture_clip_thumbnail


class UnifiedSaveDialog(QtWidgets.QDialog):
    """
    Rich save dialog matching Section 3.1 & 4.2 of AniPose Pro PRD.
    Allows toggling between Pose, Animation Clip, Script, and Selection Set.
    """

    def __init__(self, item_type: str = "pose", target_folder: str = "", parent=None):
        super(UnifiedSaveDialog, self).__init__(parent)
        self.item_type = item_type  # "pose", "clip", "script", "selection"
        self.target_folder = target_folder
        self.temp_thumb_path = ""

        self.setWindowTitle("Save Item — AniPose Pro")
        self.resize(520, 640)

        self._build_ui()
        self._set_item_type(self.item_type)

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(10)

        # 0. Item Type Selector Header
        type_box = QtWidgets.QGroupBox("Item Type")
        t_lay = QtWidgets.QHBoxLayout(type_box)
        t_lay.setContentsMargins(6, 6, 6, 6)

        self.btn_type_pose = QtWidgets.QRadioButton("Pose")
        self.btn_type_clip = QtWidgets.QRadioButton("Animation Clip")
        self.btn_type_script = QtWidgets.QRadioButton("Script")
        self.btn_type_selection = QtWidgets.QRadioButton("Selection Set")

        for b in [self.btn_type_pose, self.btn_type_clip, self.btn_type_script, self.btn_type_selection]:
            t_lay.addWidget(b)

        self.btn_type_pose.toggled.connect(lambda chk: chk and self._on_type_changed("pose"))
        self.btn_type_clip.toggled.connect(lambda chk: chk and self._on_type_changed("clip"))
        self.btn_type_script.toggled.connect(lambda chk: chk and self._on_type_changed("script"))
        self.btn_type_selection.toggled.connect(lambda chk: chk and self._on_type_changed("selection"))

        lay.addWidget(type_box)

        # 1. Top Section: Thumbnail Preview + Name/Folder/Rating/Color
        top_h = QtWidgets.QHBoxLayout()

        # Thumbnail widget
        self.thumb_lbl = QtWidgets.QLabel()
        self.thumb_lbl.setFixedSize(130, 130)
        self.thumb_lbl.setStyleSheet("background: #161a1d; border: 1px dashed #2a3038; border-radius: 4px;")
        self.thumb_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.thumb_lbl.setToolTip("Click to re-capture viewport thumbnail")
        self.thumb_lbl.setCursor(QtCore.Qt.PointingHandCursor)
        self.thumb_lbl.mousePressEvent = lambda e: self._capture_preview_thumbnail()
        top_h.addWidget(self.thumb_lbl)

        # Form layout
        form = QtWidgets.QFormLayout()
        form.setSpacing(6)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("e.g. bounceball_v1")

        self.folder_lbl = QtWidgets.QLabel(self.target_folder or "Root")
        self.folder_lbl.setStyleSheet("color: #8b9299;")

        form.addRow("Name:", self.name_edit)
        form.addRow("Folder:", self.folder_lbl)

        # Star Rating Widget
        self.rating_spin = QtWidgets.QSpinBox()
        self.rating_spin.setRange(0, 5)
        self.rating_spin.setValue(4)
        form.addRow("Rating (0-5 ★):", self.rating_spin)

        # Color Swatch Picker
        self.color_btn = QtWidgets.QPushButton("#3a9e6e")
        self.color_btn.setStyleSheet("background: #3a9e6e; color: #fff; font-weight: bold;")
        self.color_btn.clicked.connect(self._pick_color)
        self.selected_color = "#3a9e6e"
        form.addRow("Color Tag:", self.color_btn)

        top_h.addLayout(form)
        lay.addLayout(top_h)

        # 2. Tags & Notes
        lay.addWidget(QtWidgets.QLabel("Tags (comma separated):"))
        self.tags_edit = QtWidgets.QLineEdit()
        self.tags_edit.setPlaceholderText("e.g. contact, jump, cycle")
        lay.addWidget(self.tags_edit)

        lay.addWidget(QtWidgets.QLabel("Notes:"))
        self.notes_edit = QtWidgets.QTextEdit()
        self.notes_edit.setMaximumHeight(50)
        lay.addWidget(self.notes_edit)

        # 3. Stacked Options based on item type
        self.options_stack = QtWidgets.QStackedWidget()

        # Page 0: Pose Options
        self.pose_opts_page = QtWidgets.QWidget()
        p_lay = QtWidgets.QVBoxLayout(self.pose_opts_page)
        p_grp = QtWidgets.QGroupBox("Attribute Filter")
        p_glay = QtWidgets.QHBoxLayout(p_grp)
        self.chk_trans = QtWidgets.QCheckBox("Translate")
        self.chk_rot = QtWidgets.QCheckBox("Rotate")
        self.chk_scale = QtWidgets.QCheckBox("Scale")
        self.chk_custom = QtWidgets.QCheckBox("Custom")
        for c in [self.chk_trans, self.chk_rot, self.chk_scale, self.chk_custom]:
            c.setChecked(True)
            p_glay.addWidget(c)
        p_lay.addWidget(p_grp)
        self.options_stack.addWidget(self.pose_opts_page)

        # Page 1: Clip Options (Frame Range!)
        self.clip_opts_page = QtWidgets.QWidget()
        c_lay = QtWidgets.QVBoxLayout(self.clip_opts_page)
        c_grp = QtWidgets.QGroupBox("Animation Clip Range & Options")
        c_glay = QtWidgets.QVBoxLayout(c_grp)

        fr_h = QtWidgets.QHBoxLayout()
        fr_h.addWidget(QtWidgets.QLabel("Start Frame:"))
        self.start_frame_spin = QtWidgets.QSpinBox()
        self.start_frame_spin.setRange(-99999, 99999)
        fr_h.addWidget(self.start_frame_spin)

        fr_h.addWidget(QtWidgets.QLabel("End Frame:"))
        self.end_frame_spin = QtWidgets.QSpinBox()
        self.end_frame_spin.setRange(-99999, 99999)
        fr_h.addWidget(self.end_frame_spin)

        btn_get_range = QtWidgets.QPushButton("Use Timeline Range")
        btn_get_range.clicked.connect(self._fetch_timeline_range)
        fr_h.addWidget(btn_get_range)

        c_glay.addLayout(fr_h)

        self.chk_bake = QtWidgets.QCheckBox("Bake before saving (flatten layers)")
        self.chk_anim_layers = QtWidgets.QCheckBox("Include Animation Layers")
        c_glay.addWidget(self.chk_bake)
        c_glay.addWidget(self.chk_anim_layers)

        c_lay.addWidget(c_grp)
        self.options_stack.addWidget(self.clip_opts_page)

        # Page 2: Script Options
        self.script_opts_page = QtWidgets.QWidget()
        s_lay = QtWidgets.QVBoxLayout(self.script_opts_page)
        s_lay.addWidget(QtWidgets.QLabel("Python Script Code:"))
        self.script_edit = QtWidgets.QTextEdit()
        self.script_edit.setPlaceholderText("import maya.cmds as cmds\n# Your code here...")
        s_lay.addWidget(self.script_edit)
        self.options_stack.addWidget(self.script_opts_page)

        # Page 3: Selection Options
        self.selection_opts_page = QtWidgets.QWidget()
        sel_lay = QtWidgets.QVBoxLayout(self.selection_opts_page)
        sel_lay.addWidget(QtWidgets.QLabel("Saves current control selection set."))
        self.options_stack.addWidget(self.selection_opts_page)

        lay.addWidget(self.options_stack)

        # Buttons
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self._on_accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

        # Set default frame range
        self._fetch_timeline_range()

    def _fetch_timeline_range(self):
        try:
            import maya.mel as mel
            gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
            if cmds.timeControl(gPlayBackSlider, query=True, rangeVisible=True):
                r = cmds.timeControl(gPlayBackSlider, query=True, rangeArray=True)
                s, e = int(r[0]), int(r[1])
            else:
                s = int(cmds.playbackOptions(q=True, min=True))
                e = int(cmds.playbackOptions(q=True, max=True))
        except Exception:
            s, e = 1, 24

        self.start_frame_spin.setValue(s)
        self.end_frame_spin.setValue(e)

    def _set_item_type(self, itype: str):
        self.item_type = itype
        if itype == "pose":
            self.btn_type_pose.setChecked(True)
            self.options_stack.setCurrentIndex(0)
        elif itype == "clip":
            self.btn_type_clip.setChecked(True)
            self.options_stack.setCurrentIndex(1)
        elif itype == "script":
            self.btn_type_script.setChecked(True)
            self.options_stack.setCurrentIndex(2)
        elif itype == "selection":
            self.btn_type_selection.setChecked(True)
            self.options_stack.setCurrentIndex(3)
        self.setWindowTitle(f"Save {itype.capitalize()} — AniPose Pro")
        self._capture_preview_thumbnail()

    def _on_type_changed(self, new_type: str):
        self.item_type = new_type
        if new_type == "pose":
            self.options_stack.setCurrentIndex(0)
        elif new_type == "clip":
            self.options_stack.setCurrentIndex(1)
        elif new_type == "script":
            self.options_stack.setCurrentIndex(2)
        elif new_type == "selection":
            self.options_stack.setCurrentIndex(3)
        self.setWindowTitle(f"Save {new_type.capitalize()} — AniPose Pro")
        self._capture_preview_thumbnail()

    def _pick_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.selected_color), self)
        if color.isValid():
            self.selected_color = color.name()
            self.color_btn.setText(self.selected_color)
            self.color_btn.setStyleSheet(f"background: {self.selected_color}; color: #fff; font-weight: bold;")

    def _capture_preview_thumbnail(self):
        tmp_dir = os.path.join(cmds.internalVar(userTmpDir=True), "anipose_tmp")
        os.makedirs(tmp_dir, exist_ok=True)

        if self.item_type == "clip":
            self.temp_thumb_path = os.path.join(tmp_dir, "preview.gif")
            s = self.start_frame_spin.value()
            e = self.end_frame_spin.value()
            capture_clip_thumbnail(s, e, self.temp_thumb_path, 130, 130)
        else:
            self.temp_thumb_path = os.path.join(tmp_dir, "preview.jpg")
            capture_thumbnail(self.temp_thumb_path, 130, 130)

        if os.path.exists(self.temp_thumb_path):
            pix = QtGui.QPixmap(self.temp_thumb_path)
            self.thumb_lbl.setPixmap(pix.scaled(130, 130, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def _on_accept(self):
        if not self.name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a name.")
            return
        self.accept()

    def get_data(self) -> dict:
        tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
        return {
            "item_type": self.item_type,
            "name": self.name_edit.text().strip(),
            "rating": self.rating_spin.value(),
            "color": self.selected_color,
            "tags": tags,
            "notes": self.notes_edit.toPlainText().strip(),
            "temp_thumb": self.temp_thumb_path,
            "frame_start": self.start_frame_spin.value(),
            "frame_end": self.end_frame_spin.value(),
            "script_code": self.script_edit.toPlainText().strip() if hasattr(self, "script_edit") else ""
        }
