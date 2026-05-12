"""Best-effort wrapper around leonxlnx/taste-skill.

Invokes `npx -y taste-skill --project <dir>` (or the `taste-skill` binary if
already on PATH). The CLI is expected to perform lightweight polish passes
on the generated Next.js project in-place.

If the CLI isn't available or fails, we log a warning and return a skip
result — this stage is non-fatal.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional


TASTE_TIMEOUT_SEC = int(os.environ.get("TASTE_TIMEOUT_SEC", "180"))


async def run_taste_skill(
    project_dir: Path,
    on_event: Optional[Callable] = None,
) -> dict[str, Any]:
    project_dir = Path(project_dir)
    if not project_dir.exists():
        await _emit(on_event, "taste", f"project dir not found: {project_dir}", level="warn")
        return {"ok": False, "skipped": True, "summary": "no project dir"}

    # Prefer a direct binary if available
    bin_path = shutil.which("taste-skill")
    if bin_path:
        cmd = [bin_path, "--project", str(project_dir)]
    elif shutil.which("npx"):
        cmd = ["npx", "-y", "taste-skill", "--project", str(project_dir)]
    else:
        await _emit(on_event, "taste", "neither taste-skill nor npx found; skipping", level="warn")
        return {"ok": False, "skipped": True, "summary": "npx not available"}

    await _emit(on_event, "taste", f"running: {' '.join(cmd)}")

    def _run() -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TASTE_TIMEOUT_SEC,
            cwd=str(project_dir),
        )

    try:
        proc = await asyncio.get_event_loop().run_in_executor(None, _run)
    except subprocess.TimeoutExpired:
        await _emit(on_event, "taste", "taste-skill timed out", level="warn")
        return {"ok": False, "skipped": False, "summary": "timeout"}
    except Exception as e:  # noqa: BLE001
        await _emit(on_event, "taste", f"taste-skill error: {e}", level="warn")
        return {"ok": False, "skipped": True, "summary": f"error: {type(e).__name__}"}

    stdout = (proc.stdout or "")[-600:]
    stderr = (proc.stderr or "")[-600:]
    if proc.returncode != 0:
        await _emit(
            on_event,
            "taste",
            f"taste-skill exit={proc.returncode}: {stderr[:240]}",
            level="warn",
        )
        return {
            "ok": False,
            "skipped": False,
            "summary": f"exit {proc.returncode}",
            "stdout": stdout,
            "stderr": stderr,
        }

    summary_line = next(
        (ln for ln in stdout.splitlines()[::-1] if ln.strip()),
        "completed",
    )
    await _emit(on_event, "taste", f"taste-skill ok: {summary_line[:200]}")
    return {
        "ok": True,
        "skipped": False,
        "summary": summary_line[:240],
        "stdout": stdout,
    }


async def _emit(cb, stage: str, message: str, level: str = "info") -> None:
    if cb is None:
        return
    try:
        res = cb(stage, message, level)
        if asyncio.iscoroutine(res):
            await res
    except Exception:  # noqa: BLE001
        pass
