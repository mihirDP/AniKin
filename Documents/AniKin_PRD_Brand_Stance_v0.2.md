# PRD: AniKin Brand Stance & Positioning — v0.2

**Document owner:** Mihir
**Status:** Draft
**Related doc:** AniKin v0.2 Plugin Update PRD

---

## 1. Purpose

AniKin currently reads as a competent but undifferentiated combination of existing Maya animation tools (AnimBot, aTools, Studio Library, Key Machine). This PRD defines the brand stance AniKin should adopt at the v0.2 milestone so that every naming, messaging, and feature-sequencing decision going forward reinforces a single coherent identity instead of "free alternative to X."

## 2. Background

AniKin = **Ani**mation + **Kin**ematics. The name was chosen before its strategic value was fully recognized — it already implies a technical, analysis-driven tool rather than a script pack. The current feature list (tween, offset, tangents, smart bake, selection sets, motion trails, hotkeys) overlaps heavily with incumbents, which creates a "why switch?" problem. The differentiation opportunity lies in leaning into the kinematics half of the name: pose/motion analysis, diagnostics, and real-time/game-animation workflows that film-oriented toolsets ignore.

## 3. Problem Statement

Without a deliberate brand stance, AniKin risks being perceived as:
- A clone bundling Key Machine, aTools, and AnimBot functionality
- A student project rather than a pipeline-grade tool
- Generic, with no reason for an animator already using AnimBot to switch

## 4. Positioning Statement

> For Maya animators and technical animators who are tired of juggling multiple plugins, AniKin is an open-source animation productivity and analysis toolkit that unifies daily workflow tools with kinematics-driven diagnostics — unlike now-unmaintained toolsets like Key Machine or paid suites like AnimBot, AniKin is free, modular, actively developed, and built to eventually understand the *quality* of an animation, not just speed up keyframing.

Target end-state narrative (v3.0 horizon): **"The intelligent animation analysis and productivity toolkit for Maya."**

## 5. Brand Pillars

1. **Unified Workflow** — one dockable toolkit instead of five disconnected scripts.
2. **Kinematics-Driven Intelligence** — the long-term differentiator: pose mirroring, IK/FK matching, foot-slide detection, root-motion diagnostics. This is what no competitor fully owns.
3. **Open & Transparent** — GPLv3, public roadmap, community-buildable trust (in contrast to closed paid tools).
4. **Built for Modern Pipelines** — Maya 2022–2027, PySide2/PySide6 auto-detection, dockable dark-theme UI, eventual Unreal Engine real-time workflow support.
5. **Evidence of Craft** — for Mihir personally, AniKin doubles as a portfolio piece demonstrating Python/Maya API/UI-UX/product thinking alongside his animation reel.

## 6. Target Personas

| Persona | Need | Why AniKin |
|---|---|---|
| Student animator | Free, full-featured toolkit | No budget for AnimBot |
| Freelancer | Cross-version reliability | Works Maya 2022–2027 without per-studio reconfiguration |
| Indie game animator | Real-time/game-specific diagnostics | No incumbent tool targets UE export/root-motion workflows well |
| Small studio TD | Modular, extensible, auditable | Open-source code, modular architecture, no license fees |

## 7. Competitive Frame

| Tool | Their Stance | AniKin's Counter-Stance |
|---|---|---|
| AnimBot | Paid, polished, broad feature set | Free, modular, eventually diagnostic-first |
| aTools | Free, utility-first | More cohesive UI/UX, broader module roadmap |
| Studio Library | Pose/animation library focus | Library features become one module, not the whole product |
| Key Machine | Free, broad toolset (offset, selection sets, tween/blend sliders, curve editor) — now inactive, no further updates | AniTween absorbed and modernized from Key Machine's tween/blend concepts; AniKin stays actively maintained where Key Machine is archived (open question: whether AniOffset/Selection Sets also draw from Key Machine — see Plugin Update PRD) |

## 8. Messaging Guidelines

**Do:**
- Frame AniKin as a *platform of modules* (AniTween, AniOffset, AniMirror, AniAnalyze, etc.), not a flat feature list.
- Lead with "Animation Kinematics" as the conceptual anchor in any tagline or About section.
- Credit Key Machine and other open-source inspirations explicitly and generously.
- Talk about the *destination* (diagnostic, kinematics-aware tooling) even while shipping the *foundation* (daily-use utilities) in v0.2.

**Don't:**
- Don't market any module as "X tool, but free" (e.g., never say "AniKin now includes Key Machine").
- Don't lead with the full mature feature list (IK/FK matcher, Unreal validator) before it exists — this risks an underdelivery perception if v0.2 only ships MVP tools.
- Don't let the Star Wars "Anakin" association become a joke that overshadows the Animation+Kinematics meaning — acknowledge it lightly if raised, don't lean into it.

## 9. Module Naming Architecture

Use the `Ani-` prefix consistently to reinforce one brand across all sub-tools:

```
AniKin
├── AniTween     (tween/breakdown — Key Machine–inspired, modernized)
├── AniOffset
├── AniBake
├── AniMirror
├── AniGhost
├── AniMotion
├── AniAnalyze   (future: kinematics diagnostics)
└── AniExport    (future: Unreal/real-time workflows)
```

## 10. Licensing & Attribution Stance (Brand-Relevant)

- AniKin remains GPLv3.
- Any Key Machine–derived code must comply with GPLv3 (which it already shares with AniKin), retain required notices, and be credited in-app (About panel) and in the README — this is part of the "Open & Transparent" pillar, not just legal hygiene.
- Brand stance is explicit: *"merge concepts, not identity."* Borrowed logic gets rebuilt and rebranded as a native AniKin module rather than presented as a wrapper.
- **Future consideration — dual licensing:** a model worth evaluating beyond v0.2 is dual licensing — keeping AniKin's community edition under GPLv3 while offering a separate commercial license to studios that don't want GPL's copyleft obligations (e.g., closed-source pipeline integration). This is a common path for open-source projects that want to build community goodwill while creating a revenue option from commercial users. It does not change the v0.2 stance (GPLv3-only, no monetization), but it's worth flagging as a possible v1.0+ business-model direction so the module architecture and contributor agreements aren't built in a way that forecloses it later.

## 11. Success Metrics (Brand)

- Qualitative: community/forum sentiment shifts from "another free AnimBot alternative" to "the kinematics-aware toolkit" within two release cycles.
- Quantitative: GitHub stars, fork count, Discord/forum mentions referencing "AniTween," "AniMirror," etc. by name (proxy for module-brand recognition).
- Portfolio metric: AniKin referenced positively in at least one recruiter/industry conversation as evidence of technical capability.

## 12. Risks

| Risk | Mitigation |
|---|---|
| Perceived as a clone at launch | Lead all public messaging with the modular architecture and kinematics roadmap, not the MVP feature parity |
| ~~Licensing dispute over Key Machine code~~ — resolved: both are GPLv3, and Key Machine's developer has explicitly invited forking/adaptation since the project is no longer maintained | Preserve required GPLv3 notices and in-app credit regardless |
| Roadmap promises outpace v0.2 delivery | Clearly label roadmap tiers (Now / Next / Vision) in all public docs |

## 13. Open Questions

- Should "AniAnalyze" and "AniExport" be teased publicly in v0.2 docs as "coming," or held back until closer to implementation?
- Is there a need for a simple logo/wordmark system per module, or should sub-tools stay text-only within the AniKin shell for now?
