  AniKin V2 — Features: What They Do

AniKin V2 · Document Series · 02 of 04

Features:  
_What They Do_
==========================

Every feature defined from the animator's perspective — what it is, why it exists, what the user experience looks like, and what edge cases must be handled. No implementation details here. This document answers: **"What are we building?"**

Companion Doc03 · Features: How (Implementation)

Total Features21 defined

New in V29 features

[Core Anim](#pillar-core) [Workflow](#pillar-workflow) [Visual](#pillar-visual) [Kinematics](#pillar-kinematics) [Pipeline](#pillar-pipeline) [Proposed New](#proposed)

Pillar I

Core Animation Tools
--------------------

These are the daily-driver tools. Every animator uses these every single day. They must be rock-solid, fast, and zero-friction to invoke. A bug here is a production blocker.

F-001 · Set Object to Ground
----------------------------

F-001

### Set Object to Ground

Drop any mesh, object, or group so it rests exactly on Maya's world ground plane (Y=0).

Core Anim Critical Priority V2 Addition

What It Does

Automatically calculates the lowest point of the selected object's bounding box and translates the object on the Y axis until that lowest point sits at exactly Y=0 — the world ground plane in Maya. It works on any transformable node: polygon meshes, NURBS surfaces, locators, groups, rigs, or imported assets.

Animator Scenario

**The Problem:** An animator imports a character or prop that was modeled off-center or with arbitrary Y offset. Before blocking, they need it sitting on the ground. Currently: they drag the Y translate channel, eyeball it, adjust, repeat — often taking 30–60 seconds and still landing slightly above or below the floor.  
  
**With AniKin:** Select the object. Click "Ground It." Done in under a second, pixel-perfect.

Animator Benefits

*   Eliminates manual Y-axis hunting — zero guesswork
*   Works on complex rigs (calculates the actual mesh bounding box, not just the root pivot)
*   Saves time on every single prop and character scene setup
*   Particularly useful for crowd animators setting up multiple characters
*   Non-destructive — only modifies translateY, nothing else

User Experience Flow

1.  Animator selects any object, group, or rig in the viewport or outliner
2.  Clicks "Ground Object" button in the AniKin shelf/UI panel
3.  Object snaps to Y=0 — the lowest geometry point now touches the ground plane
4.  Maya's undo stack is updated — Ctrl+Z reverses it cleanly

Edge Cases & Constraints

**Multiple selection:** When multiple objects are selected, either each is grounded independently to Y=0 based on its own bounding box or if there are multiple objects are selected and Ground Object btn is hit the objects set to the ground but keeping the offsets of the other objects unchanged! [User Selected > Options a. Ground Each Individually b. Ground All to Last Selection's Ground (Keep Offset and Ground it to the last selected object's grounded position)]

**Grouped rigs:** If a character group is selected, the tool calculates bounding box of all children, not just the root node's pivot.

**Frozen transforms:** Must account for objects with frozen transforms — use world-space bounding box, not local pivot position.

**Objects already at ground:** Should detect and skip (or silently succeed) if the object is already correctly grounded. No error, no noise.

**Pivot offset:** If the pivot has been manually moved, the tool still operates on the geometry bounding box, not the pivot point.

F-002 · Key Nudge (Shift Keyframes by N Frames)
-----------------------------------------------

F-002

### Key Nudge — Shift Selected Keyframes by N Frames

Select a range or individual keys in the timeline, then push them forward or backward by a precise number of frames.

Core Anim Critical Priority V2 Addition

What It Does

Provides a precise numeric nudge for keyframes. The animator selects a range on the timeline (via shift-click drag to range), or individually selects specific keys in the Graph Editor, then inputs a frame offset amount (e.g. +1, -3, +12) and clicks nudge buttons to move all selected keys by that exact amount.

This is not the same as dragging keys — dragging is imprecise and can accidentally snap to wrong frames. This tool guarantees frame-perfect placement.

Animator Scenario

