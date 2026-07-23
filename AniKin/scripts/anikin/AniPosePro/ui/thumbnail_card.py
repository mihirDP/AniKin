"""
thumbnail_card.py — Pose / Clip Tile for AniPose Pro V3.3.
Aesthetically polished card with GIF auto-play, hover scrub bar,
type-dot badge, edit-thumbnail pencil, and drag-to-apply.

Design tokens from PRD §2 / §4.1-4.3.
"""

import os
import maya.cmds as cmds
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui


class ThumbnailCardWidget(QtWidgets.QFrame):

    card_clicked = QtCore.Signal(dict, bool)
    favorite_toggled = QtCore.Signal(dict, bool)
    action_requested = QtCore.Signal(str, dict)

    # 4:3 thumbnail ratios per preset
    CARD_SIZES = {
        "XS": (96, 72),
        "S":  (120, 90),
        "M":  (160, 120),
        "L":  (200, 150),
        "XL": (256, 192),
    }

    def __init__(self, item_dict: dict, size_preset: str = "M", parent=None):
        super(ThumbnailCardWidget, self).__init__(parent)
        self.item_data = item_dict or {}
        self.size_preset = size_preset
        self.is_selected = False
        self._movie = None
        self._hovered = False
        self._scrub_pct = 0.0
        self._drag_start = None

        self.setObjectName("tile")
        self.setMouseTracking(True)
        self._build()
        self._apply_style()

    # ── build ──────────────────────────────────────────────────────────────────

    def _build(self):
        tw, th = self.CARD_SIZES.get(self.size_preset, (160, 120))
        card_w = tw + 16        # 8px padding each side
        card_h = th + 40        # label row + meta row
        self.setFixedSize(card_w, card_h)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Thumbnail Area ─────────────────────────────────────────────────
        self._thumb_frame = QtWidgets.QWidget()
        self._thumb_frame.setFixedSize(card_w, th)
        self._thumb_frame.setMouseTracking(True)
        self._thumb_frame.setStyleSheet("border-top-left-radius: 4px; border-top-right-radius: 4px;")

        # Image label fills thumb frame
        self._img = QtWidgets.QLabel(self._thumb_frame)
        self._img.setFixedSize(card_w, th)
        self._img.setAlignment(QtCore.Qt.AlignCenter)
        self._img.setStyleSheet("background: #2E2E2E; border-top-left-radius: 4px; border-top-right-radius: 4px;")
        self._img.setMouseTracking(True)

        # Scrub progress bar (bottom edge of thumbnail)
        self._scrub_bar = QtWidgets.QFrame(self._thumb_frame)
        self._scrub_bar.setFixedHeight(3)
        self._scrub_bar.setStyleSheet("background: #2FD3C2; border-radius: 0px;")
        self._scrub_bar.setGeometry(0, th - 3, 0, 3)
        self._scrub_bar.hide()

        # Hover badge cluster (top-right)
        self._edit_btn = QtWidgets.QPushButton("✎", self._thumb_frame)
        self._edit_btn.setFixedSize(22, 22)
        self._edit_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._edit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,0.55); color: #E8E8E8;
                border-radius: 4px; font-size: 11px; border: none;
            }
            QPushButton:hover { background: rgba(0,0,0,0.8); }
        """)
        self._edit_btn.setToolTip("Edit Thumbnail")
        self._edit_btn.move(card_w - 50, 4)
        self._edit_btn.clicked.connect(lambda: self.action_requested.emit("edit_thumbnail", self.item_data))
        self._edit_btn.hide()

        root.addWidget(self._thumb_frame)

        # ── Label Row ──────────────────────────────────────────────────────
        label_w = QtWidgets.QWidget()
        label_w.setFixedHeight(40)
        label_w.setStyleSheet("background: transparent;")
        ll = QtWidgets.QVBoxLayout(label_w)
        ll.setContentsMargins(8, 4, 8, 4)
        ll.setSpacing(1)

        # Name + type dot
        name_row = QtWidgets.QHBoxLayout()
        name_row.setSpacing(4)

        self._name_lbl = QtWidgets.QLabel()
        self._name_lbl.setStyleSheet("color: #E8E8E8; font-size: 11px; font-weight: 500; background: transparent;")
        name = self.item_data.get("name", "Untitled")
        fm = QtGui.QFontMetrics(self._name_lbl.font())
        elided = fm.elidedText(name, QtCore.Qt.ElideRight, tw - 16)
        self._name_lbl.setText(elided)
        name_row.addWidget(self._name_lbl)
        name_row.addStretch()

        # Type dot (6px)
        itype = self.item_data.get("type", "pose")
        dot_color = "#C9A227" if itype == "clip" else "#2FD3C2"
        dot = QtWidgets.QLabel("●")
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"color: {dot_color}; font-size: 8px; background: transparent;")
        dot.setAlignment(QtCore.Qt.AlignCenter)
        name_row.addWidget(dot)

        ll.addLayout(name_row)

        # Meta line
        meta = self.item_data.get("meta", {})
        if itype == "clip":
            frames = meta.get("duration", meta.get("frame_count", 0))
            start = meta.get("start", 0)
            end = meta.get("end", 0)
            meta_txt = f"{frames}f · {start}–{end}"
        else:
            tags = meta.get("tags", [])
            if tags:
                meta_txt = ", ".join(tags[:3])
            else:
                meta_txt = meta.get("rig_hint", meta.get("rig", ""))

        self._meta_lbl = QtWidgets.QLabel(meta_txt)
        self._meta_lbl.setStyleSheet("color: #9A9A9A; font-size: 9px; background: transparent;")
        ll.addWidget(self._meta_lbl)

        root.addWidget(label_w)

        # Load thumbnail image / GIF
        self._load_thumb()

    def _load_thumb(self):
        path = self.item_data.get("thumbnail", "")
        tw, th = self.CARD_SIZES.get(self.size_preset, (160, 120))
        cw = tw + 16

        if path and os.path.exists(path):
            if path.lower().endswith(".gif"):
                self._movie = QtGui.QMovie(path)
                self._movie.setScaledSize(QtCore.QSize(cw, th))
                self._img.setMovie(self._movie)
                # Auto-play GIF so preview is always alive
                self._movie.start()
            else:
                pix = QtGui.QPixmap(path)
                if not pix.isNull():
                    self._img.setPixmap(pix.scaled(cw, th, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                else:
                    self._set_placeholder()
        else:
            self._set_placeholder()

    def _set_placeholder(self):
        self._img.setText(self.item_data.get("name", "?")[:3].upper())
        self._img.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #383838, stop:1 #2E2E2E);
            color: #6B6B6B; font-size: 18px; font-weight: bold;
            border-top-left-radius: 4px; border-top-right-radius: 4px;
        """)

    # ── styling ────────────────────────────────────────────────────────────────

    def _apply_style(self):
        if self.is_selected:
            border = "2px solid #2FD3C2"
            bg = "#383838"
        elif self._hovered:
            border = "1px solid rgba(47, 211, 194, 0.4)"
            bg = "#454545"
        else:
            border = "1px solid #1F1F1F"
            bg = "#383838"
        self.setStyleSheet(f"""
            QFrame#tile {{
                background: {bg};
                border: {border};
                border-radius: 4px;
            }}
        """)

    def set_selected(self, sel: bool):
        self.is_selected = sel
        self._apply_style()

    # ── hover / scrub ──────────────────────────────────────────────────────────

    def enterEvent(self, ev):
        super().enterEvent(ev)
        self._hovered = True
        self._apply_style()
        self._edit_btn.show()
        if self._movie and self.item_data.get("type") == "clip":
            self._scrub_bar.show()

    def leaveEvent(self, ev):
        super().leaveEvent(ev)
        self._hovered = False
        self._apply_style()
        self._edit_btn.hide()
        self._scrub_bar.hide()

    def mouseMoveEvent(self, ev):
        super().mouseMoveEvent(ev)
        # Scrub GIF on horizontal mouse movement
        if self._movie and self._hovered and self.item_data.get("type") == "clip":
            w = self._thumb_frame.width()
            x = max(0, min(w, ev.pos().x()))
            pct = x / float(w) if w else 0
            fc = self._movie.frameCount()
            if fc > 0:
                self._movie.jumpToFrame(int(pct * (fc - 1)))
                self._scrub_bar.setGeometry(0, self._thumb_frame.height() - 3, max(3, int(pct * w)), 3)

    # ── click / double-click / drag ────────────────────────────────────────────

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self._drag_start = ev.pos()
            self.card_clicked.emit(self.item_data, False)
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        self._drag_start = None
        super().mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.card_clicked.emit(self.item_data, True)
        super().mouseDoubleClickEvent(ev)

    # ── context menu ───────────────────────────────────────────────────────────

    def contextMenuEvent(self, ev):
        m = QtWidgets.QMenu(self)
        m.setStyleSheet("""
            QMenu {
                background: #454545; color: #E8E8E8;
                border: 1px solid #1F1F1F; border-radius: 4px;
                padding: 4px 0;
            }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background: #525252; color: #2FD3C2; }
            QMenu::separator { height: 1px; background: #1F1F1F; margin: 4px 8px; }
        """)

        a_apply = m.addAction("▶  Apply")
        m.addSeparator()
        a_thumb = m.addAction("✎  Edit Thumbnail")
        a_rename = m.addAction("Rename")
        a_move = m.addAction("Move to Folder")
        a_dup = m.addAction("Duplicate")
        m.addSeparator()

        if self.item_data.get("type") == "pose":
            a_bridge = m.addAction("Convert to Clip")
            a_bridge.triggered.connect(lambda: self.action_requested.emit("pose_to_clip_bridge", self.item_data))

        if self.item_data.get("type") == "clip":
            a_split = m.addAction("Split at Current Frame")
            a_split.triggered.connect(lambda: self.action_requested.emit("split_clip", self.item_data))

        m.addSeparator()
        a_path = m.addAction("Copy Path")
        a_del = m.addAction("Delete")
        a_del.setStyleSheet("color: #D9483D;")

        a_apply.triggered.connect(lambda: self.action_requested.emit("apply", self.item_data))
        a_thumb.triggered.connect(lambda: self.action_requested.emit("edit_thumbnail", self.item_data))
        a_rename.triggered.connect(lambda: self.action_requested.emit("rename", self.item_data))
        a_move.triggered.connect(lambda: self.action_requested.emit("move", self.item_data))
        a_dup.triggered.connect(lambda: self.action_requested.emit("duplicate", self.item_data))
        a_path.triggered.connect(lambda: self.action_requested.emit("copy_path", self.item_data))
        a_del.triggered.connect(lambda: self.action_requested.emit("delete", self.item_data))

        m.exec_(ev.globalPos())
