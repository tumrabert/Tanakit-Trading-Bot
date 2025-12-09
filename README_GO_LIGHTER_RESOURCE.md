# Lighter API Documentation Resource

> **Source:** [Lighter API Documentation](https://apidocs.lighter.xyz/docs/)  
> **Last Updated:** December 9, 2025

This document contains the complete extracted documentation from the Lighter API, covering everything from system setup to creating and cancelling orders, fetching exchange data, and more.

---

## Table of Contents

1. [Get Started For Programmers](#get-started-for-programmers)
2. [SDK](#sdk)  
3. [Account Index](#account-index)
4. [Account Types](#account-types)
5. [Rate Limits](#rate-limits)
6. [Volume Quota](#volume-quota)
7. [Nonce Management](#nonce-management)
8. [WebSocket](#websocket)
9. [Data Structures, Constants and Errors](#data-structures-constants-and-errors)

---

## Get Started For Programmers

Welcome to the Lighter SDK and API Introduction. Here, we will go through everything from the system setup, to creating and cancelling all types of orders, to fetching exchange data.

### Setting up an API KEY

In order to get started using the Lighter API, you must first set up an **API_KEY_PRIVATE_KEY**, as you will need it to sign any transaction you want to make. You can find how to do it in the following [example](https://github.com/elliottech/lighter-python/blob/main/examples/system_setup.py).

The **BASE_URL** will reflect if your key is generated on testnet or mainnet:
- **Mainnet:** `https://mainnet.zklighter.elliot.ai`
- **Testnet:** `https://testnet.zklighter.elliot.ai`

> **Note:** You also need to provide your **ETH_PRIVATE_KEY**.

#### API Key Index Configuration
- You can setup up to **253 API keys** (2 <= `API_KEY_INDEX` <= 254)
- Index **0** is reserved for the desktop
- Index **1** is reserved for the mobile  
- Index **255** can be used as a value for the `api_key_index` parameter of the `apikeys` method of the **AccountApi** for getting data about all the API keys

#### Finding Your Account Index
If you do not know your **ACCOUNT_INDEX**, you can find it by querying the **AccountApi** for your account data, as shown in this [example](https://github.com/elliottech/lighter-python/blob/main/examples/get_info.py).

### Account Types

Lighter API users can operate under a **Standard** or **Premium** account:
- **Standard account:** Fee-less (0% maker / 0% taker)
- **Premium accounts:** Pay 0.2 bps (0.002%) maker and 2 bps (0.02%) taker fees

Find out more in [Account Types](#account-types).

### The Signer

In order to create a transaction (create/cancel/modify order), you need to use the **SignerClient**. Initialize with the following code:

```python
client = lighter.SignerClient(
    url=BASE_URL,
    private_key=API_KEY_PRIVATE_KEY,
    account_index=ACCOUNT_INDEX,
    api_key_index=API_KEY_INDEX
)
```

The code for the signer can be found in the [signer_client.py](https://github.com/elliottech/lighter-python/blob/main/lighter/signer_client.py) file. 

> **Note:** The signer uses a binary. The code for it can be found in the [lighter-go](https://github.com/elliottech/lighter-go) public repo, and you can compile it yourself using the [justfile](https://github.com/elliottech/lighter-go/blob/main/justfile).

### Nonce

When signing a transaction, you may need to provide a **nonce** (number used once). A nonce needs to be incremented each time you sign something. You can:
- Get the next nonce using the **TransactionApi's** `next_nonce` method
- Manage incrementing it yourself

> **Note:** Each nonce is handled per **API_KEY**.

### Signing a Transaction

Sign a transaction using the **SignerClient's** methods:
- `sign_create_order`
- `sign_modify_order`
- `sign_cancel_order`
- Other similar methods

For pushing the transaction, call `send_tx` or `send_tx_batch` using the **TransactionApi**. Here's an [example](https://github.com/elliottech/lighter-python/blob/main/examples/send_tx_batch.py).

#### Parameters
- `base_amount`, `price` are to be passed as **integers**
- `client_order_index` is a **unique** identifier (across all markets) you provide to reference the order later

#### Order Types
```
ORDER_TYPE_LIMIT
ORDER_TYPE_MARKET
ORDER_TYPE_STOP_LOSS
ORDER_TYPE_STOP_LOSS_LIMIT
ORDER_TYPE_TAKE_PROFIT
ORDER_TYPE_TAKE_PROFIT_LIMIT
ORDER_TYPE_TWAP
```

#### Time In Force Options
```
ORDER_TIME_IN_FORCE_IMMEDIATE_OR_CANCEL
ORDER_TIME_IN_FORCE_GOOD_TILL_TIME
ORDER_TIME_IN_FORCE_POST_ONLY
```

### Signer Client Useful Wrapper Functions

The SignerClient provides several functions that sign and push transactions:

| Function | Description |
|----------|-------------|
| `create_order` | Signs and pushes a create order transaction |
| [`create_market_order`](https://github.com/elliottech/lighter-python/blob/main/examples/create_market_order.py) | Signs and pushes a create order transaction for a market order |
| `create_cancel_order` | Signs and pushes a cancel transaction. Note: `order_index` must equal the `client_order_index` of the order to cancel |
| `cancel_all_orders` | Signs and pushes a cancel all transactions (see behavior below) |
| `create_auth_token_with_expiry` | Creates an auth token for API and WebSocket methods |

#### Cancel All Orders Behavior

Depending on the `time_in_force` provided:
| Time In Force | Action |
|--------------|--------|
| `ORDER_TIME_IN_FORCE_IMMEDIATE_OR_CANCEL` | ImmediateCancelAll |
| `ORDER_TIME_IN_FORCE_GOOD_TILL_TIME` | ScheduledCancelAll |
| `ORDER_TIME_IN_FORCE_POST_ONLY` | AbortScheduledCancelAll |

### API Classes

The SDK provides API classes that make calling the Lighter API easier:

#### AccountApi - Provides account data
| Method | Description |
|--------|-------------|
| `account` | Get account data by `l1_address` or `index` |
| `accounts_by_l1_address` | Get data about all accounts (master account and subaccounts) |
| `apikeys` | Get data about API keys (use `api_key_index = 255` for all keys) |

#### TransactionApi - Provides transaction related data
| Method | Description |
|--------|-------------|
| `next_nonce` | Get next nonce for signing a transaction using a certain API key |
| `send_tx` | Push a transaction |
| `send_tx_batch` | Push several transactions at once |

#### OrderApi - Provides data about orders, trades and the orderbook
| Method | Description |
|--------|-------------|
| `order_book_details` | Get data about a specific market's orderbook |
| `order_books` | Get data about all markets' orderbooks |

You can find more API classes [here](https://github.com/elliottech/lighter-python/tree/main/lighter/api).

### WebSockets

Lighter provides access to essential info using websockets. A simple **WsClient** for subscribing to account and orderbook updates is implemented [here](https://github.com/elliottech/lighter-python/blob/main/lighter/ws_client.py).

For more data access, connect to the websockets without the provided WsClient. See the [WebSocket](#websocket) section for streams, connection methods, and data formats.

---

## SDK

### Public SDKs

| Language | Repository |
|----------|------------|
| **Python** | [https://github.com/elliottech/lighter-python](https://github.com/elliottech/lighter-python) |
| **Go** | [https://github.com/elliottech/lighter-go](https://github.com/elliottech/lighter-go) |

---

## Account Index

The account index is how Lighter identifies wallets using integer numbers.

### How to Find Your Account Index

1. Query the `accountsByL1Address` endpoint
2. The response has `sub_accounts` as a list
3. The first element of the list is your main account
4. The index of the main account is your account index

---

## Account Types

Lighter API users can operate under a **Standard** or **Premium** account.

### Premium Account (Opt-in) -- Suitable for HFT

Best for high-frequency trading with the lowest latency on Lighter.

| Feature | Value |
|---------|-------|
| **Fees** | 0.002% Maker, 0.02% Taker |
| **Maker/Cancel Latency** | 0ms |
| **Taker Latency** | 150ms |
| **Volume Quota** | Part of [Volume Quota Program](#volume-quota) |

### Standard Account (Default) -- Suitable for Retail

Best for retail and latency insensitive traders.

| Feature | Value |
|---------|-------|
| **Fees** | 0% Maker, 0% Taker |
| **Taker Latency** | 300ms |
| **Maker Latency** | 200ms |
| **Cancel Order Latency** | 100ms |

### Account Switch

You can change your Account Type (tied to your L1 address) using the `/changeAccountTier` endpoint.

#### Prerequisites
- No open positions
- No open orders
- At least 24 hours have passed since the last call

#### Python Example - Switch to Premium

```python
import asyncio
import logging
import lighter
import requests

logging.basicConfig(level=logging.DEBUG)
BASE_URL = "https://mainnet.zklighter.elliot.ai"

# You can get the values from the system_setup.py script
# API_KEY_PRIVATE_KEY = 
# ACCOUNT_INDEX = 
# API_KEY_INDEX = 

async def main():
    client = lighter.SignerClient(
        url=BASE_URL,
        private_key=API_KEY_PRIVATE_KEY,
        account_index=ACCOUNT_INDEX,
        api_key_index=API_KEY_INDEX,
    )
    
    err = client.check_client()
    if err is not None:
        print(f"CheckClient error: {err}")
        return
        
    auth, err = client.create_auth_token_with_expiry(
        lighter.SignerClient.DEFAULT_10_MIN_AUTH_EXPIRY
    )
    
    response = requests.post(
        f"{BASE_URL}/api/v1/changeAccountTier",
        data={"account_index": ACCOUNT_INDEX, "new_tier": "premium"},
        headers={"Authorization": auth},
    )
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    print(response.json())

if __name__ == "__main__":
    asyncio.run(main())
```

### How Fees Are Collected

- **Isolated Margin:** Fees are taken from the isolated position itself. If needed, funds are automatically transferred from cross margin to keep the position healthy.
- **Cross Margin:** Fees are always deducted directly from the available cross balance.

> **Note:** Sub-accounts share the same tier as the main L1 address on the account.

---

## Rate Limits

Rate limits are enforced on both REST API and WebSocket usage. These limits apply to both IP address and L1 wallet address.

### 📊 REST API Endpoint Limits

Base URL: `https://mainnet.zklighter.elliot.ai/`

| Account Type | Limit |
|-------------|-------|
| **Premium** | 24,000 weighted requests per minute |
| **Standard** | 60 requests per minute |

> **Note:** Only `sendTx` and `sendTxBatch` can increase in quota via [Volume Quota](#volume-quota).

#### Endpoint Weights

| Endpoints | Weight (Per User) |
|-----------|-------------------|
| `/api/v1/sendTx`, `/api/v1/sendTxBatch`, `/api/v1/nextNonce` | 6 |
| `/api/v1/publicPools`, `/api/v1/txFromL1TxHash` | 50 |
| `/api/v1/accountInactiveOrders`, `/api/v1/deposit/latest` | 100 |
| `/api/v1/apikeys` | 150 |
| `/api/v1/trades`, `/api/v1/recentTrades` | 1200 |
| Other endpoints | 300 |

### 🌐 Standard Tier Rate Limit

Requests from a single IP address and L1 wallet address are capped at **60 requests per minute** under Standard Account.

### 📊 Explorer REST API Endpoint Limits

Base URL: `https://explorer.elliot.ai/`

Both Standard and Premium users have the same limit of **15 weighted requests per minute**.

| Endpoints | Weight (Per User) |
|-----------|-------------------|
| `/api/search` | 3 |
| `/api/accounts/param/positions`, `/api/accounts/param/logs` | 2 |
| Other endpoints | 1 |

### 🔌 WebSocket Limits

Per IP limits to prevent resource exhaustion:

| Limit Type | Value |
|------------|-------|
| Connections | 100 |
| Subscriptions per connection | 100 |
| Total Subscriptions | 1,000 |
| Max Messages Per Minute | 200 |
| Max Inflight Messages | 50 |
| Unique Accounts | 10 |

### 🧾 Transaction Type Limits (per user)

These limits apply **only to Standard Accounts**:
- `L2Withdraw`
- `L2UpdateLeverage`
- `L2CreateSubAccount`
- `L2CreatePublicPool`
- `L2ChangePubKey`
- `L2Transfer`

### ⛔ Rate Limit Exceeding Behavior

If you exceed any rate limit:
- You will receive an **HTTP 429 Too Many Requests** error
- For WebSocket connections, excessive messages may result in disconnection

> **Recommendation:** Implement proper backoff and retry strategies.

---

## Volume Quota

Volume Quota gives users higher rate limits on `SendTx` and `SendTxBatch` based on trading volume. **Only available to Premium accounts.**

### How It Works

- For every **$10 USD of trading volume**, traders receive **+1 transaction limit** (volume quota increases by 1)
- `SendTx` and `SendTxBatch` requests return remaining quota (e.g., "10780 volume quota remaining.")
- Every **15 seconds**, you get a free `SendTx` or `SendTxBatch` which won't consume volume quota
- Volume quota is **shared across all sub-accounts** under the same L1 address

### Quota Limits

| Type | Value |
|------|-------|
| **New Account Starting Quota** | 1,000 |
| **Maximum TX Allowance** | 5,000,000 |
| **Expiration** | Never expires |

> **Note:** This differs from [Rate Limits](#rate-limits), which enforce a maximum of 24,000 weight per 60 seconds for premium accounts.

---

## Nonce Management

### Best Practice: Use Multiple API Keys

You can use up to **255 different `API_KEY_INDEX` values**. Each index manages its own nonce stream independently, allowing parallel transaction submission.

### Manual Nonce Management

If a transaction has a **non-error response**, you can increase the nonce manually (nonce will NOT update right away on the server side).

> **Note:** Cases where there is no API error but the transaction fails internally should be very rare.

---

## WebSocket

This section covers the zkLighter WebSocket server for real-time data.

### Connection

| Environment | URL |
|-------------|-----|
| **Mainnet** | `wss://mainnet.zklighter.elliot.ai/stream` |
| **Testnet** | `wss://testnet.zklighter.elliot.ai/stream` |

#### Quick Connect with wscat

```bash
wscat -c 'wss://mainnet.zklighter.elliot.ai/stream'
```

### Send Tx

Send transactions via WebSocket:

```json
{
  "type": "jsonapi/sendtx",
  "data": {
    "tx_type": INTEGER,
    "tx_info": ...
  }
}
```

The `tx_type` options can be found in the [SignerClient](https://github.com/elliottech/lighter-python/blob/main/lighter/signer_client.py) file.

**Example:** [ws_send_tx.py](https://github.com/elliottech/lighter-python/blob/main/examples/ws_send_tx.py)

### Send Batch Tx

Send batch transactions (up to 50 transactions in a single message):

```json
{
  "type": "jsonapi/sendtxbatch",
  "data": {
    "tx_types": "[INTEGER]",
    "tx_infos": "[tx_info]"
  }
}
```

**Example:** [ws_send_batch_tx.py](https://github.com/elliottech/lighter-python/blob/main/examples/ws_send_batch_tx.py)

### Data Types

#### Transaction JSON

```json
{
  "hash": "STRING",
  "type": "INTEGER",
  "info": "STRING",
  "event_info": "STRING",
  "status": "INTEGER",
  "transaction_index": "INTEGER",
  "l1_address": "STRING",
  "account_index": "INTEGER",
  "nonce": "INTEGER",
  "expire_at": "INTEGER",
  "block_height": "INTEGER",
  "queued_at": "INTEGER",
  "executed_at": "INTEGER",
  "sequence_index": "INTEGER",
  "parent_hash": "STRING"
}
```

#### Order JSON

```json
{
  "order_index": "INTEGER",
  "client_order_index": "INTEGER",
  "order_id": "STRING",
  "client_order_id": "STRING",
  "market_index": "INTEGER",
  "owner_account_index": "INTEGER",
  "initial_base_amount": "STRING",
  "price": "STRING",
  "nonce": "INTEGER",
  "remaining_base_amount": "STRING",
  "is_ask": "BOOL",
  "base_size": "INTEGER",
  "base_price": "INTEGER",
  "filled_base_amount": "STRING",
  "filled_quote_amount": "STRING",
  "side": "STRING",
  "type": "STRING",
  "time_in_force": "STRING",
  "reduce_only": "BOOL",
  "trigger_price": "STRING",
  "order_expiry": "INTEGER",
  "status": "STRING",
  "trigger_status": "STRING",
  "trigger_time": "INTEGER",
  "parent_order_index": "INTEGER",
  "parent_order_id": "STRING",
  "to_trigger_order_id_0": "STRING",
  "to_trigger_order_id_1": "STRING",
  "to_cancel_order_id_0": "STRING",
  "block_height": "INTEGER",
  "timestamp": "INTEGER"
}
```

### Channels

#### Order Book

Subscribe to new ask and bid orders for a given market:

```json
{ "type": "subscribe", "channel": "order_book/{MARKET_INDEX}" }
```

**Example Response:**
```json
{
  "channel": "order_book:0",
  "offset": 41692864,
  "order_book": {
    "code": 0,
    "asks": [{ "price": "3327.46", "size": "29.0915" }],
    "bids": [{ "price": "3338.80", "size": "10.2898" }],
    "offset": 41692864
  },
  "type": "update/order_book"
}
```

#### Market Stats

Subscribe to market statistics:

```json
{ "type": "subscribe", "channel": "market_stats/{MARKET_INDEX}" }
```

Or for all markets:
```json
{ "type": "subscribe", "channel": "market_stats/all" }
```

**Example Response:**
```json
{
  "channel": "market_stats:0",
  "market_stats": {
    "market_id": 0,
    "index_price": "3335.04",
    "mark_price": "3335.09",
    "open_interest": "235.25",
    "last_trade_price": "3335.65",
    "current_funding_rate": "0.0057",
    "funding_rate": "0.0005",
    "funding_timestamp": 1722337200000,
    "daily_base_token_volume": 230206.48999999944,
    "daily_quote_token_volume": 765295250.9804002,
    "daily_price_low": 3265.13,
    "daily_price_high": 3386.01,
    "daily_price_change": -1.1562612047992835
  },
  "type": "update/market_stats"
}
```

#### Account All

Subscribe to specific account market data for all markets:

```json
{ "type": "subscribe", "channel": "account_all/{ACCOUNT_ID}" }
```

**Response includes:**
- Daily/weekly/monthly/total trades count and volume
- Funding histories
- Positions
- Pool shares
- Trades

#### Other Channels

| Channel | Description |
|---------|-------------|
| `trade` | Trade updates |
| `account_market` | Account-specific market data |
| `account_stats` | Account statistics |
| `account_tx` | Account transactions |
| `account_all_orders` | All account orders |
| `account_orders` | Account orders (filtered) |
| `account_all_trades` | All account trades |
| `account_all_positions` | All account positions |
| `height` | Block height updates |
| `pool_data` | Pool data updates |
| `pool_info` | Pool information |
| `notification` | Notifications |

---

## Data Structures, Constants and Errors

### Data and Event Structures

#### Order Structure (Go)

```go
type Order struct {
    OrderIndex           int64  `json:"i"`
    ClientOrderIndex     int64  `json:"u"`
    OwnerAccountId       int64  `json:"a"`
    InitialBaseAmount    int64  `json:"is"`
    Price                uint32 `json:"p"`
    RemainingBaseAmount  int64  `json:"rs"`
    IsAsk                uint8  `json:"ia"`
    Type                 uint8  `json:"ot"`
    TimeInForce          uint8  `json:"f"`
    ReduceOnly           uint8  `json:"ro"`
    TriggerPrice         uint32 `json:"tp"`
    Expiry               int64  `json:"e"`
    Status               uint8  `json:"st"`
    TriggerStatus        uint8  `json:"ts"`
    ToTriggerOrderIndex0 int64  `json:"t0"`
    ToTriggerOrderIndex1 int64  `json:"t1"`
    ToCancelOrderIndex0  int64  `json:"c0"`
}
```

#### CancelOrder Structure

```go
type CancelOrder struct {
    AccountId        int64  `json:"a"`
    OrderIndex       int64  `json:"i"`
    ClientOrderIndex int64  `json:"u"`
    AppError         string `json:"ae"`
}
```

#### ModifyOrder Structure

```go
type ModifyOrder struct {
    MarketId  uint8  `json:"m"`
    OldOrder  *Order `json:"oo"`
    NewOrder  *Order `json:"no"`
    AppError  string `json:"ae"`
}
```

#### Trade Structure

```go
type Trade struct {
    Price    uint32 `json:"p"`
    Size     int64  `json:"s"`
    TakerFee int32  `json:"tf"`
    MakerFee int32  `json:"mf"`
}
```

### Constants - Transaction Types

| Constant | Value |
|----------|-------|
| `TxTypeL2ChangePubKey` | 8 |
| `TxTypeL2CreateSubAccount` | 9 |
| `TxTypeL2CreatePublicPool` | 10 |
| `TxTypeL2UpdatePublicPool` | 11 |
| `TxTypeL2Transfer` | 12 |
| `TxTypeL2Withdraw` | 13 |
| `TxTypeL2CreateOrder` | 14 |
| `TxTypeL2CancelOrder` | 15 |
| `TxTypeL2CancelAllOrders` | 16 |
| `TxTypeL2ModifyOrder` | 17 |
| `TxTypeL2MintShares` | 18 |
| `TxTypeL2BurnShares` | 19 |
| `TxTypeL2UpdateLeverage` | 20 |

### Transaction Status Mapping

| Status Code | Description |
|-------------|-------------|
| 0 | Failed |
| 1 | Pending |
| 2 | Executed |
| 3 | Pending - Final State |

### Error Codes

#### Transaction Errors (215xx)

| Code | Error | Description |
|------|-------|-------------|
| 21500 | `AppErrTxNotFound` | Transaction not found |
| 21501 | `AppErrInvalidTxInfo` | Invalid tx info |
| 21502 | `AppErrMarshalTxFailed` | Marshal tx failed |
| 21503 | `AppErrMarshalEventsFailed` | Marshal event failed |
| 21504 | `AppErrFailToL1Signature` | Fail to l1 signature |
| 21505 | `AppErrUnsupportedTxType` | Unsupported tx type |
| 21506 | `AppErrTooManyTxs` | Too many pending txs. Please try again later |
| 21507 | `AppErrAccountBelowMaintenanceMargin` | Account is below maintenance margin |
| 21508 | `AppErrAccountBelowInitialMargin` | Account is below initial margin |
| 21511 | `AppErrInvalidTxTypeForAccount` | Invalid tx type for account |
| 21512 | `AppErrInvalidL1RequestId` | Invalid l1 request id |

#### OrderBook Errors (216xx)

| Code | Error | Description |
|------|-------|-------------|
| 21600 | `AppErrInactiveCancel` | Given order is not an active limit order |
| 21601 | `AppErrOrderBookFull` | Order book is full |
| 21602 | `AppErrInvalidMarketIndex` | Invalid market index |
| 21603 | `AppErrInvalidMinAmountsForMarket` | Invalid min amounts for market |
| 21604 | `AppErrInvalidMarginFractionsForMarket` | Invalid margin fractions for market |
| 21605 | `AppErrInvalidMarketStatus` | Invalid market status |
| 21606 | `AppErrMarketAlreadyExist` | Market already exist for given index |
| 21607 | `AppErrInvalidMarketFees` | Invalid market fees |
| 21608 | `AppErrInvalidQuoteMultiplier` | Invalid quote multiplier |
| 21611 | `AppErrInvalidInterestRate` | Invalid interest rate |
| 21612 | `AppErrInvalidOpenInterest` | Invalid open interest |
| 21613 | `AppErrInvalidMarginMode` | Invalid margin mode |
| 21614 | `AppErrNoPositionFound` | No position found |

#### Order Errors (217xx)

| Code | Error | Description |
|------|-------|-------------|
| 21700 | `AppErrInvalidOrderIndex` | Invalid order index |
| 21701 | `AppErrInvalidBaseAmount` | Invalid base amount |
| 21702 | `AppErrInvalidPrice` | Invalid price |
| 21703 | `AppErrInvalidIsAsk` | Invalid isAsk |
| 21704 | `AppErrInvalidOrderType` | Invalid OrderType |
| 21705 | `AppErrInvalidOrderTimeInForce` | Invalid OrderTimeInForce |
| 21706 | `AppErrInvalidOrderAmount` | Invalid order base or quote amount |
| 21707 | `AppErrInvalidOrderOwner` | Account is not owner of the order |
| 21708 | `AppErrEmptyOrder` | Order is empty |
| 21709 | `AppErrInactiveOrder` | Order is inactive |
| 21710 | `AppErrUnsupportedOrderType` | Unsupported order type |
| 21711 | `AppErrInvalidOrderExpiry` | Invalid expiry |
| 21712 | `AppErrAccountHasAQueuedCancelAllOrdersRequest` | Account has a queued cancel all orders request |
| 21713 | `AppErrInvalidCancelAllTimeInForce` | Invalid cancel all time in force |
| 21714 | `AppErrInvalidCancelAllTime` | Invalid cancel all time |
| 21715 | `AppErrInctiveOrder` | Given order is not an active order |
| 21716 | `AppErrOrderNotExpired` | Order is not expired |
| 21717 | `AppErrMaxOrdersPerAccount` | Maximum active limit order count reached |
| 21718 | `AppErrMaxOrdersPerAccountPerMarket` | Maximum active limit order count per market reached |
| 21719 | `AppErrMaxPendingOrdersPerAccount` | Maximum pending order count reached |
| 21720 | `AppErrMaxPendingOrdersPerAccountPerMarket` | Maximum pending order count per market reached |
| 21721 | `AppErrMaxTWAPOrdersInExchange` | Maximum twap order count reached |
| 21722 | `AppErrMaxConditionalOrdersInExchange` | Maximum conditional order count reached |
| 21723 | `AppErrInvalidAccountHealth` | Invalid account health |
| 21724 | `AppErrInvalidLiquidationSize` | Invalid liquidation size |
| 21725 | `AppErrInvalidLiquidationPrice` | Invalid liquidation price |
| 21726 | `AppErrInsuranceFundCannotBePartiallyLiquidated` | Insurance fund cannot be partially liquidated |
| 21727 | `AppErrInvalidClientOrderIndex` | Invalid client order index |
| 21728 | `AppErrClientOrderIndexExists` | Client order index already exists |
| 21729 | `AppErrInvalidOrderTriggerPrice` | Invalid order trigger price |
| 21730 | `AppOrderStatusIsNotPending` | Order status is not pending |
| 21731 | `AppPendingOrderCanNotBeTriggered` | Order can not be triggered |
| 21732 | `AppReduceOnlyIncreasesPosition` | Reduce only increases position |
| 21733 | `AppErrFatFingerPrice` | Order price flagged as an accidental price |
| 21734 | `AppErrPriceTooFarFromMarkPrice` | Limit order price is too far from the mark price |
| 21735 | `AppErrPriceTooFarFromTrigger` | SL/TP order price is too far from the trigger price |
| 21736 | `AppErrInvalidOrderTriggerStatus` | Invalid order trigger status |
| 21737 | `AppErrInvalidOrderStatus` | Invalid order status |
| 21738 | `AppErrInvalidReduceOnlyDirection` | Invalid reduce only direction |
| 21739 | `AppErrNotEnoughOrderMargin` | Not enough margin to create the order |
| 21740 | `AppErrInvalidReduceOnlyMode` | Invalid reduce only mode |

#### Deleverage Errors (219xx)

| Code | Error | Description |
|------|-------|-------------|
| 21901 | `AppErrDeleverageAgainstItself` | Deleverage against itself |
| 21902 | `AppErrDeleverageDoesNotMatchLiquidationStatus` | Deleverage does not match liquidation status |
| 21903 | `AppErrDeleverageWithOpenOrders` | Deleverage with open orders |
| 21904 | `AppErrInvalidDeleverageSize` | Invalid deleverage size |
| 21905 | `AppErrInvalidDeleveragePrice` | Invalid deleverage price |
| 21906 | `AppErrInvalidDeleverageSide` | Invalid deleverage side |

#### Rate Limit Errors (23xxx)

| Code | Error | Description |
|------|-------|-------------|
| 23000 | `AppErrTooManyRequest` | Too Many Requests! |
| 23001 | `AppErrTooManySubscriptions` | Too Many Subscriptions! |
| 23002 | `AppErrTooManyDifferentAccounts` | Too Many Different Accounts! |
| 23003 | `AppErrTooManyConnections` | Too Many Connections! |

---

## Quick Reference Links

| Resource | URL |
|----------|-----|
| **API Documentation** | https://apidocs.lighter.xyz/docs/ |
| **API Reference** | https://apidocs.lighter.xyz/reference |
| **Python SDK** | https://github.com/elliottech/lighter-python |
| **Go SDK** | https://github.com/elliottech/lighter-go |
| **Mainnet URL** | https://mainnet.zklighter.elliot.ai |
| **Testnet URL** | https://testnet.zklighter.elliot.ai |
| **WebSocket (Mainnet)** | wss://mainnet.zklighter.elliot.ai/stream |
| **WebSocket (Testnet)** | wss://testnet.zklighter.elliot.ai/stream |
| **Explorer** | https://explorer.elliot.ai/ |
