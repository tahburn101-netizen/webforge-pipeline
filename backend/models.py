from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
import uuid

from pydantic import BaseModel, Field, ConfigDict


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


STAGES = [
    "scrape",
    "analyze",
    "reference",
    "generate",
    "qa",
    "deploy",
]

STAGE_LABELS = {
    "scrape": "Scrape",
    "analyze": "Analyze",
    "reference": "Reference Match",
    "generate": "Generate Next.js",
    "qa": "QA Gates",
    "deploy": "Deploy",
}


class JobStep(BaseModel):
    key: str
    label: str
    status: str = "pending"  # pending | running | done | error
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    message: Optional[str] = None

    @classmethod
    def default_steps(cls) -> list["JobStep"]:
        return [cls(key=k, label=STAGE_LABELS[k]) for k in STAGES]


class QAScores(BaseModel):
    anti_slop: int = 0
    palette: int = 0
    mobile: int = 0
    overall: int = 0
    notes: str = ""

    def passed(self, threshold: int = 70) -> bool:
        return all(
            v >= threshold for v in (self.anti_slop, self.palette, self.mobile, self.overall)
        )


class Job(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_url: str
    reference_url: Optional[str] = None
    niche: Optional[str] = None
    status: str = "queued"  # queued | running | qa_passed | deploying | deployed | failed
    steps: list[JobStep] = Field(default_factory=JobStep.default_steps)
    qa_original: QAScores = Field(default_factory=QAScores)
    qa_generated: QAScores = Field(default_factory=QAScores)
    deploy_url: Optional[str] = None
    deployment_id: Optional[str] = None
    project_id: Optional[str] = None
    video_asset_id: Optional[str] = None
    video_filename: Optional[str] = None
    error: Optional[str] = None
    pages_plan: list[dict] = Field(default_factory=list)
    design_tokens: dict = Field(default_factory=dict)
    artifacts_dir: Optional[str] = None
    screenshots: dict = Field(default_factory=dict)  # original/generated desktop/mobile URLs
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class JobCreateRequest(BaseModel):
    input_url: str
    reference_url: Optional[str] = None


class LogEvent(BaseModel):
    job_id: str
    ts: str = Field(default_factory=now_iso)
    level: str = "info"  # info | warn | error
    stage: Optional[str] = None
    message: str
    data: Optional[dict[str, Any]] = None
