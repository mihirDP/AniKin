"""
widgets.py
Reusable UI widgets for AniKin.

Small, focused widget classes used across the toolbar and panels.
"""

import os
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui


# ─────────────────────────────────────────────────────────
# Flow Layout — wraps children to next row, like a word wrap
# ─────────────────────────────────────────────────────────

class FlowLayout(QtWidgets.QLayout):
    """
    A Qt layout that arranges children left-to-right, wrapping to
    the next row when the available width is exhausted.
    Suitable for a toolbar that needs to wrap rather than compress.
    """

    def __init__(self, parent=None, margin=0, spacing=3):
        super(FlowLayout, self).__init__(parent)
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QtCore.QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QtCore.QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom()
        )
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._items:
            widget = item.widget()
            space_x = spacing
            space_y = spacing
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom


# ─────────────────────────────────────────────────────────
# Section separator
# ─────────────────────────────────────────────────────────

class SectionSeparator(QtWidgets.QFrame):
    """A vertical line separator between toolbar sections."""

    def __init__(self, parent=None):
        super(SectionSeparator, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setFixedWidth(2)


# ─────────────────────────────────────────────────────────
# Tool Button
# ─────────────────────────────────────────────────────────

class ToolButton(QtWidgets.QPushButton):
    """
    An icon-first toolbar button.

    In v0.4.0, the label directly corresponds to the SVG filename in the
    icons/ directory (e.g., label="align_all" loads "align_all.svg").
    If no icon is found, the label text is shown as a fallback.

    Args:
        label: Icon filename stem (e.g., "align_all") or display text fallback.
        tooltip: Tooltip shown on hover.
        callback: Function called on click.
        accent: If True, uses accent styling (subtle border highlight).
    """

    # Calculate icons dir once at class level
    _ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")

    def __init__(self, label, tooltip="", callback=None, accent=False,
                 parent=None):
        super(ToolButton, self).__init__(parent)

        if tooltip:
            self.setToolTip(tooltip)
        if callback:
            self.clicked.connect(callback)
        if accent:
            self.setProperty("accent", True)

        # Try to load icon by label name directly
        icon_found = False
        for ext in (".svg", ".png"):
            icon_path = os.path.join(self._ICONS_DIR, label + ext)
            if os.path.exists(icon_path):
                self.setIcon(QtGui.QIcon(icon_path))
                icon_found = True
                break

        if icon_found:
            self.setIconSize(QtCore.QSize(26, 26))
            self.setText("")  # Hide text — icon only
            self.setFixedSize(36, 36)
        else:
            # Fallback: display the label text
            self.setText(label)
            self.setMinimumWidth(34)

        # Context menu support
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self._context_menu_actions = []

    def set_context_menu(self, actions):
        """
        Set actions for the right-click menu.
        actions: list of tuples (label_text, callback_callable)
        """
        self._context_menu_actions = actions

    def _on_context_menu(self, pos):
        if not self._context_menu_actions:
            return
        menu = QtWidgets.QMenu(self)
        for label, callback in self._context_menu_actions:
            if label is None:
                menu.addSeparator()
            else:
                action = menu.addAction(label)
                action.triggered.connect(callback)
        menu.exec_(self.mapToGlobal(pos))


# ─────────────────────────────────────────────────────────
# Toggle Tool Button — swappable icon states
# ─────────────────────────────────────────────────────────

class ToggleToolButton(ToolButton):
    """
    A ToolButton with two visual states (A / B).

    On each click the icon, tooltip, and optional accent border swap,
    giving the user immediate feedback on the current state.

    Args:
        icon_a / icon_b: SVG filename stems for the two states.
        tooltip_a / tooltip_b: Tooltips for each state.
        callback: Called on every click with the *new* ``toggled`` bool
                  (True = state B, False = state A).
        start_toggled: If True, start in state B.
        accent_a / accent_b: Whether each state uses accent styling.
    """

    _ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")

    def __init__(self, icon_a, icon_b, tooltip_a="", tooltip_b="",
                 callback=None, start_toggled=False,
                 accent_a=False, accent_b=False, parent=None):
        # Initialise base class with state-A icon (no callback yet)
        super(ToggleToolButton, self).__init__(
            icon_a, tooltip=tooltip_a, callback=None,
            accent=accent_a, parent=parent
        )

        self._icon_a_path = self._find_icon(icon_a)
        self._icon_b_path = self._find_icon(icon_b)
        self._tooltip_a = tooltip_a
        self._tooltip_b = tooltip_b
        self._accent_a = accent_a
        self._accent_b = accent_b
        self._toggled = False
        self._user_callback = callback

        # Connect our own handler
        self.clicked.connect(self._on_clicked)

        if start_toggled:
            self._toggled = True
            self._apply_state()

    # ── helpers ────────────────────────────────────────────
    def _find_icon(self, label):
        for ext in (".svg", ".png"):
            path = os.path.join(self._ICONS_DIR, label + ext)
            if os.path.exists(path):
                return path
        return None

    def _apply_state(self):
        """Apply the current state's icon, tooltip, and accent."""
        if self._toggled:
            icon_path = self._icon_b_path
            tip = self._tooltip_b
            accent = self._accent_b
        else:
            icon_path = self._icon_a_path
            tip = self._tooltip_a
            accent = self._accent_a

        if icon_path:
            self.setIcon(QtGui.QIcon(icon_path))
        self.setToolTip(tip)
        self.setProperty("accent", accent)
        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _on_clicked(self):
        self._toggled = not self._toggled
        self._apply_state()
        if self._user_callback:
            self._user_callback(self._toggled)

    def set_toggled(self, state):
        """Programmatically set the toggle state without firing the callback."""
        self._toggled = bool(state)
        self._apply_state()

    def is_toggled(self):
        """Return the current toggle state."""
        return self._toggled


# ─────────────────────────────────────────────────────────
# Tween / Ease Slider  — compact, color-coded
# ─────────────────────────────────────────────────────────

# Per-slider accent colours (separate from global ACCENT so they can't be confused)
_SLIDER_THEMES = {
    "TW": {
        "badge_bg":    "#c25900",   # Warm amber-orange
        "badge_fg":    "#fff3e0",
        "groove":      "#1e1e1e",
        "fill":        "#f97316",   # Orange fill
        "handle":      "#fb923c",
        "handle_bdr":  "#c2410c",
        "label":       "TW",
    },
    "EA": {
        "badge_bg":    "#5b21b6",   # Deep violet
        "badge_fg":    "#ede9fe",
        "groove":      "#1e1e1e",
        "fill":        "#7c3aed",   # Purple fill
        "handle":      "#a78bfa",
        "handle_bdr":  "#4c1d95",
        "label":       "EA",
    },
}


class TweenSlider(QtWidgets.QWidget):
    """
    A compact, color-coded slider widget for the Tween and Ease tools.

    Emits value_changed(float) with the bias in the range -0.5..1.5.
    Each slider type (TW / EA) has its own color scheme so they are
    immediately visually distinct inside the toolbar.
    """

    value_changed = QtCore.Signal(float)

    def __init__(self, parent=None, label="TW", tooltip="Tween Slider",
                 default_val=100):
        super(TweenSlider, self).__init__(parent)

        self.default_val = default_val
        theme = _SLIDER_THEMES.get(label, _SLIDER_THEMES["TW"])

        # ── outer container ──────────────────────────────────
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(2, 1, 2, 1)
        root.setSpacing(1)

        # ── top row: badge + value label ─────────────────────
        top_row = QtWidgets.QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(3)

        self.badge = QtWidgets.QLabel(theme["label"])
        self.badge.setAlignment(QtCore.Qt.AlignCenter)
        self.badge.setFixedSize(24, 14)
        self.badge.setStyleSheet(
            "background-color: {bg}; color: {fg}; border-radius: 3px;"
            "font-weight: bold; font-size: 8px; letter-spacing: 0.5px;".format(
                bg=theme["badge_bg"], fg=theme["badge_fg"]
            )
        )
        top_row.addWidget(self.badge)

        top_row.addStretch()

        self.value_label = QtWidgets.QLabel("0%")
        self.value_label.setFixedWidth(30)
        self.value_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.value_label.setStyleSheet(
            "color: {fg}; font-size: 8px; font-weight: bold;".format(fg=theme["badge_fg"])
        )
        top_row.addWidget(self.value_label)

        root.addLayout(top_row)

        # ── slider ───────────────────────────────────────────
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 200)
        self.slider.setValue(self.default_val)
        self.slider.setFixedWidth(110)
        self.slider.setFixedHeight(14)
        self.slider.setToolTip(tooltip)

        # Per-slider inline stylesheet so both can coexist on the same widget
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {{
                height: 5px;
                background: {groove};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {fill};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {handle};
                border: 1px solid {handle_bdr};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {fill};
            }}
        """.format(
            groove=theme["groove"],
            fill=theme["fill"],
            handle=theme["handle"],
            handle_bdr=theme["handle_bdr"],
        ))

        root.addWidget(self.slider)

        # Connect signals
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.slider.sliderReleased.connect(self._on_slider_released)

        # Fixed overall size so it occupies a predictable amount of toolbar space
        self.setFixedWidth(114)
        self.setFixedHeight(36)

    # ── value helpers ────────────────────────────────────────

    def _on_slider_changed(self, raw_value):
        """Map slider int (0-200) to bias float (-0.5..1.5)."""
        bias = (raw_value - 100) / 100.0   # 0→-1, 100→0, 200→+1
        percent = int(bias * 100)
        sign = "+" if percent > 0 else ""
        self.value_label.setText("{}{}%".format(sign, percent))
        self.value_changed.emit(bias)

    def _on_slider_released(self):
        """Snap slider back to centre on mouse-up."""
        self.slider.setValue(100)
        self.value_label.setText("0%")

    def get_bias(self):
        """Return the current bias value (float -1..+1)."""
        return (self.slider.value() - 100) / 100.0
