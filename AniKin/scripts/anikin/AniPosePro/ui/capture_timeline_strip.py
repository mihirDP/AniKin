"""
capture_timeline_strip.py — Mini timeline for Animation Capture (F-AC-02).

- Shift+drag: select a frame range -> triggers 'range_selected' signal
- Single left click (no shift): paste active clip at clicked frame
  -> triggers 'paste_at_frame' signal
- Hover with active clip: ghost highlight shows clip landing zone

ALL Maya cmds calls are done outside paintEvent to prevent crashes.
The strip caches timeline state and only queries Maya on explicit user actions.
"""

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui


class CaptureTimelineStrip(QtWidgets.QWidget):
    """
    Mini timeline strip for the Animation Capture section.
    Provides click-to-paste and shift-drag range selection.
    """
    range_selected = QtCore.Signal(int, int)  # (start_frame, end_frame)
    paste_at_frame = QtCore.Signal(int)       # (dest_frame,)

    def __init__(self, parent=None):
        super(CaptureTimelineStrip, self).__init__(parent)
        self._range_start = None
        self._range_end = None
        self._active_clip = None
        self._active_clip_frames = 0
        self._hover_frame = None

        # Cached Maya state — populated on showEvent and mouse clicks
        self._cached_start = 1
        self._cached_end = 100
        self._cached_time = 1

        self.setMinimumHeight(36)
        self.setMaximumHeight(36)
        self.setMouseTracking(True)
        self.setCursor(QtCore.Qt.CrossCursor)

    # ── Maya State Sync ───────────────────────────────────────────────────

    def showEvent(self, event):
        """Defer Maya queries so they don't run inside Qt's layout pass."""
        super(CaptureTimelineStrip, self).showEvent(event)
        try:
            import maya.utils as mu
            mu.executeDeferred(self._deferred_sync)
        except Exception:
            pass

    def _deferred_sync(self):
        """Called via executeDeferred — safe to query Maya here."""
        self._sync_maya_state()
        self.update()

    def _sync_maya_state(self):
        """Fetch Maya playback range and current time into cache."""
        try:
            import maya.cmds as cmds
            self._cached_start = cmds.playbackOptions(q=True, min=True)
            self._cached_end = cmds.playbackOptions(q=True, max=True)
            self._cached_time = cmds.currentTime(q=True)
        except Exception:
            pass

    def set_active_clip(self, clip_data_or_none):
        """Set the currently selected clip for paste operations."""
        self._active_clip = clip_data_or_none
        if clip_data_or_none:
            self._active_clip_frames = clip_data_or_none.get("frame_count", 0)
        else:
            self._active_clip_frames = 0
        self.update()

    # ── Mouse Events ──────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        # Sync Maya state on click — safe context (user-initiated)
        self._sync_maya_state()
        frame = self._pixel_to_frame(event.x())

        if event.modifiers() & QtCore.Qt.ShiftModifier:
            # Begin range selection
            self._range_start = frame
            self._range_end = frame
        elif event.button() == QtCore.Qt.LeftButton:
            if self._active_clip is not None:
                # One-click paste — the signature interaction
                self.paste_at_frame.emit(frame)
            else:
                # No active clip — just move playhead
                try:
                    import maya.cmds as cmds
                    cmds.currentTime(frame)
                    self._cached_time = frame
                except Exception:
                    pass
        self.update()

    def mouseMoveEvent(self, event):
        if self._range_start is not None:
            self._range_end = self._pixel_to_frame(event.x())
            self.update()
        else:
            self._hover_frame = self._pixel_to_frame(event.x())
            self.update()

    def mouseReleaseEvent(self, event):
        if self._range_start is not None:
            s = min(self._range_start, self._range_end)
            e = max(self._range_start, self._range_end)
            if e > s:
                self.range_selected.emit(s, e)
            self._range_start = None
            self._range_end = None
            self.update()

    def leaveEvent(self, event):
        self._hover_frame = None
        self.update()

    # ── Paint (NO Maya cmds calls allowed here) ───────────────────────────

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QtGui.QColor("#1a1e26"))

        start = self._cached_start
        end = self._cached_end
        total = max(end - start, 1)

        # Frame tick marks
        painter.setPen(QtGui.QColor("#444"))
        tick_step = max(1, int(total) // 20)
        for f in range(int(start), int(end) + 1, tick_step):
            x = int(self._frame_to_pixel(f))
            painter.drawLine(x, h - 8, x, h)

        # Frame numbers
        label_step = max(1, int(total) // 10)
        painter.setPen(QtGui.QColor("#888"))
        font = painter.font()
        font.setPixelSize(9)
        painter.setFont(font)
        for f in range(int(start), int(end) + 1, label_step):
            x = int(self._frame_to_pixel(f))
            painter.drawText(x - 10, 10, 20, 12, QtCore.Qt.AlignCenter,
                             str(int(f)))

        # Range selection highlight
        if self._range_start is not None and self._range_end is not None:
            s = min(self._range_start, self._range_end)
            e = max(self._range_start, self._range_end)
            x1 = int(self._frame_to_pixel(s))
            x2 = int(self._frame_to_pixel(e))
            painter.fillRect(x1, 0, x2 - x1, h,
                             QtGui.QColor(77, 166, 255, 80))
            painter.setPen(QtGui.QColor(77, 166, 255))
            painter.drawRect(x1, 0, x2 - x1, h - 1)

        # Ghost clip preview on hover
        if (self._active_clip is not None and self._hover_frame is not None
                and self._range_start is None):
            ghost_x = int(self._frame_to_pixel(self._hover_frame))
            ghost_w = int(self._frame_to_pixel(
                self._hover_frame + self._active_clip_frames)) - ghost_x
            painter.fillRect(ghost_x, 0, ghost_w, h,
                             QtGui.QColor(100, 200, 100, 50))
            painter.setPen(QtGui.QColor(100, 200, 100, 180))
            painter.drawRect(ghost_x, 0, ghost_w, h - 1)

        # Current time indicator (from cache — no cmds call)
        cx = int(self._frame_to_pixel(self._cached_time))
        painter.setPen(QtGui.QPen(QtGui.QColor("#ff4444"), 2))
        painter.drawLine(cx, 0, cx, h)

        painter.end()

    # ── Helpers (pure math — no Maya calls) ───────────────────────────────

    def _pixel_to_frame(self, x):
        start = self._cached_start
        end = self._cached_end
        ratio = x / max(self.width(), 1)
        return int(start + ratio * (end - start))

    def _frame_to_pixel(self, frame):
        start = self._cached_start
        end = self._cached_end
        total = max(end - start, 1)
        return (frame - start) / total * self.width()
