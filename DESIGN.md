---
name: Savor Mobile
colors:
  surface: '#fff8f6'
  surface-dim: '#eed5cd'
  surface-bright: '#fff8f6'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fff1ed'
  surface-container: '#ffe9e3'
  surface-container-high: '#fde3db'
  surface-container-highest: '#f7ddd5'
  on-surface: '#261814'
  on-surface-variant: '#594139'
  inverse-surface: '#3c2d28'
  inverse-on-surface: '#ffede8'
  outline: '#8d7168'
  outline-variant: '#e1bfb5'
  surface-tint: '#ab3500'
  primary: '#ab3500'
  on-primary: '#ffffff'
  primary-container: '#ff6b35'
  on-primary-container: '#5f1900'
  inverse-primary: '#ffb59d'
  secondary: '#9f4122'
  on-secondary: '#ffffff'
  secondary-container: '#fd8863'
  on-secondary-container: '#722104'
  tertiary: '#00677e'
  on-tertiary: '#ffffff'
  tertiary-container: '#00a7cb'
  on-tertiary-container: '#003744'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdbd0'
  primary-fixed-dim: '#ffb59d'
  on-primary-fixed: '#390c00'
  on-primary-fixed-variant: '#832600'
  secondary-fixed: '#ffdbd0'
  secondary-fixed-dim: '#ffb59e'
  on-secondary-fixed: '#3a0b00'
  on-secondary-fixed-variant: '#7f2a0d'
  tertiary-fixed: '#b5ebff'
  tertiary-fixed-dim: '#59d5fb'
  on-tertiary-fixed: '#001f28'
  on-tertiary-fixed-variant: '#004e60'
  background: '#fff8f6'
  on-background: '#261814'
  surface-variant: '#f7ddd5'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.01em
  price-display:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '700'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-margin: 16px
  element-gap-sm: 8px
  element-gap-md: 16px
  element-gap-lg: 24px
  section-padding: 32px
---

## Brand & Style

This design system is built for a premium, high-intent food discovery experience. It prioritizes appetite appeal through high-quality photography, utilizing a **Corporate / Modern** style influenced by iOS design patterns. The goal is to evoke a sense of freshness, speed, and reliability.

The interface is intentionally minimal to allow food imagery to remain the focal point. By utilizing generous whitespace and a sophisticated "Soft Modern" aesthetic, the system ensures that complex menu data remains digestible and accessible. The tone is welcoming and professional, targeting urban consumers who value convenience without compromising on quality.

## Colors

The palette is anchored by a vibrant **Sunset Orange (#FF6B35)**, chosen for its psychological connection to hunger and energy. A softer secondary orange is used for supporting accents and hover states.

- **Primary:** Used for core CTAs like "Add to Cart" and active navigation states.
- **Success:** Reserved for dietary indicators (Veg/Non-veg) and confirmation messages.
- **Backgrounds:** Pure white is used for the primary canvas to ensure food photos pop, with a subtle off-white (`#F9FAFB`) used to differentiate card backgrounds or section headers.
- **Typography:** High-contrast dark grey (`#1F2937`) ensures maximum readability for menu item names, while a softer grey (`#6B7280`) handles descriptions and meta-data.

## Typography

This design system uses a dual-font approach to balance personality with utility. **Plus Jakarta Sans** is used for headlines and labels to provide a friendly, rounded aesthetic that complements the brand. **Inter** is utilized for body text and item descriptions to ensure maximum legibility at small sizes.

On mobile, headlines are capped at 24px to prevent excessive word-wrapping. Price displays are treated as critical data points, using a semi-bold weight and a dedicated role to ensure they are immediately scannable.

## Layout & Spacing

The layout follows a **Fluid Grid** model optimized for narrow viewports. It adheres to an 8px spacing scale, ensuring consistent visual rhythm.

- **Margins:** A standard 16px horizontal margin is applied to the main container.
- **Gutter:** 16px between columns for multi-column layouts (e.g., category tiles).
- **Safe Areas:** Adheres to iOS safe area insets for bottom navigation and top status bars.
- **Vertical Rhythm:** Components like Menu Items are separated by 24px-32px to provide clear visual breathing room between different dishes.

## Elevation & Depth

To achieve a premium "iOS-style" feel, the design system avoids heavy shadows in favor of **Ambient Shadows** and tonal layering.

- **Level 1 (Cards):** Very soft, diffused shadow (`0px 4px 20px rgba(0,0,0,0.05)`) used for menu item cards to lift them slightly from the background.
- **Level 2 (Floating Buttons):** Higher elevation shadow (`0px 8px 24px rgba(255, 107, 53, 0.2)`) used for the "View Cart" or "Menu" floating action buttons to denote interactivity.
- **Level 3 (Modals):** Backdrop blurs (20px) are used behind overlays and bottom sheets to maintain context of the underlying menu while focusing user attention.

## Shapes

The shape language is defined by large, friendly radii that mirror the "Plus Jakarta Sans" typography.

- **Base Radius:** 16px is used for standard menu item images and cards.
- **Large Radius:** 24px is used for bottom sheets and large promotional banners.
- **Pill Radius:** Used exclusively for tags, filters, and primary buttons to distinguish them from structural content containers.

## Components

### Buttons & Interaction
- **Primary Button:** Pill-shaped, Primary Orange background, White text. High-elevation shadow on tap.
- **"Add" Button:** A signature component. White background with a thin `#FF6B35` border, featuring a prominent `+` icon. Positioned partially overlapping the food image for clear association.
- **Chips/Filters:** Rounded borders (8px) with a subtle grey stroke. Active state uses a light orange tint background with primary orange text.

### Menu Item Card
- **Structure:** Horizontal layout for list views. The left side contains title, price, and description. The right side contains the food image (fixed aspect ratio 1:1) with the "Add" button anchored at the bottom center of the image.
- **Dietary Icons:** 12px square icons with rounded corners (2px). Green for Veg, Red for Non-Veg, positioned top-left of the item title.

### Input Fields
- **Search Bar:** Fully rounded (pill), light grey background (`#F3F4F6`), centered placeholder with a search icon. No border.

### Visual Polish
- **Image Treatment:** All food photography must have a slight inner-glow or very subtle 0.5px border to ensure white plates don't bleed into the white background.
- **Dividers:** 1px hairline dividers using `#E5E7EB` to separate category sections.