---
name: vue-saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface - fixed vertical sidebar on the left instead of a top nav bar, design tokens, consistent spacing, polished cards, tables and forms. Use when asked to modernize, restyle, "SaaS-ify" or move the navigation to a sidebar. Audits first, proposes, then applies the redesign in verified steps.
---

# Vue 3 SaaS Redesign

Turns a Vue 3 app with a top nav bar into a SaaS-style layout: collapsible left sidebar, shared design tokens, consistent spacing, polished components. Visual and structural changes only. Behavior stays identical.

## Model

- Default model is enough. Audit, token work and CSS polish are routine.
- Delegate every `.vue` create or significant edit to the `vue-expert` subagent when the project defines one.
- Ask before switching models. Never switch on your own.

## Hard rules

- Change visuals and layout only. Never touch API calls, routing paths, data logic, store/composable behavior or i18n key meaning.
- New dependency (icon library, UI kit, CSS framework) needed → stop, ask. Default: inline SVG icons, plain CSS, CSS custom properties.
- Emojis in the UI → never. Icons are line-style inline SVG, 20px, `currentColor`.
- Public repo → no credentials, internal hostnames, private registry URLs in any file.
- Every user-visible string goes through the existing i18n function. New label → add to every locale file.
- Commit only when asked. One concern per commit when asked.
- Existing status colors (green/blue/yellow/red) carry meaning → keep their hues, adjust only for contrast.

## Workflow

Run the phases in order. Do not skip Phase 2 approval.

### Phase 0 - Preconditions
1. Working tree dirty → ask whether to continue or stash.
2. Run the client build (`npm run build` in the client folder) → must pass before any change. Failing baseline → stop, report.
3. Dev server running → note URL. Not running → start it.
4. Browser tool available (Playwright MCP) → capture baseline screenshots of every route at 1440px width. Not available → ask the user to check visually later.

### Phase 1 - Audit (read-only)
Collect, then summarize in one table:
- **Shell**: component holding the header/nav and `<router-view>` (usually `App.vue`). List its children (language switcher, profile menu, filter bar, global modals).
- **Routes**: every nav link, its label key, its route.
- **Global CSS**: where shared classes live (`.card`, `.badge`, `table`, `.page-header`, `.stats-grid`, `.loading`, `.error`). Scoped styles in views only override.
- **Tokens in use**: grep hex colors, `font-size`, `border-radius`, `box-shadow`, `padding`, `gap` values. Count frequency. Most frequent value = candidate token, outliers = inconsistencies.
- **Layout dependencies on the top bar**: `position: sticky|fixed`, `top: <n>px`, `100vh`, `z-index` values, `max-width` wrappers, dropdowns anchored `top: 100%; right: 0`.
- **Modals**: z-index and positioning, backdrop style.
- **Design rules** in the project `CLAUDE.md` (palette, no emojis, chart rules) → they win over this skill on conflict.

### Phase 2 - Proposal (approval gate)
Present, 10-15 lines max:
- Token set (see Tokens) with the values mapped from the audit's most frequent ones.
- Sidebar spec (see Sidebar) and nav grouping.
- Where page-level controls go (filter bars, toolbars).
- Deviations from this skill and why.
Use `AskUserQuestion` only for real choices (e.g. keep or change brand color). Wait for approval, then continue.

### Phase 3 - Tokens
- Define tokens once as CSS custom properties on `:root` in the global stylesheet (shell component unscoped `<style>` or a `styles/tokens.css` imported in `main.js`).
- Replace hard-coded values in shared classes first (`.card`, `table`, `.badge`, `.page-header`, `.stats-grid`). Scoped view CSS → replace only in files already being edited. Never mass-rewrite every view.
- Keep a short old-value → token mapping in the final report.

Token baseline (adjust to the audit):

| Group | Tokens |
|---|---|
| Spacing | 4px base: `--space-1` 4, `-2` 8, `-3` 12, `-4` 16, `-6` 24, `-8` 32, `-12` 48 |
| Radius | `--radius-sm` 6, `--radius-md` 8, `--radius-lg` 12 |
| Shadow | `--shadow-sm` (cards), `--shadow-md` (menus), `--shadow-lg` (modals) |
| Type | 12 / 13 / 14 (body) / 16 / 20 / 24 / 30; weights 400, 500, 600, 700; headings `letter-spacing: -0.02em` |
| Color | surface, surface-muted (app bg), border, text, text-muted, primary, primary-soft, plus status colors |
| Layout | `--sidebar-w: 256px`, `--sidebar-w-collapsed: 72px`, `--content-max: 1440px` |

Rules:
- One spacing scale only. Value off the scale → snap to nearest token.
- Cards: 1px border + `--shadow-sm`, padding `--space-6`, gap between cards `--space-6`.
- Text on surfaces → contrast AA (4.5:1 body, 3:1 large).

### Phase 4 - Shell and sidebar
Layout: CSS grid on the root, `grid-template-columns: var(--sidebar-w) minmax(0, 1fr)`. `minmax(0, 1fr)` is required, otherwise wide tables push the page sideways.

