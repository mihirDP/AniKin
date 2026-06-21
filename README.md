# AniKin — Open-Source Animator's Toolkit for Maya

> **Status:** Early Development (v0.1.0-skeleton)
> **License:** GNU GPLv3

AniKin is a free, open-source, GPLv3-licensed productivity toolkit for Maya animators. It bundles high-leverage tools — tweening, anim offset, tangent shortcuts, smart bake, selection sets, and more — into a single dockable panel.

## Disclosure

Inspired by the genre of animator productivity toolbelts (Tween Machine, Studio Library, aTools, etc.). **Not affiliated with, derived from, or a replacement for any specific commercial product.** All code is original, written clean-room.

## Installation

### The Easy Way (Drag-and-Drop)
1. Extract the `AniKin` folder anywhere on your computer.
2. Drag and drop the `drag_drop_install.py` file directly into your Maya viewport.
3. The plugin will automatically install, register itself, and launch!

### The Manual Way
1. Copy the entire `AniKin` folder to your Maya modules directory:
   - **Windows:** `%USERPROFILE%\Documents\maya\modules\`
   - **macOS:** `~/Library/Preferences/Autodesk/maya/modules/`
   - **Linux:** `~/maya/modules/`
2. Copy `anikin.mod` from inside the folder to the same modules directory.
3. Restart Maya and run the following in the Python Script Editor:
   ```python
   import anikin
   anikin.launch()
   ```

## Compatibility

- Maya 2022–2027
- Windows / macOS / Linux
- PySide2 (Maya 2022–2024) / PySide6 (Maya 2025+) — auto-detected

## Features

- **Dockable Dark Theme UI** — Native Maya docking with premium vector icons and a reorderable toolbar structure.
- **Interactive Hotkey Manager** — Record and assign Maya shortcuts directly inside the plugin.
- **Motion Trails & Ghosting** — Sleek toggles wrapping Maya's native viewport visualization.
- **Selection Sets** — Save and recall custom selection sets per rig.
- **Tween/Breakdown Slider** — Interpolate between neighboring keys with overshoot.
- **Anim Offset** — Stagger keyframes across selections.
- **Tangent Shortcuts** — One-click Auto/Flat/Linear/Step/Spline tangents.
- **Smart Bake** — Bake to world-space locator and back.
- **Nudge Keys** — Shift keyframes left/right by N frames.
- **Channel Utilities** — Lock/unlock, key/unkey channel toggles.

## Contributing

See `CONTRIBUTING.md`. All contributions must be GPLv3-compatible.

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
