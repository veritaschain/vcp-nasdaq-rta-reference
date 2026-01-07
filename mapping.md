# OUCH/ITCH → VCP Field Mapping Reference
## Nasdaq OUCH 5.0 / ITCH 5.0 Integration Guide

---

## Overview

This document defines the mapping between Nasdaq OUCH 5.0 (Order Entry) and ITCH 5.0 (Market Data) protocol fields to VCP v1.1 event fields. The mapping ensures complete audit trail capture for high-frequency trading workflows.

---

## OUCH 5.0 Message Types

### Message Type Identifier

| OUCH Type | Name | VCP EventType | Direction |
|-----------|------|---------------|-----------|
| O | Enter Order | ORD | Outbound |
| U | Replace Order | MOD | Outbound |
| X | Cancel Order | CXL | Outbound |
| A | Order Accepted | ACK | Inbound |
| U | Order Replaced | MOD | Inbound |
| C | Order Canceled | CXL | Inbound |
| E | Order Executed | EXE | Inbound |
| C | Order Executed w/Price | EXE | Inbound |
| J | Order Rejected | REJ | Inbound |
| S | System Event | SYS | Inbound |
| B | Broken Trade | TRD_BRK | Inbound |

---

## OUCH 5.0 Enter Order Message (O) Mapping

### Message Structure

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'O' = Enter Order |
| 1 | 14 | Order Token | Trade.ClOrdID | Day-unique identifier |
| 15 | 1 | Buy/Sell Indicator | Trade.Side | 'B'/'S' |
| 16 | 4 | Shares | Trade.Volume | Unsigned integer |
| 20 | 8 | Stock | Trade.Symbol | Left-padded, space-filled |
| 28 | 4 | Price | Trade.Price | Price (4) format |
| 32 | 4 | Time in Force | Trade.TimeInForce | See TIF codes |
| 36 | 4 | Firm | Governance.FirmID | MPID |
| 40 | 1 | Display | Trade.DisplayType | Order visibility |
| 41 | 1 | Capacity | Trade.Capacity | 'A'/'P'/'R' |
| 42 | 1 | Intermarket Sweep | Trade.ISO | 'Y'/'N' |
| 43 | 4 | Minimum Quantity | Trade.MinQty | For MinQty orders |
| 47 | 1 | Cross Type | Trade.CrossType | Auction type |
| 48 | 1 | Customer Type | Trade.CustomerType | Retail indicator |

### Side Mapping

| OUCH Value | Meaning | VCP Value |
|------------|---------|-----------|
| B | Buy | BUY |
| S | Sell | SELL |
| T | Sell Short | SELL_SHORT |
| E | Sell Short Exempt | SELL_SHORT_EXEMPT |

### Time in Force Mapping

| OUCH Value | Meaning | VCP Value |
|------------|---------|-----------|
| 0 | Immediate or Cancel | IOC |
| 99998 | Market Hours Day | DAY |
| 99999 | System Hours | SYS_HOURS |
| 99960 | Good Till Cancel | GTC |

### Display Type Mapping

| OUCH Value | Meaning | VCP Value |
|------------|---------|-----------|
| Y | Displayed | DISPLAYED |
| N | Non-Displayed | HIDDEN |
| P | Post Only | POST_ONLY |
| I | Imbalance Only | IMBALANCE_ONLY |
| M | Midpoint Peg | MIDPOINT_PEG |

### Capacity Mapping

| OUCH Value | Meaning | VCP Value |
|------------|---------|-----------|
| A | Agency | AGENCY |
| P | Principal | PRINCIPAL |
| R | Riskless Principal | RISKLESS |

---

## OUCH 5.0 Order Accepted Message (A) Mapping

