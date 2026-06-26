# Roadmap & TODO

---

## ✅ Completed

### Infrastructure
- [x] PostgreSQL migration (from SQLite3)
- [x] Redis-backed channel layer
- [x] Dev/prod settings split with python-decouple
- [x] WhiteNoise static file serving
- [x] Railway deployment (live at `https://web-production-cac8d9.up.railway.app`)
- [x] Git-committed media strategy (AR models + food images in repo, served via `serve()`)

### Security & Architecture
- [x] **Secure QR Table System**: Replaced `?table=N` URLs with `?t=<qr_token>` (cryptographic tokens via `secrets.token_urlsafe(24)`)
- [x] **`CustomerSession` model**: One session per browser/device per table — multiple customers at one table each get their own cart and orders
- [x] **Server-side session binding**: `CustomerSession.id` stored in Django session cookie, never trusted from URL parameters
- [x] **`ordering/session.py`**: Centralized, stateless session helpers (`join_table`, `get_active_customer_session`)
- [x] **Admin QR URL**: `TableAdmin` generates absolute URLs for QR generators using `request.build_absolute_uri()`
- [x] **`rotate_qr_token` admin action**: Invalidates old QR codes and issues new ones

### Billing Dashboard
- [x] **Authenticated Billing Dashboard** at `/billing/` (separate Django app)
- [x] **Role-based auth**: `StaffProfile` model with roles Owner / Manager / Cashier
- [x] **`@billing_required` / `@role_required` decorators**
- [x] **`Bill` model**: Immutable after payment, auto-generated bill numbers
- [x] **`Payment` model**: Split-payment support (Cash, UPI, Credit Card, Debit Card)
- [x] **`billing/services.py`**: Clean service layer (generate_bill, apply_discount, add_payment, close_bill, analytics)
- [x] **Dashboard KPIs**: Today's Revenue, Open Bills, Tables Occupied, Waiting for Payment, etc.
- [x] **Open Bills page**: Color-coded table cards (green/orange/red by elapsed time)
- [x] **Bill Detail page**: Items grouped by guest, sticky billing summary, discount, multi-payment panel
- [x] **Printable Receipt**: Thermal-style layout with print CSS
- [x] **Bill History**: Filterable by date, method, table, bill number
- [x] **Reports & Analytics**: Chart.js revenue trend and payment method charts (owner/manager only)
- [x] **Live WebSocket updates**: Bill requests trigger toast notifications; table closures refresh open bills

---

## 🔴 High Priority

### Authentication Hardening
- [ ] **Kitchen dashboard auth**: `/ordering/kitchen/<id>/` is currently unauthenticated. Add `@login_required` or a PIN-based access system for kitchen staff.
- [ ] **Session expiry**: Implement a Django management command + Railway cron to auto-close `TableSession` records that have been open for more than 4 hours without activity.

### Billing Enhancements
- [ ] **Tax configuration UI**: Allow restaurant owner to configure GST percentage from the admin or settings page (currently hardcoded at 5% default).
- [ ] **Service charge configuration**: Allow per-restaurant service charge percentage to be set and auto-applied.
- [ ] **Discount approval workflow**: Notify manager when cashier applies a discount over a threshold (e.g., >20%).
- [ ] **Bill adjustment records**: For corrections after payment, create an `Adjustment` model instead of modifying the paid `Bill`.

### Performance
- [ ] **Database indexes**: Add `db_index=True` on `MenuItem.is_available`, `Category.is_active`, `Restaurant.slug` for faster menu page queries.
- [ ] **Select related**: Audit all views for N+1 query issues, especially the kitchen and billing dashboards.

---

## 🟡 Medium Priority

### Customer Experience
- [ ] **Order history tab**: Show customer's own orders for the current session in a mobile bottom nav tab (currently only visible on the confirmation page).
- [ ] **Order status on menu page**: Show live order status badge on the menu after placing an order, so customer doesn't need to stay on confirmation page.

### Kitchen Dashboard
- [ ] **Sound alerts**: Audio notification when a new order arrives or bill is requested.
- [ ] **Print KOT**: "Print Kitchen Order Ticket" button on each table card.

### Billing Enhancements
- [ ] **PDF receipt download**: Integrate WeasyPrint or a headless Chrome solution to generate downloadable PDF receipts.
- [ ] **Cashier performance report**: Per-cashier breakdown of bills processed, average discount given, total revenue handled.
- [ ] **Shift summary**: End-of-shift report showing all bills, total cash/UPI/card collected.

### Testing
- [ ] **Unit tests**: Add coverage for `ordering/session.py`, `billing/services.py`, and key view endpoints.
- [ ] **End-to-end tests**: Playwright tests for the QR scan → order → bill → close flow.

---

## 🟢 Nice to Have

### AR Enhancements
- [ ] **Ambient lighting controls**: Add lighting and rotation speed settings in `<model-viewer>`.
- [ ] **AR model upload preview**: Show a 3D preview of `.glb` files in the Django admin before saving.

### Multi-Restaurant
- [ ] **Restaurant landing page**: A homepage listing all active restaurants (currently requires knowing the slug).
- [ ] **Per-restaurant billing config**: Each restaurant can set its own tax %, service charge %, and receipt footer message.

### Operations
- [ ] **QR code image download**: Admin action to generate and download a printable QR code PNG for each table.
- [ ] **Rate limiting**: Add throttling on `cart/add/` and `place/` endpoints using `django-ratelimit`.
