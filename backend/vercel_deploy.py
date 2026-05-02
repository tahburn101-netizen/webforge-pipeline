from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

VERCEL_API = "https://api.vercel.com"
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")

_SKIP_DIRS = {"node_modules", ".next", ".git", ".vercel", ".turbo", "dist", "build"}
_TEXT_EXT = {
    ".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html", ".md", ".mjs", ".cjs",
    ".svg", ".txt", ".yaml", ".yml", ".toml",
}
_BINARY_EXT = {".mp4", ".webm", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".woff", ".woff2", ".mov"}


import hashlib
import base64


def _sha1(path: Path) -> tuple[str, int]:
    h = hashlib.sha1()
    size = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def _collect_files(project_dir: Path) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for f in files:
            ap = Path(root) / f
            if not ap.is_file():
                continue
            rel = ap.relative_to(project_dir).as_posix()
            out.append((rel, ap))
    return out


async def deploy_project(
    project_dir: Path,
    project_name: str,
    on_event=None,
) -> dict[str, Any]:
    if not VERCEL_TOKEN:
        raise RuntimeError("VERCEL_TOKEN missing")

    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}
    files = _collect_files(project_dir)
    await _emit(on_event, "deploy", f"collected {len(files)} files")

    # Build file payload: inline text, upload-by-sha for binary
    file_payload: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=300.0) as client:
        for rel, ap in files:
            ext = ap.suffix.lower()
            if ext in _BINARY_EXT:
                digest, size = _sha1(ap)
                with open(ap, "rb") as f:
                    body = f.read()
                try:
                    up = await client.post(
                        f"{VERCEL_API}/v2/files",
                        headers={
                            **headers,
                            "Content-Length": str(size),
                            "x-vercel-digest": digest,
                            "Content-Type": "application/octet-stream",
                        },
                        content=body,
                    )
                    if up.status_code not in (200, 201):
                        await _emit(
                            on_event,
                            "deploy",
                            f"binary upload failed {rel}: {up.status_code} {up.text[:200]}",
                            level="warn",
                        )
                        # Skip this binary file from the deployment to avoid 400
                        continue
                except Exception as e:
                    await _emit(on_event, "deploy", f"binary upload exception {rel}: {e!r}", level="warn")
                    continue
                file_payload.append({"file": rel, "sha": digest, "size": size})
            else:
                try:
                    text = ap.read_text(encoding="utf-8")
                except Exception:
                    continue
                file_payload.append({"file": rel, "data": text})

        # Create deployment
        body = {
            "name": project_name,
            "files": file_payload,
            "projectSettings": {"framework": "nextjs"},
            "target": "production",
        }
        r = await client.post(
            f"{VERCEL_API}/v13/deployments",
            headers={**headers, "Content-Type": "application/json"},
            json=body,
        )
        if r.status_code not in (200, 201):
            await _emit(on_event, "deploy", f"create failed: {r.status_code} {r.text[:400]}", level="error")
            r.raise_for_status()
        dep = r.json()
        dep_id = dep.get("id")
        project_id = (dep.get("project") or {}).get("id") or dep.get("projectId")
        url = dep.get("url")
        await _emit(on_event, "deploy", f"created {dep_id} -> https://{url}")

        # Disable protection to make URL publicly shareable
        if project_id:
            try:
                patch = await client.patch(
                    f"{VERCEL_API}/v9/projects/{project_id}",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"ssoProtection": None, "passwordProtection": None},
                )
                await _emit(
                    on_event,
                    "deploy",
                    f"protection_disabled status={patch.status_code}",
                )
            except Exception as e:
                await _emit(on_event, "deploy", f"protection_disable_error: {e}", level="warn")

        # Poll until READY
        deadline = time.time() + 720
        while time.time() < deadline:
            s = await client.get(f"{VERCEL_API}/v13/deployments/{dep_id}", headers=headers)
            if s.status_code == 200:
                j = s.json()
                state = j.get("readyState") or j.get("state")
                await _emit(on_event, "deploy", f"state={state}")
                if state == "READY":
                    url = j.get("url") or url
                    return {
                        "url": f"https://{url}",
                        "deployment_id": dep_id,
                        "project_id": project_id,
                        "state": "READY",
                    }
                if state in ("ERROR", "CANCELED"):
                    err = j.get("errorMessage") or state
                    raise RuntimeError(f"deployment {state}: {err}")
            await asyncio.sleep(6)
        raise RuntimeError("deployment timeout")


async def _emit(cb, stage: str, message: str, level: str = "info") -> None:
    if cb is None:
        return
    try:
        res = cb(stage, message, level)
        if asyncio.iscoroutine(res):
            await res
    except Exception:
        pass