### Message Structure

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'A' = Accepted |
| 1 | 8 | Timestamp | Header.TimestampInt | Nanoseconds since midnight |
| 9 | 14 | Order Token | Trade.ClOrdID | Echoed from Enter Order |
| 23 | 1 | Buy/Sell Indicator | Trade.Side | 'B'/'S' |
| 24 | 4 | Shares | Trade.Volume | Accepted quantity |
| 28 | 8 | Stock | Trade.Symbol | |
| 36 | 4 | Price | Trade.Price | Accepted price |
| 40 | 4 | Time in Force | Trade.TimeInForce | Accepted TIF |
| 44 | 4 | Firm | Governance.FirmID | |
| 48 | 1 | Display | Trade.DisplayType | |
| 49 | 8 | Order Reference Number | Trade.BrokerOrderID | Nasdaq-assigned |
| 57 | 1 | Capacity | Trade.Capacity | |
| 58 | 1 | Intermarket Sweep | Trade.ISO | |
| 59 | 4 | Minimum Quantity | Trade.MinQty | |
| 63 | 1 | Cross Type | Trade.CrossType | |
| 64 | 1 | Order State | Trade.OrderStatus | 'L' = Live |
| 65 | 8 | BBO Weight Indicator | Trade.BBOWeight | |

---

## OUCH 5.0 Order Executed Message (E) Mapping

### Message Structure

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'E' = Executed |
| 1 | 8 | Timestamp | Header.TimestampInt | Nanoseconds |
| 9 | 14 | Order Token | Trade.ClOrdID | |
| 23 | 4 | Executed Shares | Trade.FillQty | |
| 27 | 4 | Execution Price | Trade.FillPrice | |
| 31 | 1 | Liquidity Flag | Trade.LiquidityFlag | 'A'/'R'/'O' |
| 32 | 8 | Match Number | Trade.MatchID | Day-unique |

### Liquidity Flag Mapping

| OUCH Value | Meaning | VCP Value |
|------------|---------|-----------|
| A | Added Liquidity | MAKER |
| R | Removed Liquidity | TAKER |
| O | Opening Cross | AUCTION_OPEN |
| C | Closing Cross | AUCTION_CLOSE |
| H | Halt/IPO Cross | AUCTION_HALT |
| I | Supplemental Order | SUPPLEMENTAL |

---

## OUCH 5.0 Order Canceled Message (C) Mapping

### Message Structure

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'C' = Canceled |
| 1 | 8 | Timestamp | Header.TimestampInt | |
| 9 | 14 | Order Token | Trade.ClOrdID | |
| 23 | 4 | Decrement Shares | Trade.CancelQty | |
| 27 | 1 | Reason | Trade.CancelReason | See reason codes |

### Cancel Reason Mapping

| OUCH Value | Meaning | VCP CancelReason |
|------------|---------|------------------|
| U | User Requested | USER_CANCEL |
| I | Immediate or Cancel | IOC_CANCEL |
| T | Timeout | TIMEOUT |
| S | Supervisory | SUPERVISORY |
| D | Regulatory Restriction | REGULATORY |
| Q | Self-Match Prevention | SMP_CANCEL |
| Z | System Cancel | SYSTEM_CANCEL |
| E | Cross Cancelled | CROSS_CANCEL |
| K | Repriced (Self-Help) | SELF_HELP |
| H | Halted | HALTED |
| X | Exchange Close | MARKET_CLOSE |

---

## OUCH 5.0 Order Rejected Message (J) Mapping

### Message Structure

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'J' = Rejected |
| 1 | 8 | Timestamp | Header.TimestampInt | |
| 9 | 14 | Order Token | Trade.ClOrdID | |
| 23 | 1 | Reason | Trade.RejectionCode | See codes |

### Reject Reason Mapping

| OUCH Value | Meaning | VCP RejectionCode |
|------------|---------|-------------------|
| T | Test Mode | TEST_MODE |
| H | Halted | HALTED |
| Z | Shares Exceeds Configured Safety | SIZE_LIMIT |
| Y | Invalid Stock | INVALID_SYMBOL |
| K | Invalid Display Type | INVALID_DISPLAY |
| X | Invalid Max Floor | INVALID_FLOOR |
| N | Invalid Peg Type | INVALID_PEG |
| M | Invalid Firm | INVALID_FIRM |
| O | Outside Permitted Times | OUTSIDE_HOURS |
| C | Cross Already In Progress | CROSS_CONFLICT |
| W | Wash Trade | WASH_TRADE |
| L | Locate Required | LOCATE_REQUIRED |
| F | Fat Finger | FAT_FINGER |
| R | Reg NMS Violation | REG_NMS |

---

## OUCH 5.0 Replace Order Message (U) Mapping