**The Problem:** An animator has a walk cycle with 24 keys blocked out. The director says "shift the whole thing one frame later so it reads on a different beat." Manually selecting all keys and dragging is error-prone — it's easy to miss a key, or accidentally add a frame of offset on only some curves.  
  
**With AniKin:** Shift-drag to select the range in the AniKin{Maya} timeline strip. Enter "1" in the nudge field. Click the "+1 →" button. All keys in that range shift exactly one frame. Undo with Ctrl+Z. ~Customizable with hotkeys (left and right arrow keys to nudge by 1 frame, up and down arrow keys to nudge by 10 frames) or by using shift key modifier for larger increments.<--For eg~ 

Interaction Design

The tool has two selection modes that work in conjunction:

*   **Timeline Range Selection:** Shift-click drag on the AniKin timeline strip highlights a frame range. All keyframes of all selected objects within that range are considered "selected" for nudging.
*   **Graph Editor Selection:** If the animator has manually selected specific keys in Maya's Graph Editor, the nudge operates only on those selected keys — giving fine-grained control.
*   **Nudge field:** A numeric input where the animator types any integer (or +1/-1 with buttons). Supports both positive and negative values.
*   **Nudge buttons:** "+N →" to push forward, "← -N" to pull backward. Optionally, arrow buttons that default to ±1 for rapid single-frame adjustments. ~Customizable with hotkeys (left and right arrow keys to nudge by 1 frame, up and down arrow keys to nudge by 10 frames) or by using shift key modifier for larger increments.<--For eg~ 

User Experience Flow

1.  Select object(s) in viewport
2.  In AniKin panel: shift-click drag to select a frame range on the mini-timeline, OR select keys directly in Graph Editor
3.  Type a nudge amount in the number field (e.g. "3") or use the preset ±1 buttons
4.  Click the nudge direction button (→ forward or ← backward)
5.  All keys in range shift by the exact amount. Undo-able in one step.

Edge Cases

**Collision with existing keys:** If a nudged key would land on a frame that already has a key, the tool must warn the animator and offer to merge or overwrite — never silently overwrite.

**Fractional frames:** Only integer frame nudging is supported. Fractional frames create subframe keys which cause issues in most pipelines.

**Multi-attribute selection:** When a rig is selected, the nudge must apply to all animated attributes (all channels), not just translateX or visible curves.

F-003 · Keyframe Duplicate & Slide
----------------------------------

F-003

### Keyframe Duplicate & Slide

Select a range of keys, duplicate them as a block, then drag/place the duplicated block anywhere on the timeline.

Core Anim Critical Priority V2 Addition

What It Does

Allows the animator to select a contiguous block of keyframes from the timeline, duplicate that entire block (preserving all values and tangents), and then interactively slide the duplicated block to a new position on the timeline. This is the animation equivalent of copy-paste with visual placement feedback.

Animator Scenario

**The Problem:** A character has a bounce — frames 1–12 cover the fall and impact. Frames 13–24 need to be a second, similar bounce. Without this tool, the animator selects the first 12 frames' keys, copies them, pastes at frame 13, and prays Maya doesn't mangle the tangents or offset channels incorrectly.  
  
**With AniKin:** Shift-select frames 1–12 on the AniKin strip {Maya Timeline Strip}. Click "Duplicate Block." A ghost copy appears. Drag it to frame 13. Release. The duplicated keys are placed perfectly, with all tangents preserved. The animator modifies only what needs changing for the second bounce. ~~(Customizable with hotkeys (left and right arrow keys to nudge by 1 frame, up and down arrow keys to nudge by 10 frames) or by using shift key modifier for larger increments.) <--For eg~ 

Key Behaviours

*   Duplicated block is offset-relative — it maintains internal timing, only the absolute position changes
*   Tangent types are fully preserved (auto, spline, linear, clamped, etc.)
*   Works across all animated channels simultaneously — not one curve at a time
*   Visual preview: a ghost or highlighted strip shows where the block will land before release
*   Dragging can be snapped to frame (integer only)
*   Keyboard shortcut for placing: type exact destination frame number instead of dragging

