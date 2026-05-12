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
    "discover",
    "reference",
    "plan",
    "review",
    "generate",
    "taste",
    "qa_desktop",
    "qa_mobile",
    "deploy",
]

STAGE_LABELS = {
    "scrape": "Scrape",
    "analyze": "Analyze Original",
    "discover": "Discover References",
    "reference": "Extract Design Tokens",
    "plan": "Plan Site",
    "review": "Review (2 min)",
    "generate": "Generate Next.js",
    "taste": "Taste Polish",
    "qa_desktop": "QA Desktop ($25k rubric)",
    "qa_mobile": "QA Mobile",
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
    """Legacy 4-metric rubric (kept for qa_original back-compat)."""
    model_config = ConfigDict(extra="ignore")

    anti_slop: int = 0
    palette: int = 0
    mobile: int = 0
    overall: int = 0
    notes: str = ""

    def passed(self, threshold: int = 70) -> bool:
        return all(
            v >= threshold for v in (self.anti_slop, self.palette, self.mobile, self.overall)
        )


class BoundingBox(BaseModel):
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    label: str = ""


class QAScores25k(BaseModel):
    """Premium \"$25k agency\" rubric with overlap + human detection."""
    model_config = ConfigDict(extra="ignore")

    distinct_design: int = 0
    typography_hierarchy: int = 0
    palette_cohesion: int = 0
    spacing_rhythm: int = 0
    no_overlap: int = 0
    no_humans_in_images: int = 0
    copy_quality: int = 0
    premium_feel: int = 0
    overall: int = 0
    notes: str = ""
    overlap_regions: list[BoundingBox] = Field(default_factory=list)
    human_detections: list[BoundingBox] = Field(default_factory=list)

    def passed(self, threshold: int = 75, no_humans_threshold: int = 95) -> bool:
        return (
            self.overall >= threshold
            and self.no_overlap >= threshold
            and self.no_humans_in_images >= no_humans_threshold
        )


class DiscoveryCandidate(BaseModel):
    url: str
    name: str = ""
    source: str = ""  # 'awwwards' | 'godly' | 'curated'
    thumb: Optional[str] = None  # local artifact filename
    score: float = 0.0
    reason: str = ""


class Job(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_url: str
    reference_url: Optional[str] = None
    niche: Optional[str] = None
    status: str = "queued"
    # queued | running | awaiting_review | running | qa_passed | deploying | deployed | failed
    steps: list[JobStep] = Field(default_factory=JobStep.default_steps)
    qa_original: QAScores = Field(default_factory=QAScores)
    qa_generated: QAScores25k = Field(default_factory=QAScores25k)
    qa_mobile: QAScores25k = Field(default_factory=QAScores25k)
    deploy_url: Optional[str] = None
    deployment_id: Optional[str] = None
    project_id: Optional[str] = None
    video_asset_id: Optional[str] = None
    video_filename: Optional[str] = None
    error: Optional[str] = None
    pages_plan: list[dict] = Field(default_factory=list)
    design_tokens: dict = Field(default_factory=dict)
    brand: dict = Field(default_factory=dict)
    nav_plan: list[dict] = Field(default_factory=list)
    discovery_candidates: list[DiscoveryCandidate] = Field(default_factory=list)
    discovery_pick: Optional[DiscoveryCandidate] = None
    picked_components: list[dict] = Field(default_factory=list)
    review_deadline: Optional[str] = None
    review_action: Optional[str] = None  # accept | edit | auto
    artifacts_dir: Optional[str] = None
    screenshots: dict = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class JobCreateRequest(BaseModel):
    input_url: str
    reference_url: Optional[str] = None


class PlanReviewRequest(BaseModel):
    action: str  # "accept" | "edit" | "skip"
    plan: Optional[dict] = None


class LogEvent(BaseModel):
    job_id: str
    ts: str = Field(default_factory=now_iso)
    level: str = "info"  # info | warn | error
    stage: Optional[str] = None
    message: str
    data: Optional[dict[str, Any]] = None
