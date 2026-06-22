# AniKin Implementation Plan: AnimBot Feature Parity & Beyond

**Document owner:** Mihir
**Status:** Draft
**Related docs:** AniKin Brand Stance PRD, AniKin v0.2 Plugin Update PRD, AnimBot Feature Audit & Icon Mapping

---

## 1. Strategic Context

The market gap is real and worth naming plainly:

- **AnimBot** is the dominant tool but gated behind a subscription ($60–$396/year) or a $249 lifetime tier capped at old Maya versions — out of reach for students, hobbyists, and animators in lower-income regions.
- **aTools**, AnimBot's free predecessor, wasn't really "taken down" so much as superseded: AnimBot's own creator, Alan Camilo, rebuilt aTools into the commercial AnimBot and aTools development effectively stopped in favor of it.
- **Tween Machine** remains free but narrow in scope (tweening only).
- **Key Machine**, the broadest free alternative, is now officially archived — its developer confirmed no further updates, bug fixes, or features, though the GPLv3 source remains forkable.

So the free-tool landscape for Maya animators is genuinely thinning at the same time AnimBot's price floor stays high. That's a real opening. The honest caveat: AnimBot has been continuously refined since 2017 by a working industry animator with deep production feedback loops, and it's the tool 90%+ of the studios your sources cite already standardize on. Closing that gap isn't a single release — it's a multi-version program. The plan below sequences it so you ship real value at every stage instead of promising full parity and delivering nothing for a year.

**One specific correction to the original roadmap:** the original Vision-tier (v3.0) list included "IK/FK Matcher" alongside genuinely novel ideas like Root Motion Analyzer and Balance Checker. IK/FK matching isn't a moonshot — AnimBot has shipped it since at least 2020, and several free standalone scripts already exist for it. It's competitive table stakes, not a differentiator, and it's been moved into the v1.5 tier below. The roadmap is stronger when "catch up to AnimBot" and "go beyond AnimBot" are kept honestly separate.

## 2. Module Mapping

Each AnimBot-equivalent feature is assigned to an existing AniKin module where one fits, or a new module where it doesn't. Two new modules are proposed: `AniSpace` (space-switching/pivot tools) and `AniRecover` (autosave/recovery). Recommend adding both to the Brand Stance PRD's module diagram (Section 9) if this plan is approved.

| AniKin Module | Status | AnimBot-Equivalent Features It Houses |
|---|---|---|
| `AniTween` | Existing | Tweener, Scale to Neighboring Keys, Tangent Sliders Suite, Smart Key |
| `AniOffset` | Existing | Align (snap-to-selection fits naturally alongside offset/positioning) |
| `AniBake` | Existing | Baking Tools |
| `AniMirror` | Existing | Mirror / Auto Mirror, IK/FK Match |
| `AniGhost` | Existing | Motion Trail |
| `AniMotion` | Existing | Timeline Boost, Nudge Keys |
| `AniSpace` | **New — proposed** | Temp Controls, Temp Pivot |
| `AniRecover` | **New — proposed** | Anim Recovery |
| Core Shell Utilities (non-prefixed, dev/pipeline layer) | Existing pattern | Select Sets, Time Bookmarks, Reset, Hotkey Manager, Auto Bots, Debug Console |

## 3. Technical Approach Per Feature

### AniTween
- **Tweener:** standard Maya animation curve math — read the surrounding keyframe values via `cmds.keyframe(query=True)` or `OpenMayaAnim.MFnAnimCurve`, lerp between them on a live slider (`QSlider` in the PySide shell), and write back with `cmds.setKeyframe`. This is the same core math Tween Machine already exercises; nothing exotic.
- **Scale to Neighboring Keys:** read tangent angles/weights via `MFnAnimCurve.getTangent`, scale them proportionally toward a neighbor key's value, support multi-channel batch operation by iterating selected curves.
- **Tangent Sliders Suite:** each preset (Linear, Flat, Stepped, Plateau, Spline, Clamped) maps directly to Maya's native `cmds.keyTangent(itt=, ott=)` tangent types. "Smart"/"flow"-style presets (AnimBot's Polished/Bounce/Auto) require custom interpolation: compute a tangent angle that factors in momentum from neighboring keys rather than using a fixed type — this is the one sub-feature here with genuine algorithmic work, everything else is a thin UI layer over native Maya tangent ops.
- **Smart Key:** wrap `cmds.setKeyframe` with a check that only writes keys on channels actually present in the current pose/selection, avoiding the "set key on everything" side effect of a naive keyframe call.

### AniOffset (Align)
- Align uses `cmds.xform(query=True, worldSpace=True)` to read a target's matrix and `cmds.xform` to apply it to the selection, with options to align position only, rotation only, or both.

### AniBake (Baking Tools)
- Core op is `cmds.bakeResults`, wrapped with range options (scene range / custom range / keyframe-only range) and animation-layer awareness (bake into a new layer vs. flatten). This is largely orchestration around a native Maya command, not new math.

### AniMirror (Mirror/Auto Mirror, IK/FK Match)
- **Mirror:** requires a naming-convention or rig-metadata scheme (e.g., `_L`/`_R` suffixes, or a custom attribute on controls) to pair left/right controls, then mirrors transform values across the rig's symmetry plane. This is the one tool in this list that's rig-dependent rather than purely Maya-native — it needs a configurable mirror map per rig, which is worth building as a reusable "mirror profile" system since it'll be reused by the future Pose Mirror and Auto-Mirroring diagnostic work in v2.0+.
- **IK/FK Match:** snapshot the FK chain's world transforms, solve for the matching IK handle/pole-vector position (standard two-bone IK math: law of cosines for the pole vector angle), and vice versa. This is well-trodden — several free reference implementations exist publicly (e.g., Universal IK/FK Switch and Match scripts) that can inform a clean-room AniKin implementation.

