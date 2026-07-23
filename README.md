<div align="center">
  <img src="AniKin/scripts/anikin/icons/activity.svg" width="80" height="80" alt="AniKin Logo — Free Maya Animation Toolkit">
  <h1>AniKin — Free Animation Toolkit for Maya</h1>
  <p><b>The Next-Generation Animator-First Toolkit for Autodesk Maya</b></p>
  <p>An open-source, modular Maya Python plugin that supercharges your character animation workflow with smart tweening, pose libraries, motion trail editing, animation baking, and 30+ production-ready tools.</p>

  <p>
    <img src="https://img.shields.io/badge/Maya-2024%E2%80%932027-00A6D6?style=flat-square&logo=autodesk&logoColor=white" alt="Maya 2024–2027">
    <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.9+">
    <img src="https://img.shields.io/badge/License-GPLv3-blue?style=flat-square" alt="License GPLv3">
    <img src="https://img.shields.io/github/v/release/mihirDP/AniKin?style=flat-square&color=2FD3C2&label=Latest" alt="Latest Release">
    <img src="https://img.shields.io/github/stars/mihirDP/AniKin?style=flat-square&color=C9A227" alt="GitHub Stars">
  </p>

  <p>
    <a href="#-installation"><b>⚡ Quick Install</b></a> · 
    <a href="Documentation/HowToUse.md"><b>📖 Full Docs</b></a> · 
    <a href="https://github.com/mihirDP/AniKin/releases"><b>📦 Releases</b></a> · 
    <a href="#-contributing"><b>🤝 Contribute</b></a>
  </p>
</div>

---

## 🌟 What is AniKin?

