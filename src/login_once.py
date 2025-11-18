import asyncio
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load
from blinkpy.exceptions import BlinkTwoFARequiredError

load_dotenv()
AUTH_PATH = Path(os.getenv("BLINK_AUTH_PATH", "blink_auth.json"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        async with ClientSession() as session:
            blink = Blink(session=session)

            if AUTH_PATH.exists():
                logger.info(f"Loading existing auth from {AUTH_PATH}")
                auth_data = await json_load(str(AUTH_PATH))
                blink.auth = Auth(auth_data, no_prompt=True)
            else:
                logger.info("No saved auth found, prompting for credentials")
                blink.auth = Auth({}, no_prompt=False)

            try:
                await blink.start()
            except BlinkTwoFARequiredError:
                logger.info("Two-factor authentication required")
                await blink.prompt_2fa()
            if blink.auth.token and blink.auth.account_id and blink.auth.region_id:
                await blink.save(str(AUTH_PATH))
                AUTH_PATH.chmod(0o600)
                logger.info(f"Saved Blink auth to {AUTH_PATH.resolve()}")
            else:
                logger.error("Auth incomplete — token or region info missing, not saving.")
    except BlinkTwoFARequiredError:
        # Re-raise if 2FA wasn't handled properly
        logger.error("Two-factor authentication failed or was not completed")
        raise
    except (OSError, IOError) as e:
        logger.error(f"File operation failed: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during authentication: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())