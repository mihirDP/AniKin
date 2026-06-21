# UI/UX Resources & Differentiation Guide
## AnimForge — Where to Source Assets, and How to Stay Distinct

**Status:** Draft v0.1
**Date:** June 21, 2026
**Audience:** Design + frontend/UI engineering team
**Companion to:** `03_UIUX_Design_Guidelines_AnimForge.md`

---

## 1. Purpose

The design guidelines doc says *what* the UI should feel like. This doc says *where to actually go* to build it — icon libraries, layout/inspiration sources, color and branding tools — and, just as important, *how to use those sources without converging on a lookalike of any one competitor.*

## 2. Free & Open Icon Libraries

All of these are genuinely free, well-maintained, and — critically for a GPL project that will publicly redistribute its assets — carry permissive licenses that allow redistribution. Always re-check the license on the library's own site before pulling anything in, since terms occasionally change.

| Library | Typical license | Notes |
|---|---|---|
| Tabler Icons | MIT | Large, consistent line-icon set, good base style reference |
| Phosphor Icons | MIT | Multiple weights (thin/regular/bold), flexible for toolbar vs. larger UI |
| Lucide | ISC (MIT-equivalent) | Actively maintained fork of Feather Icons, clean and consistent |
| Iconoir | MIT | Broad coverage, simple style |
| Remix Icon | Apache 2.0 | Good fill + line variants |
| Material Symbols (Google) | Apache 2.0 | Huge library, variable weight/fill — useful as a reference, but distinctive enough on its own that you shouldn't use it unmodified if you want a unique identity |

**What not to do:** pull icons from Flaticon, Iconfinder, or similar marketplaces without checking each individual icon's license — many entries there are "free for personal use" or require attribution per-icon, which doesn't work for a redistributed open-source bundle. If you use anything CC-BY licensed, it needs a credit line in a `CREDITS.md`/`NOTICE` file in the repo — don't skip this.

**Recommended approach:** treat these libraries as a *style and proportion reference*, not a direct source of final assets. Pick one as your base grid/stroke-weight reference, then redraw a small custom set in that spirit so the final icon language is genuinely yours — this also sidesteps any "obviously using stock icon pack X" look.

## 3. Layout & Interaction Inspiration

The single biggest risk to "distinctness" is researching only Maya animation plugins — you'll naturally converge on the same shelf-of-icons look everyone else has. Deliberately widen the net:

| Source type | Examples | Use for |
|---|---|---|
| Adjacent professional creative tools | Blender, DaVinci Resolve, Ableton Live, Affinity Suite, Substance Painter, Houdini | Real, *functioning* dark-themed pro-tool UIs — better reference than concept art because they've been pressure-tested by real users |
| Design systems (general, not Maya-specific) | Material Design, IBM Carbon, Microsoft Fluent 2 | Process reference for building internally consistent tokens (spacing, elevation, state color) — don't import their visual style wholesale, just their *rigor* |
| UI inspiration galleries | Dribbble, Behance | Use sparingly, and only for color/typography/icon-style mood, not layout — a lot of what's there is unrealistic concept work that ignores real engineering constraints (in our case, Qt's actual capabilities inside Maya) |

**Practical exercise:** before finalizing layout, pull 4–5 reference screenshots from *different, non-competing* tools (not just Maya plugins) and identify what you like about each independently. If your final design can be traced back to a single source, that's a signal to diversify further.

## 4. Branding & Color Tools

| Tool | Use |
|---|---|
| Coolors.co | Fast palette generation/exploration |
| Adobe Color | Palette extraction, accessibility-aware palette tools |
| Realtime Colors | Live-preview a palette against an actual UI mockup |
| WebAIM Contrast Checker | Verify text/icon contrast meets accessibility minimums |
| Coblis (color-blindness simulator) | Check category-color coding (per design guidelines §4) against common color-vision deficiencies |
| Google Fonts | If you need a custom typeface for the wordmark/docs site (the in-Maya panel itself should still use system UI font, per design guidelines §4) |

