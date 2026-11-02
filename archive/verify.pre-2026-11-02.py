#!/usr/bin/env python3
"""
VCP v1.1 Platinum Tier Verification Script
==========================================

Verifies the cryptographic integrity of Nasdaq OUCH/ITCH evidence pack.

Usage:
    python verify.py [--verbose]

Requirements:
    pip install pynacl

References:
    - VCP Specification v1.1
    - RFC 6962 (Certificate Transparency Merkle Trees)
    - RFC 8032 (Ed25519 Digital Signatures)
    - RFC 8785 (JSON Canonicalization Scheme)
"""

import json
import hashlib
import sys
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Try to import PyNaCl for signature verification
try:
    import nacl.signing
    import nacl.encoding
    from nacl.exceptions import BadSignatureError as BadSignature
    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False
    print("⚠️ PyNaCl not installed. Install with: pip install pynacl")

# =============================================================================
# Configuration
# =============================================================================

EVIDENCE_PACK_DIR = Path(__file__).parent
EVENTS_FILE = EVIDENCE_PACK_DIR / "events.json"
BATCHES_FILE = EVIDENCE_PACK_DIR / "batches.json"
ANCHORS_FILE = EVIDENCE_PACK_DIR / "anchors.json"
HASH_MANIFEST_FILE = EVIDENCE_PACK_DIR / "hash_manifest.json"
PUBLIC_KEY_JWK = EVIDENCE_PACK_DIR / "keys" / "signer_ed25519_pub.jwk"
PUBLIC_KEY_PEM = EVIDENCE_PACK_DIR / "keys" / "signer_ed25519_pub.pem"

# =============================================================================
# Helper Functions
# =============================================================================

