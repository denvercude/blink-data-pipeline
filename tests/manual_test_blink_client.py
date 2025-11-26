#manual_test_blink_client.py


import asyncio
from pathlib import Path
import sys

# === Make project root importable so we can do `import src.blink_client` ===
# This file is: <project_root>/tests/manual_test_blink_client.py
# So `parents[1]` gives us <project_root>.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from aiohttp import ClientSession

# Import the function under test and the module so we can patch AUTH_PATH
import src.blink_client as blink_module
from src.blink_client import get_blink_client, AUTH_PATH as DEFAULT_AUTH_PATH


async def test_valid_path_client() -> None:
    """
    Test case 1: valid-path client creation.

    Goal:
      - Make sure get_blink_client() returns a Blink instance
        when the auth file exists and contains valid auth data.
      - This is the "does it basically work?" sanity check.

    If the auth file is missing, this test is marked as FAIL instead of failing.
    """
    print("=== Test case 1: valid-path client creation ===")
    print(f"Using AUTH_PATH: {DEFAULT_AUTH_PATH}\n")

    async with ClientSession() as session:
        try:
            blink = await get_blink_client(session)
        except FileNotFoundError as e:
            print("Test case 1 FAIL: auth file not found.")
            print(f"  {e}\n")
            return

    print(f"Created Blink client: {blink!r}")
    print(f"Blink auth object: {getattr(blink, 'auth', None)!r}")
    print("Test case 1 PASS: client created and initialized without exceptions.\n")


async def test_missing_auth_file() -> None:
    """
    Test case 2: Missing auth file should raise FileNotFoundError.

    Goal:
      - Temporarily point AUTH_PATH at a definitely-nonexistent file.
      - Verify that get_blink_client() raises FileNotFoundError.

    This directly tests the error-handling branch in get_blink_client.
    """
    print("=== Test case 2: missing auth file raises FileNotFoundError ===")

    # Save the original path so we can restore it after the test.
    original_auth_path = blink_module.AUTH_PATH

    try:
        # Use a filename that should not exist.
        fake_path = Path("this_file_should_not_exist_1234.json")
        blink_module.AUTH_PATH = fake_path
        print(f"Temporarily setting AUTH_PATH to: {fake_path}")

        async with ClientSession() as session:
            try:
                await get_blink_client(session)
            except FileNotFoundError as e:
                print("Caught expected FileNotFoundError:")
                print(f"  {e}")
                print("Test case 2 PASS.\n")
            else:
                print("Test case 2 FAIL: expected FileNotFoundError was NOT raised.\n")

    finally:
        # Always restore AUTH_PATH so future runs use the real value.
        blink_module.AUTH_PATH = original_auth_path


async def test_session_lifetime_not_closed() -> None:
    """
    Test case 3: Session lifetime is NOT managed by get_blink_client.

    Goal:
      - Verify that get_blink_client() does not close the aiohttp ClientSession.
      - The caller should be responsible for closing the session.

    Approach:
      - Create a ClientSession.
      - Call get_blink_client(session).
      - Check session.closed before we manually close it.
      - If auth file is missing, mark as FAIL (we can't fully verify behavior).
    """
    print("=== Test case 3: session lifetime NOT managed by get_blink_client ===")
    print("Creating a ClientSession and calling get_blink_client...\n")

    session = ClientSession()
    try:
        try:
            _ = await get_blink_client(session)
        except FileNotFoundError as e:
            print("Test case 3 FAIL: auth file not found, cannot fully verify behavior.")
            print(f"  {e}\n")
            return

        # At this point, get_blink_client has returned and should NOT have closed the session.
        if session.closed:
            print("Test case 3 FAIL: session was closed inside get_blink_client.")
        else:
            print("Test case 3 PASS: session is still open after get_blink_client;")
            print("  caller is responsible for closing the session.")

        print()

    finally:
        # Caller explicitly closes the session to clean up.
        await session.close()


async def main() -> None:
    """
    Run all manual tests in sequence.

    These correspond to the three test cases described in the write-up:
      1) Happy path when auth file exists.
      2) Error path when auth file is missing.
      3) Session lifetime behavior (not closed by get_blink_client).
    """
    print("Starting manual tests for src.blink_client.get_blink_client\n")
    print(f"Default AUTH_PATH is: {DEFAULT_AUTH_PATH}\n")

    await test_valid_path_client()
    await test_missing_auth_file()
    await test_session_lifetime_not_closed()


if __name__ == "__main__":
    # asyncio.run() drives the async tests when the script is run directly.
    asyncio.run(main())