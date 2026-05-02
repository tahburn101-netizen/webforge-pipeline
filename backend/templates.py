"""Template recipe registry.

Each template is a distinct "DNA" for the generated Next.js site: different
layout archetype, motion package, typography pairing, 3D/decorative treatment,
hero kind and palette mood. The pipeline picks one per job based on a
deterministic seed (niche + job_id) so every transformation looks different.
"""
from __future__ import annotations

import hashlib
from typing import Any

FONT_PAIRS: list[tuple[str, str]] = [
    ("Space Grotesk", "Inter"),
    ("Instrument Serif", "Inter"),
    ("DM Serif Display", "DM Sans"),
    ("Playfair Display", "Work Sans"),
    ("Fraunces", "Inter"),
    ("Syne", "Manrope"),
    ("Bricolage Grotesque", "Inter"),
    ("Unbounded", "Inter"),
    ("Archivo Black", "Archivo"),
    ("Inter Tight", "Inter"),
    ("Bebas Neue", "Inter"),
    ("Cormorant Garamond", "Work Sans"),
    ("Libre Caslon Display", "Inter"),
    ("Space Grotesk", "IBM Plex Sans"),
    ("Onest", "Onest"),
    ("Geist", "Geist"),
    ("IBM Plex Serif", "IBM Plex Sans"),
    ("Familjen Grotesk", "Inter"),
    ("Khand", "Inter"),
    ("Sora", "Inter"),
]

PALETTE_MOODS: list[dict[str, str]] = [
    {"name": "abyss_teal", "primary": "#2DE3C6", "primary_2": "#0EA5A4", "accent": "#FFB86B", "bg": "#070A0E", "bg_2": "#0B1220", "fg": "#EAF0FF", "muted_fg": "#9AA3B2"},
    {"name": "graphite_lime", "primary": "#B6F23C", "primary_2": "#8ECC15", "accent": "#D08C60", "bg": "#0A0B0D", "bg_2": "#111318", "fg": "#F2F4F8", "muted_fg": "#A4ADB8"},
    {"name": "ink_ocean", "primary": "#4CC9F0", "primary_2": "#2F7BC2", "accent": "#FFB199", "bg": "#070B12", "bg_2": "#0B1424", "fg": "#EAF2FF", "muted_fg": "#9AA9C0"},
    {"name": "black_ice", "primary": "#9AE6FF", "primary_2": "#5CC9EB", "accent": "#D7DCE3", "bg": "#050607", "bg_2": "#0B0D10", "fg": "#F5F7FA", "muted_fg": "#A0A8B3"},
    {"name": "ember_dusk", "primary": "#FF8957", "primary_2": "#E0543A", "accent": "#FFD66B", "bg": "#100A0B", "bg_2": "#1A1112", "fg": "#FFF1E8", "muted_fg": "#B8A39A"},
    {"name": "moss_forest", "primary": "#7FE3A1", "primary_2": "#3FAB6E", "accent": "#E8C872", "bg": "#0A110C", "bg_2": "#101A12", "fg": "#EEF6EF", "muted_fg": "#9DB5A5"},
    {"name": "sunset_clay", "primary": "#F26A4F", "primary_2": "#C94A30", "accent": "#F8C267", "bg": "#120A0A", "bg_2": "#1D1213", "fg": "#FBEEE8", "muted_fg": "#BAA39B"},
    {"name": "mono_silver", "primary": "#E9ECF2", "primary_2": "#B8BCC4", "accent": "#7CD4FF", "bg": "#060708", "bg_2": "#0D0F12", "fg": "#F5F6F8", "muted_fg": "#8B9099"},
    {"name": "cream_editorial", "primary": "#111111", "primary_2": "#333333", "accent": "#E05B38", "bg": "#F5F0E6", "bg_2": "#EAE1D1", "fg": "#111111", "muted_fg": "#555555"},
    {"name": "paper_slate", "primary": "#0F1720", "primary_2": "#233044", "accent": "#3E7CB1", "bg": "#F7F6F2", "bg_2": "#EDEBE4", "fg": "#0F1720", "muted_fg": "#4A5566"},
    {"name": "matte_peach", "primary": "#FF9770", "primary_2": "#E07353", "accent": "#FFD972", "bg": "#141213", "bg_2": "#1C1819", "fg": "#FFF4EC", "muted_fg": "#B9A59A"},
    {"name": "emerald_luxe", "primary": "#2EC27E", "primary_2": "#178B55", "accent": "#E2C275", "bg": "#0A120E", "bg_2": "#101A15", "fg": "#EEF6EF", "muted_fg": "#95A99B"},
    {"name": "cyber_ice", "primary": "#5EEAD4", "primary_2": "#22C2A7", "accent": "#F472B6", "bg": "#060A0F", "bg_2": "#0B131C", "fg": "#EAF6FF", "muted_fg": "#8FA0B0"},
    {"name": "industrial_amber", "primary": "#FFB347", "primary_2": "#D58F2A", "accent": "#9AE6FF", "bg": "#0C0B0A", "bg_2": "#151311", "fg": "#FFF6E8", "muted_fg": "#B3A58E"},
    {"name": "electric_mint", "primary": "#3EF5C6", "primary_2": "#00C8A4", "accent": "#FFD670", "bg": "#040807", "bg_2": "#081210", "fg": "#EAFBF4", "muted_fg": "#8EB1A6"},
    {"name": "rose_noir", "primary": "#FF5A7A", "primary_2": "#CC3E5C", "accent": "#FFD166", "bg": "#0B0708", "bg_2": "#16090C", "fg": "#FFEEF0", "muted_fg": "#B09098"},
]

