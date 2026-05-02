from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any

# Ensure Playwright looks in the shared browsers dir (installed there).
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/pw-browsers")

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def scrape_site(url: str, out_dir: Path) -> dict[str, Any]:
    """Scrape HTML + desktop/mobile screenshots + structured content."""
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"url": url}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])

        # desktop
        ctx_d = await browser.new_context(viewport={"width": 1440, "height": 900})
        page_d = await ctx_d.new_page()
        try:
            await page_d.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            await browser.close()
            raise RuntimeError(f"failed to load {url}: {e}")
        await page_d.wait_for_timeout(1600)
        html = await page_d.content()
        title = await page_d.title()
        (out_dir / "original.html").write_text(html, encoding="utf-8")
        desktop_path = out_dir / "desktop.png"
        await page_d.screenshot(path=str(desktop_path), full_page=False, type="png")
        # Also capture a taller full-page-ish screenshot for context
        fullpage_path = out_dir / "desktop_full.png"
        try:
            await page_d.screenshot(path=str(fullpage_path), full_page=True, type="png")
        except Exception:
            pass
        await ctx_d.close()

        # mobile
        ctx_m = await browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ),
        )
        page_m = await ctx_m.new_page()
        try:
            await page_m.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception:
            pass
        await page_m.wait_for_timeout(1500)
        mobile_path = out_dir / "mobile.png"
        await page_m.screenshot(path=str(mobile_path), full_page=False, type="png")
        await ctx_m.close()

        await browser.close()

    content = extract_content(html, url)
    result.update(
        {
            "title": title,
            "html_path": str(out_dir / "original.html"),
            "desktop_png": str(desktop_path),
            "desktop_fullpage_png": str(fullpage_path) if fullpage_path.exists() else None,
            "mobile_png": str(mobile_path),
            "content": content,
        }
    )
    return result


async def screenshot_url(url: str, out_dir: Path, name: str = "preview") -> dict[str, str]:
    """Capture desktop + mobile screenshots of a URL for post-deploy QA."""
    out_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx_d = await browser.new_context(viewport={"width": 1440, "height": 900})
        page_d = await ctx_d.new_page()
        await page_d.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page_d.wait_for_timeout(2500)
        d_path = out_dir / f"{name}_desktop.png"
        await page_d.screenshot(path=str(d_path), full_page=False, type="png")
        await ctx_d.close()

        ctx_m = await browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
        )
        page_m = await ctx_m.new_page()
        try:
            await page_m.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page_m.wait_for_timeout(2500)
        except Exception:
            pass
        m_path = out_dir / f"{name}_mobile.png"
        await page_m.screenshot(path=str(m_path), full_page=False, type="png")
        await ctx_m.close()

        await browser.close()
    return {"desktop": str(d_path), "mobile": str(m_path)}


def extract_content(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = (soup.title.string if soup.title else "").strip() if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    description = (desc_tag.get("content") or "").strip() if desc_tag else ""

    headings: list[dict[str, str]] = []
    for level in range(1, 4):
        for h in soup.find_all(f"h{level}"):
            text = " ".join(h.get_text(" ").split()).strip()
            if text:
                headings.append({"level": f"h{level}", "text": text[:240]})

    paragraphs: list[str] = []
    for p in soup.find_all(["p", "li"]):
        text = " ".join(p.get_text(" ").split()).strip()
        if 20 <= len(text) <= 600:
            paragraphs.append(text)
        if len(paragraphs) >= 80:
            break

    nav_links: list[dict[str, str]] = []
    nav_els = soup.find_all(["nav"]) or []
    for nav in nav_els[:2]:
        for a in nav.find_all("a"):
            href = (a.get("href") or "").strip()
            label = " ".join(a.get_text(" ").split()).strip()
            if label and href and not href.startswith("#"):
                nav_links.append({"label": label[:60], "href": href[:240]})
        if nav_links:
            break
    # fallback - top-of-page links
    if not nav_links:
        for a in soup.find_all("a")[:30]:
            href = (a.get("href") or "").strip()
            label = " ".join(a.get_text(" ").split()).strip()
            if label and href and 2 < len(label) < 30 and not href.startswith("#"):
                nav_links.append({"label": label, "href": href})

    # dedupe nav by label
    seen = set()
    dedup_nav = []
    for n in nav_links:
        key = n["label"].lower()
        if key in seen:
            continue
        seen.add(key)
        dedup_nav.append(n)
        if len(dedup_nav) >= 10:
            break

    images: list[str] = []
    for img in soup.find_all("img")[:20]:
        src = (img.get("src") or img.get("data-src") or "").strip()
        alt = (img.get("alt") or "").strip()
        if src:
            images.append(src)
        if len(images) >= 20:
            break

    domain = re.sub(r"^https?://", "", url).split("/")[0]

    return {
        "domain": domain,
        "title": title,
        "description": description,
        "headings": headings[:60],
        "paragraphs": paragraphs[:40],
        "nav": dedup_nav[:10],
        "images": images[:10],
    }
