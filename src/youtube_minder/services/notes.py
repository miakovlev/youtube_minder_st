from pathlib import Path
import re

import openai


_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
_GUIDE_PATH = _TEMPLATES_DIR / "notes_guide.md"
_BODY_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.IGNORECASE | re.DOTALL)
_WRAPPER_RE = re.compile(r"</?(html|head|body)[^>]*>", re.IGNORECASE)


def _load_notes_guide() -> str:
    try:
        return _GUIDE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def generate_notes_html(transcription_text: str, language: str = "en", title: str | None = None) -> str:
    """
    Generate HTML body for video notes based on a transcript.
    """
    client = openai.OpenAI()
    lang_instruction = "in English" if language == "en" else "in Russian"
    guide = _load_notes_guide()
    title_line = f"Title: {title}\n\n" if title else ""

    prompt = (
        f"Write structured study notes {lang_instruction} for the video transcript.\n"
        f"{title_line}"
        "Return HTML body only. Do not include <html>, <head>, <body>, <style>, or scripts.\n"
        "Use clear sections, bullet lists, and short paragraphs.\n"
    )
    if guide:
        prompt += f"\nGuide:\n{guide}\n"
    prompt += f"\nTranscript:\n{transcription_text}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You write clean, well-structured HTML study notes."},
            {"role": "user", "content": prompt},
        ],
    )

    raw_html = response.choices[0].message.content or ""
    body_match = _BODY_RE.search(raw_html)
    if body_match:
        raw_html = body_match.group(1)
    cleaned_html = _WRAPPER_RE.sub("", raw_html).strip()
    return cleaned_html
