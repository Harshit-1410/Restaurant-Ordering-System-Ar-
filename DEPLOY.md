# Deploying to Railway

The app is already live at **`https://web-production-cac8d9.up.railway.app`**.
This document serves as a reference for re-deploying, setting up from scratch, or onboarding a new environment.

---

## How Deploys Work

Every push to the `main` branch on GitHub triggers an automatic Railway deploy:

| Phase | What runs |
|---|---|
| **Build** | `bash build.sh` → `pip install -r requirements.txt` + `python manage.py collectstatic` |
| **Start** | `python manage.py migrate && daphne -b 0.0.0.0 -p $PORT core.asgi:application` |

Static files are served by **WhiteNoise** middleware directly from Daphne — no separate nginx needed.

---

## Required Environment Variables

Set these in Railway → web service → **Variables** tab:

| Variable | Value |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `core.settings.prod` |
| `SECRET_KEY` | Generate with command below |
| `ALLOWED_HOSTS` | Your Railway domain e.g. `web-production-cac8d9.up.railway.app` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` ← Railway reference syntax |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` ← Railway reference syntax |

> **Important**: `DATABASE_URL` and `REDIS_URL` must be set as **reference variables** using Railway's `${{ServiceName.VAR}}` syntax — they are not auto-injected automatically.

Generate a SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Setting Up from Scratch

### Step 1 — Push to GitHub
```bash
git add .
git commit -m "chore: initial commit"
git push origin main
```

### Step 2 — Create Railway project
1. Go to [railway.app/new](https://railway.app/new)
2. **Deploy from GitHub repo** → select `Restaurant-Ordering-System-Ar-`
3. Railway detects `railway.toml` and `Procfile` automatically

### Step 3 — Add PostgreSQL + Redis plugins
- Click **+ New** → **Database → PostgreSQL**
- Click **+ New** → **Database → Redis**

### Step 4 — Set environment variables
Add all 5 variables from the table above in the web service Variables tab.

### Step 5 — Deploy
Railway auto-deploys on push. Or click **Deploy** manually.

---

## Creating a Superuser (Production)

Railway's database uses an **internal hostname** (`postgres.railway.internal`) that is only reachable inside Railway's network. To create a superuser from your local machine, use the **public URL**:

1. Go to Railway → **Postgres** service → **Variables** tab
2. Copy `DATABASE_PUBLIC_URL`
3. Run this single command locally:

```bash
DATABASE_URL="<paste DATABASE_PUBLIC_URL here>" DJANGO_SETTINGS_MODULE=core.settings.prod python3 manage.py createsuperuser
```

> Do not use `railway run` — it overrides `DATABASE_URL` with the internal URL.

---

## Accessing the App

| Page | URL |
|---|---|
| Django Admin | `https://web-production-cac8d9.up.railway.app/admin/` |
| Customer Menu | `https://web-production-cac8d9.up.railway.app/<restaurant-slug>/?table=1` |
| Kitchen Dashboard | `https://web-production-cac8d9.up.railway.app/ordering/kitchen/<restaurant_id>/` |
| Billing Dashboard | `https://web-production-cac8d9.up.railway.app/ordering/billing/` |

Find the `restaurant_id` in Django Admin → Restaurants → click a restaurant → the number in the URL (`/admin/restaurants/restaurant/**1**/change/`) is the ID.

---

## Media Files (AR Models) — Known Limitation

Railway's filesystem is **ephemeral** — uploaded `.glb` and `.usdz` AR model files are wiped on every redeploy.

For persistent media in production, integrate cloud storage (see `TODO.md`):
- [Cloudinary](https://cloudinary.com) via `django-cloudinary-storage` (recommended, free tier)
- [AWS S3](https://django-storages.readthedocs.io) via `django-storages`
- [Railway Volumes](https://docs.railway.app/reference/volumes) (simplest for Railway, paid)

---

## Local Development

```bash
# Start PostgreSQL and Redis (Homebrew services)
brew services start postgresql@16
brew services start redis

# Run dev server (uses core.settings.dev + local PostgreSQL)
python3 manage.py runserver
```

Local app runs at `http://127.0.0.1:8000/`.
