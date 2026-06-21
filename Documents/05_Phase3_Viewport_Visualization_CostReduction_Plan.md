# Phase 3 De-Risking & Cost-Reduction Plan
## Viewport Visualization (Motion Trail + Ghosting) — AnimForge

**Status:** Draft v0.1
**Date:** June 21, 2026
**Supersedes:** Action Plan §4 (Phase 3) timeline, partially
**Audience:** Engineering team

---

## 1. The Core Insight

The original Action Plan flagged Phase 3 as the hardest piece because it assumed both motion trails and ghosting would require a custom `MPxDrawOverride` built from scratch. That assumption is only half true. Maya already does a meaningful chunk of this work natively, and several real tools in this exact genre exploit that rather than reimplementing viewport drawing themselves. The strategy below is: **wrap what Maya already draws natively wherever it covers the need, and reserve genuinely custom draw code for the one piece that actually requires it.**

This isn't cutting corners — it's the same engineering judgment that experienced Maya tool developers apply: don't rebuild what the host application already does well.

## 2. Motion Trail — Revised Approach

**Don't build a custom draw override for this.** Use Maya's native `motionTrail`/`motionTrailShape` node.

- Created via `cmds.snapshot(motionTrail=True, ...)` or the underlying `motionTrail` node directly — Maya's own Viewport 2.0 renders it, fully cross-version-compatible since Autodesk maintains that rendering path, not you.
- It already supports per-frame markers, trajectory display, and several display attributes you can drive from your UI.
- **What you actually build:** a clean UI wrapper around node creation/cleanup, a marking menu for quick access, and a thin styling layer that maps the design doc's color-coding scheme (§8 of the UI/UX guidelines) onto the node's available display attributes.
- **Real precedent:** both aTools and Zoo Tools Pro — established tools in this exact space — wrap this same native node rather than writing custom draw code. This isn't a shortcut unique to a tight budget; it's the standard approach.

**Revised estimate:** what was budgeted as ~4 weeks of draw-override R&D becomes ~1–1.5 weeks of node-management and UI work.

**When you'd actually need custom draw instead:** only if you want a visual the native node's attributes genuinely can't produce (e.g., a gradient effect well beyond its exposed color options). Treat that as a v2 stretch item gated on real user demand, not a v1.0 requirement — don't pre-build complexity nobody's asked for yet.

## 3. Ghosting / Onion-Skin — Revised Tiered Approach

This one genuinely needs custom work for full mesh ghosting, but split it into two tiers so you ship value early without committing the full budget up front.

### Tier 1 (MVP, low cost): wrap Maya's native ghosting
Maya's built-in ghost feature already ghosts rig controls/locators across a frame range with no custom draw code needed. This covers a large share of real animator use — timing reference on control positions is what most animators actually look at while blocking, even though it doesn't show ghosted mesh. Wrap it with your UI (range, opacity, color via your design tokens) and ship it in v1.0.

### Tier 2 (stretch, higher cost): true skinned-mesh onion-skin
For ghosting the actual deforming mesh (not just controls), you need a render-override / offscreen-buffer-compositing approach: render the relevant frames to offscreen buffers, then composite them into the viewport at reduced opacity. This is genuinely the harder technical lift in this whole project.

- This isn't unprecedented territory — open-source prior art exists (Christoph Lendenfeld's OnionSkinRenderer, with community forks maintained for recent Maya versions). Study its documented technique as an architecture reference before designing your own.
- **Before reusing any of its actual code:** check its current license terms directly on the repository — don't assume permissive terms apply. If the license doesn't cleanly support redistribution inside a GPLv3 project, treat it as a technique reference only and write your own implementation against that pattern.
- Gate this tier on actual user demand from your v1.0 beta feedback (per Action Plan §6) rather than building it speculatively — if Tier 1 control-ghosting satisfies most testers, you've saved real budget; if mesh ghosting is repeatedly requested, you build it knowing it's actually wanted.

## 4. General De-Risking Tactics (apply beyond just Phase 3)

- **Time-box a research spike first.** Before committing engineering weeks to any "hard" phase, spend 3–5 days specifically answering "does Maya already do most of this?" The motion trail finding above is exactly the kind of thing a short spike surfaces — it would have been expensive to discover four weeks into custom draw-override work instead.
- **`MUIDrawManager` over raw OpenGL/DirectX, when you do need custom draw.** If you reach a point where a true `MPxDrawOverride` is unavoidable, use `MUIDrawManager` inside `addUIDrawables()` rather than hand-rolling graphics-API calls — it's Maya's own high-level immediate-mode drawing API and removes a large chunk of the boilerplate and cross-backend complexity that makes custom viewport drawing expensive in the first place.
- **Build the simplest possible functional version first.** A single static debug shape drawn via the chosen approach, confirmed working across your target Maya versions, before attempting the full feature. Cheap to throw away if the approach turns out wrong; expensive if discovered after building the full feature.
- **Two-tier shipping pattern, generally.** Where a "native wrap" can deliver most of the value, ship that first and treat the fully custom version as a gated, demand-validated follow-up — not just for ghosting, this pattern is worth applying anywhere else in the roadmap that looks expensive.

## 5. Revised Phase 3 Timeline

| Item | Original estimate | Revised estimate | Why |
|---|---|---|---|
| Motion trail | ~4 weeks (custom draw override) | ~1–1.5 weeks | Wraps native `motionTrail` node instead of custom drawing |
| Ghosting — Tier 1 (control ghosting) | (bundled into the original 4-week estimate) | ~3–4 days | Wraps native ghost feature |
| Ghosting — Tier 2 (mesh ghosting) | (bundled into the original 4-week estimate) | Deferred to v2.0, gated on demand | Genuinely hard; do it once, do it informed by real feedback |
| **Phase 3 total for v1.0** | **Weeks 11–14 (full 4 weeks)** | **~2–2.5 weeks** | Net time saved gets reallocated to QA/polish or pulled forward into Phase 4 |

## 6. Recommended Updates to Other Documents

- **PRD §11 (Release Milestones):** Phase 3 can likely compress into the existing Week 11–14 window with slack left over, or the freed time can extend Phase 5 (QA) — recommend the team decide which once Tier 1 is actually prototyped and the real time cost is confirmed.
- **PRD §13 (Risks):** add "mesh-ghosting scope creep" as a tracked risk — it's the one piece of this phase still genuinely open-ended, so keep Tier 2 explicitly out of the v1.0 commitment.
- **Action Plan §4 (Phase 3):** replace the single "prototype `MPxDrawOverride` in isolation" instruction with: first prototype wrapping the native `motionTrail` node, only fall back to a custom draw override if that proves insufficient.
