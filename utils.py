import os
import requests
import lighter
from dotenv import load_dotenv
from markets import MARKETS

load_dotenv()


def price_to_int(price_float):
    """Convert price to int format (remove decimals)"""
    # Assuming standard behavior: 3000.50 -> 30005
    # Note: This logic might need adjustment based on specific token precision/decimals
    # Using the logic from start_grid.py
    price_str = f"{price_float:.1f}"
    price_int = int(price_str.replace(".", ""))
    return price_int

async def get_client():
    api_key_pk = os.getenv('API_KEY_PRIVATE_KEY')
    account_index = int(os.getenv('ACCOUNT_INDEX'))
    api_key_index = int(os.getenv('API_KEY_INDEX'))
    base_url = os.getenv('BASE_URL')
    
    client = lighter.SignerClient(
        url=base_url,
        private_key=api_key_pk,
        account_index=account_index,
        api_key_index=api_key_index
    )
    return client

def get_market_price(token):
    market_index = MARKETS.get(token)
    if market_index is None:
        raise ValueError(f"Unknown token: {token}")
    
    base_url = os.getenv('BASE_URL')
    url = f"{base_url}/api/v1/orderBookOrders?market_id={market_index}&limit=1"
    response = requests.get(url)
    data = response.json()
    
    if not data.get('bids') or not data.get('asks'):
        raise ValueError(f"Order book empty for {token} (ID {market_index})")
        
    best_bid = float(data['bids'][0]['price'])
    best_ask = float(data['asks'][0]['price'])
    return best_bid, best_ask
