import yt_dlp
import os
import time
import re
import html
import shutil
from pathlib import Path

try:
    import yt_dlp_ejs  # type: ignore
except Exception:
    yt_dlp_ejs = None

_VTT_TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}")
_VTT_METADATA_PREFIXES = ("Kind:", "Language:")


def _clean_vtt_text(vtt_content: str) -> str:
    """
    Strip WEBVTT headers, timestamps, and tags; return plain text.
    """
    lines = vtt_content.splitlines()
    cleaned_lines: list[str] = []
    skip_block = False
    last_non_empty_norm = None

    for line in lines:
        raw = line.strip()

        if not raw:
            if skip_block:
                skip_block = False
                continue
            # Keep paragraph breaks minimal
            if cleaned_lines and cleaned_lines[-1]:
                cleaned_lines.append("")
            continue

        # Skip WEBVTT header and metadata
        if raw.upper().startswith("WEBVTT"):
            continue
        if raw.startswith(_VTT_METADATA_PREFIXES):
            continue

        # Skip NOTE/STYLE/REGION blocks
        if raw.startswith("NOTE") or raw.startswith("STYLE") or raw.startswith("REGION"):
            skip_block = True
            continue

        if skip_block:
            # End block on empty line (handled above)
            continue

        # Skip cue timing lines
        if _VTT_TIMESTAMP_RE.match(raw):
            continue

        # Skip cue identifiers (usually numeric)
        if raw.isdigit():
            continue

        # Remove tags and unescape HTML entities
        text = re.sub(r"<[^>]+>", "", raw)
        text = html.unescape(text).strip()

        if text:
            norm = " ".join(text.split())
            if norm == last_non_empty_norm:
                continue
            last_non_empty_norm = norm
            cleaned_lines.append(text)

    # Collapse multiple blank lines
    output_lines: list[str] = []
    for line in cleaned_lines:
        if line == "" and (not output_lines or output_lines[-1] == ""):
            continue
        output_lines.append(line)

    return "\n".join(output_lines).strip()


def _parse_cookies_from_browser_spec(raw: str) -> tuple[str, ...]:
    """
    Convert "browser[:profile[:keyring[:cookies_db]]]" to tuple for yt-dlp API.
    """
    if ":" not in raw:
        return (raw,)
    parts = [p.strip() for p in raw.split(":", 3)]
    return tuple(p for p in parts if p)


def _apply_ytdlp_auth_and_extractor_opts(ydl_opts: dict) -> None:
    """
    Apply cookies and optional extractor args to yt-dlp options.
    """
    cookies_from_browser = os.getenv("COOKIES_FROM_BROWSER", "").strip()
    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = _parse_cookies_from_browser_spec(cookies_from_browser)
    else:
        cookies_path = os.getenv("COOKIES_FILE", "cookies.txt")
        if os.path.isfile(cookies_path):
            ydl_opts["cookiefile"] = cookies_path

    player_clients_raw = os.getenv("YTDLP_PLAYER_CLIENT", "").strip()
    if player_clients_raw:
        player_clients = [c.strip() for c in player_clients_raw.split(",") if c.strip()]
        if player_clients:
            extractor_args = ydl_opts.setdefault("extractor_args", {})
            youtube_args = extractor_args.setdefault("youtube", {})
            youtube_args["player_client"] = player_clients

    js_runtimes_raw = os.getenv("YTDLP_JS_RUNTIMES", "").strip()
    if js_runtimes_raw:
        js_runtimes: dict[str, dict] = {}
        for item in [c.strip() for c in js_runtimes_raw.split(",") if c.strip()]:
            if "=" in item:
                name, path = item.split("=", 1)
                name = name.strip()
                path = path.strip()
                if name:
                    js_runtimes[name] = {"path": path} if path else {}
            else:
                js_runtimes[item] = {}
        if js_runtimes:
            ydl_opts["js_runtimes"] = js_runtimes
    else:
        node_path = shutil.which("node")
        if node_path:
            ydl_opts["js_runtimes"] = {"node": {"path": node_path}}

    remote_components_raw = os.getenv("YTDLP_REMOTE_COMPONENTS", "").strip()
    if remote_components_raw:
        remote_components = [c.strip() for c in remote_components_raw.split(",") if c.strip()]
        if remote_components:
            ydl_opts["remote_components"] = remote_components
    elif yt_dlp_ejs is None and ydl_opts.get("js_runtimes"):
        # Allow fetching EJS scripts if package is not installed and JS runtime is available
        ydl_opts["remote_components"] = ["ejs:github"]


