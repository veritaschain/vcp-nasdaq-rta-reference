# Historical pack files

The `*.pre-2026-11-02.*` files preserve the original committed bytes before the
current metadata, documentation and verifier corrections. Their production, NDA,
conformance and attestation claims are historical statements, not current
assurance or evidence that a separate package exists. Original Markdown hard-break
spaces and Python whitespace are intentionally preserved in the archived README
and verifier; do not trim them.

`hash_manifest.pre-2026-11-02.json` is the original manifest, including its
original root value. Its paths refer to the original pack. To check those
original bytes in the current checkout, resolve these edited paths as follows:

| Original path | Preserved copy |
| --- | --- |
| `README.md` | `archive/README.pre-2026-11-02.md` |
| `CHANGELOG.md` | `archive/CHANGELOG.pre-2026-11-02.md` |
| `datasets/metadata.json` | `archive/metadata.pre-2026-11-02.json` |
| `verify.py` | `archive/verify.pre-2026-11-02.py` |

Every other file listed by the original manifest remains at its original path
with unchanged bytes. The archive test checks all original file digests and
sizes and pins the original manifest's own SHA-256.

The root `hash_manifest.json` is a separate unsigned current-distribution
inventory. Regenerate it with `python tools/update_hash_manifest.py` after
staging any new files, then run `python -m unittest discover -s tests -v`.
Regenerating that inventory is not evidence signing, an external anchor, or a
protocol-conformance assessment. Do not regenerate historical events,
signatures, certificates, or reports to make a changed narrative appear valid.