Sidebar spec:
- Fixed full height (`100dvh`), white surface, right border, own vertical scroll if links overflow.
- Top: brand (name + subtitle, subtitle hidden when collapsed).
- Middle: nav links as `<nav aria-label="...">` with `router-link`. Each link = icon + label. Group links with small uppercase muted group headings when there are more than 5 links.
- Bottom (pinned): language switcher, profile menu, collapse toggle.
- Active link: primary-soft background, primary text, 2-3px primary indicator on the left edge. Hover: surface-muted. Use `router-link-active` / `aria-current="page"`, not manual path comparison where avoidable.
- Collapsed (72px): icons only, label shown as `title` + accessible name, brand shrinks to a mark, toggle button has `aria-expanded`. Persist state in `localStorage` under an app-specific key.
- Below 1024px: sidebar becomes an off-canvas drawer with overlay. A slim top bar shows hamburger + brand. Esc and overlay click close it, focus moves into the drawer on open and back to the hamburger on close. Route change closes it.
- Transitions 150-200ms on width/transform, disabled under `prefers-reduced-motion`.
- Every interactive element gets a visible `:focus-visible` ring.

Things that break when the top bar disappears. Check each:
- `position: sticky; top: <header height>` on page-level bars → set to `top: 0`.
- Dropdowns anchored `top: calc(100% + .5rem); right: 0` → in the sidebar footer they must open upward or to the right (`bottom: 100%` / `left: 100%`), otherwise they clip.
- `z-index` ladder: content < sidebar < drawer overlay < dropdowns < modals. Sidebar must stay below existing modal and dropdown values.
- `min-height: 100vh` → `100dvh`.
- `max-width` wrapper moves from the shell to the content column.

Page-level controls (filter bars, toolbars) stay in the content column as a sticky bar, never in the sidebar.

### Phase 5 - Component polish
Apply through the shared classes, in this order:
1. **Page header**: title 24-30px, muted description, consistent bottom margin.
2. **Stat cards**: label muted 13px, value 24-30px 600 weight, optional colored accent via status token, hover without layout shift.
3. **Tables**: header muted on surface-muted, 12-13px uppercase optional, row height 44-48px, hover row, numeric columns right-aligned with `font-variant-numeric: tabular-nums`, last row without border.
4. **Badges**: pill, 12px, 500 weight, soft background + readable text color.
5. **Buttons**: primary, secondary (border), ghost. Same height (36px), radius `--radius-md`, disabled state, focus ring.
6. **Inputs / selects / range**: 36px height, border, focus ring in primary, `accent-color` for range.
7. **Loading / empty / error states**: centered, muted, consistent padding, error with soft red surface.
8. **Modals**: shared radius `--radius-lg`, `--shadow-lg`, backdrop rgba slate 40%, padding `--space-6`, header with bottom border.
9. **Custom SVG charts**: keep geometry and data. Only align colors, fonts and text sizes to tokens.

### Phase 6 - Verify
1. Client build passes.
2. Open every route at 1440, 1024, 768 and 390 px width. Check: no horizontal page scroll, no clipped dropdowns, sidebar and drawer states work, sticky bars sit at the top of the content.
3. Keyboard: Tab reaches every nav item, collapse toggle and drawer controls in order, focus ring visible, Esc closes the drawer.
4. Switch language to the longest locale → labels do not break the sidebar or buttons.
5. Open every modal and dropdown → correct layering above the sidebar.
6. Existing behavior unchanged: filters still reload data, forms still submit.
7. Browser tool unavailable → say so, list the checks the user still needs to do.

### Phase 7 - Report
Short summary: files changed, token mapping, deviations from the proposal, checks done vs not done.

## Notes for this repository (Factory Inventory Management)

Verified when this skill was written. Re-check with the audit before relying on them.
- Shell and most global CSS live in `client/src/App.vue`: `.top-nav`, `.nav-tabs`, `.page-header`, `.stats-grid`, `.stat-card`, `.card`, `table`, `.badge`, `.loading`, `.error`.
- Header holds brand, seven nav links, `LanguageSwitcher`, `ProfileMenu`. `FilterBar` renders below it, `<router-view />` in `.main-content`.
- `FilterBar.vue` is `position: sticky; top: 70px; z-index: 90` where 70px is the old header height → change to `top: 0` (or the mobile top bar height below 1024px).
- `LanguageSwitcher.vue` and `ProfileMenu.vue` dropdowns open downward and right-aligned (`z-index: 1000`) → must flip direction in the sidebar footer.
- Modals use `z-index` 2000 (`TasksModal` uses 1000) → sidebar stays at 100-200.
- The `Reports` nav label is hard-coded English in `App.vue`. Move it to the locale files while editing the nav.
- Project design system (`CLAUDE.md`): slate/gray palette (#0f172a, #64748b, #e2e8f0), status colors green/blue/yellow/red, custom SVG charts, no emojis in the UI.
- The `/orders` currency display is inconsistent between its two tables under JPY. Out of scope for a visual redesign, mention it, do not fix it silently.
