# AniKin V2 — Features: How To Build Them
**AniKin V2 · Document Series · 03 of 04**

> This document is exclusively for developers. It answers: **"How do we implement each feature?"**
> Every feature in `anikin_v2_features_what.md` has a corresponding section here with: Maya API calls,
> Python patterns, data structures, known edge cases with solutions, and code scaffolding.
> Read the WHAT document first. Come here for the HOW.

---

## Prerequisites & Environment

### Python Version
All AniKin code targets **Python 3** (Maya 2022+). No Python 2 compatibility required or desired.

### Maya API Strategy
AniKin uses a **layered API approach**:
- **Layer 1 — `maya.cmds`**: Default for all straightforward operations. Readable, maintainable, sufficient for 90% of features.
- **Layer 2 — `maya.OpenMaya` (OM1 / OM2)**: Used where `cmds` is too slow or insufficient — bounding box queries, MFnAnimCurve iteration, MDagPath traversal.
- **Layer 3 — `maya.mel`**: Avoided unless interfacing with legacy Maya systems (e.g. some timeline UI hooks). Document every MEL call with a comment explaining why `cmds` wasn't used.

### Project Structure
```
AniKin/
├── anikin/
│   ├── __init__.py
│   ├── core/
│   │   ├── ground.py          # F-001
│   │   ├── nudge.py           # F-002
│   │   ├── duplicate_slide.py # F-003
│   │   ├── tween.py           # F-004
│   │   ├── smart_key.py       # F-005
│   │   ├── wave.py            # F-014
│   │   ├── noise.py           # F-015
│   │   └── curve_cleanup.py   # F-019
│   ├── workflow/
│   │   ├── bookmarks.py       # F-006
│   │   ├── snap.py            # F-007
│   │   └── selection_sets.py  # F-008
│   ├── visual/
│   │   ├── ghost.py           # F-009
│   │   └── arc.py             # F-010
│   ├── kinematics/
│   │   ├── mirror.py          # F-011
│   │   ├── foot_slide.py      # F-012
│   │   ├── root_motion.py     # F-017
│   │   └── com_visualizer.py  # F-018
│   ├── pipeline/
│   │   ├── export.py          # F-013
│   │   └── health_check.py    # F-016
│   ├── ui/
│   │   ├── main_panel.py
│   │   ├── timeline_strip.py
│   │   └── widgets/
│   └── utils/
│       ├── rig_utils.py
│       ├── curve_utils.py
│       ├── timeline_utils.py
│       └── math_utils.py
├── tests/
├── docs/
└── README.md
```

### Shared Utilities — Build These First
Before implementing any feature module, build `utils/`. Every feature depends on them.

```python
# utils/timeline_utils.py

import maya.cmds as cmds

def get_playback_range():
    """Returns (start, end) of the current playback range."""
    return (
        int(cmds.playbackOptions(q=True, min=True)),
        int(cmds.playbackOptions(q=True, max=True))
    )

def get_current_frame():
    return int(cmds.currentTime(q=True))

def set_current_frame(frame):
    cmds.currentTime(frame, edit=True)

def get_keyframes_in_range(node, attr, start, end):
    """Returns sorted list of keyframe times for a node.attr within [start, end]."""
    keys = cmds.keyframe(f"{node}.{attr}", q=True, time=(start, end), timeChange=True)
    return sorted(keys) if keys else []

def get_all_keyframe_times(node, start=None, end=None):
    """Returns all keyframe times across all animated attrs of a node."""
    if start is not None and end is not None:
        return cmds.keyframe(node, q=True, time=(start, end), timeChange=True) or []
    return cmds.keyframe(node, q=True, timeChange=True) or []
```

```python
# utils/rig_utils.py

import maya.cmds as cmds

def get_animated_attrs(node):
    """Return list of animated attribute names on this node."""
    attrs = []
    for attr in cmds.listAttr(node, keyable=True) or []:
        full = f"{node}.{attr}"
        if cmds.objExists(full) and cmds.keyframe(full, q=True, keyframeCount=True):
            attrs.append(attr)
    return attrs

def get_selected_nodes():
    return cmds.ls(selection=True, long=True) or []

def get_world_bounding_box(node):
    """Returns (xmin, ymin, zmin, xmax, ymax, zmax) in world space."""
    return cmds.exactWorldBoundingBox(node, calculateExactly=True)
```

---

## Pillar I — Core Animation Tools

---

### F-001 · Set Object to Ground

**Goal:** Move the object's lowest geometry point to Y=0 using world-space bounding box.

#### Key API Calls
- `cmds.exactWorldBoundingBox(node, calculateExactly=True)` — returns `[xmin, ymin, zmin, xmax, ymax, zmax]`. The `calculateExactly=True` flag forces Maya to compute the tight bounding box on actual geometry, not a fast estimate. **Always use this flag.**
- `cmds.move(0, delta_y, 0, node, relative=True, worldSpace=True)` — moves the node in world space by the delta.
- `cmds.undoInfo(openChunk=True)` / `cmds.undoInfo(closeChunk=True)` — wraps the entire operation so it undoes in one step.

#### Implementation

```python
# core/ground.py

import maya.cmds as cmds
from anikin.utils.rig_utils import get_selected_nodes, get_world_bounding_box

def ground_objects(nodes=None):
    """
    Translates each node so its lowest bounding box point touches Y=0.
    Operates on provided nodes, or on current selection if nodes=None.
    """
    if nodes is None:
        nodes = get_selected_nodes()
    if not nodes:
        cmds.warning("AniKin Ground: Nothing selected.")
        return

    cmds.undoInfo(openChunk=True, chunkName="AniKin_GroundObjects")
    try:
        for node in nodes:
            _ground_single(node)
    finally:
        cmds.undoInfo(closeChunk=True)

def _ground_single(node):
    # exactWorldBoundingBox accounts for all child geometry, frozen transforms,
    # and moved pivots — unlike cmds.getAttr("translateY") which is pivot-based.
    bbox = get_world_bounding_box(node)
    ymin = bbox[1]  # index 1 = world Y minimum

    if abs(ymin) < 1e-5:
        # Already at ground within floating-point tolerance — skip silently.
        return

    delta_y = -ymin  # How much to move up (or down) to reach Y=0
    cmds.move(0, delta_y, 0, node, relative=True, worldSpace=True)
```

#### Edge Case Handling

| Scenario | Handling |
|---|---|
| Object with frozen transforms | `exactWorldBoundingBox` uses world space — frozen transforms are irrelevant. |
| Group with child meshes | `exactWorldBoundingBox` recurses into children automatically. |
| Object pivot offset from geometry | Works correctly — we move by geometry ymin, not pivot. |
| Object already at Y=0 | `abs(ymin) < 1e-5` guard prevents unnecessary move and undo entry. |
| Multiple selected objects | Loop processes each independently; each gets its own ground operation. |
| NURBS / locator / non-mesh | `exactWorldBoundingBox` works on any DAG node — not mesh-specific. |
| Object with negative scale | Bounding box is still correctly computed in world space. |

#### UI Hook
```python
# In main_panel.py
ground_btn = cmds.button(
    label="Ground Object",
    command=lambda _: ground_objects(),
    annotation="Drop selected object(s) to Maya's Y=0 ground plane."
)
```

---

### F-002 · Key Nudge — Shift Keyframes by N Frames

**Goal:** Move all keyframes in a selected range (or selected keys) forward or backward by an exact integer frame count.

