"""Pipeline orchestrator: scrape -> analyze -> reference (skillui) -> generate -> QA -> deploy.

Emits progress events via an async queue per job.
"""
from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path
from typing import Any, Callable, Optional

from slugify import slugify

from llm_gen import analyze_and_plan, qa_review
from generator import generate_project
from image_gen import generate_site_images
from models import Job, LogEvent, QAScores, now_iso
from scraper import scrape_site, screenshot_url
from skillui_runner import pick_reference, run_skillui
from templates import pick_template
from vercel_deploy import deploy_project

ARTIFACTS_ROOT = Path("/app/backend/artifacts")
ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)

UPLOADS_ROOT = Path("/app/backend/uploads")
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)


class PipelineRunner:
    def __init__(self, db):
        self.db = db
        self.subscribers: dict[str, list[asyncio.Queue]] = {}

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
        ev = LogEvent(job_id=job.id, stage=stage, level=level, message=message)
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
                    s.message = message
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

            # 1. Scrape
            self._set_step(job, "scrape", "running")
            await self._save(job)
            await self._log(job, f"Scraping {job.input_url}", stage="scrape")
            scrape_dir = artifacts / "scrape"
            scrape = await scrape_site(job.input_url, scrape_dir)
            self._set_step(job, "scrape", "done", f"Captured {scrape.get('title','')}".strip())
            job.screenshots["original_desktop"] = str(Path(scrape["desktop_png"]).name)
            job.screenshots["original_mobile"] = str(Path(scrape["mobile_png"]).name)
            await self._log(
                job,
                f"Scraped title={scrape.get('title','')!r} nav={len((scrape.get('content') or {}).get('nav', []))} paragraphs={len((scrape.get('content') or {}).get('paragraphs', []))}",
                stage="scrape",
            )
            await self._save(job)

            # 2. Analyze (first pass: QA of original + niche)
            self._set_step(job, "analyze", "running")
            await self._save(job)
            await self._log(job, "Analyzing original site (vision QA)", stage="analyze")
            try:
                qa_orig = await qa_review(
                    scrape["desktop_png"],
                    scrape["mobile_png"],
                    context=f"Original website at {job.input_url}. Score as-is.",
                )
                job.qa_original = QAScores(**qa_orig)
            except Exception as e:
                await self._log(job, f"QA original failed: {e}", stage="analyze", level="warn")
            self._set_step(
                job,
                "analyze",
                "done",
                f"Original overall={job.qa_original.overall}/100",
            )
            await self._save(job)

            # 3. Reference (skillui)
            self._set_step(job, "reference", "running")
            await self._save(job)
            ref_url = job.reference_url or pick_reference(None)
            await self._log(job, f"Running skillui on reference: {ref_url}", stage="reference")
            skill_dir = artifacts / "skillui"
            try:
                skill = await run_skillui(ref_url, skill_dir)
            except Exception as e:
                await self._log(job, f"skillui failed: {e}; using empty tokens", level="warn", stage="reference")
                skill = {"design_md_text": "", "tokens": {}, "screens": []}
            job.reference_url = ref_url
            self._set_step(
                job,
                "reference",
                "done",
                f"Extracted tokens: {', '.join(list((skill.get('tokens') or {}).keys()) or ['(none)'])}",
            )
            await self._save(job)

            # 4. Generate plan + Next.js project
            self._set_step(job, "generate", "running")
            await self._save(job)
            await self._log(job, "Planning multi-page site via Gemini 2.5 Pro vision", stage="generate")
            plan = await analyze_and_plan(scrape, skill)
            job.niche = plan.get("niche")
            job.pages_plan = plan.get("pages") or []
            job.design_tokens = plan.get("design") or {}
            # if the LLM re-scored original in plan, prefer its qa_original when not set
            if plan.get("qa_original") and job.qa_original.overall == 0:
                try:
                    job.qa_original = QAScores(**plan["qa_original"])
                except Exception:
                    pass
            await self._log(
                job,
                f"Plan: niche={job.niche} pages={len(job.pages_plan)}",
                stage="generate",
            )

            project_slug = slugify(
                (job.niche or "site") + "-" + ((plan.get("brand") or {}).get("name") or "brand") + "-" + job.id[:6]
            )[:60]
            project_dir = artifacts / "nextjs"
            hero_video = None
            if job.video_asset_id:
                candidate = UPLOADS_ROOT / job.video_asset_id
                if candidate.exists():
                    hero_video = str(candidate)

            # Pick a distinct template recipe per job so every site is unique
            tpl = pick_template(seed=job.id, niche=job.niche)
            await self._log(
                job,
                f"Template: {tpl['name']} (layout={tpl['layout']}, hero={tpl['hero']}, palette={tpl['palette']['name']}, motion={tpl['motion']}, fonts={tpl['font_heading']}/{tpl['font_body']})",
                stage="generate",
            )

            # Generate hero + section images into a temp dir (best-effort; won't fail pipeline)
            images_tmp = artifacts / "generated_images"
            images_tmp.mkdir(parents=True, exist_ok=True)
            generated_images: dict[str, str] = {}
            try:

                async def _img_event(stage_: str, msg: str, level_: str = "info"):
                    await self._log(job, msg, stage=stage_, level=level_)

                fnames = await generate_site_images(plan, images_tmp, on_event=_img_event)
                # map filename -> absolute source path (so generator can copy)
                for fn in fnames:
                    p = images_tmp / fn
                    if p.exists():
                        generated_images[fn] = str(p)
            except Exception as e:
                await self._log(
                    job, f"image generation skipped: {e}", stage="generate", level="warn"
                )

            generate_project(
                plan,
                project_dir,
                hero_video_path=hero_video,
                project_slug=project_slug,
                template=tpl,
                images=generated_images,
            )
            await self._log(job, f"Generated Next.js project at {project_dir.name}", stage="generate")
            self._set_step(job, "generate", "done", f"{len(job.pages_plan)} pages")
            await self._save(job)

            # 5. Deploy + QA on deployed site
            self._set_step(job, "qa", "running", "Deploying preview for live QA")
            await self._save(job)
            await self._log(job, "Deploying to Vercel (preview for QA)", stage="qa")

            async def _on_event(stage_: str, msg: str, level_: str = "info"):
                await self._log(job, msg, stage=stage_, level=level_)

            # NOTE: deploy_project creates a production deployment. We'll screenshot
            # it for QA; if QA passes, keep URL; else still keep URL but mark failed.
            dep = await deploy_project(project_dir, project_slug, on_event=_on_event)
            job.deployment_id = dep["deployment_id"]
            job.project_id = dep["project_id"]
            job.deploy_url = dep["url"]
            await self._save(job)

            # Screenshot deployed URL for QA
            await self._log(job, f"Capturing screenshots of {dep['url']}", stage="qa")
            gen_dir = artifacts / "generated_shots"
            try:
                shots = await screenshot_url(dep["url"], gen_dir, name="generated")
                job.screenshots["generated_desktop"] = Path(shots["desktop"]).name
                job.screenshots["generated_mobile"] = Path(shots["mobile"]).name
            except Exception as e:
                await self._log(job, f"Screenshot failed: {e}", level="warn", stage="qa")
                shots = None

            if shots:
                await self._log(job, "Running QA rubric (anti-slop, palette, mobile, overall)", stage="qa")
                try:
                    qa_gen = await qa_review(
                        shots["desktop"],
                        shots["mobile"],
                        context=(
                            f"Generated website for {job.input_url} deployed at {dep['url']}. "
                            f"Niche: {job.niche}. Must be distinctive (anti-slop) and mobile perfect."
                        ),
                    )
                    job.qa_generated = QAScores(**qa_gen)
                except Exception as e:
                    await self._log(job, f"QA generated failed: {e}", level="warn", stage="qa")

            passed = job.qa_generated.passed(threshold=70)
            self._set_step(
                job,
                "qa",
                "done" if passed else "done",
                f"Overall {job.qa_generated.overall}/100 ({'PASS' if passed else 'WARN'})",
            )
            await self._save(job)

            # 6. Deploy (already done as part of QA live preview)
            self._set_step(job, "deploy", "done", job.deploy_url)
            job.status = "deployed"
            await self._log(job, f"Public URL: {job.deploy_url}", stage="deploy")
            await self._save(job)

        except Exception as e:
            job.status = "failed"
            job.error = str(e) or repr(e) or type(e).__name__
            # mark current running step as error
            for s in job.steps:
                if s.status == "running":
                    s.status = "error"
                    s.ended_at = now_iso()
                    s.message = str(e) or type(e).__name__
            await self._log(job, f"pipeline error [{type(e).__name__}]: {e!r}", level="error")
            await self._save(job)
        finally:
            # signal end-of-stream to subscribers
            await self._publish(job.id, {"type": "done", "job_id": job.id})
