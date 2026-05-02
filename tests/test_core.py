"""
POC test_core.py - validates ALL core integrations end-to-end for the
URL -> transformed Next.js -> Vercel pipeline.

Stages tested:
  1. Playwright: scrape HTML + desktop/mobile screenshots for a real URL
  2. skillui CLI: extract design tokens from a reference URL
  3. Emergent LLM (Gemini 2.5 Pro vision): analyze screenshots + produce
     structured JSON describing a minimal Next.js project
  4. Vercel Deployments API: upload a minimal (known-good) Next.js project
     via /v13/deployments with inline files and poll until READY,
     returning a public URL.

Each stage is a separate async function; main() runs them sequentially
and prints a final PASS/FAIL table. If any stage fails the script exits 1.
"""

import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN")

WORKDIR = Path(tempfile.mkdtemp(prefix="webforge_poc_"))
print(f"[POC] Working dir: {WORKDIR}")

RESULTS: dict[str, tuple[bool, str]] = {}


def log(stage: str, msg: str) -> None:
    print(f"[{stage}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Stage 1: Playwright scrape + screenshots
# ---------------------------------------------------------------------------
async def stage_playwright(url: str) -> dict:
    from playwright.async_api import async_playwright

    out = WORKDIR / "scrape"
    out.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        # desktop
        ctx_d = await browser.new_context(viewport={"width": 1440, "height": 900})
        page_d = await ctx_d.new_page()
        await page_d.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page_d.wait_for_timeout(1500)
        html = await page_d.content()
        title = await page_d.title()
        (out / "original.html").write_text(html, encoding="utf-8")
        await page_d.screenshot(
            path=str(out / "desktop.png"), full_page=False, type="png"
        )
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
        await page_m.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page_m.wait_for_timeout(1500)
        await page_m.screenshot(
            path=str(out / "mobile.png"), full_page=False, type="png"
        )
        await ctx_m.close()
        await browser.close()

    desktop = out / "desktop.png"
    mobile = out / "mobile.png"
    assert desktop.exists() and desktop.stat().st_size > 5000, "desktop screenshot missing/too small"
    assert mobile.exists() and mobile.stat().st_size > 5000, "mobile screenshot missing/too small"
    log("playwright", f"title={title!r} desktop={desktop.stat().st_size}B mobile={mobile.stat().st_size}B")
    return {
        "title": title,
        "html_path": str(out / "original.html"),
        "desktop_png": str(desktop),
        "mobile_png": str(mobile),
    }


# ---------------------------------------------------------------------------
# Stage 2: skillui CLI
# ---------------------------------------------------------------------------
def stage_skillui(reference_url: str) -> dict:
    out_dir = WORKDIR / "skillui_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    # skillui outputs into current dir; run inside out_dir
    proc = subprocess.run(
        ["skillui", "--url", reference_url, "--out", str(out_dir), "--no-skill"],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(out_dir),
    )
    log("skillui", f"exit={proc.returncode} stdout_tail={proc.stdout.strip()[-400:]!r}")
    if proc.returncode != 0:
        log("skillui", f"stderr={proc.stderr[-600:]!r}")

    # Find produced DESIGN.md / tokens somewhere under out_dir
    design_md = None
    tokens = {}
    for root, _dirs, files in os.walk(out_dir):
        for f in files:
            p = Path(root) / f
            if f == "DESIGN.md":
                design_md = p
            if f in ("colors.json", "typography.json", "spacing.json"):
                try:
                    tokens[f] = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
    if not design_md:
        raise RuntimeError("skillui produced no DESIGN.md")
    log("skillui", f"design_md={design_md} tokens_keys={list(tokens.keys())}")
    return {
        "design_md": str(design_md),
        "tokens": tokens,
    }


# ---------------------------------------------------------------------------
# Stage 3: Emergent LLM (Gemini 2.5 Pro vision, structured JSON)
# ---------------------------------------------------------------------------
async def stage_llm(scrape: dict, tokens: dict) -> dict:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    def b64(path: str) -> str:
        return base64.b64encode(Path(path).read_bytes()).decode()

    system = (
        "You are a senior product designer and Next.js engineer. "
        "You receive two screenshots (desktop + mobile) of an existing website and a "
        "design-system summary extracted from a beautiful reference site. "
        "Return STRICT JSON ONLY (no markdown fences) matching this schema:\n"
        "{\n"
        '  "niche": string,\n'
        '  "pages": [ { "route": string, "title": string, "purpose": string } ],\n'
        '  "designTokens": { "primary": string, "secondary": string, "bg": string, "fg": string, "accent": string },\n'
        '  "qa_original": { "anti_slop": number, "palette": number, "mobile": number, "overall": number, "notes": string }\n'
        "}\n"
        "Scores are 0-100 integers. Output MUST be valid JSON."
    )
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"poc-{int(time.time())}",
        system_message=system,
    ).with_model("gemini", "gemini-2.5-pro")

    content_summary = f"Reference tokens keys: {list(tokens.keys())}."
    msg = UserMessage(
        text=(
            "Analyze the attached desktop and mobile screenshots of the input "
            "website, plus this reference design context, and produce the JSON.\n\n"
            + content_summary
        ),
        file_contents=[
            ImageContent(image_base64=b64(scrape["desktop_png"])),
            ImageContent(image_base64=b64(scrape["mobile_png"])),
        ],
    )
    resp = await chat.send_message(msg)
    text = resp if isinstance(resp, str) else str(resp)
    log("llm", f"raw_len={len(text)} head={text[:200]!r}")

    # Parse JSON; be lenient
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.strip()
    # Extract first {...} block
    first = t.find("{")
    last = t.rfind("}")
    if first != -1 and last != -1:
        t = t[first : last + 1]
    data = json.loads(t)
    assert "pages" in data and isinstance(data["pages"], list) and len(data["pages"]) >= 1
    assert "designTokens" in data and "primary" in data["designTokens"]
    log("llm", f"niche={data.get('niche')!r} pages={len(data['pages'])}")
    return data


