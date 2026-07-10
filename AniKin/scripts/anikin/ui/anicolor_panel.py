"""
anicolor_panel.py
AniColor panel — 4-tab dockable window for keyframe coloring and labeling.

Tabs: Palette | Frames | Search | Export
Follows AniKin's established design system.
"""

import os
import maya.cmds as cmds
import traceback

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui, get_maya_main_window
from anikin.ui.theme import (
    STYLESHEET, BACKGROUND_MAIN, BACKGROUND_SECTION, BACKGROUND_INPUT,
    ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, BORDER,
)
from anikin.AniColor import core as ac_core
from anikin.AniColor import palette as ac_palette
from anikin.AniColor import frames as ac_frames
from anikin.AniColor import overlay as ac_overlay
from anikin.AniColor import hud as ac_hud
from anikin.AniColor import export as ac_export

# Global variable to track "Do not show again" preference for Unassign
_UNASSIGN_PROMPT_DO_NOT_SHOW = False

def _icon_path(name):
    return os.path.join(os.path.dirname(__file__), "..", "icons", name)

def _create_icon(name):
    return QtGui.QIcon(_icon_path(name))

def _color_swatch_pixmap(rgb, size=14):
    """Create a circular color swatch pixmap."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pixmap)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    qc = QtGui.QColor.fromRgbF(rgb[0], rgb[1], rgb[2])
    p.setBrush(qc)
    p.setPen(QtCore.Qt.NoPen)
    p.drawEllipse(0, 0, size, size)
    p.end()
    return pixmap


class AniColorPanel(QtWidgets.QDialog):
    """Main AniColor dockable panel with 4 tabs."""

    def __init__(self, parent=None):
        super(AniColorPanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin — AniColor")
        self.setObjectName("AniKinColorPanel")
        self.setMinimumSize(420, 560)
        self.setStyleSheet(STYLESHEET)

        # Initialise default palette if needed
        ac_core.initialize_default_palette()

        self._assign_buttons = {}  # palette_id -> (btn, is_assigned)
        self._footer_assign_btn = None
        self._selected_palette_id = None
        self._script_job = None

        self._build_ui()
        self._refresh_palette_tab()
        self._refresh_frames_tab()

        # Enable HUD and overlay
        ac_hud.enable_hud()
        ac_overlay.create_overlay()
        
        # Track time changes to update assign/unassign states
        self._script_job = cmds.scriptJob(event=["timeChanged", self._update_assign_states], protected=True)
        self._update_assign_states()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Tab widget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # ── Tab 1: Palette ────────────────────────────────
        self._palette_tab = QtWidgets.QWidget()
        self._build_palette_tab()
        self.tabs.addTab(self._palette_tab, "Palette")

        # ── Tab 2: Frames ─────────────────────────────────
        self._frames_tab = QtWidgets.QWidget()
        self._build_frames_tab()
        self.tabs.addTab(self._frames_tab, "Frames")

        # ── Tab 3: Search ─────────────────────────────────
        self._search_tab = QtWidgets.QWidget()
        self._build_search_tab()
        self.tabs.addTab(self._search_tab, "Search")

        # ── Tab 4: Export ─────────────────────────────────
        self._export_tab = QtWidgets.QWidget()
        self._build_export_tab()
        self.tabs.addTab(self._export_tab, "Export")
        
        # ── Footer ────────────────────────────────────────
        footer = QtWidgets.QHBoxLayout()
        footer.setContentsMargins(4, 8, 4, 4)
        
        info_icon = QtWidgets.QLabel()
        info_icon.setPixmap(QtGui.QPixmap(_icon_path("info.svg")).scaled(16, 16, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        footer.addWidget(info_icon)
        
        info_text = QtWidgets.QLabel("Assign the current timeline selection to the selected color slot.")
        info_text.setStyleSheet("color: {};".format(TEXT_SECONDARY))
        footer.addWidget(info_text)
        
        footer.addStretch()
        
        self._footer_assign_btn = QtWidgets.QPushButton("  Assign Selection")
        self._footer_assign_btn.setIcon(_create_icon("box_select.svg"))
        self._footer_assign_btn.setFixedHeight(30)
        self._footer_assign_btn.setProperty("accent", True)
        self._footer_assign_btn.clicked.connect(self._on_footer_assign_clicked)
        footer.addWidget(self._footer_assign_btn)
        
        layout.addLayout(footer)

    # ══════════════════════════════════════════════════════
    #  TAB 1 — PALETTE
    # ══════════════════════════════════════════════════════

    def _build_palette_tab(self):
        layout = QtWidgets.QVBoxLayout(self._palette_tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header row
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("COLOR PALETTE")
        title.setStyleSheet("color: {}; font-weight: bold; font-size: 12px;".format(ACCENT))
        header.addWidget(title)
        header.addStretch()

        add_btn = QtWidgets.QPushButton("+ Add Slot")
        add_btn.clicked.connect(self._add_palette_slot)
        add_btn.setFixedWidth(80)
        header.addWidget(add_btn)
        layout.addLayout(header)
        
        # Table Headers
        table_header = QtWidgets.QHBoxLayout()
        table_header.setContentsMargins(12, 8, 12, 8)
        table_header.setSpacing(8)
        
        lbl_color = QtWidgets.QLabel("Color")
        lbl_color.setFixedWidth(30)
        table_header.addWidget(lbl_color)
        
        lbl_label = QtWidgets.QLabel("Label")
        table_header.addWidget(lbl_label)
        table_header.addStretch()
        
        def _th(text, width):
            lbl = QtWidgets.QLabel(text)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setFixedWidth(width)
            table_header.addWidget(lbl)
            
        _th("Actions", 40)
        _th("Visible", 40)
        _th("Assign", 40)
        _th("Count", 40)
        _th("Delete", 40)
        
        layout.addLayout(table_header)

        # Scrollable palette slots
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._palette_container = QtWidgets.QWidget()
        self._palette_layout = QtWidgets.QVBoxLayout(self._palette_container)
        self._palette_layout.setContentsMargins(0, 0, 0, 0)
        self._palette_layout.setSpacing(2)
        self._palette_layout.addStretch()
        scroll.setWidget(self._palette_container)
        layout.addWidget(scroll)

    def _refresh_palette_tab(self):
        """Rebuild palette slot rows from data."""
        self._assign_buttons.clear()
        
        # Clear existing widgets (except the terminal stretch)
        while self._palette_layout.count() > 1:
            item = self._palette_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        palettes = ac_palette.get_palettes()
        if palettes and not self._selected_palette_id:
            self._selected_palette_id = palettes[0]["id"]
            
        for pal in palettes:
            row = self._create_palette_row(pal)
            self._palette_layout.insertWidget(
                self._palette_layout.count() - 1, row)
                
        self._update_assign_states()

    def _create_palette_row(self, pal):
        """Create a single palette slot row widget."""
        row = QtWidgets.QFrame()
        bg_color = BACKGROUND_SECTION
        if pal["id"] == self._selected_palette_id:
            bg_color = "#2c333a" # Slightly highlighted
            
        row.setStyleSheet(
            "QFrame {{ background: {}; border-radius: 4px; border: 1px solid {}; }}"
            .format(bg_color, BORDER))
        row.setFixedHeight(40)

        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(8)

        # Color swatch (QFrame clickable)
        swatch = QtWidgets.QPushButton()
        swatch.setFixedSize(24, 24)
        rgb = pal["color"]
        swatch.setStyleSheet(
            "background-color: rgb({},{},{}); border-radius: 6px; border: none;"
            .format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)))
        swatch.setToolTip("Click to change color")
        swatch.clicked.connect(lambda _, pid=pal["id"]: self._change_color(pid))
        h.addWidget(swatch)

        # Slot name (editable)
        name_edit = QtWidgets.QLineEdit(pal.get("name", ""))
        name_edit.setPlaceholderText("Slot name...")
        name_edit.setFixedHeight(26)
        name_edit.setStyleSheet("QLineEdit { background: #1a1a1a; border-radius: 4px; padding-left: 6px; border: none; }")
        name_edit.editingFinished.connect(
            lambda ne=name_edit, pid=pal["id"]: self._rename_slot(pid, ne.text()))
        
        # When clicking the line edit, select the row
        name_edit.selectionChanged.connect(lambda pid=pal["id"]: self._select_row(pid))
        h.addWidget(name_edit)
        h.addStretch()

        # Action Buttons (Tool buttons 30x30)
        def _tool_btn(icon_name, tooltip, callback):
            btn = QtWidgets.QToolButton()
            btn.setIcon(_create_icon(icon_name))
            btn.setFixedSize(30, 30)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("QToolButton { background: transparent; border: none; border-radius: 4px; } QToolButton:hover { background: #4a4a4a; }")
            btn.clicked.connect(callback)
            return btn

        # Edit button
        edit_btn = _tool_btn("edit.svg", "Edit Name", lambda _, ne=name_edit: ne.setFocus())
        h.addWidget(edit_btn)
        h.addSpacing(10)

        # Visibility toggle
        is_visible = pal.get("visible", True)
        vis_icon = "eye.svg" if is_visible else "eye_off.svg"
        vis_btn = _tool_btn(vis_icon, "Toggle visibility", lambda _, pid=pal["id"]: self._toggle_visibility(pid))
        h.addWidget(vis_btn)
        h.addSpacing(10)

        # Assign / Unassign button
        assign_btn = _tool_btn("box_select.svg", "Assign to current frame", lambda _, pid=pal["id"]: self._on_assign_clicked(pid))
        self._assign_buttons[pal["id"]] = assign_btn
        h.addWidget(assign_btn)
        h.addSpacing(10)

        # Frame count badge
        count = ac_palette.get_frame_count_for_palette(pal["id"])
        badge = QtWidgets.QLabel(str(count))
        badge.setAlignment(QtCore.Qt.AlignCenter)
        badge.setFixedSize(32, 20)
        badge.setStyleSheet(
            "background: #1e252d; border-radius: 8px; color: {}; font-size: 11px; font-weight: bold;"
            .format(ACCENT))
        h.addWidget(badge)
        h.addSpacing(10)

        # Delete button
        del_btn = _tool_btn("trash.svg", "Delete slot", lambda _, pid=pal["id"]: self._delete_slot(pid))
        h.addWidget(del_btn)

        return row

    def _select_row(self, palette_id):
        if self._selected_palette_id != palette_id:
            self._selected_palette_id = palette_id
            self._refresh_palette_tab()

    def _update_assign_states(self):
        """Update assign/unassign icons based on current frame data."""
        if not hasattr(self, "_assign_buttons"): return
        
        # Get current frame data
        frame = int(cmds.currentTime(query=True))
        data = ac_frames.get_frame_data(frame)
        active_pid = data.get("palette_id") if data else None
        
        for pid, btn in self._assign_buttons.items():
            if pid == active_pid:
                btn.setIcon(_create_icon("box_unselect.svg"))
                btn.setToolTip("Unassign from current frame")
            else:
                btn.setIcon(_create_icon("box_select.svg"))
                btn.setToolTip("Assign to current frame")
                
        # Update footer button based on selected palette
        if self._footer_assign_btn and self._selected_palette_id:
            if self._selected_palette_id == active_pid:
                self._footer_assign_btn.setText("  Unassign Selection")
                self._footer_assign_btn.setIcon(_create_icon("box_unselect.svg"))
                self._footer_assign_btn.setStyleSheet("background-color: #f44336;") # Red accent
            else:
                self._footer_assign_btn.setText("  Assign Selection")
                self._footer_assign_btn.setIcon(_create_icon("box_select.svg"))
                self._footer_assign_btn.setStyleSheet("") # Default accent

    def _on_assign_clicked(self, palette_id):
        """Handle assign/unassign logic with caution prompt."""
        frame = int(cmds.currentTime(query=True))
        data = ac_frames.get_frame_data(frame)
        
        if data and data.get("palette_id") == palette_id:
            # It's currently assigned to this slot -> UNASSIGN
            self._perform_unassign(frame)
        else:
            # ASSIGN
            self._select_row(palette_id)
            ac_frames.assign_selection_to_palette(palette_id)
            self._refresh_palette_tab()
            self._refresh_frames_tab()
            ac_overlay.refresh_overlay()

    def _on_footer_assign_clicked(self):
        """Handle the big footer button click."""
        if not self._selected_palette_id:
            return
        self._on_assign_clicked(self._selected_palette_id)

    def _perform_unassign(self, frame):
        """Show caution dialog if needed, then unassign."""
        global _UNASSIGN_PROMPT_DO_NOT_SHOW
        
        if not _UNASSIGN_PROMPT_DO_NOT_SHOW:
            # Custom caution dialog with checkbox
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Confirm Unassign")
            msg_box.setText("Are you sure you want to unassign this color from the current selection?")
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            
            proceed_btn = msg_box.addButton("Proceed", QtWidgets.QMessageBox.AcceptRole)
            cancel_btn = msg_box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
            
            checkbox = QtWidgets.QCheckBox("Do not show again")
            msg_box.setCheckBox(checkbox)
            
            msg_box.exec_()
            
            if msg_box.clickedButton() == cancel_btn:
                return
                
            if checkbox.isChecked():
                _UNASSIGN_PROMPT_DO_NOT_SHOW = True
                
        # Perform unassign
        # If it's a range, we'd need to handle range removal, but for now we remove current frame
        ac_frames.remove_frame(frame)
        self._refresh_palette_tab()
        self._refresh_frames_tab()
        ac_overlay.refresh_overlay()

    def _add_palette_slot(self):
        result = ac_palette.add_palette_slot()
        if result:
            self._refresh_palette_tab()

    def _change_color(self, palette_id):
        pal = ac_palette.get_palette_by_id(palette_id)
        if not pal:
            return
        self._select_row(palette_id)
        rgb = pal["color"]
        initial = QtGui.QColor.fromRgbF(rgb[0], rgb[1], rgb[2])
        color = QtWidgets.QColorDialog.getColor(initial, self, "Pick Slot Color")
        if color.isValid():
            ac_palette.change_palette_color(
                palette_id, color.redF(), color.greenF(), color.blueF())
            self._refresh_palette_tab()
            ac_overlay.refresh_overlay()

    def _rename_slot(self, palette_id, new_name):
        ac_palette.rename_palette_slot(palette_id, new_name)
        self._refresh_palette_tab()

    def _toggle_visibility(self, palette_id):
        ac_palette.toggle_palette_visibility(palette_id)
        self._refresh_palette_tab()
        ac_overlay.refresh_overlay()

    def _delete_slot(self, palette_id):
        self._select_row(palette_id)
        result = cmds.confirmDialog(
            title="Delete Slot",
            message="Delete this palette slot and all its frame assignments?",
            button=["Delete", "Cancel"],
            defaultButton="Cancel", cancelButton="Cancel")
        if result == "Delete":
            ac_palette.delete_palette_slot(palette_id)
            if self._selected_palette_id == palette_id:
                self._selected_palette_id = None
            self._refresh_palette_tab()
            self._refresh_frames_tab()
            ac_overlay.refresh_overlay()

    # ══════════════════════════════════════════════════════
    #  TAB 2 — FRAMES
    # ══════════════════════════════════════════════════════

    def _build_frames_tab(self):
        layout = QtWidgets.QVBoxLayout(self._frames_tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self._frames_list = QtWidgets.QListWidget()
        self._frames_list.setToolTip("Click to jump to frame")
        self._frames_list.itemClicked.connect(self._on_frame_clicked)
        layout.addWidget(self._frames_list)

        btn_row = QtWidgets.QHBoxLayout()
        edit_btn = QtWidgets.QPushButton("Edit Label")
        edit_btn.clicked.connect(self._edit_frame_label)
        btn_row.addWidget(edit_btn)

        del_btn = QtWidgets.QPushButton("Remove")
        del_btn.clicked.connect(self._remove_selected_frame)
        btn_row.addWidget(del_btn)

        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_frames_tab)
        btn_row.addWidget(refresh_btn)
        layout.addLayout(btn_row)

    def _refresh_frames_tab(self):
        self._frames_list.clear()
        all_frames = ac_frames.get_all_frames()
        palettes = {p["id"]: p for p in ac_palette.get_palettes()}

        for frame_str in sorted(all_frames.keys(), key=int):
            entry = all_frames[frame_str]
            pid = entry.get("palette_id", "")
            pal = palettes.get(pid, {})
            label = entry.get("label", "")
            slot_name = pal.get("name", pid)
            rgb = pal.get("color", [0.5, 0.5, 0.5])

            display = "f.{}  |  {}".format(frame_str, slot_name)
            if label:
                display += "  —  {}".format(label)

            item = QtWidgets.QListWidgetItem()
            item.setIcon(QtGui.QIcon(_color_swatch_pixmap(rgb)))
            item.setText(display)
            item.setData(QtCore.Qt.UserRole, int(frame_str))
            self._frames_list.addItem(item)

    def _on_frame_clicked(self, item):
        frame = item.data(QtCore.Qt.UserRole)
        if frame is not None:
            cmds.currentTime(frame)

    def _edit_frame_label(self):
        item = self._frames_list.currentItem()
        if not item:
            return
        frame = item.data(QtCore.Qt.UserRole)
        entry = ac_frames.get_frame_data(frame)
        if not entry:
            return

        res = cmds.promptDialog(
            title="Edit Label", message="Label for frame {}:".format(frame),
            text=entry.get("label", ""),
            button=["OK", "Cancel"], defaultButton="OK", cancelButton="Cancel")
        if res == "OK":
            new_label = cmds.promptDialog(query=True, text=True)
            ac_frames.update_frame_label(frame, label=new_label)
            self._refresh_frames_tab()
            ac_overlay.refresh_overlay()

    def _remove_selected_frame(self):
        item = self._frames_list.currentItem()
        if not item:
            return
        frame = item.data(QtCore.Qt.UserRole)
        ac_frames.remove_frame(frame)
        self._refresh_palette_tab()
        self._refresh_frames_tab()
        ac_overlay.refresh_overlay()

    # ══════════════════════════════════════════════════════
    #  TAB 3 — SEARCH
    # ══════════════════════════════════════════════════════

    def _build_search_tab(self):
        layout = QtWidgets.QVBoxLayout(self._search_tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self._search_input = QtWidgets.QLineEdit()
        self._search_input.setPlaceholderText("Search labels & notes...")
        self._search_input.textChanged.connect(self._run_search)
        layout.addWidget(self._search_input)

        # Frame range filter
        range_row = QtWidgets.QHBoxLayout()
        range_row.addWidget(QtWidgets.QLabel("From:"))
        self._search_min = QtWidgets.QSpinBox()
        self._search_min.setRange(-99999, 99999)
        self._search_min.setValue(0)
        range_row.addWidget(self._search_min)
        range_row.addWidget(QtWidgets.QLabel("To:"))
        self._search_max = QtWidgets.QSpinBox()
        self._search_max.setRange(-99999, 99999)
        self._search_max.setValue(9999)
        range_row.addWidget(self._search_max)
        layout.addLayout(range_row)

        self._search_results = QtWidgets.QListWidget()
        self._search_results.itemClicked.connect(self._on_search_result_clicked)
        layout.addWidget(self._search_results)

        sel_btn = QtWidgets.QPushButton("Select All Matching Frames")
        sel_btn.setProperty("accent", True)
        sel_btn.clicked.connect(self._select_matching_frames)
        layout.addWidget(sel_btn)

    def _run_search(self):
        query = self._search_input.text()
        frame_min = self._search_min.value()
        frame_max = self._search_max.value()
        results = ac_frames.search_frames(
            query=query, frame_min=frame_min, frame_max=frame_max)
        palettes = {p["id"]: p for p in ac_palette.get_palettes()}

        self._search_results.clear()
        for frame, entry in results:
            pid = entry.get("palette_id", "")
            pal = palettes.get(pid, {})
            rgb = pal.get("color", [0.5, 0.5, 0.5])
            label = entry.get("label", "")
            display = "f.{}  {}".format(frame, label or pal.get("name", ""))

            item = QtWidgets.QListWidgetItem()
            item.setIcon(QtGui.QIcon(_color_swatch_pixmap(rgb)))
            item.setText(display)
            item.setData(QtCore.Qt.UserRole, frame)
            self._search_results.addItem(item)

    def _on_search_result_clicked(self, item):
        frame = item.data(QtCore.Qt.UserRole)
        if frame is not None:
            cmds.currentTime(frame)

    def _select_matching_frames(self):
        """Select all matching frames in the timeline."""
        frames = []
        for i in range(self._search_results.count()):
            item = self._search_results.item(i)
            f = item.data(QtCore.Qt.UserRole)
            if f is not None:
                frames.append(f)
        if not frames:
            return
        # Jump to first match
        cmds.currentTime(frames[0])
        cmds.inViewMessage(
            amg="<hl>AniColor</hl>: {} matching frames found".format(len(frames)),
            pos="topCenter", fade=True, fadeStayTime=1500)

    # ══════════════════════════════════════════════════════
    #  TAB 4 — EXPORT / TEMPLATES
    # ══════════════════════════════════════════════════════

    def _build_export_tab(self):
        layout = QtWidgets.QVBoxLayout(self._export_tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Export buttons
        exp_label = QtWidgets.QLabel("Export")
        exp_label.setProperty("header", True)
        layout.addWidget(exp_label)

        exp_row = QtWidgets.QHBoxLayout()
        json_exp = QtWidgets.QPushButton("Export JSON...")
        json_exp.clicked.connect(self._export_json)
        exp_row.addWidget(json_exp)

        csv_exp = QtWidgets.QPushButton("Export CSV...")
        csv_exp.clicked.connect(self._export_csv)
        exp_row.addWidget(csv_exp)
        layout.addLayout(exp_row)

        # Import
        imp_label = QtWidgets.QLabel("Import")
        imp_label.setProperty("header", True)
        layout.addWidget(imp_label)

        imp_row = QtWidgets.QHBoxLayout()
        json_imp = QtWidgets.QPushButton("Import JSON (Merge)...")
        json_imp.clicked.connect(lambda: self._import_json(merge=True))
        imp_row.addWidget(json_imp)

        json_replace = QtWidgets.QPushButton("Import JSON (Replace)...")
        json_replace.clicked.connect(lambda: self._import_json(merge=False))
        imp_row.addWidget(json_replace)
        layout.addLayout(imp_row)

        # Templates
        tmpl_label = QtWidgets.QLabel("Templates")
        tmpl_label.setProperty("header", True)
        layout.addWidget(tmpl_label)

        self._template_list = QtWidgets.QListWidget()
        for name in ac_export.list_templates():
            display = name.replace("_", " ").title()
            self._template_list.addItem(display)
            self._template_list.item(
                self._template_list.count() - 1
            ).setData(QtCore.Qt.UserRole, name)
        layout.addWidget(self._template_list)

        load_btn = QtWidgets.QPushButton("Load Template")
        load_btn.setProperty("accent", True)
        load_btn.clicked.connect(self._load_template)
        layout.addWidget(load_btn)

        layout.addStretch()

    def _export_json(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export AniColor JSON",
            os.path.expanduser("~"), "JSON Files (*.json)")
        if path:
            ac_export.export_json(path)

    def _export_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export AniColor CSV",
            os.path.expanduser("~"), "CSV Files (*.csv)")
        if path:
            ac_export.export_csv(path)

    def _import_json(self, merge=True):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import AniColor JSON",
            os.path.expanduser("~"), "JSON Files (*.json)")
        if path:
            if ac_export.import_json(path, merge=merge):
                self._refresh_palette_tab()
                self._refresh_frames_tab()
                ac_overlay.refresh_overlay()

    def _load_template(self):
        item = self._template_list.currentItem()
        if not item:
            return
        template_name = item.data(QtCore.Qt.UserRole)
        result = cmds.confirmDialog(
            title="Load Template",
            message="This will replace your current palette. Continue?",
            button=["Load", "Cancel"],
            defaultButton="Cancel", cancelButton="Cancel")
        if result == "Load":
            if ac_export.load_template(template_name):
                self._refresh_palette_tab()
                self._refresh_frames_tab()
                ac_overlay.refresh_overlay()

    # ══════════════════════════════════════════════════════
    #  Tab change handler
    # ══════════════════════════════════════════════════════

    def _on_tab_changed(self, index):
        if index == 0:
            self._refresh_palette_tab()
        elif index == 1:
            self._refresh_frames_tab()

    def closeEvent(self, event):
        """Cleanup overlay and HUD when panel closes."""
        ac_hud.disable_hud()
        ac_overlay.destroy_overlay()
        if self._script_job:
            try:
                cmds.scriptJob(kill=self._script_job, force=True)
            except Exception:
                pass
            self._script_job = None
        super(AniColorPanel, self).closeEvent(event)


# ──────────────────────────────────────────────────────────────
# Global instance
# ──────────────────────────────────────────────────────────────

_PANEL_INSTANCE = None


def show_panel():
    """Show the AniColor panel."""
    global _PANEL_INSTANCE
    import traceback
    try:
        if _PANEL_INSTANCE is not None:
            try:
                _PANEL_INSTANCE.close()
            except Exception:
                pass
        _PANEL_INSTANCE = AniColorPanel()
        _PANEL_INSTANCE.show()
    except Exception as e:
        cmds.warning("AniColor Panel Error: {} \n{}".format(e, traceback.format_exc()))
        cmds.inViewMessage(amg="<hl>AniColor Error</hl>: Check Script Editor", pos="topCenter", fade=True, fadeStayTime=3000)
