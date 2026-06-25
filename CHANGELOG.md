# Changelog

All notable changes to this project will be documented in this file.

---

## [1.0.0] - 2026-06-25

This version introduces a complete user experience redesign for both desktop and mobile viewports, fixes all session-based regression bugs, and implements a unified design system.

### Added
- **Unified Responsive Layout**: Splitted desktop and mobile views dynamically using CSS media queries within `menu.html`.
- **Desktop Layout (Culinary Clarity)**:
  - Sticky header featuring branding, search input, and shopping cart badge.
  - Sticky left-hand vertical category navigation rail.
  - Clean 4-column card grid displaying menu items.
  - Floating bottom cart bar that appears dynamically when items are in the cart.
  - "Request Bill" action button placed in the sidebar footer.
- **Mobile Layout (Savor Mobile)**:
  - Sticky header with back button and search bar.
  - Collapsible category accordions with rotating chevrons.
  - Horizontal dish list cards containing Veg/Non-veg badges, name, price, and descriptions.
  - Floating "Menu" FAB and bottom navigation bar with Menu, Orders, and Cart tabs.
  - Floating "Request Bill" FAB positioned at the bottom left.
- **Automatic CSRF Token Injection**: Added a hidden `{% csrf_token %}` block in `menu.html` and `cart.html` templates to set the `csrftoken` cookie for all client-side async `POST` actions.
- **Robust Error Handling**: Added promise-based error handling to front-end cart calls, showing descriptive error toasts when actions are rejected (e.g. attempting to add items to cart post-bill request).

### Fixed
- **Add to Cart Silent Failures**: Restored `X-CSRFToken` request headers and cookie generation, resolving the `403 Forbidden` API failures.
- **Empty Cart Page**: Fixed the cart page showing empty by successfully persisting added items to the database instead of dropping requests due to CSRF issues.
- **Cart Redirection**: Updated the back button in `cart.html` to dynamically redirect customers back to their active restaurant menu instead of a hardcoded `/` route.
- **Session Locking after Bill Request**: Restored backend validation blocking cart additions after the bill is requested, and connected the front-end buttons to display "Bill Requested ✓" and turn disabled (green) upon activation.
