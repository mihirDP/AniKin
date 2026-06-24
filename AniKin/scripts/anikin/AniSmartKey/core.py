"""
AniSmartKey.py
Smart Key Tool — keys only animated and keyable channels that have changed.

Prevents curve clutter by only keying channels that have actually changed since their last keyframe.
"""

import maya.cmds as cmds
from anikin.core.undo import UndoChunk
from anikin.core.selection import get_selected_or_warn
from anikin.core.log import log_debug


def _get_animated_channels(node):
    """Return a list of (node.attr) strings that have animation curves."""
    connections = cmds.listConnections(node, type="animCurve", plugs=False,
                                       connections=True, destination=False) or []
    attrs = []
    for i in range(0, len(connections), 2):
        plug = connections[i]
        attrs.append(plug)
    return attrs


def execute(mode="all", threshold=0.001):
    """
    Key only animated and keyable channels.
    
    Args:
        mode: "all", "translate", "rotate", "scale"
        threshold: Minimum change required from the previous key value to set a key.
                  If None or 0, keys all matched animated channels regardless of value change.
    """
    sel = get_selected_or_warn(min_count=1)
    if not sel:
        return

    current_time = cmds.currentTime(query=True)
    active_layer = cmds.animLayer(query=True, selected=True)
    layer_kwargs = {}
    if active_layer:
        layer_kwargs["animLayer"] = active_layer[0]

    log_debug("AniSmartKey: Smart Key execute (mode: {}, threshold: {})".format(mode, threshold))
    
    with UndoChunk("AniKin: Smart Key ({})".format(mode)):
        keyed_count = 0
        objects_keyed = set()
        
        for node in sel:
            channels = _get_animated_channels(node)
            filtered_channels = []
            
            for plug in channels:
                parts = plug.split(".")
                node_name = parts[0]
                attr_name = ".".join(parts[1:])
                
                # Apply filter
                if mode == "translate" and not attr_name.startswith("translate"):
                    continue
                elif mode == "rotate" and not attr_name.startswith("rotate"):
                    continue
                elif mode == "scale" and not attr_name.startswith("scale"):
                    continue
                
                # Skip locked or non-keyable channels
                if cmds.getAttr(plug, lock=True):
                    continue
                if not cmds.getAttr(plug, keyable=True):
                    continue
                
                filtered_channels.append((node_name, attr_name, plug))
                
            for node_name, attr_name, plug in filtered_channels:
                try:
                    val = cmds.getAttr(plug)
                    
                    # If threshold check is enabled, check value change from previous key
                    if threshold is not None and threshold > 0:
                        prev_t = cmds.findKeyframe(plug, time=(current_time, current_time), which="previous")
                        # If sitting on a key, search further back
                        if prev_t == current_time:
                            # Note: findKeyframe with same time and previous will find prior key
                            prev_t = cmds.findKeyframe(plug, time=(current_time - 0.001, current_time - 0.001), which="previous")
                        
                        if prev_t is not None and prev_t != current_time:
                            prev_val = cmds.keyframe(plug, time=(prev_t, prev_t), query=True, eval=True)[0]
                            if abs(val - prev_val) <= threshold:
                                continue  # Under threshold, skip keying

                    cmds.setKeyframe(node_name, attribute=attr_name,
                                     time=current_time, value=val, **layer_kwargs)
                    keyed_count += 1
                    objects_keyed.add(node_name)
                except Exception:
                    pass

    if keyed_count == 0:
        cmds.warning("Smart Key: No animated/keyable channels matching '{}' met the threshold check.".format(mode))
    else:
        msg = "Smart Key: {} keys set across {} objects".format(keyed_count, len(objects_keyed))
        cmds.inViewMessage(
            amg="<hl>AniKin</hl>: {}".format(msg),
            pos="topCenter", fade=True, fadeStayTime=1500
        )
        print("[AniKin] " + msg)
