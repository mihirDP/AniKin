"""
graph_preview.py — CurvePreviewWidget for AniPose Pro V3.3.
Unified curve renderer for both Poses and Clips (PRD §6).
Collapsed sparkline (32px) on hover → expands to 140px on selection click.
Draws multi-curve overlays with proper axis padding, grid lines, and frame-range labels.
"""

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui


# ── Color palette for up to 8 overlaid curves ─────────────────────────────────
_CURVE_COLORS = [
    "#2FD3C2",   # accent-motion teal (primary)
    "#C9A227",   # accent-clip amber
    "#E8543F",   # accent-capture red
    "#7B68EE",   # medium-slate-blue
    "#3498DB",   # dodger-blue
    "#2ECC71",   # emerald
    "#E67E22",   # carrot
    "#9B59B6",   # amethyst
]


class CurvePreviewWidget(QtWidgets.QWidget):
    """
    Bottom-panel curve preview strip.
    • Collapsed (32px): thin sparkline of all curves — no labels.
    • Expanded (140px): graph-editor-style with grid, axis labels, frame readout.
    Click to toggle.
    """

    COLLAPSED_H = 32
    EXPANDED_H = 140

    def __init__(self, parent=None):
        super(CurvePreviewWidget, self).__init__(parent)
        self.setFixedHeight(self.COLLAPSED_H)
        self.setMinimumWidth(120)
        self._expanded = False
        self._curves = []       # [{label, keys: [{t, v}]}]
        self._is_pose = False
        self._min_t = self._max_t = 0.0
        self._min_v = self._max_v = 0.0
        self.setCursor(QtCore.Qt.PointingHandCursor)

    # ── public API ─────────────────────────────────────────────────────────────

    def set_data(self, clip_data: dict, is_pose: bool = False):
        """Feed in a clip/pose JSON dict.  Parses 'controls' key."""
        self._curves = []
        self._is_pose = is_pose

        if not clip_data:
            self.update()
            return

        controls = clip_data.get("controls", clip_data.get("objects", {}))
        if not controls:
            self.update()
            return

        for ctrl, attrs in controls.items():
            if not isinstance(attrs, dict):
                continue
            for attr, c_data in attrs.items():
                if not isinstance(c_data, dict):
                    continue
                raw = c_data.get("keys", [])
                if not raw:
                    continue
                keys = []
                for k in raw:
                    t = float(k.get("time", k.get("time_offset", 0.0)))
                    v = float(k.get("value", 0.0))
                    keys.append({"t": t, "v": v})
                if keys:
                    short = ctrl.rsplit(":", 1)[-1] if ":" in ctrl else ctrl
                    self._curves.append({"label": f"{short}.{attr}", "keys": keys})

        # Precompute bounds
        self._compute_bounds()
        self.update()

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self.setFixedHeight(self.EXPANDED_H if expanded else self.COLLAPSED_H)
        self.update()

    # ── internal ───────────────────────────────────────────────────────────────

    def _compute_bounds(self):
        mt, Mt = float("inf"), float("-inf")
        mv, Mv = float("inf"), float("-inf")
        for c in self._curves:
            for k in c["keys"]:
                t, v = k["t"], k["v"]
                if t < mt: mt = t
                if t > Mt: Mt = t
                if v < mv: mv = v
                if v > Mv: Mv = v
        if Mt <= mt:
            Mt = mt + 1.0
        if Mv <= mv:
            Mv = mv + 1.0
            mv = mv - 1.0
        # Add 5 % vertical padding so curves don't kiss the edges
        pad = (Mv - mv) * 0.05
        self._min_t, self._max_t = mt, Mt
        self._min_v, self._max_v = mv - pad, Mv + pad

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.set_expanded(not self._expanded)

    # ── paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r = self.rect()

        # Background
        p.fillRect(r, QtGui.QColor("#2E2E2E"))

        # Top hairline border
        p.setPen(QtGui.QColor("#1F1F1F"))
        p.drawLine(0, 0, r.width(), 0)

        if not self._curves:
            p.setPen(QtGui.QColor("#6B6B6B"))
            font = p.font()
            font.setPixelSize(10)
            p.setFont(font)
            txt = "No Curve Data" if self._expanded else ""
            p.drawText(r, QtCore.Qt.AlignCenter, txt)
            p.end()
            return

        # Draw areas
        if self._expanded:
            self._paint_expanded(p, r)
        else:
            self._paint_sparkline(p, r)

        p.end()

    # ── collapsed sparkline ────────────────────────────────────────────────────

    def _paint_sparkline(self, p, r):
        mx = 6
        my = 4
        w = r.width() - mx * 2
        h = r.height() - my * 2
        tr = self._max_t - self._min_t
        vr = self._max_v - self._min_v

        for ci, curve in enumerate(self._curves[:8]):
            col = QtGui.QColor(_CURVE_COLORS[ci % len(_CURVE_COLORS)])
            col.setAlpha(180)
            p.setPen(QtGui.QPen(col, 1.2))
            path = QtGui.QPainterPath()
            for i, k in enumerate(curve["keys"]):
                px = mx + ((k["t"] - self._min_t) / tr) * w
                py = r.height() - my - ((k["v"] - self._min_v) / vr) * h
                if i == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)
            p.drawPath(path)

    # ── expanded graph view ────────────────────────────────────────────────────

    def _paint_expanded(self, p, r):
        # Layout constants
        left_gutter = 36          # space for value labels
        bottom_gutter = 18        # space for frame labels
        top_pad = 18              # title row
        right_pad = 8

        gx = left_gutter
        gy = top_pad
        gw = r.width() - left_gutter - right_pad
        gh = r.height() - top_pad - bottom_gutter

        if gw < 20 or gh < 10:
            return

        tr = self._max_t - self._min_t
        vr = self._max_v - self._min_v

        # ── Title ──
        p.setPen(QtGui.QColor("#9A9A9A"))
        tf = p.font()
        tf.setPixelSize(10)
        p.setFont(tf)
        p.drawText(gx, 12, "Curve Preview")

        # ── Grid lines (3 horizontal, 1 vertical center) ──
        p.setPen(QtGui.QPen(QtGui.QColor("#3A3A3A"), 1, QtCore.Qt.DotLine))
        for frac in (0.25, 0.5, 0.75):
            y = int(gy + gh * frac)
            p.drawLine(gx, y, gx + gw, y)
        cx = int(gx + gw * 0.5)
        p.drawLine(cx, gy, cx, gy + gh)

        # ── Curves ──
        for ci, curve in enumerate(self._curves[:8]):
            col = QtGui.QColor(_CURVE_COLORS[ci % len(_CURVE_COLORS)])
            p.setPen(QtGui.QPen(col, 1.5))
            keys = curve["keys"]

            if self._is_pose and len(keys) == 1:
                # Value-fan: horizontal tick at value height
                v = keys[0]["v"]
                py = gy + gh - ((v - self._min_v) / vr) * gh
                x1 = gx + gw * 0.35
                x2 = gx + gw * 0.65
                p.drawLine(QtCore.QPointF(x1, py), QtCore.QPointF(x2, py))
                # small dot
                p.setBrush(col)
                p.drawEllipse(QtCore.QPointF((x1 + x2) / 2, py), 2.5, 2.5)
                p.setBrush(QtCore.Qt.NoBrush)
            else:
                path = QtGui.QPainterPath()
                for i, k in enumerate(keys):
                    px = gx + ((k["t"] - self._min_t) / tr) * gw
                    py = gy + gh - ((k["v"] - self._min_v) / vr) * gh
                    if i == 0:
                        path.moveTo(px, py)
                    else:
                        path.lineTo(px, py)
                p.drawPath(path)

                # Key dots
                p.setBrush(col)
                for k in keys:
                    px = gx + ((k["t"] - self._min_t) / tr) * gw
                    py = gy + gh - ((k["v"] - self._min_v) / vr) * gh
                    p.drawEllipse(QtCore.QPointF(px, py), 2, 2)
                p.setBrush(QtCore.Qt.NoBrush)

        # ── Axis labels ──
        af = p.font()
        af.setPixelSize(9)
        af.setFamily("Consolas")
        p.setFont(af)
        p.setPen(QtGui.QColor("#9A9A9A"))

        # Frame labels (bottom)
        p.drawText(gx, r.height() - 4, f"{int(self._min_t)}")
        mid_f = int((self._min_t + self._max_t) / 2)
        p.drawText(cx - 8, r.height() - 4, f"{mid_f}")
        end_txt = f"{int(self._max_t)}"
        p.drawText(gx + gw - len(end_txt) * 6, r.height() - 4, end_txt)

        # Value labels (left gutter)
        for frac, label_frac in ((0.0, 1.0), (0.5, 0.5), (1.0, 0.0)):
            val = self._min_v + vr * label_frac
            y = int(gy + gh * frac)
            p.drawText(2, y + 4, f"{val:.1f}")

        # ── Legend (top-right, first 4 curves) ──
        lf = p.font()
        lf.setPixelSize(8)
        p.setFont(lf)
        lx = gx + gw - 80
        ly = top_pad + 4
        for ci, curve in enumerate(self._curves[:4]):
            col = QtGui.QColor(_CURVE_COLORS[ci % len(_CURVE_COLORS)])
            p.setPen(col)
            p.drawText(lx, ly + ci * 10, curve["label"][:16])


# ── Backward-compat alias ──────────────────────────────────────────────────────
MiniGraphPreviewWidget = CurvePreviewWidget
