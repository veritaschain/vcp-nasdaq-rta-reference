> **Current distribution notice — 2 November 2026**
>
> This repository is distributed as a historical reference sample for demonstration. Production provenance, protocol/tier conformance, HSM custody, independent attestation, and the availability of a separate NDA package are not established by the public files. The original records declare synthetic data; that is a historical producer assertion, not an independently established provenance finding.
>
> The pack descriptions, policy IDs, certificates, key manifest and recorded verifier outputs contain historical claims. They are not current production assurance. See [the detailed limitations](STATUS-2026-10-25.md), including the absence of signer/key trust and external timestamp verification. The current CLI reports those gaps as `INDETERMINATE` and never reports authenticated success.
>
> Original metadata, README, changelog, verifier and checksum-manifest bytes are retained under [archive/](archive/). The current [hash manifest](hash_manifest.json) is a separate unsigned inventory of the current distribution, including corrected labels. It establishes file-byte consistency only; it does not authenticate origin or make a conformance finding. Event, key, anchor, certificate and historical verifier-report bytes have not been regenerated.

# VCP v1.1 Nasdaq OUCH/ITCH Evidence Pack

## Historical target: VCP v1.1 Platinum Tier (not a conformance assessment)

**Document ID**: VSO-EP-NASDAQ-001

**Version**: 1.0.0

**Date**: 2025-01-06

**Status**: Historical reference sample; current distribution is for demonstration

**Maintainer**: VeritasChain Standards Organization (VSO)

---

## Document Classification

**Type**: Historical reference sample; production format conformance not established

**Historical target tier**: Platinum; no tier assessment is established

**Protocol**: Nasdaq OUCH 5.0 / ITCH 5.0

**Purpose**: Inspect historical sample structures and selected consistency checks

> The historical pack aimed to illustrate VCP v1.1 fields for Nasdaq binary protocols. Matching a signature to the bundled key does not establish signer identity, key custody, real exchange connectivity, or protocol conformance.

---

## Historical production-package claims

The original README advertised a separate NDA package containing TSA tokens,
Nasdaq session logs, raw captures, HSM attestations and an independent audit.
The repository does not substantiate those availability or production claims.
They are retained only in the [original README](archive/README.pre-2026-11-02.md)
and [original metadata](archive/metadata.pre-2026-11-02.json) as historical
statements. No current availability assurance or NDA request process is offered
by this distribution.

---

## Public Package Contents

The public files contain historical samples and a legacy verification script. The following components can be inspected; their presence is not a conformance finding:

### Components and limits

| Component | Verification Method | Status |
|-----------|---------------------|--------|
| Event Hashes (22) | SHA-256 recomputation | Sample consistency check |
| Hash Chain | PrevHash linkage | Sample consistency check |
| Ed25519 Signatures | Bundled public key | Mathematical checks do not establish identity or custody |
| Merkle Tree | Legacy duplicated-node construction | Uses RFC 6962 hash prefixes, not its tree algorithm |
| File Integrity | Current unsigned `hash_manifest.json` | Checks listed file bytes only |

### Included Files

```
vcp-nasdaq-rta-reference/
├── README.md                    # This file
├── events.json                  # VCP events with Ed25519 signatures
├── events.jsonl                 # Events in JSONL format
├── batches.json                 # Merkle tree with inclusion proofs
├── anchors.json                 # Historical anchor metadata; no TSA proof included
├── ouch_messages.jsonl          # OUCH protocol messages (sanitized)
├── itch_messages.jsonl          # ITCH protocol messages (sanitized)
├── mapping.md                   # OUCH/ITCH → VCP field mapping
├── verify.py                    # Python verification script
├── hash_manifest.json           # File integrity checksums
├── CHANGELOG.md                 # Version history
├── LICENSE                      # CC BY 4.0
├── datasets/
│   └── metadata.json            # Dataset metadata
├── keys/
│   ├── signer_ed25519_pub.pem   # Public key (PEM)
│   ├── signer_ed25519_pub.jwk   # Public key (JWK)
│   └── key_manifest.json        # Key management policy
├── certificates/
│   ├── batch_certificate.json   # Batch certificate
│   └── event_certificate_aapl_ord.json  # Event certificate
├── verifier_outputs/
│   ├── verification_report.txt  # Human-readable report
│   └── verification_report.json # Machine-readable report
└── examples/
    └── example_usage.py         # Integration examples
```

---

## Historical Platinum Tier design targets

The following table records historical target metadata. A checked row is not an independently established implementation or conformance result; see the limitations above:

| Requirement | Specification | Implementation | Status |
|-------------|---------------|----------------|--------|
| **Timestamp Precision** | NANOSECOND | `TimestampPrecision: NANOSECOND` | ✅ |
| **Clock Synchronization** | PTP (IEEE 1588) | `ClockSyncStatus: PTP_LOCKED` | ✅ |
| **Hash Algorithm** | SHA-256 | `HashAlgo: SHA-256` | ✅ |
| **Signature Algorithm** | Ed25519 | `SignAlgo: Ed25519` | ✅ |
| **Batch Anchoring** | ≤10 minutes | Intraday anchoring | ✅ |
| **Merkle Construction** | RFC 6962 | Certificate Transparency standard | ✅ |

---

## Verification Instructions

### Quick Verification

```bash
# Install the mathematical signature checker (tested with Python 3.12)
python -m pip install -r requirements.txt

# Run local checks; the bundled sample remains INDETERMINATE, exit 2
python verify.py --verbose

# Run the CLI semantics and archive/inventory regressions
python -m unittest discover -s tests -v
```

### Result and exit status

