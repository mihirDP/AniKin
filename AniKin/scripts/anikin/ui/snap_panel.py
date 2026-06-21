"""
snap_panel.py
UI Panel for AniSnap Pose Library.
Shows poses in a responsive thumbnail grid, allowing drag folders, tag search,
blended applying, offset applying, mirroring, and deletion.
Supports Hover Polaroid zoom, multiple library paths, and folder sets.
"""

import os
import maya.cmds as cmds

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui, get_maya_main_window
from anikin.ui.theme import STYLESHEET
from anikin import AniSnap


class PoseHoverPopup(QtWidgets.QLabel):
    """Frameless floating tooltip popup displaying a 256x256 scaled snapshot."""

    def __init__(self, image_path, parent=None):
        super(PoseHoverPopup, self).__init__(parent, QtCore.Qt.ToolTip | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #0f172a; border: 2px solid #3b82f6; border-radius: 8px; padding: 4px;")
        self.setFixedSize(256, 256)
        self.setAlignment(QtCore.Qt.AlignCenter)
        
        if image_path and os.path.exists(image_path):
            pix = QtGui.QPixmap(image_path)
            self.setPixmap(pix.scaled(248, 248, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        else:
            self.setText("No Viewport Preview")
            self.setStyleSheet("color: #6b7280; font-size: 12px; font-weight: bold; background-color: #0f172a;")


class PoseCard(QtWidgets.QFrame):
    """Custom grid card representing a single Pose with image and actions."""
    
    clicked = QtCore.Signal(str)
    double_clicked = QtCore.Signal(str)
    delete_requested = QtCore.Signal(str)
    mirror_requested = QtCore.Signal(str)
    offset_requested = QtCore.Signal(str)

    def __init__(self, name, image_path, parent=None):
        super(PoseCard, self).__init__(parent)
        self.name = name
        self.image_path = image_path
        self.popup = None
        
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
        self.setLineWidth(1)
        self.setFixedSize(110, 140)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet("""
            PoseCard {
                background-color: #1f2937;
                border: 1px solid #374151;
                border-radius: 6px;
            }
            PoseCard:hover {
                border-color: #3b82f6;
                background-color: #27272a;
            }
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        # Thumbnail Image Container
        self.thumb = QtWidgets.QLabel()
        self.thumb.setFixedSize(102, 85)
        self.thumb.setStyleSheet("background-color: #0f172a; border-radius: 4px;")
        self.thumb.setAlignment(QtCore.Qt.AlignCenter)

        if self.image_path and os.path.exists(self.image_path):
            pix = QtGui.QPixmap(self.image_path)
            self.thumb.setPixmap(pix.scaled(102, 85, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation))
        else:
            self.thumb.setText("No Image")
            self.thumb.setStyleSheet("color: #4b5563; font-size: 10px; background-color: #0f172a;")

        layout.addWidget(self.thumb)

        # Name label
        lbl = QtWidgets.QLabel(self.name)
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setStyleSheet("color: #e5e7eb; font-size: 10px; font-weight: 500;")
        
        metrics = QtGui.QFontMetrics(lbl.font())
        elided = metrics.elidedText(self.name, QtCore.Qt.ElideRight, 95)
        lbl.setText(elided)
        layout.addWidget(lbl)

        # Hover Actions Row
        self.actions = QtWidgets.QWidget()
        self.actions.setFixedHeight(22)
        act_layout = QtWidgets.QHBoxLayout(self.actions)
        act_layout.setContentsMargins(0, 0, 0, 0)
        act_layout.setSpacing(2)

        mirror_btn = QtWidgets.QPushButton("M")
        mirror_btn.setToolTip("Apply mirrored")
        mirror_btn.setFixedSize(20, 18)
        mirror_btn.clicked.connect(lambda: self.mirror_requested.emit(self.name))
        act_layout.addWidget(mirror_btn)

        offset_btn = QtWidgets.QPushButton("O")
        offset_btn.setToolTip("Apply as offset")
        offset_btn.setFixedSize(20, 18)
        offset_btn.clicked.connect(lambda: self.offset_requested.emit(self.name))
        act_layout.addWidget(offset_btn)

        del_btn = QtWidgets.QPushButton("X")
        del_btn.setToolTip("Delete pose")
        del_btn.setStyleSheet("color: #ef4444;")
        del_btn.setFixedSize(20, 18)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.name))
        act_layout.addWidget(del_btn)

        layout.addWidget(self.actions)

    def enterEvent(self, event):
        """Show the 2x Polaroid enlarged preview on hover."""
        if not self.popup:
            self.popup = PoseHoverPopup(self.image_path)
            # Position it to the right of the card
            global_pos = self.mapToGlobal(QtCore.QPoint(self.width() + 8, -50))
            self.popup.move(global_pos)
            self.popup.show()
        super(PoseCard, self).enterEvent(event)

    def leaveEvent(self, event):
        """Close the hover popup."""
        if self.popup:
            self.popup.close()
            self.popup.deleteLater()
            self.popup = None
        super(PoseCard, self).leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        super(PoseCard, self.mousePressEvent(event) if hasattr(super(PoseCard, self), "mousePressEvent") else None)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.name)
        super(PoseCard, self).mouseDoubleClickEvent(event)


class SnapPanel(QtWidgets.QDialog):
    """AniSnap pose library panel."""

    def __init__(self, parent=None):
        super(SnapPanel, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniKin — AniSnap Poses")
        self.setObjectName("AniKinSnapPanel")
        self.setMinimumSize(420, 520)
        self.setStyleSheet(STYLESHEET)
        
        self._block_signals = False
        self._build_ui()
        self._load_library_roots()
        self._refresh_folders()
        self._refresh_grid()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # —— Multi-Library & Folder Organization row ——————————
        org_layout = QtWidgets.QHBoxLayout()
        
        org_layout.addWidget(QtWidgets.QLabel("Lib:"))
        self.lib_combo = QtWidgets.QComboBox()
        self.lib_combo.setToolTip("Select Pose Library Root directory.")
        self.lib_combo.currentTextChanged.connect(self._on_library_changed)
        org_layout.addWidget(self.lib_combo)
        
        org_layout.addWidget(QtWidgets.QLabel("Set:"))
        self.folder_combo = QtWidgets.QComboBox()
        self.folder_combo.setToolTip("Select subfolder set (e.g. body, face, walks).")
        self.folder_combo.currentTextChanged.connect(self._on_folder_changed)
        org_layout.addWidget(self.folder_combo)
        
        add_folder_btn = QtWidgets.QPushButton("+")
        add_folder_btn.setFixedSize(22, 22)
        add_folder_btn.setToolTip("Create new subfolder pose set.")
        add_folder_btn.clicked.connect(self._create_folder)
        org_layout.addWidget(add_folder_btn)
        
        layout.addLayout(org_layout)

        # —— Search & Filters ———————————————————————————————
        top_bar = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search poses...")
        self.search_input.textChanged.connect(self._filter_poses)
        top_bar.addWidget(self.search_input)

        save_btn = QtWidgets.QPushButton("Capture Pose")
        save_btn.setProperty("accent", True)
        save_btn.clicked.connect(self._save_pose)
        top_bar.addWidget(save_btn)

        layout.addLayout(top_bar)

        # —— Blend slider ——————————————————————————————————
        blend_box = QtWidgets.QHBoxLayout()
        blend_box.addWidget(QtWidgets.QLabel("Blend Pose:"))
        self.blend_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.blend_slider.setRange(0, 100)
        self.blend_slider.setValue(100)
        blend_box.addWidget(self.blend_slider)
        
        self.blend_val_lbl = QtWidgets.QLabel("1.0")
        self.blend_val_lbl.setFixedWidth(25)
        self.blend_slider.valueChanged.connect(lambda v: self.blend_val_lbl.setText("{:.1f}".format(v / 100.0)))
        blend_box.addWidget(self.blend_val_lbl)
        
        layout.addLayout(blend_box)

        # —— Scroll Grid Area ——————————————————————————————
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #374151; background: transparent; }")
        
        grid_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(grid_widget)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

        self.cards = []

    def _load_library_roots(self):
        """Populate the library roots dropdown."""
        self._block_signals = True
        self.lib_combo.clear()
        roots = AniSnap.get_library_roots()
        for r in roots:
            # Show folder name or relative suffix
            name = os.path.basename(r) or r
            self.lib_combo.addItem(name, r)
        self._block_signals = False

    def _refresh_folders(self):
        """Populate subfolder sets dropdown."""
        self._block_signals = True
        self.folder_combo.clear()
        self.folder_combo.addItem("Root (All)", "")
        
        root_path = self.lib_combo.currentData()
        if root_path:
            rig_name = AniSnap.get_rig_name()
            subfolders = AniSnap.list_subfolders(root_path, rig_name)
            for f in subfolders:
                self.folder_combo.addItem(f, f)
        self._block_signals = False

    def _on_library_changed(self):
        if self._block_signals:
            return
        self._refresh_folders()
        self._refresh_grid()

    def _on_folder_changed(self):
        if self._block_signals:
            return
        self._refresh_grid()

    def _create_folder(self):
        """Create a new subfolder/set inside the current rig folder."""
        root_path = self.lib_combo.currentData()
        if not root_path:
            return
            
        folder_name, ok = QtWidgets.QInputDialog.getText(
            self, "New Pose Set", "Enter subfolder / pose set name:"
        )
        if ok and folder_name:
            clean = "".join([c for c in folder_name if c.isalnum() or c in ("-", "_")]).strip()
            if clean:
                rig_name = AniSnap.get_rig_name()
                AniSnap.get_pose_directory(root_path, rig_name, clean)
                self._refresh_folders()
                self.folder_combo.setCurrentText(clean)

    def _refresh_grid(self):
        """Rebuild the card grid based on files on disk."""
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.cards = []

        root_path = self.lib_combo.currentData()
        folder = self.folder_combo.currentData() or ""
        
        if not root_path:
            return

        pose_names = AniSnap.list_poses(root_path, folder)
        
        row, col = 0, 0
        cols_limit = 3

        for name in pose_names:
            img = AniSnap.get_pose_image_path(name, root_path, folder)
            card = PoseCard(name, img)
            card.clicked.connect(self._apply_pose_normal)
            card.double_clicked.connect(self._apply_pose_close)
            card.delete_requested.connect(self._delete_pose)
            card.mirror_requested.connect(self._apply_pose_mirror)
            card.offset_requested.connect(self._apply_pose_offset)

            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)

            col += 1
            if col >= cols_limit:
                col = 0
                row += 1

        self._filter_poses()

    def _filter_poses(self):
        query = self.search_input.text().strip().lower()
        for card in self.cards:
            card.setHidden(query not in card.name.lower())

    def _save_pose(self):
        root_path = self.lib_combo.currentData()
        folder = self.folder_combo.currentData() or ""
        
        if not root_path:
            return

        name, ok = QtWidgets.QInputDialog.getText(
            self, "Save Pose", "Enter pose name:", text="Pose_" + str(len(self.cards) + 1)
        )
        if ok and name:
            clean_name = "".join([c for c in name if c.isalnum() or c in ("-", "_")]).strip()
            if clean_name:
                if AniSnap.save_pose(clean_name, root_path, folder):
                    self._refresh_grid()

    def _apply_pose_normal(self, name):
        root_path = self.lib_combo.currentData()
        folder = self.folder_combo.currentData() or ""
        blend = self.blend_slider.value() / 100.0
        
        if root_path:
            AniSnap.apply_pose(name, root_path, folder, blend_factor=blend, offset_mode=False)

    def _apply_pose_close(self, name):
        self._apply_pose_normal(name)
        self.close()

    def _apply_pose_mirror(self, name):
        root_path = self.lib_combo.currentData()
        folder = self.folder_combo.currentData() or ""
        if root_path:
            AniSnap.mirror_pose(name, root_path, folder)

    def _apply_pose_offset(self, name):
        root_path = self.lib_combo.currentData()
        folder = self.folder_combo.currentData() or ""
        blend = self.blend_slider.value() / 100.0
        if root_path:
            AniSnap.apply_pose(name, root_path, folder, blend_factor=blend, offset_mode=True)

    def _delete_pose(self, name):
        root_path = self.lib_combo.currentData()
        folder = self.folder_combo.currentData() or ""
        if not root_path:
            return

        res = cmds.confirmDialog(
            title="Delete Pose",
            message="Are you sure you want to delete pose '{}'?".format(name),
            button=["Yes", "No"],
            defaultButton="No",
            cancelButton="No"
        )
        if res == "Yes":
            AniSnap.delete_pose(name, root_path, folder)
            self._refresh_grid()


# —— Global instance —————————————————————————————————————
_PANEL_INSTANCE = None


def show_panel():
    """Show the AniSnap Pose Library panel."""
    global _PANEL_INSTANCE
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.close()
        except Exception:
            pass
    _PANEL_INSTANCE = SnapPanel()
    _PANEL_INSTANCE.show()
