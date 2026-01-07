#!/usr/bin/env python3
"""
VCP v1.1 Nasdaq OUCH/ITCH Evidence Pack - Usage Examples
=========================================================

This script demonstrates how to work with the VCP evidence pack
for Nasdaq OUCH/ITCH protocols.

Usage:
    python example_usage.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def load_events():
    """Load and display VCP events."""
    print("=" * 60)
    print("Loading VCP Events")
    print("=" * 60)
    
    with open("events.json", "r") as f:
        data = json.load(f)
    
    metadata = data.get("metadata", {})
    print(f"VCP Version: {metadata.get('specification', 'N/A')}")
    print(f"Tier: {metadata.get('conformance_tier', 'N/A')}")
    print(f"Protocol: {metadata.get('protocol', 'N/A')}")
    print(f"Total Events: {metadata.get('total_events', 'N/A')}")
    print()
    
    events = data.get("events", [])
    print(f"Events Loaded: {len(events)}")
    print()
    
    # Group by event type (from Header.EventType)
    by_type = {}
    for e in events:
        header = e.get("Header", {})
        t = header.get("EventType", "Unknown")
        by_type[t] = by_type.get(t, 0) + 1
    
    print("Events by Type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    
    return events


def analyze_trading_scenarios(events):
    """Analyze the trading scenarios in the evidence pack."""
    print()
    print("=" * 60)
    print("Trading Scenario Analysis")
    print("=" * 60)
    
    # Extract unique symbols from Governance.Symbol or TradeFields
    symbols = set()
    for e in events:
        gov = e.get("Governance", {})
        # Try different possible locations for symbol
        symbol = gov.get("Symbol")
        if not symbol:
            trade_fields = gov.get("TradeFields", {})
            symbol = trade_fields.get("Symbol")
        if symbol:
            symbols.add(symbol)
    
    if not symbols:
        print("\nNo trading symbols found (may be system events only)")
        return
    
    print(f"\nSymbols traded: {', '.join(sorted(symbols))}")
    
    # Analyze each symbol's order lifecycle
    for symbol in sorted(symbols):
        print(f"\n--- {symbol} ---")
        symbol_events = []
        for e in events:
            gov = e.get("Governance", {})
            s = gov.get("Symbol") or gov.get("TradeFields", {}).get("Symbol")
            if s == symbol:
                symbol_events.append(e)
        
        for e in symbol_events:
            header = e.get("Header", {})
            event_type = header.get("EventType", "?")
            ts_ns = header.get("TimestampInt", 0)
            
            # Convert nanoseconds to readable time
            ts_sec = ts_ns / 1e9
            dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
            time_str = dt.strftime("%H:%M:%S.%f")
            
            gov = e.get("Governance", {})
            trade_fields = gov.get("TradeFields", {})
            
            if event_type == "ORD":
                print(f"  {time_str} | {event_type} | "
                      f"Side={trade_fields.get('Side', 'N/A')} "
                      f"Qty={trade_fields.get('Volume', 'N/A')} "
                      f"@{trade_fields.get('Price', 'MKT')}")
            elif event_type in ("EXE", "PRT"):
                print(f"  {time_str} | {event_type} | "
                      f"Filled={trade_fields.get('Volume', 'N/A')} "
                      f"@{trade_fields.get('Price', 'N/A')}")
            elif event_type == "REJ":
                print(f"  {time_str} | {event_type} | "
                      f"Reason: {gov.get('DecisionReason', 'Order rejected')}")
            else:
                print(f"  {time_str} | {event_type}")


def verify_merkle_integrity():
    """Demonstrate Merkle tree verification."""
    print()
    print("=" * 60)
    print("Merkle Tree Verification")
    print("=" * 60)
    
    with open("batches.json", "r") as f:
        batch = json.load(f)
    
    print(f"\nBatch ID: {batch.get('BatchID')}")
    print(f"Merkle Root: {batch.get('MerkleRoot', '')[:32]}...")
    
    event_hashes = batch.get("EventHashes", [])
    print(f"Event Hashes: {len(event_hashes)}")
    
    # Show inclusion proofs
    proofs = batch.get("InclusionProofs", {})
    print(f"Inclusion Proofs: {len(proofs)}")
    
    for event_id, proof in list(proofs.items())[:2]:
        print(f"\n  Event: {event_id[:20]}...")
        print(f"  Index: {proof.get('index')}")
        print(f"  Path Length: {len(proof.get('path', []))}")


def show_ouch_correlation():
    """Show OUCH message to VCP event correlation."""
    print()
    print("=" * 60)
    print("OUCH Protocol Correlation")
    print("=" * 60)
    
    ouch_messages = []
    with open("ouch_messages.jsonl", "r") as f:
        for line in f:
            if line.strip():
                ouch_messages.append(json.loads(line))
    
    print(f"\nTotal OUCH messages: {len(ouch_messages)}")
    
    # Show message type distribution
    by_type = {}
    for msg in ouch_messages:
        t = msg.get("message_type", "?")
        by_type[t] = by_type.get(t, 0) + 1
    
    type_names = {
        "O": "Enter Order",
        "A": "Order Accepted",
        "E": "Order Executed",
        "C": "Order Canceled",
        "J": "Order Rejected",
        "U": "Order Replaced"
    }
    
    print("\nMessage Types:")
    for t, count in sorted(by_type.items()):
        name = type_names.get(t, "Unknown")
        print(f"  {t} ({name}): {count}")
    
    # Show sample correlation
    print("\nSample Correlations:")
    for msg in ouch_messages[:3]:
        parsed = msg.get("parsed", {})
        print(f"  OUCH {msg.get('message_type')} → "
              f"VCP Event: {msg.get('vcp_event_id', 'N/A')[:20]}...")
        print(f"    Order Token: {parsed.get('order_token', 'N/A')}")


def show_itch_market_data():
    """Show ITCH market data messages."""
    print()
    print("=" * 60)
    print("ITCH Market Data")
    print("=" * 60)
    
    itch_messages = []
    with open("itch_messages.jsonl", "r") as f:
        for line in f:
            if line.strip():
                itch_messages.append(json.loads(line))
    
    print(f"\nTotal ITCH messages: {len(itch_messages)}")
    
    # Build locate code map
    locate_map = {}
    for msg in itch_messages:
        if msg.get("message_type") == "R":
            parsed = msg.get("parsed", {})
            locate_map[parsed.get("stock_locate")] = parsed.get("stock")
    
    print("\nStock Locate Codes:")
    for code, symbol in sorted(locate_map.items(), key=lambda x: x[1]):
        print(f"  {symbol}: {code}")


def main():
    print()
    print("*" * 60)
    print("VCP v1.1 Nasdaq OUCH/ITCH Evidence Pack - Demo")
    print("*" * 60)
    
    events = load_events()
    analyze_trading_scenarios(events)
    verify_merkle_integrity()
    show_ouch_correlation()
    show_itch_market_data()
    
    print()
    print("=" * 60)
    print("Demo Complete")
    print("=" * 60)
    print("\nFor full verification, run: python verify.py --verbose")
    print()


if __name__ == "__main__":
    main()