#### Key API Calls
- `cmds.keyframe(node, query=True, selected=True, timeChange=True)` — gets times of currently selected keys in Graph Editor.
- `cmds.keyframe(node, time=(start, end), edit=True, relative=True, timeChange=delta)` — shifts all keys in a time range by `delta` frames. This is the core nudge call.
- `cmds.selectKey(node, time=(start, end), add=True)` — programmatically selects keys in a range across all curves.

#### Data Flow

```
User input:
  - selected_nodes: list[str]       (from viewport selection)
  - frame_range: tuple[int, int]    (from AniKin timeline strip OR graph editor selection)
  - delta: int                      (positive = forward, negative = backward)
  - mode: "range" | "selected_keys" (determined by what user has selected)

Processing:
  1. Validate delta != 0
  2. For each node:
     a. Collect affected keys (range mode: all keys in [start, end]; selected mode: graph editor selection)
     b. Check for collision at destination frames
     c. If collision: prompt user (Overwrite / Cancel)
     d. Apply keyframe() timeChange edit
  3. Wrap in undo chunk
```

#### Implementation

```python
# core/nudge.py

import maya.cmds as cmds
from anikin.utils.rig_utils import get_selected_nodes, get_animated_attrs
from anikin.utils.timeline_utils import get_all_keyframe_times

def nudge_keyframes(delta, nodes=None, frame_range=None):
    """
    Nudge keyframes by `delta` frames.
    
    Args:
        delta (int): Frames to shift. Positive = forward, negative = backward.
        nodes (list[str]): Nodes to affect. None = current selection.
        frame_range (tuple[int,int]): (start, end) to restrict nudge.
                                       None = use graph editor selection.
    """
    if delta == 0:
        return

    if nodes is None:
        nodes = get_selected_nodes()
    if not nodes:
        cmds.warning("AniKin Nudge: Nothing selected.")
        return

    # Collision check before committing
    collision = _check_collisions(nodes, frame_range, delta)
    if collision:
        result = cmds.confirmDialog(
            title="AniKin Key Nudge — Collision Detected",
            message=f"Nudging by {delta} frames would overwrite existing keys on:\n{chr(10).join(collision[:5])}{'...' if len(collision)>5 else ''}",
            button=["Overwrite", "Cancel"],
            defaultButton="Cancel",
            cancelButton="Cancel"
        )
        if result == "Cancel":
            return

    cmds.undoInfo(openChunk=True, chunkName="AniKin_NudgeKeys")
    try:
        for node in nodes:
            _nudge_node(node, delta, frame_range)
    finally:
        cmds.undoInfo(closeChunk=True)

def _nudge_node(node, delta, frame_range):
    """Applies nudge to a single node."""
    for attr in get_animated_attrs(node):
        full_attr = f"{node}.{attr}"
        if frame_range:
            start, end = frame_range
            # keyframe with time range + relative timeChange = shift in place
            cmds.keyframe(full_attr, time=(start, end),
                          edit=True, relative=True, timeChange=delta)
        else:
            # Operate on graph editor's selected keys only
            selected_times = cmds.keyframe(full_attr, q=True, selected=True, timeChange=True)
            if selected_times:
                for t in sorted(selected_times, reverse=(delta > 0)):
                    # Shift one key at a time to avoid overwrite-then-shift issues
                    cmds.keyframe(full_attr, time=(t, t),
                                  edit=True, relative=True, timeChange=delta)

def _check_collisions(nodes, frame_range, delta):
    """
    Returns list of attribute strings where destination frames
    already have keys that are NOT in the source range.
    """
    collisions = []
    for node in nodes:
        for attr in get_animated_attrs(node):
            full = f"{node}.{attr}"
            if frame_range:
                source_keys = set(cmds.keyframe(full, q=True,
                                                time=frame_range,
                                                timeChange=True) or [])
                dest_keys = {t + delta for t in source_keys}
                all_keys = set(cmds.keyframe(full, q=True, timeChange=True) or [])
                # Collision = destination key already exists AND is NOT in source range
                overlap = dest_keys & (all_keys - source_keys)
                if overlap:
                    collisions.append(f"{node}.{attr}")
    return collisions
```

#### Nudge Direction: Why Sort in Reverse for Positive Delta
When shifting keys forward (`delta > 0`), process keys from **latest to earliest**. Otherwise, key at frame 10 shifts to 11, then the key originally at 11 (now adjacent) would collide before it gets shifted. Reverse sort eliminates this cascading collision.

#### UI — Nudge Panel
```python
# Suggested UI layout in main_panel.py

# Frame range input (driven by AniKin timeline strip selection)
# Nudge amount field (intField, default=1)
# [ ← -N ]   [ -1 ]   [ +1 ]   [ +N → ]

def _build_nudge_ui(parent):
    cmds.rowLayout(numberOfColumns=5, parent=parent)
    cmds.button(label="← -N",  command=lambda _: nudge_keyframes(-_get_nudge_amount()))
    cmds.button(label="← -1",  command=lambda _: nudge_keyframes(-1))
    cmds.intField("anikin_nudge_amount", value=1, minValue=1, maxValue=999)
    cmds.button(label="+1 →",  command=lambda _: nudge_keyframes(1))
    cmds.button(label="+N →",  command=lambda _: nudge_keyframes(_get_nudge_amount()))

def _get_nudge_amount():
    return cmds.intField("anikin_nudge_amount", q=True, value=True)
```

---

### F-003 · Keyframe Duplicate & Slide

**Goal:** Copy a block of keyframes and let the animator interactively place the copy.

#### Key API Calls
- `cmds.copyKey(node, time=(start, end))` — copies keys in range to Maya's internal key clipboard.
- `cmds.pasteKey(node, time=(dest_start,), option="merge")` — pastes at destination. `option="merge"` blends with existing; `option="replace"` overwrites.
- `cmds.keyframe(node, q=True, time=(start,end), valueChange=True)` — read values to verify copy.

#### Two-Phase Architecture

The duplicate+slide operation is two distinct phases:

**Phase 1 — Capture:** Read and store the source key block into AniKin's own data structure (not Maya's clipboard, which is shared and volatile).

**Phase 2 — Place:** The animator drags an indicator on the AniKin timeline strip. On commit, paste the stored data at the new position.

