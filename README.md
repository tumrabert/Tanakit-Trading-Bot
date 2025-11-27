# Tanakit-Trading-Bot

A powerful trading bot for Lighter.xyz, featuring an advanced **Grid Trading Bot** and limit order management.

## Features

### 🤖 Grid Trading Bot
*   **Directional Strategies**:
    *   **NEUTRAL**: Standard grid (Buy Low, Sell High). Places orders on both sides.
    *   **LONG**: Bullish grid. Initially places only Buy orders (below market). Sells are placed only to take profit on fills.
    *   **SHORT**: Bearish grid. Initially places only Sell orders (above market). Buys are placed only to take profit on fills.
*   **Auto-Refill**: Automatically replaces filled orders with opposite orders to capture volatility.
*   **Safety Mechanisms**:
    *   **Hard Cap**: Prevents exceeding exchange order limits (max 50 orders).
    *   **Grace Period**: Handles API latency to prevent duplicate orders.
    *   **Dynamic Precision**: Automatically handles price precision for any token.

### 🛠️ Order Management
*   **Open Limit Orders**: Place limit orders with optional Take Profit (TP) and Stop Loss (SL).
*   **Account Management**: Upgrade/Downgrade account tiers.

## Quick Start

### Run the Grid Bot
Use the convenience script:
```bash
./run_bot.sh
```

Or run manually via CLI:
```bash
python main.py grid --token BTC --direction LONG --leverage 10 --grids 20 --invest 100 --lower 90000 --upper 100000
```

**Parameters:**
*   `--token`: Token symbol (e.g., BTC, ETH).
*   `--direction`: Strategy direction (`LONG`, `SHORT`, `NEUTRAL`).
*   `--leverage`: Leverage multiplier (e.g., 10).
*   `--grids`: Number of grid levels (e.g., 20).
*   `--invest`: Total investment margin in USD (e.g., 100).
*   `--lower`: Lower price bound.
*   `--upper`: Upper price bound.

### Other Commands
*   **Limit Order Test**: `python main.py limit_test`
*   **Upgrade Account**: `python main.py upgrade`
*   **Downgrade Account**: `python main.py downgrade`

## Configuration

Ensure your `.env` file contains the necessary credentials:
*   `API_KEY_PRIVATE_KEY`
*   `ACCOUNT_INDEX`
*   `API_KEY_INDEX`
*   `BASE_URL`