def load_json(filepath: Path) -> dict:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def canonicalize(obj: dict) -> str:
    """Simplified RFC 8785 canonicalization."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def compute_event_hash(event: dict) -> str:
    """Compute SHA-256 hash of event (excluding hash and signature fields)."""
    event_copy = {}
    for k, v in event.items():
        if k in ('Hash', 'hash', 'Signature', 'signature'):
            continue
        if k == 'Header' and isinstance(v, dict):
            header_copy = {hk: hv for hk, hv in v.items() if hk != 'EventHash'}
            event_copy[k] = header_copy
        else:
            event_copy[k] = v
    
    canonical = canonicalize(event_copy)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def compute_merkle_root(hashes: List[str]) -> str:
    """Compute Merkle root per RFC 6962."""
    if not hashes:
        return hashlib.sha256(b'').hexdigest()
    
    leaves = [hashlib.sha256(b'\x00' + bytes.fromhex(h)).digest() for h in hashes]
    
    while len(leaves) > 1:
        next_level = []
        for i in range(0, len(leaves), 2):
            if i + 1 < len(leaves):
                node = hashlib.sha256(b'\x01' + leaves[i] + leaves[i + 1]).digest()
            else:
                node = hashlib.sha256(b'\x01' + leaves[i] + leaves[i]).digest()
            next_level.append(node)
        leaves = next_level
    
    return leaves[0].hex()

def load_public_key() -> Optional[bytes]:
    """Load Ed25519 public key from JWK or PEM."""
    # Try JWK first
    if PUBLIC_KEY_JWK.exists():
        try:
            jwk = load_json(PUBLIC_KEY_JWK)
            if jwk.get('kty') == 'OKP' and jwk.get('crv') == 'Ed25519':
                x_value = jwk['x']
                # Add padding for base64url
                padding = 4 - len(x_value) % 4
                if padding != 4:
                    x_value += '=' * padding
                return base64.urlsafe_b64decode(x_value)
        except Exception as e:
            print(f"⚠️ Failed to load JWK: {e}")
    
    # Try PEM
    if PUBLIC_KEY_PEM.exists():
        try:
            with open(PUBLIC_KEY_PEM, 'r') as f:
                pem = f.read()
            # Extract base64 content
            import re
            match = re.search(r'-----BEGIN PUBLIC KEY-----(.+?)-----END PUBLIC KEY-----', pem, re.DOTALL)
            if match:
                b64_content = match.group(1).replace('\n', '').replace(' ', '')
                der = base64.b64decode(b64_content)
                # Ed25519 public key is last 32 bytes of DER
                if len(der) >= 32:
                    return der[-32:]
        except Exception as e:
            print(f"⚠️ Failed to load PEM: {e}")
    
    return None

# =============================================================================
# Verification Functions
# =============================================================================

def verify_hash_chain(events: List[dict]) -> Tuple[int, int, List[str]]:
    """Verify SHA-256 hash chain integrity."""
    passed = 0
    failed = 0
    errors = []
    
    prev_hash = '0' * 64  # Genesis
    
    for i, event in enumerate(events):
        header = event.get('Header', {})
        stored_hash = header.get('EventHash')
        stored_prev = header.get('PrevHash')
        
        # Verify prev hash chain
        if stored_prev != prev_hash:
            errors.append(f"Event {i}: PrevHash mismatch (expected {prev_hash[:16]}..., got {stored_prev[:16] if stored_prev else 'None'}...)")
            failed += 1
        
        # Verify event hash
        computed = compute_event_hash(event)
        if computed != stored_hash:
            errors.append(f"Event {i}: EventHash mismatch (computed {computed[:16]}..., stored {stored_hash[:16] if stored_hash else 'None'}...)")
            failed += 1
        else:
            passed += 1
        
        prev_hash = stored_hash if stored_hash else prev_hash
    
    return passed, failed, errors

def verify_signatures(events: List[dict], public_key_bytes: bytes) -> Tuple[int, int, List[str]]:
    """Verify Ed25519 signatures."""
    if not NACL_AVAILABLE:
        return 0, 0, ["PyNaCl not available"]
    
    passed = 0
    failed = 0
    errors = []
    
    try:
        verify_key = nacl.signing.VerifyKey(public_key_bytes)
    except Exception as e:
        return 0, 0, [f"Failed to create verify key: {e}"]
    
    for i, event in enumerate(events):
        signature = event.get('Signature', {})
        sig_value = signature.get('Value') if isinstance(signature, dict) else signature
        
        if not sig_value:
            continue
        
        try:
            sig_bytes = base64.b64decode(sig_value)
            event_hash = event.get('Header', {}).get('EventHash')
            if not event_hash:
                continue
            
            message = bytes.fromhex(event_hash)
            verify_key.verify(message, sig_bytes)
            passed += 1
        except BadSignature:
            errors.append(f"Event {i}: Invalid signature")
            failed += 1
        except Exception as e:
            errors.append(f"Event {i}: Signature error: {e}")
            failed += 1
    
    return passed, failed, errors

def verify_merkle_tree(events: List[dict], batches: dict) -> Tuple[int, int, List[str]]:
    """Verify Merkle tree construction."""
    passed = 0
    failed = 0
    errors = []
    
    # Get event hashes
    event_hashes = [e.get('Header', {}).get('EventHash') for e in events]
    event_hashes = [h for h in event_hashes if h]
    
    # Compute Merkle root
    computed_root = compute_merkle_root(event_hashes)
    stored_root = batches.get('MerkleRoot')
    
    if computed_root == stored_root:
        passed += 1
    else:
        errors.append(f"MerkleRoot mismatch (computed {computed_root[:16]}..., stored {stored_root[:16] if stored_root else 'None'}...)")
        failed += 1
    
    # Verify stored event hashes match
    stored_hashes = batches.get('EventHashes', [])
    if stored_hashes == event_hashes:
        passed += 1
    else:
        errors.append(f"EventHashes array mismatch")
        failed += 1
    
    return passed, failed, errors

def verify_file_integrity(manifest: dict) -> Tuple[int, int, List[str]]:
    """Verify file integrity using hash manifest."""
    passed = 0
    failed = 0
    errors = []
    
    files = manifest.get('files', {})
    
    for filepath, info in files.items():
        full_path = EVIDENCE_PACK_DIR / filepath
        expected_hash = info.get('sha256')
        
        if not full_path.exists():
            errors.append(f"{filepath}: File not found")
            failed += 1
            continue
        
        with open(full_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
        
        if actual_hash == expected_hash:
            passed += 1
        else:
            errors.append(f"{filepath}: Hash mismatch")
            failed += 1
    
    return passed, failed, errors

def verify_platinum_requirements(events: List[dict]) -> Tuple[int, int, List[str]]:
    """Verify Platinum Tier requirements."""
    passed = 0
    failed = 0
    errors = []
    
    if not events:
        return 0, 1, ["No events found"]
    
    # Check first event for Platinum values
    header = events[0].get('Header', {})
    
    # ClockSyncStatus
    clock_sync = header.get('ClockSyncStatus')
    if clock_sync == 'PTP_LOCKED':
        passed += 1
    else:
        errors.append(f"ClockSyncStatus: expected PTP_LOCKED, got {clock_sync}")
        failed += 1
    
    # TimestampPrecision
    ts_precision = header.get('TimestampPrecision')
    if ts_precision == 'NANOSECOND':
        passed += 1
    else:
        errors.append(f"TimestampPrecision: expected NANOSECOND, got {ts_precision}")
        failed += 1
    
    return passed, failed, errors

# =============================================================================
# Main
# =============================================================================

def main():
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    print("=" * 70)
    print("VCP v1.1 Platinum Tier Verification - Nasdaq OUCH/ITCH")
    print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    all_errors = []
    
    # Load data
    print("\n📂 Loading evidence pack...")
    try:
        events_data = load_json(EVENTS_FILE)
        events = events_data.get('events', [])
        print(f"   Loaded {len(events)} events")
    except Exception as e:
        print(f"   ❌ Failed to load events: {e}")
        return 1
    
    try:
        batches = load_json(BATCHES_FILE)
        print(f"   Loaded batches.json")
    except Exception as e:
        print(f"   ❌ Failed to load batches: {e}")
        batches = {}
    
    try:
        manifest = load_json(HASH_MANIFEST_FILE)
        print(f"   Loaded hash_manifest.json")
    except Exception as e:
        print(f"   ⚠️ Failed to load manifest: {e}")
        manifest = {}
    
    # Load public key
    public_key = load_public_key()
    if public_key:
        print(f"   Loaded public key ({len(public_key)} bytes)")
    else:
        print(f"   ⚠️ No public key found")
    
    # 1. Hash Chain
    print("\n🔗 Verifying Hash Chain...")
    p, f, e = verify_hash_chain(events)
    total_passed += p
    total_failed += f
    all_errors.extend(e)
    print(f"   {'✅' if f == 0 else '❌'} {p} passed, {f} failed")
    
    # 2. Signatures
    print("\n✍️ Verifying Ed25519 Signatures...")
    if public_key and NACL_AVAILABLE:
        p, f, e = verify_signatures(events, public_key)
        total_passed += p
        total_failed += f
        all_errors.extend(e)
        print(f"   {'✅' if f == 0 else '❌'} {p} signatures verified")
    else:
        print(f"   ⚠️ Skipped (no key or PyNaCl)")
    
    # 3. Merkle Tree
    print("\n🌳 Verifying Merkle Tree...")
    p, f, e = verify_merkle_tree(events, batches)
    total_passed += p
    total_failed += f
    all_errors.extend(e)
    print(f"   {'✅' if f == 0 else '❌'} {p} passed, {f} failed")
    
    # 4. File Integrity
    print("\n📁 Verifying File Integrity...")
    if manifest:
        p, f, e = verify_file_integrity(manifest)
        total_passed += p
        total_failed += f
        all_errors.extend(e)
        print(f"   {'✅' if f == 0 else '❌'} {p} files verified")
    else:
        print(f"   ⚠️ Skipped (no manifest)")
    
    # 5. Platinum Requirements
    print("\n🏆 Verifying Platinum Tier Requirements...")
    p, f, e = verify_platinum_requirements(events)
    total_passed += p
    total_failed += f
    all_errors.extend(e)
    print(f"   {'✅' if f == 0 else '❌'} {p} requirements met")
    
    # Summary
    print("\n" + "=" * 70)
    if total_failed == 0:
        print(f"✅ VERIFICATION PASSED | {total_passed} checks passed")
    else:
        print(f"❌ VERIFICATION FAILED | {total_passed} passed, {total_failed} failed")
    print("=" * 70)
    
    if verbose and all_errors:
        print("\nErrors:")
        for err in all_errors[:20]:
            print(f"  - {err}")
        if len(all_errors) > 20:
            print(f"  ... and {len(all_errors) - 20} more")
    
    return 0 if total_failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
