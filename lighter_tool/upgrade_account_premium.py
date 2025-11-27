import asyncio
import logging
import lighter
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project/.env
# Assuming this script is in project/tools/
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.DEBUG)

BASE_URL = os.getenv("BASE_URL", "https://mainnet.zklighter.elliot.ai")
API_KEY_PRIVATE_KEY = os.getenv("API_KEY_PRIVATE_KEY")
ACCOUNT_INDEX = int(os.getenv("ACCOUNT_INDEX"))
API_KEY_INDEX = int(os.getenv("API_KEY_INDEX"))


async def main():
    client = lighter.SignerClient(
        url=BASE_URL,
        private_key=API_KEY_PRIVATE_KEY,
        account_index=ACCOUNT_INDEX,
        api_key_index=API_KEY_INDEX,
    )

    try:
        err = client.check_client()
        if err is not None:
            print(f"CheckClient error: {err}")
            return

        # Use 1 hour expiry (absolute timestamp)
        import time
        expiry = int(time.time()) + 3600
        auth, err = client.create_auth_token_with_expiry(expiry)
        
        if err:
            print(f"Auth Token Error: {err}")
            return

        response = requests.post(
            f"{BASE_URL}/api/v1/changeAccountTier",
            data={"account_index": ACCOUNT_INDEX, "new_tier": "premium"},
            headers={"Authorization": auth},
        )
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return
        print(response.json())
    finally:
        await client.close()



if __name__ == "__main__":
    asyncio.run(main())
