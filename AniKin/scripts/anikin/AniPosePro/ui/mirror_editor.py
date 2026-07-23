"""
mirror_editor.py — MirrorTable Editor Dialog for AniPose Pro V3.1.
"""

import os
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui
from anikin.AniPosePro.core.mirror_table import MirrorTable


class MirrorTableEditorDialog(QtWidgets.QDialog):
    """
    Dialog for viewing, auto-detecting, editing, and saving Mirror Tables.
    """

    def __init__(self, mirror_table: MirrorTable = None, parent=None):
        super(MirrorTableEditorDialog, self).__init__(parent)
        self.setWindowTitle("MirrorTable Editor — AniPose Pro")
        self.resize(600, 400)
        self.mirror_table = mirror_table or MirrorTable()

        self._build_ui()
        self._populate_table()

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(10)

        # Header toolbar
        tb = QtWidgets.QHBoxLayout()
        auto_btn = QtWidgets.QPushButton("Auto-Detect L/R Pairs")
        auto_btn.clicked.connect(self._on_auto_detect)
        add_btn = QtWidgets.QPushButton("Add Manual Pair")
        add_btn.clicked.connect(self._on_add_pair)

        tb.addWidget(auto_btn)
        tb.addWidget(add_btn)
        tb.addStretch()
        lay.addLayout(tb)

        # Main Table
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Left Control", "Right Control", "Axis"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        lay.addWidget(self.table)

        # Buttons
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self._on_save)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _populate_table(self):
        self.table.setRowCount(0)
        for pair in self.mirror_table.pairs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            l_item = QtWidgets.QTableWidgetItem(pair.get("left", ""))
            r_item = QtWidgets.QTableWidgetItem(pair.get("right", ""))
            axis_combo = QtWidgets.QComboBox()
            axis_combo.addItems(["X", "Y", "Z"])
            axis_combo.setCurrentText(pair.get("mirror_axis", "X"))

            self.table.setItem(row, 0, l_item)
            self.table.setItem(row, 1, r_item)
            self.table.setCellWidget(row, 2, axis_combo)

    def _on_auto_detect(self):
        count = self.mirror_table.auto_detect()
        self._populate_table()

    def _on_add_pair(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QtWidgets.QTableWidgetItem("L_control"))
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem("R_control"))
        axis_combo = QtWidgets.QComboBox()
        axis_combo.addItems(["X", "Y", "Z"])
        self.table.setCellWidget(row, 2, axis_combo)

    def _on_save(self):
        pairs = []
        for r in range(self.table.rowCount()):
            left = self.table.item(r, 0).text().strip()
            right = self.table.item(r, 1).text().strip()
            cb = self.table.cellWidget(r, 2)
            axis = cb.currentText() if cb else "X"

            if left and right:
                pairs.append({
                    "left": left,
                    "right": right,
                    "mirror_axis": axis,
                    "invert_rotate": ["rotateY", "rotateZ"],
                    "invert_translate": ["translateX"]
                })

        self.mirror_table.pairs = pairs

        if not self.mirror_table.filepath:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Mirror Table", "", "Mirror Table (*.mirror)")
            if not path:
                return
            self.mirror_table.filepath = path

        self.mirror_table.save(self.mirror_table.filepath)
        self.accept()
