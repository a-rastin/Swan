"""Gemini chatbox. Text + audio (multimodal). Auto-creates tasks.

Model: gemini-2.0-flash. Structured JSON output every call.
History injected as formatted context string (avoids multi-turn API complexity
while still giving the model conversation awareness).
"""
import json

from google import genai
from google.genai import types

from app.core.config import settings

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

_SYSTEM = (
    "You are Swan, a smart personal assistant. "
    "The user communicates in English or Persian — always reply in the SAME language they used. "
    "If the message implies tasks/to-dos, extract them. "
    "ALWAYS return valid JSON (no markdown fences): "
    '{"reply": "<your conversational reply>", '
    '"tasks": [{"title": str, "due_at": "ISO8601 datetime or null", '
    '"priority": 0-3, "notes": "string or null"}]}. '
    "tasks=[] when nothing actionable. priority: 0=none 1=low 2=medium 3=high."
)

_HISTORY_LIMIT = 10  # last N messages included as context


def _build_prompt(history: list[dict], text: str | None) -> str:
    parts = [_SYSTEM]
    if history:
        parts.append("\n\nConversation so far:")
        for m in history[-_HISTORY_LIMIT:]:
            role = "User" if m["role"] == "user" else "Assistant"
            parts.append(f"{role}: {m['content'] or ''}")
    if text:
        parts.append(f"\nUser: {text}")
    return "\n".join(parts)


def _parse(raw: str) -> dict:
    raw = raw.strip()
    # strip markdown fences if model ignores instruction
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        return json.loads(raw)
    except Exception:
        return {"reply": raw, "tasks": []}


def analyze_text(text: str, history: list[dict] | None = None) -> dict:
    prompt = _build_prompt(history or [], text)
    resp = _client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return _parse(resp.text)


def analyze_audio(audio_bytes: bytes, mime: str = "audio/webm", history: list[dict] | None = None) -> dict:
    prompt = _build_prompt(history or [], text=None)
    resp = _client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[
            prompt,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime),
        ],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return _parse(resp.text)