def _extract_info_with_fallback(youtube_url: str, ydl_opts: dict, download: bool):
    """
    Try extraction; on FormatNotAvailable, retry without extractor_args.
    """
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(youtube_url, download=download)
    except Exception as e:
        if "Requested format is not available" in str(e) and "extractor_args" in ydl_opts:
            ydl_opts_fallback = dict(ydl_opts)
            ydl_opts_fallback.pop("extractor_args", None)
            with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
                return ydl.extract_info(youtube_url, download=download)
        raise


def download_audio(youtube_url: str, output_path: str) -> None:
    """
    Downloads audio from YouTube and saves it as mp3.

    :param youtube_url: YouTube video URL
    :param output_path: directory to save the mp3
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save as "<id>.mp3" in output_path (more stable and filesystem-safe)
    outtmpl = str(output_dir / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "restrictfilenames": True,
        "ignoreconfig": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }
        ],
    }

    _apply_ytdlp_auth_and_extractor_opts(ydl_opts)

    # yt-dlp downloads and converts to mp3 (ffmpeg must be in PATH)
    info = _extract_info_with_fallback(youtube_url, ydl_opts, download=True)
    return info.get("title", "Unknown Title")


def get_video_info(youtube_url: str) -> dict:
    """
    Retrieves video information (title, duration, id).
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreconfig": True,
    }

    _apply_ytdlp_auth_and_extractor_opts(ydl_opts)
    try:
        info = _extract_info_with_fallback(youtube_url, ydl_opts, download=False)
    except Exception as e:
        if "Requested format is not available" in str(e):
            ydl_opts_raw = dict(ydl_opts)
            with yt_dlp.YoutubeDL(ydl_opts_raw) as ydl:
                info = ydl.extract_info(youtube_url, download=False, process=False)
        else:
            raise
    return {
        "title": info.get("title", "Unknown Title"),
        "duration": info.get("duration", 0),
        "id": info.get("id", "UnknownID"),
        "webpage_url": info.get("webpage_url", youtube_url),
    }


def download_subtitles(youtube_url: str, output_dir: str, langs: list[str] | None = None) -> str:
    """
    Downloads subtitles (auto or manual) and returns the content as text.
    Returns None if no subtitles found.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    subtitles_langs = langs or ["en", "ru"]
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": subtitles_langs,
        "subtitlesformat": "vtt",
        "outtmpl": str(Path(output_dir) / "%(id)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreconfig": True,
    }

    _apply_ytdlp_auth_and_extractor_opts(ydl_opts)

    max_attempts = min(int(os.getenv("SUBS_RETRY_ATTEMPTS", "3")), 3)
    base_sleep = float(os.getenv("SUBS_RETRY_BASE_SLEEP", "5"))

    for attempt in range(1, max_attempts + 1):
        try:
            info = _extract_info_with_fallback(youtube_url, ydl_opts, download=True)

            # Find the downloaded subtitle file
            # yt-dlp names it like {id}.en.vtt or {id}.ru.vtt
            video_id = info.get("id")
            for lang in subtitles_langs:
                sub_files = list(Path(output_dir).glob(f"{video_id}.{lang}.vtt"))
                if sub_files:
                    # Read content
                    with open(sub_files[0], "r", encoding="utf-8") as f:
                        return _clean_vtt_text(f.read())
            return None
        except Exception as e:
            if "HTTP Error 429" in str(e) and attempt < max_attempts:
                sleep_s = base_sleep * (2 ** (attempt - 1))
                time.sleep(sleep_s)
                continue
            raise

    return None
