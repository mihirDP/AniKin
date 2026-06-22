

| AniKin AniModules *Design & Polish Specification* Six mission-critical modules that transform AniKin from a toolbelt into a complete, professional-grade animator's studio. |
| :---: |

| Module | Purpose | Section |
| :---- | :---- | :---- |
| **🪄 Smart Key** | Drop keys only on channels already animated — no channel pollution | p. 2 |
| **🔖 AniBookmarks** | Save, jump to, and manage named time positions in your scene | p. 4 |
| **🌊 AniWave** | One-click overlap & follow-through propagator for joint chains | p. 6 |
| **📈 AniNoise** | Organic Perlin-noise micro-jitter injected directly into curves | p. 8 |
| **🩺 AniCheck** | Curve health diagnostics: gimbal flips, subframe keys, duplicate keys | p. 10 |
| **📸 AniSnap** | Visual pose library with viewport thumbnail snapshots | p. 12 |

| 🪄  Smart Key *Surgical keyframing — only on channels that already exist in time* |
| :---- |

The native Maya Set Key command is indiscriminate — it drops keyframes on every channel of every selected controller, regardless of whether those channels are animated. Over a session, this creates dozens of **static channels**: flat, unchanging curves that waste memory, clutter the Graph Editor, and make cleanup a chore. Smart Key solves this at the point of creation.

**How it should work**

| Trigger | ti-wand button in the Tween section toolbar (or hotkey, user-assignable) |
| :---- | :---- |
| **Selection scope** | Operates on all currently selected objects simultaneously |
| **Channel filter** | Queries each object via cmds.keyframe() — only channels with existing keys receive the new keyframe |
| **Fallback** | If an object has zero animated channels, shows a non-blocking status bar warning and skips it |
| **Undo** | Single cmds.undoInfo chunk — one Ctrl+Z undoes the entire Smart Key operation |
| **Tangent type** | Respects the user's active tangent preference (Auto / Spline / Custom), same as native setKeyframe |

**Recommended implementation**

| def smart\_key(objects=None):     objs \= objects or cmds.ls(selection=True)     with undo\_chunk('AniKin\_SmartKey'):         for obj in objs:             animated \= cmds.keyframe(obj, query=True, name=True) or \[\]             for curve in animated:                 attr \= curve\_to\_attr(curve)   \# strip obj prefix                 cmds.setKeyframe(obj, attribute=attr) |
| :---- |

| ⚠️ Edge Case:  Locked or non-keyable channels must be silently skipped. Use cmds.getAttr(attr, keyable=True) as a guard before setting. |
| :---- |

**Polish checklist**

* Button tooltip: "Smart Key — set keys only on already-animated channels"

* Show a brief status bar message: "Smart Key: 12 keys set across 3 objects" for feedback

* Right-click context menu on the button: 'Smart Key All', 'Smart Key Translate', 'Smart Key Rotate', 'Smart Key Scale' for channel-group targeting

* Respect Animation Layers — if a layer is selected, keys go on that layer only

* Integration test: run on a rig with 60+ controllers; verify zero static channels are created

**Why this elevates AniKin**

Industry tools like AnimBot's "Set Smart Key" and aTools' "Key Animated" validate this approach. Animators working at pace need to trust that pressing a key button won't pollute their Graph Editor. Smart Key is the single feature that most makes AniKin feel like a **professional studio tool** rather than a hobbyist script.

| 🔖  AniBookmarks *Named time anchors — navigate your scene like a document* |
| :---- |

Long shots with complex timing require constant jumping between important frames: the contact pose at frame 12, the breakdown at 38, the hold at 102\. Without named markers, animators scrub the timeline repeatedly, losing time and mental context. AniBookmarks makes the timeline **navigable and annotated.**

**Data model**

| Storage node | Hidden network node: anikin\_time\_bookmarks (scene-persistent across save/reload) |
| :---- | :---- |
| **Bookmark schema** | { name: str, frame: float, color: str, range\_end: float | None } |
| **Range support** | Optional end frame converts a bookmark into a coloured range highlight |
| **Color coding** | User-selectable from 8 presets: blue (default), red, green, gold, purple, teal, pink, white |
| **Max bookmarks** | Soft cap of 64 per scene — prevents node attribute bloat; warn user at 60 |

**UI Panel specification**

* Toolbar section: Bookmarks — ti-bookmark icon, opens a collapsible QFrame panel

* Save Bookmark: captures current frame \+ user-typed name (default: 'Frame {N}'). One-click, no modal dialog needed

