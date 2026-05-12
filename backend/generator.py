"""Generate a complete Next.js 14 App Router project from an LLM plan.

Produces a production-ready folder with:
- Tailwind CSS + Google Fonts loaded via next/font
- Framer Motion for animations + the signature "explode on scroll" hero
- Video hero section (/public/hero.mp4 if uploaded) with scroll-driven layer separation
- Responsive nav + footer on every page
- Multi-page routes for everything in plan['pages']
- Anti-slop content retention (uses the original paragraphs/headings verbatim)
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any


def _safe_id(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]", "_", (s or "X").strip()) or "X"
    if s[0].isdigit():
        s = "_" + s
    return s


def _slug_to_component_name(slug: str) -> str:
    """Convert 'aurora-hero' -> 'AuroraHero' for use as an import name."""
    parts = re.split(r"[^A-Za-z0-9]+", slug or "")
    name = "".join(p[:1].upper() + p[1:] for p in parts if p)
    if not name:
        name = "GenComponent"
    if name[0].isdigit():
        name = "C" + name
    return name


def _is_light_hex(hex_color: str) -> bool:
    try:
        h = (hex_color or "#000").lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        # luminance
        y = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return y > 160
    except Exception:
        return False


def _route_to_segment(route: str) -> list[str]:
    r = (route or "/").strip()
    if r in ("", "/"):
        return []
    parts = [p for p in r.split("/") if p]
    return parts


def _json_s(v: Any) -> str:
    """Python value -> safe JS literal (JSON)."""
    return json.dumps(v, ensure_ascii=False)


def generate_project(
    plan: dict[str, Any],
    out_dir: Path,
    hero_video_path: str | None = None,
    project_slug: str | None = None,
    template: dict | None = None,
    images: dict[str, str] | None = None,
    picked_components: list[dict] | None = None,
) -> Path:
    """Write the entire Next.js project to out_dir."""
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    design = plan.get("design", {}) or {}
    brand = plan.get("brand", {}) or {}
    pages = plan.get("pages", []) or []
    nav = plan.get("nav", []) or []
    images = images or {}
    picked_components = picked_components or []

    # Template overrides design tokens (so every site looks different)
    tpl = template or {}
    tpl_palette = tpl.get("palette") or {}
    primary = tpl_palette.get("primary") or design.get("primary") or "#2DE3C6"
    primary_2 = tpl_palette.get("primary_2") or design.get("primary_2") or "#0EA5A4"
    accent = tpl_palette.get("accent") or design.get("accent") or "#FFB86B"
    bg = tpl_palette.get("bg") or design.get("bg") or "#070A0E"
    bg_2 = tpl_palette.get("bg_2") or design.get("bg_2") or "#0B1220"
    fg = tpl_palette.get("fg") or design.get("fg") or "#EAF0FF"
    muted_fg = tpl_palette.get("muted_fg") or design.get("muted_fg") or "#9AA3B2"
    font_heading = tpl.get("font_heading") or design.get("font_heading") or "Space Grotesk"
    font_body = tpl.get("font_body") or design.get("font_body") or "Inter"
    radius = tpl.get("radius") or design.get("radius") or "14px"
    hero_kind = tpl.get("hero") or "explode_video"
    decor_kind = tpl.get("decor") or "grain"
    motion_pack = tpl.get("motion") or "soft_reveal"
    layout_kind = tpl.get("layout") or "editorial"
    is_light = _is_light_hex(bg)
    brand_name = brand.get("name") or (project_slug or "Brand").replace("-", " ").title()
    tagline = brand.get("tagline") or "A new standard."

    def _gf_spec(font: str) -> str:
        return font.replace(" ", "+") + ":wght@300;400;500;600;700;800"

    # package.json
    (out_dir / "package.json").write_text(
        json.dumps(
            {
                "name": (project_slug or "webforge-site").lower(),
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
                    "framer-motion": "11.3.19",
                    "lucide-react": "^0.453.0",
                    "clsx": "^2.1.1",
                    "tailwindcss": "3.4.10",
                    "postcss": "8.4.41",
                    "autoprefixer": "10.4.20",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "next.config.mjs").write_text(
        "const nextConfig = { reactStrictMode: true, eslint: { ignoreDuringBuilds: true }, typescript: { ignoreBuildErrors: true }, images: { unoptimized: true } };\nexport default nextConfig;\n",
        encoding="utf-8",
    )
    (out_dir / "postcss.config.mjs").write_text(
        "export default { plugins: { tailwindcss: {}, autoprefixer: {} } };\n",
        encoding="utf-8",
    )
    (out_dir / "jsconfig.json").write_text(
        json.dumps(
            {"compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["./*"]}}}, indent=2
        )
    )

    # Tailwind config
    (out_dir / "tailwind.config.mjs").write_text(
        "/** @type {import('tailwindcss').Config} */\n"
        "export default {\n"
        "  content: ['./app/**/*.{js,jsx}', './components/**/*.{js,jsx}'],\n"
        "  theme: {\n"
        "    extend: {\n"
        f"      colors: {{ brand: {{ DEFAULT: '{primary}', fg: '{fg}', bg: '{bg}', bg2: '{bg_2}', muted: '{muted_fg}', primary2: '{primary_2}', accent: '{accent}' }} }},\n"
        f"      fontFamily: {{ display: ['\"{font_heading}\"','ui-sans-serif','system-ui'], sans: ['\"{font_body}\"','ui-sans-serif','system-ui'] }},\n"
        f"      borderRadius: {{ xl: '{radius}' }},\n"
        "      animation: { pulseSoft: 'pulseSoft 2s ease-in-out infinite', marquee: 'marquee 28s linear infinite', floatY: 'floatY 8s ease-in-out infinite', spinSlow: 'spin 22s linear infinite' },\n"
        "      keyframes: {\n"
        "        pulseSoft: { '0%,100%': { opacity: 0.7 }, '50%': { opacity: 1 } },\n"
        "        marquee: { '0%': { transform: 'translateX(0)' }, '100%': { transform: 'translateX(-50%)' } },\n"
        "        floatY: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-16px)' } },\n"
        "      },\n"
        "    },\n"
        "  },\n"
        "  plugins: [],\n"
        "};\n",
        encoding="utf-8",
    )

    app_dir = out_dir / "app"
    app_dir.mkdir()
    components_dir = out_dir / "components"
    components_dir.mkdir()
    public_dir = out_dir / "public"
    public_dir.mkdir()

    # Hero video (optional user upload)
    has_video = False
    if hero_video_path and Path(hero_video_path).exists():
        try:
            shutil.copy2(hero_video_path, public_dir / "hero.mp4")
            has_video = True
        except Exception:
            pass

    # Copy generated images (hero.jpg, section_N.jpg ...) if provided
    has_hero_image = False
    copied_section_images: list[str] = []
    if images:
        for fname, src in images.items():
            src_path = Path(src) if os.path.isabs(src) else (public_dir / src)
            # images values are just filenames already inside public_dir when coming from image_gen
            # We expect image_gen to have written them directly into public_dir OR provided an absolute path
            if not src_path.exists():
                alt = public_dir / fname
                if alt.exists():
                    src_path = alt
            if src_path.exists():
                target = public_dir / fname
                if src_path != target:
                    try:
                        shutil.copy2(src_path, target)
                    except Exception:
                        pass
                if fname == "hero.jpg":
                    has_hero_image = True
                elif fname.startswith("section_"):
                    copied_section_images.append(fname)

    # global.css with template-specific decorations and any Google Font via CSS import
    heading_css_family = font_heading.replace(" ", "+") + ":wght@300;400;500;600;700;800"
    body_css_family = font_body.replace(" ", "+") + ":wght@300;400;500;600;700"
    (app_dir / "globals.css").write_text(
        "@import url('https://fonts.googleapis.com/css2?family="
        + heading_css_family
        + "&family="
        + body_css_family
        + "&display=swap');\n"
        "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n\n"
        f":root {{ --bg: {bg}; --bg2: {bg_2}; --fg: {fg}; --muted: {muted_fg}; "
        f"--primary: {primary}; --primary-2: {primary_2}; --accent: {accent}; --radius: {radius}; }}\n"
        "html, body { background: var(--bg); color: var(--fg); }\n"
        f"body {{ font-family: '{font_body}', ui-sans-serif, system-ui, -apple-system; -webkit-font-smoothing: antialiased; }}\n"
        f"h1,h2,h3,h4 {{ font-family: '{font_heading}', ui-sans-serif, system-ui; letter-spacing: -0.02em; }}\n"
        "::selection { background: var(--primary); color: var(--bg); }\n"
        ".glow { box-shadow: 0 20px 80px -20px color-mix(in srgb, var(--primary) 45%, transparent); }\n"
        + _decor_css(decor_kind, primary, accent, is_light)
        + _hero_grad_css(primary, accent, bg_2, is_light),
        encoding="utf-8",
    )

    # layout.jsx (root) — no next/font (Google Font is imported via CSS, enabling ANY font)
    nav_items_js = _json_s(
        [{"label": (n.get("label") or ""), "href": (n.get("href") or "/")} for n in nav]
        or [{"label": p.get("title", ""), "href": p.get("route", "/")} for p in pages][:6]
    )
    (app_dir / "layout.jsx").write_text(
        (
            "import './globals.css';\n"
            "import Nav from '@/components/Nav';\n"
            "import Footer from '@/components/Footer';\n"
            f"export const metadata = {{ title: {_json_s(brand_name)}, description: {_json_s(tagline)} }};\n"
            f"const NAV = {nav_items_js};\n"
            "export default function RootLayout({ children }) {\n"
            "  return (\n"
            "    <html lang=\"en\">\n"
            "      <body className=\"min-h-screen bg-brand-bg text-brand-fg\">\n"
            f"        <Nav items={{NAV}} brand={_json_s(brand_name)} />\n"
            "        <main>{children}</main>\n"
            f"        <Footer brand={_json_s(brand_name)} items={{NAV}} />\n"
            "      </body>\n"
            "    </html>\n"
            "  );\n"
            "}\n"
        ),
        encoding="utf-8",
    )

    # Components
    (components_dir / "Nav.jsx").write_text(_component_nav(is_light), encoding="utf-8")
    (components_dir / "Footer.jsx").write_text(_component_footer(), encoding="utf-8")
    (components_dir / "Reveal.jsx").write_text(_component_reveal(motion_pack), encoding="utf-8")
    (components_dir / "Section.jsx").write_text(_component_section(), encoding="utf-8")
    # Template-aware Hero router (keeps name ExplodingHero for backward compatibility)
    (components_dir / "ExplodingHero.jsx").write_text(
        _component_hero_router(
            hero_kind=hero_kind,
            has_video=has_video,
            has_hero_image=has_hero_image,
            primary=primary,
            accent=accent,
            is_light=is_light,
        ),
        encoding="utf-8",
    )
    # 3D decoration component (pseudo-3D via CSS + Framer Motion)
    (components_dir / "Decor3D.jsx").write_text(
        _component_decor_3d(hero_kind, primary, accent), encoding="utf-8"
    )

    # Write picked 21st.dev / motionsites-inspired components into
    # components/generated/ and build a slug->import map.
    picks_by_section: dict[int, str] = {}
    if picked_components:
        gen_components_dir = components_dir / "generated"
        gen_components_dir.mkdir(exist_ok=True)
        written_slugs: set[str] = set()
        try:
            from component_library import get_component_jsx, collect_deps  # local import to avoid hard dep at module level
            for p in picked_components:
                slug = p.get("slug")
                if not slug or slug in written_slugs:
                    # still record the mapping for the section
                    if slug:
                        picks_by_section[int(p.get("section_idx", -1))] = slug
                    continue
                body = get_component_jsx(slug)
                if not body:
                    continue
                comp_name = _slug_to_component_name(slug)
                file_body = body.replace(
                    "export default function ",
                    f"export default function {comp_name}Impl_",
                    1,
                )
                # Fallback: write the JSX as-is if we couldn't rename
                if f"function {comp_name}Impl_" not in file_body:
                    file_body = body
                (gen_components_dir / f"{slug}.jsx").write_text(
                    body, encoding="utf-8"
                )
                written_slugs.add(slug)
                picks_by_section[int(p.get("section_idx", -1))] = slug
            # Add any extra deps to package.json if needed
            extra_deps = collect_deps(picked_components)
            if extra_deps:
                pkg_path = out_dir / "package.json"
                try:
                    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
                    deps = pkg.setdefault("dependencies", {})
                    if "framer-motion" in extra_deps and "framer-motion" not in deps:
                        deps["framer-motion"] = "11.3.19"
                    pkg_path.write_text(json.dumps(pkg, indent=2), encoding="utf-8")
                except Exception:
                    pass
        except Exception:
            picks_by_section = {}

    # Write each page
    home_page = None
    for pg in pages:
        route = pg.get("route") or "/"
        if route == "/":
            home_page = pg
            continue
        segs = _route_to_segment(route)
        sub = app_dir
        for s in segs:
            sub = sub / re.sub(r"[^a-z0-9_-]", "-", s.lower())
            sub.mkdir(parents=True, exist_ok=True)
        (sub / "page.jsx").write_text(
            _page_template(pg, brand_name, tagline, is_home=False),
            encoding="utf-8",
        )

    if home_page is None:
        home_page = {
            "route": "/",
            "title": brand_name,
            "sections": [
                {"kind": "hero_video", "heading": tagline, "subheading": "", "items": [], "cta": {"label": "Learn more", "href": "/about"}}
            ],
        }
    (app_dir / "page.jsx").write_text(
        _page_template(home_page, brand_name, tagline, is_home=True, picks_by_section=picks_by_section),
        encoding="utf-8",
    )

    return out_dir


def _decor_css(kind: str, primary: str, accent: str, is_light: bool) -> str:
    ink = "rgba(0,0,0,0.7)" if is_light else "rgba(255,255,255,0.7)"
    dot = "rgba(0,0,0,0.12)" if is_light else "rgba(255,255,255,0.06)"
    line = "rgba(0,0,0,0.06)" if is_light else "rgba(255,255,255,0.04)"
    base = (
        ".noise::before { content: ''; position: absolute; inset: 0; pointer-events: none; opacity: .05; "
        "background-image: url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence baseFrequency='0.9'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.7'/></svg>\"); background-size: 180px; }\n"
        ".grain { position: relative; }\n"
        f".grain::after {{ content: ''; position: absolute; inset: 0; pointer-events: none; opacity:.04; background-image: radial-gradient({ink} 1px, transparent 1px); background-size: 3px 3px; }}\n"
    )
    if kind == "dot_grid":
        base += f".decor-bg {{ background-image: radial-gradient({dot} 1px, transparent 1px); background-size: 22px 22px; }}\n"
    elif kind == "line_grid":
        base += (
            f".decor-bg {{ background-image: linear-gradient({line} 1px, transparent 1px), linear-gradient(90deg, {line} 1px, transparent 1px); background-size: 48px 48px; }}\n"
        )
    elif kind == "orbs":
        base += (
            f".decor-bg::before {{ content:''; position:absolute; inset:auto; width: 360px; height: 360px; border-radius: 999px; background: radial-gradient(circle, {primary}33, transparent 60%); top: 10%; left: -80px; filter: blur(40px); animation: floatY 10s ease-in-out infinite; }}\n"
            f".decor-bg::after {{ content:''; position:absolute; width: 260px; height: 260px; border-radius: 999px; background: radial-gradient(circle, {accent}33, transparent 60%); bottom: 10%; right: -60px; filter: blur(36px); animation: floatY 12s ease-in-out -3s infinite; }}\n"
        )
    elif kind == "stars":
        base += (
            ".decor-bg { background-image: radial-gradient(white 1px, transparent 1px); background-size: 4px 4px; opacity: 0.35; }\n"
        )
    elif kind == "scanlines":
        base += (
            f".decor-bg {{ background-image: repeating-linear-gradient(0deg, {line} 0px, {line} 1px, transparent 1px, transparent 4px); }}\n"
        )
    elif kind == "mesh_gradient":
        base += (
            f".decor-bg {{ background: conic-gradient(from 200deg at 30% 20%, {primary}22, transparent 40%, {accent}22, transparent 70%); filter: blur(30px); }}\n"
        )
    elif kind == "glitch_lines":
        base += (
            f".decor-bg {{ background-image: repeating-linear-gradient(90deg, {primary}0D 0 2px, transparent 2px 16px); }}\n"
        )
    elif kind == "blurred_blobs":
        base += (
            f".decor-bg {{ background: radial-gradient(400px 300px at 20% 30%, {primary}22, transparent 60%), radial-gradient(500px 380px at 80% 70%, {accent}1f, transparent 65%); filter: blur(8px); }}\n"
        )
    return base


def _hero_grad_css(primary: str, accent: str, bg_2: str, is_light: bool) -> str:
    if is_light:
        return (
            f".hero-grad {{ background: radial-gradient(900px 420px at 18% 10%, {primary}22, transparent 60%), "
            f"radial-gradient(700px 360px at 82% 0%, {accent}18, transparent 55%), "
            f"linear-gradient(180deg, rgba(255,255,255,0.5), transparent); }}\n"
        )
    return (
        f".hero-grad {{ background: radial-gradient(900px 420px at 18% 10%, {primary}22, transparent 60%), "
        f"radial-gradient(700px 360px at 82% 0%, {accent}18, transparent 55%); }}\n"
    )


def _component_nav(is_light: bool = False) -> str:
    txt = "rgba(0,0,0,0.75)" if is_light else "rgba(255,255,255,0.75)"
    border = "rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.06)"
    return (
        "'use client';\n"
        "import { useState, useEffect } from 'react';\n"
        "import Link from 'next/link';\n"
        "import { Menu, X } from 'lucide-react';\n"
        "export default function Nav({ items, brand }) {\n"
        "  const [open, setOpen] = useState(false);\n"
        "  const [scrolled, setScrolled] = useState(false);\n"
        "  useEffect(() => { const onScroll = () => setScrolled(window.scrollY > 12); window.addEventListener('scroll', onScroll); return () => window.removeEventListener('scroll', onScroll); }, []);\n"
        "  return (\n"
        "    <header className={'fixed top-0 inset-x-0 z-50 transition-colors ' + (scrolled ? 'backdrop-blur-md bg-[color:var(--bg)]/70 border-b' : '')}\n"
        f"      style={{{{ borderColor: '{border}' }}}}>\n"
        "      <div className=\"max-w-[1200px] mx-auto px-5 sm:px-8 h-16 flex items-center justify-between\">\n"
        "        <Link href=\"/\" className=\"font-display text-lg tracking-tight\">{brand}</Link>\n"
        f"        <nav className=\"hidden md:flex items-center gap-8 text-sm\" style={{{{ color: '{txt}' }}}}>\n"
        "          {items?.map((it) => (<Link key={it.href} href={it.href} className=\"hover:opacity-80 transition-opacity\">{it.label}</Link>))}\n"
        "        </nav>\n"
        f"        <button aria-label=\"Menu\" onClick={{() => setOpen(v => !v)}} className=\"md:hidden inline-flex items-center justify-center size-10 rounded-xl border\" style={{{{ borderColor: '{border}' }}}}>{{open ? <X size={{18}}/> : <Menu size={{18}}/>}}</button>\n"
        "      </div>\n"
        "      {open && (\n"
        "        <div className=\"md:hidden border-t bg-[color:var(--bg)]/95 backdrop-blur\"\n"
        f"          style={{{{ borderColor: '{border}' }}}}>\n"
        "          <div className=\"px-5 py-4 flex flex-col gap-3\">\n"
        "            {items?.map((it) => (<Link key={it.href} href={it.href} onClick={() => setOpen(false)} className=\"text-base py-1.5\">{it.label}</Link>))}\n"
        "          </div>\n"
        "        </div>\n"
        "      )}\n"
        "    </header>\n"
        "  );\n"
        "}\n"
    )


def _component_reveal(motion_pack: str = "soft_reveal") -> str:
    if motion_pack == "stagger_cascade":
        init = "{ opacity: 0, y: 22 }"
        anim = "{ opacity: 1, y: 0 }"
        trans = "{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay: 0.06 + delay }"
    elif motion_pack == "bold_parallax":
        init = "{ opacity: 0, y: 40, scale: 0.98 }"
        anim = "{ opacity: 1, y: 0, scale: 1 }"
        trans = "{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay }"
    elif motion_pack == "tilt_3d":
        init = "{ opacity: 0, rotateX: 12, y: 14 }"
        anim = "{ opacity: 1, rotateX: 0, y: 0 }"
        trans = "{ duration: 0.65, ease: [0.22, 1, 0.36, 1], delay }"
    elif motion_pack == "marquee_loop":
        init = "{ opacity: 0, x: 20 }"
        anim = "{ opacity: 1, x: 0 }"
        trans = "{ duration: 0.55, ease: [0.22, 1, 0.36, 1], delay }"
    elif motion_pack == "magnetic_hover":
        init = "{ opacity: 0, y: 10 }"
        anim = "{ opacity: 1, y: 0 }"
        trans = "{ duration: 0.5, ease: 'easeOut', delay }"
    else:
        init = "{ opacity: 0, y: 14 }"
        anim = "{ opacity: 1, y: 0 }"
        trans = "{ duration: 0.6, ease: [0.22, 1, 0.36, 1], delay }"
    return (
        "'use client';\n"
        "import { motion } from 'framer-motion';\n"
        "export default function Reveal({ children, delay = 0, className = '' }) {\n"
        f"  return (<motion.div initial={{{init}}} whileInView={{{anim}}} viewport={{{{ once: true, margin: '-80px' }}}} transition={{{trans}}} className={{className}}>{{children}}</motion.div>);\n"
        "}\n"
    )


def _component_section() -> str:
    return (
        "export default function Section({ id, children, className = '' }) {\n"
        "  return (\n"
        "    <section id={id} className={'max-w-[1200px] mx-auto px-5 sm:px-8 py-16 sm:py-24 ' + className}>{children}</section>\n"
        "  );\n"
        "}\n"
    )


def _component_decor_3d(hero_kind: str, primary: str, accent: str) -> str:
    if hero_kind == "orb_3d":
        inner = (
            "<motion.div className=\"absolute inset-0 grid place-items-center\" aria-hidden>"
            "<motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 28, ease: 'linear' }} className=\"relative w-[420px] h-[420px]\">"
            "<div className=\"absolute inset-0 rounded-full\" style={{ background: 'conic-gradient(from 0deg, "
            + primary
            + ", "
            + accent
            + ", "
            + primary
            + ")', filter: 'blur(42px)', opacity: .75 }} />"
            "<div className=\"absolute inset-6 rounded-full border border-white/20\" style={{ boxShadow: '0 40px 120px -30px "
            + primary
            + "' }} />"
            "<div className=\"absolute inset-14 rounded-full border border-white/10\" />"
            "<div className=\"absolute inset-24 rounded-full border border-white/10\" />"
            "</motion.div>"
            "</motion.div>"
        )
    elif hero_kind == "perspective_stack":
        inner = (
            "<div className=\"absolute inset-0 grid place-items-center perspective-[1200px]\" aria-hidden>"
            "<div className=\"relative w-[520px] h-[340px]\" style={{ transformStyle:'preserve-3d', transform:'rotateX(22deg) rotateY(-14deg)' }}>"
            "<div className=\"absolute inset-0 rounded-2xl border border-white/15 bg-white/[0.04] animate-floatY\" style={{ transform:'translateZ(0px)' }} />"
            "<div className=\"absolute inset-0 rounded-2xl border border-white/10 bg-white/[0.03]\" style={{ transform:'translateZ(-60px) translateX(30px) translateY(20px)' }} />"
            "<div className=\"absolute inset-0 rounded-2xl border border-white/10 bg-white/[0.02]\" style={{ transform:'translateZ(-120px) translateX(60px) translateY(40px)' }} />"
            "</div>"
            "</div>"
        )
    elif hero_kind == "grid_mosaic":
        inner = (
            "<div className=\"absolute inset-0 grid grid-cols-6 grid-rows-4 gap-3 p-10\" aria-hidden>"
            "{Array.from({length:24}).map((_,i)=>(<div key={i} className=\"rounded-xl border border-white/10 bg-white/[0.03]\" style={{ animation: 'pulseSoft 2s ease-in-out infinite', animationDelay: (i*0.06)+'s' }} />))}"
            "</div>"
        )
    elif hero_kind == "marquee":
        inner = (
            "<div className=\"absolute inset-x-0 bottom-16 overflow-hidden\" aria-hidden>"
            "<div className=\"flex gap-4 whitespace-nowrap animate-marquee\">"
            "{Array.from({length:14}).map((_,i)=>(<span key={i} className=\"inline-block px-4 py-2 rounded-full border border-white/10 text-white/70 text-sm bg-white/[0.03]\">\u2605 element {i+1}</span>))}"
            "{Array.from({length:14}).map((_,i)=>(<span key={'b'+i} className=\"inline-block px-4 py-2 rounded-full border border-white/10 text-white/70 text-sm bg-white/[0.03]\">\u2605 element {i+1}</span>))}"
            "</div></div>"
        )
    else:
        inner = ""
    return (
        "'use client';\n"
        "import { motion } from 'framer-motion';\n"
        "export default function Decor3D() {\n"
        "  return (<>\n"
        "    " + inner + "\n"
        "  </>);\n"
        "}\n"
    )


def _component_hero_router(
    hero_kind: str,
    has_video: bool,
    has_hero_image: bool,
    primary: str,
    accent: str,
    is_light: bool,
) -> str:
    """Render the template's hero variant. Kept component name 'ExplodingHero' for page compatibility."""
    base = (
        "'use client';\n"
        "import { useRef } from 'react';\n"
        "import { motion, useScroll, useTransform, useReducedMotion, useMotionValue } from 'framer-motion';\n"
        "import { ArrowUpRight } from 'lucide-react';\n"
        "import Link from 'next/link';\n"
        "import Decor3D from './Decor3D';\n"
    )
    media_tag = ""
    if has_video:
        media_tag = "<video autoPlay muted loop playsInline preload=\"auto\" src=\"/hero.mp4\" className=\"w-full h-full object-cover\" />"
    elif has_hero_image:
        media_tag = "<img src=\"/hero.jpg\" alt=\"\" className=\"w-full h-full object-cover\" />"
    else:
        media_tag = "<div className=\"absolute inset-0 hero-grad\" />"

    # Default "explode video" variant (original)
    if hero_kind in ("explode_video", "split_media", "asymmetric_cards", "parallax_layers"):
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  const ref = useRef(null);\n"
            "  const reduce = useReducedMotion();\n"
            "  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });\n"
            "  const progress = reduce ? { get: () => 0 } : scrollYProgress;\n"
            "  const mediaScale = useTransform(progress, [0, 1], [1, 0.62]);\n"
            "  const mediaRotate = useTransform(progress, [0, 1], [0, -4]);\n"
            "  const mediaY = useTransform(progress, [0, 1], [0, -40]);\n"
            "  const leftX = useTransform(progress, [0, 1], [0, -260]);\n"
            "  const leftR = useTransform(progress, [0, 1], [0, -8]);\n"
            "  const rightX = useTransform(progress, [0, 1], [0, 260]);\n"
            "  const rightR = useTransform(progress, [0, 1], [0, 8]);\n"
            "  const headY = useTransform(progress, [0, 1], [0, -80]);\n"
            "  const headO = useTransform(progress, [0, 0.8], [1, 0.25]);\n"
            "  const subO = useTransform(progress, [0, 0.5], [1, 0]);\n"
            "  return (\n"
            "    <div ref={ref} className=\"relative min-h-[88vh] pt-28 pb-16 overflow-hidden noise hero-grad\">\n"
            "      <div className=\"absolute inset-0 decor-bg pointer-events-none\" />\n"
            "      <div className=\"max-w-[1200px] mx-auto px-5 sm:px-8 relative z-10\">\n"
            "        <motion.h1 style={{ y: headY, opacity: headO }} className=\"font-display text-5xl sm:text-6xl lg:text-7xl font-semibold tracking-tight leading-[1.02] max-w-4xl\">{heading}</motion.h1>\n"
            "        {subheading && (<motion.p style={{ opacity: subO }} className=\"mt-5 text-base sm:text-lg opacity-75 max-w-xl\">{subheading}</motion.p>)}\n"
            "        {cta?.label && (<div className=\"mt-8\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-5 py-3 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "      </div>\n"
            "      <div className=\"relative mt-10 sm:mt-14\">\n"
            "        <motion.div style={{ scale: mediaScale, rotate: mediaRotate, y: mediaY }} className=\"relative mx-auto max-w-[1120px] aspect-[16/9] rounded-2xl overflow-hidden border border-white/10 glow bg-black\">\n"
            f"          {media_tag}\n"
            "          <div className=\"absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none\" />\n"
            "        </motion.div>\n"
            "        <motion.div style={{ x: leftX, rotate: leftR }} className=\"hidden md:block absolute left-[-60px] top-12 w-[320px] aspect-[4/3] rounded-xl border border-white/10 bg-white/5 backdrop-blur glow\" aria-hidden />\n"
            "        <motion.div style={{ x: rightX, rotate: rightR }} className=\"hidden md:block absolute right-[-60px] bottom-8 w-[340px] aspect-[5/3] rounded-xl border border-white/10 bg-white/5 backdrop-blur glow\" aria-hidden />\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "orb_3d" or hero_kind == "perspective_stack" or hero_kind == "grid_mosaic":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  const ref = useRef(null);\n"
            "  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });\n"
            "  const headO = useTransform(scrollYProgress, [0, 0.8], [1, 0.2]);\n"
            "  return (\n"
            "    <div ref={ref} className=\"relative min-h-[88vh] pt-28 pb-20 overflow-hidden noise hero-grad\">\n"
            "      <div className=\"absolute inset-0 decor-bg pointer-events-none\" />\n"
            "      <Decor3D />\n"
            "      <div className=\"relative z-10 max-w-[1200px] mx-auto px-5 sm:px-8 text-center mt-10\">\n"
            "        <motion.h1 style={{ opacity: headO }} className=\"font-display text-5xl sm:text-7xl lg:text-8xl font-semibold tracking-tight leading-[1.02] max-w-5xl mx-auto\">{heading}</motion.h1>\n"
            "        {subheading && (<p className=\"mt-5 text-base sm:text-lg opacity-75 max-w-2xl mx-auto\">{subheading}</p>)}\n"
            "        {cta?.label && (<div className=\"mt-8 flex justify-center\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-5 py-3 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "marquee":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  return (\n"
            "    <div className=\"relative min-h-[80vh] pt-28 pb-20 overflow-hidden noise hero-grad\">\n"
            "      <div className=\"absolute inset-0 decor-bg pointer-events-none\" />\n"
            "      <div className=\"relative z-10 max-w-[1200px] mx-auto px-5 sm:px-8\">\n"
            "        <div className=\"overflow-hidden\">\n"
            "          <div className=\"flex gap-6 whitespace-nowrap animate-marquee font-display text-6xl sm:text-7xl lg:text-8xl font-semibold tracking-tight opacity-90\">\n"
            "            <span>{heading}</span><span className=\"opacity-50\">\u25CF</span><span>{heading}</span><span className=\"opacity-50\">\u25CF</span>\n"
            "            <span>{heading}</span><span className=\"opacity-50\">\u25CF</span><span>{heading}</span>\n"
            "          </div>\n"
            "        </div>\n"
            "        {subheading && (<p className=\"mt-6 text-base sm:text-lg opacity-75 max-w-xl\">{subheading}</p>)}\n"
            "        {cta?.label && (<div className=\"mt-8\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-5 py-3 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "      </div>\n"
            "      <div className=\"relative mt-10 mx-auto max-w-[1120px] aspect-[16/9] rounded-2xl overflow-hidden border border-white/10 glow bg-black\">\n"
            f"        {media_tag}\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "fullbleed_parallax":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  const ref = useRef(null);\n"
            "  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });\n"
            "  const y = useTransform(scrollYProgress, [0, 1], [0, -120]);\n"
            "  const scale = useTransform(scrollYProgress, [0, 1], [1, 1.08]);\n"
            "  return (\n"
            "    <div ref={ref} className=\"relative min-h-screen overflow-hidden\">\n"
            "      <motion.div style={{ scale, y }} className=\"absolute inset-0\">\n"
            f"        {media_tag}\n"
            "        <div className=\"absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/80\" />\n"
            "        <div className=\"absolute inset-0 decor-bg opacity-50\" />\n"
            "      </motion.div>\n"
            "      <div className=\"relative z-10 max-w-[1200px] mx-auto px-5 sm:px-8 min-h-screen flex flex-col justify-end pb-20 pt-32\">\n"
            "        <motion.h1 initial={{opacity:0,y:40}} animate={{opacity:1,y:0}} transition={{duration:1,ease:[0.22,1,0.36,1]}} className=\"font-display text-6xl sm:text-8xl lg:text-[10rem] font-bold leading-[0.92] tracking-tight text-white drop-shadow-2xl max-w-5xl\">{heading}</motion.h1>\n"
            "        {subheading && (<motion.p initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.3}} className=\"mt-6 text-lg text-white/85 max-w-xl drop-shadow-lg\">{subheading}</motion.p>)}\n"
            "        {cta?.label && (<div className=\"mt-8\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-6 py-3.5 bg-white text-black font-medium hover:brightness-95 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "framed_split":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  return (\n"
            "    <div className=\"relative min-h-screen pt-24 overflow-hidden\">\n"
            "      <div className=\"absolute inset-0 hero-grad\" />\n"
            "      <div className=\"absolute inset-0 decor-bg opacity-40\" />\n"
            "      <div className=\"relative z-10 max-w-[1400px] mx-auto px-5 sm:px-8 grid lg:grid-cols-[1.1fr_1fr] gap-8 lg:gap-12 items-center min-h-[calc(100vh-96px)] pb-16\">\n"
            "        <motion.div initial={{opacity:0,x:-30}} animate={{opacity:1,x:0}} transition={{duration:0.9,ease:[0.22,1,0.36,1]}}>\n"
            "          <div className=\"chip mb-6 inline-flex\" style={{ borderColor: 'rgba(255,255,255,0.14)' }}><span className=\"size-1.5 rounded-full bg-brand\"/>Signature</div>\n"
            "          <h1 className=\"font-display text-[12vw] sm:text-[9vw] lg:text-[8rem] font-bold leading-[0.88] tracking-tight\">{heading}</h1>\n"
            "          {subheading && (<p className=\"mt-6 text-base sm:text-lg opacity-75 max-w-lg\">{subheading}</p>)}\n"
            "          {cta?.label && (<div className=\"mt-8\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-6 py-3.5 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "        </motion.div>\n"
            "        <motion.div initial={{opacity:0,scale:0.95}} animate={{opacity:1,scale:1}} transition={{duration:1,ease:[0.22,1,0.36,1]}} className=\"relative aspect-[4/5] rounded-3xl overflow-hidden border border-white/10 glow bg-black\">\n"
            f"          {media_tag}\n"
            "          <div className=\"absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent pointer-events-none\" />\n"
            "        </motion.div>\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "architectural_tilt":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  const ref = useRef(null);\n"
            "  const mx = useMotionValue(0.5); const my = useMotionValue(0.5);\n"
            "  const rX = useTransform(my, [0,1], [6,-6]); const rY = useTransform(mx, [0,1], [-8,8]);\n"
            "  return (\n"
            "    <div ref={ref} onMouseMove={(e)=>{const r=e.currentTarget.getBoundingClientRect();mx.set((e.clientX-r.left)/r.width);my.set((e.clientY-r.top)/r.height);}} className=\"relative min-h-screen pt-28 overflow-hidden perspective-[1600px]\">\n"
            "      <div className=\"absolute inset-0 bg-black\" />\n"
            "      <motion.div style={{ rotateX: rX, rotateY: rY, transformStyle:'preserve-3d' }} className=\"absolute inset-0\">\n"
            f"        {media_tag}\n"
            "        <div className=\"absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/80\" />\n"
            "      </motion.div>\n"
            "      <div className=\"relative z-10 max-w-[1200px] mx-auto px-5 sm:px-8 pt-10 pb-20 grid min-h-[calc(100vh-112px)] place-items-center text-center\">\n"
            "        <div>\n"
            "          <motion.h1 initial={{opacity:0,y:30}} animate={{opacity:1,y:0}} transition={{duration:1}} className=\"font-display text-6xl sm:text-8xl lg:text-[9rem] font-semibold tracking-[-0.04em] leading-[0.92] text-white\">{heading}</motion.h1>\n"
            "          {subheading && (<p className=\"mt-6 text-base sm:text-lg text-white/80 max-w-xl mx-auto\">{subheading}</p>)}\n"
            "          {cta?.label && (<div className=\"mt-8\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-6 py-3.5 bg-brand text-black font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "        </div>\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        ).replace("from 'framer-motion'", "from 'framer-motion'")

    if hero_kind == "portrait_mega_type":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  const letters = (heading || '').split('');\n"
            "  return (\n"
            "    <div className=\"relative min-h-screen pt-24 overflow-hidden hero-grad\">\n"
            "      <div className=\"absolute inset-0 decor-bg opacity-60\" />\n"
            "      <div className=\"absolute inset-0 grid place-items-center pt-28 pointer-events-none\">\n"
            "        <div className=\"relative w-[72%] max-w-[640px] aspect-[4/5] rounded-3xl overflow-hidden border border-white/10 glow bg-black\">\n"
            f"          {media_tag}\n"
            "          <div className=\"absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/50\" />\n"
            "        </div>\n"
            "      </div>\n"
            "      <div className=\"relative z-10 max-w-[1400px] mx-auto px-5 sm:px-8 min-h-screen flex flex-col justify-between pt-10 pb-14 text-center\">\n"
            "        <div className=\"flex justify-center gap-[0.04em] font-display text-[22vw] sm:text-[18vw] lg:text-[15vw] font-bold tracking-[-0.05em] leading-none select-none mix-blend-difference text-white\">\n"
            "          {letters.map((c, i) => (<motion.span key={i} initial={{opacity:0, y:40}} animate={{opacity:1, y:0}} transition={{duration:0.7, delay: i*0.04, ease:[0.22,1,0.36,1]}}>{c === ' ' ? '\u00A0' : c}</motion.span>))}\n"
            "        </div>\n"
            "        <div className=\"flex flex-col items-center gap-4\">\n"
            "          {subheading && (<p className=\"text-base sm:text-lg opacity-75 max-w-xl\">{subheading}</p>)}\n"
            "          {cta?.label && (<Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-6 py-3.5 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link>)}\n"
            "        </div>\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "archway_frame":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  return (\n"
            "    <div className=\"relative min-h-screen pt-24 overflow-hidden bg-black\">\n"
            "      <motion.div initial={{scale:1.15,opacity:0}} animate={{scale:1,opacity:1}} transition={{duration:1.4,ease:[0.22,1,0.36,1]}} className=\"absolute inset-0\">\n"
            f"        {media_tag}\n"
            "        <div className=\"absolute inset-0\" style={{ background: 'radial-gradient(50% 60% at 50% 55%, transparent 40%, rgba(0,0,0,0.6) 75%, rgba(0,0,0,0.9) 100%)' }} />\n"
            "      </motion.div>\n"
            "      <svg className=\"absolute left-0 top-0 w-[40%] opacity-70 pointer-events-none\" viewBox=\"0 0 400 800\" aria-hidden><defs><filter id=\"b\"><feGaussianBlur stdDeviation=\"2\"/></filter></defs><g filter=\"url(#b)\" fill=\"#071a0c\"><path d=\"M0,0 L180,0 C120,200 80,420 0,640 Z\"/></g></svg>\n"
            "      <svg className=\"absolute right-0 bottom-0 w-[40%] opacity-70 pointer-events-none rotate-180\" viewBox=\"0 0 400 800\" aria-hidden><g fill=\"#071a0c\"><path d=\"M0,0 L180,0 C120,200 80,420 0,640 Z\"/></g></svg>\n"
            "      <div className=\"relative z-10 max-w-[1200px] mx-auto px-5 sm:px-8 min-h-[calc(100vh-96px)] grid place-items-center text-center\">\n"
            "        <div>\n"
            "          <motion.h1 initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.4,duration:1}} className=\"font-display text-6xl sm:text-8xl lg:text-[9rem] font-semibold tracking-[-0.03em] leading-[0.92] text-white drop-shadow-2xl\">{heading}</motion.h1>\n"
            "          {subheading && (<motion.p initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.8}} className=\"mt-6 text-lg text-white/85 max-w-xl mx-auto drop-shadow-lg\">{subheading}</motion.p>)}\n"
            "          {cta?.label && (<motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:1}} className=\"mt-8\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-6 py-3.5 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></motion.div>)}\n"
            "        </div>\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "diorama_layers":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  const ref = useRef(null);\n"
            "  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });\n"
            "  const y1 = useTransform(scrollYProgress, [0,1], [0, -80]);\n"
            "  const y2 = useTransform(scrollYProgress, [0,1], [0, -160]);\n"
            "  const y3 = useTransform(scrollYProgress, [0,1], [0, -240]);\n"
            "  return (\n"
            "    <div ref={ref} className=\"relative min-h-screen pt-24 overflow-hidden hero-grad\">\n"
            "      <div className=\"absolute inset-0 decor-bg opacity-50\" />\n"
            "      <motion.div style={{ y: y1 }} className=\"absolute inset-x-0 top-[20%] flex justify-center pointer-events-none\">\n"
            f"        <div className=\"w-[70%] max-w-[900px] aspect-video rounded-2xl overflow-hidden border border-white/10 glow\">{media_tag}</div>\n"
            "      </motion.div>\n"
            "      <motion.div style={{ y: y2 }} className=\"absolute inset-x-0 top-[38%] flex justify-between px-[8%] pointer-events-none\" aria-hidden>\n"
            "        <div className=\"w-[180px] h-[120px] rounded-xl border border-white/10 bg-white/[0.05] backdrop-blur glow\" />\n"
            "        <div className=\"w-[180px] h-[120px] rounded-xl border border-white/10 bg-white/[0.05] backdrop-blur glow\" />\n"
            "      </motion.div>\n"
            "      <motion.div style={{ y: y3 }} className=\"relative z-10 max-w-[1400px] mx-auto px-5 sm:px-8 pt-[48vh] pb-20 text-center\">\n"
            "        <motion.h1 initial={{opacity:0,y:40}} animate={{opacity:1,y:0}} transition={{duration:1}} className=\"font-display text-6xl sm:text-8xl lg:text-[10rem] font-bold tracking-[-0.04em] leading-[0.9]\">{heading}</motion.h1>\n"
            "        {subheading && (<p className=\"mt-6 text-lg opacity-75 max-w-xl mx-auto\">{subheading}</p>)}\n"
            "        {cta?.label && (<div className=\"mt-8 flex justify-center\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-6 py-3.5 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "      </motion.div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "product_float":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  return (\n"
            "    <div className=\"relative min-h-screen pt-24 overflow-hidden hero-grad\">\n"
            "      <div className=\"absolute inset-0 decor-bg opacity-60\" />\n"
            "      <motion.div animate={{y:[-8,8,-8]}} transition={{duration:5,repeat:Infinity,ease:'easeInOut'}} className=\"absolute left-[14%] top-[30%] w-28 h-28 rounded-full border border-white/15 bg-white/[0.04] backdrop-blur-sm\" aria-hidden />\n"
            "      <motion.div animate={{y:[6,-10,6]}} transition={{duration:6,repeat:Infinity,ease:'easeInOut'}} className=\"absolute right-[16%] top-[25%] w-20 h-20 rounded-2xl border border-white/15 bg-white/[0.04] backdrop-blur-sm rotate-12\" aria-hidden />\n"
            "      <motion.div animate={{y:[-6,10,-6]}} transition={{duration:7,repeat:Infinity,ease:'easeInOut'}} className=\"absolute left-[22%] bottom-[22%] w-16 h-16 rounded-lg border border-white/15 bg-white/[0.04] backdrop-blur-sm -rotate-6\" aria-hidden />\n"
            "      <motion.div animate={{y:[10,-6,10]}} transition={{duration:5.5,repeat:Infinity,ease:'easeInOut'}} className=\"absolute right-[24%] bottom-[20%] w-24 h-24 rounded-full border border-white/15 bg-white/[0.04] backdrop-blur-sm\" aria-hidden />\n"
            "      <div className=\"relative z-10 max-w-[1200px] mx-auto px-5 sm:px-8 min-h-[calc(100vh-96px)] grid place-items-center text-center\">\n"
            "        <div>\n"
            "          <motion.h1 initial={{opacity:0,scale:0.92}} animate={{opacity:1,scale:1}} transition={{duration:1,ease:[0.22,1,0.36,1]}} className=\"font-display text-5xl sm:text-7xl lg:text-[9rem] font-bold tracking-[-0.04em] leading-[0.92]\">{heading}</motion.h1>\n"
            "          <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.4}} className=\"mx-auto mt-8 w-[320px] aspect-[4/5] rounded-3xl overflow-hidden border border-white/10 glow bg-black relative\">\n"
            f"            {media_tag}\n"
            "            <div className=\"absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none\" />\n"
            "          </motion.div>\n"
            "          {subheading && (<p className=\"mt-8 text-lg opacity-75 max-w-xl mx-auto\">{subheading}</p>)}\n"
            "          {cta?.label && (<div className=\"mt-6 flex justify-center\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-6 py-3.5 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "        </div>\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    if hero_kind == "centered_text" or hero_kind == "typewriter":
        return base + (
            "export default function ExplodingHero({ heading, subheading, cta }) {\n"
            "  return (\n"
            "    <div className=\"relative min-h-[80vh] pt-28 pb-20 overflow-hidden noise hero-grad\">\n"
            "      <div className=\"absolute inset-0 decor-bg pointer-events-none\" />\n"
            "      <div className=\"relative z-10 max-w-[1100px] mx-auto px-5 sm:px-8 text-center\">\n"
            "        <motion.h1 initial={{opacity:0,y:30}} animate={{opacity:1,y:0}} transition={{duration:0.8, ease:[0.22,1,0.36,1]}} className=\"font-display text-5xl sm:text-7xl lg:text-8xl font-semibold tracking-tight leading-[1.02] max-w-5xl mx-auto\">{heading}</motion.h1>\n"
            "        {subheading && (<motion.p initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.2}} className=\"mt-5 text-base sm:text-lg opacity-75 max-w-2xl mx-auto\">{subheading}</motion.p>)}\n"
            "        {cta?.label && (<div className=\"mt-8 flex justify-center\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-5 py-3 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    # fallback = explode_video behavior
    return base + (
        "export default function ExplodingHero({ heading, subheading, cta }) {\n"
        "  return (\n"
        "    <div className=\"relative min-h-[80vh] pt-28 pb-20 overflow-hidden noise hero-grad\">\n"
        "      <div className=\"absolute inset-0 decor-bg pointer-events-none\" />\n"
        "      <div className=\"relative z-10 max-w-[1100px] mx-auto px-5 sm:px-8\">\n"
        "        <h1 className=\"font-display text-5xl sm:text-7xl font-semibold tracking-tight leading-[1.02] max-w-4xl\">{heading}</h1>\n"
        "        {subheading && (<p className=\"mt-5 text-base sm:text-lg opacity-75 max-w-xl\">{subheading}</p>)}\n"
        "        {cta?.label && (<div className=\"mt-8\"><Link href={cta.href || '#'} className=\"inline-flex items-center gap-2 rounded-xl px-5 py-3 bg-brand text-[color:var(--bg)] font-medium hover:brightness-110 transition\">{cta.label}<ArrowUpRight size={16}/></Link></div>)}\n"
        "      </div>\n"
        "    </div>\n"
        "  );\n"
        "}\n"
    )


def _component_footer() -> str:
    return (
        "import Link from 'next/link';\n"
        "export default function Footer({ brand, items }) {\n"
        "  return (\n"
        "    <footer className=\"mt-24 border-t border-white/5\">\n"
        "      <div className=\"max-w-[1200px] mx-auto px-5 sm:px-8 py-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4\">\n"
        "        <div className=\"font-display text-lg\">{brand}</div>\n"
        "        <nav className=\"flex flex-wrap gap-5 text-sm opacity-70\">\n"
        "          {items?.map((it) => (<Link key={it.href} href={it.href} className=\"hover:opacity-100 transition-opacity\">{it.label}</Link>))}\n"
        "        </nav>\n"
        "        <div className=\"text-xs opacity-50\">&copy; {new Date().getFullYear()} {brand}</div>\n"
        "      </div>\n"
        "    </footer>\n"
        "  );\n"
        "}\n"
    )


def _page_template(pg: dict, brand_name: str, tagline: str, is_home: bool, picks_by_section: dict | None = None) -> str:
    sections = pg.get("sections") or []
    picks_by_section = picks_by_section or {}
    picked_imports: list[tuple[str, str]] = []  # (importName, slug)
    # Always retain the text verbatim in the rendered components (anti-slop)
    rendered_js: list[str] = []
    for i, s in enumerate(sections):
        kind = (s.get("kind") or "").lower()
        heading = s.get("heading") or ""
        subheading = s.get("subheading") or ""
        items = s.get("items") or []
        cta = s.get("cta") or {}

        # If the component library picked an entry for this section, use it
        pick_slug = picks_by_section.get(i)
        if pick_slug:
            imp = _slug_to_component_name(pick_slug)
            picked_imports.append((imp, pick_slug))
            rendered_js.append(
                "      <" + imp
                + " heading=" + _safe_text(heading or tagline)
                + " subheading=" + _safe_text(subheading)
                + " items={" + _json_s(items) + "}"
                + " cta={" + _json_s(cta) + "} />"
            )
            continue

        if kind == "hero_video":
            rendered_js.append(
                "      <ExplodingHero heading={"
                + _json_s(heading or tagline)
                + "} subheading={"
                + _json_s(subheading)
                + "} cta={"
                + _json_s(cta)
                + "} />"
            )
        elif kind == "hero_text":
            rendered_js.append(
                "      <Section><Reveal><h1 className=\"font-display text-4xl sm:text-6xl font-semibold tracking-tight max-w-4xl\">"
                + _safe_text(heading or tagline)
                + "</h1>"
                + (f"<p className=\"mt-5 text-white/70 max-w-xl\">{_safe_text(subheading)}</p>" if subheading else "")
                + "</Reveal></Section>"
            )
        elif kind == "feature_grid":
            rendered_js.append(_render_feature_grid(heading, subheading, items))
        elif kind == "stats":
            rendered_js.append(_render_stats(heading, items))
        elif kind == "testimonials":
            rendered_js.append(_render_testimonials(heading, items))
        elif kind == "pricing":
            rendered_js.append(_render_pricing(heading, items))
        elif kind == "faq":
            rendered_js.append(_render_faq(heading, items))
        elif kind == "cta":
            rendered_js.append(_render_cta(heading, subheading, cta))
        elif kind == "logo_cloud":
            rendered_js.append(_render_logo_cloud(heading, items))
        elif kind == "content_split":
            rendered_js.append(_render_content_split(heading, subheading, items))
        elif kind == "gallery":
            rendered_js.append(_render_gallery(heading, items))
        elif kind == "team":
            rendered_js.append(_render_team(heading, items))
        elif kind == "timeline":
            rendered_js.append(_render_timeline(heading, items))
        elif kind == "contact_form":
            rendered_js.append(_render_contact_form(heading, subheading))
        elif kind == "blog":
            rendered_js.append(_render_blog(heading, subheading, items))
        elif kind == "docs":
            rendered_js.append(_render_docs(heading, subheading, items))
        elif kind == "case_studies":
            rendered_js.append(_render_case_studies(heading, subheading, items))
        elif kind == "footer":
            pass  # handled by global footer
        else:
            # fallback generic content section to retain info
            rendered_js.append(_render_feature_grid(heading, subheading, items))

    imports = (
        "import ExplodingHero from '@/components/ExplodingHero';\n"
        "import Section from '@/components/Section';\n"
        "import Reveal from '@/components/Reveal';\n"
    )
    for imp, slug in picked_imports:
        imports += f"import {imp} from '@/components/generated/{slug}';\n"
    title = pg.get("title") or (brand_name if is_home else "Page")
    meta = (
        "export const metadata = { title: "
        + _json_s(f"{title} \u2014 {brand_name}")
        + " };\n"
    )
    body = "\n".join(rendered_js) if rendered_js else "      <Section><h1 className=\"text-4xl font-display\">" + _safe_text(title) + "</h1></Section>"
    return (
        imports
        + meta
        + "export default function Page() {\n"
        + "  return (\n"
        + "    <div>\n"
        + body + "\n"
        + "    </div>\n"
        + "  );\n"
        + "}\n"
    )


def _safe_text(s: Any) -> str:
    # Use JSX-safe brace expression
    return "{" + _json_s(str(s or "")) + "}"


def _render_feature_grid(heading: str, sub: str, items: list) -> str:
    items = items or []
    grid_children: list[str] = []
    for it in items[:9]:
        t = it.get("title") or ""
        b = it.get("body") or ""
        grid_children.append(
            "<div className=\"rounded-2xl border border-white/10 bg-white/[0.03] p-6 hover:bg-white/[0.05] transition-colors\">"
            "<h3 className=\"font-display text-xl font-semibold\">"
            + _safe_text(t)
            + "</h3>"
            "<p className=\"mt-2 text-white/70 text-sm leading-relaxed\">"
            + _safe_text(b)
            + "</p>"
            "</div>"
        )
    inner = "".join(grid_children) or "<div className=\"text-white/50\">" + _safe_text(sub or "") + "</div>"
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <div className=\"mb-10 max-w-2xl\">\n"
        "            <h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight\">"
        + _safe_text(heading)
        + "</h2>\n"
        + ("            <p className=\"mt-3 text-white/70\">" + _safe_text(sub) + "</p>\n" if sub else "")
        + "          </div>\n"
        "          <div className=\"grid sm:grid-cols-2 lg:grid-cols-3 gap-4\">" + inner + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_stats(heading: str, items: list) -> str:
    items = items or []
    cards = "".join(
        [
            "<div className=\"rounded-2xl border border-white/10 bg-white/[0.03] p-6\">"
            "<div className=\"font-display text-4xl font-semibold text-brand\">" + _safe_text(it.get("title") or "") + "</div>"
            "<div className=\"mt-1 text-sm text-white/70\">" + _safe_text(it.get("body") or "") + "</div>"
            "</div>"
            for it in items[:6]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight mb-8\">" + _safe_text(heading) + "</h2>\n"
        "          <div className=\"grid sm:grid-cols-2 lg:grid-cols-4 gap-4\">" + cards + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_testimonials(heading: str, items: list) -> str:
    items = items or []
    cards = "".join(
        [
            "<figure className=\"rounded-2xl border border-white/10 bg-white/[0.03] p-6\">"
            "<blockquote className=\"text-white/85 text-base leading-relaxed\">\u201c" + _safe_text(it.get("body") or "") + "\u201d</blockquote>"
            "<figcaption className=\"mt-4 text-sm text-white/60\">\u2014 " + _safe_text(it.get("title") or "") + "</figcaption>"
            "</figure>"
            for it in items[:6]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight mb-8\">" + _safe_text(heading) + "</h2>\n"
        "          <div className=\"grid md:grid-cols-2 gap-4\">" + cards + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_pricing(heading: str, items: list) -> str:
    items = items or []
    cards = "".join(
        [
            "<div className=\"rounded-2xl border border-white/10 bg-white/[0.03] p-6 flex flex-col\">"
            "<div className=\"text-sm uppercase tracking-wider text-white/60\">" + _safe_text(it.get("title") or "") + "</div>"
            "<div className=\"font-display text-3xl font-semibold mt-1\">" + _safe_text(it.get("meta") or "") + "</div>"
            "<div className=\"mt-3 text-sm text-white/70\">" + _safe_text(it.get("body") or "") + "</div>"
            "</div>"
            for it in items[:4]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight mb-8\">" + _safe_text(heading) + "</h2>\n"
        "          <div className=\"grid sm:grid-cols-2 lg:grid-cols-3 gap-4\">" + cards + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_faq(heading: str, items: list) -> str:
    items = items or []
    rows = "".join(
        [
            "<details className=\"group rounded-xl border border-white/10 bg-white/[0.02] p-5\">"
            "<summary className=\"cursor-pointer list-none flex items-center justify-between gap-6 font-medium\">"
            "<span>" + _safe_text(it.get("title") or "") + "</span>"
            "<span className=\"text-white/40 group-open:rotate-45 transition-transform\">+</span>"
            "</summary>"
            "<p className=\"mt-3 text-white/70 text-sm leading-relaxed\">" + _safe_text(it.get("body") or "") + "</p>"
            "</details>"
            for it in items[:10]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight mb-8\">" + _safe_text(heading) + "</h2>\n"
        "          <div className=\"grid gap-3 max-w-3xl\">" + rows + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_cta(heading: str, sub: str, cta: dict) -> str:
    label = (cta or {}).get("label") or "Get started"
    href = (cta or {}).get("href") or "#"
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <div className=\"rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.04] to-white/[0.02] p-10 sm:p-14\">\n"
        "            <h2 className=\"font-display text-3xl sm:text-5xl font-semibold tracking-tight max-w-2xl\">" + _safe_text(heading) + "</h2>\n"
        + ("            <p className=\"mt-3 text-white/70 max-w-xl\">" + _safe_text(sub) + "</p>\n" if sub else "")
        + "            <a href=" + _json_s(href) + " className=\"inline-flex items-center gap-2 mt-6 rounded-xl px-5 py-3 bg-brand text-black font-medium hover:brightness-110 transition\">" + _safe_text(label) + "</a>\n"
        "          </div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_logo_cloud(heading: str, items: list) -> str:
    items = items or []
    chips = "".join(
        [
            "<div className=\"rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-white/70 text-sm\">" + _safe_text(it.get("title") or "") + "</div>"
            for it in items[:10]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <div className=\"text-sm uppercase tracking-widest text-white/40 mb-6\">" + _safe_text(heading) + "</div>\n"
        "          <div className=\"flex flex-wrap gap-3\">" + chips + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_content_split(heading: str, sub: str, items: list) -> str:
    items = items or []
    bullets = "".join(
        [
            "<li className=\"flex gap-3\"><span className=\"mt-[7px] w-1.5 h-1.5 rounded-full bg-brand\"/> <div><div className=\"font-medium\">" + _safe_text(it.get("title") or "") + "</div><div className=\"text-sm text-white/70 mt-0.5\">" + _safe_text(it.get("body") or "") + "</div></div></li>"
            for it in items[:6]
        ]
    )
    return (
        "      <Section>\n"
        "        <div className=\"grid md:grid-cols-2 gap-10 items-start\">\n"
        "          <Reveal><div><h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight\">" + _safe_text(heading) + "</h2>" + ("<p className=\"mt-3 text-white/70\">" + _safe_text(sub) + "</p>" if sub else "") + "</div></Reveal>\n"
        "          <Reveal delay={0.08}><ul className=\"space-y-4\">" + bullets + "</ul></Reveal>\n"
        "        </div>\n"
        "      </Section>"
    )


def _render_gallery(heading: str, items: list) -> str:
    items = items or []
    tiles = "".join(
        [
            "<div className=\"aspect-[4/3] rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.04] to-white/[0.01] grain relative overflow-hidden\"><div className=\"absolute inset-0 hero-grad\"/><div className=\"absolute bottom-3 left-3 text-xs text-white/80\">" + _safe_text(it.get("title") or "") + "</div></div>"
            for it in items[:6]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight mb-8\">" + _safe_text(heading) + "</h2>\n"
        "          <div className=\"grid sm:grid-cols-2 lg:grid-cols-3 gap-4\">" + tiles + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_team(heading: str, items: list) -> str:
    items = items or []
    cards = "".join(
        [
            "<div className=\"rounded-2xl border border-white/10 bg-white/[0.03] p-5\"><div className=\"size-14 rounded-full bg-gradient-to-br from-brand to-brand-accent\"/><div className=\"mt-4 font-medium\">" + _safe_text(it.get("title") or "") + "</div><div className=\"text-xs text-white/60\">" + _safe_text(it.get("meta") or "") + "</div><p className=\"mt-2 text-sm text-white/70\">" + _safe_text(it.get("body") or "") + "</p></div>"
            for it in items[:8]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight mb-8\">" + _safe_text(heading) + "</h2>\n"
        "          <div className=\"grid sm:grid-cols-2 lg:grid-cols-4 gap-4\">" + cards + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_timeline(heading: str, items: list) -> str:
    items = items or []
    rows = "".join(
        [
            "<li className=\"pl-6 relative\"><span className=\"absolute left-0 top-1.5 size-2 rounded-full bg-brand\"/><div className=\"text-xs uppercase tracking-wider text-white/50\">" + _safe_text(it.get("meta") or "") + "</div><div className=\"font-medium mt-1\">" + _safe_text(it.get("title") or "") + "</div><div className=\"text-sm text-white/70 mt-1\">" + _safe_text(it.get("body") or "") + "</div></li>"
            for it in items[:8]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight mb-8\">" + _safe_text(heading) + "</h2>\n"
        "          <ol className=\"space-y-6 max-w-2xl border-l border-white/10 ml-1 pl-0\">" + rows + "</ol>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_contact_form(heading: str, sub: str) -> str:
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <div className=\"max-w-xl\"><h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight\">" + _safe_text(heading) + "</h2>" + ("<p className=\"mt-3 text-white/70\">" + _safe_text(sub) + "</p>" if sub else "") + "</div>\n"
        "          <form className=\"mt-8 grid gap-3 max-w-xl\"><input className=\"h-12 rounded-xl bg-white/5 border border-white/10 px-4 placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-brand/40\" placeholder=\"Name\"/><input type=\"email\" className=\"h-12 rounded-xl bg-white/5 border border-white/10 px-4 placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-brand/40\" placeholder=\"Email\"/><textarea rows={4} className=\"rounded-xl bg-white/5 border border-white/10 p-4 placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-brand/40\" placeholder=\"Tell us about your project\"/><button type=\"button\" className=\"h-12 rounded-xl bg-brand text-black font-medium hover:brightness-110 transition\">Send message</button></form>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_blog(heading: str, sub: str, items: list) -> str:
    items = items or []
    cards = "".join(
        [
            "<article className=\"rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden hover:bg-white/[0.05] transition-colors\">"
            "<div className=\"aspect-[16/9] bg-gradient-to-br from-white/[0.06] to-white/[0.02] relative\"><div className=\"absolute inset-0 hero-grad\"/></div>"
            "<div className=\"p-5\">"
            "<div className=\"text-[10px] uppercase tracking-[0.18em] text-brand mb-2\">" + _safe_text(it.get("meta") or "Article") + "</div>"
            "<h3 className=\"font-display text-lg font-semibold\">" + _safe_text(it.get("title") or "") + "</h3>"
            "<p className=\"mt-2 text-sm text-white/65 leading-relaxed line-clamp-3\">" + _safe_text(it.get("body") or "") + "</p>"
            "</div></article>"
            for it in items[:6]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <div className=\"mb-10 flex items-end justify-between gap-6\"><div><h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight\">" + _safe_text(heading) + "</h2>" + ("<p className=\"mt-3 text-white/70 max-w-xl\">" + _safe_text(sub) + "</p>" if sub else "") + "</div></div>\n"
        "          <div className=\"grid sm:grid-cols-2 lg:grid-cols-3 gap-4\">" + cards + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_docs(heading: str, sub: str, items: list) -> str:
    items = items or []
    links = "".join(
        [
            "<a className=\"block rounded-xl border border-white/10 bg-white/[0.02] p-4 hover:bg-white/[0.05] transition-colors\" href=\"#\">"
            "<div className=\"flex items-center justify-between\">"
            "<div className=\"font-medium\">" + _safe_text(it.get("title") or "") + "</div>"
            "<span className=\"text-white/40 text-sm\">\u2192</span>"
            "</div>"
            "<p className=\"mt-1 text-[12.5px] text-white/60 leading-relaxed\">" + _safe_text(it.get("body") or "") + "</p>"
            "</a>"
            for it in items[:9]
        ]
    )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <div className=\"grid md:grid-cols-[260px_1fr] gap-8\">\n"
        "            <aside className=\"panel-soft p-4 rounded-xl border border-white/10 bg-white/[0.02] h-fit sticky top-24 hidden md:block\"><div className=\"text-[10px] uppercase tracking-[0.18em] text-white/50 mb-3\">Contents</div>"
        "              <ul className=\"space-y-2 text-sm\">" + "".join([f"<li><a href=\"#\" className=\"opacity-70 hover:opacity-100\">{_safe_text(it.get('title') or '')}</a></li>" for it in items[:9]]) + "</ul></aside>\n"
        "            <div><h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight mb-2\">" + _safe_text(heading) + "</h2>" + ("<p className=\"text-white/70 mb-6\">" + _safe_text(sub) + "</p>" if sub else "") + "\n"
        "              <div className=\"grid sm:grid-cols-2 gap-3\">" + links + "</div>\n"
        "            </div>\n"
        "          </div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )


def _render_case_studies(heading: str, sub: str, items: list) -> str:
    items = items or []
    cards = ""
    for idx, it in enumerate(items[:4]):
        reverse = "md:flex-row-reverse" if idx % 2 else ""
        cards += (
            "<article className=\"rounded-3xl border border-white/10 bg-white/[0.03] overflow-hidden\">"
            f"<div className=\"flex flex-col md:flex-row {reverse} items-stretch\">"
            "<div className=\"md:w-1/2 aspect-video md:aspect-auto relative\"><div className=\"absolute inset-0 hero-grad\"/><div className=\"absolute inset-0 bg-gradient-to-br from-white/5 to-white/[0.02]\"/></div>"
            "<div className=\"p-6 sm:p-10 md:w-1/2\">"
            "<div className=\"text-[10px] uppercase tracking-[0.18em] text-brand mb-2\">" + _safe_text(it.get("meta") or "Case study") + "</div>"
            "<h3 className=\"font-display text-2xl sm:text-3xl font-semibold tracking-tight\">" + _safe_text(it.get("title") or "") + "</h3>"
            "<p className=\"mt-3 text-white/70 text-sm leading-relaxed\">" + _safe_text(it.get("body") or "") + "</p>"
            "<a href=\"#\" className=\"inline-flex items-center gap-2 mt-4 text-sm text-brand hover:brightness-110\">Read case study \u2192</a>"
            "</div></div></article>"
        )
    return (
        "      <Section>\n"
        "        <Reveal>\n"
        "          <div className=\"mb-10 max-w-2xl\"><h2 className=\"font-display text-3xl sm:text-4xl font-semibold tracking-tight\">" + _safe_text(heading) + "</h2>" + ("<p className=\"mt-3 text-white/70\">" + _safe_text(sub) + "</p>" if sub else "") + "</div>\n"
        "          <div className=\"grid gap-5\">" + cards + "</div>\n"
        "        </Reveal>\n"
        "      </Section>"
    )
