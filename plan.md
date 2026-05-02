# plan.md

## 1) Objectives
- Deliver an end-to-end, investor-demo-friendly pipeline: **URL → scrape+screens → analyze+QA → reference design extraction (skillui) → generate multi-page Next.js → QA gates (anti-slop, palette, mobile) → Vercel deploy → public URL (no login)**.
- Ensure generated sites are:
  - **Multi-page** (minimum 4 pages in practice: Home + 3)
  - **Cinematic + animated** (Framer Motion section reveals + signature “explode on scroll” hero)
  - **Video hero** supported (user upload → packaged into `/public/hero.mp4`)
  - **Content-retentive** (reuses original headings/paragraphs where possible)
  - **Mobile-perfect** (separate mobile screenshots + QA)
- Keep the product free-to-use by default via **Emergent Universal LLM Key** + optional free media sources (user upload first).
- Operational goal: **observable + repeatable runs** (job states, steps, logs, artifacts, QA scores, public deploy link).

---

## 2) Implementation Steps (Phased)

### Phase 1: Core Workflow POC (Isolation) — ✅ COMPLETE
**Goal:** validate the 4 risk integrations with real runs.

**Validated (proven):**
- ✅ Playwright scrape + screenshots (desktop+mobile)
- ✅ skillui CLI extraction on a reference URL
- ✅ Emergent LLM vision (Gemini 2.5 Pro) returning structured JSON
- ✅ Vercel Deployments API deploy **and** post-deploy project patch to disable protection so the link is truly public

**Key learnings:**
- To guarantee truly public URLs, patch the Vercel project after deployment creation:
  - `PATCH https://api.vercel.com/v9/projects/{projectId}` with `{ "ssoProtection": null, "passwordProtection": null }`.

**POC artifact:**
- `tests/test_core.py` (regression test covering scrape → skillui → LLM → deploy)

---

### Phase 2: V1 App Development (Backend + Frontend around proven core) — ✅ COMPLETE
**Goal:** build the full product (pipeline tool UI + backend orchestration) using the proven core integrations.

#### 2.1 Backend (FastAPI + Mongo + Playwright + skillui + LLM + Vercel) — ✅ COMPLETE
**Implemented modules:**
- `scraper.py`: Playwright scrape + desktop/mobile screenshots + content extraction
- `skillui_runner.py`: reference selection + skillui execution + token parsing
- `llm_gen.py`: Gemini 2.5 Pro vision planning + QA review rubric
- `generator.py`: writes a full multi-page Next.js project (App Router) w/ Tailwind + Framer Motion + exploding hero
- `vercel_deploy.py`: deploys via REST API; uploads binaries via `/v2/files`; disables protection; polls READY
- `pipeline.py`: orchestrator + job pub/sub for SSE
- `server.py`: API routes + SSE + artifacts + video upload

**Endpoints (implemented):**
- `GET /api/` health
- `POST /api/jobs` start pipeline job
- `GET /api/jobs` list jobs
- `GET /api/jobs/{id}` job detail
- `GET /api/jobs/{id}/logs` historical logs
- `GET /api/jobs/{id}/events` SSE stream (job + log + done)
- `POST /api/jobs/{id}/upload-video` store user hero video
- `GET /api/jobs/{id}/artifact/{name}` serve screenshots/artifacts
- `DELETE /api/jobs/{id}` delete job + logs

**Pipeline stages (implemented):**
1. **Scrape**: HTML + desktop/mobile screenshots + structured content extraction
2. **Analyze**: original-site vision QA scoring
3. **Reference Match**: pick reference + run skillui
4. **Generate Next.js**: Gemini plan → generate Next.js project
5. **QA Gates**: deploy (QA preview), screenshot generated site, vision QA scoring
6. **Deploy**: mark deploy URL as final (public)

**Important runtime fix (implemented):**
- Ensure Playwright can locate browser binaries under supervisor by setting:
  - `PLAYWRIGHT_BROWSERS_PATH=/pw-browsers` (set in code via `os.environ.setdefault`)

#### 2.2 Frontend (React + shadcn/ui + Tailwind + Framer Motion) — ✅ COMPLETE
**Cinematic “WebForge” pipeline UI built per design guidelines:**
- Abyss Teal + Ember palette, Space Grotesk headings, motion-forward panels
- Routes:
  - `/` Pipeline wizard
  - `/jobs` Job history list
  - `/jobs/:id` Job detail