### Outbound (Request)

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'U' = Replace |
| 1 | 14 | Existing Token | Trade.OriginalClOrdID | |
| 15 | 14 | Replacement Token | Trade.ClOrdID | New token |
| 29 | 4 | Shares | Trade.NewVolume | |
| 33 | 4 | Price | Trade.NewPrice | |
| 37 | 4 | Time in Force | Trade.NewTIF | |
| 41 | 1 | Display | Trade.NewDisplayType | |
| 42 | 1 | Intermarket Sweep | Trade.NewISO | |
| 43 | 4 | Minimum Quantity | Trade.NewMinQty | |

---

## ITCH 5.0 Message Types

### Message Type Identifier

| ITCH Type | Name | VCP EventType | Notes |
|-----------|------|---------------|-------|
| S | System Event | SYS | Market state |
| R | Stock Directory | REF | Reference data |
| H | Stock Trading Action | STA | Halt/Resume |
| Y | Reg SHO Restriction | REG | Short sale |
| L | Market Participant Position | MPP | MPID registration |
| A | Add Order (No MPID) | MKT | Book update |
| F | Add Order (MPID) | MKT | Attributed order |
| E | Order Executed | MKT | Book execution |
| C | Order Executed w/Price | MKT | Price execution |
| X | Order Cancel | MKT | Partial cancel |
| D | Order Delete | MKT | Full removal |
| U | Order Replace | MKT | Price/Size change |
| P | Trade (Non-Cross) | TRD | Normal trade |
| Q | Cross Trade | TRD | Auction trade |
| B | Broken Trade | TRD_BRK | Trade break |

---

## ITCH 5.0 Add Order Message (A/F) Mapping

### Message Structure

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'A' or 'F' |
| 1 | 2 | Stock Locate | Trade.LocateCode | |
| 3 | 2 | Tracking Number | (internal) | |
| 5 | 6 | Timestamp | Header.TimestampInt | Nanoseconds |
| 11 | 8 | Order Reference Number | Trade.OrderRefNum | |
| 19 | 1 | Buy/Sell Indicator | Trade.Side | 'B'/'S' |
| 20 | 4 | Shares | Trade.Volume | |
| 24 | 8 | Stock | Trade.Symbol | |
| 32 | 4 | Price | Trade.Price | Price (4) |
| 36 | 4 | MPID | Trade.MPID | 'F' message only |

---

## ITCH 5.0 Order Executed Message (E) Mapping

### Message Structure

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'E' |
| 1 | 2 | Stock Locate | Trade.LocateCode | |
| 3 | 2 | Tracking Number | (internal) | |
| 5 | 6 | Timestamp | Header.TimestampInt | |
| 11 | 8 | Order Reference Number | Trade.OrderRefNum | |
| 19 | 4 | Executed Shares | Trade.FillQty | |
| 23 | 8 | Match Number | Trade.MatchID | |

---

## ITCH 5.0 Trade Message (P) Mapping

### Message Structure

| Offset | Length | Field | VCP Field | Notes |
|--------|--------|-------|-----------|-------|
| 0 | 1 | Message Type | (derived) | 'P' |
| 1 | 2 | Stock Locate | Trade.LocateCode | |
| 3 | 2 | Tracking Number | (internal) | |
| 5 | 6 | Timestamp | Header.TimestampInt | |
| 11 | 8 | Order Reference Number | Trade.OrderRefNum | |
| 19 | 1 | Buy/Sell Indicator | Trade.Side | Always 'B' |
| 20 | 4 | Shares | Trade.Volume | |
| 24 | 8 | Stock | Trade.Symbol | |
| 32 | 4 | Price | Trade.Price | |
| 36 | 8 | Match Number | Trade.MatchID | |

---

## VCP Event Structure Example

### OUCH Enter Order → VCP ORD Event

**OUCH Binary Message (hex)**:
```
4F                                    # Message Type: 'O' (Enter Order)
41 41 50 4C 30 30 30 30 30 30 30 30 31 20   # Order Token: "AAPL00000001  "
42                                    # Buy/Sell: 'B' (Buy)
00 00 00 64                           # Shares: 100
41 41 50 4C 20 20 20 20               # Stock: "AAPL    "
00 1C 6D 20                           # Price: 185.5000 (1855000)
00 01 86 9E                           # TIF: 99998 (Market Day)
48 46 54 31                           # Firm: "HFT1"
59                                    # Display: 'Y' (Displayed)
50                                    # Capacity: 'P' (Principal)
4E                                    # ISO: 'N' (No)
00 00 00 00                           # MinQty: 0
4F                                    # Cross Type: 'O' (None)
4E                                    # Customer Type: 'N' (Non-Retail)
```

