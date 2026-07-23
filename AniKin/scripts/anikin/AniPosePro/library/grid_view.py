"""
grid_view.py — Multi-Size Grid View Widget for AniPose Pro V3.1.
"""

from anikin.core.qt_compat import QtWidgets, QtCore
from anikin.AniPosePro.ui.thumbnail_card import ThumbnailCardWidget


class FlowLayout(QtWidgets.QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item): self._items.append(item)
    def count(self): return len(self._items)
    def itemAt(self, index):
        if 0 <= index < len(self._items): return self._items[index]
        return None
    def takeAt(self, index):
        if 0 <= index < len(self._items): return self._items.pop(index)
        return None
    def expandingDirections(self): return QtCore.Qt.Orientations(0)
    def hasHeightForWidth(self): return True
    def heightForWidth(self, width): return self._doLayout(QtCore.QRect(0, 0, width, 0), True)
    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._doLayout(rect, False)
    def sizeHint(self): return self.minimumSize()
    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        size += QtCore.QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _doLayout(self, rect, testOnly):
        x, y, line_height = rect.x(), rect.y(), 0
        spacing = self.spacing()
        for item in self._items:
            space_x, space_y = spacing, spacing
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x, y = rect.x(), y + line_height + space_y
                next_x, line_height = x + item.sizeHint().width() + space_x, 0
            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y()


class LibraryGridViewWidget(QtWidgets.QScrollArea):
    """
    Scrollable grid container for thumbnail cards.
    """

    item_selected = QtCore.Signal(dict, bool)
    favorite_toggled = QtCore.Signal(dict, bool)
    action_requested = QtCore.Signal(str, dict)

    def __init__(self, parent=None):
        super(LibraryGridViewWidget, self).__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; background: #0d0f10; }")

        self.size_preset = "M"
        self.cards = []
        self._selected_card = None

        self.container = QtWidgets.QWidget()
        self.flow_layout = FlowLayout(self.container, margin=10, spacing=10)
        self.setWidget(self.container)

    def set_size_preset(self, preset: str):
        if preset in ThumbnailCardWidget.CARD_SIZES:
            self.size_preset = preset

    def populate(self, items: list):
        # Clear existing
        while self.flow_layout.count():
            child = self.flow_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.cards = []
        self._selected_card = None

        for item_dict in items:
            card = ThumbnailCardWidget(item_dict, size_preset=self.size_preset)
            card.card_clicked.connect(self._on_card_clicked)
            card.favorite_toggled.connect(self.favorite_toggled.emit)
            card.action_requested.connect(self.action_requested.emit)

            self.flow_layout.addWidget(card)
            self.cards.append(card)

    def _on_card_clicked(self, item_dict: dict, is_double_click: bool):
        for c in self.cards:
            c.set_selected(c.item_data == item_dict)
        self.item_selected.emit(item_dict, is_double_click)
