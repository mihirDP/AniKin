"""
clip_card.py — Individual animation clip card widget for AniPose Pro V2.

Displays clip thumbnail (static or animated GIF on hover),
frame count badge, CLIP type indicator, and interactive behaviors.
"""

import os
import json

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui

import maya.cmds as cmds


class ClipCard(QtWidgets.QFrame):
    """A grid card for an animation clip in the CLIPS tab."""

    clip_selected = QtCore.Signal(dict)   # emits clip_data when clicked

    def __init__(self, clip_entry, parent=None):
        super(ClipCard, self).__init__(parent)
        self._entry = clip_entry
        self._selected = False
        self._clip_data = None  # loaded lazily
        self._static_pix = None
        self._gif_movie = None
        self.setFixedSize(130, 150)
        self.setToolTip(clip_entry.get("name", ""))
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.setStyleSheet("""
            ClipCard {
                background-color: #2a2a2a;
                border: 1px solid #333;
                border-radius: 4px;
            }
            ClipCard:hover {
                border: 1px solid #4da6ff;
                background-color: #2e333d;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Thumbnail
        self.thumb_label = QtWidgets.QLabel()
        self.thumb_label.setFixedSize(126, 100)
        self.thumb_label.setAlignment(QtCore.Qt.AlignCenter)

        thumb_path = self._entry.get("thumb")
        gif_path = self._get_gif_path()

        loaded = False

        # Try GIF first
        if gif_path and os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
            try:
                pix = QtGui.QPixmap(gif_path)
                if not pix.isNull():
                    self._static_pix = pix.scaled(
                        126, 100, QtCore.Qt.KeepAspectRatioByExpanding,
                        QtCore.Qt.SmoothTransformation)
                    self.thumb_label.setPixmap(self._static_pix)
                    loaded = True
                    # Prepare QMovie for hover playback
                    self._gif_movie = QtGui.QMovie(gif_path)
                    self._gif_movie.setScaledSize(QtCore.QSize(126, 100))
            except Exception:
                pass

        # Try static thumb
        if not loaded and thumb_path and os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            try:
                pix = QtGui.QPixmap(thumb_path)
                if not pix.isNull():
                    self._static_pix = pix.scaled(
                        126, 100, QtCore.Qt.KeepAspectRatioByExpanding,
                        QtCore.Qt.SmoothTransformation)
                    self.thumb_label.setPixmap(self._static_pix)
                    loaded = True
            except Exception:
                pass

        # Fallback text
        if not loaded:
            self.thumb_label.setText("CLIP")
            self.thumb_label.setStyleSheet(
                "background: #1a1e26; color: #4da6ff; "
                "font-size: 12px; font-weight: bold;")

        layout.addWidget(self.thumb_label)

        # Bottom row: name + badges
        bottom = QtWidgets.QWidget()
        bottom.setFixedHeight(38)
        bl = QtWidgets.QVBoxLayout(bottom)
        bl.setContentsMargins(2, 0, 2, 0)
        bl.setSpacing(1)

        # Type badge + frame count
        badge_row = QtWidgets.QHBoxLayout()
        badge_row.setSpacing(4)

        type_badge = QtWidgets.QLabel("CLIP")
        type_badge.setFixedSize(32, 14)
        type_badge.setAlignment(QtCore.Qt.AlignCenter)
        type_badge.setStyleSheet(
            "background: #1a6bc4; color: white; border-radius: 3px;"
            "font-size: 8px; font-weight: bold; border: none;")
        badge_row.addWidget(type_badge)

        meta = self._entry.get("meta", {})
        fc = meta.get("frame_count", "?")
        frame_badge = QtWidgets.QLabel("{}fr".format(fc))
        frame_badge.setFixedHeight(14)
        frame_badge.setStyleSheet(
            "color: #888; font-size: 8px; border: none; background: none;")
        badge_row.addWidget(frame_badge)
        badge_row.addStretch()

        # Legacy badge
        fmt = meta.get("format", "")
        if fmt == "animclip" or (not fmt and "format" not in meta):
            legacy_badge = QtWidgets.QLabel("Legacy")
            legacy_badge.setFixedSize(40, 14)
            legacy_badge.setAlignment(QtCore.Qt.AlignCenter)
            legacy_badge.setStyleSheet(
                "background: #8B6914; color: white; border-radius: 3px;"
                "font-size: 8px; border: none;")
            badge_row.addWidget(legacy_badge)

        bl.addLayout(badge_row)

        # Name
        name_str = self._entry.get("name", "")
        self.name_label = QtWidgets.QLabel(name_str)
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setStyleSheet(
            "font-size: 9px; color: #ccc; border: none; background: none;")
        self.name_label.setWordWrap(True)
        bl.addWidget(self.name_label)

        layout.addWidget(bottom)

    # ── Hover GIF Playback ────────────────────────────────────────────────

    def enterEvent(self, event):
        if self._gif_movie:
            self.thumb_label.setMovie(self._gif_movie)
            self._gif_movie.start()
        super(ClipCard, self).enterEvent(event)

    def leaveEvent(self, event):
        if self._gif_movie:
            self._gif_movie.stop()
            if self._static_pix:
                self.thumb_label.setPixmap(self._static_pix)
        super(ClipCard, self).leaveEvent(event)

    # ── Interaction ───────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._select()

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._apply_at_current()

    def set_selected(self, state):
        self._selected = state
        if state:
            self.setStyleSheet("""
                ClipCard {
                    background-color: #2a3350;
                    border: 2px solid #4da6ff;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                ClipCard {
                    background-color: #2a2a2a;
                    border: 1px solid #333;
                    border-radius: 4px;
                }
                ClipCard:hover {
                    border: 1px solid #4da6ff;
                    background-color: #2e333d;
                }
            """)

    # ── Actions ───────────────────────────────────────────────────────────

    def _select(self):
        data = self._load_clip_data()
        if data:
            self.clip_selected.emit(data)

    def _apply_at_current(self):
        data = self._load_clip_data()
        if not data:
            return
        nodes = cmds.ls(selection=True, long=True) or []
        if not nodes:
            cmds.warning("AniPose Pro: Select controls to apply clip.")
            return

        from anikin.AniPosePro.capture import load_clip_data
        _, _, is_v2 = load_clip_data(self._entry["path"])

        frame = int(cmds.currentTime(q=True))
        if is_v2:
            from anikin.AniPosePro.paste import paste_clip_at_frame
            paste_clip_at_frame(data, nodes, frame)
        else:
            from anikin.AniPosePro.paste import paste_legacy_clip
            paste_legacy_clip(data, nodes, frame)

    def _load_clip_data(self):
        if self._clip_data:
            return self._clip_data
        try:
            with open(self._entry["path"], "r", encoding="utf-8") as f:
                self._clip_data = json.load(f)
            return self._clip_data
        except Exception as e:
            cmds.warning("AniPose Pro: Failed to load clip: {}".format(e))
            return None

    def _get_gif_path(self):
        path = self._entry.get("path", "")
        gif = path.replace(".animclip", ".thumb.gif")
        return gif

    # ── Context Menu ──────────────────────────────────────────────────────

    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        apply_action = menu.addAction("Apply at Current Frame")
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        action = menu.exec_(self.mapToGlobal(pos))
        if action == apply_action:
            self._apply_at_current()
