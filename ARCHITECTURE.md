# Architecture Documentation

This document describes the component hierarchy, data flow, settings architecture, and lifecycle operations of the AR Ordering System.

---

## 1. Component Hierarchy

```
[menu.html]
  ├── Desktop Layout (Culinary Clarity)
  │     ├── Header (.d-header) -> Cart Badge (.d-cart-badge)
  │     ├── Sidebar (.d-sidebar) -> Category Nav & Request Bill Button (.d-bill-btn)
  │     ├── Main Grid (.d-grid) -> Item Cards (.d-card)
  │     └── Floating Cart Bar (.d-cart-bar)
  │
  ├── Mobile Layout (Savor Mobile)
  │     ├── Header (.m-header) -> Search Box (.m-search)
  │     ├── Body Content -> Collapsible Accordions (.m-cat) -> List Items (.m-item)
  │     ├── Floating Menu FAB (.m-fab)
  │     ├── Floating Bill FAB (.m-bill-btn)
  │     └── Bottom Navigation Bar (.m-bottom-nav)
  │
  └── Shared Dialog Modal (.modal-backdrop)
        ├── Item Details & Veg/Non-Veg Tag
        ├── AR Preview Overlay (Google <model-viewer> or Quick Look Link)
        └── Quantity Controls (.qty-ctrl) & Add to Cart button (.btn-add-cart)
```

---

## 2. Settings Architecture

```
core/settings/
  ├── base.py       ← Shared: apps, middleware (WhiteNoise), channels (Redis),
  │                            static (STATIC_ROOT, /static/), media, i18n
  ├── dev.py        ← Extends base: DEBUG=True, ALLOWED_HOSTS=*, PostgreSQL
  │                            from individual DB_* env vars
  └── prod.py       ← Extends base: DEBUG=False, ALLOWED_HOSTS CSV,
                               PostgreSQL from DATABASE_URL (dj-database-url),
                               Redis from REDIS_URL, HSTS headers,
                               SECURE_SSL_REDIRECT=False (Railway proxy handles SSL)
```

Entry points (`manage.py`, `asgi.py`, `wsgi.py`) default to `core.settings.dev`.
Set `DJANGO_SETTINGS_MODULE=core.settings.prod` in Railway to use production settings.

---

## 3. Deployment Architecture

```
[GitHub main branch]
        │  push
        ▼
[Railway CI — Nixpacks build]
        │  bash build.sh
        ├── pip install -r requirements.txt
        └── python manage.py collectstatic --no-input
                │
                ▼
        [Docker image built]
                │  container start
                ▼
        python manage.py migrate
                │
                ▼
        daphne -b 0.0.0.0 -p $PORT core.asgi:application
                │
        ┌───────┴────────────────────┐
        │                            │
   HTTP traffic                WS traffic
        │                            │
   WhiteNoise                 AuthMiddlewareStack
   (static files)             → URLRouter
        │                            │
   Django views            KitchenConsumer / OrderConsumer
        │                            │
   PostgreSQL              Redis channel layer
   (DATABASE_URL)          (REDIS_URL)
```

---

## 4. Dynamic Data Flows

### Cart Lifecycle & Addition

```
[Frontend Click] ────► [POST /ordering/cart/add/]
                             │
                             ▼
                    [get_or_create_cart]
                             │
                             ├─► Active Session?
                             │     ├── Yes: Retrieve existing TableSession
                             │     └── No: Create new TableSession
                             │
                             ▼
                    [CartItem get_or_create]
                             │
                             ▼
                    [Calculate new totals] ──► [Response HTTP 200 JSON]
                                                     │
                                                     ▼
                                            [updateCartState()]
                                                     │
                                                     ▼
                                            Update Badge Counts
                                            Show/Update Floating Cart Bar
```

---

## 5. Real-Time WebSocket Flows

```
[Client places order] ──► [POST /ordering/place/]
                                │
                                ▼
                       [Create Order & items]
                                │
                                ▼
                    [django-channels group_send]
                          (via Redis layer)
                                │
                                ▼
             [KitchenConsumer ws connection group]
                                │
                                ▼
               [Broadcast new_order to Kitchen]
```

---

## 6. Session & Request Locking Lifecycle
1. **Dining State**: Active TableSession exists. Customer can add, modify, or remove items from the cart, and place multiple orders.
2. **Bill Requested State**: Customer triggers the bill request.
   - Sets `bill_requested_at` timestamp.
   - Pushes WebSocket notice to Kitchen and Billing dashboards.
   - Locks TableSession: Frontend buttons are disabled (turning green).
   - Backend view checks `cart.session.bill_requested_at` on every addition request. If set, returns `400 Bad Request`.
3. **Paid State**: Cashier clicks "Close Session" on `/ordering/billing/`, which marks `is_active=False` and `is_paid=True`. The table QR code is ready for the next customer group.
