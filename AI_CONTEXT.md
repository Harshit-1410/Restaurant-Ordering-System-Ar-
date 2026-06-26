# AI Context Document

This document provides comprehensive context for AI assistants to understand and build on this codebase immediately.

**Live deployment**: `https://web-production-cac8d9.up.railway.app`

---

## 1. Project Overview

A Web-based Augmented Reality (AR) Restaurant Ordering System. Customers scan a table-specific QR code, browse a digital menu with AR previews, add items to a personal cart, place orders, and request a bill — all from their mobile browser. Kitchen staff see incoming orders in real time. Managers and cashiers handle billing through a dedicated, role-protected Billing Dashboard.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 4.2.30 |
| Real-Time Layer | Django Channels 4.3.2 + WebSockets |
| ASGI Server | Daphne 4.2.2 |
| Channel Layer | Redis (`channels_redis` 4.3.0) |
| Database | PostgreSQL 16 |
| DB Adapter | psycopg2-binary 2.9.12 |
| Environment Config | python-decouple 3.8 |
| Static Files | WhiteNoise 6.11.0 |
| DB URL Parsing | dj-database-url 3.0.1 |
| Image Handling | Pillow 11.2.1 |
| Frontend | HTML5, CSS3, Vanilla JavaScript (no framework) |
| AR Engine | Google `<model-viewer>` (Android/WebXR) + Apple AR Quick Look (`.usdz` on iOS) |

---

## 3. Directory Structure

```
ar-main/
├── core/                        # Django project config
│   ├── settings/
│   │   ├── base.py              # Shared settings
│   │   ├── dev.py               # DEBUG=True, local PostgreSQL
│   │   └── prod.py              # Railway: DATABASE_URL, REDIS_URL, HTTPS
│   ├── asgi.py                  # ASGI entry (Channels ProtocolTypeRouter)
│   └── urls.py                  # Root URL conf (ordering/, billing/, then restaurants catch-all)
├── restaurants/                 # Restaurant, Category, MenuItem models
│   ├── templates/restaurants/menu.html
│   └── views.py
├── ordering/                    # Cart, Table, TableSession, CustomerSession, Order
│   ├── models.py                # All ordering models (see §5)
│   ├── session.py               # Stateless QR-token → CustomerSession helpers
│   ├── consumers.py             # KitchenConsumer, OrderConsumer (WebSocket)
│   ├── routing.py               # WebSocket URL routes
│   ├── views.py                 # All ordering HTTP views
│   ├── admin.py                 # TableAdmin (with QR URL), TableSessionAdmin, etc.
│   └── templates/ordering/
│       ├── kitchen.html         # Real-time kitchen dashboard (grouped by table/guest)
│       ├── billing.html         # Simple unauthenticated billing view (legacy)
│       ├── cart.html
│       └── session_bill.html
├── billing/                     # Authenticated Billing Dashboard (separate app)
│   ├── models.py                # StaffProfile, Bill, Payment
│   ├── services.py              # Business logic: generate_bill, apply_discount, etc.
│   ├── views.py                 # All billing HTTP views
│   ├── decorators.py            # @billing_required, @role_required
│   ├── urls.py
│   ├── admin.py
│   ├── migrations/
│   └── templates/billing/
│       ├── base.html            # Dark sidebar layout + WebSocket
│       ├── login.html
│       ├── dashboard.html       # KPI cards + bill requests
│       ├── open_bills.html      # Active table session cards
│       ├── bill_detail.html     # Items, discount, payment, close
│       ├── history.html         # Filterable bill history table
│       ├── receipt.html         # Printable thermal-style receipt
│       └── reports.html         # Chart.js analytics
├── media/                       # Uploaded images + AR models (committed to git)
├── .env                         # Local secrets (git-ignored)
├── .env.example
├── requirements.txt
├── manage.py
├── railway.toml
└── build.sh
```

---

## 4. Settings Architecture

- **`base.py`**: INSTALLED_APPS (`restaurants`, `ordering`, `billing`), WhiteNoise, Redis channel layer, static/media paths, session engine.
- **`dev.py`**: `DEBUG=True`, `ALLOWED_HOSTS=['*']`, PostgreSQL from individual `DB_*` env vars.
- **`prod.py`**: `DEBUG=False`, `ALLOWED_HOSTS` from CSV env var, PostgreSQL from `DATABASE_URL`, Redis from `REDIS_URL`, `SECURE_SSL_REDIRECT=False` (Railway proxy handles SSL).

