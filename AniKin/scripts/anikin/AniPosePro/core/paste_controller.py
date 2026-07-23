"""
paste_controller.py — Click-to-Paste Timeline Controller for AniPose Pro V3.1.

Allows animators to arm a clip from the library and click any frame on Maya's timeline to paste it.
Uses scriptJob(event=['timeChanged']) with explicit playback guards and HUD overlay.
"""

import maya.cmds as cmds
from anikin.AniPosePro.paste import paste_clip_at_frame


class AnimPasteController(object):
    """
    Manages the 'click-to-paste' state for AniCapture animation clips.
    """

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = AnimPasteController()
        return cls._instance

    def __init__(self):
        self._armed = False
        self._clip_data = None
        self._paste_options = {}
        self._script_job = None

    @property
    def is_armed(self) -> bool:
        return self._armed

    def arm(self, clip_data: dict, options: dict = None):
        """Activates paste mode for the given clip."""
        if self._armed:
            self.disarm()

        if not clip_data:
            return

        self._clip_data = clip_data
        self._paste_options = options or {}
        self._armed = True

        try:
            self._script_job = cmds.scriptJob(
                event=['timeChanged', self._on_time_changed],
                protected=False
            )
        except Exception as e:
            cmds.warning(f"AniPose Pro: Failed to register paste listener — {e}")

        clip_name = clip_data.get("name", "Clip")
        self._show_armed_hud(clip_name)
        cmds.inViewMessage(
            amg=f"<hl>AniCapture</hl>: ARMED — Click timeline frame to paste '{clip_name}'",
            pos="topCenter", fade=True, fadeStayTime=2000
        )

    def disarm(self):
        """Deactivates paste mode."""
        self._armed = False
        if self._script_job and cmds.scriptJob(exists=self._script_job):
            try:
                cmds.scriptJob(kill=self._script_job, force=True)
            except Exception:
                pass
        self._script_job = None
        self._hide_armed_hud()
        self._clip_data = None

    def _on_time_changed(self):
        """
        Fires when user clicks/scrubs the timeline.
        Only acts when explicitly ARMED — ignores changes from active playback!
        """
        if not self._armed:
            return

        # Explicit playback guard: ignore time changes while playing back scene
        if cmds.play(q=True, state=True):
            return

        target_frame = float(cmds.currentTime(q=True))
        self.execute_paste(target_frame)

        if not self._paste_options.get('multi_paste', False):
            self.disarm()

    def execute_paste(self, target_frame: float, selected_nodes: list = None):
        """Pastes the armed or specified clip at target_frame."""
        clip = self._clip_data
        if not clip:
            return

        nodes = selected_nodes or cmds.ls(selection=True, long=True) or []
        if not nodes:
            cmds.warning("AniPose Pro: Select controls to paste animation clip.")
            return

        mode = self._paste_options.get('mode', 'replace')
        retime_frames = self._paste_options.get('retime_frames')
        new_layer = bool(self._paste_options.get('new_layer', False))

        if new_layer:
            layer_name = f"AniCapture_Paste_{int(target_frame)}"
            try:
                cmds.animLayer(layer_name, override=True)
                cmds.animLayer(layer_name, e=True, selected=True)
            except Exception:
                pass

        paste_clip_at_frame(clip, nodes, target_frame, mode=mode, retime_frames=retime_frames)

    def _show_armed_hud(self, clip_name: str):
        if cmds.headsUpDisplay('AniCapturePasteHUD', exists=True):
            try:
                cmds.headsUpDisplay('AniCapturePasteHUD', remove=True)
            except Exception:
                pass
        try:
            cmds.headsUpDisplay(
                'AniCapturePasteHUD',
                section=5, block=0,
                label=f'⬤ AniCapture ARMED — Click timeline to paste: "{clip_name}"',
                labelFontSize='large',
                blockSize='large',
            )
        except Exception:
            pass

    def _hide_armed_hud(self):
        if cmds.headsUpDisplay('AniCapturePasteHUD', exists=True):
            try:
                cmds.headsUpDisplay('AniCapturePasteHUD', remove=True)
            except Exception:
                pass