User Experience Flow

1.  Select objects in viewport
2.  Shift-drag on AniKin timeline strip to select the key range to duplicate
3.  Click "Duplicate Block" button
4.  A draggable "ghost" key block appears, ready to be positioned
5.  Drag the ghost block to the desired destination frame, or type the frame number directly
6.  Click "Place" or press Enter to commit. Undo works on the entire operation in one step.

Edge Cases

**Overlapping destination:** If the duplicated block overlaps with existing keys, prompt with options: Overwrite / Merge / Offset to first free frame.

**Multi-object selection:** Duplication applies simultaneously to all selected objects' key data. The relative timing between objects is preserved.

**Empty range selected:** If the selected range has no keyframes on any channel, inform the animator clearly and do nothing.

F-004 · AniTween
----------------

F-004

### AniTween — Breakdown & Tween Generator

Generate in-between poses by interpolating between two surrounding keyframes at any percentage blend.

Core Anim High Priority Existing Module

What It Does

At the current frame, AniTween reads the values of the previous and next keyframes on all animated channels of the selected object, and sets the current frame's values to a user-specified percentage blend between those two poses. A slider at 0% matches the previous key; 100% matches the next key; 50% is a true mathematical midpoint.

Why It Matters

*   Eliminates manual tweening — previously required calculating every channel value by hand
*   Especially useful for breakdowns, cushion poses, and settling frames
*   Works as inspiration from Tween Machine (GPLv3) — AniKin's implementation must be independent
*   Real-time slider preview: as the animator drags, the pose updates live in the viewport

Edge Cases

**No surrounding keys:** If the current frame has no previous or next key on a channel, that channel is skipped (not zeroed out).

**Keying:** The tool should key the result at the current frame — not leave it as a driven pose.

F-005 · Smart Key
-----------------

F-005

### Smart Key — Context-Aware Keying

Set keys only on channels that have actually changed since the last key — not on every channel blindly.

Core Anim High Priority V2 New Module

What It Does

When the animator presses the "Smart Key" button, the tool compares the current values of all animated channels against their most recent keyframed values. Only channels that have a meaningful difference (above a configurable threshold) receive a new keyframe. This prevents the graph editor from filling up with redundant keys on static channels.

Animator Benefits

*   Dramatically cleaner animation curves — no keys on channels that didn't move
*   Reduces graph editor clutter, especially on complex rigs with 100+ channels
*   Speeds up spline refinement and cleanup passes
*   Threshold is configurable: e.g. "only key if value changed by more than 0.001"

Pillar II

Workflow Tools
--------------

Tools that organize the animator's session, reduce repetitive selection steps, and put controls where fingers expect them. Often more time-saving per hour than advanced features.

F-006 · AniBookmarks — Frame Bookmarking
----------------------------------------

F-006

### AniBookmarks

Bookmark named frame positions and jump between them instantly. Like browser bookmarks, but for your timeline.

Workflow High Priority V2 New Module

What It Does

Lets the animator mark specific frames with custom labels (e.g. "Contact L", "Peak", "Land", "Hold End"). These bookmarks appear as colored markers on the AniKin timeline strip {Maya Timeline Strip}. Clicking a bookmark instantly scrubs to that frame. Bookmarks are saved per-scene in the Maya file.

Animator Benefits

*   No more typing frame numbers to jump around a complex shot
*   Essential for long shots: jump between the four contact poses instantly
*   Color-coded bookmarks for different animation phases (blocking, spline, polish)
*   Saved with scene file — bookmarks survive file reopen
*   Quick rename and delete from the marker

F-007 · AniSnap — Pose Snapshot
-------------------------------

F-007

### AniSnap — Pose Snapshot & Restore

Capture the current pose of a rig in memory, explore freely, and restore it exactly with one click.

Workflow High Priority V2 New Module

What It Does

