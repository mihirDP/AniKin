# UI/UX 2.0 — Icon Language & Execution Resources
## AnimForge — Replacing Text Labels with a Functional Icon System

**Status:** Draft v0.1
**Date:** June 21, 2026
**Builds on:** `03_UIUX_Design_Guidelines_AnimForge.md`, `04_UIUX_Resources_and_Differentiation_Guide_AnimForge.md`

---

## 1. What the Two Screenshots Actually Show

Comparing AnimBot's toolbar to the current AniKin build side by side, the structural difference isn't icon artwork quality — it's information architecture:

- **AnimBot:** zero text section labels anywhere in the row. Every tool is a small glyph, color-grouped, relying entirely on tooltips for discoverability. The whole toolset fits in roughly the same horizontal space as four or five words.
- **AniKin (current):** every section is announced with a text word — TRANSFORM, TANGENTS, TIMING, TWEEN, WORKFLOW, CHANNELS, CURVES, VIS, SETUP — interspersed with the actual function icons. That's why it reads as "not justifying what the icons do": the text labels are doing the explaining, not the icons, and they're eating roughly half the toolbar's width to do it.

This isn't unique to AnimBot — it's the default convention across essentially all professional creative software toolbars (Photoshop, Premiere, DaVinci Resolve, Blender, After Effects). None of them label tool groups with text in the main toolbar; they rely on icon recognition plus tooltips. That convention is genre-wide and free to adopt — it's a UX pattern, not anyone's IP. What follows is how to execute it with AnimForge's own original icon set.

## 2. Why Icon-Only Wins Here

- **Density:** at AniKin's current width, the text labels alone likely take more horizontal space than every icon combined — converting to icon-only could roughly halve the toolbar's footprint.
- **Scan speed:** experienced users stop reading words entirely after the first few sessions; recognizable shapes are processed faster than text, which is exactly why this pattern persists across every major creative tool.
- **Fitts's Law:** smaller, consistent, evenly-spaced icon targets are faster to hit repeatedly than mixed text-plus-icon clusters of varying width.

## 3. Principles for Icons That Actually Justify Their Function

This is the real fix for "the current icons don't justify what they do" — apply these regardless of visual style:

1. **Literal actions get literal symbols.** Lock, delete, search, settings — use the symbol everyone already recognizes from every other application (a padlock, a trash can, a magnifying glass). Don't invent a clever alternative; recognizability beats originality here.
2. **Diagrammatic concepts get literal diagrams.** Tangent/curve tools are the clearest case: the most legible icon for "ease-in-ease-out tangent" is a small graph that actually looks like that curve's shape. This is a near-universal convention across animation and motion software (After Effects' graph editor, CSS easing pickers, DaVinci Resolve) — because the icon and the function are the same thing, a mini-diagram of it. Draw your own curve shapes and your own line weight; the convention of "draw the curve" is free to use, the specific curve artwork should be yours.
3. **One stroke weight, one grid, the whole set.** Pick a canvas (e.g., 24×24px) and a stroke weight (e.g., 1.5px) and hold both across every icon — inconsistency in weight is what makes icon sets feel like they were assembled from different sources, regardless of individual icon quality.
4. **State is shown on the icon, not in a text label.** An active/toggled tool (motion trail on, channel locked) should change visually — border, fill, or color shift — rather than relying on a separate text indicator.
5. **Color groups, doesn't decorate.** Assign one accent per functional cluster (see the mockup below) so the eye can jump to "the curve tools" or "the channel tools" as a group before reading any individual icon — this replaces the job AniKin's text labels are currently doing, just visually instead of verbally.

## 4. Proposed Icon Language Map for AniKin's Current Sections

This maps each existing text-labeled section to an icon-only equivalent. Concepts are described functionally — your designer should sketch original artwork from these descriptions, not trace any reference image.

