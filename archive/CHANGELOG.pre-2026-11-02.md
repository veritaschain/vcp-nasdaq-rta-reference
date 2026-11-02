# Changelog

All notable changes to the VCP v1.1 Nasdaq OUCH/ITCH Evidence Pack.

## [1.0.0] - 2025-01-06

### Added
- Initial release of VCP v1.1 Platinum Tier conformance test dataset
- Complete OUCH 5.0 order entry protocol mapping
- Complete ITCH 5.0 market data protocol mapping
- 22 VCP events covering 5 trading scenarios
- 18 OUCH binary messages with parsed representations
- 28 ITCH market data messages including Stock Directory
- Merkle tree construction with RFC 6962 compliance
- Real Ed25519 signatures (cryptographically verifiable)
- Python verification script (verify.py)
- Comprehensive documentation (README.md, mapping.md)

### Trading Scenarios Included
1. AAPL - Market order with immediate full fill
2. MSFT - Limit order with multiple partial fills
3. GOOGL - Order replacement (price modification)
4. AMZN - Order rejection (missing locate for short sale)
5. NVDA - Order cancellation

### Compliance Features
- SEC Rule 17a-4 retention markers
- FINRA Rule 4511 compliance
- Regulation NMS support
- CAT reporting field mapping
- 6-year retention configuration

### Technical Specifications
- Nanosecond timestamp precision (NANOSECOND)
- PTP clock synchronization status (PTP_LOCKED)
- UUIDv7 event identifiers (RFC 9562)
- SHA-256 hashing (RFC 8785 canonicalization)
- RFC 6962 Merkle tree construction
- Ed25519 digital signatures (RFC 8032)

### Classification
- **Type**: Conformance Test Dataset
- **Format Compliance**: Production Format Compliant
- **Purpose**: VCP specification conformance demonstration
- **Cryptographic Verification**: All signatures independently verifiable

> **Note**: This is a conformance test dataset demonstrating VCP v1.1 Platinum Tier specification compliance. Full production evidence including RFC 3161 TSA tokens, Nasdaq connectivity proof, and third-party audit certification is available under NDA. Contact enterprise@veritaschain.org.

## Production Evidence Package (NDA Required)

The full production evidence package includes additional components not present in this public conformance test dataset:

| Component | Public Package | NDA Package |
|-----------|---------------|-------------|
| Ed25519 Signatures | ✅ | ✅ |
| Hash Chain | ✅ | ✅ |
| Merkle Proofs | ✅ | ✅ |
| RFC 3161 TSA Tokens | ❌ | ✅ |
| Nasdaq Session Proof | ❌ | ✅ |
| Raw PCAP Captures | ❌ | ✅ |
| HSM Attestation | ❌ | ✅ |
| Third-party Audit | ❌ | ✅ |

## Future Planned Changes

### [1.1.0] - Planned
- Add support for Nasdaq Nordic OUCH variants
- Include cross/auction message types
- Enhanced latency metrics
- Public TSA anchor integration demo

### [1.2.0] - Planned
- Post-quantum cryptography (ML-DSA-65) option
- Enhanced ITCH order book reconstruction
- Real-time verification streaming mode

---

For the latest updates, visit: https://github.com/veritaschain/vcp-spec