A temporary in-session clipboard for poses. The animator captures the current channel values of selected controls into a named "snap slot" (no keyframe is set). They can then freely manipulate, explore, or reference the pose elsewhere, then hit "Restore" to instantly snap back to the saved values.

Animator Benefits

*   Risk-free pose exploration — always a safety net to return to
*   Multiple snap slots allow comparing multiple pose options
*   Useful for mirroring workflows: snap left side, mirror to right, restore as reference
*   Faster than setting a temp keyframe and deleting it

F-008 · Smart Selection Sets
----------------------------

F-008

### Smart Selection Sets

Save named groups of rig controls and re-select them with a single click or hotkey.

Workflow High Priority Existing Module

What It Does

Allows the animator to select a group of rig controls (e.g. "all left arm controls," "all foot controls," "IK body controls"), name the set, and recall that selection instantly. Sets persist in the scene file. Assignable to hotkeys.

Animator Benefits

*   No more tediously re-selecting the same 12 controls every time
*   Critical for body part pass workflows (arms pass, legs pass, face pass)
*   Hotkey-assignable for maximum speed
*   Sets are rig-aware and can be transferred between scenes with the same rig

Attribution Note

**Open question (see Strategy doc):** If the Selection Sets implementation significantly overlaps with Key Machine (GPLv3), the module must carry proper GPLv3 attribution to Key Machine's author. This must be resolved before V2 release of this module.   <--This has been sought we can proceed! 

Pillar III

Visual Animation Tools
----------------------

Tools that help the animator judge motion quality visually — arcs, ghost frames, and pose comparison — without leaving Maya or exporting a playblast.

F-009 · AniGhost — Onion Skinning
---------------------------------


F-009

### AniGhost — Ghost Frame Overlay

Display semi-transparent copies of the rig at N frames before and after the current frame, like traditional onion skinning.

Visual Medium Priority Existing Module

What It Does

Renders ghosted (semi-transparent) copies of the selected rig at user-specified frame offsets — for example, -2, -4, +2, +4 frames. The animator can judge spacing, overlaps, and anticipations without scrubbing back and forth.

Animator Benefits

*   Replicates traditional animation paper onion-skinning in 3D
*   Immediately surfaces spacing errors — too-even spacing vs. ease-in/ease-out visible at a glance
*   Configurable: number of ghosts, frame step, ghost opacity, ghost color tinting
*   Toggle on/off quickly — doesn't interfere with playback

F-010 · AniMotion — Arc Visualizer
----------------------------------

F-010

### AniMotion — Motion Arc Visualizer

Draw the motion path of any rig control as a smooth arc directly in the viewport, with frame-position dots.

Visual Medium Priority Existing Module

What It Does

Draws the world-space trajectory of a selected control's motion as a visible arc in the viewport, with small dots at each frame position indicating spacing. The arc updates in real time as the animator adjusts keys. Color indicates direction of travel.

Animator Benefits

*   Broken or kinked arcs are instantly visible — no more "almost right" wrist arcs
*   Spacing dots reveal uneven timing at a glance
*   Critical for hand/wrist, head, and hip trajectory polish
*   Works on any control: hand, head, COM, prop, camera

Pillar IV — The Signature Pillar

Kinematics Tools
----------------

This is where AniKin earns its name. These tools understand rigs, body mechanics, and kinematic relationships. No free Maya tool does this comprehensively. This is the territory AniKin must own.

F-011 · AniMirror — Pose Mirror
-------------------------------

F-011

### AniMirror — Pose & Animation Mirror

Mirror a pose or an animation range from the left side of a rig to the right, or vice versa, with one click.

Kinematics Critical Priority Existing Module

What It Does

Reads the values of all controls on one side of a rig (e.g. L\_arm\_IK, L\_wrist, L\_shoulder) and applies mirrored values to the corresponding controls on the opposite side — accounting for which channels should be negated (rotations vs. translations behave differently across an axis of symmetry). Operates on the current frame for pose mirroring, or on a frame range for animation mirroring.

