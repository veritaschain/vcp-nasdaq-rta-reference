"""Current inventory consistency and byte-preserving historical archives."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CurrentManifestTests(unittest.TestCase):
    def test_current_inventory_covers_tracked_files_with_matching_bytes(self):
        manifest = json.loads((ROOT / 'hash_manifest.json').read_text())
        tracked = set(filter(None, subprocess.check_output(
            ['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')))
        self.assertEqual(set(manifest['files']), tracked - {'hash_manifest.json'})
        self.assertEqual(manifest['file_count'], len(manifest['files']))
        for name, expected in manifest['files'].items():
            with self.subTest(file=name):
                content = (ROOT / name).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), expected['sha256'])
                self.assertEqual(len(content), expected['size_bytes'])

    def test_historical_manifest_and_every_listed_original_are_preserved(self):
        historical = ROOT / 'archive/hash_manifest.pre-2026-11-02.json'
        self.assertEqual(hashlib.sha256(historical.read_bytes()).hexdigest(),
                         '5930261d25d24cf2a06cbc6c2041f8bd49b37dee5eaa4b7d8b6409b86168901a')
        original = json.loads(historical.read_text())
        redirects = {
            'README.md': 'archive/README.pre-2026-11-02.md',
            'CHANGELOG.md': 'archive/CHANGELOG.pre-2026-11-02.md',
            'datasets/metadata.json': 'archive/metadata.pre-2026-11-02.json',
            'verify.py': 'archive/verify.pre-2026-11-02.py',
        }
        for name, expected in original['files'].items():
            with self.subTest(file=name):
                content = (ROOT / redirects.get(name, name)).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), expected['sha256'])
                self.assertEqual(len(content), expected['size_bytes'])

    def test_current_metadata_does_not_assert_production_or_synthetic_provenance(self):
        metadata = json.loads((ROOT / 'datasets/metadata.json').read_text())
        self.assertNotIn('nda_package_contents', metadata)
        self.assertEqual(metadata['publication_scope']['production_provenance'], 'UNVERIFIED')
        self.assertEqual(metadata['publication_scope']['third_party_attestation'], 'NOT_ESTABLISHED')
        self.assertIsNone(metadata['dataset']['production_format_compliant'])
        self.assertIsNone(metadata['dataset']['synthetic'])


if __name__ == '__main__':
    unittest.main()
