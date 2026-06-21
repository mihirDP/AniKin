"""
selection_sets_panel.py
A popup panel for managing AniKin selection sets.

Opened from the toolbar, this panel lets users:
- Save the current selection with a name
- Recall saved sets (click to select)
- Delete sets
- Add to current selection (Shift-click)

Sets are persisted in the Maya scene via a hidden network node,
so they survive save/load cycles.
"""

import maya.cmds as cmds

from anikin.core.qt_compat import QtWidgets, QtCore, get_maya_main_window
from anikin.ui.theme import STYLESHEET
from anikin import AniSets


class SelectionSetsPanel(QtWidgets.QDialog):
    """Selection Sets management dialog."""

    def __init__(self, parent=None):
        super(SelectionSetsPanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin â€” Selection Sets")
        self.setObjectName("AniKinSelSetsPanel")
        self.setMinimumSize(280, 300)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # â”€â”€ Save row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        save_row = QtWidgets.QHBoxLayout()
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Set name...")
        self.name_input.returnPressed.connect(self._save_set)
        save_row.addWidget(self.name_input)

        save_btn = QtWidgets.QPushButton("Save Selection")
        save_btn.setProperty("accent", True)
        save_btn.setToolTip("Save current Maya selection under the given name")
        save_btn.clicked.connect(self._save_set)
        save_row.addWidget(save_btn)

        layout.addLayout(save_row)

        # â”€â”€ Sets list â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self.sets_list = QtWidgets.QListWidget()
        self.sets_list.setToolTip(
            "Click to select set  |  Double-click to select and close"
        )
        self.sets_list.itemClicked.connect(self._recall_set)
        self.sets_list.itemDoubleClicked.connect(self._recall_and_close)
        layout.addWidget(self.sets_list)

        # â”€â”€ Button row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        btn_row = QtWidgets.QHBoxLayout()

        add_btn = QtWidgets.QPushButton("Add to Sel")
        add_btn.setToolTip("Add set members to the current selection")
        add_btn.clicked.connect(self._add_to_selection)
        btn_row.addWidget(add_btn)

        del_btn = QtWidgets.QPushButton("Delete Set")
        del_btn.setToolTip("Delete the selected set")
        del_btn.clicked.connect(self._delete_set)
        btn_row.addWidget(del_btn)

        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_list)
        btn_row.addWidget(refresh_btn)

        layout.addLayout(btn_row)

    def _refresh_list(self):
        """Reload the list from the scene's storage node."""
        self.sets_list.clear()
        for name in AniSets.list_sets():
            self.sets_list.addItem(name)

    def _save_set(self):
        """Save current selection under the typed name."""
        name = self.name_input.text().strip()
        if not name:
            cmds.warning("AniKin: Enter a name for the selection set.")
            return
        # Sanitize: only alphanumeric + underscores
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        AniSets.save_set(safe_name)
        self.name_input.clear()
        self._refresh_list()

    def _recall_set(self, item):
        """Select the objects in the clicked set."""
        AniSets.recall_set(item.text())

    def _recall_and_close(self, item):
        """Select and close the dialog."""
        AniSets.recall_set(item.text())
        self.close()

    def _add_to_selection(self):
        """Add set members to current selection."""
        item = self.sets_list.currentItem()
        if item:
            AniSets.recall_set(item.text(), add_to_selection=True)

    def _delete_set(self):
        """Delete the currently selected set."""
        item = self.sets_list.currentItem()
        if item:
            AniSets.delete_set(item.text())
            self._refresh_list()


# â”€â”€ Global instance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_PANEL_INSTANCE = None


def show_panel():
    """Show the Selection Sets panel (creates or brings to front)."""
    global _PANEL_INSTANCE
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.close()
        except Exception:
            pass
    _PANEL_INSTANCE = SelectionSetsPanel()
    _PANEL_INSTANCE.show()

