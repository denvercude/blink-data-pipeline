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

            # If we already have saved auth, load it
            if AUTH_PATH.exists():
                logger.info(f"Loading existing auth from {AUTH_PATH}")
                auth_data = await json_load(str(AUTH_PATH))
                blink.auth = Auth(auth_data, no_prompt=True)
            else:
                # First time: create an auth handler that will prompt
                logger.info("No saved auth found, prompting for credentials")
                blink.auth = Auth({}, no_prompt=False)

            try:
                # This will prompt for username/password in terminal
                await blink.start()
            except BlinkTwoFARequiredError:
                # If your account has 2FA, this will ask you to enter the code
                logger.info("Two-factor authentication required")
                await blink.prompt_2fa()
                 # Verify authentication succeeded after 2FA
            if not blink.auth.check_key_required():
                # Re-start to complete the authentication flow
                await blink.start()

            # If we reached here, we are logged in. Save tokens for future runs.
            await blink.save(str(AUTH_PATH))
            AUTH_PATH.chmod(0o600)  # Owner read/write only
            logger.info(f"Saved Blink auth to {AUTH_PATH.resolve()}")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())