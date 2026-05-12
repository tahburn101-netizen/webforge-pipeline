"""Curated component library with tag-based matching.

Loads backend/data/component_library.json (recipes inspired by patterns
seen on 21st.dev and motionsites.ai — written from scratch here, not copied).

Each plan section has a `kind` field (hero_text, feature_grid, cta, ...).
We look up the entries with that kind, then score by tag overlap with
the plan's palette/style notes/template flavor, and return one per section.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).resolve().parent / "data" / "component_library.json"


def _load() -> list[dict[str, Any]]:
    try:
        data = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        return data.get("components") or []
    except Exception:
        return []


LIBRARY: list[dict[str, Any]] = _load()


def list_all() -> list[dict[str, Any]]:
    """Return a public-safe view (no full JSX bodies) for API responses."""
    return [
        {k: v for k, v in c.items() if k != "jsx"}
        for c in LIBRARY
    ]


def _hash_pick(seed: str, n: int) -> int:
    if n <= 0:
        return 0
    h = hashlib.sha256(seed.encode()).hexdigest()
    return int(h[:8], 16) % n


def _score(entry: dict[str, Any], kind: str, style_tags: set[str]) -> int:
    if entry.get("kind") != kind:
        # allow soft match: feature_grid → content_split etc.
        return 0
    tags = set((entry.get("tags") or []))
    return len(tags & style_tags) + 1  # +1 baseline for same-kind match


def pick_components_for_plan(
    plan: dict[str, Any], seed: str = ""
) -> list[dict[str, Any]]:
    """Pick one component entry per section in the home page of the plan.

    Returns a lightweight list: [{section_idx, kind, slug, source, deps}].
    The generator uses this list to optionally drop in pre-built JSX.
    """
    if not LIBRARY:
        return []

    pages = plan.get("pages") or []
    home = next((p for p in pages if (p.get("route") or "/") == "/"), pages[0] if pages else None)
    if not home:
        return []
    sections = home.get("sections") or []

    design = plan.get("design") or {}
    style_notes = (design.get("style_notes") or "").lower()
    style_tags: set[str] = set()
    for t in ("dark", "light", "minimal", "editorial", "cinematic", "motion", "3d",
              "aurora", "orbit", "magnetic", "gradient", "grid", "bento"):
        if t in style_notes:
            style_tags.add(t)
    # Default tags — most WebForge sites are dark
    if not style_tags:
        style_tags.update({"dark", "minimal"})

    picks: list[dict[str, Any]] = []
    for i, sec in enumerate(sections):
        kind = (sec.get("kind") or "").strip()
        if not kind:
            continue
        ranked = sorted(
            [(e, _score(e, kind, style_tags)) for e in LIBRARY],
            key=lambda t: t[1],
            reverse=True,
        )
        top = [e for e, s in ranked if s > 0]
        if not top:
            continue
        # deterministic tie-break by seed
        choice = top[_hash_pick(f"{seed}|{i}|{kind}", len(top))]
        picks.append(
            {
                "section_idx": i,
                "kind": kind,
                "slug": choice["slug"],
                "source": choice.get("source", ""),
                "deps": choice.get("deps") or [],
                "tags": choice.get("tags") or [],
            }
        )
    return picks


def get_component_jsx(slug: str) -> str | None:
    for c in LIBRARY:
        if c.get("slug") == slug:
            return c.get("jsx")
    return None


def collect_deps(picked: list[dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for p in picked:
        for d in p.get("deps") or []:
            out.add(d)
    return sorted(out)
