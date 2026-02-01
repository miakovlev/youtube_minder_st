import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from youtube_minder.config import DATA_DIR, DOWNLOADS_DIR, TRANSCRIPTIONS_DIR
from youtube_minder.services.downloader import download_audio, get_video_info, download_subtitles
from youtube_minder.services.transcriber import transcribe_openai
from youtube_minder.services.summarizer import summarize_text
from youtube_minder.utils.hashing import get_sha256_hash


StatusLevel = Literal["info", "warning", "error"]


class ProcessingError(RuntimeError):
    """User-facing processing errors."""


@dataclass
class ProcessingResult:
    summary: str
    transcription_text: str
    transcription_path: Path
    display_filename: str
    is_subtitle: bool
    used_cache: bool
    video_info: dict


def _emit(on_update: Callable[[str, StatusLevel], None] | None, message: str, level: StatusLevel = "info") -> None:
    if on_update:
        on_update(message, level)


def setup_directories() -> None:
    """Creates necessary directories for data storage if they don't exist."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)
    Path(TRANSCRIPTIONS_DIR).mkdir(parents=True, exist_ok=True)


def process_video(
    url: str,
    language: str,
    method: Literal["subs", "audio"],
    on_update: Callable[[str, StatusLevel], None] | None = None,
    video_info: dict | None = None,
) -> ProcessingResult:
    """Process a YouTube video and return summary + transcription details."""
    if not url:
        raise ProcessingError("Missing YouTube URL.")

    setup_directories()

    download_dir: str | None = None
    cache_path: Path | None = None
    display_filename: str | None = None

    try:
        if video_info is None:
            _emit(on_update, "Fetching video info...")
            video_info = get_video_info(url)

        title = video_info["title"]
        video_id = video_info["id"]
        duration = video_info["duration"]

        name_hash = get_sha256_hash(url)
        download_dir = os.path.join(DOWNLOADS_DIR, name_hash)

        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c == " "]).rstrip()
        filename_base = f"{safe_title}_{video_id}"

        transcription_text = ""
        is_subtitle = False

        if method == "subs":
            is_subtitle = True
            cache_path = Path(TRANSCRIPTIONS_DIR) / f"{video_id}_subtitles_{language}.txt"
            display_filename = f"{filename_base}_subtitles_{language}.txt"
        elif method == "audio":
            cache_path = Path(TRANSCRIPTIONS_DIR) / f"{video_id}_transcription.txt"
            display_filename = f"{filename_base}_transcription.txt"
        else:
            raise ProcessingError("Unknown processing method.")

        used_cache = False
        if cache_path and cache_path.is_file() and cache_path.stat().st_size > 0:
            transcription_text = cache_path.read_text(encoding="utf-8")
            used_cache = True
            _emit(on_update, "Using cached subtitles." if is_subtitle else "Using cached transcription.")
        else:
            if method == "subs":
                _emit(on_update, "Checking for subtitles...")
                subtitle_langs = [language, "ru" if language == "en" else "en"]
                subtitle_content = download_subtitles(url, download_dir, langs=subtitle_langs)
                if subtitle_content:
                    transcription_text = subtitle_content
                    _emit(on_update, "Subtitles found and downloaded.")
                else:
                    if duration > 1400:
                        raise ProcessingError("Video is too long (>1400s) and no subtitles found.")
                    raise ProcessingError("No subtitles found. Try the audio option.")
            elif method == "audio":
                if duration > 1400:
                    raise ProcessingError("Video is too long for audio transcription. Please use subtitles.")

                _emit(on_update, "Downloading and converting audio...")
                download_audio(url, download_dir)

                mp3_files = list(Path(download_dir).glob("*.mp3"))
                if not mp3_files:
                    raise ProcessingError("No MP3 file found after download.")
                mp3_path = str(mp3_files[0])

                _emit(on_update, "Transcribing with gpt-4o-mini-transcribe...")
                transcription_text = transcribe_openai(mp3_path)

            if cache_path:
                cache_path.write_text(transcription_text, encoding="utf-8")

        _emit(on_update, "Summarizing...")
        summary = summarize_text(transcription_text, language=language)

        return ProcessingResult(
            summary=summary,
            transcription_text=transcription_text,
            transcription_path=cache_path or Path(""),
            display_filename=display_filename or (cache_path.name if cache_path else "transcription.txt"),
            is_subtitle=is_subtitle,
            used_cache=used_cache,
            video_info=video_info,
        )
    except ProcessingError:
        raise
    except Exception as exc:
        raise ProcessingError(str(exc)) from exc
    finally:
        if download_dir and os.path.exists(download_dir):
            try:
                shutil.rmtree(download_dir)
            except Exception:
                pass
