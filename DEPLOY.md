# Deploying to Railway

## Prerequisites
- GitHub account with this repo pushed
- Railway account → [railway.app](https://railway.app) (sign up free)

---

## Step 1 — Push the repo to GitHub

```bash
git init          # if not already a repo
git add .
git commit -m "chore: prepare for Railway deployment"
git remote add origin https://github.com/YOUR_USERNAME/ar-main.git
git push -u origin main
```

---

## Step 2 — Create a new Railway project

1. Go to [railway.app/new](https://railway.app/new)
2. Click **Deploy from GitHub repo** → select your `ar-main` repository
3. Railway will detect the `railway.toml` and `Procfile` automatically

---

## Step 3 — Add PostgreSQL plugin

1. In your Railway project dashboard, click **+ New**
2. Select **Database → Add PostgreSQL**
3. Railway will automatically inject `DATABASE_URL` into your web service

---

## Step 4 — Add Redis plugin

1. Click **+ New** again
2. Select **Database → Add Redis**
3. Railway will automatically inject `REDIS_URL` into your web service

---

## Step 5 — Set environment variables

In your **web service → Variables tab**, add:

| Variable | Value |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `core.settings.prod` |
| `SECRET_KEY` | Run command below to generate |
| `ALLOWED_HOSTS` | `yourapp.up.railway.app` (set after first deploy) |

Generate a secure SECRET_KEY locally:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Step 6 — Deploy

Railway auto-deploys on every push to `main`. The build script will:
1. `pip install -r requirements.txt`
2. `python manage.py collectstatic --no-input`
3. `python manage.py migrate`

Then Daphne starts on Railway's assigned `$PORT`.

---

## Step 7 — Create a superuser

Once deployed, open a Railway shell (service → **Shell** tab):

```bash
python manage.py createsuperuser
```

Then go to `https://yourapp.up.railway.app/admin/` to add your restaurant, categories, and menu items.

---

## Step 8 — Update ALLOWED_HOSTS

After your first deploy, Railway gives you a domain like `ar-main-production.up.railway.app`.
Update the `ALLOWED_HOSTS` variable to match:

```
ar-main-production.up.railway.app
```

---

## Media Files (AR Models)

> **Important**: Railway's ephemeral filesystem means uploaded files (`.glb`, `.usdz` AR models)
> are wiped on every redeploy.
>
> For persistent media in production, integrate cloud storage:
> - [Cloudinary](https://cloudinary.com) — free tier, easy Django integration via `django-cloudinary-storage`
> - [AWS S3 / Backblaze B2](https://django-storages.readthedocs.io) — via `django-storages`
>
> For now, you can pre-upload AR models and they will persist between deploys as long as you
> don't redeploy. A full cloud storage integration can be added as a next step.

---

## Local dev reminder

```bash
python3 manage.py runserver   # uses core.settings.dev + local PostgreSQL + local Redis
```