| Current section | Tools (from your screenshot) | Proposed icon concept | Tooltip text |
|---|---|---|---|
| TRANSFORM | reset / move / rotate | generic reset arrow, four-way move cross, circular rotate arrow | "Reset transform" / "Move tool" / "Rotate tool" |
| TANGENTS | spline wave / linear dash / list / chain | a small original curve-graph glyph, a straight diagonal line, a stacked-list glyph, a link/chain glyph | "Spline tangent" / "Linear tangent" / "Tangent presets" / "Break tangents" |
| TIMING | prev / next / jump-start / jump-end / offset | chevron-left, chevron-right, double-chevron-left, double-chevron-right, a stepped-offset glyph | "Previous key" / "Next key" / "Jump to start" / "Jump to end" / "Offset keys" |
| TWEEN | slider + % | keep the slider control itself (it's already non-text-reliant) but drop the word "TWEEN" — pair a small icon (e.g., a midpoint-blend glyph) with the slider instead | "Tween blend" |
| WORKFLOW | cube / box select | a cube glyph (bake), a marquee/selection glyph | "Bake to world space" / "Selection set" |
| CHANNELS | lock / unlock / key / x | closed padlock, open padlock, a key glyph, a trash glyph | "Lock channel" / "Unlock channel" / "Key channel" / "Delete keys" |
| CURVES | swap arrows | a transfer/exchange arrows glyph | "Transfer curve" |
| VIS | layers | a stacked-layers glyph | "Toggle motion trail" |
| SETUP | keyboard / gear | keyboard glyph, gear glyph | "Hotkeys" / "Settings" |

See the mockup below for one way this could look assembled — treat it as a starting sketch, not a final spec.

## 5. Execution Resources

**Icon design / vector tools**
- Figma (free tier is sufficient) — build the icon grid template, draw, and export as a synced SVG set.
- Tabler Icons / Phosphor Icons / Lucide (all MIT-licensed, per the prior resources doc) — use as proportion/style references while sketching, not as final assets.

**Legibility testing**
- Export your icon set at actual toolbar size (e.g., 24px) and show it to 3–5 animators unfamiliar with the project — ask them to guess function with no tooltip visible. This is the direct test for "do these icons justify what they do."
- WebAIM Contrast Checker — verify icon-color-against-background contrast meets accessibility minimums, especially for the lighter accent colors against Maya's dark UI.
- Coblis color-blindness simulator — re-check your category color-coding (Section 4 above) since it's now doing more communicative work than before.

**Maya-specific technical prep**
- Export icons as PNG with alpha transparency (Maya's `iconTextButton` expects this format), at minimum two sizes (1x and 2x) for HiDPI displays — Maya doesn't always auto-scale shelf icons cleanly across different display scaling settings.
- Keep a master SVG source per icon so re-exporting at new sizes later doesn't mean redrawing.

## 6. Icon-Specific Differentiation Check

In addition to the general checklist in `03_UIUX_Design_Guidelines_AnimForge.md` §12, run this specifically for the icon set:

- [ ] No icon was drawn by tracing or closely matching the silhouette of an icon visible in any commercial tool's screenshot
- [ ] Curve/diagram-style icons use your own chosen curve shapes and stroke style, not a redrawn copy of a specific reference image
- [ ] The category color palette uses original hex values (Section 3 of the prior resources doc has the palette tools)
- [ ] Tested against the "fresh eyes" reviewer from the prior resources doc §7 — can they guess function without ever having seen AnimBot's UI?

## 7. Suggested Execution Order

1. Audit every current text label against the map in Section 4 — confirm nothing's missing.
2. Sketch icon concepts on paper or in Figma using the functional descriptions, not reference tracing.
3. Build the shared grid/stroke-weight template before finalizing any single icon, so the whole set stays consistent.
4. Run the legibility test (Section 5) early, on sketches if needed — cheaper to fix at this stage than after final export.
5. Export, integrate into the Qt toolbar, replace text labels, re-test with tooltips enabled.
