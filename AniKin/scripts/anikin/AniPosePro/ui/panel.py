"""
panel.py — Complete Main Window & Dockable Panel for AniPose Pro V3.1.
Connects Index Cache, Search Engine, Folder Tree, Multi-Size Grid, List View, Zone C Panel, and Save Dialogs.
"""

import os
import shutil
import json
import maya.cmds as cmds

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui, MayaQWidgetDockableMixin
from anikin.AniPosePro.ui.styles import ANIPOSE_STYLE_QSS
from anikin.AniPosePro.library.pose_library import PoseLibrary
from anikin.AniPosePro.library.index_cache import LibraryIndexCache
from anikin.AniPosePro.library.search import LibrarySearchEngine
from anikin.AniPosePro.library.folder_tree import FolderTreeWidget
from anikin.AniPosePro.library.grid_view import LibraryGridViewWidget
from anikin.AniPosePro.library.list_view import LibraryListViewWidget
from anikin.AniPosePro.ui.zone_c_panel import ZoneCPanel
from anikin.AniPosePro.ui.graph_preview import CurvePreviewWidget
from anikin.AniPosePro.ui.save_dialog import UnifiedSaveDialog
from anikin.AniPosePro.ui.mirror_editor import MirrorTableEditorDialog
from anikin.AniPosePro.core.paste_controller import AnimPasteController
from anikin.AniPosePro.history import get_history


class AniPoseProWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    """
    Main AniPose Pro V3.1 Dockable Window matching Section 11 of PRD.
    """

    def __init__(self, parent=None):
        super(AniPoseProWindow, self).__init__(parent)
        self.setWindowTitle("AniPose Pro V3.3 — Studio Library Engine")
        self.setObjectName("AniPoseProWindow")
        self.resize(420, 640)

        self.library = PoseLibrary()
        self.index_cache = LibraryIndexCache(self.library.root)
        self.search_engine = LibrarySearchEngine()

        self.current_folder = ""
        self.current_category = "all" # "all", "pose", "clip", "script", "selection"
        self.view_mode = "grid"       # "grid", "list"

        self.setStyleSheet(ANIPOSE_STYLE_QSS)

        self._build_ui()
        self._setup_connections()
        self.refresh_all()

    def _build_ui(self):
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)

        main_lay = QtWidgets.QVBoxLayout(main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── 1. Category Tab Bar ──────────────────────────────────────────────
        self.cat_tab_bar = QtWidgets.QTabBar()
        self.cat_tab_bar.setExpanding(False)
        self.cat_tab_bar.setDrawBase(False)
        self.cat_tab_bar.addTab("All")
        self.cat_tab_bar.addTab("Poses")
        self.cat_tab_bar.addTab("Clips")
        self.cat_tab_bar.addTab("Scripts")
        self.cat_tab_bar.addTab("Sets")
        self.cat_tab_bar.setCurrentIndex(0)
        self.cat_tab_bar.setStyleSheet("""
            QTabBar { background: #2E2E2E; border: none; }
            QTabBar::tab {
                background: transparent;
                color: #9A9A9A;
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 12px;
                font-weight: 600;
                min-width: 48px;
            }
            QTabBar::tab:selected {
                color: #E8E8E8;
                border-bottom: 2px solid #2FD3C2;
            }
            QTabBar::tab:hover:!selected {
                color: #E8E8E8;
                border-bottom: 2px solid #525252;
            }
        """)
        main_lay.addWidget(self.cat_tab_bar)

        # Thin separator under tabs
        tab_sep = QtWidgets.QFrame()
        tab_sep.setFixedHeight(1)
        tab_sep.setStyleSheet("background: #1F1F1F;")
        main_lay.addWidget(tab_sep)

        # ── 2. Toolbar Row ───────────────────────────────────────────────────
        toolbar = QtWidgets.QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet("background: #383838;")
        tb_lay = QtWidgets.QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(8, 4, 8, 4)
        tb_lay.setSpacing(8)

        # Search bar
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Search...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background: #454545;
                border: 1px solid #1F1F1F;
                border-radius: 4px;
                padding: 4px 8px;
                color: #E8E8E8;
                font-size: 11px;
            }
            QLineEdit:focus { border: 1px solid #2FD3C2; }
        """)
        tb_lay.addWidget(self.search_edit, stretch=1)

        # Filter funnel toggle
        self.filter_btn = QtWidgets.QPushButton("▼")
        self.filter_btn.setCheckable(True)
        self.filter_btn.setFixedSize(28, 28)
        self.filter_btn.setToolTip("Filters")
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #9A9A9A;
                border: none; font-size: 10px;
            }
            QPushButton:hover { color: #E8E8E8; }
            QPushButton:checked { color: #2FD3C2; }
        """)
        tb_lay.addWidget(self.filter_btn)

        # Separator
        sep1 = QtWidgets.QFrame()
        sep1.setFixedSize(1, 20)
        sep1.setStyleSheet("background: #525252;")
        tb_lay.addWidget(sep1)

        # ── Size Slider with Magnetic Breakpoints ────────────────────────────
        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.size_slider.setRange(0, 4)   # 5 stops: XS=0, S=1, M=2, L=3, XL=4
        self.size_slider.setValue(2)      # Default M
        self.size_slider.setFixedWidth(100)
        self.size_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.size_slider.setTickInterval(1)
        self.size_slider.setPageStep(1)
        self.size_slider.setSingleStep(1)
        self.size_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #525252;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #2FD3C2;
                width: 10px;
                height: 10px;
                margin: -3px 0;
                border-radius: 5px;
            }
            QSlider::sub-page:horizontal {
                background: #2FD3C2;
                border-radius: 2px;
            }
            QSlider::tick-mark {
                background: #9A9A9A;
            }
        """)
        tb_lay.addWidget(self.size_slider)

        # Separator
        sep2 = QtWidgets.QFrame()
        sep2.setFixedSize(1, 20)
        sep2.setStyleSheet("background: #525252;")
        tb_lay.addWidget(sep2)

        # ── Grid/List Toggle (single button) ──────────────────────────────────
        self.view_toggle_btn = QtWidgets.QPushButton("田")
        self.view_toggle_btn.setFixedSize(28, 28)
        self.view_toggle_btn.setToolTip("Toggle Grid / List")
        self.view_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #9A9A9A;
                border: none; font-size: 14px;
            }
            QPushButton:hover { color: #E8E8E8; }
        """)
        self._view_is_grid = True
        tb_lay.addWidget(self.view_toggle_btn)

        # Separator
        sep3 = QtWidgets.QFrame()
        sep3.setFixedSize(1, 20)
        sep3.setStyleSheet("background: #525252;")
        tb_lay.addWidget(sep3)

        # + Save New Button
        self.save_btn = QtWidgets.QPushButton("+ Save")
        self.save_btn.setObjectName("primary")
        self.save_btn.setFixedHeight(26)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #2FD3C2; color: #1A1A1A;
                border: none; border-radius: 4px;
                font-weight: bold; font-size: 11px;
                padding: 4px 12px;
            }
            QPushButton:hover { background: #1B7A70; }
        """)
        tb_lay.addWidget(self.save_btn)

        main_lay.addWidget(toolbar)

        # ── 2b. Filter Accordion Drawer (Hidden by default) ──────────────────
        self.filter_drawer = QtWidgets.QFrame()
        self.filter_drawer.setStyleSheet("background: #383838; border-bottom: 1px solid #1F1F1F;")
        fd_lay = QtWidgets.QHBoxLayout(self.filter_drawer)
        fd_lay.setContentsMargins(12, 6, 12, 6)
        fd_lay.setSpacing(12)

        recency_lbl = QtWidgets.QLabel("Recency:")
        recency_lbl.setStyleSheet("color: #9A9A9A; font-size: 10px;")
        fd_lay.addWidget(recency_lbl)
        self.recency_combo = QtWidgets.QComboBox()
        self.recency_combo.addItems(["All", "Today", "7 Days", "30 Days"])
        fd_lay.addWidget(self.recency_combo)

        self.chk_fav_only = QtWidgets.QCheckBox("♥ Favorites")
        self.chk_fav_only.setStyleSheet("color: #E8E8E8; font-size: 10px;")
        fd_lay.addWidget(self.chk_fav_only)

        rating_lbl = QtWidgets.QLabel("Min Rating:")
        rating_lbl.setStyleSheet("color: #9A9A9A; font-size: 10px;")
        fd_lay.addWidget(rating_lbl)
        self.rating_combo = QtWidgets.QComboBox()
        self.rating_combo.addItems(["Any", "1★", "2★", "3★", "4★", "5★"])
        fd_lay.addWidget(self.rating_combo)

        fd_lay.addStretch()
        self.filter_drawer.setVisible(False)
        main_lay.addWidget(self.filter_drawer)

        # ── 3. Main Splitter Layout ──────────────────────────────────────────
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left Zone: Folder Tree
        self.folder_tree = FolderTreeWidget(self.library.root)
        self.splitter.addWidget(self.folder_tree)

        # Center Zone: Grid View & List View
        self.center_stack = QtWidgets.QStackedWidget()
        self.grid_view = LibraryGridViewWidget()
        self.list_view = LibraryListViewWidget()
        self.center_stack.addWidget(self.grid_view)
        self.center_stack.addWidget(self.list_view)
        self.splitter.addWidget(self.center_stack)

        # Right Zone: Zone C Detail Panel
        self.zone_c = ZoneCPanel()
        self.splitter.addWidget(self.zone_c)

        self.splitter.setSizes([220, 600, 280])
        main_lay.addWidget(self.splitter, stretch=1)
        
        # ── 3.5 Curve Preview Strip ───────────────────────────────────────────
        self.curve_preview = CurvePreviewWidget()
        main_lay.addWidget(self.curve_preview)

        # ── 4. Bottom Status Bar ─────────────────────────────────────────────
        status_bar = QtWidgets.QHBoxLayout()
        self.sel_status_lbl = QtWidgets.QLabel("0 objects selected")
        self.sel_status_lbl.setStyleSheet("color: #9A9A9A; font-size: 11px;")
        status_bar.addWidget(self.sel_status_lbl)

        refresh_sel_btn = QtWidgets.QPushButton("🔄 Refresh Sel")
        refresh_sel_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #9A9A9A;
                border: 1px solid #1F1F1F; border-radius: 4px;
                font-size: 10px; padding: 2px 6px;
            }
            QPushButton:hover { background: #454545; color: #E8E8E8; border-color: #2FD3C2; }
        """)
        refresh_sel_btn.clicked.connect(self._update_selection_status)
        status_bar.addWidget(refresh_sel_btn)

        status_bar.addStretch()

        mirror_edit_btn = QtWidgets.QPushButton("⚙ MirrorTable Editor")
        mirror_edit_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #9A9A9A;
                border: 1px solid #1F1F1F; border-radius: 4px;
                font-size: 10px; padding: 2px 6px;
            }
            QPushButton:hover { background: #454545; color: #E8E8E8; border-color: #2FD3C2; }
        """)
        mirror_edit_btn.clicked.connect(self._open_mirror_editor)
        status_bar.addWidget(mirror_edit_btn)

        main_lay.addLayout(status_bar)

    def _setup_connections(self):
        # Search & Filters
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.filter_btn.toggled.connect(self.filter_drawer.setVisible)
        self.recency_combo.currentTextChanged.connect(self._on_search_changed)
        self.chk_fav_only.toggled.connect(self._on_search_changed)
        self.rating_combo.currentIndexChanged.connect(self._on_search_changed)

        # Category tab bar
        self._cat_map = {0: "all", 1: "pose", 2: "clip", 3: "script", 4: "selection"}
        self.cat_tab_bar.currentChanged.connect(self._on_cat_tab_changed)

        # Size slider (magnetic breakpoints)
        self._size_presets = ["XS", "S", "M", "L", "XL"]
        self.size_slider.valueChanged.connect(self._on_size_slider_changed)

        # View toggle (single button)
        self.view_toggle_btn.clicked.connect(self._on_view_toggle)

        # Folder Tree
        self.folder_tree.folder_selected.connect(self._on_folder_selected)
        self.folder_tree.import_requested.connect(self.refresh_all)

        # Grid / List Item selection
        self.grid_view.item_selected.connect(self._on_item_selected)
        self.grid_view.favorite_toggled.connect(self._on_favorite_toggled)
        self.grid_view.action_requested.connect(self._on_action_requested)
        self.list_view.item_selected.connect(self._on_item_selected)

        # Save Button
        self.save_btn.clicked.connect(self._open_save_dialog)

        # Zone C Actions
        self.zone_c.apply_requested.connect(self._on_zone_c_apply)
        self.zone_c.edit_info_requested.connect(self._on_edit_info)
        self.zone_c.history_restore.connect(self._on_history_restore)

    def refresh_all(self):
        self.index_cache.rebuild()
        self.folder_tree.refresh_tree()
        self._update_item_views()
        self._update_selection_status()

    def _update_item_views(self):
        # 1. Update search engine filters
        self.search_engine.query = self.search_edit.text()
        self.search_engine.recency = self.recency_combo.currentText()
        self.search_engine.favorites_only = self.chk_fav_only.isChecked()
        self.search_engine.min_rating = self.rating_combo.currentIndex()

        if self.current_category == "all":
            self.search_engine.types = {"pose", "clip", "script", "mirror", "selection"}
        else:
            self.search_engine.types = {self.current_category}

        # 2. Filter cached items
        all_items = self.index_cache.items
        if self.current_folder:
            all_items = [i for i in all_items if i.get("folder", "").startswith(self.current_folder)]

        filtered = self.search_engine.filter_items(all_items)

        # 3. Populate Grid and List
        self.grid_view.populate(filtered)
        self.list_view.populate(filtered)

    def _on_search_changed(self):
        self._update_item_views()

    def _on_cat_tab_changed(self, index: int):
        self.current_category = self._cat_map.get(index, "all")
        self._update_item_views()

    def _on_size_slider_changed(self, value: int):
        preset = self._size_presets[value]
        self.grid_view.set_size_preset(preset)
        self._update_item_views()

    def _on_view_toggle(self):
        self._view_is_grid = not self._view_is_grid
        if self._view_is_grid:
            self.center_stack.setCurrentIndex(0)
            self.view_toggle_btn.setText("田")
            self.view_toggle_btn.setToolTip("Switch to List")
        else:
            self.center_stack.setCurrentIndex(1)
            self.view_toggle_btn.setText("≡")
            self.view_toggle_btn.setToolTip("Switch to Grid")

    def _set_grid_size(self, size: str):
        """Legacy helper — maps preset name to slider position."""
        idx = self._size_presets.index(size) if size in self._size_presets else 2
        self.size_slider.setValue(idx)

    def _on_folder_selected(self, folder_rel: str):
        self.current_folder = folder_rel
        self._update_item_views()

    def _on_item_selected(self, item_dict: dict, is_double_click: bool):
        is_clip = item_dict.get("type") == "clip"
        self.zone_c.set_entry(item_dict, is_clip=is_clip)
        
        # Update Curve Preview
        path = item_dict.get("path")
        if path and os.path.exists(path):
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.curve_preview.set_data(data, is_pose=not is_clip)
            except Exception:
                self.curve_preview.set_data(None)
        else:
            self.curve_preview.set_data(None)

        if is_double_click:
            self._on_zone_c_apply("full" if not is_clip else "paste_clip")

    def _on_favorite_toggled(self, item_dict: dict, new_state: bool):
        path = item_dict.get("path")
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["favorite"] = new_state
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.index_cache.rebuild()
        except Exception as e:
            cmds.warning(f"AniPose Pro: Failed updating favorite — {e}")

    def _on_action_requested(self, action: str, item_dict: dict):
        path = item_dict.get("path")
        if not path:
            return

        if action == "rename":
            name, ok = QtWidgets.QInputDialog.getText(self, "Rename Item", "New Name:", text=item_dict.get("name", ""))
            if ok and name.strip():
                new_path = os.path.join(os.path.dirname(path), f"{name.strip()}{os.path.splitext(path)[1]}")
                os.rename(path, new_path)
                self.refresh_all()

        elif action == "copy_path":
            QtWidgets.QApplication.clipboard().setText(path)
            cmds.inViewMessage(amg="<hl>AniPose Pro</hl>: File path copied to clipboard.", pos="topCenter", fade=True, fadeStayTime=1500)

        elif action == "delete":
            confirm = QtWidgets.QMessageBox.question(self, "Delete Item", f"Delete '{item_dict.get('name')}'?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if confirm == QtWidgets.QMessageBox.Yes:
                try:
                    os.remove(path)
                    # Also remove thumbnail
                    t_path = item_dict.get("thumbnail")
                    if t_path and os.path.exists(t_path):
                        os.remove(t_path)
                except Exception:
                    pass
                self.refresh_all()

        elif action == "edit_thumbnail":
            is_clip = item_dict.get("type") == "clip"
            thumb_path = item_dict.get("thumbnail")
            
            if not thumb_path:
                # Need a fallback path if it doesn't exist
                base = os.path.splitext(path)[0]
                thumb_path = base + (".gif" if is_clip else ".jpg")
                item_dict["thumbnail"] = thumb_path
                # Write to meta json
                meta_path = base + ".meta.json"
                if os.path.exists(meta_path):
                    import json
                    with open(meta_path, "r") as f:
                        m = json.load(f)
                    m["thumbnail"] = thumb_path
                    with open(meta_path, "w") as f:
                        json.dump(m, f, indent=4)

            success = False
            if not is_clip:
                from anikin.AniPosePro.thumbnail import capture_viewport_thumbnail
                success = capture_viewport_thumbnail(thumb_path, 256, 192)
            else:
                from anikin.AniPosePro.thumbnail import capture_clip_thumbnail_gif
                meta = item_dict.get("meta", {})
                start_frame = meta.get("start", int(cmds.playbackOptions(q=True, min=True)))
                end_frame = meta.get("end", int(cmds.playbackOptions(q=True, max=True)))
                
                # Pop dialog for range
                dlg = QtWidgets.QDialog(self)
                dlg.setWindowTitle("Recapture Clip Thumbnail")
                lay = QtWidgets.QFormLayout(dlg)
                s_spin = QtWidgets.QSpinBox(); s_spin.setRange(-100000, 100000); s_spin.setValue(start_frame)
                e_spin = QtWidgets.QSpinBox(); e_spin.setRange(-100000, 100000); e_spin.setValue(end_frame)
                lay.addRow("Start:", s_spin)
                lay.addRow("End:", e_spin)
                bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
                bb.accepted.connect(dlg.accept)
                bb.rejected.connect(dlg.reject)
                lay.addRow(bb)
                
                if dlg.exec_() == QtWidgets.QDialog.Accepted:
                    s = s_spin.value()
                    e = e_spin.value()
                    # Capture GIF
                    if capture_clip_thumbnail_gif(s, e, thumb_path, 256, 192, 15):
                        success = True

            if success:
                cmds.inViewMessage(amg="<hl>AniPose Pro</hl>: Thumbnail updated.", pos="topCenter", fade=True, fadeStayTime=1500)
                self.refresh_all()
            else:
                cmds.inViewMessage(amg="<hl>AniPose Pro</hl>: Capture failed — viewport not visible or cancelled.", pos="topCenter", fade=True, fadeStayTime=2500)

        elif action == "pose_to_clip_bridge":
            # Converts a pose item into a 1-frame animation clip
            nodes = cmds.ls(selection=True, long=True) or []
            if nodes:
                from anikin.AniPosePro.core.curve_serializer import serialize_clip
                frame = cmds.currentTime(q=True)
                c_data = serialize_clip(nodes, frame, frame)
                clip_path = path.rsplit(".", 1)[0] + ".clip"
                with open(clip_path, "w") as f:
                    json.dump(c_data, f, indent=4)
                self.refresh_all()

    def _open_save_dialog(self):
        nodes = cmds.ls(selection=True, long=True) or []
        if not nodes:
            cmds.warning("AniPose Pro: Select controls in scene to capture/save.")
            return

        default_type = self.current_category if self.current_category in ["pose", "clip", "script", "selection"] else "pose"
        dlg = UnifiedSaveDialog(item_type=default_type, target_folder=self.current_folder, parent=self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            data = dlg.get_data()
            name = data["name"]
            item_type = data.get("item_type", "pose")
            folder_dir = os.path.join(self.library.root, self.current_folder) if self.current_folder else self.library.root
            os.makedirs(folder_dir, exist_ok=True)

            if item_type == "clip":
                from anikin.AniPosePro.capture import capture_anim_clip, save_clip_to_disk
                s = data.get("frame_start", int(cmds.playbackOptions(q=True, min=True)))
                e = data.get("frame_end", int(cmds.playbackOptions(q=True, max=True)))

                clip_data = capture_anim_clip(nodes, s, e)
                out_file = os.path.join(folder_dir, f"{name}.animclip")

                save_clip_to_disk(
                    clip_data,
                    out_file,
                    name=name,
                    tags=data.get("tags"),
                    notes=data.get("notes")
                )

                # Update sidecar metadata with color & rating
                meta_path = os.path.join(folder_dir, f"{name}.meta.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            m = json.load(f)
                        m["color"] = data.get("color", "#3a9e6e")
                        m["rating"] = data.get("rating", 4)
                        with open(meta_path, "w", encoding="utf-8") as f:
                            json.dump(m, f, indent=4)
                    except Exception:
                        pass

                # Copy thumbnail preview gif if captured
                if data.get("temp_thumb") and os.path.exists(data["temp_thumb"]):
                    try:
                        dest_thumb = os.path.join(folder_dir, f"{name}.gif")
                        shutil.copy(data["temp_thumb"], dest_thumb)
                    except Exception:
                        pass

            else:  # Pose
                self.library.save_pose(
                    nodes,
                    name,
                    folder=self.current_folder,
                    tags=data.get("tags"),
                    notes=data.get("notes"),
                    rating=data.get("rating", 4)
                )

            self.refresh_all()

    def _open_mirror_editor(self):
        dlg = MirrorTableEditorDialog(parent=self)
        dlg.exec_()

    def _on_zone_c_apply(self, mode: str):
        entry = self.zone_c._current_entry
        if not entry:
            return

        nodes = cmds.ls(selection=True, long=True) or []
        if not nodes:
            cmds.warning("AniPose Pro: Select controls to apply.")
            return

        path = entry.get("path", "")

        if entry.get("type") == "clip":
            if mode == "paste_clip":
                # Load real clip data and arm the paste controller
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        clip_data = json.load(f)
                    paste_ctrl = AnimPasteController.instance()
                    paste_ctrl.arm(clip_data, {"mode": "replace"})
                    paste_ctrl.execute_paste(cmds.currentTime(q=True), selected_nodes=nodes)
                except Exception as e:
                    cmds.warning(f"AniPose Pro: Failed to paste clip — {e}")
        else:  # Pose
            try:
                with open(path, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
            except Exception as e:
                cmds.warning(f"AniPose Pro: Failed to read pose file — {e}")
                return

            if mode == "full":
                from anikin.AniPosePro.apply import apply_pose_full
                apply_pose_full(p_data, nodes)
            elif mode == "keyframe":
                from anikin.AniPosePro.apply import apply_pose_full
                apply_pose_full(p_data, nodes, as_keyframe=True)
            elif mode == "mirror":
                from anikin.AniPosePro.apply import apply_pose_mirror
                apply_pose_mirror(p_data, nodes)
            elif mode == "additive":
                from anikin.AniPosePro.apply import apply_pose_additive
                apply_pose_additive(p_data, nodes)

        self.zone_c.refresh_history()

    def _on_edit_info(self):
        entry = self.zone_c._current_entry
        if not entry:
            return
        meta = entry.get("meta", {})
        meta_path = entry["path"].rsplit(".", 1)[0] + ".meta"

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Edit Metadata")
        lay = QtWidgets.QFormLayout(dlg)

        rig_e = QtWidgets.QLineEdit(meta.get("rig_hint", meta.get("rig", "")))
        tags_e = QtWidgets.QLineEdit(", ".join(meta.get("tags", [])))
        notes_e = QtWidgets.QLineEdit(meta.get("notes", ""))

        lay.addRow("Rig:", rig_e)
        lay.addRow("Tags:", tags_e)
        lay.addRow("Notes:", notes_e)

        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addRow(bb)

        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            meta["rig_hint"] = rig_e.text()
            meta["tags"] = [t.strip() for t in tags_e.text().split(",") if t.strip()]
            meta["notes"] = notes_e.text()
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=4)
            self.refresh_all()

    def _on_history_restore(self, index: int):
        get_history().restore_index(index)

    def _update_selection_status(self):
        sel = cmds.ls(selection=True, long=True) or []
        count = len(sel)
        self.sel_status_lbl.setText(f"{count} objects selected")


_PANEL_INSTANCE = None


def show_panel():
    global _PANEL_INSTANCE
    is_deleted = False
    if _PANEL_INSTANCE is not None:
        try:
            _PANEL_INSTANCE.windowTitle()
        except RuntimeError:
            is_deleted = True

    if _PANEL_INSTANCE is None or is_deleted:
        _PANEL_INSTANCE = AniPoseProWindow()

    try:
        _PANEL_INSTANCE.show(dockable=True, floating=True, area="right", allowedArea="all", width=420, height=640)
    except Exception:
        _PANEL_INSTANCE.show()

    _PANEL_INSTANCE.raise_()
    _PANEL_INSTANCE.activateWindow()
