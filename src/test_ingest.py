# src/test_ingest.py

from datetime import datetime
import sys
from pathlib import Path

# --- make sure Python can import modules from src/ (including blink_client and ingest) ---
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))

import ingest  # now this should work, and ingest can find blink_client in the same folder


# ---------- Tests for format_since ----------

def test_format_since_none_returns_none():
    """If dt is None, we should get None back."""
    result = ingest.format_since(None)
    assert result is None


def test_format_since_normal_datetime():
    """Normal datetime should be formatted as 'YYYY/MM/DD HH:MM'."""
    dt = datetime(2025, 11, 20, 14, 30)
    result = ingest.format_since(dt)
    assert result == "2025/11/20 14:30"


def test_format_since_ignores_seconds_and_microseconds():
    """Seconds and microseconds shouldn't show in the output string."""
    dt = datetime(2025, 11, 20, 14, 30, 59, 123456)
    result = ingest.format_since(dt)
    assert result == "2025/11/20 14:30"


def test_format_since_zero_padding():
    """Month/day/hour/minute should be zero-padded."""
    dt = datetime(2025, 1, 2, 9, 5)
    result = ingest.format_since(dt)
    assert result == "2025/01/02 09:05"


# ---------- Tests for get_last_downloaded_at ----------

def test_get_last_downloaded_at_none(monkeypatch):
    """
    If load_state() says last_downloaded_at is None,
    get_last_downloaded_at() should return None.
    """
    def fake_load_state():
        return {"last_downloaded_at": None}

    monkeypatch.setattr(ingest, "load_state", fake_load_state)
    result = ingest.get_last_downloaded_at()
    assert result is None


def test_get_last_downloaded_at_valid_timestamp(monkeypatch):
    """
    If load_state() returns a valid ISO timestamp string,
    get_last_downloaded_at() should return the matching datetime object.
    """
    def fake_load_state():
        return {"last_downloaded_at": "2025-11-16T23:59:59"}

    monkeypatch.setattr(ingest, "load_state", fake_load_state)

    result = ingest.get_last_downloaded_at()
    assert isinstance(result, datetime)
    assert result == datetime(2025, 11, 16, 23, 59, 59)


def test_get_last_downloaded_at_invalid_timestamp(monkeypatch):
    """
    If load_state() returns a bad timestamp string,
    get_last_downloaded_at() should swallow it and return None.
    """
    def fake_load_state():
        return {"last_downloaded_at": "not-a-real-timestamp"}

    monkeypatch.setattr(ingest, "load_state", fake_load_state)

    result = ingest.get_last_downloaded_at()
    assert result is None