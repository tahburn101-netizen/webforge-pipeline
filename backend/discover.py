"""Discover the best reference site for a given niche.

Strategy
--------
1. Hit awwwards.com + godly.website tag pages for the niche.
2. Extract ~10 top candidate site cards (title + outbound URL + thumbnail).
3. Capture a small thumbnail of each using Playwright (lightweight viewport).
4. Ask Gemini vision which candidate best matches the aspiration of the
   input site (given its own desktop screenshot).
5. Return the top pick + full candidate list. Cache results per niche in
   Mongo (TTL controlled by DISCOVER_CACHE_HOURS env var).

All scraping is read-only, throttled, and only stores small thumbnails
locally (we never rehost or redistribute third-party content).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from llm_provider import generate_text, has_llm
from models import DiscoveryCandidate

CACHE_TTL_HOURS = int(os.environ.get("DISCOVER_CACHE_HOURS", "168"))
MAX_CANDIDATES_PER_SOURCE = 6
DISCOVER_TIMEOUT_MS = 20_000


# --- niche → tag slug mapping ----------------------------------------------
_AWWWARDS_TAG: dict[str, str] = {
    "ai": "artificial-intelligence",
    "saas": "saas",
    "developer-tools": "developers",
    "fintech": "finance",
    "ecommerce": "e-commerce",
    "agency": "agency",
    "portfolio": "portfolio",
    "creator": "magazine",
    "consumer": "technology",
    "hardware": "technology",
}
_GODLY_TAG: dict[str, str] = {
    "ai": "technology",
    "saas": "saas",
    "developer-tools": "technology",
    "fintech": "finance",
    "ecommerce": "ecommerce",
    "agency": "agency",
    "portfolio": "portfolio",
    "creator": "blog",
    "consumer": "technology",
    "hardware": "product",
}


def _tag_for(niche: str, mapping: dict[str, str]) -> str:
    if not niche:
        return mapping.get("saas", "saas")
    k = niche.lower().replace(" ", "-")
    return mapping.get(k, mapping.get("saas", "saas"))


# --- public entry point ----------------------------------------------------


async def discover_references(
    niche: str,
    input_desktop_png: str,
    out_dir: Path,
    db=None,
) -> dict[str, Any]:
    """Return {'candidates': [DiscoveryCandidate], 'pick': DiscoveryCandidate}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    key_niche = (niche or "saas").lower().strip()

    # Try Mongo cache
    if db is not None:
        cached = await db.discover_cache.find_one({"niche": key_niche}, {"_id": 0})
        if cached and _is_fresh(cached.get("ts")):
            cand_raw = cached.get("candidates") or []
            pick_raw = cached.get("pick")
            return {
                "candidates": [DiscoveryCandidate(**c) for c in cand_raw],
                "pick": DiscoveryCandidate(**pick_raw) if pick_raw else None,
                "from_cache": True,
            }

    # 1. Scrape both sources in parallel
    awwwards_raw, godly_raw = await asyncio.gather(
        _fetch_awwwards(key_niche),
        _fetch_godly(key_niche),
        return_exceptions=True,
    )
    candidates: list[dict[str, Any]] = []
    if isinstance(awwwards_raw, list):
        candidates.extend(awwwards_raw[:MAX_CANDIDATES_PER_SOURCE])
    if isinstance(godly_raw, list):
        candidates.extend(godly_raw[:MAX_CANDIDATES_PER_SOURCE])

    # 2. Capture thumbnails locally (best-effort, in parallel with low concurrency)
    if candidates:
        await _capture_thumbnails(candidates, out_dir)

    # 3. Ask Gemini to pick the best match (if any candidates and LLM available)
    pick_index: Optional[int] = None
    pick_reason = ""
    if candidates and has_llm():
        try:
            pick_index, pick_reason = await _gemini_pick(
                input_desktop_png, candidates, key_niche
            )
        except Exception as e:  # noqa: BLE001
            pick_reason = f"vision pick skipped: {type(e).__name__}"

    # Fallback: if vision pick failed, take the first awwwards item, then godly
    if pick_index is None and candidates:
        pick_index = 0

    dc_list: list[DiscoveryCandidate] = []
    for i, c in enumerate(candidates):
        dc_list.append(
            DiscoveryCandidate(
                url=c["url"],
                name=c.get("name", "")[:80],
                source=c.get("source", ""),
                thumb=c.get("thumb"),
                score=float(1.0 if i == pick_index else 0.5),
                reason=(pick_reason if i == pick_index else "")[:240],
            )
        )
    pick = dc_list[pick_index] if pick_index is not None and dc_list else None

    # 4. Persist cache
    if db is not None:
        await db.discover_cache.update_one(
            {"niche": key_niche},
            {
                "$set": {
                    "niche": key_niche,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "candidates": [c.model_dump() for c in dc_list],
                    "pick": pick.model_dump() if pick else None,
                }
            },
            upsert=True,
        )

    return {"candidates": dc_list, "pick": pick, "from_cache": False}


