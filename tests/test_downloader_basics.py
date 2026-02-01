import os
from pathlib import Path

import pytest

from youtube_minder.services import downloader


def test_clean_vtt_text_strips_metadata_and_duplicates():
    vtt = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:01.000
<c>Let's welcome our first</c>

00:00:01.000 --> 00:00:02.000
Let's welcome our first

NOTE This is a note block
should be skipped

00:00:02.000 --> 00:00:03.000
[applause]

[applause]
"""
    cleaned = downloader._clean_vtt_text(vtt)
    assert cleaned == "Let's welcome our first\n\n[applause]"


def test_parse_cookies_from_browser_spec():
    assert downloader._parse_cookies_from_browser_spec("chrome") == ("chrome",)
    assert downloader._parse_cookies_from_browser_spec("chrome:Default") == ("chrome", "Default")
    assert downloader._parse_cookies_from_browser_spec("chrome:Profile 1:Keychain:/tmp/cookies.db") == (
        "chrome",
        "Profile 1",
        "Keychain",
        "/tmp/cookies.db",
    )


def test_download_subtitles_retries_and_returns_clean_text(monkeypatch, tmp_path):
    attempts = {"count": 0}

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download=True):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise Exception("HTTP Error 429: Too Many Requests")

            outdir = Path(self.opts["outtmpl"]).parent
            video_id = "abc123"
            vtt_path = outdir / f"{video_id}.en.vtt"
            vtt_path.write_text(
                "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello\n",
                encoding="utf-8",
            )
            return {"id": video_id}

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FakeYoutubeDL)
    monkeypatch.setenv("SUBS_RETRY_ATTEMPTS", "3")
    monkeypatch.setenv("SUBS_RETRY_BASE_SLEEP", "0")

    sleep_calls = {"count": 0}

    def _fake_sleep(_):
        sleep_calls["count"] += 1

    monkeypatch.setattr(downloader.time, "sleep", _fake_sleep)

    result = downloader.download_subtitles("https://example.com", str(tmp_path), langs=["en"])
    assert result == "Hello"
    assert attempts["count"] == 3
    assert sleep_calls["count"] == 2
