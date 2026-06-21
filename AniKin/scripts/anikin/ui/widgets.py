"""
widgets.py
Reusable UI widgets for AniKin.

Small, focused widget classes used across the toolbar and panels.
"""

import os
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui


class SectionSeparator(QtWidgets.QFrame):
    """A vertical line separator between toolbar sections."""

    def __init__(self, parent=None):
        super(SectionSeparator, self).__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setFixedWidth(2)


class ToolButton(QtWidgets.QPushButton):
    """
    An icon-first toolbar button.

    In v0.2.0, the label directly corresponds to the SVG filename in the
    icons/ directory (e.g., label="align_all" loads "align_all.svg").
    If no icon is found, the label text is shown as a fallback.

    Args:
        label: Icon filename stem (e.g., "align_all") or display text fallback.
        tooltip: Tooltip shown on hover.
        callback: Function called on click.
        accent: If True, uses accent styling.
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
            self.setIconSize(QtCore.QSize(20, 20))
            self.setText("")  # Hide text â€” icon only
            self.setFixedSize(30, 30)
        else:
            # Fallback: display the label text
            self.setText(label)
            self.setMinimumWidth(28)

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


class TweenSlider(QtWidgets.QWidget):
    """
    A combined slider + value display for the Tween tool.
    Emits value_changed(float) with the bias in range -0.5 to 1.5.
    """

    value_changed = QtCore.Signal(float)

    def __init__(self, parent=None):
        super(TweenSlider, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Tween icon (instead of text label)
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        tween_icon_path = os.path.join(icons_dir, "AniTween.svg")
        if os.path.exists(tween_icon_path):
            icon_label = QtWidgets.QLabel()
            icon_label.setPixmap(QtGui.QIcon(tween_icon_path).pixmap(QtCore.QSize(18, 18)))
            icon_label.setFixedSize(22, 22)
            icon_label.setAlignment(QtCore.Qt.AlignCenter)
            icon_label.setToolTip("Tween Slider")
            layout.addWidget(icon_label)
        else:
            self.label = QtWidgets.QLabel("Tween")
            self.label.setProperty("header", True)
            layout.addWidget(self.label)

        # The slider: internal range 0-200 â†’ mapped to -0.5 to 1.5
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 200)
        self.slider.setValue(100)  # 0.5 = midpoint
        self.slider.setFixedWidth(140)
        self.slider.setToolTip(
            "Tween Slider\n"
            "0% = Previous key | 100% = Next key\n"
            "Beyond range for overshoot"
        )
        layout.addWidget(self.slider)

        # Value display
        self.value_label = QtWidgets.QLabel("50%")
        self.value_label.setFixedWidth(32)
        self.value_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.value_label)

        # Connect
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.slider.sliderReleased.connect(self._on_slider_released)

    def _on_slider_changed(self, raw_value):
        """Map slider int (0-200) to bias float (-0.5 to 1.5)."""
        bias = (raw_value - 50) / 100.0  # 0â†’-0.5, 100â†’0.5, 200â†’1.5
        percent = int(bias * 100)
        self.value_label.setText("{}%".format(percent))
        self.value_changed.emit(bias)

    def _on_slider_released(self):
        """Reset slider to center when released."""
        self.slider.setValue(100)
        self.value_label.setText("50%")

    def get_bias(self):
        """Return the current bias value."""
        raw = self.slider.value()
        return (raw - 50) / 100.0

