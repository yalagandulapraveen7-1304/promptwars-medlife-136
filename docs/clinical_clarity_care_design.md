---
name: Clinical Clarity & Care
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf3'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d5e3fc'
  on-surface: '#0d1c2e'
  on-surface-variant: '#3f4850'
  inverse-surface: '#233144'
  inverse-on-surface: '#eaf1ff'
  outline: '#707881'
  outline-variant: '#bfc7d2'
  surface-tint: '#006398'
  primary: '#006194'
  on-primary: '#ffffff'
  primary-container: '#007bb9'
  on-primary-container: '#fdfcff'
  inverse-primary: '#93ccff'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  on-secondary-container: '#006f66'
  tertiary: '#4648d4'
  on-tertiary: '#ffffff'
  tertiary-container: '#6063ee'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cce5ff'
  primary-fixed-dim: '#93ccff'
  on-primary-fixed: '#001d31'
  on-primary-fixed-variant: '#004b73'
  secondary-fixed: '#89f5e7'
  secondary-fixed-dim: '#6bd8cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#e1e0ff'
  tertiary-fixed-dim: '#c0c1ff'
  on-tertiary-fixed: '#07006c'
  on-tertiary-fixed-variant: '#2f2ebe'
  background: '#f8f9ff'
  on-background: '#0d1c2e'
  surface-variant: '#d5e3fc'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 3rem
    fontWeight: '700'
    lineHeight: 3.75rem
    letterSpacing: -0.025em
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 2.25rem
    fontWeight: '700'
    lineHeight: 2.75rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.75rem
    fontWeight: '600'
    lineHeight: 2.25rem
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.375rem
    fontWeight: '600'
    lineHeight: 1.875rem
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: 1.625rem
  body-lg:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: 1.75rem
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
  body-sm:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.375rem
  label-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '500'
    lineHeight: 1.25rem
  label-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.025em
  metric-value:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 1.875rem
    letterSpacing: -0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  space-2xs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  gutter-mobile: 1rem
  gutter-desktop: 1.5rem
  sidebar-width: 17.5rem
---

## Brand & Style

This design system is tailored for clinical healthcare environments where clarity, calm reassurance, and rapid cognitive processing intersect. Designed for clinicians, care coordinators, and patients, the aesthetic rejects the cold, sterile, and mechanical tropes of legacy medical software in favor of an empathetic, human-centered atmosphere.

### Aesthetic Movement & Philosophy
The visual direction blends **Modern Humanist Minimalism** with subtle **Tactile Micro-affordances**. 
- **Calm Atmosphere:** Soft ivory and cloud backgrounds prevent eye strain during extended night shifts or stressful consultations.
- **Trust & Provenance:** Visual cues convey high clinical confidence, clear diagnostic provenance, and unambiguous semantic status indicators.
- **Warm Authority:** Rounded sans-serif headings soften clinical terminology, while rigid, tabular data alignment ensures precision during critical evaluations.

## Colors

The palette establishes clinical authority while maintaining visual softness. It relies on subtle contrast steps, tinted neutrals, and explicit status cues designed to be instantly distinguishable without inducing alert fatigue.

### Core Tones
- **Primary Accent (`#0284C7`):** Gentle sky-sapphire providing an inviting, trustworthy anchor for primary actions, active navigational states, and key interactive focal points.
- **Secondary Accent (`#0D9488`):** Deep clinical seafoam used for secondary actions, health milestones, and supportive metrics.
- **Tertiary Accent (`#6366F1`):** Gentle periwinkle reserved for audit trails, metadata tracking, provenance chips, and clinical confidence tags.
- **Neutral (`#475569`):** Balanced slate delivering high legibility for secondary metadata, labels, and icons. Headings use deep slate-charcoal (`#0F172A`).

### Surface & Canvas Architecture
- **Canvas Base:** Soft clinical cloud-ivory (`#F8FAFC`), softening edge contrast across displays.
- **Elevated Surfaces:** Pure clinical white (`#FFFFFF`) for cards, sheets, and dialogs.
- **Subtle Surface Tints:** Seafoam wash (`#F0FDFA`) for confirmed sections, soft blue-ice (`#F0F9FF`) for active summaries, and light slate (`#F1F5F9`) for disabled states and neutral toolbars.

### Semantic Status Palette
- **Verified / Optimal:** Background `#ECFDF5`, Border `#A7F3D0`, Text `#065F46`.
- **Warning / Out-of-Range Low:** Background `#FEF3C7`, Border `#FDE68A`, Text `#92400E`.
- **Critical / Out-of-Range High:** Background `#FEE2E2`, Border `#FECACA`, Text `#991B1B`.
- **Pending / Unreviewed:** Background `#FFFBEB`, Border `#FDE68A`, Text `#B45309`.
- **Provenance / Machine Confidence:** Background `#EEF2FF`, Border `#C7D2FE`, Text `#4338CA`.

## Typography

