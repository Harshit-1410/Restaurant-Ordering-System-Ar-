# Deploying to Railway

The app is live at **`https://web-production-cac8d9.up.railway.app`**.

---

## How Deploys Work

Every push to the `main` branch on GitHub triggers an automatic Railway deploy:

| Phase | What runs |
|---|---|
| **Build** | `bash build.sh` → `pip install -r requirements.txt` + `python manage.py collectstatic` |
| **Start** | `python manage.py migrate --no-input && daphne -b 0.0.0.0 -p $PORT core.asgi:application` |

Static files are served by **WhiteNoise** middleware directly from Daphne — no separate nginx needed.
Migrations run automatically on every deploy before the server starts.

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
3. Railway detects `railway.toml` and `build.sh` automatically.

### Step 3 — Add PostgreSQL + Redis plugins
- Click **+ New** → **Database → PostgreSQL**
- Click **+ New** → **Database → Redis**

### Step 4 — Set environment variables
Add all 5 variables from the table above in the web service Variables tab.

### Step 5 — Deploy
Railway auto-deploys on push. Or click **Deploy** manually in the Railway dashboard.

---

## Creating a Superuser (Production)

Railway's database uses an internal hostname only reachable inside Railway's network.
Use the **public URL** from your local machine:

1. Go to Railway → **Postgres** service → **Variables** tab.
2. Copy `DATABASE_PUBLIC_URL`.
3. Run locally:

```bash
DATABASE_URL="<paste DATABASE_PUBLIC_URL here>" DJANGO_SETTINGS_MODULE=core.settings.prod python3 manage.py createsuperuser
```

> Do not use `railway run` — it overrides `DATABASE_URL` with the internal URL which is unreachable from your machine.

---

## Creating Billing Staff (Production)

After creating a superuser, create a `StaffProfile` so they can access the Billing Dashboard:

```bash
DATABASE_URL="<DATABASE_PUBLIC_URL>" DJANGO_SETTINGS_MODULE=core.settings.prod python3 manage.py shell
```

```python
from django.contrib.auth.models import User
from restaurants.models import Restaurant
from billing.models import StaffProfile

user = User.objects.get(username='your_superuser_username')
restaurant = Restaurant.objects.first()
StaffProfile.objects.create(user=user, restaurant=restaurant, role='owner')
exit()
```

Or use **Django Admin → Billing → Staff Profiles → Add**.

---

## Accessing the App

| Page | URL |
|---|---|
| Django Admin | `https://web-production-cac8d9.up.railway.app/admin/` |
| Customer Menu | `https://web-production-cac8d9.up.railway.app/<restaurant-slug>/?t=<qr_token>` |
| Kitchen Dashboard | `https://web-production-cac8d9.up.railway.app/ordering/kitchen/<restaurant_id>/` |
| Billing Dashboard | `https://web-production-cac8d9.up.railway.app/billing/` |
| Billing Login | `https://web-production-cac8d9.up.railway.app/billing/login/` |

Find the `restaurant_id` in Django Admin → Restaurants → click a restaurant → the number in the URL is the ID.

Get the QR token for a table from Django Admin → Ordering → Tables → click a table → copy the "QR URL (full)" field.

---

## Local Development

```bash
# Start PostgreSQL and Redis (Homebrew)
brew services start postgresql@16
brew services start redis

# Run dev server (uses core.settings.dev)
python3 manage.py runserver
```

Local app runs at `http://127.0.0.1:8000/`.

---

## Media Files Strategy

AR models (`.glb`, `.usdz`) and food images are **committed to the git repository** under `media/` and served by Django's `serve()` view:

```python
re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})
```

**Why**: Railway's filesystem is ephemeral (wiped on every redeploy). Committing media to git ensures files are always present after deployment without any external cloud storage, free tier limits, or payment requirements.

Files uploaded via the Django admin are saved to the local `media/` directory. After uploading, commit and push:

```bash
git add media/
git commit -m "chore: add new AR model / food image"
git push origin main
```