```python
# core/duplicate_slide.py

import maya.cmds as cmds
from anikin.utils.rig_utils import get_selected_nodes, get_animated_attrs

class KeyBlockDuplicator:
    """
    Manages the duplicate-and-slide workflow for a key block.
    Stores a complete snapshot of key data (time, value, tangent in/out)
    for every channel, then pastes it at a user-specified offset.
    """

    def __init__(self):
        self._block = {}   # {node: {attr: [(time, value, tan_in, tan_out), ...]}}
        self._source_start = None
        self._source_end = None

    def capture(self, nodes, start, end):
        """
        Phase 1: Snapshot all key data in [start, end] for the given nodes.
        Stores raw data so we are NOT dependent on Maya's key clipboard.
        """
        self._block = {}
        self._source_start = start
        self._source_end = end

        for node in nodes:
            self._block[node] = {}
            for attr in get_animated_attrs(node):
                full = f"{node}.{attr}"
                times = cmds.keyframe(full, q=True, time=(start, end), timeChange=True) or []
                values = cmds.keyframe(full, q=True, time=(start, end), valueChange=True) or []
                in_angles = cmds.keyTangent(full, q=True, time=(start, end), inAngle=True) or []
                out_angles = cmds.keyTangent(full, q=True, time=(start, end), outAngle=True) or []
                in_types = cmds.keyTangent(full, q=True, time=(start, end), inTangentType=True) or []
                out_types = cmds.keyTangent(full, q=True, time=(start, end), outTangentType=True) or []

                if times:
                    self._block[node][attr] = list(zip(
                        times, values, in_angles, out_angles, in_types, out_types
                    ))

        return bool(self._block)

    def place(self, dest_start, overwrite=False):
        """
        Phase 2: Paste the captured block at dest_start.
        dest_start is the frame where the block's first key should land.
        """
        if not self._block:
            cmds.warning("AniKin DuplicateSlide: No block captured.")
            return

        offset = dest_start - self._source_start

        # Collision check
        if not overwrite:
            collision = self._find_collisions(offset)
            if collision:
                result = cmds.confirmDialog(
                    title="AniKin — Key Block Collision",
                    message=f"Destination overlaps existing keys on {len(collision)} channel(s). Overwrite?",
                    button=["Overwrite", "Offset to Clear", "Cancel"],
                    defaultButton="Cancel"
                )
                if result == "Cancel":
                    return
                if result == "Offset to Clear":
                    offset = self._find_clear_offset(offset)
                # "Overwrite" falls through

        cmds.undoInfo(openChunk=True, chunkName="AniKin_DuplicateSlide")
        try:
            for node, attrs in self._block.items():
                for attr, keydata in attrs.items():
                    full = f"{node}.{attr}"
                    for (t, v, in_ang, out_ang, in_type, out_type) in keydata:
                        dest_t = t + offset
                        cmds.setKeyframe(full, time=dest_t, value=v)
                        cmds.keyTangent(full, time=(dest_t, dest_t),
                                        inAngle=in_ang, outAngle=out_ang,
                                        inTangentType=in_type, outTangentType=out_type)
        finally:
            cmds.undoInfo(closeChunk=True)

    def _find_collisions(self, offset):
        collisions = []
        for node, attrs in self._block.items():
            for attr, keydata in attrs.items():
                full = f"{node}.{attr}"
                existing = set(cmds.keyframe(full, q=True, timeChange=True) or [])
                source_times = {kd[0] for kd in keydata}
                dest_times = {t + offset for t in source_times}
                if dest_times & (existing - source_times):
                    collisions.append(f"{node}.{attr}")
        return collisions

    def _find_clear_offset(self, initial_offset):
        """Walk forward until destination is collision-free."""
        offset = initial_offset
        while True:
            if not self._find_collisions(offset):
                return offset
            offset += 1

# Module-level singleton — one active duplicator per session
_duplicator = KeyBlockDuplicator()

def begin_duplicate(start, end, nodes=None):
    if nodes is None:
        nodes = cmds.ls(selection=True, long=True) or []
    return _duplicator.capture(nodes, start, end)

def commit_place(dest_start):
    _duplicator.place(dest_start)
```

#### Why Not Use `cmds.copyKey` / `cmds.pasteKey`?
Maya's key clipboard is a **global shared state**. If the user copies something else between Phase 1 and Phase 2 (which they might, while deciding where to place), the clipboard is corrupted. AniKin's own `KeyBlockDuplicator` stores the data independently.

---

### F-004 · AniTween — Breakdown & Tween Generator

**Goal:** At the current frame, interpolate between surrounding keyframes at a user-specified percentage.

#### Key API Calls
- `cmds.findKeyframe(full_attr, which="previous")` — time of the key before current frame.
- `cmds.findKeyframe(full_attr, which="next")` — time of the key after current frame.
- `cmds.getAttr(full_attr, time=t)` — sample the curve value at a specific time.
- `cmds.setKeyframe(full_attr, time=current, value=v)` — write the blended value.

```python
# core/tween.py

import maya.cmds as cmds
from anikin.utils.rig_utils import get_selected_nodes, get_animated_attrs

def apply_tween(blend, nodes=None, frame=None):
    """
    blend: float 0.0 to 1.0
        0.0 = match previous key exactly
        0.5 = midpoint
        1.0 = match next key exactly
    """
    if nodes is None:
        nodes = get_selected_nodes()
    if frame is None:
        frame = cmds.currentTime(q=True)

    cmds.undoInfo(openChunk=True, chunkName="AniKin_Tween")
    try:
        for node in nodes:
            for attr in get_animated_attrs(node):
                full = f"{node}.{attr}"
                _tween_attr(full, frame, blend)
    finally:
        cmds.undoInfo(closeChunk=True)

def _tween_attr(full_attr, frame, blend):
    prev_t = cmds.findKeyframe(full_attr, time=(frame, frame), which="previous")
    next_t = cmds.findKeyframe(full_attr, time=(frame, frame), which="next")

    # Skip if no surrounding keys on this attribute
    if prev_t is None or next_t is None:
        return
    if prev_t == next_t:
        return  # Only one key exists — no range to interpolate

    prev_val = cmds.getAttr(full_attr, time=prev_t)
    next_val = cmds.getAttr(full_attr, time=next_t)

    blended = prev_val + (next_val - prev_val) * blend
    cmds.setKeyframe(full_attr, time=frame, value=blended)
```

#### Real-Time Slider Feedback
The UI slider calls `apply_tween()` on every value change event (using `cmds.floatSlider` `dragCommand`). Since `apply_tween` wraps in an undo chunk, rapid dragging would flood the undo stack. **Solution:** Open the undo chunk when the slider drag starts (`pressCommand`) and close it only on release (`releaseCommand`). During drag, skip the undo wrapper.

```python
# Slider wired to tween:
cmds.floatSlider(
    min=0, max=1, value=0.5,
    pressCommand=lambda _: cmds.undoInfo(openChunk=True, chunkName="AniKin_TweenDrag"),
    dragCommand=lambda v: _tween_live(v),   # No undo chunk inside
    releaseCommand=lambda v: (apply_tween(v), cmds.undoInfo(closeChunk=True))
)
```

---

### F-005 · Smart Key — Context-Aware Keying

**Goal:** Key only channels with meaningful value changes since the last keyframe.

```python
# core/smart_key.py

import maya.cmds as cmds
from anikin.utils.rig_utils import get_selected_nodes, get_animated_attrs

SMART_KEY_THRESHOLD = 0.001  # Configurable — expose in AniKin settings

def smart_key(nodes=None, threshold=None, frame=None):
    """Sets keys only on channels that changed meaningfully since last key."""
    if nodes is None:
        nodes = get_selected_nodes()
    if frame is None:
        frame = int(cmds.currentTime(q=True))
    if threshold is None:
        threshold = SMART_KEY_THRESHOLD

    cmds.undoInfo(openChunk=True, chunkName="AniKin_SmartKey")
    keyed_count = 0
    try:
        for node in nodes:
            for attr in get_animated_attrs(node):
                full = f"{node}.{attr}"
                last_t = cmds.findKeyframe(full, time=(frame, frame), which="previous")
                if last_t is None:
                    # No prior key — always key it
                    cmds.setKeyframe(full, time=frame)
                    keyed_count += 1
                    continue

                last_val = cmds.getAttr(full, time=last_t)
                cur_val = cmds.getAttr(full, time=frame)

                if abs(cur_val - last_val) > threshold:
                    cmds.setKeyframe(full, time=frame)
                    keyed_count += 1
    finally:
        cmds.undoInfo(closeChunk=True)

    print(f"AniKin Smart Key: {keyed_count} channel(s) keyed on frame {frame}.")
```

