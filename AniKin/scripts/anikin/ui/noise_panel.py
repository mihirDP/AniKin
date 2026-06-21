"""
noise_panel.py
Configuration panel for AniNoise micro-jitter generator.
Provides preset dropdowns, custom parameter controls, and channel masks.
"""

import maya.cmds as cmds

from anikin.core.qt_compat import QtWidgets, QtCore, get_maya_main_window
from anikin.ui.theme import STYLESHEET
from anikin import AniNoise

PRESETS = {
    "Idle Breath": {"amp": 0.15, "freq": 0.03},
    "Camera Shake": {"amp": 0.5, "freq": 0.08},
    "Nervous Energy": {"amp": 0.4, "freq": 0.12},
    "Drunk/Dizzy": {"amp": 0.9, "freq": 0.02},
    "Machine Vibration": {"amp": 0.2, "freq": 0.4},
    "Custom": {"amp": 0.3, "freq": 0.05}
}


class NoisePanel(QtWidgets.QDialog):
    """AniNoise Panel Options."""

    def __init__(self, parent=None):
        super(NoisePanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin — AniNoise Presets")
        self.setObjectName("AniKinNoisePanel")
        self.setMinimumSize(300, 320)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self._on_preset_changed("Idle Breath") # Default

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # —— Presets Dropdown ———————————————————————————————
        preset_layout = QtWidgets.QHBoxLayout()
        preset_layout.addWidget(QtWidgets.QLabel("Preset:"))
        self.preset_combo = QtWidgets.QComboBox()
        for p in PRESETS.keys():
            self.preset_combo.addItem(p)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)

        # —— Sliders Group —————————————————————————————————
        form = QtWidgets.QFormLayout()
        form.setSpacing(8)

        # Amplitude
        self.amp_spin = QtWidgets.QDoubleSpinBox()
        self.amp_spin.setRange(0.01, 5.0)
        self.amp_spin.setSingleStep(0.05)
        self.amp_spin.setValue(0.15)
        self.amp_spin.setToolTip("Size of the jitter/sway in units or degrees.")
        self.amp_spin.valueChanged.connect(self._on_slider_manual)
        form.addRow("Amplitude:", self.amp_spin)

        # Frequency
        self.freq_spin = QtWidgets.QDoubleSpinBox()
        self.freq_spin.setRange(0.005, 1.0)
        self.freq_spin.setSingleStep(0.01)
        self.freq_spin.setValue(0.03)
        self.freq_spin.setToolTip("Speed/frequency of the noise waves.")
        self.freq_spin.valueChanged.connect(self._on_slider_manual)
        form.addRow("Frequency:", self.freq_spin)

        # Seed
        self.seed_input = QtWidgets.QLineEdit()
        self.seed_input.setPlaceholderText("Random (leave empty)")
        self.seed_input.setToolTip("Pin a seed (integer) to generate reproducible noise.")
        form.addRow("Seed:", self.seed_input)

        layout.addLayout(form)

        # —— Channel Mask ——————————————————————————————————
        mask_group = QtWidgets.QGroupBox("Channel Mask")
        mask_layout = QtWidgets.QHBoxLayout(mask_group)
        self.tx_chk = QtWidgets.QCheckBox("Translate")
        self.rx_chk = QtWidgets.QCheckBox("Rotate")
        self.sx_chk = QtWidgets.QCheckBox("Scale")
        
        self.tx_chk.setChecked(True)
        self.rx_chk.setChecked(True)
        self.sx_chk.setChecked(False)

        mask_layout.addWidget(self.tx_chk)
        mask_layout.addWidget(self.rx_chk)
        mask_layout.addWidget(self.sx_chk)
        layout.addWidget(mask_group)

        # —— Action Button —————————————————————————————————
        apply_btn = QtWidgets.QPushButton("Apply Noise")
        apply_btn.setProperty("accent", True)
        apply_btn.clicked.connect(self._apply_noise)
        layout.addWidget(apply_btn)

    def _on_preset_changed(self, text):
        """Sync sliders with selected preset values."""
        if text == "Custom":
            return
        
        vals = PRESETS[text]
        self.amp_spin.blockSignals(True)
        self.freq_spin.blockSignals(True)
        
        self.amp_spin.setValue(vals["amp"])
        self.freq_spin.setValue(vals["freq"])
        
        self.amp_spin.blockSignals(False)
        self.freq_spin.blockSignals(False)

    def _on_slider_manual(self):
        """Set preset to 'Custom' if user modifies sliders manually."""
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentText("Custom")
        self.preset_combo.blockSignals(False)

    def _apply_noise(self):
        amp = self.amp_spin.value()
        freq = self.freq_spin.value()
        
        # Parse seed
        seed_str = self.seed_input.text().strip()
        seed = None
        if seed_str:
            try:
                seed = int(seed_str)
            except ValueError:
                seed = hash(seed_str)

        # Read channel mask
        mask = []
        if self.tx_chk.isChecked():
            mask.append("translate")
        if self.rx_chk.isChecked():
            mask.append("rotate")
        if self.sx_chk.isChecked():
            mask.append("scale")

        if not mask:
            cmds.warning("AniNoise: Select at least one channel type in the mask.")
            return

        AniNoise.apply_noise(amplitude=amp, frequency=freq, seed=seed, channels_mask=mask)


# —— Global instance —————————————————————————————————————
_PANEL_INSTANCE = None


def show_panel():
    """Show the AniNoise Options panel."""
    global _PANEL_INSTANCE
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.close()
        except Exception:
            pass
    _PANEL_INSTANCE = NoisePanel()
    _PANEL_INSTANCE.show()
