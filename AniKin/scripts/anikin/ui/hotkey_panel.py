"""
hotkey_panel.py
Hotkey configuration panel for AniKin.

Provides a clean interface to list all bindable tools, capture custom hotkeys,
validate shortcuts, and save them.
"""

from anikin.core.qt_compat import QtWidgets, QtCore, get_maya_main_window
from anikin.ui.theme import STYLESHEET
from anikin.tools import hotkeys


class KeyCaptureDialog(QtWidgets.QDialog):
    """A dialog that grabs keyboard input to record a shortcut combination."""

    def __init__(self, tool_name, parent=None):
        super(KeyCaptureDialog, self).__init__(parent)
        self.setWindowTitle("Record Shortcut")
        self.setFixedSize(320, 140)
        self.setModal(True)
        self.setStyleSheet(STYLESHEET)
        
        self.shortcut = "None"
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        info = QtWidgets.QLabel("Press key combination for:\n<b>{}</b>".format(tool_name))
        info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(info)
        
        self.display = QtWidgets.QLabel("Press any keys...")
        self.display.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #00b4d8; "
            "padding: 10px; border: 1px dashed #023e8a; border-radius: 4px; "
            "background-color: #1e1e1e;"
        )
        self.display.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.display)
        
        # Action Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        
        clear_btn = QtWidgets.QPushButton("Clear")
        clear_btn.clicked.connect(self._clear)
        btn_layout.addWidget(clear_btn)
        
        ok_btn = QtWidgets.QPushButton("Assign")
        ok_btn.setProperty("accent", True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def _clear(self):
        self.shortcut = "None"
        self.display.setText("None")

    def keyPressEvent(self, event):
        key = event.key()
        
        # Ignore modifier keys pressed alone
        if key in [QtCore.Qt.Key_Control, QtCore.Qt.Key_Alt, QtCore.Qt.Key_Shift, QtCore.Qt.Key_Meta]:
            super(KeyCaptureDialog, self).keyPressEvent(event)
            return
            
        modifiers = event.modifiers()
        parts = []
        if modifiers & QtCore.Qt.ControlModifier:
            parts.append("Ctrl")
        if modifiers & QtCore.Qt.AltModifier:
            parts.append("Alt")
        if modifiers & QtCore.Qt.ShiftModifier:
            parts.append("Shift")
            
        key_str = self._key_to_string(key)
        if key_str:
            parts.append(key_str)
            self.shortcut = "+".join(parts)
            self.display.setText(self.shortcut)
        else:
            self.display.setText("Unknown Key")
            
    def _key_to_string(self, key):
        # A-Z
        if QtCore.Qt.Key_A <= key <= QtCore.Qt.Key_Z:
            return chr(key)
        # 0-9
        if QtCore.Qt.Key_0 <= key <= QtCore.Qt.Key_9:
            return chr(key)
            
        # Special keys
        mapping = {
            QtCore.Qt.Key_Up: "Up",
            QtCore.Qt.Key_Down: "Down",
            QtCore.Qt.Key_Left: "Left",
            QtCore.Qt.Key_Right: "Right",
            QtCore.Qt.Key_Home: "Home",
            QtCore.Qt.Key_End: "End",
            QtCore.Qt.Key_PageUp: "PageUp",
            QtCore.Qt.Key_PageDown: "PageDown",
            QtCore.Qt.Key_Insert: "Insert",
            QtCore.Qt.Key_Delete: "Delete",
            QtCore.Qt.Key_Return: "Return",
            QtCore.Qt.Key_Enter: "Return",
            QtCore.Qt.Key_Space: "Space",
            QtCore.Qt.Key_Backspace: "Backspace",
            QtCore.Qt.Key_Escape: "Escape",
            QtCore.Qt.Key_Tab: "Tab",
        }
        
        # F1-F12
        for f in range(1, 13):
            mapping[getattr(QtCore.Qt, "Key_F{}".format(f))] = "F{}".format(f)
            
        return mapping.get(key, None)


class HotkeyPanel(QtWidgets.QDialog):
    """Hotkey assignment editor."""

    def __init__(self, parent=None):
        super(HotkeyPanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin — Hotkey Manager")
        self.setObjectName("AniKinHotkeyPanel")
        self.setMinimumSize(450, 400)
        self.setStyleSheet(STYLESHEET)

        self.current_mappings = hotkeys.load_hotkeys()
        
        self._build_ui()
        self._populate_table()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header Info
        header = QtWidgets.QLabel("<b>Assign Custom Hotkeys</b>")
        header.setStyleSheet("font-size: 12px; color: #00b4d8;")
        layout.addWidget(header)

        # Table showing bindable tools
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Category", "Tool Action", "Hotkey"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #1e1e1e; gridline-color: #2d2d2d; }"
            "QHeaderView::section { background-color: #383838; color: #999999; border: 1px solid #1a1a1a; }"
        )
        layout.addWidget(self.table)

        # Double click to edit hotkey
        self.table.doubleClicked.connect(self._on_table_double_clicked)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        assign_btn = QtWidgets.QPushButton("Assign Shortcut")
        assign_btn.clicked.connect(self._on_assign_clicked)
        btn_layout.addWidget(assign_btn)

        clear_btn = QtWidgets.QPushButton("Clear Shortcut")
        clear_btn.clicked.connect(self._on_clear_clicked)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()

        save_btn = QtWidgets.QPushButton("Save && Close")
        save_btn.setProperty("accent", True)
        save_btn.clicked.connect(self._on_save_clicked)
        btn_layout.addWidget(save_btn)

        close_btn = QtWidgets.QPushButton("Cancel")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _populate_table(self):
        """Fill table with bindable tools."""
        self.table.setRowCount(len(hotkeys.BINDABLE_TOOLS))
        for row, tool in enumerate(hotkeys.BINDABLE_TOOLS):
            # Category
            cat_item = QtWidgets.QTableWidgetItem(tool["category"])
            cat_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table.setItem(row, 0, cat_item)
            
            # Action Name
            name_item = QtWidgets.QTableWidgetItem(tool["name"])
            self.table.setItem(row, 1, name_item)
            
            # Current Hotkey
            hk_val = self.current_mappings.get(tool["id"], "None")
            hk_item = QtWidgets.QTableWidgetItem(hk_val)
            hk_item.setTextAlignment(QtCore.Qt.AlignCenter)
            # Use accent color for bound hotkeys
            if hk_val != "None":
                hk_item.setForeground(QtCore.Qt.cyan)
            self.table.setItem(row, 2, hk_item)

    def _get_selected_tool(self):
        row = self.table.currentRow()
        if row < 0:
            return None, None
        tool = hotkeys.BINDABLE_TOOLS[row]
        return row, tool

    def _on_table_double_clicked(self, index):
        self._on_assign_clicked()

    def _on_assign_clicked(self):
        row, tool = self._get_selected_tool()
        if not tool:
            return

        dialog = KeyCaptureDialog(tool["name"], self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_hk = dialog.shortcut
            
            # Check if this hotkey is already mapped elsewhere in AniKin
            duplicate_id = None
            for tid, hk in self.current_mappings.items():
                if tid != tool["id"] and hk != "None" and hk == new_hk:
                    duplicate_id = tid
                    break
            
            if duplicate_id:
                dup_tool = next((t for t in hotkeys.BINDABLE_TOOLS if t["id"] == duplicate_id), None)
                dup_name = dup_tool["name"] if dup_tool else duplicate_id
                
                # Warn user
                msg = "Hotkey '{}' is already assigned to:\n<b>{}</b>\n\nDo you want to reassign it?".format(
                    new_hk, dup_name
                )
                res = QtWidgets.QMessageBox.question(
                    self, "Duplicate Hotkey", msg,
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if res != QtWidgets.QMessageBox.Yes:
                    return
                    
                # Clear duplicate assignment
                self.current_mappings[duplicate_id] = "None"
                
            self.current_mappings[tool["id"]] = new_hk
            self._populate_table()

    def _on_clear_clicked(self):
        row, tool = self._get_selected_tool()
        if not tool:
            return
        self.current_mappings[tool["id"]] = "None"
        self._populate_table()

    def _on_save_clicked(self):
        # 1. Unbind removed/changed hotkeys
        old_mappings = hotkeys.load_hotkeys()
        for tool_id, old_hk in old_mappings.items():
            new_hk = self.current_mappings.get(tool_id, "None")
            if old_hk != "None" and old_hk != new_hk:
                hotkeys.remove_hotkey(tool_id, old_hk)

        # 2. Bind new hotkeys
        for tool_id, new_hk in self.current_mappings.items():
            old_hk = old_mappings.get(tool_id, "None")
            if new_hk != "None" and new_hk != old_hk:
                hotkeys.apply_hotkey(tool_id, new_hk)

        # 3. Persist to file
        hotkeys.save_hotkeys(self.current_mappings)
        self.close()


# ── Global instance ────────────────────────────────────────────
_PANEL_INSTANCE = None


def show_panel():
    """Show the Hotkey Manager panel."""
    global _PANEL_INSTANCE
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.close()
        except Exception:
            pass
    _PANEL_INSTANCE = HotkeyPanel()
    _PANEL_INSTANCE.show()
