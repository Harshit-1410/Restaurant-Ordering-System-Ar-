# AI Context Document

This document provides a comprehensive context and documentation of the Augmented Reality (AR) Restaurant Ordering system, optimized for subsequent AI assistants to understand the codebase and build on it immediately.

---

## 1. Project Overview
The project is a Web-based Augmented Reality (AR) Restaurant Ordering application. It allows customers sitting at a table to scan a QR code, browse a digital menu with rich food photography, view 3D AR representations of select dishes directly on their table, add items to a cart, place orders, and request the bill, all via their mobile web browsers.
The kitchen staff can view incoming orders and update their preparation status in real-time, and the manager can handle billing at the counter via dedicated dashboards.

**Live deployment**: `https://web-production-cac8d9.up.railway.app`

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 4.2.30 |
| Real-Time Layer | Django Channels 4.3.2 + WebSockets |
| ASGI Server | Daphne 4.2.2 |
| Channel Layer | Redis (channels_redis 4.3.0) |
| Database | PostgreSQL 16 (local dev + Railway production) |
| DB Adapter | psycopg2-binary 2.9.12 |
| Environment Config | python-decouple 3.8 (reads from `.env`) |
| Static Files | WhiteNoise 6.11.0 |
| DB URL Parsing | dj-database-url 3.0.1 |
| Image Handling | Pillow 11.2.1 |
| Frontend | HTML5, CSS3, Vanilla JavaScript (no framework) |
| AR Engine | Google `<model-viewer>` (Android/WebXR) + Apple AR Quick Look (`.usdz` on iOS) |
| Icons & Fonts | FontAwesome 6.5.0, Google Fonts |

---

## 3. Directory Structure
```
ar-main/
├── core/                        # Core Django project config
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Shared settings (all environments)
│   │   ├── dev.py               # Development: DEBUG=True, local PostgreSQL
│   │   └── prod.py              # Production: Railway DATABASE_URL + REDIS_URL
│   ├── asgi.py                  # ASGI entry point (Channels ProtocolTypeRouter)
│   ├── wsgi.py                  # WSGI entry point
│   └── urls.py
├── restaurants/                 # Restaurant, Category, MenuItem models
│   ├── templates/restaurants/
│   │   └── menu.html            # Unified responsive menu template
│   └── views.py
├── ordering/                    # Cart, TableSession, Order, WebSocket logic
│   ├── templates/ordering/
│   │   ├── cart.html
│   │   ├── kitchen.html         # Real-time kitchen dashboard
│   │   ├── billing.html         # Counter billing dashboard
│   │   └── session_bill.html    # Printed receipt layout
│   ├── consumers.py             # KitchenConsumer, OrderConsumer (WebSocket)
│   ├── routing.py               # WebSocket URL routes
│   └── views.py
├── media/                       # Uploaded images and AR models (.glb, .usdz)
├── staticfiles/                 # Collected static files (generated, git-ignored)
├── .env                         # Local secrets (git-ignored)
├── .env.example                 # Template for .env
├── .gitignore
├── requirements.txt
├── manage.py
├── Procfile                     # Railway process definition
├── railway.toml                 # Railway build + deploy config
└── build.sh                     # Railway build script (install + collectstatic)
```

---

## 4. Settings Architecture

The settings are split into three files under `core/settings/`:

- **`base.py`**: All shared config — INSTALLED_APPS, MIDDLEWARE (with WhiteNoise), TEMPLATES, CHANNEL_LAYERS (Redis), static files (WhiteNoise + STATIC_ROOT), media, i18n, session engine.
- **`dev.py`**: `DEBUG=True`, `ALLOWED_HOSTS=['*']`, PostgreSQL from individual `.env` vars (`DB_NAME`, `DB_USER`, etc.).
- **`prod.py`**: `DEBUG=False`, `ALLOWED_HOSTS` from `ALLOWED_HOSTS` env var (CSV), PostgreSQL from `DATABASE_URL` (Railway plugin), Redis from `REDIS_URL` (Railway plugin), HSTS + security headers, `SECURE_SSL_REDIRECT=False` (Railway terminates SSL at proxy).

**Default settings module**: `core.settings.dev` (set in `manage.py`, `asgi.py`, `wsgi.py`).  
**Production**: set `DJANGO_SETTINGS_MODULE=core.settings.prod` as an env var.

---

## 5. Database Models & Schema
```
              ┌─────────────────┐
              │   Restaurant    │
              └────────┬────────┘
                       │ 1
                       │ *
              ┌────────┴────────┐
              │    Category     │
              └────────┬────────┘
                       │ 1
                       │ *
              ┌────────┴────────┐
              │   MenuItem      │◄──────────────────┐
              └─────────────────┘                   │
                                                    │
              ┌─────────────────┐                   │
              │  TableSession   │                   │
              └────────┬────────┘                   │
                       │ 1                          │
                       ├─────────────────────┐      │
                       │ 1                   │ 1    │ *
              ┌────────┴────────┐   ┌────────┴───┐  │
              │     Order       │   │    Cart    │  │
              └────────┬────────┘   └────────┬───┘  │
                       │ 1                   │ 1    │
                       │ *                   │ *    │
              ┌────────┴────────┐   ┌────────┴───┐  │
              │   OrderItem     ├───┼─── CartItem ──┘
              └─────────────────┘   └────────────┘
```

