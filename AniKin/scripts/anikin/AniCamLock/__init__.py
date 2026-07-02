"""
AniCamLock — Viewport Camera Lock-to-Object
============================================

Locks the active **viewport** camera to follow a selected object during
animation playback using Maya constraints (evaluates natively in the DG).

Usage:
    from anikin.AniCamLock import cam_lock_toggle
    cam_lock_toggle(mode='track')
"""

import maya.cmds as cmds
from maya.api.OpenMaya import MMatrix
from anikin.core.log import log_debug

HUD_NAME = 'AniKinCamLockHUD'


def show_hud(object_name):
    if cmds.headsUpDisplay(HUD_NAME, exists=True):
        cmds.headsUpDisplay(HUD_NAME, remove=True)
    cmds.headsUpDisplay(
        HUD_NAME,
        section=5,              # top-center section
        block=0,
        blockSize='medium',
        label='AniCamLock: ON  [{}]'.format(object_name),
        labelFontSize='large',
        dataFontSize='large',
    )


def hide_hud():
    if cmds.headsUpDisplay(HUD_NAME, exists=True):
        cmds.headsUpDisplay(HUD_NAME, remove=True)


def get_active_panel_and_camera():
    """
    Returns (panel_name, camera_transform, camera_shape) for the
    currently focused model panel.
    Returns (None, None, None) if no model panel is active.
    """
    panel = cmds.getPanel(withFocus=True)

    # Validate it's a model panel (3D viewport), not UV editor etc.
    if cmds.getPanel(typeOf=panel) != 'modelPanel':
        # Fall back: find the first visible model panel
        all_panels = cmds.getPanel(type='modelPanel') or []
        if not all_panels:
            return None, None, None
        panel = all_panels[0]

    # modelEditor gives us the camera SHAPE name
    cam_shape = cmds.modelEditor(panel, query=True, camera=True)

    # Get the transform (parent) of the shape
    if cmds.nodeType(cam_shape) != 'transform':
        cam_transform = cmds.listRelatives(cam_shape, parent=True, fullPath=True)[0]
    else:
        cam_transform = cam_shape
        shapes = cmds.listRelatives(cam_transform, shapes=True, fullPath=True, type="camera")
        cam_shape = shapes[0] if shapes else cam_transform

    return panel, cam_transform, cam_shape


def get_world_matrix(node):
    """Returns the 4x4 world-space matrix of a transform node as MMatrix."""
    return MMatrix(cmds.xform(node, query=True, matrix=True, worldSpace=True))


def create_temp_camera(name='AniKin_CamLock_temp'):
    """
    Creates a camera transform+shape pair.
    Returns (transform_name, shape_name).
    """
    result = cmds.camera(name=name)
    transform = result[0]
    shape = result[1]
    # Hide from the outliner's default display to keep scene clean
    cmds.setAttr(transform + '.hiddenInOutliner', True)
    return transform, shape


def match_camera_transform(source_cam_transform, target_cam_transform):
    """
    Moves target_cam to the exact world-space position and orientation
    of source_cam. Uses xform matrix for rotation-order safety.
    """
    matrix = cmds.xform(source_cam_transform, query=True, matrix=True, worldSpace=True)
    cmds.xform(target_cam_transform, matrix=matrix, worldSpace=True)