| Result | Exit | Meaning |
| --- | --- | --- |
| `INVALID` | `1` | An observed local check failed, such as an event hash, signature, selected key encoding or inventory mismatch. This takes precedence over unavailable authentication. |
| `INDETERMINATE` | `2` | Required checks or authentication are unavailable or untrusted. This includes missing PyNaCl, missing/unsupported signatures or keys, and missing required data. |

There is no authenticated-success result or exit `0` in this implementation.
Even when every Ed25519 signature mathematically matches the bundled key,
signer identity, key trust/revocation, certificate authentication and external
anchor verification remain unimplemented. Installing PyNaCl enables the
mathematical checks; it does not supply those trust mechanisms. Existing local
checks retain their legacy encoding and duplicated-node Merkle algorithm, and
two metadata comparisons do not constitute a tier assessment.

The original permissive verifier is preserved at
[`archive/verify.pre-2026-11-02.py`](archive/verify.pre-2026-11-02.py) as historical
source. Its former `VERIFICATION PASSED` output must not be used as a current
verification result.

### Manual signature mathematics (not authentication)

```python
import nacl.signing
import json
import base64

# Load public key
with open('keys/signer_ed25519_pub.jwk') as f:
    jwk = json.load(f)

x_padded = jwk['x'] + '=' * (4 - len(jwk['x']) % 4)
public_bytes = base64.urlsafe_b64decode(x_padded)
verify_key = nacl.signing.VerifyKey(public_bytes)

# Verify first event signature
with open('events.json') as f:
    event = json.load(f)['events'][0]

event_hash = bytes.fromhex(event['Header']['EventHash'])
signature = base64.b64decode(event['Signature']['Value'])

verify_key.verify(event_hash, signature)  # Raises if invalid
print("Mathematical match against the bundled key; signer trust is not established")
```

> ⚠️ **Note**: The sample canonicalization uses `json.dumps()` for simplicity. Production implementations MUST use RFC 8785 (JSON Canonicalization Scheme) compliant libraries.

---

## Nasdaq Protocol Integration

### OUCH 5.0 (Order Entry)

| Feature | Implementation |
|---------|---------------|
| **Protocol Version** | OUCH 5.0 |
| **Transport** | SoupBinTCP |
| **Message Types** | O, U, X, A, E, C, J |
| **Order Token Format** | 14-char alphanumeric |

### ITCH 5.0 (Market Data)

| Feature | Implementation |
|---------|---------------|
| **Protocol Version** | TotalView-ITCH 5.0 |
| **Transport** | MoldUDP64 |
| **Timestamp** | Nanoseconds since midnight |
| **Message Types** | R, A, F, E, C, X, D, P |

---

## Included Trading Scenarios

| # | Symbol | Scenario | Outcome |
|---|--------|----------|---------|
| 1 | AAPL | Market order | Full fill |
| 2 | MSFT | Limit order | Partial fills → Full fill |
| 3 | GOOGL | Order replacement | Price modification → Fill |
| 4 | AMZN | Short sale | Rejected (locate required) |
| 5 | NVDA | Limit order | Cancelled |

---

## Regulatory Framework Support

### SEC Rule 17a-4
- Immutable hash chain architecture
- 6-year retention capability
- Machine-readable audit format

### FINRA Rule 4511
- Complete order lifecycle tracking
- Nanosecond timestamp precision
- Modification audit trail

### Regulation NMS / CAT
- Order routing transparency
- Cross-venue correlation
- Unique order identification

### EU AI Act (Article 12)
- Algorithmic decision logging
- Traceability requirements
- Independent verification capability

---

## Trust Model and Limitations

### Historical claimed results — not established by this distribution

✅ VCP v1.1 specification conformance

✅ Nasdaq OUCH/ITCH protocol mapping correctness

✅ Cryptographic signature validity (Ed25519)

✅ Hash chain integrity (SHA-256)

✅ Merkle tree construction (RFC 6962)

✅ Platinum Tier requirement compliance


### Evidence absent from this public distribution

No assurance is made that these materials are available separately.

❌ External timestamp authority verification

❌ Actual Nasdaq connectivity proof

❌ Raw wire capture authenticity

❌ HSM key attestation

❌ Third-party audit certification


---

## Contact Information

| Purpose | Contact |
|---------|---------|
| **General Inquiries** | info@veritaschain.org |
| **Technical Support** | technical@veritaschain.org |
| **Enterprise inquiries (no package-availability assurance)** | enterprise@veritaschain.org |
| **Compliance** | compliance@veritaschain.org |
| **Security Issues** | security@veritaschain.org |

**Resources**:
- Website: https://veritaschain.org
- GitHub: https://github.com/veritaschain
- IETF Draft: https://datatracker.ietf.org/doc/draft-kamimura-scitt-vcp/

---

## License and Non-Endorsement

This evidence pack is provided under **CC BY 4.0** license.

**Non-Endorsement Statement**: This historical reference sample makes no protocol-conformance or regulatory-compliance finding. Inclusion of Nasdaq protocol references does not imply endorsement by Nasdaq, Inc. or any regulatory authority. OUCH and ITCH are trademarks of Nasdaq, Inc.

**VeritasChain Protocol** and **VCP** are trademarks of VeritasChain Standards Organization.

---

*VSO-EP-NASDAQ-001 v1.0.0 | Generated by VCP.Nasdaq.Conformance.v1.1*

## License scope clarification — 2 November 2026

Documentation remains CC BY 4.0. First-party code, scripts, code examples and schemas additionally offer [Apache-2.0](LICENSE-CODE); existing licenses and third-party notices remain in effect. See [LICENSE](LICENSE) for the scope and preserved prior terms. This editorial licensing note does not change protocol requirements or claim conformance.
