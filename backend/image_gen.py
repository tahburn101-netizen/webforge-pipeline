"""Generate hero + section images for the produced Next.js site."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from llm_provider import generate_image


async def generate_site_images(
    plan: dict[str, Any],
    public_dir: Path,
    on_event=None,
) -> dict[str, str]:
    """Generate up to N images used by the site.

    Returns a dict: {
      'hero.jpg': 'hero.jpg',  # filename in /public/
      'section_<slug>.jpg': '...',
    }
    """
    public_dir.mkdir(parents=True, exist_ok=True)
    brand = plan.get("brand") or {}
    design = plan.get("design") or {}
    niche = plan.get("niche") or "modern tech product"
    style_notes = design.get("style_notes") or "cinematic, premium, dark, distinctive palette"
    primary = design.get("primary") or "#2DE3C6"
    accent = design.get("accent") or "#FFB86B"
    brand_voice = brand.get("voice") or "confident, modern"

    tasks: list[tuple[str, str, str]] = []

    # Hero image (always)
    hero_prompt = (
        f"Abstract cinematic hero visual for {niche}. Mood: {brand_voice}. "
        f"Style: {style_notes}. Palette hinting at {primary} and {accent}. "
        "Moody 3D render feel, soft bokeh, no text, premium product aesthetic."
    )
    tasks.append(("hero", hero_prompt, "hero.jpg"))

    # Up to 4 section images based on gallery/team/stats/feature sections
    pages = plan.get("pages") or []
    used = 0
    limit = 4
    for pg in pages:
        for s in pg.get("sections") or []:
            if used >= limit:
                break
            kind = (s.get("kind") or "").lower()
            if kind not in ("gallery", "content_split", "team", "case_studies", "blog"):
                continue
            heading = s.get("heading") or ""
            sub = s.get("subheading") or ""
            prompt = (
                f"Editorial illustration for '{heading}' section (niche: {niche}). "
                f"Tone: {sub or brand_voice}. Style: {style_notes}. "
                f"Palette hinting {primary}/{accent}. No text, dark minimal composition."
            )
            slug = f"section_{used + 1}.jpg"
            tasks.append((f"section_{used + 1}", prompt, slug))
            used += 1
        if used >= limit:
            break

    results: dict[str, str] = {}

    async def _one(name: str, prompt: str, fname: str):
        out = public_dir / fname
        if on_event:
            await _emit(on_event, f"generating image: {name}")
        try:
            p = await generate_image(prompt, str(out), size_hint="16:9")
            if p:
                results[fname] = fname
                if on_event:
                    await _emit(on_event, f"image ready: {fname} ({out.stat().st_size // 1024}KB)")
            else:
                if on_event:
                    await _emit(on_event, f"image failed: {fname}", level="warn")
        except Exception as e:
            if on_event:
                await _emit(on_event, f"image error {fname}: {e}", level="warn")

    # Generate in parallel (bounded)
    sem = asyncio.Semaphore(2)

    async def _wrap(args):
        async with sem:
            await _one(*args)

    await asyncio.gather(*[_wrap(t) for t in tasks], return_exceptions=True)
    return results


async def _emit(cb, message: str, level: str = "info"):
    if cb is None:
        return
    try:
        res = cb("generate", message, level)
        if asyncio.iscoroutine(res):
            await res
    except Exception:
        pass
