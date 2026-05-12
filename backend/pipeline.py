"""Pipeline orchestrator with 11 stages:

  scrape -> analyze -> discover -> reference (skillui) -> plan ->
  review (2-min gate) -> generate -> taste -> qa_desktop -> qa_mobile -> deploy

Emits progress events via an async queue per job.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from slugify import slugify

from component_library import pick_components_for_plan
from discover import discover_references
from generator import generate_project
from image_gen import generate_site_images
from llm_gen import analyze_and_plan, qa_review, qa_review_25k
from models import (
    DiscoveryCandidate,
    Job,
    LogEvent,
    QAScores,
    QAScores25k,
    now_iso,
)
from scraper import scrape_site, screenshot_url
from skillui_runner import pick_reference, run_skillui
from taste_runner import run_taste_skill
from templates import pick_template
from vercel_deploy import deploy_project

_BACKEND_DIR = Path(__file__).resolve().parent
ARTIFACTS_ROOT = Path(os.environ.get("WEBFORGE_ARTIFACTS_DIR") or (_BACKEND_DIR / "artifacts"))
ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)

UPLOADS_ROOT = Path(os.environ.get("WEBFORGE_UPLOADS_DIR") or (_BACKEND_DIR / "uploads"))
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)

REVIEW_WINDOW_SECONDS = int(os.environ.get("REVIEW_WINDOW_SECONDS", "120"))
QA_OVERALL_THRESHOLD = int(os.environ.get("QA_OVERALL_THRESHOLD", "75"))
QA_NO_HUMANS_THRESHOLD = int(os.environ.get("QA_NO_HUMANS_THRESHOLD", "95"))
QA_MOBILE_THRESHOLD = int(os.environ.get("QA_MOBILE_THRESHOLD", "75"))
DISCOVER_ENABLED = os.environ.get("DISCOVER_ENABLED", "1") != "0"


class PipelineRunner:
    def __init__(self, db):
        self.db = db
        self.subscribers: dict[str, list[asyncio.Queue]] = {}
        # Review gate state per job
        self.review_gates: dict[str, dict[str, Any]] = {}

    # --- Pub/Sub for SSE -----------------------------------------------------
    def subscribe(self, job_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        self.subscribers.setdefault(job_id, []).append(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        lst = self.subscribers.get(job_id) or []
        if q in lst:
            lst.remove(q)

    async def _publish(self, job_id: str, payload: dict) -> None:
        for q in list(self.subscribers.get(job_id, [])):
            try:
                q.put_nowait(payload)
            except Exception:
                pass

    # --- Review gate public API ---------------------------------------------
    async def resolve_review(
        self, job_id: str, action: str, plan: Optional[dict] = None
    ) -> bool:
        """Called by the API when the user submits a review decision."""
        gate = self.review_gates.get(job_id)
        if not gate:
            return False
        gate["action"] = action or "accept"
        if plan is not None:
            gate["plan"] = plan
        ev: asyncio.Event = gate["event"]
        ev.set()
        return True

    # --- Persistence helpers -------------------------------------------------
    async def _save(self, job: Job) -> None:
        job.updated_at = now_iso()
        await self.db.jobs.replace_one(
            {"id": job.id}, job.model_dump(), upsert=True
        )
        await self._publish(job.id, {"type": "job", "job": job.model_dump()})

    async def _log(
        self,
        job: Job,
        message: str,
        stage: Optional[str] = None,
        level: str = "info",
    ) -> None:
        # Redact any tokens that may have leaked into logs
        safe = _redact(message)
        ev = LogEvent(job_id=job.id, stage=stage, level=level, message=safe)
        await self.db.logs.insert_one(ev.model_dump())
        await self._publish(job.id, {"type": "log", "event": ev.model_dump()})

    def _set_step(
        self,
        job: Job,
        key: str,
        status: str,
        message: Optional[str] = None,
    ) -> None:
        for s in job.steps:
            if s.key == key:
                s.status = status
                if status == "running" and not s.started_at:
                    s.started_at = now_iso()
                if status in ("done", "error"):
                    s.ended_at = now_iso()
                if message:
                    s.message = message[:500]
                break

    # --- Main pipeline -------------------------------------------------------
    async def run(self, job_id: str) -> None:
        doc = await self.db.jobs.find_one({"id": job_id}, {"_id": 0})
        if not doc:
            return
        job = Job(**doc)
        try:
            job.status = "running"
            await self._save(job)
            artifacts = ARTIFACTS_ROOT / job.id
            artifacts.mkdir(parents=True, exist_ok=True)
            job.artifacts_dir = str(artifacts)

            # 1. SCRAPE
            self._set_step(job, "scrape", "running")
            await self._save(job)
            await self._log(job, f"Scraping {job.input_url}", stage="scrape")
            scrape_dir = artifacts / "scrape"
            scrape = await scrape_site(job.input_url, scrape_dir)
            job.screenshots["original_desktop"] = str(Path(scrape["desktop_png"]).name)
            job.screenshots["original_mobile"] = str(Path(scrape["mobile_png"]).name)
            content = scrape.get("content") or {}
            self._set_step(
                job, "scrape", "done", f"Captured {scrape.get('title', '')[:60]}"
            )
            await self._log(
                job,
                f"Scraped nav={len(content.get('nav', []))} paragraphs={len(content.get('paragraphs', []))}",
                stage="scrape",
            )
            await self._save(job)

            # 2. ANALYZE ORIGINAL (legacy 4-metric rubric — fast sanity check)
            self._set_step(job, "analyze", "running")
            await self._save(job)
            await self._log(job, "Analyzing original site (vision QA)", stage="analyze")
            try:
                qa_orig = await qa_review(
                    scrape["desktop_png"],
                    scrape["mobile_png"],
                    context=f"Original website at {job.input_url}. Score as-is.",
                )
                if qa_orig.get("overall", 0) >= 0:
                    job.qa_original = QAScores(**qa_orig)
            except Exception as e:
                await self._log(job, f"QA original failed: {e}", stage="analyze", level="warn")
            self._set_step(
                job, "analyze", "done", f"Original overall={job.qa_original.overall}/100"
            )
            await self._save(job)

            # Rough niche guess from scraped content; will be refined in plan stage
            niche_guess = _guess_niche(content)
            job.niche = niche_guess

            # 3. DISCOVER (awwwards + godly → best match; cached 7 days in Mongo)
            self._set_step(job, "discover", "running")
            await self._save(job)
            candidates: list[DiscoveryCandidate] = []
            pick: Optional[DiscoveryCandidate] = None
            if DISCOVER_ENABLED and not job.reference_url:
                try:
                    await self._log(
                        job,
                        f"Discovering references on awwwards + godly (niche={niche_guess})",
                        stage="discover",
                    )
                    disc_dir = artifacts / "discovery"
                    res = await discover_references(
                        niche=niche_guess,
                        input_desktop_png=scrape["desktop_png"],
                        out_dir=disc_dir,
                        db=self.db,
                    )
                    candidates = res.get("candidates") or []
                    pick = res.get("pick")
                    job.discovery_candidates = candidates
                    job.discovery_pick = pick
                    if pick:
                        job.reference_url = pick.url
                        await self._log(
                            job,
                            f"Picked {pick.name or pick.url} ({pick.source}) — {pick.reason[:120]}",
                            stage="discover",
                        )
                except Exception as e:
                    await self._log(
                        job, f"discover failed: {e}; falling back to curated list",
                        stage="discover", level="warn",
                    )
            if not job.reference_url:
                job.reference_url = pick_reference(niche_guess)
                await self._log(
                    job,
                    f"Using curated reference: {job.reference_url}",
                    stage="discover",
                )
            self._set_step(
                job, "discover", "done",
                f"{len(candidates)} candidates, picked {job.reference_url}",
            )
            await self._save(job)

            # 4. REFERENCE (skillui → design tokens)
            self._set_step(job, "reference", "running")
            await self._save(job)
            ref_url = job.reference_url
            await self._log(job, f"Running skillui on reference: {ref_url}", stage="reference")
            skill_dir = artifacts / "skillui"
            try:
                skill = await run_skillui(ref_url, skill_dir, db=self.db)
            except Exception as e:
                await self._log(
                    job, f"skillui failed: {e}; using empty tokens",
                    level="warn", stage="reference",
                )
                skill = {"design_md_text": "", "tokens": {}, "screens": []}
            self._set_step(
                job, "reference", "done",
                f"Tokens: {', '.join(list((skill.get('tokens') or {}).keys()) or ['(none)'])}",
            )
            await self._save(job)

            # 5. PLAN (Gemini multi-page plan)
            self._set_step(job, "plan", "running")
            await self._save(job)
            await self._log(job, "Planning multi-page site via Gemini 2.5 Pro", stage="plan")
            plan = await analyze_and_plan(scrape, skill)
            job.niche = plan.get("niche") or niche_guess
            job.pages_plan = plan.get("pages") or []
            job.design_tokens = plan.get("design") or {}
            job.brand = plan.get("brand") or {}
            job.nav_plan = plan.get("nav") or []
            # Pick components from 21st.dev / motionsites library
            try:
                picked = pick_components_for_plan(plan, seed=job.id)
                job.picked_components = picked
                await self._log(
                    job,
                    f"Picked {len(picked)} components: "
                    + ", ".join(p.get("slug", "?") for p in picked[:6])
                    + ("…" if len(picked) > 6 else ""),
                    stage="plan",
                )
            except Exception as e:
                await self._log(job, f"component pick failed: {e}", stage="plan", level="warn")
            self._set_step(
                job, "plan", "done",
                f"niche={job.niche} pages={len(job.pages_plan)}",
            )
            await self._save(job)

            # 6. REVIEW GATE (2-minute window)
            self._set_step(job, "review", "running", f"Awaiting user review ({REVIEW_WINDOW_SECONDS}s)")
            job.status = "awaiting_review"
            deadline = datetime.now(timezone.utc) + timedelta(seconds=REVIEW_WINDOW_SECONDS)
            job.review_deadline = deadline.isoformat()
            await self._save(job)
            await self._log(
                job,
                f"Review gate open — user has {REVIEW_WINDOW_SECONDS}s to accept or edit the plan.",
                stage="review",
            )

            gate = {
                "event": asyncio.Event(),
                "plan": plan,
                "action": "auto",
            }
            self.review_gates[job.id] = gate
            try:
                await asyncio.wait_for(gate["event"].wait(), timeout=REVIEW_WINDOW_SECONDS)
                action = gate.get("action") or "accept"
                if action == "edit" and gate.get("plan"):
                    plan = _merge_plan_edits(plan, gate["plan"])
                    job.pages_plan = plan.get("pages") or job.pages_plan
                    job.design_tokens = plan.get("design") or job.design_tokens
                    job.brand = plan.get("brand") or job.brand
                    job.nav_plan = plan.get("nav") or job.nav_plan
                await self._log(job, f"Review resolved: {action}", stage="review")
                job.review_action = action
            except asyncio.TimeoutError:
                await self._log(
                    job,
                    "Review window elapsed without input. Auto-accepting plan and continuing.",
                    stage="review",
                )
                job.review_action = "auto"
            finally:
                self.review_gates.pop(job.id, None)

            job.status = "running"
            self._set_step(
                job, "review", "done",
                f"Resolved: {job.review_action}",
            )
            await self._save(job)

            # 7. GENERATE (Next.js + images)
            self._set_step(job, "generate", "running")
            await self._save(job)
            project_slug = slugify(
                (job.niche or "site")
                + "-" + ((job.brand or {}).get("name") or "brand")
                + "-" + job.id[:6]
            )[:60] or f"webforge-{job.id[:6]}"
            project_dir = artifacts / "nextjs"
            hero_video: Optional[str] = None
            if job.video_asset_id:
                candidate = UPLOADS_ROOT / job.video_asset_id
                if candidate.exists():
                    hero_video = str(candidate)

            tpl = pick_template(seed=job.id, niche=job.niche)
            await self._log(
                job,
                f"Template: {tpl['name']} (layout={tpl['layout']}, hero={tpl['hero']}, palette={tpl['palette']['name']})",
                stage="generate",
            )

            images_tmp = artifacts / "generated_images"
            images_tmp.mkdir(parents=True, exist_ok=True)
            generated_images: dict[str, str] = {}

            async def _img_event(stage_: str, msg: str, level_: str = "info"):
                await self._log(job, msg, stage=stage_, level=level_)

            try:
                fnames = await generate_site_images(plan, images_tmp, on_event=_img_event)
                for fn in fnames:
                    p = images_tmp / fn
                    if p.exists():
                        generated_images[fn] = str(p)
            except Exception as e:
                await self._log(
                    job, f"image generation skipped: {e}",
                    stage="generate", level="warn",
                )

            generate_project(
                plan,
                project_dir,
                hero_video_path=hero_video,
                project_slug=project_slug,
                template=tpl,
                images=generated_images,
                picked_components=job.picked_components,
            )
            self._set_step(
                job, "generate", "done",
                f"{len(job.pages_plan)} pages, {len(generated_images)} images",
            )
            await self._save(job)

            # 8. TASTE (polish pass via npx taste-skill — non-fatal)
            self._set_step(job, "taste", "running")
            await self._save(job)
            try:
                taste_res = await run_taste_skill(project_dir, on_event=_img_event)
                self._set_step(
                    job, "taste", "done",
                    taste_res.get("summary", "completed")[:140],
                )
            except Exception as e:
                await self._log(
                    job, f"taste-skill skipped: {e}",
                    stage="taste", level="warn",
                )
                self._set_step(job, "taste", "done", "skipped")
            await self._save(job)

            # Deploy (initial) — happens as part of QA because we need the live URL to screenshot
            async def _on_event(stage_: str, msg: str, level_: str = "info"):
                await self._log(job, msg, stage=stage_, level=level_)

            await self._log(job, "Deploying to Vercel for live QA", stage="qa_desktop")
            dep = await deploy_project(project_dir, project_slug, on_event=_on_event)
            job.deployment_id = dep["deployment_id"]
            job.project_id = dep["project_id"]
            job.deploy_url = dep["url"]
            await self._save(job)

            gen_dir = artifacts / "generated_shots"

            async def _capture_and_qa(label: str) -> tuple[Optional[dict], Optional[dict]]:
                """Screenshot deployed site + run desktop & mobile $25k QA."""
                try:
                    shots = await screenshot_url(job.deploy_url, gen_dir, name=label)
                except Exception as e:
                    await self._log(
                        job, f"Screenshot failed: {e}",
                        level="warn", stage="qa_desktop",
                    )
                    return None, None
                job.screenshots["generated_desktop"] = Path(shots["desktop"]).name
                job.screenshots["generated_mobile"] = Path(shots["mobile"]).name
                await self._save(job)

                ctx = (
                    f"Generated website for {job.input_url} deployed at {job.deploy_url}. "
                    f"Niche: {job.niche}. This must look like a $25,000 agency-built site."
                )
                try:
                    qa_desk = await qa_review_25k(
                        shots["desktop"], mode="desktop", context=ctx
                    )
                except Exception as e:
                    await self._log(
                        job, f"desktop QA failed: {e}",
                        level="warn", stage="qa_desktop",
                    )
                    qa_desk = None
                try:
                    qa_mob = await qa_review_25k(
                        shots["mobile"], mode="mobile", context=ctx
                    )
                except Exception as e:
                    await self._log(
                        job, f"mobile QA failed: {e}",
                        level="warn", stage="qa_mobile",
                    )
                    qa_mob = None
                return qa_desk, qa_mob

            # 9. QA DESKTOP
            self._set_step(job, "qa_desktop", "running")
            await self._save(job)
            qa_desk, qa_mob = await _capture_and_qa("generated")
            if qa_desk:
                job.qa_generated = QAScores25k(**_sanitize_qa(qa_desk))
            self._set_step(
                job, "qa_desktop", "done",
                f"Overall {job.qa_generated.overall}/100 · no_humans {job.qa_generated.no_humans_in_images}/100 · no_overlap {job.qa_generated.no_overlap}/100",
            )
            await self._save(job)

            # 10. QA MOBILE
            self._set_step(job, "qa_mobile", "running")
            await self._save(job)
            if qa_mob:
                job.qa_mobile = QAScores25k(**_sanitize_qa(qa_mob))
            self._set_step(
                job, "qa_mobile", "done",
                f"Mobile overall {job.qa_mobile.overall}/100",
            )
            await self._save(job)

            # Redo loop: if QA failed thresholds, regenerate ONCE with feedback
            need_retry = (
                (0 < job.qa_generated.overall < QA_OVERALL_THRESHOLD)
                or (0 < job.qa_generated.no_humans_in_images < QA_NO_HUMANS_THRESHOLD)
                or (0 < job.qa_mobile.overall < QA_MOBILE_THRESHOLD)
            )
            if need_retry and not getattr(job, "_retried", False):
                feedback_parts = [
                    f"Desktop notes: {job.qa_generated.notes or ''}",
                    f"Mobile notes: {job.qa_mobile.notes or ''}",
                ]
                if job.qa_generated.no_humans_in_images < QA_NO_HUMANS_THRESHOLD:
                    feedback_parts.append(
                        "CRITICAL: Remove ALL humans/people/faces/portraits from all imagery. "
                        "Use only abstract, architectural, product, or environmental photography."
                    )
                feedback = " | ".join(feedback_parts)[:600]
                await self._log(
                    job,
                    f"QA below threshold. Retrying with feedback: {feedback[:200]}",
                    stage="qa_desktop", level="warn",
                )

                plan2 = dict(plan)
                plan2.setdefault("design", {})
                plan2["design"]["style_notes"] = (
                    (plan2["design"].get("style_notes") or "") + f" FIXES: {feedback}"
                )
                # NO_HUMANS is already a hard constraint in image_gen; retry only sharpens
                # the style notes feedback.

                images_tmp2 = artifacts / "generated_images_v2"
                images_tmp2.mkdir(parents=True, exist_ok=True)
                try:
                    fnames2 = await generate_site_images(
                        plan2, images_tmp2, on_event=_img_event
                    )
                    generated_images = {}
                    for fn in fnames2:
                        p = images_tmp2 / fn
                        if p.exists():
                            generated_images[fn] = str(p)
                except Exception as e:
                    await self._log(
                        job, f"retry image gen failed: {e}",
                        stage="generate", level="warn",
                    )

                tpl2 = pick_template(seed=job.id + "_retry", niche=job.niche)
                generate_project(
                    plan2,
                    project_dir,
                    hero_video_path=hero_video,
                    project_slug=project_slug,
                    template=tpl2,
                    images=generated_images,
                    picked_components=job.picked_components,
                )
                dep2 = await deploy_project(
                    project_dir, project_slug + "-v2", on_event=_on_event
                )
                job.deployment_id = dep2["deployment_id"]
                job.project_id = dep2["project_id"]
                job.deploy_url = dep2["url"]
                await self._save(job)

                qa_desk2, qa_mob2 = await _capture_and_qa("generated-v2")
                if qa_desk2:
                    job.qa_generated = QAScores25k(**_sanitize_qa(qa_desk2))
                if qa_mob2:
                    job.qa_mobile = QAScores25k(**_sanitize_qa(qa_mob2))
                job._retried = True
                await self._save(job)

            # 11. DEPLOY (already happened; just finalize step status)
            self._set_step(job, "deploy", "done", job.deploy_url or "deployed")
            job.status = "deployed"
            await self._log(job, f"Public URL: {job.deploy_url}", stage="deploy")
            await self._save(job)

        except Exception as e:
            job.status = "failed"
            job.error = str(e) or repr(e) or type(e).__name__
            for s in job.steps:
                if s.status == "running":
                    s.status = "error"
                    s.ended_at = now_iso()
                    s.message = (str(e) or type(e).__name__)[:400]
            await self._log(
                job, f"pipeline error [{type(e).__name__}]: {_redact(str(e))[:400]}",
                level="error",
            )
            await self._save(job)
        finally:
            self.review_gates.pop(job_id, None)
            await self._publish(job.id, {"type": "done", "job_id": job.id})


# --- helpers ---------------------------------------------------------------

_NICHE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("ai", ("ai", "gpt", "ml", "llm", "neural", "bot", "agent")),
    ("developer-tools", ("api", "sdk", "cli", "devops", "github", "deploy", "docker")),
    ("saas", ("saas", "platform", "dashboard", "workspace", "b2b")),
    ("fintech", ("bank", "finance", "invoice", "payment", "payroll", "money")),
    ("ecommerce", ("shop", "store", "cart", "checkout", "product")),
    ("agency", ("agency", "studio", "creative", "branding", "design")),
    ("portfolio", ("portfolio", "freelance", "my work", "about me")),
    ("creator", ("newsletter", "substack", "podcast", "youtube")),
    ("hardware", ("hardware", "device", "headphone", "speaker", "camera")),
]


def _guess_niche(content: dict) -> str:
    text = " ".join(
        [
            content.get("title") or "",
            content.get("description") or "",
            " ".join(h.get("text", "") for h in content.get("headings", [])[:12]),
            " ".join(content.get("paragraphs", [])[:6]),
        ]
    ).lower()
    for niche, kws in _NICHE_KEYWORDS:
        if any(k in text for k in kws):
            return niche
    return "saas"


def _merge_plan_edits(orig: dict, edits: dict) -> dict:
    """Merge user-submitted plan edits onto the original plan."""
    out = dict(orig)
    for k in ("brand", "design"):
        if isinstance(edits.get(k), dict):
            out[k] = {**(orig.get(k) or {}), **edits[k]}
    for k in ("pages", "nav", "niche"):
        if edits.get(k):
            out[k] = edits[k]
    return out


def _sanitize_qa(d: dict) -> dict:
    """Clamp QA scores to ints 0-100 and normalize boxes."""
    out: dict[str, Any] = {}
    int_fields = (
        "distinct_design",
        "typography_hierarchy",
        "palette_cohesion",
        "spacing_rhythm",
        "no_overlap",
        "no_humans_in_images",
        "copy_quality",
        "premium_feel",
        "overall",
    )
    for k in int_fields:
        try:
            v = int(d.get(k, 0))
        except Exception:
            v = 0
        out[k] = max(0, min(100, v))
    out["notes"] = (d.get("notes") or "").strip()[:900]
    # Normalize boxes
    def _boxes(raw: Any) -> list[dict]:
        if not isinstance(raw, list):
            return []
        result = []
        for b in raw[:20]:
            if not isinstance(b, dict):
                continue
            try:
                result.append(
                    {
                        "x": float(b.get("x", 0)),
                        "y": float(b.get("y", 0)),
                        "w": float(b.get("w", b.get("width", 0))),
                        "h": float(b.get("h", b.get("height", 0))),
                        "label": str(b.get("label") or b.get("explanation") or "")[:120],
                    }
                )
            except Exception:
                continue
        return result

    out["overlap_regions"] = _boxes(d.get("overlap_regions"))
    out["human_detections"] = _boxes(d.get("human_detections"))
    return out


def _redact(s: str) -> str:
    """Mask anything that looks like a Vercel or Google API token."""
    if not s:
        return s
    import re as _re

    # Vercel tokens: vcp_... or vercel_...
    s = _re.sub(r"(vcp|vercel)_[A-Za-z0-9]{20,}", "vcp_***REDACTED***", s)
    # Google AI Studio keys
    s = _re.sub(r"AIza[0-9A-Za-z_\-]{20,}", "AIza***REDACTED***", s)
    # sk-... style
    s = _re.sub(r"sk-[A-Za-z0-9_\-]{20,}", "sk-***REDACTED***", s)
    return s
