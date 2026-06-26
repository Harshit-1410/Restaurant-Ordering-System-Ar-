# Architecture Documentation

---

## 1. Application Architecture Overview

```
ar-main/
  ├── restaurants/   Menu & item data (read-mostly)
  ├── ordering/      Session, cart, orders, kitchen, WebSocket
  └── billing/       Authenticated billing dashboard, bills, payments, analytics
```

The three Django apps are fully separate with clear dependency direction:
- `restaurants` has no dependencies on other apps
- `ordering` depends on `restaurants` (MenuItem FKs)
- `billing` depends on `ordering` (TableSession FK) and `restaurants` (Restaurant FK)

### billing app — Template Component Hierarchy

```
billing/templates/billing/
  │
  ├── login.html            Standalone (no sidebar). Staff login form.
  │
  └── base.html             Dark sidebar layout. All authenticated pages extend this.
        │  Sidebar: Dashboard, Open Tables, Bill History, Reports (manager+), Kitchen link
        │  Topbar: page title, live WebSocket dot, sign-out form
        │  Blocks: title, page_title, nav_*, topbar_actions, content, extra_styles, extra_scripts
        │
        ├── dashboard.html        KPI cards (revenue, bills, guests, tables)
        │                         Bill requests table + recent bills table
        │                         JS: auto-refreshes KPI grid on WS events (setInterval 30s)
        │
        ├── open_bills.html       Grid of table cards, color-coded by elapsed time
        │                         (green <30 min, orange 30–60 min, red >60 min)
        │                         JS: reloads on bill_requested / table_closed WS events
        │
        ├── bill_detail.html      Two-column layout:
        │                           Left  — orders grouped by Guest 1 / Guest 2 / …
        │                           Right (sticky) — billing summary panel
        │                                            + discount section (% or flat)
        │                                            + payment method grid + amount input
        │                                            + recorded payments list
        │                                            + "Mark as Paid" button → confirm modal
        │                         All mutations via fetch() POST → JSON response → DOM update
        │
        ├── receipt.html          Printable thermal-style white layout (font: monospace)
        │                         print CSS hides sidebar/topbar; only receipt-paper visible
        │
        ├── history.html          Filter bar (date tabs, method select, table input, search)
        │                         Sortable data-table of all bills with receipt links
        │
        └── reports.html          KPI row + period toggle (7-day / 30-day)
                                  Chart.js line chart — revenue trend
                                  Chart.js doughnut — payment method breakdown
                                  Top items table (last 30 days)
```

---

## 2. Settings Architecture

```
core/settings/
  ├── base.py   ← Shared: INSTALLED_APPS (restaurants, ordering, billing),
  │                       WhiteNoise middleware, Redis channel layer,
  │                       static (STATIC_ROOT, /static/), media, sessions
  ├── dev.py    ← DEBUG=True, ALLOWED_HOSTS=*, PostgreSQL from DB_* vars
  └── prod.py   ← DEBUG=False, ALLOWED_HOSTS from CSV env var,
                   PostgreSQL from DATABASE_URL, Redis from REDIS_URL,
                   SECURE_SSL_REDIRECT=False (Railway proxy handles SSL)
```

---

## 3. URL Routing Architecture

**Critical ordering rule**: specific prefixes must come before the restaurants slug catch-all.

```
core/urls.py
  ├── path('admin/', ...)
  ├── path('ordering/', include('ordering.urls'))   ← BEFORE restaurants
  ├── path('billing/',  include('billing.urls'))    ← BEFORE restaurants
  ├── path('',          home)
  └── path('',          include('restaurants.urls'))
         └── path('<slug:restaurant_slug>/', ...)   ← catch-all, must be last
```

If `billing/` or `ordering/` appeared after the restaurants include, the slug pattern `<slug:...>` would match them first and return 404.

---

## 4. Data Model Relationships

```
Restaurant
  │
  ├──< Category ──< MenuItem
  │
  ├──< Table  (qr_token = unique secret)
  │     │
  │     └──< TableSession  (status: open/paid/closed)
  │               │
  │               ├──< CustomerSession  (1 per browser/device)
  │               │         │
  │               │         ├── Cart (1:1) ──< CartItem ──> MenuItem
  │               │         └──< Order ──< OrderItem ──> MenuItem
  │               │
  │               └── Bill (1:1, OneToOneField)
  │                     └──< Payment
  │
  └──< StaffProfile ──> User  (role: owner/manager/cashier)
```

---

## 5. Deployment Architecture

```
[GitHub main branch]
        │  git push
        ▼
[Railway CI — Nixpacks]
        │  bash build.sh
        ├── pip install -r requirements.txt
        └── python manage.py collectstatic --no-input
                │
                ▼
        [Docker image built]
                │  container start
                ▼
        python manage.py migrate --no-input
                │
                ▼
        daphne -b 0.0.0.0 -p $PORT core.asgi:application
                │
        ┌───────┴───────────────────────┐
        │                               │
   HTTP requests                  WS connections
        │                               │
  WhiteNoise (static)           AuthMiddlewareStack
  Django views                  → URLRouter
        │                               │
  PostgreSQL (DATABASE_URL)     KitchenConsumer / OrderConsumer
                                        │
                                  Redis (REDIS_URL)
```