class AniCamLockController:
    """
    Manages the Cam Lock state for AniKin.
    Singleton pattern: only one lock active at a time.
    """

    def __init__(self):
        self._locked = False
        self._panel = None
        self._original_cam = None   # camera shape of original view
        self._temp_cam = None       # transform name of temp camera
        self._temp_cam_shape = None # shape name of temp camera
        self._buffer_grp = None     # buffer group to avoid evaluation cycles
        self._target_object = None
        self._mode = 'track'        # 'track' or 'aim'
        self._constraints = []      # list of constraint node names
        self._script_jobs = []

    @property
    def is_locked(self):
        return self._locked

    def lock(self, mode='track'):
        if self._locked:
            cmds.warning('AniCamLock: Already locked. Click again to unlock.')
            return False

        # --- Validate selection ---
        selection = cmds.ls(selection=True, long=True)
        if not selection:
            cmds.warning('AniCamLock: Select an object to lock onto first.')
            return False
        target = selection[0]

        # --- Get active panel + camera ---
        panel, orig_cam_xform, orig_cam_shape = get_active_panel_and_camera()
        if not panel:
            cmds.warning('AniCamLock: No active 3D viewport found.')
            return False

        # --- Create and position temp camera ---
        temp_xform, temp_shape = create_temp_camera()
        match_camera_transform(orig_cam_xform, temp_xform)

        # --- Create buffer group ---
        buffer_grp = cmds.group(empty=True, name='AniKin_CamLock_Buffer')
        cmds.setAttr(buffer_grp + '.hiddenInOutliner', True)
        match_camera_transform(orig_cam_xform, buffer_grp)
        cmds.parent(temp_xform, buffer_grp)

        # --- Apply constraint(s) to buffer group ---
        constraints = []
        if mode == 'track':
            c = cmds.parentConstraint(target, buffer_grp,
                                      maintainOffset=True,
                                      name='AniKin_CamLock_pConst')[0]
            constraints.append(c)
        elif mode == 'aim':
            c1 = cmds.pointConstraint(target, buffer_grp,
                                      maintainOffset=True,
                                      name='AniKin_CamLock_ptConst')[0]
            c2 = cmds.aimConstraint(target, buffer_grp,
                                    aimVector=(0, 0, -1),
                                    upVector=(0, 1, 0),
                                    worldUpType='scene',
                                    name='AniKin_CamLock_aimConst')[0]
            constraints.extend([c1, c2])

        # --- Switch viewport ---
        cmds.lookThru(panel, temp_shape)

        # --- Store state ---
        self._locked = True
        self._panel = panel
        self._original_cam = orig_cam_shape
        self._temp_cam = temp_xform
        self._temp_cam_shape = temp_shape
        self._buffer_grp = buffer_grp
        self._target_object = target
        self._mode = mode
        self._constraints = constraints

        short_name = target.split("|")[-1]
        show_hud(short_name)
        log_debug("CamLock ON → tracking '{}' (mode: {})".format(short_name, mode))

        # Register script jobs to handle edge cases
        self._register_script_jobs()

        return True

    def unlock(self):
        if not self._locked:
            return

        # Restore original camera view
        if self._panel and self._original_cam:
            try:
                cmds.lookThru(self._panel, self._original_cam)
            except Exception as e:
                cmds.warning('AniCamLock: Could not restore camera — {}'.format(e))

        # Defer deletion of the camera and constraints to the next idle event.
        # Deleting a camera immediately after lookThru corrupts the Viewport 2.0 
        # evaluation state in the current frame, causing permanent glitching!
        nodes_to_delete = [n for n in self._constraints + [self._temp_cam, self._buffer_grp] if n]
        if nodes_to_delete:
            def deferred_delete(nodes=nodes_to_delete):
                for node in nodes:
                    if cmds.objExists(node):
                        try:
                            cmds.delete(node)
                        except Exception:
                            pass
            cmds.evalDeferred(deferred_delete)

        # Remove HUD
        hide_hud()
        
        # Kill script jobs
        self._kill_script_jobs()

        log_debug("CamLock OFF — camera restored.")

        # Reset state
        self._locked = False
        self._panel = None
        self._original_cam = None
        self._temp_cam = None
        self._temp_cam_shape = None
        self._buffer_grp = None
        self._target_object = None
        self._constraints = []
        self._script_jobs = []

    def toggle(self, mode='track'):
        if self._locked:
            self.unlock()
            return False
        else:
            return self.lock(mode=mode)
            
    def _register_script_jobs(self):
        # Auto unlock if target is deleted
        if self._target_object and cmds.objExists(self._target_object):
            sj_del = cmds.scriptJob(nodeDeleted=[self._target_object, self._on_target_deleted])
            self._script_jobs.append(sj_del)
            
        # Auto unlock on scene change
        sj_open = cmds.scriptJob(event=['SceneOpened', self._on_scene_changed])
        sj_new = cmds.scriptJob(event=['NewSceneOpened', self._on_scene_changed])
        self._script_jobs.extend([sj_open, sj_new])

    def _kill_script_jobs(self):
        for sj in self._script_jobs:
            if cmds.scriptJob(exists=sj):
                try:
                    cmds.scriptJob(kill=sj, force=True)
                except Exception:
                    pass
        self._script_jobs = []

    def _on_target_deleted(self):
        cmds.warning('AniCamLock: Target object was deleted. Lock released.')
        self.unlock()
        
        # We need to notify the UI to update the toggle button state
        # A simple broadcast or finding the UI
        try:
            from anikin.ui.main_window import _INSTANCE
            if _INSTANCE and hasattr(_INSTANCE, '_cam_lock_btn'):
                _INSTANCE._cam_lock_btn.set_toggled(False)
        except Exception:
            pass

    def _on_scene_changed(self):
        # Silent unlock on scene change
        self.unlock()
        try:
            from anikin.ui.main_window import _INSTANCE
            if _INSTANCE and hasattr(_INSTANCE, '_cam_lock_btn'):
                _INSTANCE._cam_lock_btn.set_toggled(False)
        except Exception:
            pass

# Module-level singleton
_cam_lock = AniCamLockController()

def lock(mode='track'):
    return _cam_lock.lock(mode=mode)

def unlock():
    _cam_lock.unlock()
    
def is_locked():
    return _cam_lock.is_locked

def toggle(mode='track'):
    """Entry point called by the UI button."""
    return _cam_lock.toggle(mode=mode)

# Keep the same interface that UI expects
def cam_lock_toggle(mode='track'):
    return _cam_lock.toggle(mode=mode)
