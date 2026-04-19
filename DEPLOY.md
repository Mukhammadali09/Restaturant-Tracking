# Deployment — Vercel + Neon Postgres

This app is architected for Vercel serverless Python functions with a Neon Postgres database. The frontend is served from Vercel's CDN.

## 1. Create a Neon database

1. Sign up at <https://neon.tech> (free tier is fine to start).
2. Create a new project → pick a region close to your users.
3. Copy the **connection string** (looks like `postgresql://user:password@ep-xxx.neon.tech/neondb?sslmode=require`).

## 2. Deploy to Vercel

1. Push this repo to GitHub.
2. Go to <https://vercel.com> → **New Project** → import the repo.
3. Framework preset: **Other**. Leave build/output settings empty.
4. Set these **environment variables**:

   | Key                | Value                                       |
   |--------------------|---------------------------------------------|
   | `DATABASE_URL`     | your Neon connection string                 |
   | `SECRET_KEY`       | run `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `ANTHROPIC_API_KEY`| your Anthropic key (for OCR menu uploads)   |
   | `JWT_EXPIRY_HOURS` | `168` (optional, default 7 days)            |

5. Click **Deploy**. First deploy takes ~60s.

## 3. First use

- Visit your Vercel URL.
- Click **Create account**. Each new account gets its own private workspace seeded with the starter Tashkent restaurants.
- Multiple users (e.g. different restaurant holdings) can sign up and their data is fully isolated.

## 4. Local development

```bash
pip install -r requirements.txt

# Uses a local SQLite file if DATABASE_URL is unset
export SECRET_KEY=dev-local-secret
export ANTHROPIC_API_KEY=sk-ant-...   # optional, for OCR
python app.py
```

Open <http://localhost:5000>.

## Architecture notes

- **`api/index.py`** — Vercel serverless entry; imports the Flask app from `app.py`.
- **`static/`** — Static assets (HTML, JS, CSS) served by Vercel's CDN.
- **`vercel.json`** — Routes `/api/*` to the Python function, everything else to static files.
- **Multi-tenancy** — Every restaurant, menu item, and price history row is scoped by `user_id`. Queries join through `Restaurant` to enforce ownership.
- **Auth** — Email/password with JWT tokens stored in `localStorage`. Password hashing via `werkzeug.security`.

## Commercialization checklist

When you're ready to charge for this:

1. Add a Stripe subscription gate (free trial → paid tier).
2. Add quotas per plan (number of restaurants tracked, OCR uploads/month).
3. Add a team workspace feature (invite coworkers to the same workspace).
4. Optional: custom domain, SSO, data export.