Default: `core.settings.dev`. Production: set `DJANGO_SETTINGS_MODULE=core.settings.prod`.

---

## 5. Database Models & Schema

### restaurants app
| Model | Key Fields |
|---|---|
| `Restaurant` | `name`, `slug`, `logo`, `is_active`, `address`, `phone`, `gst_number` |
| `Category` | `restaurant` FK, `name`, `image`, `is_active` |
| `MenuItem` | `category` FK, `name`, `description`, `price`, `image`, `ar_model_file` (.glb), `ar_model_usdz` (.usdz), `is_veg`, `is_available` |

### ordering app
| Model | Key Fields |
|---|---|
| `Table` | `restaurant` FK, `table_number`, `qr_token` (unique, `secrets.token_urlsafe(24)`), `is_active` |
| `TableSession` | `table` FK, `status` (open/paid/closed), `started_at`, `ended_at`, `bill_requested_at` |
| `CustomerSession` | `table_session` FK, `browser_uuid`, `created_at`, `last_seen` |
| `Cart` | `customer_session` OneToOne |
| `CartItem` | `cart` FK, `menu_item` FK, `quantity`, `notes` |
| `Order` | `customer_session` FK, `status` (pending/preparing/ready/served/cancelled), `total_amount` |
| `OrderItem` | `order` FK, `menu_item` FK, `quantity`, `unit_price`, `notes` |

### billing app
| Model | Key Fields |
|---|---|
| `StaffProfile` | `user` OneToOne, `restaurant` FK, `role` (owner/manager/cashier), `is_active` |
| `Bill` | `table_session` OneToOne, `restaurant` FK, `cashier` FK, `subtotal`, `tax_percentage`, `tax_amount`, `discount_type/value/amount/reason`, `round_off`, `grand_total`, `status` (draft/paid/void), `paid_at` |
| `Payment` | `bill` FK, `payment_method` (cash/upi/credit_card/debit_card), `amount`, `transaction_ref`, `received_by` FK |

**Schema relationships:**
```
Restaurant ──< Table ──< TableSession ──< CustomerSession ──< Order ──< OrderItem
                                  │                    └──── Cart ──< CartItem
                                  └── Bill (OneToOne) ──< Payment
                                  (StaffProfile ──> Restaurant + User)
```

---

## 6. Security Model

- **QR tokens**: Generated with `secrets.token_urlsafe(24)`. Never expose `table_id` in URLs.
- **Session binding**: `CustomerSession.id` stored in the Django server-side session cookie (`request.session['customer_session_id']`). Never trusted from URL parameters.
- **Billing auth**: `StaffProfile` role check via `@billing_required` and `@role_required` decorators. Kitchen dashboard is unauthenticated (internal use).
- **Bill immutability**: `services._guard_paid()` raises `ValueError` on any mutation attempt after `status == 'paid'`. Admin `has_delete_permission` returns `False` for `Bill` and `Payment`.

---

## 7. URL Routing

**Important**: `ordering/` and `billing/` prefixes must appear BEFORE `path('', include('restaurants.urls'))` in `core/urls.py`, because `restaurants/urls.py` contains `path('<slug:restaurant_slug>/', ...)` which would otherwise match any URL as a restaurant slug.