## 5. Maya/Qt-Specific Technical References

- Qt Style Sheets reference (doc.qt.io) — for actually implementing the dark theme/tokens in PySide.
- Qt Designer — for laying out panel structure visually before hand-coding it.
- The same open-source Maya tool repos referenced in the Action Plan doc (Red9 StudioPack, Studio Library, mGear) are also useful here — not for their visuals, but to see how they handle Qt docking inside Maya's own window manager, which has real quirks worth learning from rather than rediscovering.

## 6. Asset Licensing Vetting Process (run for every sourced asset)

1. What's the exact license? (MIT/Apache/SIL OFL = safe and simple. CC-BY = usable, but requires attribution. CC-BY-NC, "free for personal use," or unstated = do not use in a redistributed open-source project.)
2. Does the license explicitly permit redistribution/modification? (Required, since the whole icon set ships inside the GPL repo.)
3. If attribution is required, has it been added to `CREDITS.md`?
4. Was the asset used as direct-use, or as a style reference for original redrawn work? (Direct-use assets need licenses checked individually every time; redrawn-from-reference work just needs the *style* inspiration noted, not licensed.)

## 7. How to Stay Distinct But Intuitive

Distinctness and intuitiveness can feel like they pull in opposite directions — familiar patterns are intuitive *because* they're common. The way to reconcile them: keep interaction patterns familiar (genre conventions, per the design guidelines doc), and make visual identity distinct (color, icon style, logo, motion/feedback details). Don't try to innovate on both axes at once.

**Process:**

1. **Write 2–3 design adjectives before drawing anything** (e.g., "precise, quiet, fast"). Every visual decision gets checked against these instead of against a competitor's screenshot — this keeps the team aligned without anyone needing to reference AnimBot's actual UI mid-design.
2. **Diversify inspiration sources** (Section 3) so no single tool dominates the final look.
3. **Apply standard usability heuristics**, not invented ones:
   - *Hick's Law* — more visible choices = slower decisions, so keep the default shelf view lean and let users opt into showing more tools.
   - *Fitts's Law* — frequently-used toolbar buttons should be appropriately sized and spaced; don't shrink icons just to fit more in.
   - *Progressive disclosure* — advanced options (e.g., bake settings, trail color customization) live in a secondary panel, not cluttering the primary shelf.
   - Nielsen Norman Group's 10 usability heuristics are a solid general checklist to run any new screen against before calling it done.
4. **Low-fidelity first.** Wireframe and test layout/flow before investing in final visual polish — distinctness is cheap to iterate on in grayscale, expensive to redo after icons are finished.
5. **"Fresh eyes" test.** Have someone who has never used AnimBot, aTools, or any similar plugin try the tool cold. If they can't guess what an icon does without a tooltip on first try, that's useful signal regardless of how visually distinct it is — intuitive and distinct both need validating, not just one.
6. **Blind-resemblance check** before each milestone: show a screenshot to someone unfamiliar with the project and ask "does this remind you of a specific existing tool?" If yes, that's a flag to revisit color/icon choices, not necessarily layout (layout conventions are fine to share — see Section 3).

## 8. Suggested Team Workflow

1. Designer pulls reference set (Section 3) and drafts 2–3 design adjectives — share with team for buy-in before any pixels are drawn.
2. Build the color/spacing token system (Section 4 tools) and validate contrast/color-blind safety immediately, not after the fact.
3. Block out low-fidelity wireframes for the shelf + one tool popup, run the "fresh eyes" test even at this stage.
4. Draw the icon set using the licensing-checked reference style (Section 2), holding to one consistent stroke weight/grid.
5. Assemble the Figma component library (per design guidelines §10), run the blind-resemblance check.
6. Hand off to engineering with tokens + assets + the differentiation checklist (design guidelines §12) attached to the PR.