**VCP Event (JSON)**:
```json
{
  "Header": {
    "Version": "1.1",
    "EventID": "01943af3-21fc-796e-96cb-c02b045bb6e9",
    "EventType": "ORD",
    "TimestampISO": "2025-01-06T09:30:00.000000123Z",
    "TimestampInt": 1736155800000000123,
    "HashAlgo": "SHA256",
    "SignAlgo": "ED25519",
    "ClockSyncStatus": "PTP_SYNC",
    "TimestampPrecision": "NANOSECOND",
    "PrevHash": "...",
    "EventHash": "..."
  },
  "Trade": {
    "Symbol": "AAPL",
    "ClOrdID": "AAPL00000001",
    "Side": "BUY",
    "Volume": 100.0,
    "Price": 185.5,
    "TimeInForce": "DAY",
    "DisplayType": "DISPLAYED",
    "Capacity": "PRINCIPAL",
    "ISO": false
  },
  "Governance": {
    "AlgorithmName": "NASDAQ_HFT_SUITE",
    "AlgorithmVersion": "3.0.0",
    "DecisionReason": "OUCH Enter Order submitted",
    "OUCHCorrelation": {
      "MsgType": "O",
      "OrderToken": "AAPL00000001",
      "Direction": "OUTBOUND"
    },
    "FirmID": "HFT1",
    "Latency_ns": 18500
  },
  "PolicyIdentification": {
    "Version": "1.1",
    "PolicyID": "org.veritaschain:vcp-nasdaq-production-v1",
    "ConformanceTier": "PLATINUM",
    "RegistrationPolicy": {
      "Issuer": "VeritasChain Nasdaq Production Issuer",
      "PolicyURI": "https://veritaschain.org/policies/nasdaq-production-v1",
      "EffectiveDate": 1736121600000000
    },
    "VerificationDepth": {
      "HashChainValidation": true,
      "MerkleProofRequired": true,
      "ExternalAnchorRequired": true,
      "SignatureVerificationRequired": true
    }
  }
}
```

---

## Price Field Conversion

OUCH/ITCH prices are stored as 32-bit unsigned integers with implied 4 decimal places:

```python
def decode_price(raw_price: int) -> float:
    """Convert OUCH/ITCH price (4 decimal places) to float"""
    return raw_price / 10000.0

def encode_price(price: float) -> int:
    """Convert float to OUCH/ITCH price format"""
    return int(price * 10000)

# Examples:
# 185.5000 → 1855000
# 378.2500 → 3782500
# 0.0001   → 1
```

---

## Timestamp Conversion

ITCH timestamps are nanoseconds since midnight UTC:

```python
from datetime import datetime, timezone

def itch_timestamp_to_iso(ns_since_midnight: int, trade_date: str) -> str:
    """Convert ITCH nanosecond timestamp to ISO 8601"""
    base_date = datetime.strptime(trade_date, "%Y-%m-%d")
    base_date = base_date.replace(tzinfo=timezone.utc)
    
    total_ns = ns_since_midnight
    seconds = total_ns // 1_000_000_000
    nano_remainder = total_ns % 1_000_000_000
    
    timestamp = base_date + timedelta(seconds=seconds)
    # Format with nanosecond precision
    return f"{timestamp.isoformat()[:-6]}.{nano_remainder:09d}Z"

# Example:
# 34200000000000 (9:30:00.000000000 AM) → "2025-01-06T09:30:00.000000000Z"
```

---

## Stock Locate Code Management

ITCH uses locate codes as efficient stock identifiers:

```python
# Stock Directory builds the locate map
locate_map = {}

def process_stock_directory(msg):
    """Process ITCH Stock Directory message (R)"""
    locate_code = struct.unpack('>H', msg[1:3])[0]
    stock = msg[11:19].decode('ascii').strip()
    locate_map[locate_code] = stock

def get_symbol(locate_code: int) -> str:
    """Get stock symbol from locate code"""
    return locate_map.get(locate_code, f"LOCATE_{locate_code}")

# Common locate codes (day-specific):
# AAPL → 4135
# MSFT → 5234
# GOOGL → 3721
```