```
/admin/                                  → Django admin

/ordering/cart/add/                      → POST: add item to cart
/ordering/cart/data/                     → GET: cart count + subtotal (JSON)
/ordering/cart/remove/<cart_item_id>/    → POST: remove / decrement cart item
/ordering/cart/                          → GET: cart page
/ordering/place/                         → POST: place order
/ordering/bill/request/                  → POST: customer requests bill
/ordering/confirmation/<order_id>/       → GET: order confirmation page
/ordering/kitchen/<restaurant_id>/       → GET: kitchen dashboard (unauthenticated)
/ordering/billing/                       → GET: legacy billing view (unauthenticated)
/ordering/billing/close/<session_id>/    → POST: close table session (legacy)

/billing/                                → GET: dashboard (KPIs, bill requests) — redirects to login if not auth
/billing/login/                          → GET/POST: staff login
/billing/logout/                         → POST: staff logout
/billing/open/                           → GET: all active table sessions
/billing/bills/<session_id>/             → GET: bill detail (auto-generates Bill on first open)
/billing/bills/<id>/recalc/              → POST: refresh totals from current orders (JSON)
/billing/bills/<id>/discount/            → POST: apply discount (JSON)
/billing/bills/<id>/discount/remove/     → POST: remove discount (JSON)
/billing/bills/<id>/payment/             → POST: add a payment entry (JSON)
/billing/bills/<id>/payment/<pid>/delete/ → POST: delete a payment entry (JSON)
/billing/bills/<id>/close/               → POST: mark bill PAID + close TableSession (JSON)
/billing/bills/<id>/receipt/             → GET: printable receipt page
/billing/history/                        → GET: bill history with date/method/table/search filters
/billing/reports/                        → GET: analytics + Chart.js charts (owner/manager only)

/<restaurant-slug>/                      → GET: customer menu (restaurants app catch-all)
/<restaurant-slug>/?t=<qr_token>         → GET: menu with QR session join

/ws/kitchen/<restaurant_id>/             → WebSocket: kitchen + billing real-time events
/ws/order/<order_id>/                    → WebSocket: order status updates for customer
```

---

## 8. Key Application Flows

### QR Scan → Order Flow
1. Customer scans QR → `/<slug>/?t=<qr_token>`.
2. `ordering/session.py:join_table()` validates token → finds/creates `TableSession` → finds/creates `CustomerSession` → stores `CustomerSession.id` in Django session cookie.
3. Customer adds items → `POST /ordering/cart/add/` → `_get_or_create_cart(customer_session)`.
4. Customer places order → `POST /ordering/place/` → creates `Order` + `OrderItem` records → broadcasts `new_order` via WebSocket to `kitchen_{restaurant_id}` group.
5. Customer requests bill → `POST /ordering/bill/request/` → sets `bill_requested_at` → broadcasts `bill_requested`.

### Billing Flow (Authenticated)
1. Cashier logs in at `/billing/login/` (requires `StaffProfile`).
2. Dashboard shows KPIs + bill requests (live WebSocket updates).
3. Cashier opens `/billing/open/` → clicks table card → `/billing/bills/<session_id>/`.
4. `Bill` is auto-generated on first open (idempotent, `services.generate_bill()`).
5. Cashier applies optional discount → adds payment method(s) → clicks "Mark as Paid".
6. `services.close_bill()` → marks `Bill.status = 'paid'` → calls `TableSession.close(paid=True)` → broadcasts `table_closed` WebSocket event.
7. Future QR scans create a fresh `TableSession`.

---

## 9. session.py Reference

`ordering/session.py` — imported by both `ordering/views.py` and `restaurants/views.py`:

| Function | Purpose |
|---|---|
| `get_or_create_browser_uuid(request)` | Returns a stable random UUID stored in Django session |
| `join_table(request, qr_token)` | Validates token → creates/reuses `TableSession` + `CustomerSession` |
| `get_active_customer_session(request)` | Looks up the `CustomerSession` from Django session; returns None if closed |

---

## 10. services.py Reference (billing)

`billing/services.py` — all business logic; views are thin wrappers:

| Function | Purpose |
|---|---|
| `calculate_totals(bill)` | Computes subtotal, discount, tax, round-off, grand_total. Does NOT save. |
| `generate_bill(table_session, cashier)` | Creates Draft Bill (idempotent) |
| `recalculate_bill(bill)` | Refreshes all totals and saves |
| `apply_discount(bill, type, value, reason, user)` | Applies/replaces discount with audit trail |
| `remove_discount(bill)` | Clears discount fields |
| `add_payment(bill, method, amount, ref, user)` | Records a Payment row |
| `delete_payment(payment)` | Removes a Payment (draft bills only) |
| `close_bill(bill)` | Marks PAID, closes TableSession, broadcasts WebSocket |
| `today_stats(restaurant)` | KPI dict for dashboard |
| `revenue_last_n_days(restaurant, n)` | List of `{date, revenue}` for charts |
| `payment_method_breakdown(restaurant, days)` | `{labels, values}` for doughnut chart |
| `top_items(restaurant, limit, days)` | Top items by quantity sold |

