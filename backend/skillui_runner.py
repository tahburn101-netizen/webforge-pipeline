from __future__ import annotations

import asyncio
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from references import pick_for_niche

CACHE_TTL_HOURS = 72


async def run_skillui(
    reference_url: str,
    out_dir: Path,
    mode: str = "default",
    db=None,
) -> dict[str, Any]:
    """Run skillui CLI on a reference URL with MongoDB-backed cache."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Try cache
    if db is not None:
        cached = await db.skillui_cache.find_one({"url": reference_url}, {"_id": 0})
        if cached and _is_fresh(cached.get("ts")):
            return {
                "exit_code": 0,
                "design_md": None,
                "design_md_text": cached.get("design_md_text", ""),
                "tokens": cached.get("tokens", {}),
                "screens": [],
                "from_cache": True,
            }

    cmd = [
        "skillui",
        "--url",
        reference_url,
        "--out",
        str(out_dir),
        "--no-skill",
        "--mode",
        mode,
    ]

    def _run() -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, cwd=str(out_dir)
        )

    proc = await asyncio.get_event_loop().run_in_executor(None, _run)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    design_md: Optional[Path] = None
    tokens: dict[str, Any] = {}
    screens: list[str] = []
    for root, _dirs, files in os.walk(out_dir):
        for f in files:
            p = Path(root) / f
            if f == "DESIGN.md":
                design_md = p
            elif f in ("colors.json", "typography.json", "spacing.json"):
                try:
                    tokens[f.replace(".json", "")] = json.loads(
                        p.read_text(encoding="utf-8")
                    )
                except Exception:
                    pass
            elif f.endswith((".png", ".jpg", ".jpeg")):
                screens.append(str(p))

    design_md_text = ""
    if design_md:
        try:
            design_md_text = design_md.read_text(encoding="utf-8", errors="ignore")[:8000]
        except Exception:
            pass

    # Persist to cache
    if db is not None:
        await db.skillui_cache.update_one(
            {"url": reference_url},
            {
                "$set": {
                    "url": reference_url,
                    "design_md_text": design_md_text,
                    "tokens": tokens,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
            },
            upsert=True,
        )

    return {
        "exit_code": proc.returncode,
        "stdout_tail": stdout[-1200:],
        "stderr_tail": stderr[-600:],
        "design_md": str(design_md) if design_md else None,
        "design_md_text": design_md_text,
        "tokens": tokens,
        "screens": screens[:6],
        "from_cache": False,
    }


def _is_fresh(ts: Optional[str]) -> bool:
    if not ts:
        return False
    try:
        dt = datetime.fromisoformat(ts)
        return datetime.now(timezone.utc) - dt < timedelta(hours=CACHE_TTL_HOURS)
    except Exception:
        return False


# Back-compat helper for old imports
def pick_reference(niche: str | None, override: str | None = None) -> str:
    if override:
        return override
    return pick_for_niche(niche)
