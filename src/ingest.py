import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import asyncio
from aiohttp import ClientSession
from blink_client import get_blink_client
from datetime import datetime, timedelta

# BASE_DIR = src/
BASE_DIR = Path(__file__).resolve().parent

# PROJECT_ROOT = repo root
PROJECT_ROOT = BASE_DIR.parent

# data/ is at the repo root:
# blink-data-pipeline/
#   ├─ data/
#   │   ├─ meta_data/
#   │   └─ raw_clips/
#   └─ src/
DATA_DIR = PROJECT_ROOT / "data"
RAW_CLIPS_DIR = DATA_DIR / "raw_clips"
META_DIR = DATA_DIR / "meta_data"

STATE_PATH = META_DIR / "state.json"
CLIPS_CSV_PATH = META_DIR / "clips.csv"

logger = logging.getLogger(__name__)

def format_since(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert a datetime into the string format expected by blink.download_videos.
    Example format: '2025/11/20 14:30'

    If dt is None, returns None (blinkpy will use its default behavior).
    """
    if dt is None:
        return None
    return dt.strftime("%Y/%m/%d %H:%M")

async def ingest_new_clips():
    """
    Download Blink clips for camera 'sort_C15' from a fixed window:
    yesterday at 9:00 AM (local time) up to now.

    NOTE: Blink's API only supports a 'since' parameter (no 'until'), so this
    will download clips recorded after yesterday 9 AM. If you want to restrict
    strictly to 9–12, you can later post-filter the downloaded files.
    """
    logging.basicConfig(level=logging.INFO)

    # Compute "yesterday at 09:00:00" in local time
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    yesterday_9am = yesterday.replace(hour=9, minute=0, second=0, microsecond=0)

    since_str = format_since(yesterday_9am)
    logger.info(f"Using fixed ingestion window: yesterday 9 AM (since {since_str}).")

    async with ClientSession() as session:
        blink = await get_blink_client(session)

        # Only the sort_C15 camera
        cameras_of_interest = ["sort_C15"]

        logger.info(f"Downloading videos for cameras: {cameras_of_interest}")
        logger.info(f"Saving to: {RAW_CLIPS_DIR.resolve()}")

        RAW_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

        # Blinkpy call – this does the real work
        await blink.download_videos(
            str(RAW_CLIPS_DIR),
            since=since_str,      # yesterday at 9:00 AM
            camera=cameras_of_interest,
            delay=2,
        )

        # NOTE: blinkpy may emit an 'Unclosed client session' warning;
        # this is a known quirk and not fatal for our simple script.

    logger.info("Finished downloading clips for yesterday 9 AM and later.")

def load_state() -> dict:
    """
    Load ingestion state from state.json.

    Returns a dict like:
    {
        "last_downloaded_at": "2025-11-16T23:59:59"
    }
    or a default if the file doesn't exist.
    """
    if STATE_PATH.exists():
        with STATE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Default state: never downloaded anything
    return {"last_downloaded_at": None}


def save_state(state: dict) -> None:
    """
    Save the ingestion state back to state.json.
    """
    META_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_last_downloaded_at() -> Optional[datetime]:
    """
    Convenience accessor that returns last_downloaded_at as a datetime object,
    or None if we've never downloaded anything.
    """
    state = load_state()
    ts = state.get("last_downloaded_at")
    if ts is None:
        return None

    # Expecting an ISO 8601 string like "2025-11-16T23:59:59"
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        logger.warning("Invalid last_downloaded_at in state.json, ignoring it.")
        return None


def set_last_downloaded_at(dt: datetime) -> None:
    """
    Update the state's last_downloaded_at to the given datetime.
    """
    state = load_state()
    state["last_downloaded_at"] = dt.isoformat(timespec="seconds")
    save_state(state)

async def close_blink_sessions(blink):
    """
    Attempts to close any aiohttp sessions Blink may have created internally.
    blinkpy is inconsistent with session management, so we try all known locations.
    """
    # Case 1: Latest versions store it here
    sess = getattr(blink, "aio_session", None)
    if sess:
        await sess.close()

    # Case 2: Older versions stored it here
    sess2 = getattr(blink, "_session", None)
    if sess2:
        await sess2.close()

    # Case 3: BlinkSyncModule subclients may have sessions
    if hasattr(blink, "sync"):
        for sync in blink.sync.values():
            subsess = getattr(sync, "session", None)
            if subsess:
                await subsess.close()

async def debug_list_cameras():
    logging.basicConfig(level=logging.INFO)

    async with ClientSession() as session:
        blink = await get_blink_client(session)
        logger.info("Connected to Blink. Available cameras:")
        for name, camera in blink.cameras.items():
            camera_id = getattr(camera, "camera_id", None)
            serial = getattr(camera, "serial", None)
            logger.info(f"- {name} (id={camera_id}, serial={serial})")

        # NEW: close any Blink-created sessions
        await close_blink_sessions(blink)

if __name__ == "__main__":
    asyncio.run(ingest_new_clips())