Animator Benefits

*   Walk cycles: animate right side, mirror to get left — saves ~50% of cycle blocking time
*   Eliminates the mental overhead of manually inverting rotation values
*   Critical for symmetrical actions: jumps, rolls, T-poses, reference poses
*   Requires a rig naming convention mapping (L\_ / R\_, \_L / \_R, Left / Right) — configurable

Edge Cases

**Naming convention flexibility:** Must support multiple common naming patterns. Rigs that don't follow a convention need a manual mapping UI.

**World-space vs local-space:** Some controls need world-space mirroring, others local-space. The tool must handle both correctly per control type.

**IK vs FK:** Mirror mode must detect whether controls are in IK or FK and handle accordingly.

F-012 · Foot Slide Detector
---------------------------

F-012

### Foot Slide Detector

Automatically detect frames where a planted foot is sliding rather than staying grounded — the single most common technical animation error.

Kinematics Critical Priority V2 New Module

What It Does

Analyzes the world-space position of foot controls across a frame range. On frames where a foot should be planted (based on user-defined "contact" markers, or automatically detected from Y-position), it checks if the XZ position is moving — which indicates sliding. Reports problematic frame ranges in a list panel, color-codes them on the timeline, and optionally auto-corrects by baking the foot control to a static position during the slide frames.

Animator Benefits

*   Foot slide is invisible until playback — this makes it visible before the director sees it
*   Saves the animator an entire QC pass before shot review
*   The "fix" mode can automatically lock sliding feet in place, giving the animator a corrected base to refine from
*   Especially valuable for game animation where foot slide is a hard technical failure

Pillar V

Pipeline Tools
--------------

The least glamorous but often most impactful category. Pipeline failures cost hours of rework. AniKin should catch them before export.

F-013 · AniExport + Unreal Validator
------------------------------------

F-013

### AniExport — FBX Export with Unreal Validation

Export animation-ready FBX with pre-export checks for Unreal Engine compatibility issues.

Pipeline High Priority Existing Module

What It Does

Before exporting FBX for Unreal Engine (or any target engine), AniExport runs a validation checklist: root bone presence, unit scale match, frame rate correctness, namespace cleanup, constraint baking, and naming convention sanity. Reports pass/fail per check. Only exports if all critical checks pass (or animator overrides with explicit confirmation).

Validation Checks

*   Root bone exists and is at world origin on frame 1
*   Scene units match target engine (cm for Unreal)
*   Frame rate matches target spec (e.g. 30fps for game, 24fps for film)
*   No constraints remaining unbaked on exported skeleton
*   No Maya namespaces in exported joint names
*   No zero-scale or negative-scale joints
*   Animation range is correctly set (start/end frames)

Proposed — V2 New Features for Team Discussion

Proposed New Feature Additions
------------------------------

These features are proposed for V2 based on production pain points and strategic positioning. Each should be evaluated by the team for scope and priority before implementation begins.

F-014

### AniWave — Wave / Ripple Key Offset

Automatically offset keyframes across a selection of objects to create a natural wave or ripple effect in timing.

Core Anim High Priority V2 Proposed

What It Does

When multiple objects are selected (e.g. fingers on a hand, links in a chain, crowd characters), AniWave progressively offsets each object's keyframes by a configurable frame delay. The first object plays on time; the second plays N frames later; the third plays 2N frames later — creating an organic wave of motion. Delay amount and direction (left-to-right, top-to-bottom, random) are configurable.

Animator Benefits

*   Finger ripples on hand impacts: manually doing this for 10 finger joints takes 10+ minutes. AniWave: 10 seconds.
*   Tail/tentacle ripple offset for creatures
*   Crowd character stagger — randomize delay for naturalistic crowd movement
*   Chain/cloth follow-through overlapping action

F-015

### AniNoise — Procedural Noise Layer

Add natural-looking noise (jitter, tremor, secondary motion) on top of existing animation as a non-destructive layer.

Core Anim High Priority V2 Proposed

What It Does

