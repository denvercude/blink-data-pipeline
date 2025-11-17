import os
import logging
from pathlib import Path
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load

AUTH_PATH = Path(os.getenv("BLINK_AUTH_PATH", "blink_auth.json"))
logger = logging.getLogger(__name__)

async def get_blink_client():
    """
    Loads saved Blink authentication tokens and returns a ready-to-use Blink client.
    Assumes login_once.py has already created blink_auth.json.
    """
    if not AUTH_PATH.exists():
        raise FileNotFoundError(
            f"Blink auth file not found at {AUTH_PATH}. Run login_once.py first."
        )

    async with ClientSession() as session:
        blink = Blink(session=session)
        auth_data = await json_load(str(AUTH_PATH))
        blink.auth = Auth(auth_data, no_prompt=True)
        await blink.start()
        return blink