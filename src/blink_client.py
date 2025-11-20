import os
import logging
from pathlib import Path
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load

AUTH_PATH = Path(os.getenv("BLINK_AUTH_PATH", "blink_auth.json"))
logger = logging.getLogger(__name__)


async def get_blink_client(session: ClientSession) -> Blink:
    """
    Initialize and return a Blink client using a provided aiohttp session.
    Assumes login_once.py has already created blink_auth.json.

    NOTE: This function does NOT close the session. The caller is responsible
    for managing the session's lifetime (e.g. via `async with ClientSession()`).
    """
    if not AUTH_PATH.exists():
        raise FileNotFoundError(
            f"Blink auth file not found at {AUTH_PATH}. Run login_once.py first."
        )

    blink = Blink(session=session)

    auth_data = await json_load(str(AUTH_PATH))
    blink.auth = Auth(auth_data, no_prompt=True)

    await blink.start()
    return blink