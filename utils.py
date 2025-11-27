import os
import requests
import lighter
from dotenv import load_dotenv
from markets import MARKETS

load_dotenv()


PRICE_PRECISIONS = {
    "BTC": 1,
    "ETH": 2,
    "SOL": 2,
    "BNB": 1,
}

SIZE_MULTIPLIERS = {
    "BTC": 1e5,
    "ETH": 1e4,
    "SOL": 1e3, # Guessing for SOL, need verification
    "BNB": 1e3,
}

def get_size_multiplier(token):
    return SIZE_MULTIPLIERS.get(token, 1e5) # Default to 1e5

def price_to_int(price_float, token="BTC"):
    """Convert price to int format (remove decimals)"""
    precision = PRICE_PRECISIONS.get(token, 1)
    format_str = f"{{:.{precision}f}}"
    price_str = format_str.format(price_float)
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
