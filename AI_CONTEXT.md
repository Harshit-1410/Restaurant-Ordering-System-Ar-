# AI Context Document

This document provides a comprehensive context and documentation of the Augmented Reality (AR) Restaurant Ordering system, optimized for subsequent AI assistants to understand the codebase and build on it immediately.

---

## 1. Project Overview
The project is a Web-based Augmented Reality (AR) Restaurant Ordering application. It allows customers sitting at a table to scan a QR code, browse a digital menu with rich food photography, view 3D AR representations of select dishes directly on their table, add items to a cart, place orders, and request the bill, all via their mobile web browsers.
The kitchen staff can view incoming orders and update their preparation status in real-time, and the manager can handle billing at the counter via dedicated dashboards.

---

## 2. Tech Stack
- **Backend Framework**: Django (v4.2.30)
- **Real-Time Layer**: Django Channels (v4.3.0) + WebSockets
- **WSGI/ASGI Server**: Daphne (v4.2.2)
- **Database**: SQLite3 (default local development)
- **Grid Frontend**: HTML5 (Responsive Desktop & Mobile Separated Layouts), CSS3, Vanilla Javascript
- **3D/AR engine**: Google `<model-viewer>` (Android / Generic WebXR), Apple AR Quick Look (`.usdz` on iOS Safari)
- **Icons & Fonts**: FontAwesome (v6.5.0), Google Fonts (Plus Jakarta Sans, Inter, Geist, Playfair Display)

---

## 3. Directory Structure
```
ar-main/
├── core/                # Core Django project config (settings, URLs, ASGI/WSGI)
├── restaurants/         # Restaurant details, categories, and MenuItem models
│   ├── templates/
│   │   └── restaurants/
│   │       └── menu.html        # Unified high-fidelity redesigned menu template
│   └── views.py                 # Views for rendering the menu and returning item details
├── ordering/            # Cart, TableSession, Order, and Real-time ws logic
│   ├── templates/
│   │   └── ordering/
│   │       ├── cart.html         # Cart view
│   │       ├── kitchen.html      # Kitchen real-time dashboard
│   │       ├── billing.html      # Billing dashboard for counter
│   │       └── session_bill.html # Printed receipt layout
│   ├── consumers.py     # WebSocket consumers (KitchenConsumer, OrderConsumer)
│   ├── routing.py       # WebSocket URL routes
│   └── views.py         # Transactional views (Cart addition, Order placing, Bill requesting)
├── media/               # Uploaded images and AR model files (.glb, .usdz)
├── manage.py            # Django command-line utility
└── db.sqlite3           # Local development database
```

---

## 4. Database Models & Schema
```
                  ┌─────────────────┐
                  │   Restaurant    │
                  └────────┬────────┘
                           │ 1
                           │
                           │ *
                  ┌────────┴────────┐
                  │  Category       │
                  └────────┬────────┘
                           │ 1
                           │
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
4. **TableSession**: Represents a continuous visit by a customer group. Fields `restaurant` (FK), `table_number`, `session_token`, `is_active`, `bill_requested_at`, `is_paid`, `closed_at`.
5. **Cart**: Belongs to a `TableSession`.
6. **CartItem**: Fields `cart` (FK), `menu_item` (FK), `quantity`, `notes`.
7. **Order**: Fields `table_session` (FK), `restaurant` (FK), `status` (`pending`, `preparing`, `ready`, `served`, `cancelled`), `total_amount`, `created_at`.
8. **OrderItem**: Fields `order` (FK), `menu_item` (FK), `quantity`, `unit_price`, `subtotal`.

---

## 5. End-to-End Application Flows

### 1. Cart Flow
1. Customer visits `/<restaurant-slug>/?table=<table_number>`.
2. Django view sets up a `TableSession` in the session store.
3. Customer clicks "Add to Cart". Frontend makes a `POST` request to `/ordering/cart/add/`.
4. Backend updates the `CartItem` record associated with the active session.
5. Badges in the header and the bottom navigation bar, and the floating desktop Cart Bar, update immediately with items and total cost.

### 2. Ordering Flow
1. Customer clicks "View Cart" to open `/ordering/cart/`.
2. Cart shows all items in the active session's cart. Quantity buttons send increment/decrement calls to the backend.
3. Customer clicks "Place Order". Frontend disables the button to prevent duplicate submissions, displays "Placing order...", and sends a `POST` request to `/ordering/place/`.
4. Backend converts all `CartItem`s into an `Order` and `OrderItem` records, clears the cart, and notifies the kitchen dashboard in real-time via WebSockets (`KitchenConsumer`).
5. Customer is redirected to `/ordering/confirmation/<order_id>/`.

### 3. AR Flow
1. If a `MenuItem` has `ar_has_model` set to `True` (meaning `.glb` / `.usdz` models are uploaded via Admin), the "View on your table" button appears on mobile item cards and detail modals.
2. In iOS Safari: Tapping the button launches **Apple AR Quick Look** using a link with `rel="ar"` targeting the `.usdz` file.
3. In Android Chrome / generic browsers: It dynamically overlays the Google `<model-viewer>` component and allows launching the model in AR via **Android Scene Viewer** (using WebXR mode).
4. Unsupported browsers show an interactive 3D model inline on the modal.

### 4. Bill Request Flow
1. Customer clicks "Request Bill" (sidebar footer on desktop, bottom-left FAB on mobile).
2. Frontend sends a `POST` request to `/ordering/bill/request/` with the CSRF token.
3. Backend records `bill_requested_at` in the `TableSession`, notifies the kitchen and billing dashboards via WebSockets, and locks the session.
4. UI turns the button green, showing "Bill Requested ✓", and disables further interaction.
5. Further item additions to the cart are blocked at the database level with a `400 Bad Request` and descriptive error message.

---

## 6. Key API Endpoints
- `GET /item/<item_id>/detail/` : Returns product details, images, and AR model URLs in JSON.
- `POST /ordering/cart/add/` : Adds an item to the cart. Requires `item_id` and `quantity`.
- `GET /ordering/cart/data/` : Returns the total item count and subtotal of the cart.
- `POST /ordering/cart/remove/<cart_item_id>/` : Removes or decrements a cart item.
- `POST /ordering/place/` : Converts cart items into a placed order.
- `POST /ordering/bill/request/` : Requests the bill for the active session.

---

## 7. Real-Time WebSockets
- **Kitchen Updates**: Connecting to `/ws/kitchen/<restaurant_id>/` sends real-time order alerts (`new_order` event) and bill requests (`bill_requested` event) to the kitchen dashboard.
- **Order Tracker**: Connecting to `/ws/order/<order_id>/` broadcasts status updates to the customer's confirmation page.
