import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import asyncio
from blink_client import get_blink_client

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

async def debug_list_cameras():
    """
    Simple debug helper to verify Blink auth and connectivity.
    Lists available cameras and then exits.
    """
    logging.basicConfig(level=logging.INFO)

    blink = await get_blink_client()
    try:
        logger.info("Connected to Blink. Available cameras:")
        for name, camera in blink.cameras.items():
            # camera has various attributes; id / serial are useful for reference
            camera_id = getattr(camera, "camera_id", None)
            serial = getattr(camera, "serial", None)
            logger.info(f"- {name} (id={camera_id}, serial={serial})")
    finally:
        # Make sure we close the underlying HTTP session
        await blink.session.close()

if __name__ == "__main__":
    asyncio.run(debug_list_cameras())