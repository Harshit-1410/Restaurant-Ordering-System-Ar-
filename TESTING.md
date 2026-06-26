# Testing Guide

Manual test procedures for all major flows in the AR Restaurant Ordering System.

---

## Automated Tests

Run the Django test suite for all three apps:
```bash
python3 manage.py test ordering restaurants billing
```

---

## Manual Test Setup

Start the dev server:
```bash
brew services start postgresql@16
brew services start redis
python3 manage.py runserver
```

Ensure you have:
- A `Restaurant` created in admin (e.g., slug `art-of-kitchen`, id `1`)
- At least one `Category` and `MenuItem` with an image
- At least one `Table` created in admin for that restaurant
- A `StaffProfile` linked to your superuser for billing tests

---

## Module 1: Menu & AR

### Test 1.1 — QR Token Session Join
- **Steps**:
  1. Go to Django Admin → Ordering → Tables. Click a table. Copy the "QR URL (full)" value.
  2. Open that URL in a browser (e.g., `http://127.0.0.1:8000/art-of-kitchen/?t=<token>`).
- **Expected**: Menu loads with a green banner: "Ordering at Table X". A `TableSession` and `CustomerSession` are created in the database.

### Test 1.2 — Invalid QR Token
- **Steps**: Visit `http://127.0.0.1:8000/art-of-kitchen/?t=fakeinvalidtoken`.
- **Expected**: Menu loads with a red banner: "Invalid QR code". Cart and order buttons are disabled.

### Test 1.3 — Browse-Only Mode (no token)
- **Steps**: Visit `http://127.0.0.1:8000/art-of-kitchen/` without a `?t=` parameter.
- **Expected**: Menu loads with a blue banner: "Scan the QR code at your table to order". Cart buttons are disabled.

### Test 1.4 — Category Navigation & Search
- **Steps**:
  1. Click category names in the sidebar (desktop) or tap accordions (mobile).
  2. Type in the search bar.
- **Expected**: Items filter correctly. Accordions collapse/expand with chevron animation.

### Test 1.5 — AR Button
- **Steps**:
  1. Open a menu item that has both `.glb` and `.usdz` files uploaded.
  2. Click "View on Your Table".
  3. On iOS Safari: AR Quick Look should launch.
  4. On Android Chrome: `<model-viewer>` should overlay with AR option.
- **Expected**: AR launches on the respective platform. Items without AR models should not show the button.

---

## Module 2: Cart & Ordering

### Test 2.1 — Add to Cart
- **Steps**:
  1. Scan a valid QR (or use `?t=<token>` URL). Click a menu item. Click "+ Add to Cart".
- **Expected**: Toast "Added [item] to cart". Cart badge count increments. Floating cart bar appears.

### Test 2.2 — Cart Management
- **Steps**:
  1. Navigate to `/ordering/cart/`.
  2. Increase/decrease quantities. Remove an item.
- **Expected**: Totals update dynamically. Removing the last item empties the cart.

### Test 2.3 — Place Order
- **Steps**:
  1. Add items to cart. Click "Place Order".
- **Expected**: Redirects to `/ordering/confirmation/<id>/`. Order appears in the kitchen dashboard.

### Test 2.4 — Kitchen Real-Time Update
- **Steps**:
  1. Open the kitchen dashboard at `/ordering/kitchen/1/` in a second tab.
  2. Place an order from the menu in the first tab.
- **Expected**: New order card appears in the kitchen tab instantly (WebSocket), without page refresh.

### Test 2.5 — Order Status Update
- **Steps**:
  1. On the customer confirmation page, note the order status ("Pending").
  2. In the kitchen dashboard, change the order status to "Preparing".
- **Expected**: Customer confirmation page updates status in real time via WebSocket.

### Test 2.6 — Multi-Customer at Same Table
- **Steps**:
  1. Open the same QR URL in two different browsers (or incognito).
  2. Add different items from each browser and place orders.
- **Expected**: Kitchen dashboard shows both customers' orders under the same table section, in separate guest columns.

---

## Module 3: Bill Request

