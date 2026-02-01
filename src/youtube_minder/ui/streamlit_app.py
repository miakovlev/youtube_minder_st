import re
import sys
from pathlib import Path
from typing import List, Tuple

import streamlit as st

SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from youtube_minder.services.downloader import get_video_info
from youtube_minder.workflows.processor import ProcessingError, process_video


URL_PATTERN = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/")


def _is_valid_url(url: str) -> bool:
    return bool(URL_PATTERN.search(url or ""))


def _reset_state() -> None:
    for key in ("video_info", "last_result", "log_messages"):
        if key in st.session_state:
            del st.session_state[key]


def _render_logs(messages: List[Tuple[str, str]]) -> None:
    for level, message in messages:
        if level == "warning":
            st.warning(message)
        elif level == "error":
            st.error(message)
        else:
            st.info(message)


def main() -> None:
    st.set_page_config(page_title="YouTube Minder", page_icon="🎬", layout="centered")

    st.title("YouTube Minder")
    st.write("Summarize YouTube videos via subtitles or audio transcription.")

    url = st.text_input(
        "YouTube URL",
        key="url",
        placeholder="https://www.youtube.com/watch?v=...",
        on_change=_reset_state,
    )

    fetch_col, _ = st.columns([1, 2])
    with fetch_col:
        if st.button("Fetch video info", use_container_width=True):
            if not _is_valid_url(url):
                st.error("Please enter a valid YouTube link.")
            else:
                with st.spinner("Fetching video info..."):
                    try:
                        st.session_state.video_info = get_video_info(url)
                    except Exception as exc:
                        st.error(f"Error fetching video info: {exc}")
                        st.stop()

    video_info = st.session_state.get("video_info")
    if video_info:
        st.subheader("Video")
        st.write(f"**Title:** {video_info['title']}")
        st.write(f"**Duration:** {video_info['duration']} seconds")

    st.subheader("Summary options")
    language = st.radio("Summary language", ["English", "Russian"], horizontal=True)
    language_code = "en" if language == "English" else "ru"

    method = "subs"
    if video_info and video_info.get("duration", 0) > 1400:
        st.info("Video is longer than 1400 seconds. Subtitles will be used if available.")
        method = "subs"
    else:
        method_label = st.radio(
            "Processing method",
            ["Subtitles (faster)", "Audio (transcribe)"],
            horizontal=True,
        )
        method = "subs" if method_label.startswith("Subtitles") else "audio"

    if st.button("Process video", type="primary", use_container_width=True):
        if not _is_valid_url(url):
            st.error("Please enter a valid YouTube link.")
            st.stop()

        if "log_messages" not in st.session_state:
            st.session_state.log_messages = []
        else:
            st.session_state.log_messages.clear()

        log_placeholder = st.empty()

        def on_update(message: str, level: str = "info") -> None:
            st.session_state.log_messages.append((level, message))
            with log_placeholder.container():
                _render_logs(st.session_state.log_messages)

        with st.spinner("Processing video..."):
            try:
                result = process_video(
                    url=url,
                    language=language_code,
                    method=method,
                    on_update=on_update,
                    video_info=video_info,
                )
                st.session_state.last_result = result
            except ProcessingError as exc:
                on_update(str(exc), level="error")
                st.stop()

    result = st.session_state.get("last_result")
    if result:
        st.subheader("Summary")
        st.markdown(result.summary)

        st.subheader("Transcription")
        st.download_button(
            label="Download full text",
            data=result.transcription_text,
            file_name=result.display_filename,
            mime="text/plain",
        )
        st.caption("Generated file is cached in data/transcriptions.")


if __name__ == "__main__":
    main()
