# Lighter API Reference Documentation

> **Source:** [Lighter API Documentation](https://apidocs.lighter.xyz/reference)  
> **Version:** 1.0  
> **Base URL (Mainnet):** `https://mainnet.zklighter.elliot.ai`

## Table of Contents

- [Introduction](#introduction)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Root](#root)
  - [Account](#account)
  - [Order](#order)
  - [Transaction](#transaction)
  - [Announcement](#announcement)
  - [Block](#block)
  - [Candlestick](#candlestick)
  - [Bridge](#bridge)
  - [Funding](#funding)
  - [Notification](#notification)
  - [Referral](#referral)
  - [Info](#info)
- [Lighter Explorer API](#lighter-explorer-api)
- [Error Codes](#error-codes)

---

## Introduction

Lighter is a decentralized perpetual trading platform. This API reference provides comprehensive documentation for all available endpoints to interact with the Lighter protocol.

## Authentication

Some endpoints require authentication. Authentication can be provided in two ways:

### 1. HTTP Header Authentication
```
Authorization: [auth_token]
```

### 2. Query Parameter Authentication
```
?auth=[auth_token]
```

### API Tokens

You can create read-only API tokens using the `/api/v1/tokens` endpoint. Token format:
```
ro:{account_index}:{single|all}:{expiry_unix}:{random_hex}
```

**Example:** `ro:6:all:1767139200:a1b2c3d4e5f6...`

---

## API Endpoints

### Root

#### GET /
**Operation:** `status`  
**Description:** Get status of zklighter

**Response Example:**
```json
{
  "status": 1,
  "network_id": 1,
  "timestamp": 1717777777
}
```

#### GET /api/v1/info
**Operation:** `info`  
**Description:** Get general information about the zklighter protocol

---

### Account

#### GET /api/v1/account
**Operation:** `account`  
**Description:** Get account by account's index or L1 address

**Query Parameters:**
- `by` (required): `index` or `l1_address`
- `value` (required): Account index or L1 address

**Response Fields:**
- `account_type`: 1 for active, 0 for inactive
- `index`: Account index
- `l1_address`: Ethereum address
- `cancel_all_time`: Timestamp of last cancel all
- `total_order_count`: Total number of orders placed
- `total_isolated_order_count`: Total isolated orders
- `pending_order_count`: Number of pending orders
- `available_balance`: Available balance in USDC
- `status`: Account status (1 = active, 0 = inactive)
- `collateral`: Total collateral in the account
- `positions`: Array of position details

**Position Details:**
- `market_id`: Market identifier
- `symbol`: Trading pair symbol
- `initial_margin_fraction`: Initial margin requirement
- `open_order_count` (OOC): Open orders in market
- `sign`: 1 for Long, -1 for Short
- `position`: Position size
- `avg_entry_price`: Average entry price
- `position_value`: Current position value
- `unrealized_pnl`: Unrealized profit/loss
- `realized_pnl`: Realized profit/loss
- `liquidation_price`: Liquidation price
- `margin_mode`: Cross or Isolated margin
- `allocated_margin`: Allocated margin for isolated positions

**Reference:** [Account Index Documentation](https://apidocs.lighter.xyz/docs/account-index)

#### GET /api/v1/accountsByL1Address
**Operation:** `accountsByL1Address`  
**Description:** Get all accounts associated with an L1 address

**Query Parameters:**
- `l1_address` (required): Ethereum address

#### GET /api/v1/accountLimits
**Operation:** `accountLimits`  
**Description:** Get account limits

**Query Parameters:**
- `account_index` (required): Account index
- `auth` (optional): Authentication token

**Response:**
```json
{
  "code": 200,
  "max_llp_percentage": 25,
  "user_tier": "std",
  "can_create_public_pool": true
}
```

#### GET /api/v1/apikeys
**Operation:** `apikeys`  
**Description:** Get account API keys

**Query Parameters:**
- `account_index` (required): Account index
- `api_key_index` (optional): Specific API key index, or 255 for all keys

#### POST /api/v1/tokens
**Operation:** `createToken`  
**Description:** Create an API token for read-only access

**Request Body (multipart/form-data):**
- `name` (required): Token name (e.g., "My Trading Bot Token")
- `account_index` (required): Account index
- `expiry` (required): Unix timestamp for token expiration
- `sub_account_access` (required): Boolean - if true and created by master account, grants access to all sub-accounts
- `scopes` (optional): Token permission scopes (default: "read.*")

**Access Rules:**
- Token created by account → access that account
- Master account token with `sub_account_access=true` → access all sub-accounts
- Master account token with `sub_account_access=false` → only master account
- Sub-account token → only that sub-account

**Response:**
```json
{
  "code": 200,
  "api_token": "ro:6:all:1767139200:a1b2c3...",
  "token_id": 123
}
```

**Note:** The `api_token` is only shown once upon creation.

**WebSocket Usage:**
```json
{
  "type": "subscribe",
  "channel": "account:6:tx",
  "auth": "ro:6:all:1767139200:a1b2c3..."
}
```

#### GET /api/v1/tokens
**Operation:** `listTokens`  
**Description:** List all API tokens for the specified account

**Query Parameters:**
- `account_index` (required): Account index

#### POST /api/v1/tokens/revoke
**Operation:** `revokeToken`  
**Description:** Revoke an existing API token

**Request Body (multipart/form-data):**
- `token_id` (required): Token ID to revoke
- `account_index` (required): Account index

#### GET /api/v1/accountMetadata
**Operation:** `accountMetadata`  
**Description:** Get account metadata

**Query Parameters:**
- `by` (required): `index` or `l1_address`
- `value` (required): Account index or L1 address
- `auth` (optional): Authentication token

#### GET /api/v1/pnl
**Operation:** `pnl`  
**Description:** Get profit and loss information

#### GET /api/v1/l1Metadata
**Operation:** `l1Metadata`  
**Description:** Get Layer 1 metadata

#### POST /api/v1/changeAccountTier
**Operation:** `changeAccountTier`  
**Description:** Change account tier

#### GET /api/v1/liquidations
**Operation:** `liquidations`  
**Description:** Get liquidation events

#### GET /api/v1/positionFunding
**Operation:** `positionFunding`  
**Description:** Get position funding information

#### GET /api/v1/publicPoolsMetadata
**Operation:** `publicPoolsMetadata`  
**Description:** Get public pools metadata

---

### Order

#### GET /api/v1/accountActiveOrders
**Operation:** `accountActiveOrders`  
**Description:** Get account active orders

**Query Parameters:**
- `authorization` (header, optional): Authentication token
- `account_index` (required): Account index
- `market_id` (required): Market ID (uint8)
- `auth` (optional): Authentication token (alternative to header)

**Response:** Returns array of orders with status `in-progress`, `pending`, or `open`

**Order Fields:**
- `order_index`: Order index
- `client_order_index`: Client-specified order index
- `order_id`: Order ID (string)
- `client_order_id`: Client-specified order ID
- `market_index`: Market identifier
- `owner_account_index`: Account owning the order
- `initial_base_amount`: Initial base amount
- `price`: Order price
- `nonce`: Transaction nonce
- `remaining_base_amount`: Remaining unfilled amount
- `is_ask`: Boolean - true for sell, false for buy
- `filled_base_amount`: Filled base amount
- `filled_quote_amount`: Filled quote amount
- `side`: `buy` or `sell`
- `type`: Order type - `limit`, `market`, `stop-loss`, `stop-loss-limit`, `take-profit`, `take-profit-limit`, `twap`, `twap-sub`, `liquidation`
- `time_in_force`: `good-till-time`, `immediate-or-cancel`, `post-only`, `Unknown`
- `reduce_only`: Boolean
- `trigger_price`: Trigger price for conditional orders
- `order_expiry`: Unix timestamp
- `status`: Order status
- `trigger_status`: `na`, `ready`, `mark-price`, `twap`, `parent-order`
- `block_height`: Block height
- `timestamp`: Unix timestamp
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

**Order Status Values:**
- `in-progress`
- `pending`
- `open`
- `filled`
- `canceled`
- `canceled-post-only`
- `canceled-reduce-only`
- `canceled-position-not-allowed`
- `canceled-margin-not-allowed`
- `canceled-too-much-slippage`
- `canceled-not-enough-liquidity`
- `canceled-self-trade`
- `canceled-expired`
- `canceled-oco`
- `canceled-child`
- `canceled-liquidation`

#### GET /api/v1/accountInactiveOrders
**Operation:** `accountInactiveOrders`  
**Description:** Get account inactive orders

**Query Parameters:**
- `authorization` (header, optional): Authentication token
- `auth` (optional): Authentication token
- `account_index` (required): Account index
- `market_id` (optional): Market ID (default: 255 for all markets)
- `ask_filter` (optional): Filter by ask/bid (-1 for all, default: -1)
- `between_timestamps` (optional): Filter by timestamp range
- `cursor` (optional): Pagination cursor
- `limit` (required): Number of results (1-100)

#### GET /api/v1/export
**Operation:** `export`  
**Description:** Export order data

#### GET /api/v1/exchangeStats
**Operation:** `exchangeStats`  
**Description:** Get exchange statistics

#### GET /api/v1/orderBookDetails
**Operation:** `orderBookDetails`  
**Description:** Get order books metadata

**Endpoint:** `GET https://mainnet.zklighter.elliot.ai/api/v1/orderBookDetails`

#### GET /api/v1/orderBookOrders
**Operation:** `orderBookOrders`  
**Description:** Get orders in an order book

#### GET /api/v1/orderBooks
**Operation:** `orderBooks`  
**Description:** Get all order books

#### GET /api/v1/recentTrades
**Operation:** `recentTrades`  
**Description:** Get recent trades

#### GET /api/v1/trades
**Operation:** `trades`  
**Description:** Get trade history

---

### Transaction

#### GET /api/v1/blockTxs
**Operation:** `blockTxs`  
**Description:** Get transactions in a block

#### GET /api/v1/deposit_history
**Operation:** `deposit_history`  
**Description:** Get deposit history

#### GET /api/v1/nextNonce
**Operation:** `nextNonce`  
**Description:** Get next nonce for transactions

#### POST /api/v1/sendTx
**Operation:** `sendTx`  
**Description:** Send a transaction

#### POST /api/v1/sendTxBatch
**Operation:** `sendTxBatch`  
**Description:** Send multiple transactions in a batch

#### GET /api/v1/tx
**Operation:** `tx`  
**Description:** Get transaction by hash

**Transaction Fields:**
- `hash`: Transaction hash
- `type`: Transaction type (1-64)
- `info`: Transaction info JSON
- `event_info`: Event info JSON
- `status`: Transaction status (1 = success)
- `transaction_index`: Transaction index
- `l1_address`: Ethereum address
- `account_index`: Account index
- `nonce`: Transaction nonce
- `expire_at`: Expiration timestamp
- `block_height`: Block height
- `queued_at`: Queue timestamp
- `executed_at`: Execution timestamp
- `sequence_index`: Sequence index
- `parent_hash`: Parent transaction hash

#### GET /api/v1/transfer_history
**Operation:** `transfer_history`  
**Description:** Get transfer history

#### GET /api/v1/txFromL1TxHash
**Operation:** `txFromL1TxHash`  
**Description:** Get L2 transaction from L1 transaction hash

#### GET /api/v1/txs
**Operation:** `txs`  
**Description:** Get multiple transactions

**Query Parameters:**
- `by` (required): `account_index`
- `value` (required): Account index value
- `index` (optional): Starting index
- `limit` (required): Number of results (1-100)
- `types` (optional): Filter by transaction types (comma-separated uint8 values)
- `auth` (optional): Authentication token

#### GET /api/v1/withdraw_history
**Operation:** `withdraw_history`  
**Description:** Get withdrawal history

---

### Announcement

#### GET /api/v1/announcement
**Operation:** `announcement`  
**Description:** Get announcements

**Response:**
```json
{
  "code": 200,
  "announcements": [
    {
      "title": "Announcement title",
      "content": "Announcement content",
      "created_at": 1640995200
    }
  ]
}
```

---

### Block

#### GET /api/v1/block
**Operation:** `block`  
**Description:** Get block information

**Query Parameters:**
- `by` (required): Query method
- `value` (required): Query value

**Block Fields:**
- `commitment`: Block commitment
- `height`: Block height
- `state_root`: State root hash
- `priority_operations`: Number of priority operations
- `on_chain_l2_operations`: Number of L2 operations
- `pending_on_chain_operations_pub_data`: Pending operations public data
- `committed_tx_hash`: Commit transaction hash
- `committed_at`: Commit timestamp
- `verified_tx_hash`: Verification transaction hash
- `verified_at`: Verification timestamp
- `txs`: Array of transactions in block
- `status`: Block status
- `size`: Block size

#### GET /api/v1/blocks
**Operation:** `blocks`  
**Description:** Get multiple blocks

#### GET /api/v1/currentHeight
**Operation:** `currentHeight`  
**Description:** Get current block height

---

### Candlestick

#### GET /api/v1/candlesticks
**Operation:** `candlesticks`  
**Description:** Get candlestick/OHLCV data

#### GET /api/v1/fundings
**Operation:** `fundings`  
**Description:** Get funding rate data

---

### Bridge

#### GET /api/v1/fastbridge_info
**Operation:** `fastbridge_info`  
**Description:** Get fast bridge information

---

### Funding

#### GET /api/v1/funding-rates
**Operation:** `funding-rates`  
**Description:** Get funding rates

---

### Notification

#### POST /api/v1/notification_ack
**Operation:** `notification_ack`  
**Description:** Acknowledge notification

---

### Referral

#### GET /api/v1/referral_points
**Operation:** `referral_points`  
**Description:** Get referral points

---

### Info

#### GET /api/v1/transferFeeInfo
**Operation:** `transferFeeInfo`  
**Description:** Get transfer fee information

#### GET /api/v1/withdrawalDelay
**Operation:** `withdrawalDelay`  
**Description:** Get withdrawal delay information

---

## Lighter Explorer API

Additional endpoints for blockchain exploration:

### Account

#### GET /explorer/accounts/{param}/logs
**Operation:** `logs`  
**Description:** Get account logs

#### GET /explorer/accounts/{param}/positions
**Operation:** `positions`  
**Description:** Get account positions

### Batches

#### GET /explorer/batches
**Operation:** `batches`  
**Description:** Get batches

#### GET /explorer/batches/{batchId}
**Operation:** `batchId`  
**Description:** Get batch by ID

### Blocks

#### GET /explorer/blocks
**Operation:** `blocks`  
**Description:** Get blocks

#### GET /explorer/blocks/{blockId}
**Operation:** `blockId`  
**Description:** Get block by ID

### Logs

#### GET /explorer/logs/{hash}
**Operation:** `hash`  
**Description:** Get log by hash

### Markets

#### GET /explorer/markets
**Operation:** `markets`  
**Description:** Get markets

#### GET /explorer/markets/{symbol}/logs
**Operation:** `logs`  
**Description:** Get market logs

### Search

#### GET /explorer/search
**Operation:** `search`  
**Description:** Search explorer

### Stats

#### GET /explorer/stats/tx
**Operation:** `tx`  
**Description:** Get transaction statistics

---

## Error Codes

### Standard Response
All endpoints return a standard response structure:

```json
{
  "code": 200,
  "message": "Optional message"
}
```

### Common Error Codes:
- `200`: Success
- `400`: Bad request - Invalid parameters or malformed request

### Error Response Example:
```json
{
  "code": 400,
  "message": "Error description"
}
```

---

## Additional Resources

- **API Documentation:** https://apidocs.lighter.xyz/docs/
- **API Reference:** https://apidocs.lighter.xyz/reference
- **Account Index Guide:** https://apidocs.lighter.xyz/docs/account-index

---

## Notes

1. **Pagination:** Many list endpoints support pagination via `cursor` and `limit` parameters
2. **Timestamps:** All timestamps are Unix timestamps (seconds since epoch)
3. **Decimal Precision:** Financial values are returned as strings to preserve precision
4. **Rate Limiting:** API rate limits may apply (check with specific deployment)
5. **Base URL:** The mainnet base URL is `https://mainnet.zklighter.elliot.ai`

---

*Last Updated: December 2024*  
*API Version: 1.0*