The type system blends friendly approachability with scientific rigor.

### Role Allocation
- **Display & Headlines (`Plus Jakarta Sans`):** Features geometric foundations with friendly, softened terminals. This counteracts clinical intimidation in titles, modal headers, and diagnostic section anchors.
- **Body, Inputs & Labels (`Inter`):** Delivers clean neutral legibility at dense scales, maintaining crisp distinction between glyphs (such as `1`, `l`, and `I`).

### Tabular Setting (`tnum`)
All numerical quantities, vital signs, dosage calculations, and timestamps must render with `font-feature-settings: 'tnum' 1`. This preserves column integrity across tabular reports and chart comparisons, preventing jitter during live monitor updates.

## Layout & Spacing

A structured 8-point base grid governs layout density, maintaining consistent visual breathing room while allowing high data density within clinical workspaces.

### Grid & Responsiveness
- **Desktop (1024px+):** Fluid 12-column layout with 24px (`1.5rem`) gutters and a fixed 280px (`17.5rem`) navigation panel. Lab panels and diagnostic split-views use sticky sidebars with independent scrolling.
- **Tablet (768px - 1023px):** 8-column layout with 16px (`1rem`) gutters. Complex panels stack into progressive disclosure accordions.
- **Mobile (< 768px):** 4-column layout with 16px (`1rem`) margins. Navigation shifts to a persistent bottom action sheet or dock. Primary doctor verification bars remain anchored to the viewport base.

## Elevation & Depth

Visual hierarchy uses ambient, diffused light-scattering rather than heavy directional drops. This mirrors ambient room light bouncing across clean clinical surfaces.

### Surface Tiers
- **Tier 0 (Base Canvas):** `#F8FAFC` flat surface. No elevation.
- **Tier 1 (Cards, Modules, Patient Records):** `#FFFFFF` surface bordered by `#E2E8F0` with shadow: `0 4px 20px -2px rgba(15, 23, 42, 0.05)`.
- **Tier 2 (Popovers, Sticky Action Panels, Dropdowns):** `#FFFFFF` surface with shadow: `0 10px 25px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -2px rgba(15, 23, 42, 0.03)`.
- **Tier 3 (Modals, Overlays, Urgent Alerts):** Backdrop blur `backdrop-filter: blur(4px)` with background `rgba(15, 23, 42, 0.35)` and modal elevation `0 20px 35px -5px rgba(15, 23, 42, 0.12)`.

## Shapes

The interface implements level `2` roundedness (`0.5rem` base), establishing a tactile feel that maintains structured form alignment.

### Radius Assignments
- **Micro Radii (`0.375rem` / `rounded-sm`):** Segmented tab segments, nested metric badges, and validation tooltips.
- **Base Components (`0.5rem` / `rounded`):** Text inputs, primary/secondary buttons, checkboxes, and table row selections.
- **Containers & Cards (`1rem` / `rounded-lg`):** Patient summary cards, medical test widgets, floating action groups, and sheet containers.
- **Full Radii (`9999px` / `rounded-full`):** Status indicators, confidence badges, patient avatars, and provenance source indicators.

## Components

### Buttons
- **Primary:** Filled `#0284C7` with white text, font weight 600, radius `0.5rem`. Smooth transition hover state `#0369A1`.
- **Secondary (Clinical Seafoam):** Subtle tinted background `#F0FDFA` with `#0D9488` text and border `#CCFBF1`. Hover transitions to `#CCFBF1`.
- **Review Bar Action Set:**
  - `[✓ Verify]`: Emerald solid (`#059669`) with white text.
  - `[✏ Edit]`: Outline with `#E2E8F0` border and `#334155` text.
  - `[✕ Reject]`: Subtle crimson wash (`#FEF2F2`) with `#DC2626` text.

### Chips & Semantic Status Badges
- Displayed with `rounded-full`, padding `0.25rem 0.75rem`, and font size `0.75rem` (weight 600).
- Always include an explicit text label and supporting iconography (or colored dot indicator) to ensure accessibility for color-vision deficiencies.

### Medical Provenance Indicators
- Sub-cards indicating source and timestamp (`Source: CBC Panel, 12 Oct 2026`). Rendered on `#F8FAFC` backgrounds with a faint `#EEF2FF` left accent border (2px) and periwinkle label tag.

### Input Fields & Controls
- Form controls use white backgrounds, `#CBD5E1` borders, and 40px minimum touch targets. 
- Focus states apply a 2px ring in `#0284C7` with an ambient glow (`rgba(2, 132, 199, 0.15)`).
- Checkboxes and radios use `0.5rem` and full circles respectively, checking with a high-contrast tick icon.

### Clinical Data Tables
- Clean zebra separation using alternating transparent and `#F8FAFC` row fills. 
- Header rows utilize uppercase `label-sm` with `#64748B` text and bottom border `#E2E8F0`. 
- Lab results that fall out of range trigger a subtle background highlight matching the appropriate semantic status.