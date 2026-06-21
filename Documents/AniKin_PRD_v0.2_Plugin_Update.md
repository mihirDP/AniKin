# PRD: AniKin v0.2 — Plugin Update

**Document owner:** Mihir
**Status:** Draft
**Related doc:** AniKin Brand Stance PRD

---

## 1. Overview

AniKin is a free, open-source (GPLv3) Maya animator productivity toolkit, targeting Maya 2022–2027 on Windows, macOS, and Linux. v0.2 is the first structured release after the initial concept/repository stage: it establishes the **modular architecture**, ships the **daily-use core tools**, and begins the **Key Machine → AniTween** migration — without yet attempting the kinematics-diagnostics features that define the long-term vision.

## 2. Goals

1. Ship a stable, daily-usable core toolset inside a single dockable window.
2. Stand up the modular package architecture (`AniTween`, `AniOffset`, `AniBake`, etc.) so future modules can be added without refactoring.
3. Begin the Key Machine merge: rebuild its tween/blend slider functionality as the `AniTween` module, license-compliant and rebranded.
4. Validate cross-version compatibility (Maya 2022–2027, PySide2/PySide6 auto-detection) early, since this is a stated differentiator.
5. Establish the dark-theme dockable UI shell that all future modules will plug into.

## 3. Non-Goals (explicitly deferred)

- Pose Mirror, Smart Bake refinements, Motion Trails/Ghosting polish → targeted for v0.3/v1.5 tier.
- Foot Slide Detector, Gimbal Warning System, Curve Cleanup Assistant, Broken Constraint Detection, Overshoot Detection → v2.0 tier.
- IK/FK Matcher, Root Motion Analyzer, Center-of-Mass Visualizer, Balance Checker, Unreal Export Validator, Retargeting Diagnostics → v3.0 "Animation Kinematics" tier.
- No AI-assisted detection in v0.2 — flagged as a later phase requiring its own design pass.

## 4. Scope: Modules in v0.2

| Module | Description | Source |
|---|---|---|
| `AniTween` | Tween, Breakdown, Favor Left/Right, Overshoot, Ease In/Out, multi-object tweening | Rebuilt from Key Machine's tween/blend slider concepts, GPLv3-compatible |
| `AniOffset` | Animation offset across selected controls | New |
| Tangent Utilities | Quick tangent type switching (spline, linear, stepped, flat) | New |
| `AniKey` Nudge | Keyframe nudging via hotkeys | New |
| Selection Sets | Save/recall control selections | New |
| Hotkey Manager | Centralized, customizable hotkey assignment for all AniKin tools | New |
| Dockable UI Shell | Dark-theme, dockable, searchable tool panel | New |

## 5. Functional Requirements

### 5.1 AniTween
- FR-1: Support standard tween (blend between adjacent keys) and breakdown insertion at the current frame.
- FR-2: Support Favor Left / Favor Right weighting.
- FR-3: Support Overshoot beyond 100%/0% for exaggeration.
- FR-4: Support Ease In / Ease Out presets.
- FR-5: Operate on multi-object/multi-attribute selections simultaneously.
- FR-6: Respect existing animation layers (apply to the active layer only).
- FR-7: All Key Machine–derived logic must be reimplemented or adapted in compliance with GPLv3 (Key Machine's own license, matching AniKin's), with required notices preserved and credited in an in-app About panel.

### 5.2 AniOffset
- FR-8: Apply a frame offset to selected controls' keyframes relative to a reference object or frame.
- FR-9: Support both uniform offset and incremental/staggered offset across multiple selected objects (e.g., for cloth/tail follow-through).

### 5.3 Tangent Utilities
- FR-10: One-click tangent type switching for selected keys (spline, linear, stepped, flat, plateau).
- FR-11: Batch apply to multiple selected curves/objects at once.

### 5.4 Keyframe Nudge
- FR-12: Hotkey-driven nudge of selected keyframes left/right by 1 frame (and a configurable larger step).

### 5.5 Selection Sets
- FR-13: Save current selection as a named set, scoped per-rig or per-scene.
- FR-14: Recall a saved set with one click or hotkey.

