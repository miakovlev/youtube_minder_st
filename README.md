# YouTube Minder

*Streamlit app that summarizes YouTube videos via subtitles or audio transcription.*

* * *

## Features

- Paste a YouTube URL and get a clean summary in English or Russian.
- Subtitle-first workflow for long videos to reduce cost and latency.
- Automatic fallback to audio transcription when subtitles are unavailable.
- Cached transcriptions for faster repeat runs.
- Cookie support for age-restricted or rate-limited videos.

* * *

## How it works

1. Paste a YouTube link.
2. Choose summary language.
3. For long videos (> 1400s), subtitles are used automatically; otherwise pick subtitles vs audio.
4. Audio path: download -> transcribe -> summarize.
5. Subtitles path: download VTT -> clean to text -> summarize.

* * *

## Quick start

```bash
uv venv
uv sync
streamlit run src/youtube_minder/ui/streamlit_app.py
```

Open `http://localhost:8501` in your browser.

* * *

## Usage

### Web interface

- Enter a YouTube URL.
- Select summary language.
- Choose processing method (subtitles or audio).
- Download the full transcription if needed.

* * *

## Output

- Summary in the selected language.
- Full transcription/subtitles as a downloadable text file.

* * *

## Configuration (.env)

Required:
- `OPENAI_API_KEY`

Optional:
- `COOKIES_FROM_BROWSER=chrome` (or `firefox`, `edge`, `brave`)
- `COOKIES_FILE=cookies.txt` (default: `cookies.txt`)
- `YTDLP_PLAYER_CLIENT=android` (comma-separated list supported)
- `YTDLP_JS_RUNTIMES=node` or `node=/usr/local/bin/node`
- `YTDLP_REMOTE_COMPONENTS=ejs:github`
- `SUBS_RETRY_ATTEMPTS=3`
- `SUBS_RETRY_BASE_SLEEP=5`

* * *

## Architecture

- `src/youtube_minder/ui/streamlit_app.py` — Streamlit entry point.
- `src/youtube_minder/workflows/processor.py` — orchestration flow.
- `src/youtube_minder/services/` — download, transcription, summary.
- `src/youtube_minder/utils/` — helpers.
- `data/` — cached transcriptions and temporary downloads.

* * *

## Development

```bash
uv sync --dev
uv run pytest
```

* * *

## About

YouTube Minder turns long-form video into a concise summary while keeping a full text version for deeper reading.

* * *

## Resources

- Streamlit
- OpenAI
- yt-dlp
- ffmpeg

* * *

## License

MIT