### Key Models
1. **Restaurant**: Fields `name`, `slug`, `image`, `is_active`, `created_at`.
2. **Category**: Fields `restaurant` (FK), `name`, `image`, `is_active`.
3. **MenuItem**: Fields `category` (FK), `name`, `description`, `price`, `image`, `is_available`, `ar_model_file` (`.glb`), `ar_model_usdz` (`.usdz`), `is_veg`.
4. **TableSession**: Fields `restaurant` (FK), `table_number`, `session_token`, `is_active`, `bill_requested_at`, `is_paid`, `closed_at`.
5. **Cart**: Belongs to a `TableSession`.
6. **CartItem**: Fields `cart` (FK), `menu_item` (FK), `quantity`, `notes`.
7. **Order**: Fields `table_session` (FK), `restaurant` (FK), `status` (`pending`, `preparing`, `ready`, `served`, `cancelled`), `total_amount`, `created_at`.
8. **OrderItem**: Fields `order` (FK), `menu_item` (FK), `quantity`, `unit_price`, `subtotal`.

---

## 6. End-to-End Application Flows

### 1. Cart Flow
1. Customer visits `/<restaurant-slug>/?table=<table_number>`.
2. Django view sets up a `TableSession` in the session store.
3. Customer clicks "Add to Cart". Frontend makes a `POST` to `/ordering/cart/add/`.
4. Backend updates the `CartItem` record associated with the active session.
5. Badges and the floating desktop Cart Bar update immediately.

### 2. Ordering Flow
1. Customer clicks "View Cart" → `/ordering/cart/`.
2. Quantity buttons send increment/decrement calls to the backend.
3. Customer clicks "Place Order" → `POST /ordering/place/`.
4. Backend converts `CartItem`s into `Order` + `OrderItem` records, clears cart, notifies kitchen via WebSockets.
5. Customer is redirected to `/ordering/confirmation/<order_id>/`.

### 3. AR Flow
1. If a `MenuItem` has `.glb` / `.usdz` models uploaded, "View on your table" appears.
2. **iOS Safari**: Launches Apple AR Quick Look via `<a rel="ar">` targeting `.usdz`.
3. **Android Chrome**: Overlays Google `<model-viewer>` and launches Android Scene Viewer.
4. **Unsupported browsers**: Shows interactive 3D model inline.

### 4. Bill Request Flow
1. Customer clicks "Request Bill".
2. `POST /ordering/bill/request/` → records `bill_requested_at`, notifies dashboards via WebSockets.
3. UI locks the button (green "Bill Requested ✓").
4. Further cart additions return `400 Bad Request`.

---

## 7. Key API Endpoints
- `GET /<restaurant-slug>/?table=<n>` : Customer-facing menu page.
- `GET /item/<item_id>/detail/` : Returns item details + AR model URLs as JSON.
- `POST /ordering/cart/add/` : Adds an item to the cart.
- `GET /ordering/cart/data/` : Returns cart item count and subtotal.
- `POST /ordering/cart/remove/<cart_item_id>/` : Removes or decrements a cart item.
- `POST /ordering/place/` : Places the order.
- `POST /ordering/bill/request/` : Requests the bill.
- `GET /ordering/kitchen/<restaurant_id>/` : Kitchen real-time dashboard.
- `GET /ordering/billing/` : Counter billing dashboard.

---

## 8. Real-Time WebSockets
- **`/ws/kitchen/<restaurant_id>/`**: Broadcasts `new_order` and `bill_requested` events to the kitchen dashboard.
- **`/ws/order/<order_id>/`**: Broadcasts order status updates to the customer confirmation page.

Both channels use Redis as the backing channel layer (`channels_redis.core.RedisChannelLayer`).

---

## 9. Deployment
- **Platform**: Railway (`https://railway.app`)
- **Build**: `bash build.sh` → `pip install` + `collectstatic`
- **Start**: `python manage.py migrate && daphne -b 0.0.0.0 -p $PORT core.asgi:application`
- **Database**: Railway PostgreSQL plugin (injects `DATABASE_URL`)
- **Redis**: Railway Redis plugin (injects `REDIS_URL`)
- **Static files**: Served by WhiteNoise middleware from `staticfiles/`
- **Media files**: Ephemeral (wiped on redeploy) — cloud storage integration pending

### Required Railway Environment Variables
| Variable | Source |
|---|---|
| `DJANGO_SETTINGS_MODULE` | Set manually: `core.settings.prod` |
| `SECRET_KEY` | Set manually (generate with `get_random_secret_key()`) |
| `ALLOWED_HOSTS` | Set manually: your `.up.railway.app` domain |
| `DATABASE_URL` | Reference: `${{Postgres.DATABASE_URL}}` |
| `REDIS_URL` | Reference: `${{Redis.REDIS_URL}}` |