---

## 11. WebSocket Events

All events broadcast to `kitchen_{restaurant_id}` group:

| Event `type` | Payload | Consumers |
|---|---|---|
| `new_order` | `order_id`, `table`, `customer_session_id`, `items` | Kitchen, Billing dashboard |
| `order_update` | `order_id`, `status` | Customer confirmation page |
| `bill_requested` | `session_id`, `table` | Kitchen, Billing dashboard |
| `table_closed` | `session_id`, `table` | Kitchen, Billing open bills |

---

## 12. Deployment (Railway)

| Phase | Command |
|---|---|
| Build | `bash build.sh` → pip install + collectstatic |
| Start | `python manage.py migrate && daphne -b 0.0.0.0 -p $PORT core.asgi:application` |

**Required env vars**: `DJANGO_SETTINGS_MODULE=core.settings.prod`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`.

**Media files**: AR models (`.glb`, `.usdz`) and food images are committed directly to the git repo under `media/` and served via Django's `serve()` view. No external cloud storage needed.

---

## 13. Creating Billing Staff (Production)

After deploying, open a Django shell on Railway:

```bash
railway run python3 manage.py shell
```

Then create a `StaffProfile` for the superuser:

```python
from django.contrib.auth.models import User
from restaurants.models import Restaurant
from billing.models import StaffProfile

user = User.objects.get(username='your_superuser_username')
restaurant = Restaurant.objects.get(slug='your-restaurant-slug')
StaffProfile.objects.create(user=user, restaurant=restaurant, role='owner')
exit()
```

Then log in at `/billing/login/`.

Alternatively, use **Django Admin → Billing → Staff Profiles → Add** — no shell required.

---

## 14. Adding a New Restaurant (Production Checklist)

Follow these steps in order every time a new restaurant is set up.

### Step 1 — Create the Restaurant in Django Admin
1. Go to `/admin/restaurants/restaurant/add/`.
2. Fill in: **Name**, **Slug** (URL-safe, e.g. `my-cafe`), **Logo**, **Address**, **Phone**, **GST Number**.
3. Tick **Is active**.
4. Save. Note the `restaurant_id` from the URL (e.g. `/admin/restaurants/restaurant/**3**/change/`).

### Step 2 — Add Categories and Menu Items
1. Go to `/admin/restaurants/category/add/` → set Restaurant + Name + Image.
2. Go to `/admin/restaurants/menuitem/add/` → fill Category, Name, Price, Image.
3. For AR: upload `.glb` (Android) and `.usdz` (iOS) files. After saving, commit the new files:
   ```bash
   git add media/
   git commit -m "chore: add AR models for <restaurant>"
   git push origin main
   ```

### Step 3 — Create Tables and QR Codes
1. Go to `/admin/ordering/table/add/`.
2. Set **Restaurant**, **Table Number** (e.g. `1`, `2`, `3`). Leave **QR Token** blank — it is auto-generated.
3. Tick **Is active**. Save.
4. Back in the Table list, copy the **QR URL (full)** field for each table (it is an absolute URL like `https://web-production-cac8d9.up.railway.app/my-cafe/?t=<token>`).
5. Paste each URL into a QR code generator (e.g. [qr-code-generator.com](https://www.qr-code-generator.com)) and print/laminate for each table.

### Step 4 — Create a Staff Profile for the Cashier
```bash
railway run python3 manage.py shell
```
```python
from django.contrib.auth.models import User
from restaurants.models import Restaurant
from billing.models import StaffProfile

# Create a login for the cashier if they don't have one yet
user = User.objects.create_user(username='cashier1', password='securepassword')
restaurant = Restaurant.objects.get(slug='my-cafe')
StaffProfile.objects.create(user=user, restaurant=restaurant, role='cashier')
exit()
```

### Step 5 — Verify
| Check | URL |
|---|---|
| Menu visible | `https://…/my-cafe/?t=<any_table_token>` |
| Kitchen dashboard | `https://…/ordering/kitchen/<restaurant_id>/` |
| Billing dashboard | `https://…/billing/` (log in as cashier) |
