"""Curated reference library per niche."""
from __future__ import annotations

from typing import TypedDict


class Reference(TypedDict):
    url: str
    name: str
    vibe: str


REFERENCE_LIBRARY: dict[str, list[Reference]] = {
    "saas": [
        {"url": "https://linear.app", "name": "Linear", "vibe": "Dark precision, calm hierarchy"},
        {"url": "https://vercel.com", "name": "Vercel", "vibe": "Editorial + high-contrast"},
        {"url": "https://stripe.com", "name": "Stripe", "vibe": "Iconic color + motion"},
        {"url": "https://cursor.com", "name": "Cursor", "vibe": "AI-native product"},
    ],
    "developer-tools": [
        {"url": "https://linear.app", "name": "Linear", "vibe": "Dark precision"},
        {"url": "https://vercel.com", "name": "Vercel", "vibe": "Editorial"},
        {"url": "https://cursor.com", "name": "Cursor", "vibe": "AI-native"},
        {"url": "https://railway.com", "name": "Railway", "vibe": "Playful dev-first"},
    ],
    "ai": [
        {"url": "https://anthropic.com", "name": "Anthropic", "vibe": "Editorial + warm neutral"},
        {"url": "https://openai.com", "name": "OpenAI", "vibe": "Minimal, confident"},
        {"url": "https://cursor.com", "name": "Cursor", "vibe": "AI-native product"},
    ],
    "fintech": [
        {"url": "https://stripe.com", "name": "Stripe", "vibe": "Colorful gradients + motion"},
        {"url": "https://mercury.com", "name": "Mercury", "vibe": "Editorial banking"},
        {"url": "https://ramp.com", "name": "Ramp", "vibe": "Confident B2B"},
    ],
    "ecommerce": [
        {"url": "https://shopify.com", "name": "Shopify", "vibe": "Vibrant + bold"},
        {"url": "https://arc.net", "name": "Arc", "vibe": "Playful expressive"},
    ],
    "creator": [
        {"url": "https://framer.com", "name": "Framer", "vibe": "Design-forward motion"},
        {"url": "https://beehiiv.com", "name": "Beehiiv", "vibe": "Warm creator-first"},
    ],
    "agency": [
        {"url": "https://framer.com", "name": "Framer", "vibe": "Design-forward"},
        {"url": "https://unitedus.com", "name": "UNITED", "vibe": "Cinematic portfolio"},
    ],
    "portfolio": [
        {"url": "https://rauno.me", "name": "Rauno", "vibe": "Craft-first minimalism"},
        {"url": "https://pacodeluxe.com", "name": "Paco", "vibe": "Unique animation"},
    ],
    "consumer": [
        {"url": "https://notion.so", "name": "Notion", "vibe": "Friendly + clean"},
        {"url": "https://arc.net", "name": "Arc", "vibe": "Playful expressive"},
    ],
    "hardware": [
        {"url": "https://nothing.tech", "name": "Nothing", "vibe": "Industrial minimalism"},
        {"url": "https://apple.com", "name": "Apple", "vibe": "Iconic clarity"},
    ],
}


def niches() -> list[str]:
    return list(REFERENCE_LIBRARY.keys())


def list_all() -> list[dict]:
    out: list[dict] = []
    for niche, refs in REFERENCE_LIBRARY.items():
        for r in refs:
            out.append({**r, "niche": niche})
    # dedupe by url
    seen: set[str] = set()
    uniq: list[dict] = []
    for r in out:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        uniq.append(r)
    return uniq


def pick_for_niche(niche: str | None) -> str:
    if niche:
        key = niche.lower().strip().replace(" ", "-")
        for k, refs in REFERENCE_LIBRARY.items():
            if k in key or key in k:
                return refs[0]["url"]
    return REFERENCE_LIBRARY["saas"][0]["url"]
