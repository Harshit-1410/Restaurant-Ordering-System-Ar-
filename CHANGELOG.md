# Changelog

All notable changes to this project will be documented in this file.

---

## [1.1.0] - 2026-06-25

This version migrates the infrastructure to a production-ready stack, introduces a dev/prod settings split, and deploys the application to Railway.

### Added
- **PostgreSQL Database**: Migrated from SQLite3 to PostgreSQL 16. All migrations applied cleanly. Local dev uses a `postgres` role; production uses Railway's managed PostgreSQL plugin.
- **Redis Channel Layer**: Configured `channels_redis.core.RedisChannelLayer` on `redis://127.0.0.1:6379/0` (dev) and Railway's injected `REDIS_URL` (prod). Replaces any in-process channel layer.
- **Dev/Prod Settings Split**: Introduced `core/settings/base.py`, `core/settings/dev.py`, and `core/settings/prod.py` using `python-decouple` for env-based configuration.
- **WhiteNoise Static File Serving**: Added `whitenoise.middleware.WhiteNoiseMiddleware` and `CompressedManifestStaticFilesStorage` for production static file serving without a separate CDN or nginx.
- **Railway Deployment**: Added `railway.toml`, `Procfile`, and `build.sh`. The app is live at `https://web-production-cac8d9.up.railway.app`.
- **`requirements.txt`**: First committed dependency manifest — `Django`, `daphne`, `channels`, `channels_redis`, `redis`, `psycopg2-binary`, `python-decouple`, `whitenoise`, `dj-database-url`, `Pillow`.
- **`.gitignore`**: Added project-level gitignore covering `.env`, `db.sqlite3`, `media/`, `staticfiles/`, `__pycache__/`, `.venv/`.
- **`.env.example`**: Safe template for environment variable documentation.

### Fixed
- **`STATIC_URL` Missing Leading Slash**: Changed `'static/'` to `'/static/'` so Django admin CSS resolves correctly at nested URL paths (e.g. `/admin/login/`).
- **`ASGIStaticFilesHandler` Removed**: Removed the dev-only `ASGIStaticFilesHandler` wrapper from `asgi.py` which was intercepting `/static/` requests before WhiteNoise and returning nothing with `DEBUG=False`.
- **`SECURE_SSL_REDIRECT` Disabled**: Set to `False` in `prod.py` — Railway terminates SSL at the load balancer and forwards HTTP internally; keeping it `True` caused Railway's health checker to enter a redirect loop.
- **`migrate` Moved to Start Command**: Removed `migrate` from `build.sh` (database is unavailable during image build) and moved it to the `startCommand` in `railway.toml`, running just before Daphne starts.
- **Pillow Added**: Added `Pillow==11.2.1` to `requirements.txt` to satisfy Django's `ImageField` requirement on `Restaurant.logo` and `MenuItem.image`.

---

## [1.0.0] - 2026-06-25

This version introduces a complete user experience redesign for both desktop and mobile viewports, fixes all session-based regression bugs, and implements a unified design system.

### Added
- **Unified Responsive Layout**: Split desktop and mobile views dynamically using CSS media queries within `menu.html`.
- **Desktop Layout (Culinary Clarity)**:
  - Sticky header featuring branding, search input, and shopping cart badge.
  - Sticky left-hand vertical category navigation rail.
  - Clean 4-column card grid displaying menu items.
  - Floating bottom cart bar that appears dynamically when items are in the cart.
  - "Request Bill" action button placed in the sidebar footer.
- **Mobile Layout (Savor Mobile)**:
  - Sticky header with back button and search bar.
  - Collapsible category accordions with rotating chevrons.
  - Horizontal dish list cards containing Veg/Non-veg badges, name, price, and descriptions.
  - Floating "Menu" FAB and bottom navigation bar with Menu, Orders, and Cart tabs.
  - Floating "Request Bill" FAB positioned at the bottom left.
- **Automatic CSRF Token Injection**: Added a hidden `{% csrf_token %}` block in `menu.html` and `cart.html` templates to set the `csrftoken` cookie for all client-side async `POST` actions.
- **Robust Error Handling**: Added promise-based error handling to front-end cart calls, showing descriptive error toasts when actions are rejected.

### Fixed
- **Add to Cart Silent Failures**: Restored `X-CSRFToken` request headers and cookie generation, resolving `403 Forbidden` API failures.
- **Empty Cart Page**: Fixed the cart page showing empty by successfully persisting added items to the database.
- **Cart Redirection**: Updated the back button in `cart.html` to dynamically redirect customers back to their active restaurant menu.
- **Session Locking after Bill Request**: Restored backend validation blocking cart additions after the bill is requested.