---

### F-014 · AniWave — Wave / Ripple Key Offset

**Goal:** Progressively offset keyframes across multiple selected objects to create a ripple timing effect.

```python
# core/wave.py

import maya.cmds as cmds
from anikin.utils.rig_utils import get_animated_attrs

def apply_wave_offset(nodes, delay_per_object, start_frame=None, end_frame=None, reverse=False):
    """
    nodes: ordered list of nodes (order determines wave direction)
    delay_per_object: int, frames of delay per step
    start_frame/end_frame: restrict which keys to offset (None = all keys)
    reverse: if True, last node gets longest delay instead of first
    """
    if not nodes or delay_per_object == 0:
        return

    if reverse:
        nodes = list(reversed(nodes))

    cmds.undoInfo(openChunk=True, chunkName="AniKin_WaveOffset")
    try:
        for i, node in enumerate(nodes):
            total_offset = i * delay_per_object
            if total_offset == 0:
                continue  # First node is untouched
            for attr in get_animated_attrs(node):
                full = f"{node}.{attr}"
                kwargs = dict(edit=True, relative=True, timeChange=total_offset)
                if start_frame is not None and end_frame is not None:
                    kwargs["time"] = (start_frame, end_frame)
                cmds.keyframe(full, **kwargs)
    finally:
        cmds.undoInfo(closeChunk=True)
```

**UI Note:** The "Wave" panel should show the selected objects in a list with drag-to-reorder. The order of the list = the order of the wave. A "Randomize Order" button shuffles for organic crowd stagger.

---

### F-015 · AniNoise — Procedural Noise Layer

**Goal:** Apply Perlin-style noise on top of existing animation non-destructively, with optional bake-to-keys.

#### Implementation Strategy
Two modes:
1. **Expression mode** — Adds a Maya expression that layers noise on top of the attribute at runtime. Non-destructive, editable.
2. **Bake mode** — Samples noise values per frame and writes keyframes directly. Required for export.

```python
# core/noise.py

import maya.cmds as cmds
import math
import random
from anikin.utils.rig_utils import get_animated_attrs
from anikin.utils.timeline_utils import get_playback_range

def _simple_noise(t, frequency, seed):
    """
    Simple smooth noise using sine superposition.
    Not true Perlin — but deterministic, no dependencies, sufficient for animation use.
    For production quality, consider numpy-based Perlin if available.
    """
    random.seed(seed)
    phases = [random.uniform(0, math.pi * 2) for _ in range(4)]
    freqs  = [frequency * (i + 1) for i in range(4)]
    amps   = [1.0 / (i + 1) for i in range(4)]  # 1/f falloff for naturalness
    val = sum(a * math.sin(f * t + p) for a, f, p in zip(amps, freqs, phases))
    return val / sum(amps)  # Normalize to [-1, 1]

def bake_noise(nodes, attrs_config, seed=42):
    """
    attrs_config: {attr_name: {"amplitude": float, "frequency": float, "enabled": bool}}
    Bakes noise on top of existing animation by reading current curve values
    and adding noise, then writing new keyframes.
    """
    start, end = get_playback_range()

    cmds.undoInfo(openChunk=True, chunkName="AniKin_NoiseLayer")
    try:
        for node in nodes:
            for attr, cfg in attrs_config.items():
                if not cfg.get("enabled", True):
                    continue
                full = f"{node}.{attr}"
                if not cmds.objExists(full):
                    continue

                amplitude = cfg.get("amplitude", 1.0)
                frequency = cfg.get("frequency", 0.5)

                for frame in range(int(start), int(end) + 1):
                    base_val = cmds.getAttr(full, time=frame)
                    noise_val = _simple_noise(frame, frequency, seed) * amplitude
                    cmds.setKeyframe(full, time=frame, value=base_val + noise_val)
    finally:
        cmds.undoInfo(closeChunk=True)
```

**Frequency guidance for UI tooltips:**
- 0.1 = very slow drift (breathing, weight shift)
- 0.5 = medium tremor (nervous energy)
- 2.0+ = rapid jitter (camera shake, impact vibration)

---

### F-019 · Auto Curve Cleanup

**Goal:** Remove mathematically redundant keyframes while preserving the curve shape within a tolerance.

#### Algorithm
For each key at time `t`:
1. Temporarily remove it (store the value).
2. Sample the curve value at time `t` using Maya's interpolation (without the key).
3. If `|sampled - stored| < tolerance`, the key is redundant — leave it removed.
4. If `|sampled - stored| >= tolerance`, restore the key.

```python
# core/curve_cleanup.py

import maya.cmds as cmds
from anikin.utils.rig_utils import get_selected_nodes, get_animated_attrs

def cleanup_curves(nodes=None, tolerance=0.001, preview_only=False):
    """
    Removes redundant keyframes within tolerance.
    preview_only=True: returns list of removable keys without deleting.
    Returns: dict {node.attr: [list of removed key times]}
    """
    if nodes is None:
        nodes = get_selected_nodes()

    results = {}

    cmds.undoInfo(openChunk=True, chunkName="AniKin_CurveCleanup")
    try:
        for node in nodes:
            for attr in get_animated_attrs(node):
                full = f"{node}.{attr}"
                removed = _cleanup_attr(full, tolerance, preview_only)
                if removed:
                    results[full] = removed
    finally:
        cmds.undoInfo(closeChunk=True)

    return results

def _cleanup_attr(full_attr, tolerance, preview_only):
    times = cmds.keyframe(full_attr, q=True, timeChange=True) or []
    if len(times) < 3:
        return []  # Need at least 3 keys to have a redundant middle one

    removable = []

    # Evaluate from inside-out, never remove first or last key
    for t in times[1:-1]:
        stored_val = cmds.getAttr(full_attr, time=t)
        stored_tangents = {
            "in": cmds.keyTangent(full_attr, time=(t,t), q=True, inAngle=True)[0],
            "out": cmds.keyTangent(full_attr, time=(t,t), q=True, outAngle=True)[0],
            "inType": cmds.keyTangent(full_attr, time=(t,t), q=True, inTangentType=True)[0],
            "outType": cmds.keyTangent(full_attr, time=(t,t), q=True, outTangentType=True)[0],
        }

        # Temporarily remove key
        cmds.cutKey(full_attr, time=(t, t), clear=True)

        # Sample what the curve gives without this key
        interpolated_val = cmds.getAttr(full_attr, time=t)

        if abs(interpolated_val - stored_val) < tolerance:
            # Redundant — keep removed (or restore if preview only)
            removable.append(t)
            if preview_only:
                # Restore for preview mode
                cmds.setKeyframe(full_attr, time=t, value=stored_val)
                cmds.keyTangent(full_attr, time=(t,t),
                                inAngle=stored_tangents["in"],
                                outAngle=stored_tangents["out"],
                                inTangentType=stored_tangents["inType"],
                                outTangentType=stored_tangents["outType"])
        else:
            # Not redundant — restore key exactly
            cmds.setKeyframe(full_attr, time=t, value=stored_val)
            cmds.keyTangent(full_attr, time=(t,t),
                            inAngle=stored_tangents["in"],
                            outAngle=stored_tangents["out"],
                            inTangentType=stored_tangents["inType"],
                            outTangentType=stored_tangents["outType"])

    return removable
```

---

## Pillar II — Workflow Tools

---

### F-006 · AniBookmarks — Frame Bookmarking

