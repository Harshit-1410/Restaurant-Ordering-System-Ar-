# Changelog

All notable changes to this project are documented here.

---

## [1.3.0] — 2026-06-26

### Added — Authenticated Billing Dashboard

A completely separate `billing` Django app with role-based authentication, full POS-style UI, and analytics.

#### Authentication & Roles
- **`StaffProfile` model**: Links `User` to a `Restaurant` with a role (`owner`, `manager`, `cashier`).
- **`@billing_required` decorator**: Blocks unauthenticated users and users without a `StaffProfile`.
- **`@role_required(['owner', 'manager'])` decorator**: Restricts reports page to management roles.
- Login page at `/billing/login/` with a clean POS-style dark UI.

#### Models (`billing/models.py`)
- **`Bill`**: One per `TableSession` (OneToOneField). Stores `subtotal`, `tax_percentage`, `tax_amount`, `discount_type/value/amount/reason/by/at`, `service_charge`, `round_off`, `grand_total`, `status` (draft/paid/void), `paid_at`. Auto-generates bill number (`BILL-YYYYMMDD-NNNN`). Immutable after payment.
- **`Payment`**: One or more per `Bill` (split-payment support). Stores `payment_method` (cash/upi/credit_card/debit_card), `amount`, `transaction_ref`, `received_by`.

#### Services (`billing/services.py`)
All business logic lives here — views are thin wrappers:
- `calculate_totals(bill)` — computes all amounts without saving.
- `generate_bill(table_session, cashier)` — idempotent draft bill creation.
- `recalculate_bill(bill)` — refreshes totals from current orders.
- `apply_discount(bill, ...)` / `remove_discount(bill)` — with full audit trail.
- `add_payment(bill, ...)` / `delete_payment(payment)`.
- `close_bill(bill)` — marks PAID, calls `TableSession.close(paid=True)`, broadcasts `table_closed` WebSocket.
- `today_stats()`, `revenue_last_n_days()`, `payment_method_breakdown()`, `top_items()` — analytics helpers.

#### Pages & Views
| URL | Page |
|---|---|
| `/billing/` | Dashboard — KPI cards, bill requests, recent bills |
| `/billing/open/` | Open Tables — color-coded cards (green/orange/red by wait time) |
| `/billing/bills/<session_id>/` | Bill Detail — items by guest, sticky summary, discount & payment |
| `/billing/bills/<id>/receipt/` | Printable receipt (thermal layout + print CSS) |
| `/billing/history/` | Bill history — filters by date/method/table/bill number |
| `/billing/reports/` | Analytics — Chart.js revenue trend + payment distribution |

#### Admin
- `Bill` and `Payment` admin have `has_delete_permission = False` (bills are immutable).
- `StaffProfile` admin for managing staff roles.

### Fixed
- **URL routing 404**: `path('billing/', ...)` was placed after `path('', include('restaurants.urls'))` in `core/urls.py`. The slug pattern `<slug:restaurant_slug>/` was matching `/billing/` as a restaurant slug and returning 404. Fixed by moving `ordering/` and `billing/` URL includes before the restaurants catch-all.

---

## [1.2.0] — 2026-06-25

### Added — Secure Multi-Table QR Ordering System

Complete architectural redesign of the table session and ordering models for security and multi-customer support.

#### New Models
- **`Table`**: Physical table with a `qr_token` generated via `secrets.token_urlsafe(24)`. Never exposes table ID in URLs. Includes `qr_menu_url(request)` to build absolute URLs for QR generators.
- **`CustomerSession`**: One per browser/device per `TableSession`. Linked via a `browser_uuid` stored server-side in Django's session cookie — never trusted from URL parameters.

#### Refactored Models
- **`TableSession`**: Now links to `Table` (FK). `status` replaces `is_active`/`is_paid`. `started_at` replaces `created_at`. `ended_at` replaces `closed_at`. `orders` property aggregates all orders through `CustomerSession`. `close(paid=True)` method sets status and `ended_at`.
- **`Cart`**: Now linked to `CustomerSession` (OneToOne) instead of `TableSession`.
- **`Order`**: Now linked to `CustomerSession` (FK) instead of `TableSession` directly. `table_session` and `restaurant` exposed as properties.

#### New Module: `ordering/session.py`
Centralizes all session logic to prevent circular imports:
- `get_or_create_browser_uuid(request)` — stable random UUID per browser session.
- `join_table(request, qr_token)` — validates QR token, finds/creates `TableSession` and `CustomerSession`, binds to Django session.
- `get_active_customer_session(request)` — retrieves active `CustomerSession` from server-side session.

#### Migrations
- `0003_add_table_and_customersession` — adds nullable new fields/models.
- `0004_data_migration` — data migration: creates `Table` per restaurant/table_number pair, creates legacy `CustomerSession` per existing session, re-links `Cart`s and `Order`s.
- `0005_finalize_schema` — makes FKs non-nullable, removes legacy columns.

#### Updated Views & Templates
- `ordering/views.py`: All views use `get_active_customer_session(request)` for session validation.
- `restaurants/views.py`: `menu` view handles `?t=<qr_token>` parameter, calls `join_table()`.
- `ordering/admin.py`: `TableAdmin` with QR URL generation (absolute URL using `request.build_absolute_uri()`), `rotate_qr_token` admin action.
- `kitchen.html`: Redesigned to show orders grouped by table and then by guest/CustomerSession.
- `menu.html`: Shows session status banners (QR error, browse-only, active table).

---

## [1.1.0] — 2026-06-25

### Added — Production Infrastructure

- **PostgreSQL**: Migrated from SQLite3. Local dev uses individual `DB_*` env vars; production uses Railway's `DATABASE_URL`.
- **Redis Channel Layer**: `channels_redis.core.RedisChannelLayer` replacing in-memory layer.
- **Dev/Prod Settings Split**: `core/settings/base.py`, `dev.py`, `prod.py` with `python-decouple`.
- **WhiteNoise**: Static files served directly from Daphne without nginx.
- **Railway Deployment**: `railway.toml`, `build.sh`. Live at `https://web-production-cac8d9.up.railway.app`.
- **Git-committed media**: AR models and food images committed to `media/` dir, served via Django's `serve()` view. Eliminates dependency on ephemeral Railway filesystem and external cloud storage.

### Fixed
- `STATIC_URL` missing leading slash → Django admin CSS broken at nested paths.
- `ASGIStaticFilesHandler` removed from `asgi.py` → was blocking WhiteNoise in production.
- `SECURE_SSL_REDIRECT=False` → Railway proxy handles SSL termination; `True` caused redirect loops.
- `migrate` moved from `build.sh` to `startCommand` → database unavailable during image build.

---

## [1.0.0] — 2026-06-25

### Added — Initial Release

- **Dual responsive layout**: Desktop ("Culinary Clarity") with sticky sidebar + 4-column grid. Mobile ("Savor Mobile") with collapsible accordions + bottom navigation.
- **AR integration**: iOS AR Quick Look (`.usdz`) and Android Scene Viewer (`<model-viewer>`, `.glb`).
- **Cart system**: Session-based cart with real-time badge updates and floating cart bar.
- **Order placement**: Cart → Order flow with WebSocket notification to kitchen.
- **Kitchen dashboard**: Real-time order cards with status updates.
- **Bill request**: Customer-triggered bill request locks session; notifies kitchen via WebSocket.
- **Veg/Non-veg badges**: Dietary indicators on menu items.
