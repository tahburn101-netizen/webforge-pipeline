# WebForge — AI Website Transformation Pipeline

> Paste any website URL → get back a beautiful, multi-page Next.js site with a video / exploding hero, AI-generated images, QA gates, and a publicly shareable Vercel deployment in ~2 minutes.

![status](https://img.shields.io/badge/status-MVP-2DE3C6) ![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Next.js%20%2B%20MongoDB-0EA5A4) ![deploy](https://img.shields.io/badge/deploys-Vercel-000000)

WebForge ingests a (usually mediocre) source website, reverse-engineers the design system of a beautiful reference site in the same niche via [`skillui`](https://github.com/amaancoderx/npxskillui), regenerates a brand-new multi-page Next.js 14 project with a distinct **template recipe** out of a library of 50, generates hero + section images with **Gemini Nano Banana**, runs vision-based QA on desktop & mobile, then deploys to Vercel with deployment protection automatically disabled so the link is publicly shareable.

## Features

- End-to-end pipeline with live SSE progress (6 stages: Scrape → Analyze → Reference → Generate → QA → Deploy)
- Vision-driven analysis (Gemini 2.5 Pro reads desktop & mobile screenshots)
- `skillui` reverse-engineers design tokens from a beautiful reference site in the same niche
- Curated reference library (19+ premium sites) + 50 distinct template recipes
- 17 hero archetypes incl. exploding video, full-bleed parallax, framed split, architectural cursor-tilt, portrait mega-type, archway frame, diorama parallax, product float, 3D orb, perspective stack, marquee, kinetic type, …
- Live image generation with **Gemini Nano Banana** (`gemini-3.1-flash-image-preview`) — hero + section illustrations embedded in `/public/`
- Multi-page output (Home + Features/Pricing/About/Blog/Docs/Case studies/Contact)
- 16+ section kinds (feature_grid, stats, testimonials, pricing, FAQ, CTA, gallery, team, timeline, contact_form, blog, docs, case_studies …)
- Vision QA gates: anti_slop, palette, mobile, overall (0–100)
- Vercel deploy with **auto-disabled** `ssoProtection` & `passwordProtection` → public URL works without login
- Hero video upload (4K MP4/WEBM/MOV)
- Skillui cache (72h TTL in MongoDB)
- **Provider-agnostic LLM** — works with Emergent's Universal LLM Key OR your own Google/OpenAI/Anthropic keys

## Architecture

```
React + Vite (shadcn/ui + Framer Motion)  ←→  FastAPI + Playwright + skillui CLI
                                                      ↓
                             MongoDB (jobs, logs, skillui_cache)
                                                      ↓
        Gemini 2.5 Pro (Emergent or direct) + Nano Banana (image gen)
                                                      ↓
                        Vercel REST API (/v13/deployments + /v9/projects)
```

## Quick start

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/webforge.git
cd webforge

cd backend
pip install -r requirements.txt
playwright install chromium       # required for scraping
npm install -g skillui            # required for reference design extraction

cd ../frontend
yarn install
```

### 2. Configure environment

Copy `.env.example` → `backend/.env` and fill in:

```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="webforge_db"
CORS_ORIGINS="*"

# REQUIRED for deployment
VERCEL_TOKEN="vcp_xxxxxxxxxxxxxxxxxxxxxxxx"

# Path A — Emergent Universal LLM Key (one key for everything)
EMERGENT_LLM_KEY="sk-emergent-xxxxxxxxxxxxxxxx"

# Path B — Direct Google key (works WITHOUT Emergent)
# GOOGLE_API_KEY="AIza..."
```

### 3. Run

```bash
# Terminal 1 — MongoDB
mongod --dbpath ./.data

# Terminal 2 — Backend
cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3 — Frontend
cd frontend && yarn start
```

Open http://localhost:3000 → paste a URL → watch the live pipeline.

## Required credentials

| Key | Purpose | Where |
|---|---|---|
| `VERCEL_TOKEN` | Programmatic deployments | https://vercel.com/account/tokens |
| `EMERGENT_LLM_KEY` *(option A)* | Universal Gemini/OpenAI/Claude key | https://app.emergent.sh → Profile → Universal Key |
| `GOOGLE_API_KEY` *(option B)* | Direct Gemini + Nano Banana | https://aistudio.google.com/apikey |

> Minimum: `VERCEL_TOKEN` + ONE of the LLM keys.

## Run **without** Emergent

WebForge ships with `backend/llm_provider.py` that auto-switches between providers. When `EMERGENT_LLM_KEY` is missing, it uses `google-genai` SDK with `GOOGLE_API_KEY` for both text (`gemini-2.5-pro`) and image generation (`gemini-3.1-flash-image-preview`).

```bash
# In backend/.env
unset EMERGENT_LLM_KEY
GOOGLE_API_KEY="AIza..."
VERCEL_TOKEN="vcp_..."
```

Restart backend. Done.

## Live test (POC)

```bash
python tests/test_core.py
```

Validates Playwright + skillui + Gemini 2.5 Pro vision + Vercel deploy in ~90s.

## REST API

Base: `${REACT_APP_BACKEND_URL}/api`

| Method | Path | Description |
|---|---|---|
| POST | `/jobs` | Create job: `{input_url, reference_url?}` |
| GET  | `/jobs/{id}` | Job details |
| GET  | `/jobs/{id}/events` | **SSE** progress stream |
| POST | `/jobs/{id}/upload-video` | Upload hero video |
| GET  | `/references` | Curated reference library |
| GET  | `/templates` | 50 template recipes |

## Template registry

50 recipes mixing 8 layouts × 17 heroes × 6 motion packs × 10 decor kinds × 16 palette moods × 20 typography pairings — picked deterministically by `hash(job_id + niche)`. Every transformation is unique but reproducible.

## Security

- Never commit `.env`. Use `.env.example`.
- Rotate Vercel & GitHub tokens if shared publicly.
- Generated sites have `ssoProtection` disabled by design (intended for shareable demos).

## Credits

- [`skillui`](https://github.com/amaancoderx/npxskillui) — design system reverse-engineering CLI
- [Emergent](https://emergent.sh) — universal LLM key
- Hero archetype inspiration: **@neuwebstudio** on TikTok
- shadcn/ui • Framer Motion • Tailwind • lucide-react • Next.js 14

## License

MIT
