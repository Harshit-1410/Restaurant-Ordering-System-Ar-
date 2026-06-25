# Architecture Documentation

This document describes the component hierarchy, data flow, and lifecycle operations of the AR Ordering System.

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

## 2. Dynamic Data Flows

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

## 3. Real-Time WebSocket Flows

```
[Client places order] ──► [POST /ordering/place/]
                                │
                                ▼
                       [Create Order & items]
                                │
                                ▼
                    [django-channels group_send]
                                │
                                ▼
             [KitchenConsumer ws connection group]
                                │
                                ▼
               [Broadcast new_order to Kitchen]
```

---

## 4. Session & Request Locking Lifecycle
1. **Dining State**: Active TableSession exists. Customer can add, modify, or remove items from the cart, and place multiple orders.
2. **Bill Requested State**: Customer triggers the bill request.
   - Sets `bill_requested_at` timestamp.
   - Pushes websocket notice to Kitchen and Billing dashboards.
   - Locks TableSession: Frontend buttons are disabled (turning green).
   - Backend view checks `cart.session.bill_requested_at` on every addition request. If set, it returns `400 Bad Request`, preventing database modifications.
3. **Paid State**: Cashier reviews the table session subtotal on the counter billing dashboard `/ordering/billing/`, clicks "Close Session", which marks `is_active = False` and `is_paid = True`. The session terminates, and the table QR code is ready for the next customer group.
