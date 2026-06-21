# Product Requirements Document
## AnimForge — An Open-Source Animator's Toolkit for Maya

**Status:** Draft v0.1
**Date:** June 21, 2026
**License target:** GNU GPLv3
**Author:** Mihir (drafted with Claude)

> Working name only. "AnimForge" should be run through a trademark/domain check before public release. Any final name must be clearly distinct from existing commercial products in this space.

---

## 1. Background & Problem Statement

A handful of paid plugins (AnimBot being the best-known) bundle dozens of small but high-leverage productivity tools for Maya animators — tweening, motion trails, anim offset, smart bake, ghosting, custom hotkeys — into a single subscription-gated package. These tools genuinely save time, but:

- They're closed-source, so studios and individuals can't audit, fix, or extend them.
- The subscription model ($15/week and up, per current AnimBot pricing) is a real barrier for students, freelancers, and small/indie teams.
- There's no community contribution path — a bug or missing feature waits on one developer's roadmap.

Free alternatives exist for *pieces* of this (Studio Library for pose management, Tween Machine for breakdowns, aTools for selection/mirroring) but nothing unifies them into one coherent, actively maintained, copyleft toolkit.

## 2. Vision

A single, dockable, GPLv3-licensed toolkit that covers the core animator-productivity workflow in Maya — built from original code, free forever, forkable, and maintained in the open.

## 3. Goals / Non-Goals

**Goals**
- G1: Ship an MVP covering the 5–6 highest-leverage tools (tween/breakdown, anim offset, motion trail viz, selection sets, smart bake) within ~10 weeks of active development.
- G2: Architecture that's modular — each tool is an independent, loadable component, so contributors can add tools without touching the core.
- G3: Cross-version compatibility (Maya 2022–2026, Windows/macOS/Linux).
- G4: Zero telemetry, zero phone-home — consistent with open-source ethos.

**Non-Goals**
- NG1: Pixel-parity or feature-parity cloning of any named commercial product.
- NG2: Reproducing any proprietary code, icon assets, UI layout, or branding from AnimBot or any other closed tool.
- NG3: Reverse-engineering or decompiling any commercial plugin's binary/bytecode.

## 4. Target Users

| Persona | Context | Primary need |
|---|---|---|
| Freelance/indie animator | Limited tool budget | Free, reliable productivity tools |
| Small studio TD | Needs to customize/extend tools for pipeline | Source access, GPL forkability |
| Student/educator (like Mihir) | Learning Maya API + building portfolio | A real, shippable engineering project |

## 5. Legal & Licensing Framework

This section is load-bearing — read it before writing any code.

- **Clean-room only.** No AnimBot code, assets, or icons are ever opened, viewed, or referenced during development. Architecture inspiration is drawn only from genuinely open/permissively-licensed prior art (see §6).
- **License: GPLv3.** Chosen specifically because it's copyleft — any fork or derivative must also stay open, which protects the tool from being absorbed into a closed commercial product later.
- **Dependency audit.** Every third-party library (PySide2/6, etc.) must be GPL-compatible. PySide is LGPL — fine for dynamic linking, but don't statically bundle Qt in a way that violates LGPL terms.
- **Naming/branding.** Original name, original icon set, no visual mimicry of any commercial tool's UI. Run a basic trademark search before public launch.
- **README disclosure.** State plainly: "Inspired by the genre of animator productivity toolbelts (Tween Machine, Studio Library, aTools, etc.). Not affiliated with, derived from, or a replacement for any specific commercial product."

## 6. Prior Art (study for architecture patterns, not for code)

| Tool | License | What to learn from it |
|---|---|---|
| Red9 StudioPack | GPL | Largest GPL animation toolset for Maya — closest architectural reference for a modular GPL toolkit |
| Studio Library | LGPL | Pose/anim library UI patterns, Qt dockable panel structure |
| aTools (Anzovin Studio) | Open | Selection sets, mirroring, picker UX |
| mGear | MIT | Clean plugin/module loading architecture |
| Tween Machine | Public/open script | Minimal breakdown-tool implementation as a reference point |

## 7. Feature Set

### Module A — Selection & Picker
- Custom selection sets, savable per-rig
- Quick-select UI (buttons/picker, not a full custom rig picker initially)

### Module B — Key & Curve Editing
- Tween/breakdown slider (interpolate between neighboring keys)
- Overshoot/smooth (Euler-filter-based smoothing pass)
- Anim offset (stagger keyframes across a selection by N frames)

### Module C — Viewport Visualization
- Motion trail overlay (custom `MPxDrawOverride`)
- Ghosting / onion-skin overlay

### Module D — Workflow Utilities
- Smart bake (bake to world-space locator and back)
- Channel lock/key toggles
- Frame range utilities

### Module E — Shelf & Hotkeys
- Dockable, reorderable toolbar
- User-assignable hotkeys per tool

### Module F — Stretch
- Interop with Studio Library's pose format (read-compatible, not a fork)

Each module ships with: functional spec, acceptance criteria, and a manual + automated test scene before being marked "done."

## 8. Non-Functional Requirements

- Maya 2022–2026 support; PySide2 for 2022–2024, PySide6 for 2025+, detected at install time.
- Viewport overlay tools (motion trail, ghosting) must not visibly drop frame rate on a 50-joint rig.
- No `pymel` in any per-frame/per-draw hot path — use `OpenMaya` 2.0 API directly.
- Fully offline — no network calls, no analytics.

## 9. Technical Architecture

- **Core:** Maya Python API 2.0 (`OpenMaya`), not MEL, not legacy API 1.0.
- **UI:** PySide2/6 + Qt, single dockable panel, modules register themselves into it.
- **Viewport draw:** `MPxDrawOverride` / VP2 custom draw for trails and ghosting — this is the hardest technical piece and should be prototyped early (see action plan, Phase 3).
- **Packaging:** Maya Module (`.mod`) format for clean install/uninstall, no manual `userSetup.py` editing required.
- **Versioning:** Semantic versioning (`MAJOR.MINOR.PATCH`), CI matrix across Maya versions if feasible.

## 10. Success Metrics

- GitHub stars/forks as adoption proxy (no telemetry, so this is the honest signal)
- Number of accepted community PRs
- Used in at least one real personal/portfolio production by launch+3 months

## 11. Release Milestones

| Milestone | Scope | Target |
|---|---|---|
| M0 | Plugin skeleton loads in Maya, empty dockable panel | Week 2 |
| M1 (MVP) | Modules A, B, D functional | Week 10 |
| M2 (v1.0) | Module C added, public GPL release on GitHub | Week 18–20 |
| M3 | Community feedback iteration | Ongoing |
| M4 (v2.0) | Module E polish + Module F stretch | TBD |

## 12. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Any code/asset resemblance to a commercial tool | Strict clean-room process; only original code is ever written; periodic self-audit |
| Trademark dispute over name | Distinct branding, trademark search pre-launch |
| Maya API breakage across versions | Maintain a small test-scene matrix per version |
| Solo-dev burnout | Phase scoping (§ Action Plan), realistic part-time timeline |

## 13. Glossary

- **VP2** — Viewport 2.0, Maya's modern hardware-accelerated viewport, requires `MPxDrawOverride` for custom draws.
- **Breakdown** — An animation key whose value is a blend between its neighbors, used for refining timing.
- **Ghosting/onion-skinning** — Displaying faded previous/next-frame poses in the viewport for timing reference.