**Goal:** Persistent named frame markers stored in the Maya scene file, rendered on the AniKin timeline strip.

#### Storage Strategy
Store bookmarks as a **custom attribute on a persistent node** in the scene. AniKin creates a transform node named `AniKin_Data` (if it doesn't exist) and uses it as a data store via string attributes.

```python
# workflow/bookmarks.py

import maya.cmds as cmds
import json

STORE_NODE = "AniKin_Data"
BOOKMARK_ATTR = "anikin_bookmarks"

def _ensure_store_node():
    if not cmds.objExists(STORE_NODE):
        cmds.createNode("transform", name=STORE_NODE)
        cmds.setAttr(f"{STORE_NODE}.visibility", False)
        cmds.lockNode(STORE_NODE, lock=True)

def _ensure_attr():
    _ensure_store_node()
    if not cmds.objExists(f"{STORE_NODE}.{BOOKMARK_ATTR}"):
        cmds.addAttr(STORE_NODE, longName=BOOKMARK_ATTR, dataType="string")
        cmds.setAttr(f"{STORE_NODE}.{BOOKMARK_ATTR}", "[]", type="string")

def _load():
    _ensure_attr()
    raw = cmds.getAttr(f"{STORE_NODE}.{BOOKMARK_ATTR}") or "[]"
    return json.loads(raw)

def _save(data):
    _ensure_attr()
    cmds.lockNode(STORE_NODE, lock=False)
    cmds.setAttr(f"{STORE_NODE}.{BOOKMARK_ATTR}", json.dumps(data), type="string")
    cmds.lockNode(STORE_NODE, lock=True)

def add_bookmark(frame, label, color="#FFD700"):
    """Add a named bookmark at the given frame."""
    data = _load()
    # Remove existing bookmark at same frame
    data = [b for b in data if b["frame"] != frame]
    data.append({"frame": frame, "label": label, "color": color})
    data.sort(key=lambda b: b["frame"])
    _save(data)

def remove_bookmark(frame):
    data = [b for b in _load() if b["frame"] != frame]
    _save(data)

def get_all_bookmarks():
    return _load()

def jump_to_bookmark(frame):
    cmds.currentTime(frame, edit=True)
```

---

### F-007 · AniSnap — Pose Snapshot & Restore

```python
# workflow/snap.py

import maya.cmds as cmds
from anikin.utils.rig_utils import get_animated_attrs

class PoseSnap:
    """In-memory pose clipboard. Not persisted to file — session-only."""

    def __init__(self):
        self._slots = {}   # {slot_name: {node: {attr: value}}}

    def capture(self, nodes, slot_name="default"):
        snap = {}
        for node in nodes:
            snap[node] = {}
            for attr in get_animated_attrs(node):
                val = cmds.getAttr(f"{node}.{attr}")
                snap[node][attr] = val
        self._slots[slot_name] = snap
        return True

    def restore(self, nodes=None, slot_name="default"):
        if slot_name not in self._slots:
            cmds.warning(f"AniKin Snap: No snapshot in slot '{slot_name}'.")
            return False

        snap = self._slots[slot_name]
        target_nodes = nodes or list(snap.keys())

        cmds.undoInfo(openChunk=True, chunkName="AniKin_SnapRestore")
        try:
            for node in target_nodes:
                if node not in snap:
                    continue
                for attr, val in snap[node].items():
                    try:
                        cmds.setAttr(f"{node}.{attr}", val)
                    except RuntimeError:
                        pass  # Locked or connected attr — skip silently
        finally:
            cmds.undoInfo(closeChunk=True)
        return True

    def list_slots(self):
        return list(self._slots.keys())

    def clear_slot(self, slot_name):
        self._slots.pop(slot_name, None)

_snap = PoseSnap()

def capture_pose(nodes, slot="default"):
    return _snap.capture(nodes, slot)

def restore_pose(nodes=None, slot="default"):
    return _snap.restore(nodes, slot)
```

---

### F-008 · Smart Selection Sets

#### Storage
Same `AniKin_Data` node, separate attribute `anikin_selection_sets` — JSON string.

```python
# workflow/selection_sets.py

import maya.cmds as cmds
import json

STORE_NODE = "AniKin_Data"
SETS_ATTR  = "anikin_selection_sets"

# (ensure_store_node and attr helpers — same pattern as bookmarks.py, import from shared utils)

def save_set(name, nodes=None):
    """Save current selection (or provided nodes) as a named set."""
    if nodes is None:
        nodes = cmds.ls(selection=True, long=True) or []
    if not nodes:
        cmds.warning("AniKin Sets: Nothing selected to save.")
        return
    data = _load_sets()
    data[name] = nodes
    _save_sets(data)

def load_set(name):
    """Select the nodes in the named set. Skips nodes that no longer exist."""
    data = _load_sets()
    if name not in data:
        cmds.warning(f"AniKin Sets: Set '{name}' not found.")
        return
    existing = [n for n in data[name] if cmds.objExists(n)]
    if existing:
        cmds.select(existing, replace=True)
    if len(existing) < len(data[name]):
        missing = len(data[name]) - len(existing)
        cmds.warning(f"AniKin Sets: {missing} node(s) in '{name}' no longer exist.")

def delete_set(name):
    data = _load_sets()
    data.pop(name, None)
    _save_sets(data)

def list_sets():
    return list(_load_sets().keys())

def _load_sets():
    # Same pattern as bookmarks — load from AniKin_Data node
    ...

def _save_sets(data):
    ...
```

**Attribution reminder:** If this implementation overlaps significantly with Key Machine (GPLv3), add file header:
```python
# AniKin Selection Sets
# Portions of this module are inspired by Key Machine (GPLv3)
# by [Key Machine Author]. Original source: [URL]
# This file is also distributed under GPLv3.
```

---

## Pillar III — Visual Tools

---

### F-009 · AniGhost — Ghost Frame Overlay

#### Implementation Strategy
Ghost frames are rendered using **Maya's native `ghostingControl` node** (available in Maya 2018+), which is the correct production-grade approach. Avoid manual mesh duplication — it's slower and harder to clean up.

```python
# visual/ghost.py

import maya.cmds as cmds

def enable_ghosting(nodes, pre_frames, post_frames, step=2, opacity=0.3):
    """
    Enables Maya's built-in ghosting on the given nodes.
    pre_frames: list of negative offsets, e.g. [-2, -4]
    post_frames: list of positive offsets, e.g. [2, 4]
    step: frame step between ghosts
    """
    all_offsets = sorted(set(pre_frames + post_frames))

    for node in nodes:
        # Enable ghosting on the node
        cmds.setAttr(f"{node}.ghosting", True)
        cmds.setAttr(f"{node}.ghostingMode", 2)  # 2 = Custom frame offsets
        # ghostFrames is a multi-attribute
        cmds.removeMultiInstance(f"{node}.ghostFrames", allChildren=True)
        for i, offset in enumerate(all_offsets):
            cmds.setAttr(f"{node}.ghostFrames[{i}]", offset)
        cmds.setAttr(f"{node}.ghostOpacityRange[0].ghostOpacityRange_FloatValue", opacity)

def disable_ghosting(nodes):
    for node in nodes:
        if cmds.objExists(f"{node}.ghosting"):
            cmds.setAttr(f"{node}.ghosting", False)
```

**Note:** `ghostingMode=2` (custom offsets) is available in Maya 2020+. For 2018-2019, fall back to `ghostingMode=0` (global range) and document the limitation.

---

### F-010 · AniMotion — Arc Visualizer

#### Implementation
Use `cmds.snapshot` to create locator snapshots along the arc, then draw them as a visible curve. For real-time update, register a `scriptJob` on `timeChanged`.

```python
# visual/arc.py

import maya.cmds as cmds

_arc_curves = {}  # {node: arc_curve_transform}

def draw_arc(node, start_frame, end_frame):
    """
    Samples world-space position at each frame and creates a NURBS curve
    representing the arc. Dots at each frame = spacing visualization.
    """
    positions = []
    for frame in range(int(start_frame), int(end_frame) + 1):
        pos = cmds.xform(node, q=True, worldSpace=True, translation=True,
                         time=frame)  # Note: time arg to xform works in Maya cmds
        positions.append(pos)

    if len(positions) < 2:
        return

    # Flatten for curve creation: [x0,y0,z0, x1,y1,z1, ...]
    flat = [v for pos in positions for v in pos]
    degree = min(3, len(positions) - 1)

    curve = cmds.curve(point=list(zip(*[iter(flat)]*3)), degree=degree)
    curve = cmds.rename(curve, f"AniKin_Arc_{node.split('|')[-1].split(':')[-1]}")

    # Visual styling
    cmds.setAttr(f"{curve}.overrideEnabled", True)
    cmds.setAttr(f"{curve}.overrideColor", 13)  # Red

    _arc_curves[node] = curve
    return curve

def clear_arc(node):
    if node in _arc_curves:
        crv = _arc_curves.pop(node)
        if cmds.objExists(crv):
            cmds.delete(crv)

def clear_all_arcs():
    for node in list(_arc_curves.keys()):
        clear_arc(node)
```

**Live update:** Register `cmds.scriptJob(event=["timeChanged", update_arcs_callback])` when arcs are active. Clean up the scriptJob when arcs are disabled. Store the job ID and kill it explicitly on disable.

---

## Pillar IV — Kinematics Tools

---

### F-011 · AniMirror — Pose & Animation Mirror

This is one of the most complex features. The core challenge is correctly identifying mirror pairs and knowing which channels to negate.

#### Naming Convention Detection

```python
# kinematics/mirror.py

import maya.cmds as cmds
import re
from anikin.utils.rig_utils import get_animated_attrs

MIRROR_PATTERNS = [
    (r"_L_", "_R_"),    # _L_ / _R_
    (r"_L$", "_R"),     # suffix _L / _R
    (r"Left", "Right"), # camelCase
    (r"left", "right"), # lowercase
    (r":L_", ":R_"),    # namespace:L_
]

# Channels that are NEGATED on mirror across YZ plane (X mirror)
# This depends on rig convention — expose as configurable
NEGATE_ON_MIRROR = {
    "translateX": True,
    "rotateY": True,
    "rotateZ": True,
}

def find_mirror_pair(node):
    """Returns the mirror counterpart of a node, or None if not found."""
    for pat_l, pat_r in MIRROR_PATTERNS:
        # Try L -> R
        mirrored = re.sub(pat_l, pat_r, node)
        if mirrored != node and cmds.objExists(mirrored):
            return mirrored
        # Try R -> L
        mirrored = re.sub(pat_r, pat_l, node)
        if mirrored != node and cmds.objExists(mirrored):
            return mirrored
    return None

def mirror_pose(source_nodes, frame=None):
    """Mirrors pose from source_nodes to their mirror counterparts at the given frame."""
    if frame is None:
        frame = int(cmds.currentTime(q=True))

    pairs = []
    no_pair = []
    for node in source_nodes:
        pair = find_mirror_pair(node)
        if pair:
            pairs.append((node, pair))
        else:
            no_pair.append(node)

    if no_pair:
        cmds.warning(f"AniKin Mirror: No mirror found for: {', '.join(no_pair[:5])}")

    cmds.undoInfo(openChunk=True, chunkName="AniKin_MirrorPose")
    try:
        for src, dst in pairs:
            _mirror_node_at_frame(src, dst, frame)
    finally:
        cmds.undoInfo(closeChunk=True)

def mirror_animation(source_nodes, start_frame, end_frame):
    """Mirrors full animation range frame by frame."""
    pairs = [(n, find_mirror_pair(n)) for n in source_nodes]
    pairs = [(s, d) for s, d in pairs if d]

    cmds.undoInfo(openChunk=True, chunkName="AniKin_MirrorAnim")
    try:
        for frame in range(int(start_frame), int(end_frame) + 1):
            for src, dst in pairs:
                _mirror_node_at_frame(src, dst, frame)
                cmds.setKeyframe(dst, time=frame)
    finally:
        cmds.undoInfo(closeChunk=True)

def _mirror_node_at_frame(src, dst, frame):
    for attr in get_animated_attrs(src):
        val = cmds.getAttr(f"{src}.{attr}", time=frame)
        mirrored_val = -val if NEGATE_ON_MIRROR.get(attr, False) else val
        try:
            cmds.setAttr(f"{dst}.{attr}", mirrored_val)
        except RuntimeError:
            pass  # Locked / connected
```

**Known limitation:** World-space mirroring for IK handles requires converting to world space before negating and converting back. Document as a V2.1 enhancement — implement local-space mirror for V2 release, flag IK controls in the UI.

---

### F-012 · Foot Slide Detector

```python
# kinematics/foot_slide.py

import maya.cmds as cmds
import math

def detect_foot_slide(foot_controls, start_frame, end_frame,
                      slide_threshold=0.01, plant_y_threshold=0.05):
    """
    foot_controls: list of control names to analyze
    slide_threshold: XZ movement (world units) per frame considered "sliding"
    plant_y_threshold: Y height below which the foot is considered "planted"

    Returns: {control: [(slide_start, slide_end), ...]}
    """
    results = {}

    for ctrl in foot_controls:
        planted_ranges = []
        slide_events = []
        prev_xz = None
        in_slide = False
        slide_start = None

        for frame in range(int(start_frame), int(end_frame) + 1):
            world_pos = cmds.xform(ctrl, q=True, worldSpace=True, translation=True,
                                   time=frame)
            x, y, z = world_pos

            is_planted = y < plant_y_threshold

            if is_planted and prev_xz is not None:
                dx = x - prev_xz[0]
                dz = z - prev_xz[1]
                dist = math.sqrt(dx*dx + dz*dz)

                if dist > slide_threshold:
                    if not in_slide:
                        in_slide = True
                        slide_start = frame
                else:
                    if in_slide:
                        slide_events.append((slide_start, frame - 1))
                        in_slide = False
            elif in_slide:
                slide_events.append((slide_start, frame - 1))
                in_slide = False

            if is_planted:
                prev_xz = (x, z)
            else:
                prev_xz = None

        if in_slide:
            slide_events.append((slide_start, int(end_frame)))

        if slide_events:
            results[ctrl] = slide_events

    return results

def report_slide(results):
    """Prints a readable report to the Maya script editor."""
    if not results:
        print("AniKin Foot Slide: No sliding detected. Clean!")
        return
    for ctrl, events in results.items():
        print(f"\nAniKin Foot Slide — {ctrl}:")
        for start, end in events:
            print(f"  Frames {start}–{end} ({end - start + 1} frames of slide)")
```

**Auto-fix mode (V2.1 scope):** For each slide range, read the foot position at the start of the slide, and bake that fixed position across the slide range. Flag this as experimental — it works on simple cases but breaks when the animator intentionally moves the foot during a plant phase.

---

## Pillar V — Pipeline Tools

---

### F-013 · AniExport + Unreal Validator

```python
# pipeline/export.py

import maya.cmds as cmds
import os

class ExportValidator:
    """Runs pre-export validation checks and collects pass/fail results."""

    def __init__(self, export_target="unreal"):
        self.target = export_target
        self.results = []  # [(check_name, passed, message)]

    def run_all(self):
        self.results = []
        self._check_root_bone()
        self._check_units()
        self._check_framerate()
        self._check_unbaked_constraints()
        self._check_namespaces()
        self._check_negative_scale()
        self._check_anim_range()
        return self.results

    def all_critical_pass(self):
        critical = [r for r in self.results if r[0].startswith("CRITICAL")]
        return all(r[1] for r in critical)

    def _check_root_bone(self):
        joints = cmds.ls(type="joint")
        roots = [j for j in joints if not cmds.listRelatives(j, parent=True, type="joint")]
        if not roots:
            self.results.append(("CRITICAL_root_bone", False, "No root joint found."))
        elif len(roots) > 1:
            self.results.append(("CRITICAL_root_bone", False,
                                 f"Multiple root joints: {roots}"))
        else:
            root = roots[0]
            pos = cmds.xform(root, q=True, worldSpace=True, translation=True)
            at_origin = all(abs(v) < 0.001 for v in pos)
            self.results.append((
                "CRITICAL_root_bone",
                at_origin,
                "OK" if at_origin else f"Root '{root}' not at world origin on frame 1."
            ))

    def _check_units(self):
        unit = cmds.currentUnit(q=True, linear=True)
        expected = "cm" if self.target == "unreal" else "cm"
        passed = unit == expected
        self.results.append((
            "CRITICAL_units", passed,
            f"Unit is '{unit}' — expected '{expected}'." if not passed else "OK"
        ))

    def _check_framerate(self):
        fps_map = {"film": 24, "game": 30, "pal": 25, "ntsc": 30}
        current_fps_str = cmds.currentUnit(q=True, time=True)
        self.results.append((
            "WARNING_framerate", True,
            f"Scene framerate: {current_fps_str}. Verify against target spec."
        ))

    def _check_unbaked_constraints(self):
        constraints = cmds.ls(type=["parentConstraint", "pointConstraint",
                                     "orientConstraint", "scaleConstraint"])
        self.results.append((
            "CRITICAL_constraints",
            not bool(constraints),
            "Unbaked constraints found — bake before export." if constraints else "OK"
        ))

    def _check_namespaces(self):
        non_default = [ns for ns in cmds.namespaceInfo(listOnlyNamespaces=True,
                                                        recurse=True)
                       if ns not in ("UI", "shared")]
        self.results.append((
            "WARNING_namespaces",
            not bool(non_default),
            f"Non-default namespaces: {non_default}." if non_default else "OK"
        ))

    def _check_negative_scale(self):
        joints = cmds.ls(type="joint")
        bad = []
        for j in joints:
            sx, sy, sz = cmds.getAttr(f"{j}.scale")[0]
            if sx < 0 or sy < 0 or sz < 0:
                bad.append(j)
        self.results.append((
            "CRITICAL_negative_scale",
            not bool(bad),
            f"Negative scale joints: {bad}." if bad else "OK"
        ))

    def _check_anim_range(self):
        start = cmds.playbackOptions(q=True, animationStartTime=True)
        end = cmds.playbackOptions(q=True, animationEndTime=True)
        passed = end > start
        self.results.append((
            "CRITICAL_anim_range", passed,
            f"Animation end ({end}) must be after start ({start})." if not passed else "OK"
        ))


def export_fbx(filepath, validator=None):
    """
    Runs validation, prompts on failure, then exports FBX.
    """
    if validator is None:
        validator = ExportValidator()

    validator.run_all()

    if not validator.all_critical_pass():
        failed = [r for r in validator.results if not r[1] and r[0].startswith("CRITICAL")]
        msg = "\n".join(f"• {r[2]}" for r in failed)
        result = cmds.confirmDialog(
            title="AniKin Export — Critical Checks Failed",
            message=f"The following issues must be resolved:\n\n{msg}\n\nExport anyway?",
            button=["Export Anyway", "Cancel"],
            defaultButton="Cancel"
        )
        if result == "Cancel":
            return False

    # Execute FBX export via MEL (Maya's FBX plugin exposes MEL commands)
    cmds.loadPlugin("fbxmaya", quiet=True)
    mel_cmd = f'FBXExport -f "{filepath}" -s'
    import maya.mel as mel
    mel.eval(mel_cmd)
    return True
```

---

### F-016 · AniCheck — Animation Health Report

```python
# pipeline/health_check.py

import maya.cmds as cmds
import math
from anikin.utils.rig_utils import get_animated_attrs

def run_health_check(nodes, start_frame, end_frame):
    """
    Returns list of issue dicts:
    {"severity": "ERROR"|"WARNING"|"INFO", "node": str, "attr": str,
     "frame": int|None, "message": str}
    """
    issues = []
    for node in nodes:
        issues += _check_gimbal_risk(node, start_frame, end_frame)
        issues += _check_redundant_keys(node)
        issues += _check_key_density_spikes(node, start_frame, end_frame)
        issues += _check_missing_end_key(node, end_frame)
    return issues

def _check_gimbal_risk(node, start, end):
    """Detects rotation channels approaching gimbal-prone configurations."""
    issues = []
    rot_attrs = ["rotateX", "rotateY", "rotateZ"]
    for attr in rot_attrs:
        full = f"{node}.{attr}"
        if not cmds.objExists(full):
            continue
        for frame in range(int(start), int(end) + 1):
            val = cmds.getAttr(full, time=frame)
            # Gimbal risk: values near ±90 on the middle rotation axis
            if attr == "rotateY" and abs(abs(val) - 90) < 10:
                issues.append({
                    "severity": "WARNING",
                    "node": node,
                    "attr": attr,
                    "frame": frame,
                    "message": f"Gimbal risk: {attr} = {val:.1f}° near ±90°"
                })
                break  # One warning per channel is enough
    return issues

def _check_redundant_keys(node):
    """Finds keys where all values match neighbors exactly."""
    issues = []
    for attr in get_animated_attrs(node):
        full = f"{node}.{attr}"
        times = cmds.keyframe(full, q=True, timeChange=True) or []
        values = cmds.keyframe(full, q=True, valueChange=True) or []
        for i in range(1, len(times) - 1):
            if abs(values[i] - values[i-1]) < 1e-6 and abs(values[i] - values[i+1]) < 1e-6:
                issues.append({
                    "severity": "INFO",
                    "node": node,
                    "attr": attr,
                    "frame": int(times[i]),
                    "message": f"Redundant key at frame {int(times[i])} — value matches neighbors."
                })
    return issues

def _check_key_density_spikes(node, start, end):
    """Flags anomalously dense key clusters (potential accidental over-keying)."""
    issues = []
    total_frames = end - start + 1
    for attr in get_animated_attrs(node):
        full = f"{node}.{attr}"
        key_count = cmds.keyframe(full, q=True, keyframeCount=True,
                                  time=(start, end)) or 0
        density = key_count / total_frames if total_frames > 0 else 0
        if density > 0.9 and key_count > 10:
            issues.append({
                "severity": "WARNING",
                "node": node,
                "attr": attr,
                "frame": None,
                "message": f"Key density {density:.0%} — possible over-keying or baked data."
            })
    return issues

def _check_missing_end_key(node, end_frame):
    """Warns if no key exists on the final frame of the animation range."""
    issues = []
    for attr in get_animated_attrs(node):
        full = f"{node}.{attr}"
        last_t = cmds.findKeyframe(full, which="last")
        if last_t is not None and int(last_t) < int(end_frame):
            issues.append({
                "severity": "WARNING",
                "node": node,
                "attr": attr,
                "frame": int(end_frame),
                "message": f"No key on last frame ({end_frame}). Last key at {int(last_t)}."
            })
    return issues
```

---

## UI Architecture

### Main Panel
AniKin uses a dockable `maya.cmds` window hosted in a `workspaceControl`. This keeps it non-blocking and Maya-native.

```python
# ui/main_panel.py

import maya.cmds as cmds

PANEL_NAME = "AniKinPanel"
WORKSPACE_CTRL = "AniKinWorkspace"

def show_panel():
    if cmds.workspaceControl(WORKSPACE_CTRL, exists=True):
        cmds.workspaceControl(WORKSPACE_CTRL, edit=True, restore=True)
        return

    cmds.workspaceControl(
        WORKSPACE_CTRL,
        label="AniKin",
        initialWidth=280,
        minimumWidth=220,
        uiScript="from anikin.ui.main_panel import _build_ui; _build_ui()"
    )

def _build_ui():
    """Builds the AniKin panel UI. Called by workspaceControl uiScript."""
    parent = cmds.workspaceControl(WORKSPACE_CTRL, q=True, uiScript=True)
    # Build tabbed layout — one tab per pillar
    tabs = cmds.tabLayout(parent=parent)
    _build_core_tab(tabs)
    _build_workflow_tab(tabs)
    _build_visual_tab(tabs)
    _build_kinematics_tab(tabs)
    _build_pipeline_tab(tabs)

def _build_core_tab(parent):
    col = cmds.columnLayout(parent=parent, adjustableColumn=True, rowSpacing=4)
    cmds.frameLayout(label="Ground", collapsable=True, parent=col)
    cmds.button(label="Ground Selected Object(s)",
                command=lambda _: __import__("anikin.core.ground",
                                             fromlist=["ground_objects"]).ground_objects())
    # ... (other core tools follow same pattern)
```

### AniKin Timeline Strip
The AniKin timeline strip is a custom `QWidget` (using Maya's `shiboken`/`PySide2` bridge) rendered below or alongside Maya's native timeline. It displays:
- Frame range selection (shift-drag)
- Bookmark markers (colored dots)
- Key density overview (minimap bars)

```python
# ui/timeline_strip.py — PySide2 widget skeleton

from PySide2 import QtWidgets, QtCore, QtGui
import maya.cmds as cmds

class AniKinTimelineStrip(QtWidgets.QWidget):
    rangeSelected = QtCore.Signal(int, int)  # (start, end)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(24)
        self._drag_start = None
        self._drag_end = None
        self._bookmarks = []

    def refresh_bookmarks(self, bookmarks):
        self._bookmarks = bookmarks
        self.update()

    def mousePressEvent(self, event):
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            self._drag_start = self._pixel_to_frame(event.x())

    def mouseMoveEvent(self, event):
        if self._drag_start is not None:
            self._drag_end = self._pixel_to_frame(event.x())
            self.update()

    def mouseReleaseEvent(self, event):
        if self._drag_start is not None and self._drag_end is not None:
            start = min(self._drag_start, self._drag_end)
            end   = max(self._drag_start, self._drag_end)
            self.rangeSelected.emit(start, end)
        self._drag_start = None
        self._drag_end = None

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        # Background
        painter.fillRect(self.rect(), QtGui.QColor(40, 40, 40))
        # Draw selection range
        if self._drag_start is not None and self._drag_end is not None:
            x1 = self._frame_to_pixel(min(self._drag_start, self._drag_end))
            x2 = self._frame_to_pixel(max(self._drag_start, self._drag_end))
            painter.fillRect(x1, 0, x2 - x1, self.height(),
                             QtGui.QColor(100, 180, 255, 80))
        # Draw bookmarks
        for bm in self._bookmarks:
            x = self._frame_to_pixel(bm["frame"])
            color = QtGui.QColor(bm.get("color", "#FFD700"))
            painter.setPen(color)
            painter.drawLine(x, 0, x, self.height())
            painter.drawText(x + 2, 12, bm["label"])

    def _frame_to_pixel(self, frame):
        start = cmds.playbackOptions(q=True, min=True)
        end   = cmds.playbackOptions(q=True, max=True)
        ratio = (frame - start) / max(end - start, 1)
        return int(ratio * self.width())

    def _pixel_to_frame(self, px):
        start = cmds.playbackOptions(q=True, min=True)
        end   = cmds.playbackOptions(q=True, max=True)
        ratio = px / max(self.width(), 1)
        return int(start + ratio * (end - start))
```

---

## Testing Strategy

### Unit Tests
Use `pytest` with Maya's `mayapy` interpreter. Each module has a corresponding `tests/test_<module>.py`.

```
mayapy -m pytest tests/ -v
```

### Test Scaffold Example

```python
# tests/test_ground.py

import maya.standalone
maya.standalone.initialize()

import maya.cmds as cmds
import pytest
from anikin.core.ground import ground_objects

def setup_function():
    cmds.file(new=True, force=True)

def test_ground_simple_cube():
    cube = cmds.polyCube()[0]
    cmds.move(0, 5, 0, cube)  # Move cube 5 units up
    ground_objects([cube])
    bbox = cmds.exactWorldBoundingBox(cube, calculateExactly=True)
    assert abs(bbox[1]) < 1e-4, f"Lowest point should be at Y=0, got {bbox[1]}"

def test_ground_already_grounded():
    cube = cmds.polyCube()[0]
    # Default cube is centered at origin — ymin = -0.5
    ground_objects([cube])
    bbox = cmds.exactWorldBoundingBox(cube, calculateExactly=True)
    assert abs(bbox[1]) < 1e-4

def test_ground_no_selection_warns(capsys):
    cmds.select(clear=True)
    ground_objects()  # Should warn, not error
```

---

## Undo Philosophy

Every user-facing action in AniKin must be **undoable in a single Ctrl+Z**. Rules:

1. **Always** wrap multi-step operations in `cmds.undoInfo(openChunk=True)` / `closeChunk`.
2. Use `try/finally` to guarantee the chunk closes even if an exception occurs.
3. Name every chunk: `chunkName="AniKin_OperationName"` — this appears in Maya's undo history.
4. Never call `cmds.undo()` or `cmds.redo()` from within AniKin code.
5. Read-only operations (queries, previews, health checks) must NOT open undo chunks.

---

## Error Handling Standard

```python
# Standard pattern for all AniKin operations

import maya.cmds as cmds

def _safe_execute(fn, *args, **kwargs):
    """Wraps a function call with AniKin's standard error handling."""
    try:
        return fn(*args, **kwargs)
    except RuntimeError as e:
        cmds.warning(f"AniKin: {e}")
    except Exception as e:
        cmds.error(f"AniKin unexpected error: {e}")  # cmds.error raises, stops execution
```

---

*AniKin V2 · Features: How To Build Them · GPLv3 · Animation Kinematics Toolkit for Maya*
*Companion: `anikin_v2_features_what.md` | Next: `anikin_v2_strategic_roadmap.md`*