---

## Order Reference Number Tracking

ITCH uses 8-byte order reference numbers for order lifecycle:

```python
# Order book tracks active orders
order_book = {}

def process_add_order(msg):
    """Track order addition"""
    order_ref = struct.unpack('>Q', msg[11:19])[0]
    order_book[order_ref] = {
        'symbol': get_symbol(struct.unpack('>H', msg[1:3])[0]),
        'side': 'BUY' if msg[19:20] == b'B' else 'SELL',
        'shares': struct.unpack('>I', msg[20:24])[0],
        'price': struct.unpack('>I', msg[32:36])[0] / 10000.0
    }

def process_order_executed(msg):
    """Track partial execution"""
    order_ref = struct.unpack('>Q', msg[11:19])[0]
    exec_shares = struct.unpack('>I', msg[19:23])[0]
    
    if order_ref in order_book:
        order_book[order_ref]['shares'] -= exec_shares
        if order_book[order_ref]['shares'] <= 0:
            del order_book[order_ref]
```

---

## Regulatory Field Requirements

### SEC Rule 17a-4 / CAT Compliance Fields

| Requirement | OUCH/ITCH Source | VCP Field |
|-------------|------------------|-----------|
| Order ID | Order Token (OUCH) | Trade.ClOrdID |
| Symbol | Stock field | Trade.Symbol |
| Side | Buy/Sell Indicator | Trade.Side |
| Quantity | Shares field | Trade.Volume |
| Price | Price field | Trade.Price |
| Timestamp | ITCH ns timestamp | Header.TimestampISO |
| Execution Venue | (implicit Nasdaq) | Trade.ExecutionVenue |
| Fill Details | Executed fields | Trade.FillPrice/FillQty |
| Firm ID | Firm / MPID | Governance.FirmID |
| Capacity | Capacity field | Trade.Capacity |

### CAT Reporting Fields

| CAT Requirement | VCP Field | Source |
|-----------------|-----------|--------|
| CAT Order ID | Trade.CATOrderID | Generated |
| Firm ROE ID | Trade.ROEID | Firm configuration |
| Session ID | Trade.SessionID | OUCH session |
| Sequence Number | Governance.SeqNum | Message sequence |
| Manual Order Indicator | Trade.ManualOrder | Order source |

---

## Implementation Notes

### Binary Parsing Best Practices

1. **Zero-Copy Design**: Parse directly from network buffer
2. **Endianness**: All OUCH/ITCH integers are big-endian
3. **Alignment**: Messages are not aligned; use packed structs
4. **Validation**: Verify message types before parsing

### Timestamp Handling

1. **ITCH**: Nanoseconds since midnight UTC
2. **OUCH Accepted**: Same nanosecond format
3. **VCP Platinum**: Requires nanosecond precision
4. **PTP Sync**: IEEE 1588 for clock accuracy

### Order Correlation

```
OUCH Order Token Pattern: {SYMBOL}{YYYYMMDD}{NNNNNN}
Example: AAPL20250106000001

VCP stores:
- Trade.ClOrdID: Order Token
- Trade.BrokerOrderID: Order Reference Number (from Accepted)
- Trade.MatchID: Match Number (from Executed)
```

---

## Message Flow Examples

### Normal Order Lifecycle

```
1. [OUT] Enter Order (O)     → ORD event
2. [IN]  Order Accepted (A)  → ACK event
3. [IN]  Order Executed (E)  → EXE event (if filled)
```

### Replace Order Flow

```
1. [OUT] Replace Order (U)           → MOD event (request)
2. [IN]  Order Replaced (U)          → MOD event (confirm)
3. [IN]  Previous Order Canceled (C) → CXL event (auto)
```

### Cancel Order Flow

```
1. [OUT] Cancel Order (X)    → CXL event (request)
2. [IN]  Order Canceled (C)  → CXL event (confirm)
```

### Rejection Flow

```
1. [OUT] Enter Order (O)     → ORD event
2. [IN]  Order Rejected (J)  → REJ event
```

---

*Document Version: 1.0 | VCP v1.1 | Nasdaq OUCH 5.0 / ITCH 5.0*
*Generated by VeritasChain Standards Organization*
