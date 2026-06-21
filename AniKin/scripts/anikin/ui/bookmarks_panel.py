"""
bookmarks_panel.py
UI Panel for AniBookmarks.
Allows saving, searching, reordering, and exporting/importing time bookmarks.
"""

import os
import maya.cmds as cmds

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui, get_maya_main_window
from anikin.ui.theme import STYLESHEET
from anikin import AniBookmarks

# List of color keys for UI dropdown
COLOR_KEYS = ["blue", "red", "green", "gold", "purple", "teal", "pink", "white"]


def get_color_icon(color_hex):
    """Generate a circular color icon dynamically."""
    pixmap = QtGui.QPixmap(14, 14)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(QtGui.QColor(color_hex))
    painter.setPen(QtCore.Qt.NoPen)
    painter.drawEllipse(0, 0, 14, 14)
    painter.end()
    return QtGui.QIcon(pixmap)


class BookmarksPanel(QtWidgets.QDialog):
    """Time Bookmarks management dialog."""

    def __init__(self, parent=None):
        super(BookmarksPanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin — Bookmarks")
        self.setObjectName("AniKinBookmarksPanel")
        self.setMinimumSize(320, 420)
        self.setStyleSheet(STYLESHEET)
        
        self._block_signals = False
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # —— Search bar —————————————————————————————————————
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Filter bookmarks...")
        self.search_input.textChanged.connect(self._filter_list)
        layout.addWidget(self.search_input)

        # —— Save row ——————————————————————————————————————
        save_layout = QtWidgets.QVBoxLayout()
        save_layout.setSpacing(4)
        
        name_row = QtWidgets.QHBoxLayout()
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("New bookmark name...")
        self.name_input.returnPressed.connect(self._save_bookmark)
        name_row.addWidget(self.name_input)
        
        # Color dropdown
        self.color_combo = QtWidgets.QComboBox()
        for c in COLOR_KEYS:
            self.color_combo.addItem(c.capitalize(), c)
        name_row.addWidget(self.color_combo)
        save_layout.addLayout(name_row)
        
        # Range inputs
        range_row = QtWidgets.QHBoxLayout()
        self.use_range_chk = QtWidgets.QCheckBox("Range Bookmark")
        self.use_range_chk.toggled.connect(self._toggle_range_fields)
        range_row.addWidget(self.use_range_chk)
        
        self.start_frame_input = QtWidgets.QDoubleSpinBox()
        self.start_frame_input.setRange(-99999, 99999)
        self.start_frame_input.setToolTip("Start Frame")
        self.start_frame_input.setValue(cmds.currentTime(query=True))
        self.start_frame_input.setEnabled(False)
        range_row.addWidget(self.start_frame_input)
        
        self.end_frame_input = QtWidgets.QDoubleSpinBox()
        self.end_frame_input.setRange(-99999, 99999)
        self.end_frame_input.setToolTip("End Frame")
        self.end_frame_input.setValue(cmds.currentTime(query=True) + 10)
        self.end_frame_input.setEnabled(False)
        range_row.addWidget(self.end_frame_input)
        
        save_layout.addLayout(range_row)

        save_btn = QtWidgets.QPushButton("Save Bookmark")
        save_btn.setProperty("accent", True)
        save_btn.clicked.connect(self._save_bookmark)
        save_layout.addWidget(save_btn)

        layout.addLayout(save_layout)

        # —— Bookmarks list ——————————————————————————————————
        self.bookmarks_list = QtWidgets.QListWidget()
        self.bookmarks_list.setToolTip(
            "Click to jump to bookmark  |  Double-click to focus timeline range  |  Drag to reorder"
        )
        self.bookmarks_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.bookmarks_list.itemClicked.connect(self._goto_bookmark)
        self.bookmarks_list.itemDoubleClicked.connect(self._goto_and_close)
        
        # Connect layout changed to save reordering
        self.bookmarks_list.model().layoutChanged.connect(self._on_reordered)
        
        layout.addWidget(self.bookmarks_list)

        # —— Button row ————————————————————————————————————
        btn_row = QtWidgets.QHBoxLayout()

        del_btn = QtWidgets.QPushButton("Delete Selected")
        del_btn.clicked.connect(self._delete_bookmark)
        btn_row.addWidget(del_btn)

        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_list)
        btn_row.addWidget(refresh_btn)

        layout.addLayout(btn_row)
        
        # —— Export/Import Row ——————————————————————————————
        io_row = QtWidgets.QHBoxLayout()
        export_btn = QtWidgets.QPushButton("Export JSON...")
        export_btn.clicked.connect(self._export_bookmarks)
        io_row.addWidget(export_btn)
        
        import_btn = QtWidgets.QPushButton("Import JSON...")
        import_btn.clicked.connect(self._import_bookmarks)
        io_row.addWidget(import_btn)
        layout.addLayout(io_row)

    def _toggle_range_fields(self, enabled):
        self.start_frame_input.setEnabled(enabled)
        self.end_frame_input.setEnabled(enabled)
        if enabled:
            # Sync to current time
            curr = cmds.currentTime(query=True)
            self.start_frame_input.setValue(curr)
            self.end_frame_input.setValue(curr + 10)

    def _refresh_list(self):
        """Reload the list from core bookmarks."""
        if self._block_signals:
            return
            
        self.bookmarks_list.clear()
        bookmarks = AniBookmarks.list_bookmarks()
        
        for idx, b in enumerate(bookmarks):
            name = b["name"]
            frame = b["frame"]
            color = b["color"]
            range_end = b.get("range_end")
            
            hex_color = AniBookmarks.COLORS.get(color, "#3b82f6")
            icon = get_color_icon(hex_color)
            
            if range_end is not None:
                display_text = "[{:.1f} - {:.1f}]  {}".format(frame, range_end, name)
            else:
                display_text = "[{:.1f}]  {}".format(frame, name)
                
            item = QtWidgets.QListWidgetItem()
            item.setIcon(icon)
            item.setText(display_text)
            # Store the original dict and original index
            item.setData(QtCore.Qt.UserRole, b)
            item.setData(QtCore.Qt.UserRole + 1, idx)
            
            self.bookmarks_list.addItem(item)
            
        self._filter_list()

    def _filter_list(self):
        """Filter list items based on the search input."""
        query = self.search_input.text().lower()
        for i in range(self.bookmarks_list.count()):
            item = self.bookmarks_list.item(i)
            item.setHidden(query not in item.text().lower())

    def _save_bookmark(self):
        """Save a bookmark from user inputs."""
        name = self.name_input.text().strip()
        color = self.color_combo.currentData()
        
        if self.use_range_chk.isChecked():
            start = self.start_frame_input.value()
            end = self.end_frame_input.value()
            if end <= start:
                cmds.warning("AniKin: End frame must be greater than start frame.")
                return
            success = AniBookmarks.save_bookmark(name, frame=start, color=color, range_end=end)
        else:
            success = AniBookmarks.save_bookmark(name, color=color)
            
        if success:
            self.name_input.clear()
            self._refresh_list()

    def _goto_bookmark(self, item):
        """Jump to the clicked bookmark's frame/range."""
        b = item.data(QtCore.Qt.UserRole)
        # Find index in list
        bookmarks = AniBookmarks.list_bookmarks()
        try:
            idx = bookmarks.index(b)
            AniBookmarks.goto_bookmark(idx)
        except ValueError:
            pass

    def _goto_and_close(self, item):
        """Jump and close."""
        self._goto_bookmark(item)
        self.close()

    def _delete_bookmark(self):
        """Delete selected bookmark."""
        item = self.bookmarks_list.currentItem()
        if item:
            b = item.data(QtCore.Qt.UserRole)
            bookmarks = AniBookmarks.list_bookmarks()
            try:
                idx = bookmarks.index(b)
                AniBookmarks.delete_bookmark(idx)
                self._refresh_list()
            except ValueError:
                pass

    def _on_reordered(self):
        """Save the new order back to the core after a drag-and-drop internal move."""
        self._block_signals = True
        new_list = []
        for i in range(self.bookmarks_list.count()):
            item = self.bookmarks_list.item(i)
            new_list.append(item.data(QtCore.Qt.UserRole))
        
        AniBookmarks._save_bookmarks(new_list)
        self._block_signals = False

    def _export_bookmarks(self):
        """Prompt path and export bookmarks."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Bookmarks", os.path.expanduser("~"), "JSON Files (*.json)"
        )
        if path:
            if AniBookmarks.export_bookmarks(path):
                cmds.inViewMessage(amg="<hl>AniKin</hl>: Bookmarks exported successfully.", pos="topCenter", fade=True, fadeStayTime=1500)

    def _import_bookmarks(self):
        """Prompt path and import bookmarks."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Bookmarks", os.path.expanduser("~"), "JSON Files (*.json)"
        )
        if path:
            if AniBookmarks.import_bookmarks(path):
                self._refresh_list()
                cmds.inViewMessage(amg="<hl>AniKin</hl>: Bookmarks imported successfully.", pos="topCenter", fade=True, fadeStayTime=1500)


# —— Global instance —————————————————————————————————————
_PANEL_INSTANCE = None


def show_panel():
    """Show the Bookmarks panel."""
    global _PANEL_INSTANCE
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.close()
        except Exception:
            pass
    _PANEL_INSTANCE = BookmarksPanel()
    _PANEL_INSTANCE.show()
