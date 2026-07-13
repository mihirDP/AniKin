# 🚀 AniKin Key Features & Tools

AniKin is divided into specialized modules, accessible right above your timeline. The toolbar is **fully customizable** — you can hide or reorder sections in the Settings panel!

### 🟠 Pose & Transform Tools
Your bread and butter tools for manipulating objects and keys.

* <img src="../AniKin/scripts/anikin/icons/reset.svg" width="18"> **Reset Pose:** Instantly zero out translation and rotation (leaving scale at 1.0).
* <img src="../AniKin/scripts/anikin/icons/mirror_pose.svg" width="18"> **Mirror & Flip Pose:** Negates TX, TZ, and RY to mirror a pose, or swaps poses between Left/Right controls automatically. (Right-click for options)
* <img src="../AniKin/scripts/anikin/icons/copy_pose.svg" width="18"> **Copy/Paste Pose:** Stores your current pose in memory to paste elsewhere. **Pro Tip:** Shift+Click on the timeline to highlight a range, then Copy to capture an entire animated block!
* <img src="../AniKin/scripts/anikin/icons/camera.svg" width="18"> **AniSnap:** Visual Pose Library — capture viewport screenshots of poses and apply them back to the rig.

### 🎨 Tweening & Easing
Our custom slider engine gives you absolute control over your breakdowns.

* **TW (Tween Slider):** Linearly blends your current pose between the previous and next keyframes. Push it past 100% or below 0% for instant overshoots!
* **EA (Ease Slider):** Uses a smooth ease-in/ease-out curve. Perfect for organic breakdowns.
* <img src="../AniKin/scripts/anikin/icons/smart_key.svg" width="18"> **Smart Key:** Sets a keyframe *only* on channels that already have animation, keeping your curves clean.

### 🟠 Tangents & Curves
* <img src="../AniKin/scripts/anikin/icons/spline.svg" width="18"> <img src="../AniKin/scripts/anikin/icons/linear.svg" width="18"> <img src="../AniKin/scripts/anikin/icons/flat.svg" width="18"> <img src="../AniKin/scripts/anikin/icons/step.svg" width="18"> <img src="../AniKin/scripts/anikin/icons/auto.svg" width="18"> **Tangent Shortcuts:** 1-click buttons to set tangents to Spline, Linear, Flat, Stepped, or Auto.
* <img src="../AniKin/scripts/anikin/icons/euler.svg" width="18"> **Euler Filter:** Fix gimbal lock on selected curves.
* <img src="../AniKin/scripts/anikin/icons/smooth.svg" width="18"> **Smooth Curves:** Averages out jittery keys.
* <img src="../AniKin/scripts/anikin/icons/cleanup.svg" width="18"> **Clean Curves:** Intelligently reduces keyframe density on dense mocap data while preserving the overall shape of the curve.

### 🟡 Playback & Key Operations
The redesigned playback cluster puts your most-used keys front and center.

* <img src="../AniKin/scripts/anikin/icons/first_key.svg" width="18"> <img src="../AniKin/scripts/anikin/icons/prev_key.svg" width="18"> <img src="../AniKin/scripts/anikin/icons/next_key.svg" width="18"> <img src="../AniKin/scripts/anikin/icons/last_key.svg" width="18"> **Key Navigation:** Jump between keyframes with single clicks.
* <img src="../AniKin/scripts/anikin/icons/key.svg" width="18"> **Set Key** (Accent): Places a keyframe on selected controls. Amber-accented as the primary action.
* <img src="../AniKin/scripts/anikin/icons/play.svg" width="18"> **Play / Pause Toggle:** Visually swaps icons between Play and Pause states.
* <img src="../AniKin/scripts/anikin/icons/delkey.svg" width="18"> **Delete Key** (Danger): Removes keyframes with red-on-hover safety feedback.

### 🔒 Channel Utilities
* <img src="../AniKin/scripts/anikin/icons/lock.svg" width="18"> **Lock/Unlock Toggle:** A single button that swaps between Lock and Unlock states — no more hunting for two separate buttons.

### 🔵 Advanced Workflow Modules
* <img src="../AniKin/scripts/anikin/icons/offset.svg" width="18"> **AniOffset:** Select multiple objects and stagger their animation by N frames, creating overlap in one click.
* <img src="../AniKin/scripts/anikin/icons/nudge_right.svg" width="18"> **Nudge Keys:** Shift selected keys left or right by 1 frame. Works on Graph Editor selections and timeline ranges.
* <img src="../AniKin/scripts/anikin/icons/duplicate.svg" width="18"> **Duplicate & Slide:** Duplicate an entire block of animation to a new location.
* <img src="../AniKin/scripts/anikin/icons/bake_to_locator.svg" width="18"> **Smart Bake:** Bake world-space motion to a locator, modify the rig, and paste it back.
* <img src="../AniKin/scripts/anikin/icons/wave_sine.svg" width="18"> **AniWave:** Procedural overlap and follow-through down a chain of controls.
* <img src="../AniKin/scripts/anikin/icons/activity.svg" width="18"> **AniNoise:** Add organic micro-jitter to your animation.
* <img src="../AniKin/scripts/anikin/icons/cam_lock.svg" width="18"> **Cam-Lock to Object:** Lock the viewport camera to any selected object during playback. Choose Track or Aim mode.

### 🟣 Visualization
* <img src="../AniKin/scripts/anikin/icons/trail.svg" width="18"> **Motion Trails:** Toggle editable 3D motion trails.
* <img src="../AniKin/scripts/anikin/icons/ghost.svg" width="18"> **Ghosting (Onion Skin):** Toggle viewport ghosting for previous/next frames.

### 🔴 Pipeline & Diagnostics
* <img src="../AniKin/scripts/anikin/icons/stethoscope.svg" width="18"> **AniCheck:** Scans for messy data (decimal frame keys, flat animation, dense mocap keys, foot sliding) and offers 1-click fixes.
* <img src="../AniKin/scripts/anikin/icons/palette.svg" width="18"> **AniColor:** Keyframe coloring and labeling system for organizing your timeline.
* <img src="../AniKin/scripts/anikin/icons/file_export.svg" width="18"> **AniExport:** Validates your skeleton and exports clean FBX for Unreal Engine.

---

## ⌨️ Full Hotkey Support
AniKin features a built-in **Hotkey Manager** (<img src="../AniKin/scripts/anikin/icons/hotkeys.svg" width="18">). You can bind *any* AniKin tool to a Maya hotkey without writing a single line of Python.

**Highly Recommended:** Map `Copy Pose` to `Ctrl+C` and `Paste Pose` to `Ctrl+V` inside the AniKin Hotkey Manager to override Maya's default geometry duplication behavior!
