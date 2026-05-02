import asyncio
import logging
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from models import Job, JobCreateRequest, JobStep, LogEvent, now_iso  # noqa: E402
from pipeline import ARTIFACTS_ROOT, UPLOADS_ROOT, PipelineRunner  # noqa: E402
from references import list_all as list_references_all  # noqa: E402
from templates import TEMPLATES  # noqa: E402

# Mongo
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI(title="WebForge - Website Transformer Pipeline")
api = APIRouter(prefix="/api")
runner = PipelineRunner(db)

logger = logging.getLogger("webforge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class StatusCheckCreate(BaseModel):
    client_name: str


class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: str = Field(default_factory=now_iso)


@api.get("/")
async def root():
    return {
        "service": "webforge",
        "ok": True,
        "has_vercel_token": bool(os.environ.get("VERCEL_TOKEN")),
        "has_llm_key": bool(os.environ.get("EMERGENT_LLM_KEY")),
    }


@api.post("/status", response_model=StatusCheck)
async def status_create(payload: StatusCheckCreate):
    obj = StatusCheck(client_name=payload.client_name)
    await db.status_checks.insert_one(obj.model_dump())
    return obj


@api.get("/status", response_model=list[StatusCheck])
async def status_list():
    out = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    return out


# ---------------- Jobs ------------------
@api.get("/references")
async def get_references():
    return {"references": list_references_all()}


@api.get("/templates")
async def get_templates():
    # Return lightweight template summaries
    return {
        "count": len(TEMPLATES),
        "templates": [
            {
                "id": t["id"],
                "name": t["name"],
                "layout": t["layout"],
                "hero": t["hero"],
                "motion": t["motion"],
                "palette": t["palette"]["name"],
                "primary": t["palette"]["primary"],
                "bg": t["palette"]["bg"],
                "fonts": f"{t['font_heading']} / {t['font_body']}",
            }
            for t in TEMPLATES
        ],
    }


@api.post("/jobs", response_model=Job)
async def create_job(req: JobCreateRequest, bg: BackgroundTasks):
    url = (req.input_url or "").strip()
    if not url:
        raise HTTPException(400, "input_url required")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    job = Job(input_url=url, reference_url=(req.reference_url or None))
    await db.jobs.insert_one(job.model_dump())
    # start pipeline
    bg.add_task(runner.run, job.id)
    return job


@api.get("/jobs", response_model=list[Job])
async def list_jobs():
    docs = await db.jobs.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return docs


@api.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    doc = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "job not found")
    return doc


@api.get("/jobs/{job_id}/logs")
async def get_logs(job_id: str, limit: int = 400):
    docs = await db.logs.find({"job_id": job_id}, {"_id": 0}).sort("ts", 1).to_list(limit)
    return docs


@api.get("/jobs/{job_id}/events")
async def job_events(job_id: str, request: Request):
    """Server-Sent Events stream of pipeline updates for a job."""

    async def stream():
        q = runner.subscribe(job_id)
        try:
            # Send current state immediately
            doc = await db.jobs.find_one({"id": job_id}, {"_id": 0})
            if doc:
                yield f"event: job\ndata: {Job(**doc).model_dump_json()}\n\n"
            # Historical logs (last 200)
            logs = (
                await db.logs.find({"job_id": job_id}, {"_id": 0})
                .sort("ts", 1)
                .to_list(200)
            )
            for lg in logs:
                import json as _json
                yield f"event: log\ndata: {_json.dumps(lg)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                import json as _json
                mtype = msg.get("type", "message")
                if mtype == "job":
                    yield f"event: job\ndata: {_json.dumps(msg['job'])}\n\n"
                elif mtype == "log":
                    yield f"event: log\ndata: {_json.dumps(msg['event'])}\n\n"
                elif mtype == "done":
                    yield f"event: done\ndata: {_json.dumps({'job_id': job_id})}\n\n"
                    break
                else:
                    yield f"event: message\ndata: {_json.dumps(msg)}\n\n"
        finally:
            runner.unsubscribe(job_id, q)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api.post("/jobs/{job_id}/upload-video")
async def upload_video(job_id: str, file: UploadFile = File(...)):
    doc = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "job not found")
    allowed = {".mp4", ".webm", ".mov"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"only {', '.join(allowed)} allowed")
    asset_id = f"{job_id}_{uuid.uuid4().hex[:8]}{ext}"
    dest = UPLOADS_ROOT / asset_id
    async with aiofiles.open(dest, "wb") as f:
        while True:
            chunk = await file.read(1 << 20)
            if not chunk:
                break
            await f.write(chunk)
    size = dest.stat().st_size
    await db.jobs.update_one(
        {"id": job_id},
        {"$set": {"video_asset_id": asset_id, "video_filename": file.filename, "updated_at": now_iso()}},
    )
    return {"asset_id": asset_id, "size": size, "filename": file.filename}


@api.get("/jobs/{job_id}/artifact/{name}")
async def get_artifact(job_id: str, name: str):
    doc = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "job not found")
    base = Path(doc.get("artifacts_dir") or (ARTIFACTS_ROOT / job_id))
    # Search common locations
    candidates = [
        base / "scrape" / name,
        base / "generated_shots" / name,
        base / "skillui" / name,
        base / name,
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            mt = mimetypes.guess_type(c.name)[0] or "application/octet-stream"
            return FileResponse(str(c), media_type=mt)
    raise HTTPException(404, "artifact not found")


@api.get("/uploads/{asset_id}")
async def get_upload(asset_id: str):
    p = UPLOADS_ROOT / asset_id
    if not p.exists():
        raise HTTPException(404, "not found")
    mt = mimetypes.guess_type(p.name)[0] or "video/mp4"
    return FileResponse(str(p), media_type=mt)


@api.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    await db.jobs.delete_one({"id": job_id})
    await db.logs.delete_many({"job_id": job_id})
    return {"ok": True}


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def _shutdown():
    client.close()
