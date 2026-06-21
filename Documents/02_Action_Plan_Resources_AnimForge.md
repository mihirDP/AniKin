# Step-by-Step Action Plan & Resources
## Building AnimForge — Open-Source Maya Animation Toolkit

Companion document to the PRD. This is the execution playbook: what to set up, in what order, what to study (and what *not* to touch), and a realistic timeline.

---

## 0. Ground Rules (read first)

1. Never open, decompile, or reference AnimBot's actual code/binary at any point in this project. If you're ever unsure whether something counts as "too close," default to not doing it.
2. Every line of code in this project is either written by you or pulled from a license-compatible (MIT/BSD/LGPL/GPL-compatible) source with attribution.
3. GPLv3 `LICENSE` file goes into the repo on day one, not at the end.

---

## 1. Phase 0 — Research & Environment Setup (Week 1–2)

**Software/accounts**
- Maya — install your current version plus at least one older one (e.g., latest + 2022) for compatibility testing later.
- Maya Python API devkit / Autodesk's official Maya Python API documentation (search "Maya Python API help.autodesk.com" for the current version's docs — the URL structure changes per release, so don't hardcode an old link).
- Git + a GitHub repo, initialized with a GPLv3 `LICENSE` (GitHub's "Choose a license" flow generates this correctly).
- VS Code (or your editor of choice) configured to use `mayapy` as the Python interpreter so autocomplete/linting works against Maya's actual Python environment.
- PySide2 or PySide6 — match whichever your target Maya version ships with; don't assume, check per-version.

**Study (concepts only, not code copying)**
- Autodesk's official Maya Python API 2.0 documentation — this is your primary reference for the whole project.
- Red9 StudioPack source (GPL) — read for *architecture* patterns: how a large modular GPL animation toolkit is organized.
- Studio Library source (LGPL) — read for dockable Qt panel structure.
- Chad Vernon's Maya Python API tutorials/blog — widely regarded as the best technical on-ramp for `OpenMaya` 2.0.
- mGear source (MIT) — clean example of a plugin/module loader pattern.

Given your CS background, the Qt/Python architecture work here will feel familiar — the genuinely new territory is Maya's `OpenMaya` API and `MPxDrawOverride` for viewport drawing, which has no real equivalent in Unreal/Blender's scripting models. Budget extra study time specifically there.

## 2. Phase 1 — Architecture & Plugin Skeleton (Week 3–4)

- Build the Maya Module (`.mod`) file and minimal plugin registration so Maya recognizes and loads your tool.
- Build an empty dockable Qt panel that opens reliably across your test Maya versions.
- Define the module-loader interface every tool will plug into (this is the single most important piece to get right early — everything else builds on it).
- Commit early, commit often, tag this as `v0.0.1-skeleton`.

## 3. Phase 2 — Core MVP Tools (Week 5–10)

Build in this order (easiest → hardest, and each one is independently shippable/testable):

1. **Selection sets** — straightforward `cmds`/API selection management, good warm-up.
2. **Anim offset** — stagger keyframes across a selection; mostly keyframe-data manipulation, no viewport drawing.
3. **Tween/breakdown slider** — slightly more involved, requires a live-updating slider UI tied to keyframe interpolation.
4. **Smart bake** — bake to world-space locator and back; touches constraints and bake API.

Each tool: write a design note (1 paragraph), build it, test it against a rigged test scene, then move on. Don't polish UI yet — function first.

## 4. Phase 3 — Viewport Visualization (Week 11–14)

This is the hard phase — budget real slack time here.

- Prototype `MPxDrawOverride` in isolation first (a static debug shape) before attempting motion trails.
- Motion trail: draw per-frame world-space positions of selected controls across a frame range.
- Ghosting/onion-skin: render faded poses at offset frames — this typically needs either duplicate geometry rendering or a custom shader/draw approach; research both before committing.
- Performance-test on a 50+ joint rig before calling this phase done.

## 5. Phase 4 — UI/UX Polish & Hotkeys (Week 15–16)

- Reorderable toolbar/shelf.
- Per-tool hotkey assignment UI, persisted to a local config file.
- Pass over icons — original artwork only (this is actually a place where your 3D/illustration background is a direct advantage).

## 6. Phase 5 — QA & Cross-Version Testing (Week 17–18)

- Test matrix: Maya 2022 / 2023 / 2024 / 2025 / 2026 × Windows/macOS/Linux (at minimum, cover Windows fully since that's the dominant install base; macOS/Linux can be best-effort).
- Recruit a few beta testers — animator friends, or communities like r/Maya, Polycount, CGSociety, relevant Discord servers. Real animators stress-testing real shots will surface bugs you won't find solo.

## 7. Phase 6 — Packaging & Distribution (Week 19–20)

- Build a simple drag-and-drop installer (a Python `.mod`-based installer is the standard pattern in this ecosystem).
- GitHub release with: README, `LICENSE` (GPLv3), `CONTRIBUTING.md`, screenshots/GIFs of each tool in action.
- Consider also mirroring the release on itch.io — it supports free/pay-what-you-want GPL projects fine and has discoverability among technical artists.

## 8. Phase 7 — Documentation (ongoing, finalize Week 21)

- A simple docs site (GitHub Wiki is fine to start; `mkdocs` if you want something nicer later).
- Short demo videos per tool — these double as portfolio content for your LinkedIn presence, which is a nice two-birds outcome.

## 9. Phase 8 — Launch & Community (Week 22+)

- Announce on r/Maya, r/vfx, Polycount, CGSociety, relevant Maya Discords, and LinkedIn.
- Open GitHub Issues/Discussions for feature requests.
- Set up a public roadmap (GitHub Projects board) so contributors know where help is wanted.

---

## 10. Timeline Summary

| Pace | Estimated time to v1.0 |
|---|---|
| Part-time, alongside coursework | ~5–6 months |
| Full-time focus | ~10–12 weeks |

## 11. Legal Compliance Checklist (revisit before every release)

- [ ] No code, assets, or icons copied/decompiled from any closed-source tool
- [ ] Original name, original icon set, trademark search done before public launch
- [ ] `LICENSE` file (GPLv3) present and current
- [ ] All third-party dependencies checked for GPL compatibility
- [ ] README clearly states the project is original work inspired by a *genre* of tools, with no claim of affiliation with any specific commercial product

## 12. Where to Find Help When Stuck

- Autodesk's official Maya Python API forums/documentation — first stop for API questions.
- Tech-Artists.org and the Maya subreddit — both have active, knowledgeable communities for exactly this kind of tool development.
- Red9 StudioPack and mGear GitHub Issues (closed and open) — often contain solved versions of problems you'll hit.
