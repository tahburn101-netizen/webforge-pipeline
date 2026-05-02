"""Provider-agnostic LLM wrapper.

Primary path: Emergent Universal LLM Key via emergentintegrations (when EMERGENT_LLM_KEY is set).
Fallback: direct provider SDKs using GOOGLE_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY.

This allows the project to run without Emergent (e.g. when cloned from GitHub and
users provide their own keys).
"""
from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any


def _has_emergent() -> bool:
    return bool(os.environ.get("EMERGENT_LLM_KEY"))


def _has_google() -> bool:
    return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))


def _google_key() -> str:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""


def has_llm() -> bool:
    return _has_emergent() or _has_google()


async def generate_text(
    system: str,
    prompt: str,
    images: list[str] | None = None,
    model_text: str = "gemini-2.5-pro",
) -> str:
    """Generate a text response, optionally with image attachments (file paths)."""
    images = images or []
    if _has_emergent():
        from emergentintegrations.llm.chat import ImageContent, LlmChat, UserMessage

        chat = LlmChat(
            api_key=os.environ["EMERGENT_LLM_KEY"],
            session_id=f"wf-{int(time.time() * 1000)}",
            system_message=system,
        ).with_model("gemini", model_text)
        files = []
        for p in images:
            if p and Path(p).exists():
                files.append(
                    ImageContent(
                        image_base64=base64.b64encode(Path(p).read_bytes()).decode()
                    )
                )
        msg = UserMessage(text=prompt, file_contents=files)
        resp = await chat.send_message(msg)
        return resp if isinstance(resp, str) else str(resp)

    # Direct Google GenAI fallback
    if _has_google():
        try:
            from google import genai
            from google.genai import types as gtypes
        except ImportError as e:
            raise RuntimeError(
                "google-genai not installed. Run `pip install google-genai` or set EMERGENT_LLM_KEY."
            ) from e

        client = genai.Client(api_key=_google_key())
        parts: list[Any] = [prompt]
        for p in images:
            if p and Path(p).exists():
                mime = "image/png" if p.lower().endswith(".png") else "image/jpeg"
                parts.append(
                    gtypes.Part.from_bytes(data=Path(p).read_bytes(), mime_type=mime)
                )
        contents = [
            gtypes.Content(role="user", parts=[gtypes.Part.from_text(text=system)]),
            gtypes.Content(
                role="user",
                parts=[
                    gtypes.Part.from_text(text=prompt)
                    if isinstance(p, str)
                    else p
                    for p in parts
                ],
            ),
        ]
        resp = await _run_in_thread(
            lambda: client.models.generate_content(
                model=model_text, contents=contents
            )
        )
        return getattr(resp, "text", "") or ""

    raise RuntimeError("No LLM provider configured. Set EMERGENT_LLM_KEY or GOOGLE_API_KEY.")


async def generate_image(
    prompt: str,
    out_path: str,
    model_image: str = "gemini-3.1-flash-image-preview",
    size_hint: str = "16:9",
) -> str | None:
    """Generate an image from text prompt and save to out_path. Returns path on success.

    Tries Emergent Nano Banana first, then google-genai image preview.
    """
    full_prompt = (
        prompt
        + f"\nAspect ratio guide: {size_hint}. High-fidelity, cinematic, photorealistic where appropriate. No text overlays. No watermarks."
    )
    if _has_emergent():
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage

            chat = (
                LlmChat(
                    api_key=os.environ["EMERGENT_LLM_KEY"],
                    session_id=f"img-{int(time.time() * 1000)}",
                    system_message="You generate a single high-quality image matching the user prompt.",
                )
                .with_model("gemini", model_image)
                .with_params(modalities=["image", "text"])
            )
            msg = UserMessage(text=full_prompt)
            _, images = await chat.send_message_multimodal_response(msg)
            if images:
                data = base64.b64decode(images[0]["data"])
                Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                Path(out_path).write_bytes(data)
                return out_path
        except Exception as e:
            print(f"[llm_provider] emergent image gen failed: {e}")

    if _has_google():
        try:
            from google import genai

            client = genai.Client(api_key=_google_key())
            resp = await _run_in_thread(
                lambda: client.models.generate_content(
                    model=model_image, contents=full_prompt
                )
            )
            for cand in getattr(resp, "candidates", []) or []:
                for part in getattr(cand.content, "parts", []) or []:
                    inline = getattr(part, "inline_data", None)
                    if inline and getattr(inline, "data", None):
                        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(out_path).write_bytes(inline.data)
                        return out_path
        except Exception as e:
            print(f"[llm_provider] google image gen failed: {e}")
    return None


async def _run_in_thread(fn):
    import asyncio

    return await asyncio.get_event_loop().run_in_executor(None, fn)