def _is_fresh(ts: Optional[str]) -> bool:
    if not ts:
        return False
    try:
        dt = datetime.fromisoformat(ts)
        return datetime.now(timezone.utc) - dt < timedelta(hours=CACHE_TTL_HOURS)
    except Exception:  # noqa: BLE001
        return False


# --- awwwards ---------------------------------------------------------------

_AWW_URL = "https://www.awwwards.com/websites/{tag}/"
_UA_DESKTOP = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


async def _fetch_awwwards(niche: str) -> list[dict[str, Any]]:
    tag = _tag_for(niche, _AWWWARDS_TAG)
    url = _AWW_URL.format(tag=tag)
    html = await _fetch_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Awwwards cards: <figure class="... js-figure ..."> with data-url-detail + img
    for fig in soup.select("figure.js-collectable, figure.js-figure, figure"):
        if len(out) >= MAX_CANDIDATES_PER_SOURCE * 2:
            break
        # Title
        title_el = fig.select_one("h3") or fig.select_one(".heading-6") or fig.select_one("a")
        name = (title_el.get_text(" ", strip=True) if title_el else "")[:80]
        # Outbound URL — prefer the live site link
        href = ""
        for a in fig.find_all("a"):
            h = (a.get("href") or "").strip()
            if h.startswith("http") and "awwwards.com" not in h:
                href = h
                break
        if not href:
            # fallback: follow the detail link on awwwards
            for a in fig.find_all("a"):
                h = (a.get("href") or "").strip()
                if h.startswith("/sites/"):
                    href = urljoin("https://www.awwwards.com", h)
                    break
        if not href or href in seen:
            continue
        seen.add(href)
        if not name:
            name = urlparse(href).netloc
        out.append(
            {
                "name": name,
                "url": href,
                "source": "awwwards",
                "thumb": None,
            }
        )
    return out


# --- godly.website ----------------------------------------------------------

_GODLY_URL = "https://godly.website/tags/{tag}"


async def _fetch_godly(niche: str) -> list[dict[str, Any]]:
    tag = _tag_for(niche, _GODLY_TAG)
    url = _GODLY_URL.format(tag=tag)
    html = await _fetch_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Godly cards: inspect anchor tags with external hrefs within article/section blocks
    for a in soup.find_all("a"):
        if len(out) >= MAX_CANDIDATES_PER_SOURCE * 2:
            break
        href = (a.get("href") or "").strip()
        if not href.startswith("http"):
            continue
        if "godly.website" in href or "twitter.com" in href or "instagram.com" in href:
            continue
        if href in seen:
            continue
        # only accept root-level URLs (heuristic for "the actual site")
        parsed = urlparse(href)
        if parsed.path not in ("", "/"):
            # allow /home, /landing, etc. but not deep marketing pages
            if len(parsed.path.strip("/").split("/")) > 1:
                continue
        seen.add(href)
        # Try to find a nearby caption or title
        parent = a.find_parent(["article", "li", "div"]) or a
        title_el = parent.find(["h2", "h3", "h4"])
        name = (title_el.get_text(" ", strip=True) if title_el else parsed.netloc)[:80]
        out.append(
            {
                "name": name,
                "url": href,
                "source": "godly",
                "thumb": None,
            }
        )
    return out


# --- html fetch helper ------------------------------------------------------