### Test 3.1 — Request Bill
- **Steps**:
  1. After placing an order, click "Request Bill" (sidebar on desktop, FAB on mobile).
- **Expected**: Button turns green, shows "Bill Requested ✓", becomes disabled. Kitchen dashboard shows a bill request notification.

### Test 3.2 — Session Lock After Bill Request
- **Steps**:
  1. After requesting the bill, try to add another item to the cart.
- **Expected**: Returns error toast "Cannot add items after requesting the bill." (400 response).

---

## Module 4: Billing Dashboard

### Test 4.1 — Login & Role Check
- **Steps**:
  1. Go to `/billing/login/`.
  2. Log in with a user that has a `StaffProfile`.
  3. Log in with a regular user (no `StaffProfile`).
- **Expected**: Staff user is redirected to `/billing/`. Regular user sees error "You are not registered as billing staff."

### Test 4.2 — Open Tables Page
- **Steps**:
  1. Go to `/billing/open/`.
- **Expected**: Cards show all tables with active `TableSession`s. Color coded: green (< 30 min), orange (30–60 min), red (> 60 min). Tables with bill requests show orange "Bill Requested" badge.

### Test 4.3 — Auto-Generate Bill
- **Steps**:
  1. Click "View Bill" on a table card.
- **Expected**: Bill is created automatically. Bill number (e.g., `BILL-20260626-0001`) appears. Subtotal matches the sum of all non-cancelled orders for the table.

### Test 4.4 — Apply Discount
- **Steps**:
  1. On the bill detail page, expand "Discount". Select "% Percentage". Enter `10`. Enter reason "Regular customer". Click "Apply Discount".
- **Expected**: Toast confirms discount applied. Summary panel updates: discount row appears, grand total decreases. Tax is calculated on the post-discount amount.

### Test 4.5 — Record Payment
- **Steps**:
  1. Select "Cash" as payment method. Enter an amount. Click "Add Payment".
- **Expected**: Payment tag appears in the "Payments Recorded" section. "Amount Due" decreases.

### Test 4.6 — Split Payment
- **Steps**:
  1. Add a Cash payment for part of the total. Add a UPI payment for the remainder.
- **Expected**: Both payments listed. "Amount Due" shows ₹0.00.

### Test 4.7 — Close Bill
- **Steps**:
  1. With amount due at ₹0, click "Mark as Paid & Close Table". Confirm in modal.
- **Expected**: Toast "Bill marked as PAID ✓". Redirects to open bills page. Table no longer appears in open bills. `TableSession.status` is now `paid` in the database.

### Test 4.8 — Bill Immutability
- **Steps**:
  1. Visit the bill detail page of a paid bill.
- **Expected**: Green banner "Bill paid on [date]". Discount, payment, and close sections are hidden. No mutation is possible.

### Test 4.9 — Printable Receipt
- **Steps**:
  1. Click "🖨️ Print Receipt" on a paid bill.
- **Expected**: Receipt page opens in a new tab with thermal-style white layout. Browser print dialog works. Sidebar and navigation are hidden in print mode.

### Test 4.10 — Bill History Filters
- **Steps**:
  1. Go to `/billing/history/`. Filter by "Today". Filter by payment method "Cash". Search by bill number.
- **Expected**: Table shows only matching bills. Filters combine correctly.

### Test 4.11 — Reports (Owner/Manager Only)
- **Steps**:
  1. Log in as an owner. Go to `/billing/reports/`.
  2. Log in as a cashier. Try to access `/billing/reports/`.
- **Expected**: Owner sees Chart.js charts and top items table. Cashier receives 403 Forbidden.

---

## Module 5: WebSocket Connection

### Test 5.1 — Live Connection Indicator
- **Steps**:
  1. Open the billing dashboard.
  2. Disconnect the internet briefly.
- **Expected**: The green live dot in the top bar turns red and label shows "Reconnecting…". Reconnects automatically when internet restores.

### Test 5.2 — Bill Request Toast
- **Steps**:
  1. Open the billing dashboard.
  2. From a customer browser, click "Request Bill".
- **Expected**: Yellow toast appears on the billing dashboard: "🧾 Bill Requested — Table X".
