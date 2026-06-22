# AniKin Research: AnimBot Feature Audit & Icon Mapping

**Document owner:** Mihir
**Status:** Research draft
**Related docs:** AniKin Brand Stance PRD, AniKin v0.2 Plugin Update PRD, AniKin "Beyond AnimBot" Implementation Plan

---

## Research Note

AnimBot's own public "Features" page (animbot.ca/tooltips) renders entirely via JavaScript and returned no extractable content. This audit was instead compiled from animbot.ca's pricing/download pages, the official animBot API/command documentation (help.animbot.ca — which lists real tool names like `createSelectSet`, `createTimeBookmark`, `createTempControl`, `nudge_nudgeRight`), animBot's own changelog ("Major updates on 2.2.0"), and corroborating professional tutorials (Animation Mentor, m3dsAcademy, Polycount). 20 distinct tools are documented below with confidence; AnimBot likely has additional minor utilities not independently verifiable from public sources.

**Icon disclaimer:** the icon names below are best-effort matches based on each library's existing naming conventions, picked from my knowledge of Phosphor's and Tabler's semantic, kebab/PascalCase-style catalogs. Streamline's catalog spans multiple visual styles (Core, Plump, Sharp, Freehand, etc.) and isn't a fixed-name catalog the way Phosphor/Tabler are, so I've given a search term instead of an exact icon ID. **Verify exact spelling and current availability on each site before wiring them into a UI** — icon libraries add, rename, and deprecate icons between versions.

---

## A. Sliders & Tangent Tools

| Feature | What It Does | Phosphor Icon | Tabler Icon | Streamline (search term) |
|---|---|---|---|---|
| Tweener | Interactive slider to blend a key toward its previous or next neighbor (Tween), or insert a breakdown pose with Favor Left/Right weighting | `Sliders` | `ti-adjustments-horizontal` | "slider control blend" |
| Scale to Neighboring Keys | Scales ease-in/ease-out on selected keys/channels toward the left or right key, applied across multiple channels at once | `ArrowsHorizontal` | `ti-arrows-horizontal` | "resize horizontal arrows" |
| Tangent Sliders Suite | One-click or blended tangent switching: Best Guess, Polished, Smooth (Flow), Bounce, Auto, Spline, Clamped, Linear, Flat, Plateau | `ChartLineUp` | `ti-chart-line` | "curve graph line" |
| Smart Key | Sets keys ("Set Smart Key All Channels") without disturbing tangents on unrelated curves | `MagicWand` | `ti-wand` | "magic wand smart" |

## B. Pose & Symmetry Tools

| Feature | What It Does | Phosphor Icon | Tabler Icon | Streamline (search term) |
|---|---|---|---|---|
| Mirror / Auto Mirror | Mirrors a pose or live-mirrors animation across the rig's symmetry axis as you work | `FlipHorizontal` | `ti-flip-horizontal` | "mirror flip horizontal" |
| Reset | Returns selected controls (or the whole rig) to their default/bind pose | `ArrowCounterClockwise` | `ti-refresh` | "reset undo arrow" |
| IK/FK Match | Switches between IK and FK while keeping the limb's world-space position, and can bake a frame range | `ArrowsLeftRight` | `ti-arrows-left-right` | "switch toggle arrows" |

## C. Selection & Organization

| Feature | What It Does | Phosphor Icon | Tabler Icon | Streamline (search term) |
|---|---|---|---|---|
| Select Sets | Save and recall named control selections, scoped per rig | `Selection` | `ti-select` | "selection box dashed" |
| Time Bookmarks | Save and jump between named ranges/frames on the timeline | `BookmarkSimple` | `ti-bookmark` | "bookmark tag ribbon" |
| Align | Snaps selected objects' position/rotation to a target selection | `AlignCenterHorizontal` | `ti-layout-align-center` | "align objects center" |

## D. Space & Rigging Utilities

| Feature | What It Does | Phosphor Icon | Tabler Icon | Streamline (search term) |
|---|---|---|---|---|
| Temp Controls | Builds a temporary native-Maya rig (parent constraints) for ad-hoc space-switching, then bakes back onto the original controls | `Stack` | `ti-stack-2` | "layers stack temporary" |
| Temp Pivot | Creates a temporary pivot point to rotate/scale around, auto-cleaned after use | `PushPin` | `ti-pin` | "pin pivot point" |

## E. Visualization

| Feature | What It Does | Phosphor Icon | Tabler Icon | Streamline (search term) |
|---|---|---|---|---|
| Motion Trail | Color-coded, in-viewport motion path showing spacing/arcs for the selected control, tracked on a specific point rather than just the default pivot | `Path` | `ti-route` | "motion path trail dots" |

## F. Timeline & Curve Editor Enhancements

| Feature | What It Does | Phosphor Icon | Tabler Icon | Streamline (search term) |
|---|---|---|---|---|
| Timeline Boost | Extra gestures/shortcuts on the Maya timeline for faster scrubbing and range operations | `Gauge` | `ti-gauge` | "speedometer boost" |
| Nudge Keys | Hotkey-driven small step move of selected keyframes left/right | `ArrowLineRight` | `ti-arrow-bar-right` | "nudge step arrow" |

## G. Pipeline & Automation

| Feature | What It Does | Phosphor Icon | Tabler Icon | Streamline (search term) |
|---|---|---|---|---|
| Baking Tools | Bakes and shares keys/animation between objects or rigs (evolved from the older "Share Keys" tool) | `Package` | `ti-package` | "package box export" |
| Anim Recovery | Auto-saves periodic checkpoints of in-progress animation work for recovery after a crash, with automatic disk-usage cleanup | `ClockCounterClockwise` | `ti-history` | "history restore clock" |
| Auto Bots | Background manager for tools that hook into Maya's scene callbacks, so the user can see/control what's running automatically | `Robot` | `ti-robot` | "robot automation gear" |
| Debug Console | Shows real-time internal logging of what AnimBot/AniKin tools are doing under the hood | `Bug` | `ti-bug` | "bug debug terminal" |
| Hotkey Manager | Central panel for assigning and customizing hotkeys across all tools | `Keyboard` | `ti-keyboard` | "keyboard shortcut key" |

---

## Summary

20 features across 7 categories. Notably, several of these already line up with module names you defined in the Brand Stance PRD but hadn't yet filled with content — `AniMirror`, `AniGhost`, `AniBake`, and `AniMotion` all now have a natural home for real AnimBot-equivalent functionality. See the Implementation Plan document for how each feature maps to AniKin's module architecture and a proposed build sequence.
