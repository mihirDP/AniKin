"""
panel.py — Main UI for AniPose Pro.
"""

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui, get_maya_main_window
import maya.cmds as cmds
import os

from anikin.AniPosePro.library import PoseLibrary
from anikin.AniPosePro.history import get_history
from anikin.AniPosePro.quick_snap import QuickSnapManager
from anikin.AniPosePro.ui.pose_card import PoseCard

class FlowLayout(QtWidgets.QLayout):
    """Simple FlowLayout for the pose grid."""
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


class AniPoseProWindow(QtWidgets.QDialog):
    """
    The main AniPose Pro panel. Can be docked or a standalone window.
    """
    
    def __init__(self, parent=None):
        super(AniPoseProWindow, self).__init__(parent or get_maya_main_window())
        self.setWindowTitle("AniPose Pro")
        self.resize(800, 600)
        
        # Determine library root from settings or use default
        try:
            from anikin.core.settings import load_settings
            cfg = load_settings()
            root_path = cfg.get("pose_library_roots", [os.path.join(os.path.expanduser("~"), "anikin_poses")])[0]
        except Exception:
            root_path = os.path.join(os.path.expanduser("~"), "anikin_poses")
            
        self.library = PoseLibrary(root_path)
        self.quick_snap = QuickSnapManager()
        self.current_folder = ""
        
        self._build_ui()
        self.refresh_grid()

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # ── Top Bar ───────────────────────────────────────────────────────────
        top_bar = QtWidgets.QHBoxLayout()
        
        lbl = QtWidgets.QLabel("<b>Library:</b>")
        self.lib_combo = QtWidgets.QComboBox()
        self.lib_combo.addItem("Local (Default)")
        
        self.new_folder_btn = QtWidgets.QPushButton("+ New Folder")
        self.new_folder_btn.clicked.connect(self._create_folder)
        
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search poses... 🔍")
        self.search_bar.textChanged.connect(self.refresh_grid)
        
        top_bar.addWidget(lbl)
        top_bar.addWidget(self.lib_combo)
        top_bar.addWidget(self.new_folder_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.search_bar)
        
        main_layout.addLayout(top_bar)
        
        # ── Splitter (Folders / Grid) ──────────────────────────────────────────
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # Left: Folder Tree
        self.folder_tree = QtWidgets.QTreeWidget()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.itemClicked.connect(self._on_folder_selected)
        splitter.addWidget(self.folder_tree)
        
        # Right: Grid View + Action Bar
        grid_widget = QtWidgets.QWidget()
        grid_layout = QtWidgets.QVBoxLayout(grid_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Grid Toolbar
        grid_toolbar = QtWidgets.QHBoxLayout()
        self.save_pose_btn = QtWidgets.QPushButton("+ Save Pose")
        self.save_pose_btn.setStyleSheet("background-color: #d4860a; color: white; font-weight: bold;")
        self.save_pose_btn.clicked.connect(self._save_pose_dialog)
        grid_toolbar.addWidget(self.save_pose_btn)
        grid_toolbar.addStretch()
        
        grid_layout.addLayout(grid_toolbar)
        
        # Scroll Area for FlowLayout
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QtWidgets.QWidget()
        self.flow_layout = FlowLayout(self.scroll_widget, margin=4, spacing=4)
        self.scroll_area.setWidget(self.scroll_widget)
        
        grid_layout.addWidget(self.scroll_area)
        
        splitter.addWidget(grid_widget)
        splitter.setSizes([200, 600])
        
        main_layout.addWidget(splitter, stretch=1)
        
        # ── History & Quick Snap Bar ───────────────────────────────────────────
        bottom_bar = QtWidgets.QHBoxLayout()
        
        # History
        self.history_btn = QtWidgets.QPushButton("↩ Restore Previous")
        self.history_btn.clicked.connect(self._restore_history)
        self.history_lbl = QtWidgets.QLabel("History empty")
        
        bottom_bar.addWidget(self.history_btn)
        bottom_bar.addWidget(self.history_lbl)
        bottom_bar.addStretch()
        
        # Quick Snap
        qs_lbl = QtWidgets.QLabel("<b>Quick Snap:</b>")
        bottom_bar.addWidget(qs_lbl)
        
        for slot in ["A", "B", "C", "D", "E"]:
            btn = QtWidgets.QPushButton(slot)
            btn.setFixedSize(30, 24)
            # Use lambda default argument to capture slot
            btn.clicked.connect(lambda _, s=slot: self._quick_snap_action(s))
            bottom_bar.addWidget(btn)
            
        self.snap_capture_btn = QtWidgets.QPushButton("+ Snap")
        self.snap_capture_btn.clicked.connect(self._quick_snap_capture)
        bottom_bar.addWidget(self.snap_capture_btn)
        
        main_layout.addLayout(bottom_bar)
        
        self._refresh_folders()
        self._update_history_label()

    # ── Folder Logic ───────────────────────────────────────────────────────────
    
    def _refresh_folders(self):
        self.folder_tree.clear()
        
        root_item = QtWidgets.QTreeWidgetItem(["/ (Root)"])
        root_item.setData(0, QtCore.Qt.UserRole, "")
        self.folder_tree.addTopLevelItem(root_item)
        
        folders = self.library.list_folders()
        
        # Simplistic flat insertion for now
        for f in folders:
            item = QtWidgets.QTreeWidgetItem([f"📁 {f}"])
            item.setData(0, QtCore.Qt.UserRole, f)
            root_item.addChild(item)
            
        root_item.setExpanded(True)

    def _create_folder(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and text:
            path = os.path.join(self.current_folder, text)
            self.library.create_folder(path)
            self._refresh_folders()

    def _on_folder_selected(self, item, column):
        self.current_folder = item.data(0, QtCore.Qt.UserRole)
        self.refresh_grid()

    # ── Grid Logic ─────────────────────────────────────────────────────────────
    
    def refresh_grid(self):
        # Clear existing
        while self.flow_layout.count():
            child = self.flow_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        search = self.search_bar.text()
        poses = self.library.list_poses(folder=self.current_folder, search=search)
        
        for p in poses:
            card = PoseCard(p, self.scroll_widget)
            self.flow_layout.addItem(QtWidgets.QWidgetItem(card))
            card.show()
            
        self.scroll_widget.updateGeometry()

    def _save_pose_dialog(self):
        nodes = cmds.ls(selection=True, long=True) or []
        if not nodes:
            cmds.warning("AniPose Pro: Select controls to save.")
            return
            
        name, ok = QtWidgets.QInputDialog.getText(self, "Save Pose", "Pose Name:")
        if ok and name:
            self.library.save_pose(nodes, name, folder=self.current_folder)
            self.refresh_grid()

    # ── History & Quick Snap ───────────────────────────────────────────────────

    def _update_history_label(self):
        h = get_history()
        count = len(h)
        if count == 0:
            self.history_lbl.setText("History empty")
        else:
            entries = h.get_entries()
            last_label = entries[-1][1]
            self.history_lbl.setText(f"[{count} states deep] - {last_label}")

    def _restore_history(self):
        get_history().pop()
        self._update_history_label()

    def _quick_snap_action(self, slot):
        # Restore slot
        self.quick_snap.restore(slot)
        
    def _quick_snap_capture(self):
        # We need a slot to capture to. Let's just ask for one, or default to A
        slot, ok = QtWidgets.QInputDialog.getItem(self, "Quick Snap", "Select Slot:", ["A", "B", "C", "D", "E"], 0, False)
        if ok and slot:
            self.quick_snap.snap(slot)

    # ── Events ─────────────────────────────────────────────────────────────────
    
    def showEvent(self, event):
        super(AniPoseProWindow, self).showEvent(event)
        # Update history label on show in case it changed
        self._update_history_label()


# ── Global instance ────────────────────────────────────────────────────────────

_PANEL_INSTANCE = None

def show_panel():
    global _PANEL_INSTANCE
    
    # Safely check if C++ object was destroyed by Maya
    is_deleted = False
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.windowTitle()
        except RuntimeError:
            is_deleted = True
            
    if _PANEL_INSTANCE is None or is_deleted:
        _PANEL_INSTANCE = AniPoseProWindow()
        
    _PANEL_INSTANCE.show()
    _PANEL_INSTANCE.raise_()
    _PANEL_INSTANCE.activateWindow()
