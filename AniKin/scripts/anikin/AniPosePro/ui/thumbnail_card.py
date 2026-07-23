"""
thumbnail_card.py — Multi-Size Thumbnail Card for AniPose Pro V3.1 Grid View.
Supports XS/S/M/L/XL sizing, type badges, animated GIF playback on hover, pose diff overlay, favorite toggle, and rich context menu.
"""

import os
import maya.cmds as cmds
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui


class ThumbnailCardWidget(QtWidgets.QFrame):
    """
    Card widget matching Section 7.2 of AniPose Pro PRD.
    """

    card_clicked = QtCore.Signal(dict, bool)        # (item_dict, is_double_click)
    favorite_toggled = QtCore.Signal(dict, bool)    # (item_dict, new_fav_state)
    action_requested = QtCore.Signal(str, dict)     # (action_name, item_dict)

    CARD_SIZES = {
        "XS": (80, 80),
        "S": (120, 120),
        "M": (160, 160),
        "L": (200, 200),
        "XL": (256, 256)
    }

    def __init__(self, item_dict: dict, size_preset: str = "M", parent=None):
        super(ThumbnailCardWidget, self).__init__(parent)
        self.item_data = item_dict or {}
        self.size_preset = size_preset
        self.is_selected = False
        self._movie = None

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setObjectName("card")

        self._build_ui()
        self.update_style()

    def _build_ui(self):
        w, h = self.CARD_SIZES.get(self.size_preset, (160, 160))
        self.setFixedSize(w + 16, h + 50)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)

        # Image Container Stack
        self.img_container = QtWidgets.QFrame()
        self.img_container.setFixedSize(w, h)
        self.img_container.setStyleSheet("background: #161a1d; border-radius: 4px;")

        img_lay = QtWidgets.QVBoxLayout(self.img_container)
        img_lay.setContentsMargins(0, 0, 0, 0)

        self.img_lbl = QtWidgets.QLabel()
        self.img_lbl.setAlignment(QtCore.Qt.AlignCenter)
        img_lay.addWidget(self.img_lbl)

        # Type Badge (Top-Left)
        itype = self.item_data.get("type", "pose")
        badge_text = "P"
        badge_bg = "#3a9e6e"
        if itype == "clip":
            dur = self.item_data.get("duration") or self.item_data.get("frame_count") or 0
            badge_text = f"C {dur}f" if dur else "C"
            badge_bg = "#d4860a"
        elif itype == "script":
            badge_text = "S"
            badge_bg = "#9b59b6"
        elif itype == "mirror":
            badge_text = "M"
            badge_bg = "#2980b9"
        elif itype == "selection":
            badge_text = "Sel"
            badge_bg = "#e67e22"

        self.type_badge = QtWidgets.QLabel(badge_text, self.img_container)
        self.type_badge.setStyleSheet(f"background: {badge_bg}; color: #ffffff; font-weight: bold; font-size: 9px; padding: 2px 4px; border-bottom-right-radius: 4px;")
        self.type_badge.move(0, 0)

        # Favorite Heart Toggle (Top-Right)
        self.fav_btn = QtWidgets.QPushButton("♥" if self.item_data.get("favorite") else "♡", self.img_container)
        self.fav_btn.setFixedSize(22, 22)
        self.fav_btn.setStyleSheet("background: transparent; color: #e74c3c; border: none; font-size: 14px;")
        self.fav_btn.move(w - 24, 2)
        self.fav_btn.clicked.connect(self._toggle_favorite)

        # Diff Overlay Label (for pose hovers)
        self.diff_overlay = QtWidgets.QLabel(self.img_container)
        self.diff_overlay.setFixedSize(w, h)
        self.diff_overlay.setStyleSheet("background: rgba(13, 15, 16, 0.85); color: #f0f2f4; font-size: 10px; padding: 6px;")
        self.diff_overlay.setWordWrap(True)
        self.diff_overlay.hide()

        lay.addWidget(self.img_container)

        # Text Info
        self.name_lbl = QtWidgets.QLabel(self.item_data.get("name", "Item"))
        self.name_lbl.setStyleSheet("font-weight: 500; font-size: 11px; color: #f0f2f4;")
        lay.addWidget(self.name_lbl)

        # Rating + Color Dot
        bottom_h = QtWidgets.QHBoxLayout()
        bottom_h.setContentsMargins(0, 0, 0, 0)

        rating = self.item_data.get("rating", 0)
        stars = "★" * rating + "☆" * (5 - rating)
        self.rating_lbl = QtWidgets.QLabel(stars)
        self.rating_lbl.setStyleSheet("color: #d4860a; font-size: 10px;")

        color = self.item_data.get("color", "#3a9e6e")
        self.color_dot = QtWidgets.QLabel("●")
        self.color_dot.setStyleSheet(f"color: {color}; font-size: 10px;")

        bottom_h.addWidget(self.rating_lbl)
        bottom_h.addStretch()
        bottom_h.addWidget(self.color_dot)
        lay.addLayout(bottom_h)

        self._load_thumbnail()

    def _load_thumbnail(self):
        thumb_path = self.item_data.get("thumbnail", "")
        w, h = self.CARD_SIZES.get(self.size_preset, (160, 160))

        if thumb_path and os.path.exists(thumb_path):
            if thumb_path.endswith(".gif"):
                self._movie = QtGui.QMovie(thumb_path)
                self._movie.setScaledSize(QtCore.QSize(w, h))
                self.img_lbl.setMovie(self._movie)
                self._movie.jumpToFrame(0)
            else:
                pix = QtGui.QPixmap(thumb_path)
                if not pix.isNull():
                    self.img_lbl.setPixmap(pix.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                else:
                    self.img_lbl.setText(self.item_data.get("name", "")[:4])
        else:
            self.img_lbl.setText(self.item_data.get("name", "")[:4])

    def _toggle_favorite(self):
        new_state = not self.item_data.get("favorite", False)
        self.item_data["favorite"] = new_state
        self.fav_btn.setText("♥" if new_state else "♡")
        self.favorite_toggled.emit(self.item_data, new_state)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("QFrame#card { background: #1e2428; border: 2px solid #d4860a; border-radius: 6px; }")
        else:
            self.setStyleSheet("QFrame#card { background: #161a1d; border: 1px solid #2a3038; border-radius: 6px; } QFrame#card:hover { border-color: #404854; }")

    def enterEvent(self, event):
        super(ThumbnailCardWidget, self).enterEvent(event)
        # Start GIF playback on hover for clips
        if self._movie:
            self._movie.start()

        # Show diff overlay for pose items if controls exist
        if self.item_data.get("type") == "pose":
            self._show_diff_overlay()

    def leaveEvent(self, event):
        super(ThumbnailCardWidget, self).leaveEvent(event)
        if self._movie:
            self._movie.stop()
            self._movie.jumpToFrame(0)
        self.diff_overlay.hide()

    def _show_diff_overlay(self):
        meta = self.item_data.get("meta", {})
        controls = meta.get("controls", {})
        if not controls:
            return

        diffs = []
        sel = cmds.ls(selection=True, long=True) or []

        for ctrl, attrs in list(controls.items())[:5]:
            scene_node = ctrl
            if not cmds.objExists(scene_node):
                continue
            for attr, target_val in list(attrs.items())[:3]:
                try:
                    curr = cmds.getAttr(f"{scene_node}.{attr}")
                    delta = abs(curr - target_val)
                    if delta > 0.01:
                        diffs.append(f"{ctrl.split(':')[-1]}.{attr}: Δ{delta:.2f}")
                except Exception:
                    pass

        if diffs:
            self.diff_overlay.setText("Diff Preview:\n" + "\n".join(diffs))
            self.diff_overlay.show()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.card_clicked.emit(self.item_data, False)
        super(ThumbnailCardWidget, self).mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.card_clicked.emit(self.item_data, True)
        super(ThumbnailCardWidget, self).mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("QMenu { background: #161a1d; border: 1px solid #2a3038; } QMenu::item:selected { background: #2a3038; color: #d4860a; }")

        act_rename = menu.addAction("Rename")
        act_move = menu.addAction("Move to Folder")
        act_dup = menu.addAction("Duplicate")
        menu.addSeparator()

        if self.item_data.get("type") == "pose":
            act_bridge = menu.addAction("Turn into Clip from Timeline (Bridge)")
            act_bridge.triggered.connect(lambda: self.action_requested.emit("pose_to_clip_bridge", self.item_data))

        if self.item_data.get("type") == "clip":
            act_split = menu.addAction("Split at Current Frame")
            act_split.triggered.connect(lambda: self.action_requested.emit("split_clip", self.item_data))

        menu.addSeparator()
        act_path = menu.addAction("Copy Path to Clipboard")
        act_del = menu.addAction("Delete")

        act_rename.triggered.connect(lambda: self.action_requested.emit("rename", self.item_data))
        act_move.triggered.connect(lambda: self.action_requested.emit("move", self.item_data))
        act_dup.triggered.connect(lambda: self.action_requested.emit("duplicate", self.item_data))
        act_path.triggered.connect(lambda: self.action_requested.emit("copy_path", self.item_data))
        act_del.triggered.connect(lambda: self.action_requested.emit("delete", self.item_data))

        menu.exec_(event.globalPos())
