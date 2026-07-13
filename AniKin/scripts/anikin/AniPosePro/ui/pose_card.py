"""
pose_card.py — Individual pose card widget for AniPose Pro grid view.
"""

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui
from anikin.core.qt_compat import MIDDLE_BUTTON

import maya.cmds as cmds
import json
import os

from anikin.AniPosePro.apply import (
    apply_pose_full, apply_pose_partial, apply_pose_mirror, apply_pose_additive,
    begin_blend, update_blend, commit_blend, cancel_blend
)


class PoseCard(QtWidgets.QFrame):
    def __init__(self, pose_entry, parent=None):
        super(PoseCard, self).__init__(parent)
        self._entry = pose_entry
        self._blend_start_x = None
        self.setFixedSize(130, 150)
        self.setToolTip(pose_entry.get("name", ""))
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        self.setStyleSheet("""
            PoseCard {
                background-color: #2a2a2a;
                border: 1px solid #333;
                border-radius: 4px;
            }
            PoseCard:hover {
                border: 1px solid #d4860a;
                background-color: #333;
            }
        """)
        
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Thumbnail
        self.thumb_label = QtWidgets.QLabel()
        self.thumb_label.setFixedSize(126, 110)
        self.thumb_label.setAlignment(QtCore.Qt.AlignCenter)
        
        thumb_path = self._entry.get("thumb")
        if thumb_path and os.path.exists(thumb_path):
            pix = QtGui.QPixmap(thumb_path)
            # Scale and crop to square
            pix = pix.scaled(126, 110, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            self.thumb_label.setPixmap(pix)
        else:
            self.thumb_label.setText("No Preview")
            self.thumb_label.setStyleSheet("background: #1a1a1a; color: #666; font-size: 10px;")
            
        layout.addWidget(self.thumb_label)

        # Name label
        name_str = self._entry.get("name", "")
        self.name_label = QtWidgets.QLabel(name_str)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 10px; color: #ccc; border: none; background: transparent;")
        
        # Rig Tag / Additive Badge (Optional overlays)
        meta = self._entry.get("meta", {})
        if meta.get("is_additive"):
            self.name_label.setText(f"[Δ] {name_str}")
            self.name_label.setStyleSheet("font-size: 10px; color: #4CAF50; border: none; background: transparent;")
            
        layout.addWidget(self.name_label)

    # ── Interaction ────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # Full apply on click
            self._apply_pose()
        elif event.button() == MIDDLE_BUTTON:
            # Begin MMB Blend
            self._blend_start_x = event.x()
            nodes = cmds.ls(selection=True, long=True) or []
            if not nodes:
                cmds.warning("AniPose Pro: Select objects to blend pose.")
                return
            try:
                with open(self._entry["path"], "r") as f:
                    pose_data = json.load(f)
                begin_blend(pose_data, nodes)
            except Exception as e:
                cmds.warning(f"AniPose Pro: Failed to read pose data for blend: {e}")

    def mouseMoveEvent(self, event):
        if self._blend_start_x is not None:
            delta = event.x() - self._blend_start_x
            # Map +/- 100px drag to 0.0 -> 1.0 blend range
            # Base is 0.0 (current pose), drag right approaches 1.0 (library pose)
            # Actually, standard behavior: press = 0%, drag right = 100%
            t = max(0.0, min(1.0, delta / 150.0))
            update_blend(t)
            
            # Show overlay tooltip
            QtWidgets.QToolTip.showText(event.globalPos(), f"Blend: {int(t*100)}%")

    def mouseReleaseEvent(self, event):
        if event.button() == MIDDLE_BUTTON and self._blend_start_x is not None:
            delta = event.x() - self._blend_start_x
            t = max(0.0, min(1.0, delta / 150.0))
            commit_blend(t)
            self._blend_start_x = None
            QtWidgets.QToolTip.hideText()

    # ── Context Menu ───────────────────────────────────────────────────────────
    
    def _show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        
        apply_action = menu.addAction("Apply Pose")
        apply_key_action = menu.addAction("Apply as Keyframe")
        mirror_action = menu.addAction("Mirror Apply")
        additive_action = menu.addAction("Additive Apply")
        menu.addSeparator()
        compare_action = menu.addAction("Compare (WIP)")
        menu.addSeparator()
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec_(self.mapToGlobal(pos))
        
        if action == apply_action:
            self._apply_pose()
        elif action == apply_key_action:
            self._apply_as_key()
        elif action == mirror_action:
            self._mirror_apply()
        elif action == additive_action:
            self._additive_apply()
        elif action == rename_action:
            self._rename()
        elif action == delete_action:
            self._delete()

    # ── Actions ────────────────────────────────────────────────────────────────

    def _get_pose_data(self):
        try:
            with open(self._entry["path"], "r") as f:
                return json.load(f)
        except Exception as e:
            cmds.warning(f"AniPose Pro: Failed to read pose data: {e}")
            return None

    def _apply_pose(self):
        data = self._get_pose_data()
        if data:
            nodes = cmds.ls(selection=True, long=True) or []
            apply_pose_full(data, nodes, pose_name=self._entry.get("name", "pose"))

    def _apply_as_key(self):
        data = self._get_pose_data()
        if data:
            nodes = cmds.ls(selection=True, long=True) or []
            apply_pose_full(data, nodes, as_keyframe=True, pose_name=self._entry.get("name", "pose"))

    def _mirror_apply(self):
        data = self._get_pose_data()
        if data:
            nodes = cmds.ls(selection=True, long=True) or []
            apply_pose_mirror(data, nodes, pose_name=self._entry.get("name", "pose"))

    def _additive_apply(self):
        data = self._get_pose_data()
        if data:
            nodes = cmds.ls(selection=True, long=True) or []
            apply_pose_additive(data, nodes, pose_name=self._entry.get("name", "pose"))

    def _rename(self):
        # Fire signal to parent panel to handle rename
        pass
        
    def _delete(self):
        # Fire signal to parent panel to handle delete
        pass
