"""
pose_brush.py — Pose Brush tool for AniPose Pro V2 (F-NEW-06).

Interactively "paint" a library pose onto specific controls in the viewport.
Uses Maya's draggerContext to detect click/hold on controls, applying
only the hovered control's values from the pose data. Hold duration controls blend.
"""

import maya.cmds as cmds
from anikin.AniPosePro.apply import apply_pose_full
from anikin.core.qt_compat import QtCore

_BRUSH_CTX = "AniPoseBrushContext"
_BRUSH_INSTANCE = None

class PoseBrushState:
    def __init__(self, pose_data):
        self.pose_data = pose_data
        self.active_control = None
        self.press_time = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._on_tick)
        self.timer.setInterval(50)  # 20 ticks per second
        self._initial_state = {}

    def _on_tick(self):
        if not self.active_control:
            return
            
        import time
        elapsed = time.time() - self.press_time
        # Map 0 to 1.5 seconds -> 0.0 to 1.0 blend
        blend = max(0.0, min(1.0, elapsed / 1.5))
        
        # Apply the blend for the active control
        self._apply_blend(blend)
        
        # Overlay message
        cmds.inViewMessage(
            amg=f"<hl>Pose Brush</hl>: Blending {self.active_control} ({int(blend*100)}%)",
            pos="topCenter", fade=True, fadeStayTime=100
        )

    def _apply_blend(self, t):
        if not self.active_control or not self.pose_data:
            return
            
        short = self.active_control.split("|")[-1]
        ns_key = ":".join(short.split(":")[1:]) if ":" in short else short
        
        controls = self.pose_data.get("controls", {})
        if ns_key not in controls:
            return
            
        channels = controls[ns_key]
        for attr, lib_val in channels.items():
            full_attr = f"{self.active_control}.{attr}"
            if cmds.objExists(full_attr) and full_attr in self._initial_state:
                start_val = self._initial_state[full_attr]
                blended_val = start_val + (lib_val - start_val) * t
                try:
                    cmds.setAttr(full_attr, blended_val)
                except Exception:
                    pass

    def start_drag(self, control):
        self.active_control = control
        import time
        self.press_time = time.time()
        
        # Snapshot initial state for blending
        self._initial_state = {}
        short = self.active_control.split("|")[-1]
        ns_key = ":".join(short.split(":")[1:]) if ":" in short else short
        channels = self.pose_data.get("controls", {}).get(ns_key, {})
        
        for attr in channels.keys():
            full_attr = f"{self.active_control}.{attr}"
            if cmds.objExists(full_attr):
                self._initial_state[full_attr] = cmds.getAttr(full_attr)
                
        cmds.undoInfo(openChunk=True, chunkName="AniKin_PoseBrush")
        self.timer.start()

    def end_drag(self):
        self.timer.stop()
        self._apply_blend(1.0 if (time.time() - self.press_time) >= 1.5 else (time.time() - self.press_time)/1.5) # ensure final state is applied
        import time
        self.active_control = None
        cmds.undoInfo(closeChunk=True)


def activate_pose_brush(pose_data):
    """
    Activates the viewport dragger context for Pose Brush.
    """
    global _BRUSH_INSTANCE
    
    # Clean up previous context if it exists
    if cmds.draggerContext(_BRUSH_CTX, exists=True):
        cmds.deleteUI(_BRUSH_CTX)
        
    _BRUSH_INSTANCE = PoseBrushState(pose_data)
    
    cmds.draggerContext(
        _BRUSH_CTX,
        pressCommand=_on_press,
        releaseCommand=_on_release,
        name=_BRUSH_CTX,
        cursor="crossHair",
        undoMode="step"
    )
    cmds.setToolTo(_BRUSH_CTX)
    cmds.inViewMessage(
        amg="<hl>Pose Brush Active</hl>: Click and hold controls in viewport to paint pose.",
        pos="midCenter", fade=True, fadeStayTime=3000
    )


def deactivate_pose_brush():
    global _BRUSH_INSTANCE
    if cmds.draggerContext(_BRUSH_CTX, exists=True):
        cmds.setToolTo("selectSuperContext")
        cmds.deleteUI(_BRUSH_CTX)
    _BRUSH_INSTANCE = None
    cmds.inViewMessage(
        amg="Pose Brush Disabled",
        pos="topCenter", fade=True, fadeStayTime=1000
    )


def _on_press():
    """Triggered on mouse press during draggerContext."""
    global _BRUSH_INSTANCE
    if not _BRUSH_INSTANCE: return
    
    modifier = cmds.draggerContext(_BRUSH_CTX, q=True, modifier=True)
    if modifier == "ctrl":
        # Ctrl+click to exit
        deactivate_pose_brush()
        return
        
    # Get click location
    vp_x = cmds.draggerContext(_BRUSH_CTX, q=True, anchorPoint=True)[0]
    vp_y = cmds.draggerContext(_BRUSH_CTX, q=True, anchorPoint=True)[1]
    
    # Select from screen to find what was clicked
    # Store old selection
    old_sel = cmds.ls(selection=True, long=True)
    
    cmds.selectFromScreen(int(vp_x), int(vp_y), int(vp_x), int(vp_y), clear=True)
    new_sel = cmds.ls(selection=True, long=True)
    
    # Restore old selection (we don't want to actually change selection just paint)
    if old_sel:
        cmds.select(old_sel, replace=True)
    else:
        cmds.select(clear=True)
        
    if new_sel:
        _BRUSH_INSTANCE.start_drag(new_sel[0])
    else:
        cmds.warning("Pose Brush: No control found under cursor.")


def _on_release():
    """Triggered on mouse release during draggerContext."""
    global _BRUSH_INSTANCE
    if _BRUSH_INSTANCE:
        _BRUSH_INSTANCE.end_drag()
