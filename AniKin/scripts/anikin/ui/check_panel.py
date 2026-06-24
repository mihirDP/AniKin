"""
check_panel.py
UI Panel for AniCheck Diagnostics.
Scans and displays curve health issues in a table with inline auto-fix tools.
"""

import os
import maya.cmds as cmds
import maya.mel as mel

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui, get_maya_main_window
from anikin.ui.theme import STYLESHEET
from anikin import AniCheck


class CheckPanel(QtWidgets.QDialog):
    """AniCheck Diagnostics UI panel."""

    def __init__(self, parent=None):
        super(CheckPanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin — AniCheck Diagnostics")
        self.setObjectName("AniKinCheckPanel")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(STYLESHEET)
        
        self.issues = []
        self._build_ui()
        self._run_scan()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # —— Scope & Filter Area ————————————————————————————
        top_settings = QtWidgets.QHBoxLayout()
        
        # Scope Selector
        scope_group = QtWidgets.QGroupBox("Scope")
        scope_layout = QtWidgets.QHBoxLayout(scope_group)
        self.scope_sel_radio = QtWidgets.QRadioButton("Selected Objects")
        self.scope_scene_radio = QtWidgets.QRadioButton("All Scene Objects")
        self.scope_sel_radio.setChecked(True)
        scope_layout.addWidget(self.scope_sel_radio)
        scope_layout.addWidget(self.scope_scene_radio)
        top_settings.addWidget(scope_group)
        
        # Checkbox Filters
        filter_group = QtWidgets.QGroupBox("Filters")
        filter_layout = QtWidgets.QGridLayout(filter_group)
        
        self.chk_gimbal = QtWidgets.QCheckBox("Gimbal Flips")
        self.chk_subframe = QtWidgets.QCheckBox("Subframe Keys")
        self.chk_duplicate = QtWidgets.QCheckBox("Duplicate Keys")
        self.chk_infinity = QtWidgets.QCheckBox("Infinity Settings")
        self.chk_zerolen = QtWidgets.QCheckBox("Zero-length Keys")
        self.chk_footslide = QtWidgets.QCheckBox("Foot Slide")
        self.chk_density = QtWidgets.QCheckBox("Key Density")

        self.chk_gimbal.setChecked(True)
        self.chk_subframe.setChecked(True)
        self.chk_duplicate.setChecked(True)
        self.chk_infinity.setChecked(True)
        self.chk_zerolen.setChecked(True)
        self.chk_footslide.setChecked(True)
        self.chk_density.setChecked(True)

        filter_layout.addWidget(self.chk_gimbal, 0, 0)
        filter_layout.addWidget(self.chk_subframe, 0, 1)
        filter_layout.addWidget(self.chk_duplicate, 0, 2)
        filter_layout.addWidget(self.chk_infinity, 1, 0)
        filter_layout.addWidget(self.chk_zerolen, 1, 1)
        filter_layout.addWidget(self.chk_footslide, 1, 2)
        filter_layout.addWidget(self.chk_density, 2, 0)

        top_settings.addWidget(filter_group)
        layout.addLayout(top_settings)

        # —— Clean Banner ——————————————————————————————————
        self.clean_banner = QtWidgets.QFrame()
        self.clean_banner.setStyleSheet("background-color: #064e3b; border: 1px solid #059669; border-radius: 4px;")
        self.clean_banner.setFixedHeight(36)
        banner_layout = QtWidgets.QHBoxLayout(self.clean_banner)
        banner_layout.setContentsMargins(10, 0, 10, 0)
        
        clean_lbl = QtWidgets.QLabel("✨ Clean! All curves in scope are perfectly healthy.")
        clean_lbl.setStyleSheet("color: #34d399; font-weight: bold; font-size: 12px;")
        banner_layout.addWidget(clean_lbl)
        self.clean_banner.hide()
        layout.addWidget(self.clean_banner)

        # —— Action Row —————————————————————————————————
        top_row = QtWidgets.QHBoxLayout()
        scan_btn = QtWidgets.QPushButton("Run Diagnostics Scan")
        scan_btn.setToolTip("Scan active scope for curve issues")
        scan_btn.setProperty("accent", True)
        scan_btn.clicked.connect(self._run_scan)
        top_row.addWidget(scan_btn)

        fix_all_btn = QtWidgets.QPushButton("Fix Selected Issues")
        fix_all_btn.setToolTip("Batch fix all ticked issues currently in the list")
        fix_all_btn.clicked.connect(self._fix_selected_batch)
        top_row.addWidget(fix_all_btn)

        layout.addLayout(top_row)

        # —— Issues Table ——————————————————————————————————
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Object", "Channel", "Frame", "Issue Type", "Severity", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.itemClicked.connect(self._on_row_clicked)
        layout.addWidget(self.table)

        # —— Bottom row ———————————————————————————————————
        bottom_row = QtWidgets.QHBoxLayout()
        self.status_lbl = QtWidgets.QLabel("")
        self.status_lbl.setStyleSheet("color: #9ca3af; font-size: 11px;")
        bottom_row.addWidget(self.status_lbl)
        
        bottom_row.addStretch()
        
        export_btn = QtWidgets.QPushButton("Export Report...")
        export_btn.clicked.connect(self._export_report)
        bottom_row.addWidget(export_btn)
        
        layout.addLayout(bottom_row)

    def _run_scan(self):
        """Scan curves and populate table according to scope and filters."""
        scope = "selected" if self.scope_sel_radio.isChecked() else "all"
        raw_issues = AniCheck.run_diagnostics(scope=scope)

        # Filter issues based on UI checkboxes
        self.issues = []
        for issue in raw_issues:
            if issue.category == "Gimbal" and not self.chk_gimbal.isChecked():
                continue
            if issue.category == "Subframe" and not self.chk_subframe.isChecked():
                continue
            if issue.category == "Duplicate" and not self.chk_duplicate.isChecked():
                continue
            if issue.category == "Infinity" and not self.chk_infinity.isChecked():
                continue
            if issue.category == "ZeroLength" and not self.chk_zerolen.isChecked():
                continue
            if issue.category == "FootSlide" and not self.chk_footslide.isChecked():
                continue
            if issue.category == "Density" and not self.chk_density.isChecked():
                continue
            self.issues.append(issue)

        self.table.setRowCount(len(self.issues))

        if not self.issues:
            self.clean_banner.show()
            self.table.hide()
            self.status_lbl.setText("Scan complete: 0 issues found.")
            return
            
        self.clean_banner.hide()
        self.table.show()

        errors = 0
        warnings = 0

        for row, issue in enumerate(self.issues):
            plug_parts = issue.plug.split(".")
            node = plug_parts[0]
            attr = ".".join(plug_parts[1:])

            # Object
            obj_item = QtWidgets.QTableWidgetItem(node)
            obj_item.setFlags(obj_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 0, obj_item)

            # Channel
            chan_item = QtWidgets.QTableWidgetItem(attr)
            chan_item.setFlags(chan_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 1, chan_item)

            # Frame
            frame_str = "{:.2f}".format(issue.time) if issue.time is not None else "All"
            frame_item = QtWidgets.QTableWidgetItem(frame_str)
            frame_item.setFlags(frame_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 2, frame_item)

            # Issue Type
            type_item = QtWidgets.QTableWidgetItem(issue.description)
            type_item.setFlags(type_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 3, type_item)

            # Severity
            sev_item = QtWidgets.QTableWidgetItem(issue.severity)
            if issue.severity == "Critical":
                sev_item.setForeground(QtGui.QColor("#ef4444"))
                errors += 1
            elif issue.severity == "High":
                sev_item.setForeground(QtGui.QColor("#f97316"))
                errors += 1
            elif issue.severity == "Medium":
                sev_item.setForeground(QtGui.QColor("#eab308"))
                warnings += 1
            else:
                sev_item.setForeground(QtGui.QColor("#3b82f6"))
                warnings += 1
            sev_item.setFlags(sev_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 4, sev_item)

            # Actions Cell (Widget layout with Select and Fix buttons)
            cell_widget = QtWidgets.QWidget()
            cell_layout = QtWidgets.QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(2, 2, 2, 2)
            cell_layout.setSpacing(4)

            select_btn = QtWidgets.QPushButton("Select")
            select_btn.setFixedSize(50, 20)
            select_btn.clicked.connect(lambda _, r=row: self._select_curve(r))
            cell_layout.addWidget(select_btn)

            fix_btn = QtWidgets.QPushButton("Fix")
            fix_btn.setFixedSize(40, 20)
            fix_btn.setProperty("accent", True)
            fix_btn.clicked.connect(lambda _, r=row: self._fix_single(r))
            cell_layout.addWidget(fix_btn)

            self.table.setCellWidget(row, 5, cell_widget)

        self.status_lbl.setText("Found {} Errors/Criticals, {} Warnings/Lows.".format(errors, warnings))

    def _on_row_clicked(self, item):
        """Jump playhead to the frame where the issue occurs."""
        row = item.row()
        if row < len(self.issues):
            issue = self.issues[row]
            if issue.time is not None:
                cmds.currentTime(issue.time)

    def _select_curve(self, row):
        """Select the object and open the curve in Graph Editor."""
        if row < len(self.issues):
            issue = self.issues[row]
            plug_parts = issue.plug.split(".")
            node = plug_parts[0]
            
            # Select object in Maya
            cmds.select(node, replace=True)
            
            # Open Graph Editor and focus
            try:
                mel.eval("GraphEditor;")
            except Exception:
                pass

    def _fix_single(self, row):
        """Fix a single issue and re-scan."""
        if row < len(self.issues):
            issue = self.issues[row]
            if issue.fix():
                self._run_scan()

    def _fix_selected_batch(self):
        """Batch fix all issues currently shown in the table."""
        fixed = 0
        # Iterate in reverse to avoid index shifts during key deletion
        for issue in reversed(self.issues):
            if issue.fix():
                fixed += 1
                
        self._run_scan()
        cmds.inViewMessage(
            amg="<hl>AniKin</hl>: Auto-fixed {} curve issues".format(fixed),
            pos="topCenter", fade=True, fadeStayTime=1500
        )

    def _export_report(self):
        """Saves diagnostics issues as a text report."""
        if not self.issues:
            cmds.warning("AniCheck: No issues to export.")
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Diagnostics Report", os.path.expanduser("~"), "Text Files (*.txt);;CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w") as f:
                if path.endswith(".csv"):
                    f.write("Object,Channel,Frame,Issue Type,Severity\n")
                    for issue in self.issues:
                        plug_parts = issue.plug.split(".")
                        node = plug_parts[0]
                        attr = ".".join(plug_parts[1:])
                        f.write("{},{},{},{},{}\n".format(
                            node, attr, issue.time or "All", issue.description, issue.severity
                        ))
                else:
                    f.write("=== ANIKIN DIAGNOSTICS REPORT ===\n")
                    f.write("Scope: {}\n".format("Selected" if self.scope_sel_radio.isChecked() else "Scene"))
                    f.write("Issues found: {}\n\n".format(len(self.issues)))
                    for issue in self.issues:
                        f.write("[{}] Object: {} | Channel: {} | Frame: {} | {}\n".format(
                            issue.severity, issue.plug.split(".")[0], ".".join(issue.plug.split(".")[1:]),
                            issue.time or "All", issue.description
                        ))
            cmds.inViewMessage(amg="<hl>AniKin</hl>: Diagnostics report exported.", pos="topCenter", fade=True, fadeStayTime=1500)
        except Exception as e:
            cmds.warning("AniCheck: Export report failed: {}".format(e))


# —— Global instance —————————————————————————————————————
_PANEL_INSTANCE = None


def show_panel():
    """Show the AniCheck Diagnostics panel."""
    global _PANEL_INSTANCE
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.close()
        except Exception:
            pass
    _PANEL_INSTANCE = CheckPanel()
    _PANEL_INSTANCE.show()