---

## 6. Customer QR Session Flow

```
Customer scans QR (/<slug>/?t=<qr_token>)
        │
        ▼
restaurants/views.py:menu()
        │
        ├── ordering/session.py:join_table(request, qr_token)
        │         │
        │         ├── Validate token → Table (raises 'invalid_token' if not found)
        │         ├── Find or create open TableSession for Table
        │         ├── Generate or retrieve browser_uuid from Django session
        │         └── Find or create CustomerSession(table_session, browser_uuid)
        │                   │
        │                   └── Store CustomerSession.id in request.session
        │
        └── Render menu.html with: has_session=True, table_number, bill_requested
```

---

## 7. Ordering Flow

```
Customer adds item
        │  POST /ordering/cart/add/
        ▼
ordering/views.py:cart_add()
        │
        ├── get_active_customer_session(request)  ← from session cookie only
        ├── _get_or_create_cart(customer_session)
        └── CartItem.objects.get_or_create(cart, menu_item)

Customer places order
        │  POST /ordering/place/
        ▼
ordering/views.py:place_order()
        │
        ├── Convert CartItems → Order + OrderItems
        ├── Clear cart
        └── channel_layer.group_send('kitchen_{id}', {type:'new_order', ...})
                │
                ▼
        KitchenConsumer.new_order()
                │
                └── Broadcast to all kitchen WebSocket connections
```

---

## 8. Billing Flow

```
Cashier opens /billing/
        │
        ├── @billing_required → check User has active StaffProfile
        ├── billing/views.py:dashboard() → today_stats(), bill_requests
        └── Render KPI cards + pending bill requests

Cashier clicks "View Bill" for a table
        │
        └── /billing/bills/<session_id>/
                │
                ├── billing/services.generate_bill(table_session, cashier)
                │     ← Idempotent: returns existing Bill if already exists
                │     ← Computes subtotal from all non-cancelled orders
                │
                ├── Cashier optionally applies discount
                │     POST /billing/bills/<id>/discount/
                │     └── services.apply_discount() → recalculate all totals
                │
                ├── Cashier records payment(s)
                │     POST /billing/bills/<id>/payment/
                │     └── services.add_payment() → Payment row created
                │
                └── Cashier closes bill (when amount_due ≤ ₹0.50)
                      POST /billing/bills/<id>/close/
                      └── services.close_bill()
                            ├── Bill.status = 'paid', paid_at = now()
                            ├── TableSession.close(paid=True)
                            │     ├── TableSession.status = 'paid'
                            │     └── TableSession.ended_at = now()
                            └── group_send('kitchen_{id}', {type:'table_closed'})
```

---

## 9. WebSocket Architecture

```
Browser (Kitchen / Billing / Customer)
        │  ws://.../ws/kitchen/<restaurant_id>/
        ▼
Django Channels URLRouter
        │
        ▼
KitchenConsumer (ordering/consumers.py)
        │
        ├── connect()   → join group 'kitchen_{restaurant_id}'
        ├── disconnect()→ leave group
        └── Handlers:
              new_order(data)    → forward to WebSocket client
              order_update(data) → forward to WebSocket client
              bill_requested(data) → forward to WebSocket client
              table_closed(data)   → forward to WebSocket client

Browser (Customer order confirmation)
        │  ws://.../ws/order/<order_id>/
        ▼
OrderConsumer
        │
        ├── connect()  → join group 'order_{order_id}'
        └── order_update(data) → forward to customer browser
```

---

## 10. Session & Request Locking Lifecycle

```
1. BROWSING      → No CustomerSession. Menu visible, cart/order buttons disabled.
                   (Banner shown: "Scan QR to order")

2. ACTIVE        → CustomerSession exists, TableSession.status = 'open'.
                   Full cart and ordering access.

3. BILL REQUESTED→ bill_requested_at set on TableSession.
                   Cart additions blocked (400 response).
                   Bill Request button locked green.

4. BILL OPEN     → Bill generated (status=draft), cashier handling payment.
                   TableSession still 'open', customers cannot order.

5. PAID          → Bill.status = 'paid', TableSession.status = 'paid'.
                   CustomerSessions invalidated (get_active_customer_session returns None).
                   New QR scan creates a fresh TableSession.
```

---

## 11. Media File Strategy

AR models (`.glb`, `.usdz`) and food images are **committed directly to the git repository** under `media/`. They are served by Django's `serve()` view registered in `core/urls.py`:

```python
re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})
```

**Why**: Railway's filesystem is ephemeral (wiped on redeploy). Git-committed media is always present after every deploy without requiring any external cloud storage service, free tier limits, or payment methods.

**Trade-off**: Large binary files in git history. Acceptable for a small restaurant with a fixed menu of AR models.
