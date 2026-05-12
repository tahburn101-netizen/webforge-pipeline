# Deploying WebForge as a public service

Everything below uses free tiers. Total recurring cost: **$0** (within quotas).

## Architecture

```
 Vercel (frontend, free Hobby tier)
    │
    │ HTTPS  REACT_APP_BACKEND_URL
    ▼
 Render / Railway / Fly.io (backend Docker, free tier)
    │
    ├─► MongoDB Atlas M0 (free 512 MB)  — jobs, logs, caches
    │
    ├─► Google AI Studio (Gemini 2.5 Pro + Nano Banana, free daily quota)
    │
    └─► Vercel REST API (your Vercel token, Hobby deploys are unlimited)
```

## 1. MongoDB Atlas (free M0)

1. Sign up at https://www.mongodb.com/atlas → create M0 free cluster.
2. Database Access → add a user with a strong password.
3. Network Access → allow `0.0.0.0/0` (or lock to your host's IP).
4. Copy the connection string. It looks like `mongodb+srv://USER:PASS@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority`.

## 2. Backend on Render (free starter)

1. Fork this repository on GitHub.
2. https://dashboard.render.com → **New → Blueprint** → select your fork.
3. Render reads `render.yaml` and creates the web service.
4. In the service's **Environment** tab, set:
   - `MONGO_URL` = your Atlas connection string
   - `GOOGLE_API_KEY` = from https://aistudio.google.com/apikey
   - `VERCEL_TOKEN` = from https://vercel.com/account/tokens
5. Deploy. First build is ~6 min (installs Chromium + skillui).
6. Note the public URL: `https://webforge-backend.onrender.com` (or similar).

Render free tier sleeps after 15 min of inactivity — the first request after sleep takes ~30 s. Upgrade to a paid plan ($7/mo) to eliminate cold starts.

### Alt: Railway / Fly.io

Both auto-detect `backend/Dockerfile`. Set the same env vars. Railway free tier gives $5 credit/month. Fly.io free tier includes 3 small VMs.

## 3. Frontend on Vercel

1. In Vercel, **Import Project** → point at your GitHub fork.
2. **Root Directory** = `frontend`.
3. Framework preset = Create React App (auto-detected via `vercel.json`).
4. Environment variables:
   - `REACT_APP_BACKEND_URL` = your Render backend URL (no trailing slash)
5. Deploy.

## 4. Domain (optional)

Point your domain at the Vercel project in **Settings → Domains**. Vercel handles SSL automatically.

## 5. Cost & quota notes

| Resource | Free tier | Expected usage / job | Jobs/month for free |
|---|---|---|---|
| Gemini 2.5 Pro (plan + QA) | ~50 calls/day free | 4-6 calls | ~8-12 jobs/day |
| Gemini Flash (discover pick) | 1500/min, 250/day | 1 call | ample |
| Nano Banana images | shared with above | 3-5 images | ~50-80 images/day |
| Vercel Hobby deploys | unlimited | 1-2 deploys | ample |
| Render starter | 750 hrs/mo | continuous | works 24/7 |
| Mongo Atlas M0 | 512 MB | ~200 KB/job | ~2500 jobs stored |

The `RATE_LIMIT_PER_HOUR` env var (default 12) caps how many jobs a single IP can start per hour — protects the Gemini quota on a public deployment.

## 6. Security checklist

- `.env` is git-ignored. Never commit it.
- Logs auto-redact `vcp_*`, `AIza*`, `sk-*` tokens.
- Set `CORS_ORIGINS` to your Vercel frontend URL in production (not `*`).
- Enable Atlas IP allowlist once you know your Render egress IPs.
- Consider adding Cloudflare Turnstile to the frontend submit button if abuse rises (template in `frontend/src/pages/PipelinePage.jsx`).
