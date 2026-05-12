# WebForge — AI Website Transformation Pipeline

> Paste any website URL → get back a fully-designed multi-page Next.js site, a 2-minute review window to edit the plan, a `$25k`-rubric QA pass (no humans in images, no overlaps, mobile-perfect), and a publicly shareable Vercel deployment.

## Pipeline (11 stages)

```
1.  SCRAPE        — Playwright: HTML + desktop + mobile screenshots
2.  ANALYZE       — Gemini vision QA of the original site
3.  DISCOVER      — scrape awwwards.com + godly.website for similar sites
                    → Gemini picks the best match for the niche
4.  REFERENCE     — skillui reverse-engineers the reference's design tokens
5.  PLAN          — Gemini 2.5 Pro produces multi-page plan (brand, palette,
                    pages, sections) and the 21st.dev/motionsites-inspired
                    component library picks drop-in components per section
6.  REVIEW (2m)   — user has 120s to accept / edit / skip. Auto-continues.
7.  GENERATE      — Next.js 14 project + Nano Banana images (NO HUMANS prompt)
                    + drop-in picked components written into components/generated/
8.  TASTE         — best-effort `npx taste-skill --project <dir>` polish pass
9.  QA DESKTOP    — $25k rubric (8 metrics incl. no_overlap, no_humans_in_images,
                    premium_feel) with 3 zoom crops (top/mid/bot) for small-detail checks
10. QA MOBILE     — dedicated mobile gate on the same rubric
11. DEPLOY        — Vercel with SSO/password protection auto-disabled for a
                    publicly shareable URL
```

If desktop overall, mobile overall, or no_humans_in_images scores below thresholds, the pipeline regenerates images + project + redeploys ONCE with reviewer feedback injected.

## $25k QA rubric (0-100)

- `distinct_design` — clear POV, not generic AI-slop
- `typography_hierarchy` — scale, pairing, rhythm
- `palette_cohesion` — feels like one brand; accessible contrast
- `spacing_rhythm` — generous whitespace
- `no_overlap` — no elements overlap/clip/truncate
- `no_humans_in_images` — ZERO humans/faces/portraits in any imagery
- `copy_quality` — concrete, no lorem
- `premium_feel` — would a $25k agency ship this
- `overall` — honest gestalt

Plus structured `overlap_regions` and `human_detections` (normalized bboxes) shown as red/amber overlays in the before/after viewer.

## Stack

- **Backend:** FastAPI + Motor (Mongo) + Playwright + google-genai
- **Frontend:** React 19 + CRA (craco) + Tailwind + shadcn/ui + framer-motion
- **LLM:** Gemini 2.5 Pro (text+vision) + Gemini Nano Banana (images) via `GOOGLE_API_KEY` (free tier)
- **Optional:** Emergent Universal LLM Key (skip Google key in that case)
- **Design extraction:** [`skillui`](https://github.com/amaancoderx/npxskillui) (`npm i -g skillui`)
- **Polish:** [`taste-skill`](https://github.com/leonxlnx/taste-skill) (`npx taste-skill` — best-effort, optional)
- **Deploy:** Vercel REST API with auto-disable of `ssoProtection` + `passwordProtection`

## Quick start (free tier)

1. Clone and install:

   ```bash
   git clone <this repo>
   cd webforge
   cd backend && pip install -r requirements.txt && playwright install chromium
   npm install -g skillui
   cd ../frontend && yarn install
   ```

2. Create `backend/.env` (git-ignored):

   ```env
   MONGO_URL="mongodb://localhost:27017"
   DB_NAME="webforge_db"
   CORS_ORIGINS="*"

   # Free Google AI Studio key — https://aistudio.google.com/apikey
   GOOGLE_API_KEY="AIza..."

   # Vercel Hobby token — https://vercel.com/account/tokens
   VERCEL_TOKEN="vcp_..."

   # Tunable defaults
   REVIEW_WINDOW_SECONDS=120
   QA_OVERALL_THRESHOLD=75
   QA_NO_HUMANS_THRESHOLD=95
   QA_MOBILE_THRESHOLD=75
   DISCOVER_ENABLED=1
   DISCOVER_CACHE_HOURS=168
   ```

3. Run:

   ```bash
   # Terminal 1
   mongod --dbpath ./.data

   # Terminal 2
   cd backend && uvicorn server:app --port 8001 --reload

   # Terminal 3
   cd frontend && yarn start
   ```

4. Open http://localhost:3000 → paste any URL → watch 11-stage pipeline → review the plan in the 2-minute window → get a public Vercel URL.

## REST API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/` | health + provider flags |
| `GET` | `/api/references` | curated reference library |
| `GET` | `/api/templates` | 50 template recipes |
| `GET` | `/api/components` | 21st.dev/motionsites-inspired component library |
| `POST` | `/api/jobs` | start job `{input_url, reference_url?}` |
| `GET` | `/api/jobs/:id` | job details |
| `GET` | `/api/jobs/:id/events` | **SSE** live stream |
| `POST` | `/api/jobs/:id/review` | resolve the 2-min review gate `{action: accept\|edit\|skip, plan?}` |
| `POST` | `/api/jobs/:id/upload-video` | upload hero video |

## Security

- `.env` is git-ignored. Do not commit it.
- Logs auto-redact `vcp_*`, `AIza*`, and `sk-*` tokens before persistence or SSE fan-out.
- Deployed sites have Vercel SSO/password protection disabled BY DESIGN so the link is shareable without login.

## Credits & inspiration

- [skillui](https://github.com/amaancoderx/npxskillui) — design-system reverse-engineering CLI
- [taste-skill](https://github.com/leonxlnx/taste-skill) — polish pass CLI
- Component recipes in `backend/data/component_library.json` are **inspired by** patterns commonly seen on [21st.dev](https://21st.dev) and [motionsites.ai](https://motionsites.ai) — all JSX in this library is written from scratch, not copied.

## License

MIT