async def _fetch_html(url: str) -> str:
    """Fetch HTML via Playwright (handles modern JS-rendered pages)."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                ctx = await browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    user_agent=_UA_DESKTOP,
                )
                page = await ctx.new_page()
                await page.goto(
                    url, wait_until="domcontentloaded", timeout=DISCOVER_TIMEOUT_MS
                )
                await page.wait_for_timeout(1500)
                html = await page.content()
                await ctx.close()
                return html
            finally:
                await browser.close()
    except Exception:  # noqa: BLE001
        return ""


# --- thumbnail capture ------------------------------------------------------


async def _capture_thumbnails(
    candidates: list[dict[str, Any]], out_dir: Path
) -> None:
    """Visit each candidate URL with a small viewport and screenshot it."""
    sem = asyncio.Semaphore(3)

    async def _one(idx: int, c: dict[str, Any]) -> None:
        async with sem:
            thumb_name = _safe_thumb_name(c["source"], idx, c["url"])
            thumb_path = out_dir / thumb_name
            if thumb_path.exists():
                c["thumb"] = thumb_name
                return
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True, args=["--no-sandbox"]
                    )
                    try:
                        ctx = await browser.new_context(
                            viewport={"width": 1280, "height": 720},
                            user_agent=_UA_DESKTOP,
                        )
                        page = await ctx.new_page()
                        await page.goto(
                            c["url"],
                            wait_until="domcontentloaded",
                            timeout=DISCOVER_TIMEOUT_MS,
                        )
                        await page.wait_for_timeout(1800)
                        await page.screenshot(path=str(thumb_path), type="png")
                        await ctx.close()
                        c["thumb"] = thumb_name
                        c["thumb_abs"] = str(thumb_path)
                    finally:
                        await browser.close()
            except Exception:  # noqa: BLE001
                pass

    await asyncio.gather(
        *[_one(i, c) for i, c in enumerate(candidates)], return_exceptions=True
    )


def _safe_thumb_name(source: str, idx: int, url: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]", "_", urlparse(url).netloc)[:32] or f"site{idx}"
    return f"{source}_{idx:02d}_{base}.png"


# --- Gemini vision pick -----------------------------------------------------

_PICK_SYSTEM = (
    "You are a senior design director choosing a reference website whose design "
    "best elevates a given input site. You will see the input site's screenshot, "
    "followed by numbered candidate screenshots. Pick the candidate whose design "
    "language would BEST uplift the input for the given niche. Return STRICT JSON: "
    '{"index": int, "reason": string}. Index is 0-based. Reason is one short sentence.'
)


async def _gemini_pick(
    input_png: str, candidates: list[dict[str, Any]], niche: str
) -> tuple[Optional[int], str]:
    imgs: list[str] = []
    if input_png and Path(input_png).exists():
        imgs.append(input_png)
    for c in candidates:
        thumb = c.get("thumb")
        if not thumb:
            continue
        # thumbs are relative names — need absolute path; caller ensured they live in out_dir
        # We resolve via filesystem check at use site
    # Build absolute paths from candidate thumbs
    # (Caller placed thumbs in out_dir and set c["thumb"] to the filename.)
    # Reconstruct the out_dir from the first valid thumb's sibling of input_png is not reliable,
    # so the caller passes only filename and the thumbs are in out_dir. To keep this function
    # pure, we accept that candidates may already contain absolute thumb paths via "thumb_abs".
    for c in candidates:
        abs_thumb = c.get("thumb_abs")
        if abs_thumb and Path(abs_thumb).exists():
            imgs.append(abs_thumb)

    if len(imgs) < 2:
        return None, "not enough thumbnails for vision pick"

    listing = "\n".join(
        f"{i}. {c.get('name', c['url'])} — {c['url']} (source: {c['source']})"
        for i, c in enumerate(candidates)
    )
    prompt = (
        f"Niche: {niche}\n\nCandidates:\n{listing}\n\n"
        "First image is the INPUT site. Remaining images are the candidates in order. "
        "Return JSON only."
    )
    text = await generate_text(_PICK_SYSTEM, prompt, images=imgs)
    try:
        t = text.strip().strip("`")
        if t.lower().startswith("json"):
            t = t[4:].strip()
        first = t.find("{")
        last = t.rfind("}")
        data = json.loads(t[first : last + 1]) if first != -1 else {}
        idx = int(data.get("index", 0))
        reason = str(data.get("reason", ""))[:240]
        if 0 <= idx < len(candidates):
            return idx, reason
    except Exception:  # noqa: BLE001
        pass
    return None, "vision pick returned invalid response"
