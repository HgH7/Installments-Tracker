---
name: TaqseetPro High-Density Interface
colors:
  surface: '#101415'
  surface-dim: '#101415'
  surface-bright: '#363a3b'
  surface-container-lowest: '#0b0f10'
  surface-container-low: '#191c1e'
  surface-container: '#1d2022'
  surface-container-high: '#272a2c'
  surface-container-highest: '#323537'
  on-surface: '#e0e3e5'
  on-surface-variant: '#c3c6d7'
  inverse-surface: '#e0e3e5'
  inverse-on-surface: '#2d3133'
  outline: '#8d90a0'
  outline-variant: '#434655'
  surface-tint: '#b4c5ff'
  primary: '#b4c5ff'
  on-primary: '#002a78'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#0053db'
  secondary: '#4ae176'
  on-secondary: '#003915'
  secondary-container: '#00b954'
  on-secondary-container: '#004119'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#996100'
  on-tertiary-container: '#ffeedd'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#6bff8f'
  secondary-fixed-dim: '#4ae176'
  on-secondary-fixed: '#002109'
  on-secondary-fixed-variant: '#005321'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#101415'
  on-background: '#e0e3e5'
  surface-variant: '#323537'
typography:
  title-1:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '700'
    lineHeight: 24px
  section-header:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 20px
  body-main:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  data-mono:
    fontFamily: Courier Prime
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar_width: 220px
  detail_panel_width: 320px
  gutter: 16px
  margin_page: 24px
  component_padding_x: 12px
  component_padding_y: 8px
---

## Brand & Style
The design system is engineered for high-density financial management and administrative utility. It prioritizes information density and operational speed over decorative elements. The aesthetic is rooted in **Modern Minimalism** with a **Corporate/Technical** lean, emphasizing clarity, structural integrity, and professional reliability.

The interface is strictly flat to ensure performance and visual predictability. By removing shadows and gradients, the design system focuses the user's attention entirely on data hierarchy and actionable controls. The emotional response is one of precision, control, and efficiency—essential for a desktop business application handling complex transactions.

## Colors
The color palette utilizes a deep slate foundation to reduce eye strain during prolonged use. 

- **Action Strategy:** The Primary Action color (#2563EB) is reserved strictly for main triggers. Hover states shift to a deeper blue (#1D4ED8) to provide immediate tactile feedback without needing elevation changes.
- **Semantic Badges:** Status indicators use high-contrast pairings (e.g., Deep Red background with Light Pink text) to ensure readability at small sizes while maintaining a clear distinction between success, warning, and danger states.
- **Accessibility:** Text Secondary/Muted must never go darker than #94A3B8 to maintain WCAG-compliant contrast ratios against the dark surfaces.

## Typography
This design system employs a dual-font strategy to separate narrative UI from raw data.

- **Interface Font:** While the user request specified Segoe UI, this design system utilizes **Inter** (as the closest available modern equivalent) for all UI controls, navigation, and headers to ensure a clean, neutral professional look across platforms.
- **Financial Font:** **Courier Prime** is used for all numeric data, currency, and dates. The monospaced nature ensures that columns of numbers align perfectly, which is critical for financial auditing and quick scanning.
- **Hierarchy:** Use `title-1` for page headers, `section-header` for widget titles, and `body-main` for general labels and content.

## Layout & Spacing
The layout follows a rigid, high-density desktop grid designed for a 1280x800 viewport.

- **Structural Pillars:** 
    - A fixed **220px Sidebar** on the left for primary navigation.
    - A fixed **320px Detail Panel** on the right for deep-dive information or contextual editing.
    - The **Main Content Area** is fluid between these two pillars, utilizing a 12-column grid.
- **Spacing Rhythm:** A 4px/8px base unit is used. Use 16px gutters between cards and 24px margins at the edge of the application window. 
- **Density:** Padding within inputs and buttons is kept tight (8px/12px) to maximize the amount of visible data without sacrificing clickability.

## Elevation & Depth
In this design system, depth is communicated through **Tonal Layering** rather than shadows.

- **Level 0 (#0F172A):** The application background.
- **Level 1 (#1E293B):** Primary content containers (Cards, Sidebar, Detail Panel).
- **Level 2 (#253347):** Raised elements such as input fields, secondary buttons, or nested containers within a Level 1 card.
- **Separation:** 1px solid borders using #334155 are mandatory for all Level 1 and Level 2 elements to provide crisp definition in the absence of shadows.

## Shapes
The shape language is disciplined and professional, using subtle rounding to prevent the UI from feeling overly aggressive while maintaining a "utilitarian" look.

- **Cards/Containers:** 8px radius creates a soft structural frame.
- **Buttons:** 6px radius distinguishes interactive actions from static containers.
- **Inputs/Fields:** 4px radius provides a sharp, technical feel appropriate for data entry.
- **Status Badges:** Strictly rectangular (0px or 2px radius) to maintain a "stamp" or "label" aesthetic.

## Components
- **Buttons:** Use the Primary Action color for main tasks. Secondary buttons should use the Surface Raised background with a 1px Border. Text should be centered.
- **Status Badges:** Constructed using a Frame. They must include a leading symbol (✓ for Success, ✕ for Danger, ⚠ for Warning, ◷ for Pending) followed by uppercase text in `label-caps` style.
- **Input Fields:** Background should be Surface Raised (#253347) with a 1px border (#334155). On focus, the border should change to the Primary Action color.
- **Data Tables:** Use `data-mono` for all cell content. Headers should be `section-header` with a subtle bottom border. Row height should be fixed at 32px for high density.
- **Sidebar:** Navigation items should have an 8px left-accent bar that appears in the Primary color only when the item is active.
- **Detail Panel:** Should feature a persistent header with a "Close" or "Collapse" action and use Level 1 surface coloring to distinguish it from the Main Content.