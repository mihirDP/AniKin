<div align="center">
  <img src="AniKin/scripts/anikin/icons/activity.svg" width="80" height="80">
  <h1>AniKin</h1>
  <p><b>The Next-Generation Animator-First Toolkit for Autodesk Maya</b></p>
  <p>Free, Open-Source, and designed to make your animation workflow significantly faster.</p>
</div>

---

## 🌟 What is AniKin?

AniKin is a highly polished, modular, and professional-grade dockable toolbar designed directly for character animators in Maya. It brings the power of industry-standard tools (like advanced tweening, smart baking, timeline range operations, and pose caching) directly to your viewport with a clean, flat, modern UI. 

Whether you're animating keyframe-by-keyframe, cleaning up dense motion capture, or exporting to Unreal Engine, AniKin removes the technical friction so you can focus on the art of animation.

## 🚀 Key Features & Tools

AniKin is divided into specialized modules, accessible right above your timeline. The toolbar is **fully customizable** — you can hide or reorder sections in the Settings panel!

### 🟠 Core Animation & Transform
Your bread and butter tools for manipulating objects and keys.

* <img src="AniKin/scripts/anikin/icons/reset.svg" width="18"> **Reset Pose:** Instantly zero out translation and rotation (leaving scale at 1.0).
* <img src="AniKin/scripts/anikin/icons/align_all.svg" width="18"> **Align Tools:** Snap the translation, rotation, or both of your selected objects to the *last selected* object.
* <img src="AniKin/scripts/anikin/icons/ground.svg" width="18"> **AniGround:** Automatically calculates the bounding box of your selected object and snaps its lowest point perfectly to the floor (Y=0). Great for planting feet!
* <img src="AniKin/scripts/anikin/icons/copy_pose.svg" width="18"> **Copy/Paste Pose:** Stores your current pose in memory to paste elsewhere. **Pro Tip:** If you highlight a red range on the timeline (Shift+Click) and hit Copy, it copies the *entire animated block* to paste later!
* <img src="AniKin/scripts/anikin/icons/mirror_pose.svg" width="18"> **Mirror & Flip Pose:** Negates TX, TZ, and RY to mirror a pose, or swaps poses between Left/Right controls automatically.

### 🟠 Timing & Key Manipulation
Everything you need to slide and adjust your timing effortlessly.

* <img src="AniKin/scripts/anikin/icons/play.svg" width="18"> **Play / Pause Toggle:** Easily toggle animation playback with a button that visually swaps between a green Play triangle and an orange Pause icon.
* <img src="AniKin/scripts/anikin/icons/cam_lock.svg" width="18"> **Cam-Lock to Object:** Lock the viewport camera to any selected object during playback. It uses a robust, constraint-based architecture (no scriptJobs). Choose between **Track Mode** (maintains exact offset) and **Aim Mode** (continuous framing). It safely restores the camera when unlocked without polluting the scene.
* <img src="AniKin/scripts/anikin/icons/nudge_right.svg" width="18"> **Nudge Keys:** Shift selected keys left or right by 1 or 5 frames. Works on Graph Editor selections, or seamlessly on highlighted timeline ranges!
* <img src="AniKin/scripts/anikin/icons/offset.svg" width="18"> **Anim Offset (Stagger):** Select multiple objects (e.g., tail joints) and hit this tool to instantly stagger their animation by N frames, creating beautiful overlap and follow-through in one click.
* <img src="AniKin/scripts/anikin/icons/duplicate.svg" width="18"> **Duplicate & Slide:** Highlight a range of keys, click this tool, and type a target frame. It safely duplicates the entire block of animation and merges it into the new location.

### 🟠 Tangents & Curves
* <img src="AniKin/scripts/anikin/icons/auto.svg" width="18"> <img src="AniKin/scripts/anikin/icons/step.svg" width="18"> **Tangent Shortcuts:** 1-click buttons to set tangents to Auto, Spline, Linear, Flat, or Stepped.
* <img src="AniKin/scripts/anikin/icons/euler.svg" width="18"> **Euler Filter:** Fix gimbal lock on selected curves.
* <img src="AniKin/scripts/anikin/icons/smooth.svg" width="18"> **Smooth Curves:** Averages out jittery keys.
* <img src="AniKin/scripts/anikin/icons/cleanup.svg" width="18"> **Clean Curves:** Intelligently reduces keyframe density on dense mocap data while preserving the overall shape of the curve.

### 🎨 Tweening & Easing
Our custom slider engine gives you absolute control over your breakdowns.

* **TW (Tween Slider):** Linearly blends your current pose between the previous and next keyframes. Push it past 100% or below 0% for instant overshoots!
* **EA (Ease Slider):** Uses a smooth ease-in/ease-out curve. Perfect for organic breakdowns.
* <img src="AniKin/scripts/anikin/icons/wand.svg" width="18"> **Smart Key:** Sets a keyframe *only* on channels that already have animation, keeping your curves clean.

### 🔵 Advanced Workflow Tools
* <img src="AniKin/scripts/anikin/icons/bake_to_locator.svg" width="18"> **Smart Bake:** Bake an object's world-space motion to a locator, modify the underlying rig, and paste the motion back. Essential for space-switching and complex constraint changes!
* <img src="AniKin/scripts/anikin/icons/wave_sine.svg" width="18"> **AniWave:** A procedural generator that propagates overlap and follow-through down a selected chain of controls automatically.
* <img src="AniKin/scripts/anikin/icons/camera.svg" width="18"> **AniSnap:** A visual pose-library that lets you capture viewport screenshots of poses and apply them back to the rig.
* <img src="AniKin/scripts/anikin/icons/selection_sets.svg" width="18"> **Selection Sets & Bookmarks:** Manage quick selection groups and timeline bookmarks without diving into Maya's clunky default menus.

### 🟣 Visualization
* <img src="AniKin/scripts/anikin/icons/trail.svg" width="18"> **Motion Trails:** Toggle editable 3D motion trails.
* <img src="AniKin/scripts/anikin/icons/ghost.svg" width="18"> **Ghosting (Onion Skin):** Toggle viewport ghosting to see your previous and next frames overlaid in the viewport.

### 🔴 Pipeline & Diagnostics
* <img src="AniKin/scripts/anikin/icons/stethoscope.svg" width="18"> **AniCheck:** Scans your scene/selection for messy data (decimal frame keys, flat animation, dense mocap keys, and even foot sliding!) and offers 1-click fixes.
* <img src="AniKin/scripts/anikin/icons/file_export.svg" width="18"> **AniExport:** Specifically designed for games. Validates your skeleton (checks for correct units, negative scales, unbaked constraints, etc.) before exporting a clean FBX directly to Unreal Engine.

---

## ⌨️ Full Hotkey Support
AniKin features a built-in **Hotkey Manager** (<img src="AniKin/scripts/anikin/icons/hotkeys.svg" width="18">). You can bind *any* AniKin tool to a Maya hotkey without writing a single line of Python.

**Highly Recommended:** Map `Copy Pose` to `Ctrl+C` and `Paste Pose` to `Ctrl+V` inside the AniKin Hotkey Manager to override Maya's default geometry duplication behavior!

## ⚙️ Installation

1. Download or clone this repository to your machine.
2. Drag and drop the `install.mel` file into your Maya viewport.
3. The AniKin toolbar will dock automatically to the bottom of your workspace!

## 📜 License
AniKin is an open-source project distributed under the GPLv3 License. It shares a lineage and principles with the open-source community, aiming to keep professional animation tools accessible to everyone.
