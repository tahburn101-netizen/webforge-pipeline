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

    last_error: str = ""
    text = ""
    for attempt in range(2):
        try:
            text = await generate_text(QA_SYSTEM, prompt, images=imgs)
            break
        except Exception as e:
            last_error = f"{type(e).__name__}: {str(e)[:200]}"
            if attempt == 0:
                # brief wait then retry once
                import asyncio as _a
                await _a.sleep(2)
                continue
            # No more retries; return graceful "unavailable" placeholder
            return {
                "anti_slop": -1,
                "palette": -1,
                "mobile": -1,
                "overall": -1,
                "notes": f"QA unavailable: {last_error}",
            }

    try:
        data = _parse_json_lenient(text)
    except Exception:
        # Try one targeted JSON repair pass
        try:
            data = await _json_repair(text)
        except Exception:
            return {
                "anti_slop": -1,
                "palette": -1,
                "mobile": -1,
                "overall": -1,
                "notes": (text or "")[:400] or "QA returned unparseable response",
            }
    for k in ("anti_slop", "palette", "mobile", "overall"):
        try:
            data[k] = int(data.get(k, 0))
        except Exception:
            data[k] = 0
    data["notes"] = (data.get("notes") or "").strip()[:800]
    return data


# --- $25k rubric (distinct_design, typography_hierarchy, palette_cohesion,
#     spacing_rhythm, no_overlap, no_humans_in_images, copy_quality, premium_feel)

QA_25K_SYSTEM = """You are a senior design director at a top-tier agency
reviewing a website that claims to be worth $25,000 USD. Score strictly 0-100.

Metrics (all 0-100):
- distinct_design: has a clear, non-generic design POV. AI-slop <= 50.
- typography_hierarchy: scale, weight contrast, rhythm, pairing quality.
- palette_cohesion: feels like ONE brand; accessible contrast; no random color dumps.
- spacing_rhythm: generous whitespace, consistent vertical rhythm, no cramped sections.
- no_overlap: 100 = NO elements overlap, clip, or truncate. Penalize ANY visible overlap.
- no_humans_in_images: 100 = ZERO humans/people/faces/portraits in ANY image on the page. This is HARD CRITERIA.
- copy_quality: concrete, specific, no lorem, no AI-slop phrasing.
- premium_feel: would a $25k agency ship this as-is? Consider craft, restraint, polish.
- overall: honest gestalt.

You will also receive 1-3 zoom crops of the page (hero, mid, footer) to catch small overlap/clipping issues.
Also return arrays:
- overlap_regions: up to 6 boxes {x,y,w,h,label} where x,y,w,h are fractions 0-1 of the screenshot size
- human_detections: up to 6 boxes {x,y,w,h,label} for any detected human/face

Return STRICT JSON (no markdown fences):
{
  "distinct_design": int, "typography_hierarchy": int, "palette_cohesion": int,
  "spacing_rhythm": int, "no_overlap": int, "no_humans_in_images": int,
  "copy_quality": int, "premium_feel": int, "overall": int,
  "notes": string (3-6 concrete actionable lines),
  "overlap_regions": [{"x":number,"y":number,"w":number,"h":number,"label":string}],
  "human_detections": [{"x":number,"y":number,"w":number,"h":number,"label":string}]
}"""