### AniGhost (Motion Trail)
- Maya already has a native `cmds.snapshot` / motion trail node (`motionTrail`); the value-add is custom viewport drawing (color-coding spacing between frames) via a `MPxDrawOverride` or by driving curve color attributes on the native node, plus letting the user pick a tracked point other than the control's default pivot (e.g., a vertex or locator).

### AniMotion (Timeline Boost, Nudge Keys)
- **Nudge Keys:** trivial — shift selected key times by ±1 frame via `cmds.keyframe(edit=True, timeChange=...)`, bound to a hotkey.
- **Timeline Boost:** custom Qt event handling layered on top of Maya's timeline widget (or a custom overlay widget) to add gesture-based scrubbing/range-select shortcuts Maya doesn't natively support.

### AniSpace — new module (Temp Controls, Temp Pivot)
- **Temp Controls:** create a transient null/locator parented via `parentConstraint` to the rig control, animate the null, then bake the result back onto the original control and clean up the temp node. This is the most architecturally involved feature in the list — it's effectively a mini constraint-rig system — but it's also one of the most-loved AnimBot tools, so it's worth the investment.
- **Temp Pivot:** simpler version of the same idea — create a temp transform at a chosen pivot location, parent the selection under it for the duration of a rotate/scale operation, then bake and clean up.

### AniRecover — new module (Anim Recovery)
- A background `scriptJob` or Maya callback (`MSceneMessage.kBeforeSave` style) that periodically snapshots keyframe data for the current selection/scene to disk (JSON or `.ma` fragment) in a local cache folder, with automatic pruning of entries older than N days — directly mirrors AnimBot's confirmed approach (`animBot_tmp_data` folder, age-based cleanup).

### Core Shell Utilities (Select Sets, Time Bookmarks, Reset, Hotkey Manager, Auto Bots, Debug Console)
- **Select Sets / Time Bookmarks:** both are straightforward — store a list of object names (or a frame range) under a user-named key, persisted to the per-rig or per-scene prefs file already planned for the Hotkey Manager in the v0.2 PRD.
- **Reset:** cache each control's bind-pose/default values once (on rig load or first use) and restore them with `cmds.setAttr` on demand.
- **Hotkey Manager / Debug Console:** already scoped in the v0.2 PRD (FR-15–17); Debug Console is a thin log viewer reading from a shared AniKin logging utility used across all modules.
- **Auto Bots:** a registry pattern — any module that hooks a Maya callback (`MEventMessage`, `MSceneMessage`, etc.) registers itself with a central manager so the user can see and selectively disable what's running, rather than callbacks being scattered and invisible across modules.

## 4. Revised Roadmap

This supersedes the tiering in the v0.2 Plugin Update PRD's "Non-Goals" section only where noted — v0.2 scope itself is unchanged.

| Tier | Contents |
|---|---|
| **v0.2 (current scope, unchanged)** | Tween basics, Offset, Tangent basics, Nudge, Selection Sets, Hotkey Manager — already defined |
| **v0.3 — AnimBot catch-up, wave 1** | Tangent Sliders Suite, Smart Key, Reset, Align, Temp Pivot, Time Bookmarks, Debug Console |
| **v1.5 — AnimBot catch-up, wave 2 (absorbs original Phase 2 list)** | AniMirror (Pose Mirror + **IK/FK Match, pulled forward from v3.0**), AniBake (Smart Bake), AniGhost (Motion Trail/Ghosting), AniSpace (Temp Controls), AniRecover (Anim Recovery), AniMotion (Timeline Boost), Animation Layer utilities |
| **v2.0 — diagnostics tier (unchanged from original plan)** | Foot Slide Detector, Gimbal Warning System, Curve Cleanup Assistant, Broken Constraint Detection, Overshoot Detection |
| **v3.0 — "Animation Kinematics" vision (IK/FK Matcher removed, now in v1.5)** | Root Motion Analyzer, Center-of-Mass Visualizer, Balance Checker, Unreal Export Validator, Retargeting Diagnostics |

At v1.5, AniKin reaches rough functional parity with AnimBot's most-used tools. Everything from v2.0 onward is where AniKin stops chasing AnimBot and starts being the only free tool in this category that does it.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Solo/small-team bandwidth vs. a multi-year commercial product's feature surface | Phase honestly (above); market "the best free alternative, with a real roadmap to surpass it" rather than "full AnimBot parity now" |
| `AniMirror`'s rig-dependent mirroring breaks on rigs without a clean naming convention | Ship a configurable mirror-map system early (v1.5) rather than hardcoding a naming scheme, so it survives contact with real-world rigs |
| Building a clean-room IK/FK matcher that doesn't infringe on any specific paid implementation | Implement from first-principles two-bone IK math (law of cosines), not by reading AnimBot or paid-script source |
| Feature-by-feature parity messaging undercuts the brand stance ("kinematics-aware," not "AnimBot clone") | Lead public-facing v1.5 release notes with the differentiators already shipped (modular architecture, GPLv3, AniSpace/AniRecover), not a checklist matched 1:1 against AnimBot |

## 6. Open Questions

- Is a rig-agnostic mirror-map system (user defines L/R pairs once per rig) in scope for v1.5, or should v1.5 ship a simpler suffix-convention-only mirror as a stopgap?
- Should `AniRecover`'s checkpoint data sync anywhere (even just a local Git-style history), or stay purely local-disk like AnimBot's implementation?
- Given the bandwidth risk above, is there appetite to scope contributor onboarding (good-first-issue labeling, CONTRIBUTING.md) at v0.3 so the v1.5 wave isn't solely on you?
