from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from llm_provider import generate_text


def _parse_json_lenient(text: str) -> dict[str, Any]:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.strip()
    first = t.find("{")
    last = t.rfind("}")
    if first != -1 and last != -1:
        t = t[first : last + 1]
    return json.loads(t)


ANALYZE_SYSTEM = """You are a senior product designer and Next.js engineer who creates investor-grade websites.
You receive screenshots of an EXISTING website to transform, its extracted content, and a reference design summary from a beautiful site in the same niche.

Return STRICT JSON ONLY (no markdown fences) with this schema:
{
  "niche": string,
  "brand": {"name": string, "tagline": string, "voice": string},
  "design": {
    "primary": string (hex),
    "primary_2": string (hex),
    "accent": string (hex),
    "bg": string (hex),
    "bg_2": string (hex),
    "fg": string (hex),
    "muted_fg": string (hex),
    "font_heading": string (Google Font name),
    "font_body": string (Google Font name),
    "radius": string (e.g., '14px'),
    "style_notes": string
  },
  "pages": [
    {
      "route": string (one of '/', '/about', '/features', '/services', '/pricing', '/blog', '/docs', '/case-studies', '/contact', etc.),
      "title": string,
      "purpose": string,
      "sections": [
        {
          "kind": string (one of: 'hero_video','hero_text','feature_grid','stats','testimonials','pricing','faq','cta','logo_cloud','content_split','gallery','team','timeline','contact_form','blog','docs','case_studies','footer'),
          "heading": string,
          "subheading": string,
          "items": [ { "title": string, "body": string, "meta": string } ],
          "cta": { "label": string, "href": string }
        }
      ]
    }
  ],
  "nav": [ { "label": string, "href": string } ],
  "qa_original": {"anti_slop": int, "palette": int, "mobile": int, "overall": int, "notes": string}
}

Rules:
- AT LEAST 4 pages; include blog/docs/case-studies if source content suggests those.
- Home MUST begin with a 'hero_video' section, then 3+ more sections.
- Retain original content: reuse input headings/paragraphs verbatim where possible.
- No lorem ipsum. Copy must be concise and concrete.
- Colors must form a cohesive, distinctive palette (avoid generic grays and purple-to-pink gradients).
- All nav hrefs must map to pages in 'pages'.
- Scores 0-100. Be honest.
"""


async def analyze_and_plan(
    scrape: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any]:
    content = scrape.get("content") or {}
    ref_text = (reference.get("design_md_text") or "")[:4000]
    ref_tokens = reference.get("tokens") or {}
    prompt = (
        "INPUT SITE CONTENT (JSON):\n"
        + json.dumps(content, ensure_ascii=False)[:6500]
        + "\n\nREFERENCE DESIGN SUMMARY:\n"
        + ref_text
        + "\n\nREFERENCE TOKENS (JSON keys): "
        + ", ".join(list(ref_tokens.keys()))
        + "\n\nReturn the strict JSON plan now."
    )
    imgs = [p for p in [scrape.get("desktop_png"), scrape.get("mobile_png")] if p]
    text = await generate_text(ANALYZE_SYSTEM, prompt, images=imgs)
    plan = _parse_json_lenient(text)

    pages = plan.get("pages") or []
    seen: set[str] = set()
    clean_pages: list[dict] = []
    for p in pages:
        r = (p.get("route") or "/").strip()
        if not r.startswith("/"):
            r = "/" + r
        if r in seen:
            continue
        seen.add(r)
        clean_pages.append({**p, "route": r})
    if not clean_pages:
        raise RuntimeError("LLM returned no pages")
    home = next((pg for pg in clean_pages if pg["route"] == "/"), clean_pages[0])
    home.setdefault("sections", [])
    if not home["sections"] or home["sections"][0].get("kind") != "hero_video":
        home["sections"].insert(
            0,
            {
                "kind": "hero_video",
                "heading": plan.get("brand", {}).get("tagline") or "A new standard.",
                "subheading": content.get("description", "")[:140] or "",
                "items": [],
                "cta": {"label": "Explore", "href": "/about"},
            },
        )
    plan["pages"] = clean_pages
    return plan


QA_SYSTEM = """You are a critical senior design QA reviewer. Score strictly (0-100):
- anti_slop: NON-generic, distinctive, original? (90+ premium, 60-89 serviceable, <60 AI-slop)
- palette: cohesive, distinctive, accessible color palette?
- mobile: perfect mobile layout; no broken elements; good tap targets; readable type?
- overall: gestalt.

Return STRICT JSON: {"anti_slop": int, "palette": int, "mobile": int, "overall": int, "notes": string}
Notes: 2-4 concrete actionable lines. No markdown."""


async def qa_review(
    desktop_png: str,
    mobile_png: str,
    context: str = "",
) -> dict[str, Any]:
    prompt = (
        "Review the attached desktop + mobile screenshots of a website and score strictly.\n"
        + (f"Context: {context}\n" if context else "")
        + "Return JSON only."
    )
    imgs = [p for p in [desktop_png, mobile_png] if p and Path(p).exists()]
    text = await generate_text(QA_SYSTEM, prompt, images=imgs)
    try:
        data = _parse_json_lenient(text)
    except Exception:
        data = {"anti_slop": 0, "palette": 0, "mobile": 0, "overall": 0, "notes": text[:400]}
    for k in ("anti_slop", "palette", "mobile", "overall"):
        try:
            data[k] = int(data.get(k, 0))
        except Exception:
            data[k] = 0
    data["notes"] = (data.get("notes") or "").strip()[:800]
    return data
