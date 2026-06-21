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


class SectionLabel(QtWidgets.QLabel):
    """A tiny uppercase header label for toolbar sections."""

    def __init__(self, text, parent=None):
        super(SectionLabel, self).__init__(text.upper(), parent)
        self.setProperty("header", True)
        self.setAlignment(QtCore.Qt.AlignCenter)


class ToolButton(QtWidgets.QPushButton):
    """
    A toolbar button with tooltip.

    Args:
        label: Button text.
        tooltip: Tooltip shown on hover.
        callback: Function called on click.
        accent: If True, uses accent styling.
    """

    def __init__(self, label, tooltip="", callback=None, accent=False,
                 parent=None):
        super(ToolButton, self).__init__(label, parent)
        if tooltip:
            self.setToolTip(tooltip)
        if callback:
            self.clicked.connect(callback)
        if accent:
            self.setProperty("accent", True)
        
        # Try to load icon dynamically
        icon_name = label.lower().replace(" ", "_").replace("◀", "left").replace("▶", "right").replace("🔒", "lock").replace("🔓", "unlock").replace("⚙", "settings")
        icon_map = {
            "align": "align_all",
            "alignt": "align_translate",
            "alignr": "align_rotate",
            "left": "nudge_left",
            "right": "nudge_right",
            "leftleft": "nudge_left_fast",
            "rightright": "nudge_right_fast",
            "lock": "lock",
            "unlock": "unlock",
            "settings": "settings",
            "sel_sets": "selection_sets",
            "bake→loc": "bake_to_locator",
            "loc→obj": "bake_from_locator"
        }
        icon_file = icon_map.get(icon_name, icon_name)
        
        # Calculate icons dir relative to this file
        # this file is at scripts/anikin/ui/widgets.py
        # icons are at scripts/anikin/icons/
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        icon_path_png = os.path.join(icons_dir, icon_file + ".png")
        icon_path_svg = os.path.join(icons_dir, icon_file + ".svg")
        
        icon_found = False
        if os.path.exists(icon_path_svg):
            self.setIcon(QtGui.QIcon(icon_path_svg))
            icon_found = True
        elif os.path.exists(icon_path_png):
            self.setIcon(QtGui.QIcon(icon_path_png))
            icon_found = True
            
        if icon_found:
            self.setIconSize(QtCore.QSize(16, 16))
            self.setText("") # Hide text if icon exists
            
        # Compact sizing for toolbar
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

        # Label
        self.label = QtWidgets.QLabel("Tween")
        self.label.setProperty("header", True)
        layout.addWidget(self.label)

        # The slider: internal range 0-200 → mapped to -0.5 to 1.5
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
        bias = (raw_value - 50) / 100.0  # 0→-0.5, 100→0.5, 200→1.5
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
