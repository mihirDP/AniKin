"""
widgets.py
Reusable UI widgets for AniKin.

Small, focused widget classes used across the toolbar and panels.
"""

import os
import re
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui
from anikin.ui.theme import get_theme_colors

def _load_colored_svg(icon_path, target_color):
    """Loads an SVG file, string-replaces its colors, and returns a QIcon."""
    if not os.path.exists(icon_path):
        return QtGui.QIcon()
        
    with open(icon_path, "r", encoding="utf-8") as f:
        svg_data = f.read()
        
    # Replace any stroke or fill color with the target color
    svg_data = re.sub(r'stroke\s*=\s*["\'](currentColor|#[0-9a-fA-F]{3,6}|white|black)["\']', f'stroke="{target_color}"', svg_data, flags=re.IGNORECASE)
    svg_data = re.sub(r'fill\s*=\s*["\'](currentColor|#[0-9a-fA-F]{3,6}|white|black)["\']', f'fill="{target_color}"', svg_data, flags=re.IGNORECASE)
    svg_data = re.sub(r'stroke\s*:\s*(currentColor|#[0-9a-fA-F]{3,6}|white|black)\s*;?', f'stroke: {target_color};', svg_data, flags=re.IGNORECASE)
    svg_data = re.sub(r'fill\s*:\s*(currentColor|#[0-9a-fA-F]{3,6}|white|black)\s*;?', f'fill: {target_color};', svg_data, flags=re.IGNORECASE)

    svg_bytes = QtCore.QByteArray(svg_data.encode('utf-8'))
    pixmap = QtGui.QPixmap()
    pixmap.loadFromData(svg_bytes, "SVG")
    
    return QtGui.QIcon(pixmap)


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
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setFixedWidth(1)
        self.setFixedHeight(28)
        
        from anikin.ui.theme import get_theme_colors
        colors = get_theme_colors()
        self.setStyleSheet("background-color: {}; border: none;".format(colors["separator"]))


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
                 danger=False, size=36, parent=None):
        super(ToolButton, self).__init__(parent)

        if tooltip:
            self.setToolTip(tooltip)
        if callback:
            self.clicked.connect(callback)
        if accent:
            self.setProperty("accent", True)
        if danger:
            self.setProperty("danger", True)

        self._btn_size = size
        self.setMinimumSize(size, size)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        colors = get_theme_colors()
        if danger:
            icon_color = colors["danger"]
        elif accent:
            icon_color = colors["accent"]
        else:
            icon_color = colors["text"]

        # Try to load icon by label name directly
        icon_found = False
        icon_path = os.path.join(self._ICONS_DIR, label + ".svg")
        if os.path.exists(icon_path):
            self.setIcon(_load_colored_svg(icon_path, icon_color))
            icon_found = True
        else:
            # Fallback to PNG without recoloring
            png_path = os.path.join(self._ICONS_DIR, label + ".png")
            if os.path.exists(png_path):
                self.setIcon(QtGui.QIcon(png_path))
                icon_found = True

        icon_render_size = max(size - 12, 16)
        if icon_found:
            self.setIconSize(QtCore.QSize(icon_render_size, icon_render_size))
            self.setText("")
        else:
            self.setText(label)

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
    """

    _ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")

    def __init__(self, icon_a, icon_b, tooltip_a, tooltip_b, callback,
                 accent_a=False, accent_b=False, size=36, parent=None):
        super(ToggleToolButton, self).__init__(icon_a, tooltip_a, None, accent_a, size=size, parent=parent)
        self.setCheckable(True)
        self.setChecked(False)
        self._toggled = False

        self._icon_a_name = icon_a
        self._icon_b_name = icon_b
        self._tooltip_a = tooltip_a
        self._tooltip_b = tooltip_b
        self._user_callback = callback
        self._accent_a = accent_a
        self._accent_b = accent_b
        self.clicked.connect(self._on_clicked)
        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _apply_state(self):
        colors = get_theme_colors()
        if self._toggled:
            self.setToolTip(self._tooltip_b)
            self.setProperty("accent", self._accent_b)
            icon_color = colors["accent"] if self._accent_b else colors["text"]
            icon_path = os.path.join(self._ICONS_DIR, self._icon_b_name + ".svg")
        else:
            self.setToolTip(self._tooltip_a)
            self.setProperty("accent", self._accent_a)
            icon_color = colors["accent"] if self._accent_a else colors["text"]
            icon_path = os.path.join(self._ICONS_DIR, self._icon_a_name + ".svg")
            
        if os.path.exists(icon_path):
            self.setIcon(_load_colored_svg(icon_path, icon_color))
        else:
            # PNG fallback (no color replace)
            png_path = icon_path.replace(".svg", ".png")
            if os.path.exists(png_path):
                self.setIcon(QtGui.QIcon(png_path))

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
        "label":       "TW",
        "fill":        "#d4860a",  # Defaults, overridden by current theme
    },
    "EA": {
        "label":       "EA",
        "fill":        "#8855cc",
    },
}

class TweenSlider(QtWidgets.QSlider):
    """
    A custom-painted slider for tweening that matches the 'pill on a dotted track'
    design from the updated specs.
    """
    value_changed = QtCore.Signal(float)

    def __init__(self, label="TW", tooltip=""):
        super(TweenSlider, self).__init__(QtCore.Qt.Horizontal)
        self.setRange(0, 200)
        self.setValue(100)
        self.setFixedWidth(130)
        self.setFixedHeight(24)
        if tooltip:
            self.setToolTip(tooltip)
            
        self._label = label
        self.theme_def = _SLIDER_THEMES.get(label, _SLIDER_THEMES["TW"])
        
        self.valueChanged.connect(self._on_slider_changed)
        self.sliderReleased.connect(self._on_slider_released)

    def _on_slider_changed(self, raw_value):
        bias = (raw_value - 100) / 100.0
        self.value_changed.emit(bias)

    def _on_slider_released(self):
        # Snap back to center
        self.setValue(100)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        colors = get_theme_colors()
        
        # Use theme accent if it's TW, otherwise keep EA purple
        slider_color = colors["accent"] if self._label == "TW" else self.theme_def["fill"]
        
        rect = self.rect()
        
        # 1. Draw the track (dark, slightly rounded)
        groove_rect = QtCore.QRect(rect.left(), rect.center().y() - 3, rect.width(), 6)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(colors["bg_elevated"]))
        painter.drawRoundedRect(groove_rect, 3, 3)
        
        # 2. Draw the ticks (tiny squares of accent color)
        painter.setBrush(QtGui.QColor(slider_color))
        ticks = 8
        spacing = rect.width() / float(ticks)
        for i in range(ticks + 1):
            x = rect.left() + (i * spacing)
            if i == 0: x += 3
            elif i == ticks: x -= 5
            else: x -= 1
            painter.drawRect(QtCore.QRect(int(x), rect.center().y() - 1, 2, 2))
            
        # 3. Draw the Handle (a Pill with text inside)
        val_range = self.maximum() - self.minimum()
        val_percent = (self.value() - self.minimum()) / float(val_range) if val_range > 0 else 0
        
        handle_w = 26
        handle_h = 18
        handle_x = int(rect.left() + val_percent * (rect.width() - handle_w))
        handle_y = rect.center().y() - (handle_h // 2)
        
        draw_rect = QtCore.QRect(handle_x, handle_y, handle_w, handle_h)
        
        # Inner background of the handle
        painter.setBrush(QtGui.QColor(colors["bg_surface"]))
        # Border of the handle
        painter.setPen(QtGui.QPen(QtGui.QColor(colors["border_light"]), 1))
        painter.drawRoundedRect(draw_rect, 4, 4)
        
        # Text inside handle
        painter.setPen(QtGui.QColor(slider_color))
        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(draw_rect, QtCore.Qt.AlignCenter, self._label)