### 5.6 Hotkey Manager
- FR-15: Central panel listing all AniKin tool actions with editable hotkey bindings.
- FR-16: Detect and warn on conflicts with existing Maya hotkeys.
- FR-17: Support exportable/importable hotkey presets (for studio standardization).

### 5.7 UI Shell
- FR-18: Single dockable window housing all v0.2 modules as tabs/sections.
- FR-19: Dark theme by default, consistent with the established icon language and UI/UX direction already planned in the repo.
- FR-20: Searchable tool/action list within the shell.
- FR-21: Window state (docked position, last-used tab) persists between Maya sessions.

## 6. Technical Requirements

- TR-1: Support Maya versions 2022 through 2027.
- TR-2: Auto-detect and load PySide2 (Maya ≤2024) or PySide6 (Maya 2025+) without requiring user configuration.
- TR-3: Cross-platform support for Windows, macOS, and Linux — no OS-specific code paths without a fallback.
- TR-4: Package structure must reflect the modular architecture (`AniKin/AniTween/`, `AniKin/AniOffset/`, etc.) so v0.3+ modules can be added as new subpackages without touching core shell code.
- TR-5: GPLv3 license headers on all source files; third-party-derived code (e.g., Key Machine–based logic) flagged separately with its own license notice.
- TR-6: No external paid dependencies — installation should remain a simple drag-and-drop or `userSetup.py`-based install consistent with typical Maya tool distribution.

## 7. UX Requirements

- Dockable, not floating-only.
- Customizable hotkeys and savable user presets/workspace layouts.
- Visual consistency with the icon language and UI/UX system already drafted in the repository's planning docs.
- Tool discoverability via search, given the module count will grow significantly by v2.0/v3.0.

## 8. Success Metrics

- Functional: all seven v0.2 modules pass manual QA across at least two Maya versions (one pre-2025 PySide2 build, one 2025+ PySide6 build) and two OSes.
- Adoption: GitHub stars/forks and download counts post-release, tracked against the "student release → community release" growth stages.
- Quality: number of open bugs/issues per module within 30 days of release; target trending downward, not flat or rising.
- Brand alignment: release notes and README framed per the Brand Stance PRD (modular architecture and roadmap visible, not just a feature list).

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| ~~Key Machine license incompatible with GPLv3 merge~~ — confirmed resolved: Key Machine is GPLv3 (same as AniKin) and is no longer in active development, with its developer explicitly permitting forking/adaptation | N/A — proceed | Still preserve required GPLv3 notices and in-app credit when adapting its code |
| Feature parity perception ("just AnimBot but free") | Undermines differentiation goal | Pair v0.2 release notes with the Brand Stance roadmap (Now/Next/Vision framing) |
| Cross-version PySide2/PySide6 bugs | Breaks tool for a subset of users | Explicit QA pass on both bindings before release, not just the dev's primary Maya version |
| Scope creep into v0.3/v2.0 features | Delays v0.2 ship date | Hold the line on Non-Goals list; track deferred features in a separate backlog |

## 10. Milestones (Suggested)

1. **Architecture lock** — finalize modular package structure and UI shell.
2. **Core module build** — AniOffset, Tangent Utilities, Nudge, Selection Sets, Hotkey Manager.
3. **AniTween build** — confirm Key Machine GPLv3 compliance/attribution → adapt/rebuild → QA.
4. **Cross-version QA pass** — Maya 2022–2027, Win/macOS/Linux.
5. **Release** — v0.2 tag, README/brand messaging update, About-panel attribution.

## 11. Open Questions

- Should Smart Bake and Motion Trails/Ghosting be pulled forward into v0.2 if AniTween development finishes early, or strictly held for v0.3?
- Does the Hotkey Manager need per-rig or per-project hotkey profiles in v0.2, or is a single global profile sufficient until studio-adoption use cases emerge?
- What is the minimum viable "About/Credits" panel needed to satisfy Key Machine's GPLv3 attribution requirements?
- Key Machine's own feature set includes Anim Offset and a Selection Manager (Selection Sets) alongside its Tween/Blend sliders — should the `AniOffset` and Selection Sets rows in the Section 4 table also be marked as Key Machine–inspired (Source: "Adapted from Key Machine"), or were those built independently and the overlap is coincidental?
