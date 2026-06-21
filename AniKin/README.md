# AniKin — The Intelligent Animation Analysis and Productivity Toolkit

> **Status:** Beta (v0.2.0)
> **License:** GNU GPLv3

AniKin (Animation + Kinematics) is a free, open-source productivity toolkit for Maya animators. It unifies daily workflow tools with kinematics-driven diagnostics into a single dockable panel.

## Open Source Credits & Attribution

AniKin is licensed under the GPLv3. 

**Key Machine:**
The `AniTween` module (along with concepts in `AniOffset` and `AniSets`) were inspired by and adapted from the excellent *Key Machine* toolset by its original developer. Key Machine is also licensed under the GPLv3. We extend our deep gratitude to the Key Machine project for establishing these open-source animation workflows.

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

## Modules (v0.2)

AniKin is built as a platform of modules. Current features include:

- **AniTween** — Interpolate between neighboring keys with overshoot, ease-in, and ease-out.
- **AniOffset** — Stagger keyframes across selections.
- **AniTangents** — One-click Auto/Flat/Linear/Step/Spline tangents.
- **AniBake** — Smart bake to world-space locator and back.
- **AniSets** — Save and recall custom selection sets per rig.
- **AniMotion & AniGhost** — Sleek toggles wrapping Maya's native viewport motion trails and ghosting.
- **AniNudge** — Shift keyframes left/right by N frames.
- **AniChannels** — Lock/unlock, key/unkey channel toggles.
- **AniAlign** — Align objects in translate and rotate space.
- **Interactive UI Shell** — Dockable Dark Theme UI with premium vector icons, reorderable toolbar, and Hotkey Manager.

## Contributing

See `CONTRIBUTING.md`. All contributions must be GPLv3-compatible.

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
