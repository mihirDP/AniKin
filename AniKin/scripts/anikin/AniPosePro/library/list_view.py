"""
list_view.py — Compact Sortable List View for AniPose Pro V3.1.
"""

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui


class LibraryListViewWidget(QtWidgets.QTableWidget):
    """
    Compact sortable table view per item conforming to Section 7.5 of AniPose Pro PRD.
    """

    item_selected = QtCore.Signal(dict, bool)

    def __init__(self, parent=None):
        super(LibraryListViewWidget, self).__init__(0, 7, parent)
        self.setHorizontalHeaderLabels(["Type", "Thumb", "Name", "Tags", "Rating", "Date", "Color"])
        self.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.item_map = {} # row -> item_dict
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def populate(self, items: list):
        self.setSortingEnabled(False)
        self.setRowCount(0)
        self.item_map = {}

        for row, item in enumerate(items):
            self.insertRow(row)
            self.item_map[row] = item

            # Type
            itype = item.get("type", "pose").upper()
            t_item = QtWidgets.QTableWidgetItem(itype)

            # Thumb placeholder
            thumb_item = QtWidgets.QTableWidgetItem()
            t_path = item.get("thumbnail", "")
            if t_path:
                pix = QtGui.QPixmap(t_path)
                if not pix.isNull():
                    thumb_item.setIcon(QtGui.QIcon(pix.scaled(32, 32, QtCore.Qt.KeepAspectRatio)))

            # Name
            name_item = QtWidgets.QTableWidgetItem(item.get("name", ""))

            # Tags
            tags_str = ", ".join(item.get("tags", []))
            tags_item = QtWidgets.QTableWidgetItem(tags_str)

            # Rating
            rating_item = QtWidgets.QTableWidgetItem("★" * item.get("rating", 0))

            # Date
            date_item = QtWidgets.QTableWidgetItem(str(item.get("created", ""))[:10])

            # Color
            color_item = QtWidgets.QTableWidgetItem("●")
            color_item.setForeground(QtGui.QColor(item.get("color", "#3a9e6e")))

            self.setItem(row, 0, t_item)
            self.setItem(row, 1, thumb_item)
            self.setItem(row, 2, name_item)
            self.setItem(row, 3, tags_item)
            self.setItem(row, 4, rating_item)
            self.setItem(row, 5, date_item)
            self.setItem(row, 6, color_item)

        self.setSortingEnabled(True)

    def _on_selection_changed(self):
        rows = self.selectionModel().selectedRows()
        if rows:
            r = rows[0].row()
            item = self.item_map.get(r)
            if item:
                self.item_selected.emit(item, False)
