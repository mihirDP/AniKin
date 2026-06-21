# UI/UX Design Guidelines
## AnimForge — Open-Source Animator's Toolkit for Maya

**Status:** Draft v0.1
**Date:** June 21, 2026
**Audience:** Design + frontend/UI engineering team

---

## 1. Purpose & Scope

This document guides the visual and interaction design of AnimForge's UI. It exists so that every contributor — whether building the shelf, an icon set, or a single tool's popup — works from the same design language instead of improvising one per feature.

## 2. Design Ethics & IP Note (read first)

AnimForge sits in an established genre: professional Maya "animator toolbelt" plugins (AnimBot, aTools, Studio Library, Red9, mGear, etc.). That genre shares a set of **functional UX conventions** — dockable icon shelves, dark themes matching Maya's own UI, tooltip-driven discoverability, marking-menu-style secondary actions. These conventions aren't proprietary to any one product; they're how this category of tool has converged over a decade of Maya plugin development.

What we deliberately do **not** do: copy any specific commercial tool's actual icon artwork, exact color values, logo, or pixel-for-pixel layout. The principle is "same genre, distinct identity" — think of how multiple DAWs (Ableton, FL Studio, Logic) all use a dark theme with a horizontal timeline, but none of them look like a reskin of another. That's the bar here. Section 12 has a concrete differentiation checklist — every designer should run new work against it before merging.

## 3. Design Principles

1. **Stay out of the animator's way.** The UI is a utility belt, not a destination — it should be glanceable and fast, not a thing people "browse."
2. **Icon-first, label-second.** Animators work fast and repeatedly; icons should be recognizable at a glance once learned, with tooltips as the safety net, not the primary label.
3. **Match Maya's native chrome.** The toolkit should feel like it belongs inside Maya, not like an embedded web app — respect Maya's existing dark palette and widget conventions rather than importing an unrelated design system.
4. **Status is always visible.** Any tool with an "on/off" or "active" state (motion trail, ghosting, locked channels) must show that state directly on its icon — no hidden toggles.
5. **Everything is keyboard-reachable.** Every action available via click must also be hotkey-assignable.

## 4. Visual Identity

- **Name/logo:** Original, distinct from any existing commercial tool. Logo should work as a small monochrome glyph (for the toolbar) and a full wordmark (for docs/website).
- **Color system:**
  - Base UI: dark neutral grays matching Maya's default theme (so the panel doesn't visually clash when docked).
  - One primary accent color for "active/selected" states.
  - A small secondary palette (3–4 colors max) for *category* coding across modules (e.g., Key Editing tools share one hue family, Visualization tools another) — this aids muscle memory without relying on text labels.
  - Run the full palette through a color-blindness simulator (deuteranopia/protanopia at minimum) before finalizing — category coding by color alone is an accessibility risk if not checked.
- **Typography:** System/UI font matching Maya's own (avoid introducing a custom font — it's the fastest way to make the panel feel like a foreign element).

## 5. Layout & Information Architecture

- **Primary surface:** a single dockable/floating shelf, matching the standard Maya custom-toolbar paradigm (this is a widely used, generic Qt pattern — not specific to any one plugin).
- **Organization:** icons grouped into the five PRD modules (Selection, Key Editing, Visualization, Workflow, Hotkeys), each with a subtle visual separator, not a hard boxed section — keep it light.
- **Customization:** users can reorder, hide, or pin frequently-used tools — store this in a local config, not hardcoded.
- **Density:** default to a compact icon-grid layout (single row or 2-row wrap depending on dock width) — avoid large padding that wastes shelf space, since shelf real estate is precious in a typical animator's window layout.

## 6. Interaction Patterns

| Action | Pattern | Notes |
|---|---|---|
| Primary tool action | Single click | Immediate execution, no confirmation dialog for non-destructive actions |
| Secondary/related options | Right-click → marking-menu-style radial or simple context menu | Standard Maya interaction idiom, already familiar to every animator |
| Reorder shelf icons | Drag handle, visible on hover | Don't require a separate "edit mode" toggle if avoidable |
| Toggle tools (trail, ghosting, lock) | Click to engage, icon changes state (border/glow) while active | State must be visible without opening a panel |
| Destructive actions (e.g., bake overwrite) | Single click + lightweight inline confirm (not a modal dialog) | Modal dialogs interrupt animation flow — avoid them unless truly destructive and unrecoverable |

## 7. Iconography Guidelines

- **Style:** flat, simple line/glyph icons — legible down to ~20–24px (typical Maya shelf icon size).
- **Stroke weight:** consistent across the full set (pick one weight, e.g., 1.5px at a 24px canvas, and hold it everywhere).
- **Process:** sketch concept → vector in a single tool (Figma/Illustrator) → normalize stroke/sizing against a shared icon grid template → export as SVG (scales cleanly across HiDPI displays) → convert to the format Maya's `cmds.iconTextButton` needs at build time.
- **Originality check:** every icon should be sketched from the *function* it represents (e.g., a wavy line for "smooth/overshoot," a dotted arc for "motion trail"), not redrawn from a reference screenshot of any existing tool's icon.

## 8. Viewport Overlay UX (motion trail / ghosting)

These render *inside* the Maya viewport, not the panel, so they need their own conventions:

- **Motion trail:** distinct color gradient across the frame range (e.g., one consistent hue with opacity/brightness falloff toward past/future) so direction of time is readable without a legend.
- **Ghosting/onion-skin:** clearly distinguishable past-vs-future pose color (e.g., one cool tone for past, one warm tone for future), low opacity by default with a user-adjustable slider.
- Keep both overlays toggleable independently and visually quiet by default — they should aid, not clutter, the viewport.

## 9. Accessibility & Usability

- Color is never the *only* signal for state — pair category/status color with a shape or icon-state change too.
- All icons sized for legibility at standard 1080p–4K display scaling; test at both.
- Tooltips include the assigned hotkey, not just the tool name.
- First-run experience: a lightweight, dismissible tooltip walkthrough rather than a forced modal tutorial.

## 10. Design System Deliverables (what the team should actually produce)

- A Figma (or equivalent) file containing: color tokens, spacing scale, icon grid template, full icon sheet, and a component library for the shelf/panel.
- A living style guide page in the project docs site referencing the same tokens, so engineering and design never drift out of sync.

## 11. Review & Testing Process

- Icon legibility test: show the icon set at actual 20–24px size to 3–5 animators unfamiliar with the project, ask them to guess function — anything under ~70% correct guesses gets redesigned.
- Usability pass with real animators on real shots before each milestone release (ties to the beta-testing step in the Action Plan document).

## 12. Differentiation Checklist (run before merging any new UI work)

- [ ] No icon was traced or closely redrawn from a screenshot/reference of an existing commercial tool
- [ ] Color palette hex values are original, not sampled from another tool's UI
- [ ] Logo/wordmark is original artwork
- [ ] Panel layout is structurally similar to the *genre* (dockable icon shelf) but not a 1:1 layout match to any single named product
- [ ] Naming/labels in the UI are original wording, not copied from another tool's tooltips or menu text