**AniKin** is a free, open-source animation toolkit for [Autodesk Maya](https://www.autodesk.com/products/maya/) designed from the ground up for **character animators**. It installs as a single drag-and-drop dockable toolbar that sits above your timeline, giving you instant access to 30+ professional tools without leaving the viewport.

Whether you're blocking out keyframes, polishing breakdowns, cleaning mocap data, or exporting FBX for Unreal Engine, AniKin eliminates the repetitive technical friction of Maya and lets you focus on the **art of animation**.

### Why AniKin?

| Feature | Maya Default | AniKin |
|:---|:---:|:---:|
| Tween / Breakdown Slider | ❌ | ✅ Linear + Ease modes |
| Visual Pose Library with GIF preview | ❌ | ✅ AniPose Pro |
| Studio Library `.pose` / `.anim` import | ❌ | ✅ Native parsing |
| Smart Key (animated channels only) | ❌ | ✅ |
| One-click Nudge / Duplicate keys | ❌ | ✅ |
| Procedural Overlap (AniWave) | ❌ | ✅ |
| Motion Noise / Jitter generator | ❌ | ✅ |
| Animation Health Check (AniCheck) | ❌ | ✅ |
| Cam-Lock to Object viewport tracking | ❌ | ✅ |
| Drag-and-drop install | ❌ | ✅ |

---

## ✨ What's New in v0.6.0

- **AniPose Pro V3.3** — Complete UI overhaul with dark-chrome design tokens, tabbed category navigation, magnetic size slider, and fluid Grid/List toggle.
- **Native Studio Library Support** — Import your existing Studio Library `.pose` and `.anim` folders directly. Thumbnails, metadata, and JSON controls are parsed natively.
- **Auto-Playing GIF Thumbnails** — Clip thumbnails auto-play in the library grid. Hover to scrub frames manually.
- **100% Curve-Fidelity Clip Paste** — Animation clips now paste with mathematically identical Graph Editor curves by bypassing Maya's tangent lock ordering bug.
- **Multi-Curve Preview Widget** — Overlaid sparkline graph with grid lines, axis labels, key dots, and a per-curve color legend.

<details>
<summary><b>Previous: v0.5.0 — Complete UI Redesign</b></summary>

- New 10-group toolbar layout with clear visual separators
- Custom-designed V2 SVG icons for every tool
- Amber accent dark-mode color system (`#d4860a`)
- Merged Lock/Unlock toggle button
- Clickable "AniKin" brand logo → About/Settings
- Compact 28×28px buttons for a tighter professional toolbar
</details>

---

## 🚀 Key Features & Tools

AniKin is organized into specialized modules. Every tool is accessible from the toolbar above your timeline. The layout is **fully customizable** — hide, reorder, or hotkey any section.

### 🎭 Pose & Transform Tools
- **Reset Pose** — Zero out translation and rotation instantly.
- **Mirror / Flip Pose** — Negate TX, TZ, RY or swap L↔R controls.
- **Copy / Paste Pose** — Clipboard-based pose transfer across frames and rigs.
- **AniPose Pro** — Full visual Pose & Animation Library with GIF thumbnails, Studio Library compatibility, and 100% curve-fidelity pasting.

### 🎨 Tweening & Easing
- **Tween Slider** — Linear blend between previous/next keys. Push past 100% for overshoots.
- **Ease Slider** — Smooth ease-in/out curve for organic breakdowns.
- **Smart Key** — Sets keyframes *only* on channels that already have animation.

### 📐 Tangents & Curves
- **1-Click Tangent Presets** — Spline, Linear, Flat, Stepped, Auto.
- **Euler Filter** — Fix gimbal lock on selected curves.
- **Smooth Curves** — Average out jittery keyframes.
- **Clean Curves** — Reduce mocap key density while preserving shape.

### ▶️ Playback & Key Operations
- **Key Navigation** — Jump First / Prev / Next / Last keyframe.
- **Set Key** — Accent-highlighted primary action button.
- **Play / Pause Toggle** — Swaps icon state live.
- **Delete Key** — Red-on-hover danger button for safety feedback.

### 🔧 Advanced Workflow Modules
- **AniOffset** — Stagger animation across multiple objects by N frames.
- **Nudge Keys** — Shift selected keys ±1 frame. Timeline range aware.
- **Duplicate & Slide** — Copy animation blocks to a new time.
- **AniBake** — Bake world-space motion to locator, modify rig, paste back.
- **AniWave** — Procedural overlap and follow-through on chains.
- **AniNoise** — Organic micro-jitter for living-hold generation.
- **Cam-Lock** — Lock viewport camera to any object during playback.
- **AniTrail** — Editable 3D motion trails in viewport.
- **AniMatch** — IK/FK matching and space switching.
- **AniRetime** — Non-destructive animation retiming.
- **AniBlast** — Quick viewport playblast with annotation overlays.

### 🔍 Pipeline & Diagnostics
- **AniCheck** — Scan for decimal-frame keys, flat anim, dense mocap, foot sliding.
- **AniColor** — Keyframe coloring and timeline labeling system.
- **AniExport** — Skeleton validation + clean FBX export for Unreal Engine.

👉 **[Read the Full Feature Documentation →](Documentation/HowToUse.md)**

---

## ⚙️ Installation

### Quick Install (Drag & Drop)
1. [Download the latest release](https://github.com/mihirDP/AniKin/releases) or clone this repo.
2. Drag `drag_drop_install.py` into your Maya viewport.
3. AniKin docks automatically above your timeline. Done!

### Manual Install
1. Copy the `AniKin` folder to your Maya modules directory.
2. Add the `.mod` file path to your `MAYA_MODULE_PATH` environment variable.
3. Restart Maya.

### Requirements
- **Maya 2024** or newer (Maya 2027 recommended)
- **Python 3.9+** (ships with Maya 2024+)
- **PySide2** or **PySide6** (auto-detected)

---

## ⌨️ Hotkey Support

AniKin includes a built-in **Hotkey Manager**. Bind any AniKin tool to a Maya hotkey without writing a single line of Python.

> **Pro Tip:** Map `Copy Pose` → `Ctrl+C` and `Paste Pose` → `Ctrl+V` inside the AniKin Hotkey Manager to override Maya's default geometry duplication.

---

## 🤝 Contributing

AniKin is open-source and welcomes contributions! Whether it's a bug fix, a new tool module, or documentation improvements — all help is appreciated.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-tool`
3. Write your code with clear docstrings
4. Test in at least one Maya version
5. Submit a Pull Request

See [CONTRIBUTING.md](AniKin/CONTRIBUTING.md) for full guidelines.

---

## 📜 License

AniKin is distributed under the **[GNU General Public License v3.0](LICENSE)**. Free to use, modify, and distribute — keeping professional animation tools accessible to everyone.

---

<div align="center">
  <p><b>⭐ If AniKin helps your animation workflow, consider giving it a star!</b></p>
  <p>Built with ❤️ for the Maya animation community</p>
</div>
