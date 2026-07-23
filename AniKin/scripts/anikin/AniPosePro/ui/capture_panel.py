"""
capture_panel.py — CLIPS tab panel for AniPose Pro V2 (F-AC-03/06).

Contains:
  - Clip Slots bar (A-E quick capture slots)
  - CaptureTimelineStrip (click-to-paste / shift-drag range select)
  - Save Clip button
  - Graph Editor selection filter (F-NEW-04)
"""

import os
import re

from anikin.core.qt_compat import QtWidgets, QtCore, QtGui
from anikin.AniPosePro.ui.capture_timeline_strip import CaptureTimelineStrip
from anikin.AniPosePro.clip_slots import get_clip_slots, SLOT_NAMES

import maya.cmds as cmds


class CapturePanel(QtWidgets.QWidget):
    """
    Top bar for the CLIPS tab.
    Houses clip slot buttons, timeline strip, and save/capture controls.
    """

    clip_saved = QtCore.Signal()          # Refresh grid after save
    slot_activated = QtCore.Signal(dict)  # clip_data from a slot

    def __init__(self, library=None, parent=None):
        super(CapturePanel, self).__init__(parent)
        self._library = library
        self.current_folder = ""
        self._pending_range = None  # (start, end) from mini-timeline strip
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── Clip Slots Row ────────────────────────────────────────────────
        slots_row = QtWidgets.QHBoxLayout()
        slots_row.setSpacing(4)

        lbl = QtWidgets.QLabel("<b>Clip Slots:</b>")
        lbl.setStyleSheet("color: #aaa; border: none; background: none;")
        slots_row.addWidget(lbl)

        self._slot_btns = {}
        for slot in SLOT_NAMES:
            btn = QtWidgets.QPushButton(slot)
            btn.setFixedSize(50, 24)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2a2e36; color: #888;
                    border: 1px solid #3a3e46; border-radius: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background: #363a42; color: #4da6ff;
                    border-color: #4da6ff;
                }
            """)
            btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            btn.clicked.connect(lambda _, s=slot: self._on_slot_click(s))
            btn.customContextMenuRequested.connect(
                lambda pos, s=slot, b=btn: self._slot_context(pos, s, b))
            slots_row.addWidget(btn)
            self._slot_btns[slot] = btn

        slots_row.addStretch()

        # Capture button
        self.capture_btn = QtWidgets.QPushButton("⚡ Capture to Slot")
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background: #1a6bc4; color: white; font-weight: bold;
                border: none; border-radius: 4px; padding: 4px 10px;
            }
            QPushButton:hover { background: #2080e0; }
        """)
        self.capture_btn.clicked.connect(self._capture_to_slot)
        slots_row.addWidget(self.capture_btn)

        layout.addLayout(slots_row)

        # ── Timeline Strip ────────────────────────────────────────────────
        self.timeline = CaptureTimelineStrip()
        self.timeline.range_selected.connect(self._on_range_selected)
        self.timeline.paste_at_frame.connect(self._on_paste_at_frame)
        layout.addWidget(self.timeline)

        # ── Save Clip Row ─────────────────────────────────────────────────
        save_row = QtWidgets.QHBoxLayout()

        self.range_label = QtWidgets.QLabel("Range: —")
        self.range_label.setStyleSheet(
            "color: #888; font-size: 10px; border: none; background: none;")
        save_row.addWidget(self.range_label)

        save_row.addStretch()

        # F-NEW-04: Graph Editor Selection
        self.ge_check = QtWidgets.QCheckBox("Capture GE Selection Only")
        self.ge_check.setStyleSheet("color: #aaa; font-size: 10px;")
        self.ge_check.setToolTip(
            "When checked, only animation curves currently selected\n"
            "in the Graph Editor will be captured.\n"
            "Leave unchecked to capture ALL animated channels.")
        save_row.addWidget(self.ge_check)

        self.save_clip_btn = QtWidgets.QPushButton("💾 Save Clip to Library")
        self.save_clip_btn.setStyleSheet("""
            QPushButton {
                background: #2a2e36; color: #aaa;
                border: 1px solid #3a3e46; border-radius: 4px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background: #363a42; color: #d4860a;
                border-color: #d4860a;
            }
        """)
        self.save_clip_btn.clicked.connect(self._save_clip_to_library)
        save_row.addWidget(self.save_clip_btn)

        layout.addLayout(save_row)

        self._refresh_slot_labels()

    # ── Range helpers ─────────────────────────────────────────────────────

    def _get_effective_range(self):
        """
        Return (start, end) tuple.
        Priority:
          1. AniPose mini-timeline Shift+drag range
          2. Maya's native timeline red Shift+drag range
          3. Maya's playback range if it differs from the animation range
          4. None — no valid range found
        """
        # 1. AniPose internal strip range
        if self._pending_range is not None:
            return self._pending_range

        try:
            # 2. Maya's native red highlight range (Shift+drag on timeline)
            import maya.mel as mel
            slider = mel.eval('$tmpVar=$gPlayBackSlider')
            range_visible = cmds.timeControl(slider, q=True, rangeVisible=True)
            if range_visible:
                rng = cmds.timeControl(slider, q=True, rangeArray=True)
                if len(rng) >= 2 and int(rng[1]) > int(rng[0]):
                    return (int(rng[0]), int(rng[1]))
        except Exception:
            pass

        try:
            # 3. Green playback range vs grey animation range
            hs = cmds.playbackOptions(q=True, min=True)
            he = cmds.playbackOptions(q=True, max=True)
            rs = cmds.playbackOptions(q=True, animationStartTime=True)
            re = cmds.playbackOptions(q=True, animationEndTime=True)
            if (hs != rs or he != re):
                return (int(hs), int(he))
        except Exception:
            pass

        return None

    def _get_ge_curves(self):
        """Return Graph Editor selected curve nodes, or None."""
        if not self.ge_check.isChecked():
            return None
        try:
            curves = cmds.keyframe(q=True, selected=True, name=True)
            if curves:
                return curves
        except Exception:
            pass
        cmds.warning("AniPose Pro: No curves selected in Graph Editor.")
        return "ABORT"  # sentinel to abort capture

    # ── Slot Actions ──────────────────────────────────────────────────────

    def _on_slot_click(self, slot):
        """Click on a slot button activates it for paste."""
        mgr = get_clip_slots()
        data = mgr.get_slot_data(slot)
        if data:
            self.timeline.set_active_clip(data)
            self.slot_activated.emit(data)
            cmds.inViewMessage(
                amg="<hl>AniPose Pro</hl>: Slot [{}] active — "
                    "click timeline to paste".format(slot),
                pos="topCenter", fade=True, fadeStayTime=1200)
        else:
            cmds.warning(
                "AniPose Pro: Slot [{}] is empty.".format(slot))

    def _capture_to_slot(self):
        """Capture current range to a slot."""
        effective = self._get_effective_range()
        if effective is None:
            cmds.warning(
                "AniPose Pro: Select a range first. "
                "Shift-drag on the AniPose mini-timeline, or "
                "Shift-drag on Maya's main timeline.")
            return

        nodes = cmds.ls(selection=True, long=True) or []
        if not nodes:
            cmds.warning("AniPose Pro: Select controls to capture.")
            return

        # Pick a slot
        slot, ok = QtWidgets.QInputDialog.getItem(
            self, "Capture to Slot", "Select Slot:",
            SLOT_NAMES, 0, False)
        if not ok:
            return

        # F-NEW-04
        ge_curves = self._get_ge_curves()
        if ge_curves == "ABORT":
            return
        import importlib
        import anikin.AniPosePro.capture
        importlib.reload(anikin.AniPosePro.capture)
        from anikin.AniPosePro.capture import capture_anim_clip
        clip_data = capture_anim_clip(
            nodes, effective[0], effective[1],
            graph_editor_curves=ge_curves)

        if not clip_data.get("controls"):
            cmds.warning(
                "AniPose Pro: No animation data found on selected "
                "controls in the given range.")
            return

        mgr = get_clip_slots()
        mgr._slots[slot] = {
            "timestamp": QtCore.QTime.currentTime().toString("HH:mm:ss"),
            "frame_range": "{}-{}".format(int(effective[0]), int(effective[1])),
            "clip_data": clip_data,
        }
        mgr._persist()

        cmds.inViewMessage(
            amg="<hl>AniPose Pro</hl>: Clip Slot [{}] captured "
                "({}-{})".format(slot, int(effective[0]), int(effective[1])),
            pos="topCenter", fade=True, fadeStayTime=1200
        )
        self._refresh_slot_labels()
        self.range_label.setText(
            "Range: {} \u2013 {} ({} frames)".format(
                int(effective[0]), int(effective[1]),
                int(effective[1]) - int(effective[0])))

    def _slot_context(self, pos, slot, btn):
        menu = QtWidgets.QMenu(self)
        promote = menu.addAction("\U0001f4c1 Promote to Library")
        clear = menu.addAction("\U0001f5d1 Clear Slot")

        action = menu.exec_(btn.mapToGlobal(pos))
        if action == promote:
            self._promote_slot(slot)
        elif action == clear:
            get_clip_slots().clear_slot(slot)
            self._refresh_slot_labels()

    def _promote_slot(self, slot):
        if self._library is None:
            return
        mgr = get_clip_slots()
        if mgr.get_slot_data(slot) is None:
            cmds.warning("AniPose Pro: Slot [{}] is empty.".format(slot))
            return

        name, ok = QtWidgets.QInputDialog.getText(
            self, "Save Clip", "Clip Name:")
        if ok and name:
            mgr.promote_to_library(self._library, slot, name)
            self.clip_saved.emit()

    def _refresh_slot_labels(self):
        mgr = get_clip_slots()
        for slot in SLOT_NAMES:
            ts, fr = mgr.get_slot_info(slot)
            btn = self._slot_btns[slot]
            if ts:
                btn.setText("{}: {}".format(slot, fr))
                btn.setStyleSheet("""
                    QPushButton {
                        background: #1a3a5c; color: #4da6ff;
                        border: 1px solid #4da6ff; border-radius: 3px;
                        font-size: 9px;
                    }
                    QPushButton:hover { background: #2a4a6c; }
                """)
            else:
                btn.setText(slot)
                btn.setStyleSheet("""
                    QPushButton {
                        background: #2a2e36; color: #888;
                        border: 1px solid #3a3e46; border-radius: 3px;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        background: #363a42; color: #4da6ff;
                        border-color: #4da6ff;
                    }
                """)

    # ── Timeline Events ───────────────────────────────────────────────────

    def _on_range_selected(self, start, end):
        self._pending_range = (start, end)
        self.range_label.setText(
            "Range: {} \u2013 {} ({} frames)".format(
                start, end, end - start))

    def _on_paste_at_frame(self, frame):
        """
        One-click paste — the signature V2 interaction.
        Pastes the active clip at the clicked frame.
        """
        clip_data = self.timeline._active_clip
        if clip_data is None:
            return

        nodes = cmds.ls(selection=True, long=True) or []
        if not nodes:
            cmds.warning("AniPose Pro: Select controls to paste onto.")
            return

        from anikin.AniPosePro.paste import paste_clip_at_frame
        paste_clip_at_frame(clip_data, nodes, frame)

    # ── Save Clip ─────────────────────────────────────────────────────────

    def _save_clip_to_library(self):
        """Full save-to-library flow with validation at every step."""

        # 1. Range
        effective = self._get_effective_range()
        if effective is None:
            cmds.warning(
                "AniPose Pro: Select a range first. "
                "Shift-drag on the AniPose mini-timeline, or "
                "Shift-drag on Maya's main timeline.")
            return

        if self._library is None:
            cmds.warning("AniPose Pro: No library loaded.")
            return

        # 2. Selection
        nodes = cmds.ls(selection=True, long=True) or []
        if not nodes:
            cmds.warning("AniPose Pro: Select controls to capture.")
            return

        # 3. Name
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Save Clip", "Clip Name:")
        if not ok or not name.strip():
            return
        name = name.strip()

        # 4. GE filter
        ge_curves = self._get_ge_curves()
        if ge_curves == "ABORT":
            return

        # 5. Defer the heavy lifting to avoid Evaluation Manager UI crashes
        import maya.utils as mu
        mu.executeDeferred(lambda: self._do_deferred_save(nodes, effective, name, ge_curves))

    def _do_deferred_save(self, nodes, effective, name, ge_curves):
        import importlib
        import anikin.AniPosePro.capture
        importlib.reload(anikin.AniPosePro.capture)
        from anikin.AniPosePro.capture import (
            capture_anim_clip, save_clip_to_disk, ANIMCLIP_EXT
        )
        import re
        import os

        # 6. Capture
        try:
            clip_data = capture_anim_clip(
                nodes, effective[0], effective[1],
                graph_editor_curves=ge_curves)
        except Exception as e:
            cmds.warning("AniPose Pro: Capture failed - {}".format(e))
            return

        if not clip_data.get("controls"):
            cmds.warning(
                "AniPose Pro: No animation data found on selected "
                "controls in range {}-{}.".format(
                    int(effective[0]), int(effective[1])))
            return

        # 7. Write to disk
        safe = re.sub(r"[^\w\-]", "_", name).lower()
        folder_path = (os.path.join(self._library.root, self.current_folder)
                       if self.current_folder else self._library.root)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            output = os.path.join(folder_path, safe + ANIMCLIP_EXT)
            save_clip_to_disk(clip_data, output, name=name)
        except Exception as e:
            cmds.warning("AniPose Pro: Failed to save file to disk - {}".format(e))
            return

        # 8. Thumbnail (non-fatal)
        try:
            from anikin.AniPosePro.thumbnail import (
                capture_clip_thumbnail_gif
            )
            gif_path = output.replace(ANIMCLIP_EXT, ".thumb.gif")
            capture_clip_thumbnail_gif(
                effective[0], effective[1], gif_path)
        except Exception:
            pass

        # 9. Refresh
        cmds.inViewMessage(
            amg="<hl>AniPose Pro</hl>: Clip '{}' saved to library".format(name),
            pos="topCenter", fade=True, fadeStayTime=1500)

        self.clip_saved.emit()

    # ── Public API ────────────────────────────────────────────────────────

    def set_active_clip(self, clip_data):
        """Set a library clip as active for paste on timeline click."""
        self.timeline.set_active_clip(clip_data)
