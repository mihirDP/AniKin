"""
folder_tree.py — Folder Tree Navigation & Studio Library Import for AniPose Pro V3.1.
"""

import os
import shutil
import maya.cmds as cmds
from anikin.core.qt_compat import QtWidgets, QtCore, QtGui
from anikin.AniPosePro.io.studiolibrary_importer import import_studiolibrary_folder


class FolderTreeWidget(QtWidgets.QWidget):
    """
    Folder tree with color-coded borders and drag-and-drop.
    """

    folder_selected = QtCore.Signal(str) # rel_folder_path
    import_requested = QtCore.Signal()

    def __init__(self, root_dir: str = "", parent=None):
        super(FolderTreeWidget, self).__init__(parent)
        self.root_dir = root_dir

        self._build_ui()
        self.refresh_tree()

    def _build_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # Header toolbar
        tb = QtWidgets.QHBoxLayout()
        hdr_lbl = QtWidgets.QLabel("FOLDERS")
        hdr_lbl.setStyleSheet("font-weight: bold; color: #8b9299; font-size: 11px;")
        tb.addWidget(hdr_lbl)
        tb.addStretch()

        new_folder_btn = QtWidgets.QPushButton("+")
        new_folder_btn.setFixedSize(22, 22)
        new_folder_btn.setToolTip("Create New Folder")
        new_folder_btn.clicked.connect(self._create_new_folder)
        tb.addWidget(new_folder_btn)

        lay.addLayout(tb)

        # Tree Widget
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        lay.addWidget(self.tree)

        # Studio Library Import Button
        import_btn = QtWidgets.QPushButton("Import Studio Library...")
        import_btn.setStyleSheet("font-size: 10px; padding: 4px;")
        import_btn.clicked.connect(self._on_import_studio_library)
        lay.addWidget(import_btn)

    def refresh_tree(self):
        self.tree.clear()
        if not self.root_dir or not os.path.exists(self.root_dir):
            return

        all_item = QtWidgets.QTreeWidgetItem(self.tree, ["📁 All Items"])
        all_item.setData(0, QtCore.Qt.UserRole, "")

        folder_map = {"": all_item}

        for root, dirs, files in os.walk(self.root_dir):
            # Prune hidden directories and Studio Library item directories from traversal
            sl_item_dirs = [d for d in dirs if d.endswith(".pose") or d.endswith(".anim") or d.endswith(".clip")]
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != ".versions" and "_tmp_" not in d and d not in sl_item_dirs]
            
            rel = os.path.relpath(root, self.root_dir)
            if rel == "." or rel == "":
                continue

            parent_rel = os.path.dirname(rel)
            if parent_rel == "." or parent_rel == "":
                parent_rel = ""

            parent_item = folder_map.get(parent_rel, all_item)
            folder_name = os.path.basename(rel)

            item = QtWidgets.QTreeWidgetItem(parent_item, [f"📁 {folder_name}"])
            item.setData(0, QtCore.Qt.UserRole, rel)
            folder_map[rel] = item

        self.tree.expandAll()

    def _on_selection_changed(self):
        selected = self.tree.selectedItems()
        if selected:
            rel_path = selected[0].data(0, QtCore.Qt.UserRole)
            self.folder_selected.emit(rel_path if rel_path is not None else "")
        else:
            self.folder_selected.emit("")

    def _create_new_folder(self):
        selected = self.tree.selectedItems()
        parent_rel = selected[0].data(0, QtCore.Qt.UserRole) if selected else ""
        parent_dir = os.path.join(self.root_dir, parent_rel) if parent_rel else self.root_dir

        name, ok = QtWidgets.QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and name.strip():
            new_dir = os.path.join(parent_dir, name.strip())
            os.makedirs(new_dir, exist_ok=True)
            self.refresh_tree()

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        rel_path = item.data(0, QtCore.Qt.UserRole)
        if rel_path is None or rel_path == "":
            return

        menu = QtWidgets.QMenu(self)
        act_new = menu.addAction("New Sub-folder")
        act_rename = menu.addAction("Rename")
        act_del = menu.addAction("Delete Folder")

        action = menu.exec_(self.tree.mapToGlobal(pos))
        if action == act_new:
            self._create_new_folder()
        elif action == act_rename:
            name, ok = QtWidgets.QInputDialog.getText(self, "Rename Folder", "New Name:", text=os.path.basename(rel_path))
            if ok and name.strip():
                old_dir = os.path.join(self.root_dir, rel_path)
                new_dir = os.path.join(os.path.dirname(old_dir), name.strip())
                os.rename(old_dir, new_dir)
                self.refresh_tree()
        elif action == act_del:
            confirm = QtWidgets.QMessageBox.question(self, "Delete Folder", f"Delete folder '{rel_path}' and all contents?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if confirm == QtWidgets.QMessageBox.Yes:
                shutil.rmtree(os.path.join(self.root_dir, rel_path), ignore_errors=True)
                self.refresh_tree()

    def _on_import_studio_library(self):
        sl_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Studio Library Root Folder")
        if sl_dir:
            import_studiolibrary_folder(sl_dir, self.root_dir)
            self.refresh_tree()
            self.import_requested.emit()
