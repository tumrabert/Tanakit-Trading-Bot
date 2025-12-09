# Lighter Go SDK Documentation

> **Source:** [lighter-go Repository](https://github.com/elliottech/lighter-go)  
> **Version:** Based on local `lighter-go-sdk` analysis  
> **Last Updated:** December 9, 2025

This document provides comprehensive documentation for the Lighter Go SDK, the reference implementation for signing and hashing Lighter transactions.

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Client Management](#client-management)
4. [API Key Management](#api-key-management)
5. [Transaction Types & Request Structures](#transaction-types--request-structures)
6. [Order Operations](#order-operations)
7. [Leverage & Margin Operations](#leverage--margin-operations)
8. [Transfer & Withdrawal Operations](#transfer--withdrawal-operations)
9. [Sub-accounts & Public Pools](#sub-accounts--public-pools)
10. [Auth Tokens](#auth-tokens)
11. [Build Instructions](#build-instructions)

---

## Overview

The lighter-go SDK is the **reference implementation** for signing & hashing Lighter transactions. It provides:

- **Cross-platform shared libraries** compiled for multiple platforms
- **Core signing functionality** using Poseidon2 hashing and Schnorr signatures
- **HTTP client integration** for automatic nonce fetching and client validation
- **Thread-safe client management** supporting multiple API keys and accounts

### Platform Support

| Platform | Architecture | File Type |
|----------|-------------|-----------|
| **macOS (darwin)** | ARM64 (M processors) | `.dylib` |
| **Linux** | AMD64 (x86) | `.so` |
| **Linux** | ARM64 | `.so` |
| **Windows** | AMD64 | `.dll` |
| **WebAssembly** | WASM | `.wasm` |

### SDK vs Python SDK

| Feature | Go SDK | Python SDK |
|---------|--------|------------|
| Core signing | ✅ | ✅ (uses Go shared lib) |
| HTTP client | Basic | Full support |
| WebSocket | ❌ | ✅ |
| Examples | Limited | Extensive |
| API key generation | ✅ | ✅ |

The [Python SDK](https://github.com/elliottech/lighter-python) offers full HTTP and WebSocket functionality plus extensive examples.

---

## Installation

### Go Module

```bash
go get github.com/elliottech/lighter-go
```

### Dependencies

The SDK depends on:
- `github.com/elliottech/poseidon_crypto` - Poseidon2 hashing and Schnorr signatures
- `github.com/ethereum/go-ethereum` - Hex utilities

### Shared Library

Pre-built binaries follow the naming convention: `lighter_signer_{os}_{arch}`

Download from [GitHub Releases](https://github.com/elliottech/lighter-go/releases).

---

## Client Management

The SDK uses a thread-safe client registry for managing multiple API keys and accounts.

### CreateClient

Creates and registers a new `TxClient` for signing transactions.

```go
func CreateClient(
    httpClient MinimalHTTPClient,
    privateKey string,
    chainId uint32,
    apiKeyIndex uint8,
    accountIndex int64,
) (*TxClient, error)
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `httpClient` | `MinimalHTTPClient` | HTTP client for API calls |
| `privateKey` | `string` | API key private key (hex encoded) |
| `chainId` | `uint32` | Chain ID (mainnet/testnet) |
| `apiKeyIndex` | `uint8` | API key index (2-254) |
| `accountIndex` | `int64` | Account index (must be > 0) |

**Returns:** `*TxClient` - The created client, or error if creation fails.

**Note:** The most recently created client becomes the **default client**.

### CheckClient

Validates that the API key is correctly configured on the exchange.

```go
func (c *TxClient) Check() error
```

Verifies that the public key derived from the private key matches the one registered on Lighter.

### GetClient

Retrieves an existing client by API key and account index.

```go
func GetClient(apiKeyIndex uint8, accountIndex int64) (*TxClient, error)
```

**Special Cases:**
- `apiKeyIndex=255, accountIndex=-1` → Returns default client
- `apiKeyIndex=255, accountIndex=N` → Returns default client for account N

---

## API Key Management

### GenerateAPIKey

Generates a new API key pair from an optional seed.

```go
func GenerateAPIKey(seed string) (privateKey string, publicKey string, error)
```

**Parameters:**
- `seed` - Optional seed string (empty for random generation)

**Returns:** Hex-encoded private and public keys.

### GetAuthToken

Creates an authentication token for HTTP/WebSocket endpoints.

```go
func (c *TxClient) GetAuthToken(deadline time.Time) (string, error)
```

**Token Format:** `{unix_timestamp}:{account_index}:{api_key_index}:{signature}`

---

## Transaction Types & Request Structures

### TransactOpts

Common options for all transactions.

```go
type TransactOpts struct {
    FromAccountIndex *int64   // Account index (default: 0)
    ApiKeyIndex      *uint8   // API key index (default: 255)
    ExpiredAt        int64    // Transaction expiration timestamp
    Nonce            *int64   // Nonce (default: -1 for auto-fetch)
    DryRun           bool     // Dry run mode
}
```

### Default Parameter Values

| Parameter | Default | Description |
|-----------|---------|-------------|
| `nonce` | `-1` | Auto-fetch from server |
| `apiKeyIndex` | `255` | Use default client |
| `accountIndex` | `0` | Use default account |

> **Note:** For the default client, pass `-1, 255, 0` for nonce, apiKeyIndex, accountIndex.

### Order Request Types

#### CreateOrderTxReq

```go
type CreateOrderTxReq struct {
    MarketIndex      int16   // Market ID
    ClientOrderIndex int64   // Unique order identifier
    BaseAmount       int64   // Order size
    Price            uint32  // Order price
    IsAsk            uint8   // 1 = sell, 0 = buy
    Type             uint8   // Order type
    TimeInForce      uint8   // Time in force
    ReduceOnly       uint8   // Reduce only flag
    TriggerPrice     uint32  // Stop/take profit trigger
    OrderExpiry      int64   // Expiration timestamp
}
```

#### CreateGroupedOrdersTxReq

```go
type CreateGroupedOrdersTxReq struct {
    GroupingType uint8               // Grouping type
    Orders       []*CreateOrderTxReq // List of orders
}
```

#### CancelOrderTxReq

```go
type CancelOrderTxReq struct {
    MarketIndex int16 // Market ID
    Index       int64 // Order index to cancel
}
```

#### ModifyOrderTxReq

```go
type ModifyOrderTxReq struct {
    MarketIndex  int16  // Market ID
    Index        int64  // Order index to modify
    BaseAmount   int64  // New order size
    Price        uint32 // New price
    TriggerPrice uint32 // New trigger price
}
```

#### CancelAllOrdersTxReq

```go
type CancelAllOrdersTxReq struct {
    TimeInForce uint8 // Determines cancel type
    Time        int64 // Scheduled time (for scheduled cancel)
}
```

### Transfer & Withdrawal Request Types

#### TransferTxReq

```go
type TransferTxReq struct {
    ToAccountIndex int64    // Destination account
    AssetIndex     int16    // Asset to transfer
    FromRouteType  uint8    // Source route type
    ToRouteType    uint8    // Destination route type
    Amount         int64    // Transfer amount
    USDCFee        int64    // USDC fee
    Memo           [32]byte // Transfer memo
}
```

#### WithdrawTxReq

```go
type WithdrawTxReq struct {
    AssetIndex int16  // Asset to withdraw
    RouteType  uint8  // Withdrawal route
    Amount     uint64 // Withdrawal amount
}
```

### Leverage & Margin Request Types

#### UpdateLeverageTxReq

```go
type UpdateLeverageTxReq struct {
    MarketIndex           int16  // Market ID
    InitialMarginFraction uint16 // New leverage setting
    MarginMode            uint8  // Cross/isolated mode
}
```

#### UpdateMarginTxReq

```go
type UpdateMarginTxReq struct {
    MarketIndex int16 // Market ID
    USDCAmount  int64 // Margin amount
    Direction   uint8 // Add/remove direction
}
```

### Pool Request Types

#### CreatePublicPoolTxReq

```go
type CreatePublicPoolTxReq struct {
    OperatorFee          int64  // Operator fee
    InitialTotalShares   int64  // Initial shares
    MinOperatorShareRate uint16 // Minimum operator share rate
}
```

#### UpdatePublicPoolTxReq

```go
type UpdatePublicPoolTxReq struct {
    PublicPoolIndex      int64  // Pool index
    Status               uint8  // Pool status
    OperatorFee          int64  // New operator fee
    MinOperatorShareRate uint16 // New min operator share rate
}
```

#### MintSharesTxReq / BurnSharesTxReq

```go
type MintSharesTxReq struct {
    PublicPoolIndex int64 // Pool index
    ShareAmount     int64 // Shares to mint
}

type BurnSharesTxReq struct {
    PublicPoolIndex int64 // Pool index
    ShareAmount     int64 // Shares to burn
}
```

---

## Order Operations

All order methods return signed transaction info ready for submission.

### GetCreateOrderTransaction

```go
func (c *TxClient) GetCreateOrderTransaction(
    tx *types.CreateOrderTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2CreateOrderTxInfo, error)
```

### GetCreateGroupedOrdersTransaction

Create multiple orders in a single transaction.

```go
func (c *TxClient) GetCreateGroupedOrdersTransaction(
    tx *types.CreateGroupedOrdersTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2CreateGroupedOrdersTxInfo, error)
```

### GetCancelOrderTransaction

```go
func (c *TxClient) GetCancelOrderTransaction(
    tx *types.CancelOrderTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2CancelOrderTxInfo, error)
```

### GetCancelAllOrdersTransaction

```go
func (c *TxClient) GetCancelAllOrdersTransaction(
    tx *types.CancelAllOrdersTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2CancelAllOrdersTxInfo, error)
```

### GetModifyOrderTransaction

```go
func (c *TxClient) GetModifyOrderTransaction(
    tx *types.ModifyOrderTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2ModifyOrderTxInfo, error)
```

---

## Leverage & Margin Operations

### GetUpdateLeverageTransaction

```go
func (c *TxClient) GetUpdateLeverageTransaction(
    tx *types.UpdateLeverageTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2UpdateLeverageTxInfo, error)
```

### GetUpdateMarginTransaction

```go
func (c *TxClient) GetUpdateMarginTransaction(
    tx *types.UpdateMarginTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2UpdateMarginTxInfo, error)
```

---

## Transfer & Withdrawal Operations

### GetTransferTransaction

```go
func (c *TxClient) GetTransferTransaction(
    tx *types.TransferTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2TransferTxInfo, error)
```

### GetWithdrawTransaction

```go
func (c *TxClient) GetWithdrawTransaction(
    tx *types.WithdrawTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2WithdrawTxInfo, error)
```

---

## Sub-accounts & Public Pools

### GetCreateSubAccountTransaction

```go
func (c *TxClient) GetCreateSubAccountTransaction(
    ops *types.TransactOpts,
) (*txtypes.L2CreateSubAccountTxInfo, error)
```

### GetCreatePublicPoolTransaction

```go
func (c *TxClient) GetCreatePublicPoolTransaction(
    tx *types.CreatePublicPoolTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2CreatePublicPoolTxInfo, error)
```

### GetUpdatePublicPoolTransaction

```go
func (c *TxClient) GetUpdatePublicPoolTransaction(
    tx *types.UpdatePublicPoolTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2UpdatePublicPoolTxInfo, error)
```

### GetMintSharesTransaction

```go
func (c *TxClient) GetMintSharesTransaction(
    tx *types.MintSharesTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2MintSharesTxInfo, error)
```

### GetBurnSharesTransaction

```go
func (c *TxClient) GetBurnSharesTransaction(
    tx *types.BurnSharesTxReq,
    ops *types.TransactOpts,
) (*txtypes.L2BurnSharesTxInfo, error)
```

### GetChangePubKeyTransaction

```go
func (c *TxClient) GetChangePubKeyTransaction(
    tx *types.ChangePubKeyReq,
    ops *types.TransactOpts,
) (*txtypes.L2ChangePubKeyTxInfo, error)
```

---

## Auth Tokens

Auth tokens are used for HTTP & WebSocket endpoints that require authentication.

### Token Properties

| Property | Value |
|----------|-------|
| **Validity** | 8 hours maximum |
| **Bound to** | Specific API key |

### Creating Auth Tokens

```go
token, err := client.GetAuthToken(deadline)
```

- `CreateAuthToken(deadline=0)` → Token valid for 7 hours from now
- If deadline is 20 hours in future → Token starts being valid in 12 hours (max 8-hour window)

### Pre-generation Strategy

You can generate tokens ahead of time and use them accordingly. The token will only start being valid once it falls within the 8-hour window from the deadline.

```go
// Generate token for 7 hours from now
token, err := client.GetAuthToken(time.Now().Add(7 * time.Hour))
```

> **Warning:** Changing the API key **invalidates all generated auth tokens** for that key.

---

## Build Instructions

### Library Naming Convention

All shared libraries follow: `lighter_signer_{os}_{arch}`

| OS | Arch | Filename |
|----|------|----------|
| darwin | arm64 | `lighter-signer-darwin-arm64.dylib` |
| linux | amd64 | `lighter-signer-linux-amd64.so` |
| linux | arm64 | `lighter-signer-linux-arm64.so` |
| windows | amd64 | `lighter-signer-windows-amd64.dll` |

### Local Builds

#### macOS (ARM64 / M processors)

```bash
go mod vendor
go build -buildmode=c-shared -trimpath -o ./build/lighter-signer-darwin-arm64.dylib ./sharedlib/main.go
```

#### Linux (local architecture)

```bash
go mod vendor
CGO_ENABLED=1 go build -buildmode=c-shared -trimpath -o ./build/lighter-signer-linux.so ./sharedlib/main.go
```

#### Windows (requires MSYS2)

```powershell
# PowerShell
$env:Path='C:\msys64\mingw64\bin;'+$env:Path
$env:CGO_ENABLED='1'
go mod vendor
go build -buildmode=c-shared -trimpath -o ./build/lighter-signer-windows.dll ./sharedlib/main.go
```

### Docker Builds (Cross-compilation)

#### Linux AMD64

```bash
go mod vendor
docker run --rm --platform linux/amd64 -v ${PWD}:/go/src/sdk -w /go/src/sdk golang:1.23.2-bullseye /bin/sh -c " \
  CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build -buildmode=c-shared -trimpath -o ./build/lighter-signer-linux-amd64.so ./sharedlib"
```

#### Linux ARM64

```bash
go mod vendor
docker run --rm --platform linux/arm64 -v ${PWD}:/go/src/sdk -w /go/src/sdk golang:1.23.2-bullseye /bin/sh -c " \
  CGO_ENABLED=1 GOOS=linux GOARCH=arm64 go build -buildmode=c-shared -trimpath -o ./build/lighter-signer-linux-arm64.so ./sharedlib"
```

#### Windows AMD64

```bash
go mod vendor
docker run --rm --platform linux/amd64 -v ${PWD}:/go/src/sdk -w /go/src/sdk golang:1.23.2-bullseye bash -c " \
  apt-get update && \
  apt-get install -y gcc-mingw-w64-x86-64 && \
  CGO_ENABLED=1 GOOS=windows GOARCH=amd64 CC=x86_64-w64-mingw32-gcc go build -buildmode=c-shared -trimpath -o ./build/lighter-signer-windows-amd64.dll ./sharedlib"
```

### WASM Build

```bash
go mod vendor
GOOS=js GOARCH=wasm go build -trimpath -o ./build/lighter-signer.wasm ./wasm/
```

---

## Quick Reference

### Complete Method List

| Category | Methods |
|----------|---------|
| **Client** | `CreateClient`, `CheckClient`, `GetClient` |
| **API Key** | `GenerateAPIKey`, `GetAuthToken`, `GetChangePubKeyTransaction` |
| **Orders** | `GetCreateOrderTransaction`, `GetCreateGroupedOrdersTransaction`, `GetCancelOrderTransaction`, `GetCancelAllOrdersTransaction`, `GetModifyOrderTransaction` |
| **Leverage/Margin** | `GetUpdateLeverageTransaction`, `GetUpdateMarginTransaction` |
| **Transfers** | `GetTransferTransaction`, `GetWithdrawTransaction` |
| **Pools** | `GetCreatePublicPoolTransaction`, `GetUpdatePublicPoolTransaction`, `GetMintSharesTransaction`, `GetBurnSharesTransaction` |
| **Account** | `GetCreateSubAccountTransaction` |

### Quick Links

| Resource | URL |
|----------|-----|
| **Go SDK** | https://github.com/elliottech/lighter-go |
| **Python SDK** | https://github.com/elliottech/lighter-python |
| **Releases** | https://github.com/elliottech/lighter-go/releases |
| **Examples (Python)** | https://github.com/elliottech/lighter-python/tree/main/examples |