# ---------------------------------------------------------------------------
# Stage 4: Vercel deploy minimal Next.js project
# ---------------------------------------------------------------------------
def build_minimal_nextjs(project_dir: Path, design: dict) -> None:
    """Write a minimal Next.js 14 app router project that builds on Vercel."""
    pages = design.get("pages") or [
        {"route": "/", "title": "Home", "purpose": "Landing"},
        {"route": "/about", "title": "About", "purpose": "About us"},
    ]
    tokens = design.get("designTokens") or {}
    primary = tokens.get("primary", "#0ea5e9")
    bg = tokens.get("bg", "#0b0b0f")
    fg = tokens.get("fg", "#f5f5f7")

    (project_dir / "package.json").write_text(
        json.dumps(
            {
                "name": "webforge-poc-site",
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                },
                "dependencies": {
                    "next": "14.2.5",
                    "react": "18.3.1",
                    "react-dom": "18.3.1",
                },
            },
            indent=2,
        )
    )
    (project_dir / "next.config.mjs").write_text(
        "export default { reactStrictMode: true, "
        "eslint: { ignoreDuringBuilds: true }, "
        "typescript: { ignoreBuildErrors: true } };\n"
    )
    (project_dir / "app").mkdir()

    nav_items = json.dumps([{"route": p["route"], "title": p["title"]} for p in pages])
    (project_dir / "app" / "layout.jsx").write_text(
        f"""export const metadata = {{ title: 'WebForge POC', description: 'POC' }};
const NAV = {nav_items};
export default function RootLayout({{ children }}) {{
  return (
    <html lang="en">
      <body style={{{{ margin:0, background:'{bg}', color:'{fg}', fontFamily:'system-ui, sans-serif' }}}}>
        <nav style={{{{ padding:'16px 24px', borderBottom:'1px solid #222', display:'flex', gap:16 }}}}>
          {{NAV.map(function(p){{ return (
            <a key={{p.route}} href={{p.route}} style={{{{ color:'{fg}', textDecoration:'none' }}}}>{{p.title}}</a>
          ); }})}}
        </nav>
        <main>{{children}}</main>
      </body>
    </html>
  );
}}
"""
    )
    # Home
    (project_dir / "app" / "page.jsx").write_text(
        f"""export default function Page() {{
  return (
    <section style={{{{ padding:'64px 24px', maxWidth:960, margin:'0 auto' }}}}>
      <h1 style={{{{ fontSize:56, lineHeight:1.05, margin:0, color:'{primary}' }}}}>WebForge POC</h1>
      <p style={{{{ fontSize:18, opacity:.8, marginTop:16 }}}}>Generated by the pipeline POC.</p>
    </section>
  );
}}
"""
    )
    # Additional pages
    for p in pages:
        route = p["route"].strip("/")
        if not route:
            continue
        sub = project_dir / "app" / route
        sub.mkdir(parents=True, exist_ok=True)
        safe_title = json.dumps(p["title"])
        safe_purpose = json.dumps(p.get("purpose", ""))
        (sub / "page.jsx").write_text(
            f"""export default function Page() {{
  return (
    <section style={{{{ padding:'64px 24px', maxWidth:960, margin:'0 auto' }}}}>
      <h1 style={{{{ fontSize:40, margin:0, color:'{primary}' }}}}>{{{safe_title}}}</h1>
      <p style={{{{ fontSize:16, opacity:.8, marginTop:12 }}}}>{{{safe_purpose}}}</p>
    </section>
  );
}}
"""
        )