* Bookmark list: each row shows: colored swatch | frame number | name | Jump button | Delete button

* Jump: calls cmds.currentTime(frame) — instant navigation

* Range bookmarks: secondary 'Set Range End' button appears on hover; highlights timeline via cmds.playbackOptions

* Drag to reorder: QListWidget with InternalMove drag-drop to organize bookmarks logically

* Export/Import: JSON file bookmark set — portable between scenes or animator machines

* Search bar: filter the list by name for dense shots

| 💡 Power Feature:  Double-clicking a range bookmark should set both the playback range AND the Time Slider highlight range simultaneously — one click to scope your workspace to an action. |
| :---- |

**Persistence implementation detail**

| \# Store as JSON string on a hidden network node attribute node \= 'anikin\_time\_bookmarks' if not cmds.objExists(node):     cmds.createNode('network', name=node)     cmds.addAttr(node, longName='data', dataType='string')     cmds.setAttr(f'{node}.data', lock=False) cmds.setAttr(f'{node}.data', json.dumps(bookmark\_list), type='string') |
| :---- |

| ⚠️ Risk:  The network node will be deleted if the animator runs 'Delete All History' or 'Optimize Scene'. Add a scene save callback that silently recreates it from a session cache. |
| :---- |

| 🌊  AniWave *One-click overlap & follow-through for joint chains — tails, capes, spines, tentacles* |
| :---- |

Follow-through and overlapping action is one of the 12 Disney principles — and one of the most time-consuming to animate manually. For chain structures (tails, capes, hair, spines, sleeves), the process is always the same: copy root curves, offset by N frames, scale amplitude. AniWave automates this **completely in a single click.**

**Algorithm specification**

| Input | User selects the root-to-tip joint chain (order matters; use selection order) |
| :---- | :---- |
| **Curve source** | Copies all animated channels from the root joint using cmds.copyKey / cmds.pasteKey |
| **Frame offset** | Default: \+2 frames per joint downstream. User-editable in an options popover. |
| **Amplitude scale** | Default: 0.80x per joint (80%). Produces natural decay toward the tip. |
| **Tangent handling** | Re-runs cmds.keyTangent(outTangentType='auto') after paste to prevent linear snapping |
| **Undo** | Single undo chunk wrapping all pasteKey and keyTangent operations |
| **Dry run mode** | Preview overlay shows expected offset in a tooltip before applying |

**Advanced options (right-click popover)**

* Frame Offset: configurable per-joint delay (default 2, range 0.5–10)

* Amplitude Falloff: configurable decay per joint (default 0.80, range 0.5–1.0). Values above 1.0 amplify — useful for whipcrack effects

* Channel Mask: checkboxes for Translate / Rotate / Scale — typically Rotate-only for FK chains

* Tip Damping: extra amplitude reduction on the last 2 joints for a more natural stop

* Reverse Mode: propagate from tip to root instead (for lead-driven animations like a whip throw)

| 💡 Key Insight:  The amplitude scale should be applied as a value scale (cmds.scaleKey), not by manually editing key values. This preserves the curve shape and tangent handles, producing cleaner results than brute-force value multiplication. |
| :---- |

**Use cases to validate against**

1. Dragon tail: 8-joint chain, large rotational amplitude, test tip damping

2. Cape: 5-joint chain with translate \+ rotate, test channel mask

3. Spine secondary: 4-joint spine, test that root is NOT offset (offset starts at joint 2\)

4. Antenna: 3-joint chain with very small movement — test that 0.8x falloff still looks alive at joint 3

| 📈  AniNoise *Organic Perlin-noise micro-jitter — making held poses breathe* |
| :---- |

Perfectly still held poses look dead on screen. Real cameras shake. Real bodies breathe and shift weight. AniNoise injects a thin layer of **procedurally generated, physics-informed noise** into selected animation curves — adding life without destroying the pose work underneath.

**Perlin noise implementation (pure Python, zero dependencies)**

| \# 1D Perlin noise — no numpy or external deps required import random, math def fade(t):    return t \* t \* t \* (t \* (t \* 6 \- 15\) \+ 10\) def lerp(a,b,t): return a \+ t \* (b \- a) class Perlin1D:     def \_\_init\_\_(self, seed=None):         rng \= random.Random(seed)         self.p \= list(range(256))         rng.shuffle(self.p)         self.p \*= 2   \# double for overflow safety     def noise(self, x):         X \= int(math.floor(x)) & 255         x \-= math.floor(x)         u \= fade(x)         a \= self.p\[X\]; b \= self.p\[X+1\]         return lerp(self.\_grad(a, x), self.\_grad(b, x-1), u)     def \_grad(self, h, x):         return x if h & 1 else \-x |
| :---- |