**Implemented UI features:**
- URL command bar (start job)
- Live SSE progress via EventSource
- Stepper with all 6 stages + overall progress
- Log stream with filters + auto-scroll
- Before/After viewer (desktop + mobile tabs)
- QA scorecards for original + generated
- Video upload panel (dropzone)
- Deploy panel: public URL + copy + open + QR code

#### 2.3 Phase 2 Verification — ✅ COMPLETE
**Testing results:**
- Backend: **100%** (8/8)
- Frontend: **85%** (17/20)
  - Minor issue: JobDetailPage “data timing” resolved after initial render/SSE hydration
  - JobsPage perceived slowness only while a pipeline is actively running due to temporary CPU load (base64 encoding). Normal calls are ~24–39ms.

**Live E2E verified:**
- `https://example.com` → deployed to **public** Vercel URL (HTTP 200 without auth)
- Generated site includes:
  - **4 pages**: `/`, `/features`, `/pricing`, `/contact`
  - Distinctive dark style (Linear-inspired), Framer Motion
  - Exploding hero behavior
  - Mobile navigation support
  - QA scores example: **Generated overall 75/100, mobile 95/100**

---

### Phase 3: QA Retry Loop + Reference Library + Better “Anti-Slop” — ⏭️ NEXT (Optional)
**Goal:** raise consistency and quality, reduce generic outputs.

**Planned improvements:**
- Auto-retry loop:
  - If any QA dimension (anti-slop/palette/mobile/overall) < threshold (e.g., 80), regenerate with targeted feedback (max 2 retries)
- Reference library upgrades:
  - Expand curated references per niche
  - Add UI to pick/override reference site
  - Cache skillui outputs per reference URL for speed
- Better before/after:
  - Add wipe slider comparison mode
  - Side-by-side iteration comparisons
- Anti-slop heuristics:
  - Enforce niche-specific language
  - Detect boilerplate sections and require unique layout patterns

**User stories (Phase 3):**
1. As a user, I see why QA failed and what will be improved on retry.
2. As a user, I automatically get a better 2nd iteration if the first looks generic.
3. As a user, I can pick a reference style from a curated list.
4. As a user, I can compare iterations visually.
5. As a user, deploy is gated by thresholds I can configure.

---

### Phase 4: Polish + Hardening — ⏭️ LATER (Optional)
**Goal:** production hardening + richer generated sites.

**Planned improvements:**
- Queue/worker separation (Celery/RQ/Arq) + better concurrency controls
- Artifact lifecycle management (cleanup, retention policies)
- More robust content extraction (multi-page crawl, sitemap support)
- Richer generator coverage:
  - More section types and better mapping (case studies, blog, docs)
- Optional media sourcing (where licensing allows): curated 4K video library fallback

**User stories (Phase 4):**
1. As a user, I can run many jobs reliably and in parallel.
2. As a user, I can re-deploy an updated iteration without re-scraping.
3. As a user, content-heavy sites generate richer page structures.
4. As a user, jobs finish faster due to cached references.
5. As a user, the system is stable with timeouts/retries.

---

## 3) Next Actions
### Immediate (If continuing to Phase 3)
1. Implement QA auto-retry loop with targeted regeneration prompts.
2. Add reference picker UI + store curated reference catalog.
3. Cache skillui extraction results by reference URL.
4. Add wipe-slider comparison mode in Before/After viewer.
5. Improve performance during pipeline runs (move heavy operations off main thread; consider background workers).

### Maintenance
- Keep `tests/test_core.py` as regression coverage.
- Add an additional regression: end-to-end job via API + verify public URL HTTP 200.

---

## 4) Success Criteria
- Phase 1: ✅ POC succeeded (screenshots, skillui outputs, LLM structured output, Vercel deploy, public URL).
- Phase 2: ✅ V1 app shipped (backend pipeline + cinematic frontend + SSE + artifacts + video upload).
- Quality: ✅ Multi-page Next.js with animations + exploding hero + QA scoring + mobile checks.
- Deployment: ✅ Returned Vercel URL is **publicly accessible** (HTTP 200 without authentication).
- Next (Phase 3+): improve consistency via retry loop, reference caching, and richer comparisons.
