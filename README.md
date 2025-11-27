# Tanakit-Trading-Bot

This project implements a trading bot for the Lighter.xyz exchange, featuring limit order placement with Take Profit (TP) and Stop Loss (SL) capabilities.

## Key Features

*   **Open Limit Orders**: Place limit orders with optional TP and SL.
*   **Grouped Orders**: Supports OCO (One-Cancels-the-Other) for TP/SL management.
*   **Token Support**: Supports multiple tokens (BTC, ETH, SOL, BNB, etc.) via a centralized market mapping.
*   **Leverage**: Configurable leverage for position sizing.
*   **Utils**: Helper functions for price conversion, client initialization, and market data fetching.

## Project Structure

*   `open_limit_order.py`: Main script to open limit orders. Contains the `open_limit_order` function and a test suite.
*   `markets.py`: Dictionary mapping token symbols (e.g., "BTC") to their Lighter market IDs.
*   `utils.py`: Helper functions:
    *   `price_to_int`: Converts float prices to integer format required by the API.
    *   `get_client`: Initializes the Lighter SignerClient.
    *   `get_market_price`: Fetches the current Best Bid and Best Ask for a token.
*   `test_open_limit_order.py`: Unit tests for the order placement logic.

## Usage

### Open a Limit Order

```python
from open_limit_order import open_limit_order
import asyncio

async def main():
    # Example: Open Long ETH with 10x Leverage
    # Margin: $53, Price: 3200
    # TP: 3300, SL: 3000
    await open_limit_order(
        token="ETH", 
        leverage=10, 
        side="Long", 
        amount_in_usd=53, 
        price=3200, 
        take_profit_price=3300, 
        stop_loss_price=3000
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Run Tests

To run the built-in verification suite (tests BTC, ETH, SOL, BNB):
```bash
python open_limit_order.py
```

To run unit tests:
```bash
python test_open_limit_order.py
```

## Configuration

Ensure your `.env` file contains the necessary credentials:
*   `API_KEY_PRIVATE_KEY`
*   `ACCOUNT_INDEX`
*   `API_KEY_INDEX`
*   `BASE_URL`