**Application parameters**

| Amplitude | Default 0.3 units/degrees. User-adjustable per-application with a slider in the panel. |
| :---- | :---- |
| **Frequency** | Default 0.05 (gentle, low-frequency sway). Higher \= faster/jerkier noise. |
| **Seed** | Random by default; user can pin a seed for reproducible results. |
| **Frame range** | Operates on the current inner timeline range (highlighted region) only. |
| **Curve target** | Selected curves in the Graph Editor, or all curves on selected objects if Graph Editor has no selection. |
| **Additive** | Adds noise values ON TOP of existing key values — never replaces or destroys existing animation. |
| **Bake density** | Adds one key per frame within the range. Warns user before operating on ranges \> 500 frames. |

| ⚠️ Critical:  AniNoise MUST operate additively — never replace existing keys. The implementation should read existing cmds.keyframe values, add Perlin output, and write back the sum. This ensures the animator's work is always preserved. |
| :---- |

**Noise presets (ship with these out of the box)**

* Idle Breath — very low amplitude (0.15), low frequency (0.03): subtle weight shift for standing holds

* Camera Shake — medium amplitude (0.5), medium frequency (0.08): simulate handheld camera feel on camera objects

* Nervous Energy — medium amplitude (0.4), higher frequency (0.12): tense characters waiting for something to happen

* Drunk/Dizzy — high amplitude (0.9), very low frequency (0.02): slow, large, uncontrolled sway

* Machine Vibration — low amplitude (0.2), very high frequency (0.4): mechanical/robotic jitter

| 🩺  AniCheck *Curve health diagnostics — find and fix hidden problems before they reach render* |
| :---- |

The three issues AniCheck targets — gimbal flips, subframe keys, and duplicate keys — are **invisible during normal playback** but cause real problems: gimbal flips corrupt rotation on export; subframe keys break game engine importers; duplicate keys bloat file size and cause popping. AniCheck surfaces all three with auto-fix.

**Diagnostic definitions**

| Issue | Detection Logic | Severity | Auto-Fix |
| :---- | :---- | :---- | :---- |
| **Gimbal Flip** | Rotation channel value delta between adjacent keys exceeds 170° | Critical — breaks export | Euler filter on affected curves |
| **Subframe Key** | Key time has non-integer component: frame % 1.0 \!= 0.0 | High — breaks game importers | Round to nearest integer frame |
| **Duplicate Key** | Key value equals both surrounding key values (flat island ≥ 3 keys) | Medium — file bloat, pops | Delete redundant middle keys |
| **Infinite Curves** | Pre/Post infinity is not 'constant' on a non-looping shot | Low — unexpected motion | Set infinity to Constant |
| **Zero-length Key** | Two keys on the same frame (same time, different values) | High — undefined behaviour | Merge: keep last-placed key |

**UI panel specification**

* Toolbar: Diagnostics section — ti-stethoscope icon opens the AniCheck panel

* Scope selector: radio buttons for 'Selected Objects' / 'All Objects' / 'Scene'

* Run Scan button: iterates all relevant animation curves; populates the table in under 2s for scenes up to 200 controllers

* Results table columns: Object | Channel | Frame | Issue Type | Severity badge

* Row actions: each row has 'Select Curve' (opens Graph Editor) and 'Fix This' buttons

* Fix All button at the bottom with issue-type checkboxes to batch-fix selectively

* Re-scan after fix: automatically re-runs and shows a 'Clean\!' green banner if zero issues remain

* Export Report: saves diagnostics as a .txt or .csv for pipeline review or supervisor sign-off

| 💡 Pro Tip:  Add a 'Scan on Save' option in AniKin preferences. Animators who enable it get a lightweight check before every scene save — catching issues at creation rather than at delivery. |
| :---- |

| 📸  AniSnap *Visual pose library — save, browse, and apply poses with viewport thumbnail previews* |
| :---- |

A pose library is table stakes for professional animation production. AniSnap goes beyond attribute-list libraries by capturing a **real viewport thumbnail** at the moment of saving — making poses instantly recognisable in a visual grid rather than a list of cryptic names.

**Save Pose — full pipeline**

