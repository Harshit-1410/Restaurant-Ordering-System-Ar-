---
name: Culinary Clarity
colors:
  surface: '#f9f9ff'
  surface-dim: '#d3daef'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3ff'
  surface-container: '#e9edff'
  surface-container-high: '#e1e8fd'
  surface-container-highest: '#dce2f7'
  on-surface: '#141b2b'
  on-surface-variant: '#584237'
  inverse-surface: '#293040'
  inverse-on-surface: '#edf0ff'
  outline: '#8c7164'
  outline-variant: '#e0c0b1'
  surface-tint: '#9d4300'
  primary: '#9d4300'
  on-primary: '#ffffff'
  primary-container: '#f97316'
  on-primary-container: '#582200'
  inverse-primary: '#ffb690'
  secondary: '#006e2f'
  on-secondary: '#ffffff'
  secondary-container: '#6bff8f'
  on-secondary-container: '#007432'
  tertiary: '#006398'
  on-tertiary: '#ffffff'
  tertiary-container: '#00a2f4'
  on-tertiary-container: '#003554'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdbca'
  primary-fixed-dim: '#ffb690'
  on-primary-fixed: '#341100'
  on-primary-fixed-variant: '#783200'
  secondary-fixed: '#6bff8f'
  secondary-fixed-dim: '#4ae176'
  on-secondary-fixed: '#002109'
  on-secondary-fixed-variant: '#005321'
  tertiary-fixed: '#cde5ff'
  tertiary-fixed-dim: '#93ccff'
  on-tertiary-fixed: '#001d32'
  on-tertiary-fixed-variant: '#004b74'
  background: '#f9f9ff'
  on-background: '#141b2b'
  surface-variant: '#dce2f7'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-max-width: 1280px
  gutter: 24px
  margin-desktop: 40px
  margin-mobile: 16px
  card-padding: 24px
  section-gap: 48px
---

## Brand & Style

The brand personality is professional, transparent, and appetizing. It targets a modern audience that values efficiency and visual clarity in their dining experience. The UI evokes a sense of freshness and reliability through a balanced use of white space and high-quality imagery.

The design style is **Minimalism** blended with **Modern Corporate** sensibilities. It prioritizes the food as the hero of the interface, using a clean, card-based layout and generous whitespace to reduce cognitive load. Subtle depth and soft shadows are used to create a layered, tactile feel that makes interactive elements feel "clickable" and physically present.

## Colors

The color palette is built on a foundation of absolute white to signify cleanliness and highlight food photography. 

- **Primary (Orange - #F97316):** Used sparingly for accents, primary calls to action, and highlights to stimulate appetite and draw attention to key interactive areas.
- **Secondary (Vibrant Green - #22C55E):** Reserved for status indicators, "Most Liked" badges, and nutritional affirmations (e.g., "Vegetarian").
- **Neutral (Charcoal - #111827):** Employed for typography and iconography to ensure high legibility and a grounded, professional feel.
- **Surface:** A very light grey is used for subtle background containers to separate content areas without breaking the minimalist aesthetic.

## Typography

This design system utilizes **Geist** for its technical precision and modern, neutral character. The typography scale is designed to create a clear information hierarchy, allowing users to scan dish names and prices effortlessly.

Headlines use semi-bold and bold weights with slightly tightened letter spacing for a more compact, editorial look. Body text maintains a generous line height to ensure readability in menu descriptions. Labels and badges use a slightly heavier weight to remain legible at smaller sizes.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy on desktop, transitioning to a fluid single-column layout on mobile. The system is built on an 8px base unit.

- **Desktop (1280px+):** A 12-column grid with a left-hand navigation rail. Food cards typically span 3 or 4 columns depending on the category prominence.
- **Tablet (768px - 1024px):** Grid shifts to 8 columns. Sidebar navigation may collapse into a top-scrollable bar or a hamburger menu.
- **Mobile (<768px):** Single column for list items or 2-column for compact grid items. Margins reduce to 16px to maximize screen real estate for dish imagery.

Whitespace is used intentionally as a separator between categories, preventing the menu from feeling cluttered even with high item counts.

## Elevation & Depth

Visual hierarchy is achieved through **Tonal Layers** and **Ambient Shadows**.

1.  **Level 0 (Background):** Pure white (#FFFFFF).
2.  **Level 1 (Cards/Containers):** Subtle low-opacity shadows (Blur: 20px, Y: 4px, Color: Neutral at 5% opacity) provide separation from the background.
3.  **Level 2 (Interactive/Floating):** Higher elevation shadows for active states, cart drawers, or modals (Blur: 40px, Y: 12px, Color: Neutral at 10% opacity).

The design avoids heavy borders, instead using light grey strokes (#F3F4F6) only when necessary to define boundaries on white backgrounds.

## Shapes

The shape language is defined by a consistent, generous roundedness to convey friendliness and safety.

- **Standard Elements:** Buttons, input fields, and small cards use a radius of **8px (0.5rem)**.
- **Menu Cards:** Main dish cards use a larger radius of **16px (1rem)** to create a soft, premium container for food photography.
- **Badges/Chips:** Utilize a **pill-shaped** (full radius) design to distinguish them from functional UI components.

## Components

### Buttons
- **Primary:** Solid Orange (#F97316) with white text. Rounded corners (8px). 
- **Secondary:** Ghost style with charcoal border or light grey background.
- **Add to Cart (+):** Circular buttons with a soft shadow to indicate primary interactivity within a card.

### Cards
- Dish cards must feature a 1:1 or 4:3 aspect ratio image container.
- Use a slight background tint (#F9FAFB) for the text area of the card to subtly separate it from the image.

### Badges & Chips
- **Status Badges:** Used for "Best Seller" or "Vegan." Vibrant Green (#22C55E) background with white text, pill-shaped.
- **Filter Chips:** Light grey background, turning Orange or Charcoal when active.

### Input Fields
- Search bars should be prominent with a soft 8px radius and a subtle search icon. Use a light border (#E5E7EB) that darkens on focus.

### Lists (Navigation)
- Left-hand navigation uses high-contrast typography. The active state is indicated by a vertical orange bar (4px width) to the left of the category name.