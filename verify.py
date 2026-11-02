#!/usr/bin/env python3
"""
Historical Nasdaq Sample Consistency Checks
==========================================

Checks the legacy event encoding, duplicated-node Merkle construction, file
inventory and selected metadata. Ed25519 mathematical checks require PyNaCl.
Signer/key trust, revocation and external timestamp verification are not
implemented. Observed failures produce INVALID (exit 1); unavailable or
untrusted authentication produces INDETERMINATE (exit 2). This tool cannot
produce an authenticated success or establish protocol conformance.

Usage:
    python verify.py [--verbose]

Requirements:
    pip install -r requirements.txt

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
    """Preserve the legacy duplicated-node tree; not the RFC 6962 algorithm."""
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
    """Load bundled key bytes, without establishing their identity or trust.

    A malformed selected key must not silently fall back to another file.
    Unsupported algorithms remain unavailable, rather than being guessed.
    """
    if PUBLIC_KEY_JWK.exists():
        jwk = load_json(PUBLIC_KEY_JWK)
        if not isinstance(jwk, dict):
            raise ValueError('JWK must be an object')
        if jwk.get('kty') != 'OKP' or jwk.get('crv') != 'Ed25519':
            raise NotImplementedError('Unsupported JWK key type or curve')
        x_value = jwk.get('x')
        if not isinstance(x_value, str) or not x_value:
            raise ValueError('JWK x must contain an Ed25519 public key')
        key = base64.b64decode(x_value + '=' * (-len(x_value) % 4),
                               altchars=b'-_', validate=True)
        if len(key) != 32:
            raise ValueError('Ed25519 public key must be 32 bytes')
        return key

    if PUBLIC_KEY_PEM.exists():
        import re
        pem = PUBLIC_KEY_PEM.read_text(encoding='ascii')
        match = re.fullmatch(r'\s*-----BEGIN PUBLIC KEY-----(.+?)-----END PUBLIC KEY-----\s*',
                             pem, re.DOTALL)
        if not match:
            raise ValueError('Malformed public-key PEM')
        der = base64.b64decode(re.sub(r'\s+', '', match.group(1)), validate=True)
        # RFC 8410 SubjectPublicKeyInfo for an Ed25519 key without parameters.
        prefix = bytes.fromhex('302a300506032b6570032100')
        if not der.startswith(prefix):
            raise NotImplementedError('Unsupported public-key DER encoding or algorithm')
        if len(der) != len(prefix) + 32:
            raise ValueError('Malformed Ed25519 public-key length')
        return der[len(prefix):]

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
    """Check signature mathematics only; missing/unsupported checks stay incomplete.

    Return matching and invalid counts plus diagnostic messages. A count total
    smaller than the event count means required checks could not be performed.
    No result from this function establishes trust in the bundled key.
    """
    if not NACL_AVAILABLE:
        return 0, 0, ["PyNaCl not available"]
    
    passed = 0
    failed = 0
    errors = []
    
    try:
        verify_key = nacl.signing.VerifyKey(public_key_bytes)
    except (TypeError, ValueError) as e:
        return 0, 1, [f"Invalid public key: {e}"]
    except Exception as e:
        return 0, 0, [f"Signature backend unavailable: {type(e).__name__}"]
    
    for i, event in enumerate(events):
        try:
            header = event.get('Header', {})
            signature = event.get('Signature', {})
            sig_value = signature.get('Value') if isinstance(signature, dict) else signature
            algorithms = [header.get('SignAlgo')]
            if isinstance(signature, dict):
                algorithms.append(signature.get('Algorithm'))
            if any(not isinstance(algorithm, str) or algorithm.upper() != 'ED25519'
                   for algorithm in algorithms):
                errors.append(f"Event {i}: Missing or unsupported signature algorithm")
                continue
            if not sig_value:
                errors.append(f"Event {i}: Required signature is unavailable")
                continue
            sig_bytes = base64.b64decode(sig_value, validate=True)
            if len(sig_bytes) != 64:
                raise ValueError('Ed25519 signature must be 64 bytes')
            event_hash = header.get('EventHash')
            if not event_hash:
                errors.append(f"Event {i}: Signature message hash is unavailable")
                continue
            message = bytes.fromhex(event_hash)
            if len(message) != 32:
                raise ValueError('Event hash must be 32 bytes')
            verify_key.verify(message, sig_bytes)
            passed += 1
        except BadSignature:
            errors.append(f"Event {i}: Invalid signature")
            failed += 1
        except (TypeError, ValueError, AttributeError) as e:
            errors.append(f"Event {i}: Signature error: {e}")
            failed += 1
        except Exception as e:
            errors.append(f"Event {i}: Signature check unavailable ({type(e).__name__})")
    
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
    """Compare two historical target metadata values, not tier conformance."""
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
    print('=' * 70)
    print('Historical Nasdaq Sample — Local Checks (not authenticated)')
    print('=' * 70)

    total_passed = 0
    total_failed = 0
    all_errors = []
    gaps = [
        'Signer identity, key trust and revocation checks are NOT_IMPLEMENTED.',
        'External timestamp/anchor and certificate authentication are NOT_IMPLEMENTED.',
    ]

    def read_required(path: Path, label: str):
        nonlocal total_failed
        try:
            document = load_json(path)
            if not isinstance(document, dict):
                raise ValueError('top-level JSON must be an object')
            return document
        except OSError as error:
            gaps.append(f'{label}: unavailable ({type(error).__name__})')
        except (ValueError, UnicodeError) as error:
            total_failed += 1
            all_errors.append(f'{label}: malformed evidence ({error})')
        return None

    def record(label, check, *arguments):
        nonlocal total_passed, total_failed
        try:
            passed, failed, errors = check(*arguments)
        except (TypeError, ValueError, KeyError, AttributeError, OSError) as error:
            passed, failed = 0, 1
            errors = [f'{label}: could not process malformed or unavailable evidence ({type(error).__name__})']
        total_passed += passed
        total_failed += failed
        all_errors.extend(errors)
        print(f'{label}: {passed} local matches, {failed} failures')
        return passed, failed

    events_data = read_required(EVENTS_FILE, 'Events')
    events = events_data.get('events', []) if events_data is not None else []
    if not isinstance(events, list) or any(not isinstance(event, dict) for event in events):
        total_failed += 1
        all_errors.append('Events: events must be an array of objects')
        events = []
    if not events:
        gaps.append('Required event records are unavailable or empty.')
    print(f'Loaded {len(events)} event records')

    batches = read_required(BATCHES_FILE, 'Batch')
    if not batches:
        gaps.append('Required batch data is unavailable or empty.')
    manifest = read_required(HASH_MANIFEST_FILE, 'File inventory')
    if not manifest or not manifest.get('files'):
        gaps.append('Required file inventory is unavailable or empty.')

    public_key = None
    try:
        public_key = load_public_key()
    except (OSError, NotImplementedError) as error:
        gaps.append(f'Signature key unavailable: {error}')
    except (ValueError, UnicodeError, TypeError, KeyError) as error:
        total_failed += 1
        all_errors.append(f'Invalid public key: {error}')

    if events:
        record('Legacy event hashes and chain', verify_hash_chain, events)
        if public_key is not None and NACL_AVAILABLE:
            matched, invalid = record('Ed25519 mathematical checks (not authentication)',
                                      verify_signatures, events, public_key)
            if matched + invalid != len(events):
                gaps.append('Required signature checks are incomplete; missing or unsupported signatures are not passes.')
        else:
            reason = 'PyNaCl unavailable' if not NACL_AVAILABLE else 'no usable public key'
            gaps.append(f'Required signature mathematics: INDETERMINATE ({reason}).')
        if batches:
            record('Legacy duplicated-node Merkle checks', verify_merkle_tree, events, batches)
        record('Historical tier metadata (not conformance)', verify_platinum_requirements, events)

    if manifest and manifest.get('files'):
        record('Unsigned current file inventory', verify_file_integrity, manifest)

    # Mathematical matches do not establish trust in a key supplied by the pack.
    # Observed failures take precedence over any unavailable checks or trust gaps.
    status = 'INVALID' if total_failed else 'INDETERMINATE'
    print('\n' + '=' * 70)
    print(f'Local checks: {total_passed} matches, {total_failed} failures')
    print('Signer/key trust: INDETERMINATE (not implemented)')
    for gap in gaps:
        print('Unresolved: ' + gap)
    print('No production provenance, clock accuracy or protocol conformance is established.')
    print('Overall: ' + status)
    print('=' * 70)
    if verbose and all_errors:
        print('\nLocal check diagnostics:')
        for error in all_errors[:20]:
            print('  - ' + error)
        if len(all_errors) > 20:
            print(f'  ... and {len(all_errors) - 20} more')
    return 1 if total_failed else 2

if __name__ == '__main__':
    sys.exit(main())