| 1\. Capture Attributes | cmds.channelBox() or user-selected controllers. Query all keyable, non-locked attributes. Strips namespace (character:) for cross-rig portability. |
| :---- | :---- |
| **2\. Snapshot** | Temporarily isolate-select the character. Call cmds.playblast(frame=\[currentFrame\], format='image', widthHeight=\[256,256\], viewer=False). Move output to AniSnap poses directory. |
| **3\. Serialize** | Write pose as JSON: { name, controls: {attr: value}, thumbnail\_path, timestamp, rig\_hint }. |
| **4\. Index Update** | Append to poses\_index.json in the library directory. UI refreshes automatically via a file watcher. |

**UI panel specification**

* Toolbar: Poses section — ti-camera icon opens AniSnap panel as a dockable widget

* Grid layout: 3-column thumbnail grid, each card \= 256px image \+ pose name below \+ Apply/Delete hover buttons

* Search \+ tag filter bar at the top: search by name, filter by tags (body, face, action, idle, etc.)

* Save Pose button: one click — no modal. Uses current character name as default pose name (editable inline)

* Apply Pose: pastes values directly onto matching attributes. Namespace-stripped matching allows cross-character use

* Apply with Offset: applies the pose but offsets values by the delta from the current pose (non-destructive blend)

* Mirror Pose button: flips L/R attribute naming conventions (L\_arm → R\_arm) for instant mirror application

* Pose Sets / Folders: drag poses into named folders for organisation (walk cycle, jump, idles, etc.)

* Library Paths: AniKin preferences panel allows multiple library roots (local \+ studio shared network drive)

| ⚠️ Namespace Stripping:  This is the single most important robustness feature. The save pipeline must strip 'character:', 'rig:', or any ':' prefix from attribute names before serializing. Without this, poses saved on 'charA:spine' will fail to apply on 'charB:spine'. |
| :---- |

| 💡 Delight Feature:  On hover, the thumbnail card should smoothly enlarge to 2x size with a subtle drop-shadow popup — like a physical Polaroid being picked up. This is a tiny animation but makes AniSnap feel premium. |
| :---- |

# **Cross-Module Standards**

All six AniModules must conform to these shared standards to feel like a single, coherent product rather than six separate scripts stapled together.

## **Error Handling**

* Never let an exception propagate to Maya's Script Editor unhandled — catch and display in AniKin's status bar

* Every destructive operation (AniNoise, AniWave, AniCheck auto-fix) must be wrapped in a single undoInfo chunk

* If selection is empty when a module is triggered, show a status bar message: '\[Module\] — nothing selected' and return early

* Log verbose debug output to a AniKin.log file in the temp directory, controlled by a Debug Mode toggle in preferences

## **Performance Targets**

| Smart Key | \< 100ms for 30 selected controllers |
| :---- | :---- |
| **AniBookmarks** | \< 50ms for save/jump operations; panel open \< 200ms |
| **AniWave** | \< 500ms for an 8-joint chain |
| **AniNoise** | \< 1s per 100 frames of range; warn before processing \> 500 frames |
| **AniCheck scan** | \< 2s for 200 controllers, 5,000 keys |
| **AniSnap save** | \< 3s including viewport playblast; apply pose \< 200ms |

## **UI / UX Consistency**

* All panels open as collapsible QFrame sections inside AniKin's main dockable window — no floating dialogs except the AniCheck diagnostics table

* All icons use the Tabler Icons set already established in AniKin (ti-\* prefix)

* All configurable parameters have tooltips that explain the parameter AND a real-world example of its effect

* Destructive operations show a one-line confirmation in the status bar before executing (not a popup modal — those break flow)

* All modules respect Maya's Undo queue — one Ctrl+Z must always cleanly reverse any module's action

# **Suggested Release Roadmap**

| Phase | Milestone | Modules / Deliverables |
| :---- | :---- | :---- |
| **v0.2** | **Foundation Modules** | Smart Key (highest impact, lowest risk), AniBookmarks (no animation curve touching) |
| **v0.3** | **Physics & Curves** | AniWave (overlap), AniNoise (micro-jitter) — both curve-manipulation modules together |
| **v0.4** | **Quality & Library** | AniCheck (diagnostics \+ auto-fix), AniSnap (pose library \+ thumbnails) |
| **v1.0** | **Polish Release** | Full cross-module testing, performance benchmarks, documentation, PyPI/Maya Module installer |

| *Each of these six modules addresses a real, daily pain point that professional animators encounter in production. Built together with consistent UX, robust undo, and clean Python, they transform AniKin from a promising open-source experiment into a toolkit that animators will reach for every single day.* |
| :---: |

