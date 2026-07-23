"""
graph_preview.py — Mini Graph Editor Curve Preview for AniPose Pro V3.1.
Draws bezier animation curves from serialized clip tangent data.

Supports both data formats:
  - V2 capture format (capture.py):  controls → ctrl → attr → {keys: [{time_offset, value, ...}]}
  - V3.1 serializer (curve_serializer.py): controls → ctrl → attr → {keys: [{time, value, ...}]}
"""

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui


class MiniGraphPreviewWidget(QtWidgets.QWidget):
    """
    Mini read-only graph editor preview for clip curves.
    Shows up to 8 curves with color-coded lines and key dots.
    """

    def __init__(self, parent=None):
        super(MiniGraphPreviewWidget, self).__init__(parent)
        self.setMinimumHeight(120)
        self.setMaximumHeight(160)
        self.curve_data_list = []  # list of {"label": str, "keys": [{"t": float, "v": float}, ...]}

    def set_clip_data(self, clip_data: dict):
        """
        Parse controls from a clip data dict.
        Expects: clip_data["controls"] = {ctrl_name: {attr_name: {keys: [...]}}}
        """
        self.curve_data_list = []
        if not clip_data:
            self.update()
            return

        controls = clip_data.get("controls", {})
        if not controls:
            self.update()
            return

        for ctrl, attrs in controls.items():
            if not isinstance(attrs, dict):
                continue
            for attr, c_data in attrs.items():
                if not isinstance(c_data, dict):
                    continue
                raw_keys = c_data.get("keys", [])
                if not raw_keys:
                    continue

                parsed_keys = []
                for k in raw_keys:
                    # Support both "time" and "time_offset" key names
                    t = k.get("time", k.get("time_offset", 0.0))
                    v = k.get("value", 0.0)
                    parsed_keys.append({"t": float(t), "v": float(v)})

                if parsed_keys:
                    short_ctrl = ctrl.split(":")[-1] if ":" in ctrl else ctrl
                    self.curve_data_list.append({
                        "label": f"{short_ctrl}.{attr}",
                        "keys": parsed_keys
                    })

        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QtGui.QColor("#161a1d"))

        # Grid lines
        painter.setPen(QtGui.QPen(QtGui.QColor("#2a3038"), 1, QtCore.Qt.DashLine))
        mid_y = rect.height() // 2
        mid_x = rect.width() // 2
        painter.drawLine(0, mid_y, rect.width(), mid_y)
        painter.drawLine(mid_x, 0, mid_x, rect.height())

        if not self.curve_data_list:
            painter.setPen(QtGui.QColor("#8b9299"))
            painter.drawText(rect, QtCore.Qt.AlignCenter, "No Curve Data")
            painter.end()
            return

        # Find global time & value bounds across ALL curves
        min_t, max_t = float("inf"), float("-inf")
        min_v, max_v = float("inf"), float("-inf")

        for curve in self.curve_data_list:
            for k in curve["keys"]:
                t, v = k["t"], k["v"]
                if t < min_t: min_t = t
                if t > max_t: max_t = t
                if v < min_v: min_v = v
                if v > max_v: max_v = v

        # Safety: avoid zero-range
        if max_t <= min_t:
            max_t = min_t + 1.0
        if max_v <= min_v:
            max_v = min_v + 1.0
            min_v = min_v - 1.0

        time_range = max_t - min_t
        val_range = max_v - min_v

        margin = 15
        w = rect.width() - (margin * 2)
        h = rect.height() - (margin * 2)

        colors = [
            QtGui.QColor("#e74c3c"),  # red
            QtGui.QColor("#2ecc71"),  # green
            QtGui.QColor("#3498db"),  # blue
            QtGui.QColor("#f1c40f"),  # yellow
            QtGui.QColor("#9b59b6"),  # purple
            QtGui.QColor("#e67e22"),  # orange
            QtGui.QColor("#1abc9c"),  # teal
            QtGui.QColor("#e91e63"),  # pink
        ]

        # Draw up to 8 curves
        for idx, curve in enumerate(self.curve_data_list[:8]):
            color = colors[idx % len(colors)]
            pen = QtGui.QPen(color, 1.5)
            painter.setPen(pen)

            keys = curve["keys"]
            path = QtGui.QPainterPath()

            for i, k in enumerate(keys):
                t, v = k["t"], k["v"]
                px = margin + ((t - min_t) / time_range) * w
                py = rect.height() - margin - ((v - min_v) / val_range) * h

                if i == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)

            painter.drawPath(path)

            # Draw key dots
            painter.setBrush(QtGui.QBrush(color))
            for k in keys:
                t, v = k["t"], k["v"]
                px = margin + ((t - min_t) / time_range) * w
                py = rect.height() - margin - ((v - min_v) / val_range) * h
                painter.drawEllipse(QtCore.QPointF(px, py), 2.5, 2.5)

        # Legend (top-left, small)
        painter.setPen(QtGui.QColor("#8b9299"))
        font = painter.font()
        font.setPixelSize(8)
        painter.setFont(font)
        y_off = 8
        for idx, curve in enumerate(self.curve_data_list[:4]):
            color = colors[idx % len(colors)]
            painter.setPen(color)
            painter.drawText(margin + 2, y_off + 8, curve["label"])
            y_off += 10

        painter.end()
