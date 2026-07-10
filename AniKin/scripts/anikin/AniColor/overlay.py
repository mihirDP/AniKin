"""
AniColor — overlay.py
Qt label bar overlay widget drawn on top of Maya's playback slider.

Shows colored marker rectangles and truncated label text at labeled
frame positions. The overlay is transparent to mouse events — it's
display-only, passing all clicks through to the real timeline.
"""

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui, wrapInstance
from anikin.AniColor.core import load_payload


class TimelineResizeFilter(QtCore.QObject):
    """Event filter that keeps the overlay in sync with timeline resizes."""

    def __init__(self, label_bar, parent=None):
        super(TimelineResizeFilter, self).__init__(parent)
        self.label_bar = label_bar

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Resize:
            self.label_bar.setGeometry(obj.rect())
            self.label_bar.update()
        return False


class AniColorLabelBar(QtWidgets.QWidget):
    """
    Transparent overlay widget drawn on top of Maya's timeline.
    Shows colored marker rectangles and label text at labeled frames.
    """

    def __init__(self):
        # Get the Maya playback slider Qt widget
        slider_name = mel.eval("$tmp=$gPlayBackSlider")
        ptr = omui.MQtUtil.findControl(slider_name)
        timeline_qt = wrapInstance(int(ptr), QtWidgets.QWidget)

        super(AniColorLabelBar, self).__init__(parent=timeline_qt)

        # Overlay settings — transparent to mouse, no background
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        # Match parent geometry and stay on top
        self.setGeometry(timeline_qt.rect())
        self.raise_()
        self.show()

        # Data caches
        self._frame_data = {}
        self._range_data = {}
        self._palettes = {}

        # Install resize filter
        self._resize_filter = TimelineResizeFilter(self, timeline_qt)
        timeline_qt.installEventFilter(self._resize_filter)

    def update_data(self):
        """Reload data from the scene payload."""
        data = load_payload()
        self._frame_data = data.get("frames", {})
        self._range_data = data.get("ranges", {})
        # Index palettes by ID for quick lookup
        self._palettes = {}
        for p in data.get("palettes", []):
            self._palettes[p["id"]] = p
        self.update()

    def frame_to_x(self, frame):
        """Map a frame number to a pixel X position on the timeline widget."""
        try:
            slider_name = mel.eval("$tmp=$gPlayBackSlider")
            vis_range = cmds.playbackOptions(q=True, minTime=True)
            vis_end = cmds.playbackOptions(q=True, maxTime=True)
        except Exception:
            return 0

        width = self.width()
        total = vis_end - vis_range
        if total <= 0:
            return 0

        # Offset ~24px for Maya's timeline left margin
        margin_left = 24
        usable_width = width - margin_left - 10
        ratio = (frame - vis_range) / total
        return int(margin_left + ratio * usable_width)

    def paintEvent(self, event):
        if not self._frame_data and not self._range_data:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        bar_height = 6
        bar_y = self.height() - bar_height - 1

        # Draw range blocks (semi-transparent fills)
        for rid, rng in self._range_data.items():
            pid = rng.get("palette_id")
            pal = self._palettes.get(pid, {})
            if not pal.get("visible", True):
                continue
            color_rgb = pal.get("color", [1, 0, 0])
            qcolor = QtGui.QColor.fromRgbF(color_rgb[0], color_rgb[1], color_rgb[2])
            qcolor.setAlpha(80)

            x1 = self.frame_to_x(float(rng.get("start", 0)))
            x2 = self.frame_to_x(float(rng.get("end", 0)))
            painter.fillRect(x1, bar_y, max(x2 - x1, 2), bar_height, qcolor)

        # Draw individual frame markers
        try:
            font = QtGui.QFont("Inter", 7)
            painter.setFont(font)
        except Exception:
            pass

        for frame_str, entry in self._frame_data.items():
            frame = int(frame_str)
            pid = entry.get("palette_id")
            label = entry.get("label", "")
            pal = self._palettes.get(pid, {})

            if not pal.get("visible", True):
                continue

            color_rgb = pal.get("color", [1, 0, 0])
            qcolor = QtGui.QColor.fromRgbF(color_rgb[0], color_rgb[1], color_rgb[2])

            x = self.frame_to_x(frame)
            # Colored tick (6px wide)
            painter.fillRect(x - 3, bar_y, 6, bar_height, qcolor)

            # Label text above tick
            if label:
                painter.setPen(QtGui.QColor(240, 242, 244))
                short = label[:10] + "…" if len(label) > 10 else label
                painter.drawText(x - 25, bar_y - 12, 50, 12,
                                 QtCore.Qt.AlignCenter, short)

        painter.end()

    def destroy_overlay(self):
        """Clean up the overlay and event filter."""
        try:
            parent = self.parentWidget()
            if parent and self._resize_filter:
                parent.removeEventFilter(self._resize_filter)
        except Exception:
            pass
        self.setParent(None)
        self.deleteLater()


# ──────────────────────────────────────────────────────────────
# Global overlay instance
# ──────────────────────────────────────────────────────────────

_OVERLAY_INSTANCE = None


def create_overlay():
    """Create and return the global label bar overlay."""
    global _OVERLAY_INSTANCE
    destroy_overlay()
    try:
        _OVERLAY_INSTANCE = AniColorLabelBar()
        _OVERLAY_INSTANCE.update_data()
        return _OVERLAY_INSTANCE
    except Exception as e:
        cmds.warning("AniColor: Could not create overlay: {}".format(e))
        return None


def destroy_overlay():
    """Destroy the existing overlay if any."""
    global _OVERLAY_INSTANCE
    if _OVERLAY_INSTANCE is not None:
        try:
            _OVERLAY_INSTANCE.destroy_overlay()
        except Exception:
            pass
        _OVERLAY_INSTANCE = None


def refresh_overlay():
    """Refresh the overlay data (call after any data change)."""
    global _OVERLAY_INSTANCE
    if _OVERLAY_INSTANCE is not None:
        try:
            _OVERLAY_INSTANCE.update_data()
        except Exception:
            pass
