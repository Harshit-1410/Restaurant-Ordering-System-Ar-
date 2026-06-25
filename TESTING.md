# Testing Guide

This document outlines the manual and automated testing cases and procedures for the AR Ordering System.

---

## 1. Automated Backend Test
To run the automated endpoint validation checks for sessions, cart operations, order placements, and bill request blockages:
```bash
./.venv/bin/python3 /Users/harshitprajapati/.gemini/antigravity-ide/brain/15e96b20-0ee1-4ae5-999a-916924bdd840/scratch/qa_backend_test.py
```

---

## 2. Manual Test Procedures

### Test Case 1: Restaurant Loading & Menu Browsing
- **Steps**:
  1. Open a web browser and navigate to `http://127.0.0.1:8000/art-of-kitchen/?table=1`.
  2. Verify that the restaurant name "art of kitchen" renders in the header.
  3. Verify that the category headers ("American", "Indian", etc.) are displayed.
- **Expected Outcome**: Page loads without errors, showing the correct restaurant logo and available categories.

### Test Case 2: Category Switching & Search
- **Steps**:
  1. **Desktop**: Click on the categories in the sidebar. Verify the active layout shifts and displays items in that category.
  2. **Mobile**: Collapse and expand category accordions. Verify that the chevron arrow rotates.
  3. In the search bar, type "burger". Verify only the "Burger & Fries" card remains visible.
  4. Clear the search input. Verify all dishes reappear.
- **Expected Outcome**: Category switching changes active lists, and search filters items in real time.

### Test Case 3: Detail Modal & Cart Additions
- **Steps**:
  1. Click on the "Burger & Fries" product card.
  2. Verify the product details modal opens, displaying veg/non-veg tags, description, and price.
  3. Click the `+` button in the modal to increase quantity to `2`.
  4. Click "Add to Cart".
- **Expected Outcome**: Modal closes, a success toast "Added Burger & Fries to cart!" appears, the shopping cart badge count updates to `2`, and the desktop floating cart bar appears at the bottom.

### Test Case 4: Cart Management & Place Order
- **Steps**:
  1. Click "View Cart" in the floating cart bar (or the cart icon in the header) to navigate to `/ordering/cart/`.
  2. Verify "Burger & Fries" is listed with quantity `2` and correct subtotal/total.
  3. Click the `+` button to increase quantity to `3`. Verify total changes dynamically.
  4. Click "Place Order".
- **Expected Outcome**: The button immediately disables, displays "Placing order...", and redirects to the confirmation page displaying "Order #<id> Placed".

### Test Case 5: Bill Request & Session Lock
- **Steps**:
  1. Click the back arrow from the order confirmation page to return to `/art-of-kitchen/`.
  2. Click the "Request Bill" button (sidebar on desktop, bottom-left FAB on mobile).
  3. Verify the button background changes to green, displays "Bill Requested ✓", and becomes disabled.
  4. Click on the "Burger & Fries" card to open the modal, and try to click "Add to Cart".
- **Expected Outcome**: The request succeeds. Attempting to add items to the cart is blocked, showing a toast "Cannot add items after requesting the bill."

### Test Case 6: Augmented Reality (AR) Button
- **Steps**:
  1. **With Model**: Ensure an item has AR models uploaded. Open the modal and verify the "View on Your Table" (AR) button is visible.
  2. **Without Model**: Ensure an item has no AR models. Verify the button is hidden.
  3. **iOS Safari**: Tap the button. Apple AR Quick Look should launch.
  4. **Android Chrome**: Tap the button. Google Model Viewer should open, presenting the 3D model with an option to enter AR.
- **Expected Outcome**: Button renders conditionally and launches the respective native platform viewer.
