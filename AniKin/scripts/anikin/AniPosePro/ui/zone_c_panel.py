"""
zone_c_panel.py — Upgraded Right Detail Panel for AniPose Pro V3.1.
Implements Pose & Clip options, live blend slider, MMB drag driver, Mini Graph Preview, history, and click-to-paste arming.
"""

import os
import maya.cmds as cmds
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui
from anikin.AniPosePro.history import get_history

from anikin.AniPosePro.core.pose_blender import PoseBlender
from anikin.AniPosePro.core.paste_controller import AnimPasteController


class ZoneCPanel(QtWidgets.QWidget):
    """
    Right detail panel with Info / Options / History tabs matching Section 3.2 & 4.6 of PRD.
    """

    apply_requested = QtCore.Signal(str)       # mode string
    history_restore = QtCore.Signal(int)        # history index
    edit_info_requested = QtCore.Signal()       # trigger edit info dialog
    arm_paste_requested = QtCore.Signal(dict, dict) # (clip_data, paste_options)

    def __init__(self, parent=None):
        super(ZoneCPanel, self).__init__(parent)
        self.setFixedWidth(280)

        self._current_entry = None
        self._is_clip = False
        self._pose_blender = None
        self._movie = None

        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Preview Thumbnail
        self.thumb_label = QtWidgets.QLabel()
        self.thumb_label.setFixedSize(264, 180)
        self.thumb_label.setAlignment(QtCore.Qt.AlignCenter)
        self.thumb_label.setStyleSheet("background: #2E2E2E; border: 1px solid #1F1F1F; border-radius: 4px;")
        self.thumb_label.setText("Select a pose or clip")
        self.thumb_label.setStyleSheet("background: #2E2E2E; border: 1px solid #1F1F1F; border-radius: 4px; color: #6B6B6B; font-size: 11px;")
        layout.addWidget(self.thumb_label)

        # 2. Main Tabs Widget
        self.tabs = QtWidgets.QTabWidget()
        self.info_tab = self._build_info_tab()
        self.options_tab = self._build_options_tab()
        self.history_tab = self._build_history_tab()

        self.tabs.addTab(self.info_tab, "Info")
        self.tabs.addTab(self.options_tab, "Options")
        self.tabs.addTab(self.history_tab, "History")
        layout.addWidget(self.tabs, stretch=1)

        # 3. Action Buttons
        self.btn_stack = QtWidgets.QStackedWidget()

        # Pose Actions Widget
        pose_w = QtWidgets.QWidget()
        p_lay = QtWidgets.QVBoxLayout(pose_w)
        p_lay.setContentsMargins(0, 0, 0, 0)
        p_lay.setSpacing(4)

        # Blend slider
        blend_row = QtWidgets.QHBoxLayout()
        blend_row.addWidget(QtWidgets.QLabel("Blend:"))
        self.blend_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.blend_slider.setRange(0, 100)
        self.blend_slider.setValue(100)
        self.blend_slider.valueChanged.connect(self._on_blend_changed)
        self.blend_slider.sliderPressed.connect(self._on_blend_start)
        blend_lbl = QtWidgets.QLabel("100%")
        self.blend_slider.valueChanged.connect(lambda v: blend_lbl.setText(f"{v}%"))
        blend_row.addWidget(self.blend_slider)
        blend_row.addWidget(blend_lbl)
        p_lay.addLayout(blend_row)

        p_btns = QtWidgets.QHBoxLayout()
        self.apply_btn = QtWidgets.QPushButton("Load Pose")
        self.apply_btn.setObjectName("primary")
        self.apply_btn.clicked.connect(lambda: self.apply_requested.emit("full"))

        self.apply_key_btn = QtWidgets.QPushButton("+ Key")
        self.apply_key_btn.clicked.connect(lambda: self.apply_requested.emit("keyframe"))

        self.mirror_btn = QtWidgets.QPushButton("Mirror")
        self.mirror_btn.clicked.connect(lambda: self.apply_requested.emit("mirror"))

        p_btns.addWidget(self.apply_btn)
        p_btns.addWidget(self.apply_key_btn)
        p_btns.addWidget(self.mirror_btn)
        p_lay.addLayout(p_btns)

        self.btn_stack.addWidget(pose_w)

        # Clip Actions Widget
        clip_w = QtWidgets.QWidget()
        c_lay = QtWidgets.QVBoxLayout(clip_w)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(4)

        self.arm_btn = QtWidgets.QPushButton("Arm for Paste")
        self.arm_btn.setObjectName("primary")
        self.arm_btn.clicked.connect(self._on_arm_paste_clicked)

        self.load_curr_btn = QtWidgets.QPushButton("Load at Current Frame")
        self.load_curr_btn.clicked.connect(lambda: self.apply_requested.emit("paste_clip"))

        c_lay.addWidget(self.arm_btn)
        c_lay.addWidget(self.load_curr_btn)

        self.btn_stack.addWidget(clip_w)
        layout.addWidget(self.btn_stack)

    def _build_info_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(4, 6, 4, 4)
        lay.setSpacing(6)

        form = QtWidgets.QFormLayout()
        form.setSpacing(4)

        self.info_name = QtWidgets.QLabel("—")
        self.info_name.setStyleSheet("font-weight: bold; font-size: 13px; color: #E8E8E8;")
        self.info_rig = QtWidgets.QLabel("—")
        self.info_author = QtWidgets.QLabel("—")
        self.info_date = QtWidgets.QLabel("—")
        self.info_tags = QtWidgets.QLabel("—")
        self.info_tags.setWordWrap(True)
        self.info_notes = QtWidgets.QLabel("—")
        self.info_notes.setWordWrap(True)

        form.addRow("Name:", self.info_name)
        form.addRow("Rig:", self.info_rig)
        form.addRow("Author:", self.info_author)
        form.addRow("Date:", self.info_date)
        form.addRow("Tags:", self.info_tags)
        form.addRow("Notes:", self.info_notes)

        # Clip-specific
        self.info_frames_lbl = QtWidgets.QLabel("—")
        self.info_fps_lbl = QtWidgets.QLabel("—")
        form.addRow("Frames:", self.info_frames_lbl)
        form.addRow("FPS:", self.info_fps_lbl)

        lay.addLayout(form)



        self.edit_info_btn = QtWidgets.QPushButton("Edit Info")
        self.edit_info_btn.setStyleSheet("font-size: 10px; padding: 4px; margin-top: 6px;")
        self.edit_info_btn.clicked.connect(self.edit_info_requested.emit)
        lay.addWidget(self.edit_info_btn)

        return w

    def _build_options_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(4, 6, 4, 4)
        lay.setSpacing(8)

        # Pose Options Group
        self.pose_opts_grp = QtWidgets.QGroupBox("Pose Options")
        po_lay = QtWidgets.QVBoxLayout(self.pose_opts_grp)

        self.chk_key = QtWidgets.QCheckBox("Key on Apply")
        self.chk_key.setChecked(True)
        self.chk_mirror = QtWidgets.QCheckBox("Mirror Pose")
        self.chk_additive = QtWidgets.QCheckBox("Additive Blend")

        po_lay.addWidget(self.chk_key)
        po_lay.addWidget(self.chk_mirror)
        po_lay.addWidget(self.chk_additive)

        # Channels Picker
        po_lay.addWidget(QtWidgets.QLabel("Channels to Apply:"))
        ch_lay = QtWidgets.QHBoxLayout()
        self.chk_t = QtWidgets.QCheckBox("Trans")
        self.chk_r = QtWidgets.QCheckBox("Rot")
        self.chk_s = QtWidgets.QCheckBox("Scale")
        self.chk_c = QtWidgets.QCheckBox("Custom")
        for c in [self.chk_t, self.chk_r, self.chk_s, self.chk_c]:
            c.setChecked(True)
            ch_lay.addWidget(c)
        po_lay.addLayout(ch_lay)
        lay.addWidget(self.pose_opts_grp)

        # Clip Options Group
        self.clip_opts_grp = QtWidgets.QGroupBox("AniCapture Clip Options")
        co_lay = QtWidgets.QVBoxLayout(self.clip_opts_grp)

        # Paste Mode radios
        co_lay.addWidget(QtWidgets.QLabel("Paste Mode:"))
        pm_h = QtWidgets.QHBoxLayout()
        self.rb_replace = QtWidgets.QRadioButton("Replace")
        self.rb_merge = QtWidgets.QRadioButton("Merge")
        self.rb_insert = QtWidgets.QRadioButton("Insert")
        self.rb_replace.setChecked(True)
        for rb in [self.rb_replace, self.rb_merge, self.rb_insert]:
            pm_h.addWidget(rb)
        co_lay.addLayout(pm_h)

        self.chk_clip_additive = QtWidgets.QCheckBox("Additive Layer")
        self.chk_new_layer = QtWidgets.QCheckBox("New Anim Layer")
        self.chk_multi_paste = QtWidgets.QCheckBox("Multi-Paste")
        co_lay.addWidget(self.chk_clip_additive)
        co_lay.addWidget(self.chk_new_layer)
        co_lay.addWidget(self.chk_multi_paste)

        # Time Scale
        ts_row = QtWidgets.QHBoxLayout()
        ts_row.addWidget(QtWidgets.QLabel("Time Scale:"))
        self.scale_spin = QtWidgets.QDoubleSpinBox()
        self.scale_spin.setRange(0.25, 3.0)
        self.scale_spin.setSingleStep(0.25)
        self.scale_spin.setValue(1.0)
        ts_row.addWidget(self.scale_spin)
        co_lay.addLayout(ts_row)

        lay.addWidget(self.clip_opts_grp)

        # Namespace Option
        ns_grp = QtWidgets.QGroupBox("Namespace")
        ns_lay = QtWidgets.QVBoxLayout(ns_grp)
        self.ns_combo = QtWidgets.QComboBox()
        self.ns_combo.addItems(["From Selection", "From File", "Custom"])
        ns_lay.addWidget(self.ns_combo)
        self.ns_custom_edit = QtWidgets.QLineEdit()
        self.ns_custom_edit.setPlaceholderText("Custom namespace...")
        self.ns_custom_edit.setVisible(False)
        self.ns_combo.currentTextChanged.connect(lambda t: self.ns_custom_edit.setVisible(t == "Custom"))
        ns_lay.addWidget(self.ns_custom_edit)
        lay.addWidget(ns_grp)

        lay.addStretch()
        return w

    def _build_history_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(4, 6, 4, 4)

        self.history_list = QtWidgets.QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_restore)
        lay.addWidget(self.history_list)

        restore_btn = QtWidgets.QPushButton("↩ Restore Selected")
        restore_btn.clicked.connect(self._on_history_btn)
        lay.addWidget(restore_btn)
        return w

    def set_entry(self, entry, is_clip=False):
        self._current_entry = entry
        self._is_clip = is_clip
        meta = entry.get("meta", {}) if entry else {}

        if not entry:
            self.info_name.setText("—")
            self.info_rig.setText("—")
            self.info_author.setText("—")
            self.info_date.setText("—")
            self.info_tags.setText("—")
            self.info_notes.setText("—")
            self.info_frames_lbl.setText("—")
            self.info_fps_lbl.setText("—")

            self.thumb_label.setText("Select a pose\nor clip")
            return

        self.info_name.setText(meta.get("name", entry.get("name", "—")))
        self.info_rig.setText(meta.get("rig_hint", meta.get("rig", "—")))
        self.info_author.setText(meta.get("author", "—"))
        self.info_date.setText(str(meta.get("created", meta.get("date", "—")))[:10])
        self.info_tags.setText(", ".join(meta.get("tags", [])) or "—")
        self.info_notes.setText(meta.get("notes", "") or "—")

        if is_clip:
            self.btn_stack.setCurrentIndex(1)
            self.pose_opts_grp.setVisible(False)
            self.clip_opts_grp.setVisible(True)
            self.info_frames_lbl.setText(str(meta.get("duration", meta.get("frame_count", "—"))))
            self.info_fps_lbl.setText(str(meta.get("fps", "—")))
            # Load the actual clip file for curve preview (not the sidecar metadata)
            clip_data = self._load_clip_file(entry.get("path", ""))

        else:
            self.btn_stack.setCurrentIndex(0)
            self.pose_opts_grp.setVisible(True)
            self.clip_opts_grp.setVisible(False)
            self.info_frames_lbl.setText("—")
            self.info_fps_lbl.setText("—")


        # Thumbnail
        thumb = entry.get("thumbnail", entry.get("thumb", ""))
        if thumb and os.path.exists(thumb):
            if thumb.endswith(".gif"):
                self._movie = QtGui.QMovie(thumb)
                self._movie.setScaledSize(QtCore.QSize(264, 180))
                self.thumb_label.setMovie(self._movie)
                self._movie.start()
            else:
                pix = QtGui.QPixmap(thumb).scaled(264, 180, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                self.thumb_label.setPixmap(pix)
        else:
            self.thumb_label.setPixmap(QtGui.QPixmap())
            self.thumb_label.setText("No Preview")

    def _on_blend_start(self):
        if self._current_entry and not self._is_clip:
            meta = self._current_entry.get("meta", {})
            channels_filter = {
                "translate": self.chk_t.isChecked(),
                "rotate": self.chk_r.isChecked(),
                "scale": self.chk_s.isChecked(),
                "custom": self.chk_c.isChecked()
            }
            self._pose_blender = PoseBlender(meta, channels_filter=channels_filter)

    def _on_blend_changed(self, value: int):
        if self._pose_blender:
            self._pose_blender.blend(value / 100.0)

    def _load_clip_file(self, filepath: str) -> dict:
        """Load the actual clip/animclip JSON file from disk for curve preview."""
        if not filepath or not os.path.exists(filepath):
            return None
        try:
            import json
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _on_arm_paste_clicked(self):
        if self._current_entry and self._is_clip:
            # Load real clip data from disk (not sidecar metadata)
            clip_data = self._load_clip_file(self._current_entry.get("path", ""))
            if not clip_data:
                cmds.warning("AniPose Pro: Could not load clip data for arming.")
                return

            mode = "replace"
            if self.rb_merge.isChecked(): mode = "merge"
            elif self.rb_insert.isChecked(): mode = "insert"

            options = {
                "mode": mode,
                "time_scale": self.scale_spin.value(),
                "additive": self.chk_clip_additive.isChecked(),
                "new_layer": self.chk_new_layer.isChecked(),
                "multi_paste": self.chk_multi_paste.isChecked()
            }
            AnimPasteController.instance().arm(clip_data, options)

    def refresh_history(self):
        self.history_list.clear()
        try:
            for idx, label, ts in get_history().get_entries():
                self.history_list.addItem(f"[{ts}] {label}")
        except Exception:
            pass

    def _on_history_restore(self, item):
        row = self.history_list.row(item)
        self.history_restore.emit(row)

    def _on_history_btn(self):
        row = self.history_list.currentRow()
        if row >= 0:
            self.history_restore.emit(row)