def collect_files(project_dir: Path) -> list[tuple[str, str]]:
    out = []
    skip_dirs = {"node_modules", ".next", ".git", ".vercel"}
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            abs_p = Path(root) / f
            rel = abs_p.relative_to(project_dir).as_posix()
            out.append((rel, str(abs_p)))
    return out


async def stage_vercel(design: dict) -> dict:
    proj_dir = WORKDIR / "nextjs_site"
    proj_dir.mkdir(parents=True, exist_ok=True)
    build_minimal_nextjs(proj_dir, design)

    files = collect_files(proj_dir)
    log("vercel", f"collected {len(files)} files")

    file_payload = []
    for rel, abs_p in files:
        data = Path(abs_p).read_text(encoding="utf-8", errors="ignore")
        file_payload.append({"file": rel, "data": data})

    project_name = f"webforge-poc-{int(time.time())}"
    body = {
        "name": project_name,
        "files": file_payload,
        "projectSettings": {"framework": "nextjs"},
        "target": "production",
    }
    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            "https://api.vercel.com/v13/deployments",
            headers=headers,
            json=body,
        )
        log("vercel", f"create status={r.status_code}")
        if r.status_code not in (200, 201):
            log("vercel", f"create body={r.text[:1200]}")
            r.raise_for_status()
        dep = r.json()
        dep_id = dep.get("id")
        url = dep.get("url")
        project_id = (dep.get("project") or {}).get("id") or dep.get("projectId")
        log("vercel", f"deployment_id={dep_id} project_id={project_id} url=https://{url}")

        # Disable Vercel SSO protection so the link is publicly shareable
        if project_id:
            try:
                patch = await client.patch(
                    f"https://api.vercel.com/v9/projects/{project_id}",
                    headers=headers,
                    json={"ssoProtection": None, "passwordProtection": None},
                )
                log(
                    "vercel",
                    f"patch_protection status={patch.status_code} body={patch.text[:200]}",
                )
            except Exception as e:
                log("vercel", f"patch_protection error={e}")

        # poll
        deadline = time.time() + 600
        final_state = None
        while time.time() < deadline:
            s = await client.get(
                f"https://api.vercel.com/v13/deployments/{dep_id}",
                headers=headers,
            )
            if s.status_code == 200:
                j = s.json()
                state = j.get("readyState") or j.get("state")
                log("vercel", f"state={state}")
                if state == "READY":
                    final_state = "READY"
                    url = j.get("url") or url
                    break
                if state in ("ERROR", "CANCELED"):
                    log("vercel", f"failed body={json.dumps(j)[:1000]}")
                    raise RuntimeError(f"deployment failed: {state}")
            await asyncio.sleep(6)

        if final_state != "READY":
            raise RuntimeError("deployment timeout")

    public_url = f"https://{url}"
    log("vercel", f"PUBLIC URL -> {public_url}")
    return {"url": public_url, "deployment_id": dep_id}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main() -> int:
    assert EMERGENT_LLM_KEY, "EMERGENT_LLM_KEY missing"
    assert VERCEL_TOKEN, "VERCEL_TOKEN missing"

    input_url = "https://example.com"
    reference_url = "https://linear.app"

    # 1
    try:
        scrape = await stage_playwright(input_url)
        RESULTS["playwright"] = (True, f"desktop+mobile captured for {input_url}")
    except Exception as e:
        RESULTS["playwright"] = (False, f"{type(e).__name__}: {e}")
        return _report()

    # 2
    try:
        skill = stage_skillui(reference_url)
        RESULTS["skillui"] = (True, f"design_md={Path(skill['design_md']).name}")
    except Exception as e:
        RESULTS["skillui"] = (False, f"{type(e).__name__}: {e}")
        skill = {"tokens": {}}

    # 3
    try:
        design = await stage_llm(scrape, skill.get("tokens", {}))
        RESULTS["llm"] = (True, f"pages={len(design.get('pages', []))}")
    except Exception as e:
        RESULTS["llm"] = (False, f"{type(e).__name__}: {e}")
        design = {
            "pages": [
                {"route": "/", "title": "Home", "purpose": "Landing"},
                {"route": "/about", "title": "About", "purpose": "About"},
            ],
            "designTokens": {"primary": "#0ea5e9", "bg": "#0b0b0f", "fg": "#fafafa"},
        }

    # 4
    try:
        dep = await stage_vercel(design)
        RESULTS["vercel"] = (True, dep["url"])
    except Exception as e:
        RESULTS["vercel"] = (False, f"{type(e).__name__}: {e}")

    return _report()


def _report() -> int:
    print("\n======== POC RESULTS ========")
    all_ok = True
    for k in ("playwright", "skillui", "llm", "vercel"):
        ok, msg = RESULTS.get(k, (False, "not run"))
        flag = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  {k:<11} {flag}  {msg}")
    print("=============================")
    print(f"Artifacts: {WORKDIR}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