HERO_KINDS = [
    "explode_video",
    "centered_text",
    "split_media",
    "asymmetric_cards",
    "orb_3d",
    "marquee",
    "parallax_layers",
    "typewriter",
    "grid_mosaic",
    "perspective_stack",
    # Premium archetypes (from byshabn / neuwebstudio reference video)
    "fullbleed_parallax",    # Hong Kong-style full-bleed photo with overlay type + slight perspective
    "framed_split",           # Forest-style split with giant serif + textured frame
    "architectural_tilt",     # Dark dramatic facade with cursor tilt + magnetic feel
    "portrait_mega_type",     # Huge letter-spaced type over portrait/subject
    "archway_frame",          # Foreground-framed discovery (leaves/shapes) + layered depth
    "diorama_layers",         # Layered parallax diorama with kinetic headline
    "product_float",          # Centered "product" with floating decorative satellites
]

DECOR_KINDS = [
    "grain",
    "dot_grid",
    "line_grid",
    "orbs",
    "stars",
    "scanlines",
    "mesh_gradient",
    "noise_only",
    "glitch_lines",
    "blurred_blobs",
]

MOTION_PACKS = [
    "soft_reveal",     # subtle fade+up
    "bold_parallax",   # scroll-driven layered
    "magnetic_hover",  # buttons pull toward cursor
    "tilt_3d",         # cards tilt on hover
    "marquee_loop",    # horizontal marquees
    "stagger_cascade", # list items cascade
]

LAYOUT_ARCHETYPES = [
    "editorial",       # large serif display, narrow column, generous whitespace
    "split",           # 50/50 left text/right media
    "centered",        # single-column centered
    "asymmetric",      # off-grid bold headings
    "grid",            # bento grid hero
    "overlay",         # media bg, text overlay
    "terminal",        # mono, developer-ish
    "portfolio",       # image-led, minimal text
]

RADIUS_OPTIONS = ["2px", "6px", "10px", "14px", "18px", "24px", "999px"]


def _mix(seed: str, salt: str, n: int) -> int:
    h = hashlib.sha256(f"{seed}|{salt}".encode()).hexdigest()
    return int(h[:8], 16) % n


def build_templates() -> list[dict[str, Any]]:
    """Deterministically build a library of 50 distinct template recipes."""
    templates: list[dict[str, Any]] = []
    # 50 distinct combos (stride to avoid collisions)
    for i in range(50):
        font = FONT_PAIRS[i % len(FONT_PAIRS)]
        palette = PALETTE_MOODS[(i * 3 + 2) % len(PALETTE_MOODS)]
        hero = HERO_KINDS[(i * 7 + 1) % len(HERO_KINDS)]
        decor = DECOR_KINDS[(i * 5 + 3) % len(DECOR_KINDS)]
        motion = MOTION_PACKS[(i * 2 + 1) % len(MOTION_PACKS)]
        layout = LAYOUT_ARCHETYPES[(i * 11 + 4) % len(LAYOUT_ARCHETYPES)]
        radius = RADIUS_OPTIONS[(i * 13 + 5) % len(RADIUS_OPTIONS)]
        name = f"tpl_{i + 1:02d}_{layout}_{palette['name']}_{hero}"
        templates.append(
            {
                "id": i + 1,
                "name": name,
                "layout": layout,
                "hero": hero,
                "decor": decor,
                "motion": motion,
                "font_heading": font[0],
                "font_body": font[1],
                "radius": radius,
                "palette": palette,
            }
        )
    return templates


TEMPLATES: list[dict[str, Any]] = build_templates()


def pick_template(seed: str, niche: str | None = None) -> dict[str, Any]:
    idx = _mix(seed, niche or "", len(TEMPLATES))
    tpl = TEMPLATES[idx]
    # Bias choice slightly by niche keywords
    if niche:
        k = niche.lower()
        if any(w in k for w in ("dev", "api", "code", "tech", "ai", "cloud")):
            for t in TEMPLATES:
                if t["layout"] in ("terminal", "editorial", "split") and \
                        t["palette"]["name"] in ("abyss_teal", "black_ice", "cyber_ice", "graphite_lime"):
                    if _mix(seed + t["name"], "b", 4) == 0:
                        return t
        if any(w in k for w in ("food", "restaurant", "coffee", "cafe", "bakery")):
            for t in TEMPLATES:
                if t["palette"]["name"] in ("sunset_clay", "ember_dusk", "matte_peach", "cream_editorial") and \
                        t["layout"] in ("editorial", "portfolio", "overlay"):
                    if _mix(seed + t["name"], "f", 4) == 0:
                        return t
        if any(w in k for w in ("fitness", "gym", "studio", "wellness", "yoga")):
            for t in TEMPLATES:
                if t["palette"]["name"] in ("electric_mint", "emerald_luxe", "moss_forest") and \
                        t["motion"] in ("bold_parallax", "marquee_loop", "stagger_cascade"):
                    if _mix(seed + t["name"], "w", 4) == 0:
                        return t
    return tpl
