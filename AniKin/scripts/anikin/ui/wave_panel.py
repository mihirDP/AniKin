"""
wave_panel.py
Configuration panel for AniWave overlap propagator.
Includes dry-run live preview information panel.
"""

import maya.cmds as cmds

from anikin.core.qt_compat import QtWidgets, QtCore, get_maya_main_window
from anikin.ui.theme import STYLESHEET
from anikin import AniWave
from anikin.core.log import log_debug


class WavePanel(QtWidgets.QDialog):
    """AniWave Advanced Options Panel."""

    def __init__(self, parent=None):
        super(WavePanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin — AniWave Options")
        self.setObjectName("AniKinWavePanel")
        self.setMinimumSize(320, 380)
        self.setStyleSheet(STYLESHEET)
        
        self._build_ui()
        self._update_preview()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # —— Settings Group —————————————————————————————————
        form = QtWidgets.QFormLayout()
        form.setSpacing(8)

        # Frame Offset
        self.offset_spin = QtWidgets.QDoubleSpinBox()
        self.offset_spin.setRange(-20.0, 20.0)
        self.offset_spin.setSingleStep(0.5)
        self.offset_spin.setValue(2.0)
        self.offset_spin.setToolTip("Number of frames delay between successive joints.")
        self.offset_spin.valueChanged.connect(self._update_preview)
        form.addRow("Frame Delay:", self.offset_spin)

        # Amplitude Falloff
        self.decay_spin = QtWidgets.QDoubleSpinBox()
        self.decay_spin.setRange(0.1, 2.0)
        self.decay_spin.setSingleStep(0.05)
        self.decay_spin.setValue(0.8)
        self.decay_spin.setToolTip("Scale factor for keys on each successive joint (0.8 = 80%).")
        self.decay_spin.valueChanged.connect(self._update_preview)
        form.addRow("Decay Factor:", self.decay_spin)

        layout.addLayout(form)

        # —— Channel Mask ——————————————————————————————————
        mask_group = QtWidgets.QGroupBox("Channel Mask")
        mask_layout = QtWidgets.QHBoxLayout(mask_group)
        self.tx_chk = QtWidgets.QCheckBox("Translate")
        self.rx_chk = QtWidgets.QCheckBox("Rotate")
        self.sx_chk = QtWidgets.QCheckBox("Scale")
        
        self.tx_chk.setChecked(False)
        self.rx_chk.setChecked(True)
        self.sx_chk.setChecked(False)

        self.tx_chk.toggled.connect(self._update_preview)
        self.rx_chk.toggled.connect(self._update_preview)
        self.sx_chk.toggled.connect(self._update_preview)

        mask_layout.addWidget(self.tx_chk)
        mask_layout.addWidget(self.rx_chk)
        mask_layout.addWidget(self.sx_chk)
        layout.addWidget(mask_group)

        # —— Other Options —————————————————————————————————
        opt_group = QtWidgets.QGroupBox("Options")
        opt_layout = QtWidgets.QVBoxLayout(opt_group)
        
        self.damping_chk = QtWidgets.QCheckBox("Tip Damping (extra decay on last 2 joints)")
        self.damping_chk.setChecked(False)
        self.damping_chk.toggled.connect(self._update_preview)
        opt_layout.addWidget(self.damping_chk)

        self.reverse_chk = QtWidgets.QCheckBox("Reverse Mode (propagate tip → root)")
        self.reverse_chk.setChecked(False)
        self.reverse_chk.toggled.connect(self._update_preview)
        opt_layout.addWidget(self.reverse_chk)

        layout.addWidget(opt_group)

        # —— Dry-Run Preview Panel ——————————————————————————
        self.preview_group = QtWidgets.QGroupBox("Dry-Run Live Preview")
        preview_layout = QtWidgets.QVBoxLayout(self.preview_group)
        self.preview_text = QtWidgets.QLabel("Select joints to preview wave propagation.")
        self.preview_text.setWordWrap(True)
        self.preview_text.setStyleSheet("color: #9ca3af; font-size: 11px; line-height: 1.2;")
        preview_layout.addWidget(self.preview_text)
        layout.addWidget(self.preview_group)

        # —— Action Button —————————————————————————————————
        apply_btn = QtWidgets.QPushButton("Propagate Wave")
        apply_btn.setProperty("accent", True)
        apply_btn.clicked.connect(self._apply_wave)
        layout.addWidget(apply_btn)

    def _update_preview(self):
        """Calculate and display dry-run results based on parameters and current Maya selection."""
        sel = cmds.ls(selection=True) or []
        count = len(sel)

        if count < 2:
            self.preview_text.setText("⚠️ Needs at least 2 selected joints (current: {} selected).".format(count))
            return

        offset = self.offset_spin.value()
        decay = self.decay_spin.value()
        damping = self.damping_chk.isChecked()
        reverse = self.reverse_chk.isChecked()

        # Calculation simulation
        steps = count - 1
        final_offset = steps * offset
        final_scale = decay ** steps
        if damping and steps >= 2:
            final_scale *= 0.5

        source = sel[-1] if reverse else sel[0]
        end_joint = sel[0] if reverse else sel[-1]

        text = (
            "<b>Chain Source:</b> {}<br>"
            "<b>Chain End:</b> {}<br>"
            "<b>Stagger Steps:</b> {} joints<br>"
            "<b>Final Joint Delay:</b> {:.1f} frames<br>"
            "<b>Final Joint Scale:</b> {:.1%}"
        ).format(source, end_joint, steps, final_offset, final_scale)
        
        self.preview_text.setText(text)

    def _apply_wave(self):
        """Invoke core propagate_wave with current parameters."""
        offset = self.offset_spin.value()
        decay = self.decay_spin.value()
        
        mask = []
        if self.tx_chk.isChecked():
            mask.append("translate")
        if self.rx_chk.isChecked():
            mask.append("rotate")
        if self.sx_chk.isChecked():
            mask.append("scale")

        if not mask:
            cmds.warning("AniWave: Select at least one channel mask option.")
            return

        damping = self.damping_chk.isChecked()
        reverse = self.reverse_chk.isChecked()

        log_debug("AniWave: Propagating wave (offset: {}, decay: {}, mask: {}, damping: {}, reverse: {})".format(
            offset, decay, mask, damping, reverse
        ))

        AniWave.propagate_wave(
            offset_frames=offset,
            amplitude_falloff=decay,
            channels_mask=mask,
            tip_damping=damping,
            reverse_mode=reverse
        )
        self._update_preview()


# —— Global instance —————————————————————————————————————
_PANEL_INSTANCE = None


def show_panel():
    """Show the AniWave Options panel."""
    global _PANEL_INSTANCE
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.close()
        except Exception:
            pass
    _PANEL_INSTANCE = WavePanel()
    _PANEL_INSTANCE.show()
