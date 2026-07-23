"""
instancing.py — Clip Instancing Tracking (F-NEW-05).

Tracks where clips have been pasted in the Maya scene by writing metadata
to a hidden 'anikin_data' node. Allows updating all instances of a clip
simultaneously if the source clip is modified.
"""

import maya.cmds as cmds
import json

_DATA_NODE = "anikin_data"
_DATA_ATTR = "clip_instances"


def _ensure_data_node():
    """Ensure the persistent data node and attribute exist in the scene."""
    if not cmds.objExists(_DATA_NODE):
        # Create a hidden transform node
        cmds.createNode("transform", name=_DATA_NODE)
        cmds.setAttr(f"{_DATA_NODE}.hiddenInOutliner", True)
        # Lock transforms
        for attr in ["t", "r", "s"]:
            for axis in ["x", "y", "z"]:
                cmds.setAttr(f"{_DATA_NODE}.{attr}{axis}", lock=True)
                
    if not cmds.attributeQuery(_DATA_ATTR, node=_DATA_NODE, exists=True):
        cmds.addAttr(_DATA_NODE, longName=_DATA_ATTR, dataType="string")
        cmds.setAttr(f"{_DATA_NODE}.{_DATA_ATTR}", "[]", type="string")


def record_instance(clip_path, dest_frame, nodes, mode, retime_factor):
    """
    Record a paste event for a clip.
    """
    _ensure_data_node()
    
    current_data = cmds.getAttr(f"{_DATA_NODE}.{_DATA_ATTR}") or "[]"
    try:
        instances = json.loads(current_data)
    except Exception:
        instances = []
        
    entry = {
        "clip_path": clip_path,
        "dest_frame": dest_frame,
        "nodes": nodes,
        "mode": mode,
        "retime_factor": retime_factor
    }
    
    instances.append(entry)
    cmds.setAttr(f"{_DATA_NODE}.{_DATA_ATTR}", json.dumps(instances), type="string")


def get_instances_for_clip(clip_path):
    """
    Return all recorded instances for a specific clip in the current scene.
    """
    if not cmds.objExists(f"{_DATA_NODE}.{_DATA_ATTR}"):
        return []
        
    current_data = cmds.getAttr(f"{_DATA_NODE}.{_DATA_ATTR}") or "[]"
    try:
        instances = json.loads(current_data)
        return [i for i in instances if i.get("clip_path") == clip_path]
    except Exception:
        return []


def update_all_instances(clip_path):
    """
    Re-paste all recorded instances of a clip in the current scene using replace mode.
    """
    instances = get_instances_for_clip(clip_path)
    if not instances:
        cmds.warning(f"AniPose Pro: No instances found in scene for {clip_path}")
        return 0
        
    from anikin.AniPosePro.capture import load_clip_data
    from anikin.AniPosePro.paste import paste_clip_at_frame, paste_legacy_clip
    
    clip_data, _, is_v2 = load_clip_data(clip_path)
    if not clip_data:
        cmds.warning("AniPose Pro: Could not load source clip data.")
        return 0
        
    cmds.undoInfo(openChunk=True, chunkName="AniKin_UpdateClipInstances")
    try:
        updated = 0
        for inst in instances:
            nodes = [n for n in inst.get("nodes", []) if cmds.objExists(n)]
            if not nodes:
                continue
                
            frame = inst.get("dest_frame")
            retime = inst.get("retime_factor")
            
            # Force "replace" mode so it cleanly overwrites the previous instance
            if is_v2:
                paste_clip_at_frame(clip_data, nodes, frame, mode="replace", retime_frames=retime)
            else:
                paste_legacy_clip(clip_data, nodes, frame, mode="replace", retime_frames=retime)
                
            updated += 1
            
        cmds.inViewMessage(
            amg=f"<hl>AniPose Pro</hl>: Updated {updated} instances of clip.",
            pos="topCenter", fade=True, fadeStayTime=1500
        )
        return updated
    finally:
        cmds.undoInfo(closeChunk=True)