Applies procedural noise (Perlin or simplex) to specified channels of selected controls. The noise is added on top of existing animation — it doesn't modify original keys. Parameters: amplitude (how much), frequency (how fast), seed (which noise pattern), and per-channel enable/disable. The result can be baked to keyframes or left as a noise expression.

Animator Benefits

*   Camera shake — non-destructive, adjustable at any point
*   Breathing secondary motion on a standing character
*   Hand tremor for elderly or scared characters
*   Cloth/hair auxiliary jitter without simulation
*   Bake option: convert noise to real keyframes for export

F-016

### AniCheck — Animation Health Report

Run a full diagnostic on the current animation and report issues: gimbal lock risk, broken curves, redundant keys, and more.

Pipeline / Kinematics High Priority V2 Proposed

What It Does

Runs a comprehensive diagnostic on the selected rig's animation and generates a report panel listing detected issues by severity (Error / Warning / Info). The animator can click any issue to jump to the relevant frame and control.

Checks Performed

*   **Gimbal Lock Risk:** Detects rotation channels approaching gimbal-prone Euler configurations
*   **Broken Tangents:** Curves with infinity issues or NaN values
*   **Redundant Keys:** Keyframes where all values exactly match neighbors — removable without changing the animation
*   **Key Density Spike:** Frames where key density is anomalously high (often a sign of accidental over-keying)
*   **Foot Slide:** (Integrated from F-012)
*   **Missing End Key:** Animation range has no key on the final frame

F-017

### Root Motion Inspector

Visualize and analyze the root bone's motion curve — essential for game animation and Unreal Engine root motion workflows.

Kinematics / Pipeline Medium Priority V2 Proposed

What It Does

Plots the root bone's world-space trajectory as a visual overlay in the viewport and as a curve graph. Flags anomalies: sudden velocity spikes, non-zero Y root motion where the game engine expects locked Y, or root drift between loop points in a looping animation.

Animator Benefits

*   Critical for game animators — root motion errors cause character teleportation in engine
*   Loop validation: checks if start and end root positions match for seamless cycles
*   Velocity graph reveals foot-plant correlation issues immediately

F-018

### Balance & COM Visualizer

Display an estimated Center of Mass trajectory to help animators maintain believable weight and balance.

Kinematics Medium Priority V2 Proposed

What It Does

Estimates the character's Center of Mass position based on the approximate positions of major body segments (head, chest, pelvis, upper arms, forearms, thighs, calves). Displays it as a visible locator in the viewport that moves with the animation. Also plots a projected ground contact point — useful for checking that a balanced pose's COM projects inside the foot contact area.

Animator Benefits

*   Immediately reveals "floaty" or unbalanced poses — COM projected outside foot base means the character would tip over in reality
*   Useful for action shots: jumps, falls, martial arts — tracks weight arc believability
*   Educational for students learning body mechanics principles

F-019

### Auto Curve Cleanup

Intelligently reduce redundant keyframes while preserving the shape of animation curves within a user-defined tolerance.

Core Anim / Pipeline Medium Priority V2 Proposed

What It Does

Analyzes baked or over-keyed animation curves and removes keyframes that are mathematically redundant — frames where the interpolated value without the key would be within a specified tolerance (e.g. 0.01 units) of the keyed value. The result is cleaner, more readable, and more editable curves without changing the visible animation.

Animator Benefits

*   Baked simulation data commonly has a key on every single frame — cleanup makes it human-editable
*   Dramatically reduces file size for complex shots
*   Tolerance is configurable: tight tolerance (0.001) for high-precision work, loose (0.1) for fast cleanup passes
*   Preview before committing — shows curve before/after comparison

AniKin V2 · Features: What They Do · 21 Features Defined

[01 · Vision](anikin_v2_01_vision_overview.md) [02 · Features: What](anikin_v2_02_features_what.md) [03 · Features: How](anikin_v2_03_features_how.md) [04 · Strategy](anikinv2_04_strategic_direction.md)