# Roadmap & TODO List

This document lists the prioritized roadmap, technical debt cleanup, and future enhancements for the AR Restaurant Ordering System.

---

## ✅ Completed

- [x] PostgreSQL migration (from SQLite3)
- [x] Redis-backed channel layer
- [x] Dev/prod settings split with python-decouple
- [x] WhiteNoise static file serving
- [x] Railway deployment (live at `https://web-production-cac8d9.up.railway.app`)
- [x] `requirements.txt`, `.gitignore`, `.env.example`
- [x] Fixed `STATIC_URL`, removed `ASGIStaticFilesHandler`, disabled `SECURE_SSL_REDIRECT` for Railway

---

## 1. High Priority

### Media File Persistence (Production Blocker)
- **Cloud Storage for AR Models**: Railway's ephemeral filesystem wipes uploaded `.glb` and `.usdz` files on every redeploy. Integrate cloud storage using one of:
  - [Cloudinary](https://cloudinary.com) via `django-cloudinary-storage` (free tier, easiest)
  - [AWS S3 / Backblaze B2](https://django-storages.readthedocs.io) via `django-storages`
  - [Railway Volumes](https://docs.railway.app/reference/volumes) (paid, simplest for Railway)

### Security
- **Staff Dashboard Authentication**: The kitchen (`/ordering/kitchen/<id>/`) and billing (`/ordering/billing/`) dashboards have no login protection. Anyone who knows the URL can access them. Add `@login_required` or HTTP Basic Auth.
- **Rate Limiting**: Add throttling on `cart/add/` and `place/` endpoints to prevent abuse. Use `django-ratelimit` or DRF throttle classes.

### Database Performance
- **Index Optimization**: Add `db_index=True` on `MenuItem.is_available`, `Category.is_active`, and `Restaurant.slug` to speed up menu page queries.
- **Session Expiry Cron**: Implement a background task (Django management command + Railway cron) to auto-close `TableSession` records inactive for more than 4 hours.

---

## 2. Medium Priority

### Testing Integration
- **Unit Tests**: Add test coverage for `cart_add`, `place_order`, and `request_bill` views in `ordering/tests.py` and `restaurants/tests.py`.
- **End-to-End Tests**: Set up Playwright or Cypress for automated responsive layout and checkout flow testing.

### Kitchen Dashboard Enhancements
- **Sound Alerts**: Add audio notification alerts when a new order is received or a bill is requested. WebSocket reconnection with exponential backoff is already implemented.

### Customer UX
- **Order History Tab**: Create an inline "Orders List" modal on the mobile bottom navigation Orders tab so customers can see previously placed orders during their current session.

---

## 3. Nice to Have

### Analytics & Reporting
- **Counter Sales Analytics**: Build a simple analytics page showing daily revenue, popular items, average dining times, and order volume.

### AR Enhancements
- **AR Model Viewer Customization**: Add ambient lighting controls and rotation speed settings in `<model-viewer>` to improve item exploration.

### Operations
- **QR Code Generator**: Build an admin action that auto-generates and downloads a printable QR code for each table number per restaurant.
- **Multi-Restaurant Support UI**: Add a landing page listing all active restaurants (currently only accessible if you know the slug).