async def qa_review_25k(
    screenshot_png: str,
    mode: str = "desktop",
    context: str = "",
) -> dict[str, Any]:
    """Run the premium $25k rubric against a single screenshot.

    Automatically creates 3 zoom crops (top/mid/bottom) and includes them
    in the vision call so small overlap or clipping issues are catchable.
    """
    p = Path(screenshot_png) if screenshot_png else None
    if not p or not p.exists():
        return _qa25k_unavailable("missing screenshot")

    crops = _build_zoom_crops(p)
    imgs = [str(p)] + crops

    device_note = (
        "This is a MOBILE view (390px). Be extra strict on tap targets, "
        "font readability at small sizes, and horizontal scroll."
        if mode == "mobile"
        else "This is a DESKTOP view (1440px)."
    )
    prompt = (
        f"{device_note}\n"
        + (f"Context: {context}\n" if context else "")
        + "First image: the full screenshot. Subsequent images: zoom crops (top, mid, bottom). "
        "Use the crops to catch small overlap / clipping / humans in imagery. "
        "Return STRICT JSON only."
    )

    last_error = ""
    text = ""
    for attempt in range(2):
        try:
            text = await generate_text(QA_25K_SYSTEM, prompt, images=imgs)
            break
        except Exception as e:
            last_error = f"{type(e).__name__}: {str(e)[:200]}"
            if attempt == 0:
                import asyncio as _a
                await _a.sleep(2)
                continue
            return _qa25k_unavailable(last_error)

    try:
        data = _parse_json_lenient(text)
    except Exception:
        try:
            data = await _json_repair_25k(text)
        except Exception:
            return _qa25k_unavailable(
                "unparseable: " + (text or "")[:300]
            )

    # Normalize ints, clamp, preserve arrays
    int_fields = (
        "distinct_design",
        "typography_hierarchy",
        "palette_cohesion",
        "spacing_rhythm",
        "no_overlap",
        "no_humans_in_images",
        "copy_quality",
        "premium_feel",
        "overall",
    )
    out: dict[str, Any] = {}
    for k in int_fields:
        try:
            v = int(data.get(k, 0))
        except Exception:
            v = 0
        out[k] = max(0, min(100, v))
    out["notes"] = (data.get("notes") or "").strip()[:1200]
    # Preserve arrays; pipeline._sanitize_qa will coerce further
    out["overlap_regions"] = data.get("overlap_regions") or []
    out["human_detections"] = data.get("human_detections") or []
    return out


def _qa25k_unavailable(reason: str) -> dict[str, Any]:
    """Return a QAScores25k-shaped dict with -1 sentinel on failure."""
    out = {
        k: -1
        for k in (
            "distinct_design",
            "typography_hierarchy",
            "palette_cohesion",
            "spacing_rhythm",
            "no_overlap",
            "no_humans_in_images",
            "copy_quality",
            "premium_feel",
            "overall",
        )
    }
    out["notes"] = f"QA unavailable: {reason[:400]}"
    out["overlap_regions"] = []
    out["human_detections"] = []
    return out


def _build_zoom_crops(src_png: Path) -> list[str]:
    """Generate 3 zoom crops (top/mid/bottom) next to the source image.

    Returns absolute paths. Silently returns [] on Pillow errors.
    """
    try:
        from PIL import Image  # type: ignore

        img = Image.open(src_png)
        w, h = img.size
        out: list[str] = []
        stem = src_png.stem
        parent = src_png.parent
        # Portions of the page to zoom into
        spans = [
            ("top", (0, 0, w, min(h, int(h * 0.45)))),
            ("mid", (0, int(h * 0.3), w, int(h * 0.7))),
            ("bot", (0, max(0, int(h * 0.55)), w, h)),
        ]
        for name, box in spans:
            x0, y0, x1, y1 = box
            if x1 <= x0 or y1 <= y0:
                continue
            crop = img.crop(box)
            # Cap height for the vision API (keep file sizes reasonable)
            if crop.height > 1400:
                new_h = 1400
                new_w = int(crop.width * (new_h / crop.height))
                crop = crop.resize((new_w, new_h))
            out_path = parent / f"{stem}_zoom_{name}.png"
            crop.save(out_path, format="PNG", optimize=True)
            out.append(str(out_path))
        return out
    except Exception:
        return []


async def _json_repair_25k(text: str) -> dict[str, Any]:
    sys = (
        "Convert the user's free-form review into STRICT JSON with the schema: "
        '{"distinct_design":int,"typography_hierarchy":int,"palette_cohesion":int,'
        '"spacing_rhythm":int,"no_overlap":int,"no_humans_in_images":int,'
        '"copy_quality":int,"premium_feel":int,"overall":int,'
        '"notes":string,"overlap_regions":[{"x":number,"y":number,"w":number,"h":number,"label":string}],'
        '"human_detections":[{"x":number,"y":number,"w":number,"h":number,"label":string}]}.'
        ' Use 0-100 ranges. Output ONLY the JSON.'
    )
    out = await generate_text(sys, text or "{}")
    return _parse_json_lenient(out)


async def _json_repair(text: str) -> dict[str, Any]:
    """Use a tiny LLM call to coerce QA text into valid JSON."""
    sys = (
        "Convert the user's free-form QA review into STRICT JSON of the schema: "
        '{"anti_slop": int, "palette": int, "mobile": int, "overall": int, "notes": string}. '
        "Use 0-100 ranges. Output ONLY the JSON, nothing else."
    )
    out = await generate_text(sys, text or "{}")
    return _parse_json_lenient(out)
