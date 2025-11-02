import asyncio
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

async def main():
    async with ClientSession() as session:
        blink = Blink(session=session)

        # If we already have saved auth, load it
        if AUTH_PATH.exists():
            auth_data = await json_load(str(AUTH_PATH))
            blink.auth = Auth(auth_data, no_prompt=True)
        else:
            # First time: create an auth handler that will prompt
            blink.auth = Auth({}, no_prompt=False)

        try:
            # This will prompt for username/password in terminal
            await blink.start()
        except BlinkTwoFARequiredError:
            # If your account has 2FA, this will ask you to enter the code
            await blink.prompt_2fa()

        # If we reached here, we are logged in. Save tokens for future runs.
        await blink.save(str(AUTH_PATH))
        print(f"Saved Blink auth to {AUTH_PATH.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())