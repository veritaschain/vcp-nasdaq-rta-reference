"""CLI regressions: unavailable authentication never becomes a successful result."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VerifierStatusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.pack = Path(self.temporary.name)
        # Copy only the inputs needed by this CLI. The temporary unsigned file
        # inventory is independent of the repository's preserved evidence bytes.
        self.manifest = {'files': {}}
        for name in ('verify.py', 'events.json', 'batches.json',
                     'keys/signer_ed25519_pub.jwk', 'keys/signer_ed25519_pub.pem'):
            destination = self.pack / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
            self.inventory_entry(name)
        self.write_manifest()

    def inventory_entry(self, name):
        content = (self.pack / name).read_bytes()
        self.manifest['files'][name] = {
            'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content)}

    def write_manifest(self):
        (self.pack / 'hash_manifest.json').write_text(json.dumps(self.manifest))

    def rewrite_json(self, name, value):
        (self.pack / name).write_text(json.dumps(value))
        # Keep file checksums consistent to isolate event/signature checks. No
        # event hash or signature is regenerated to hide a changed payload.
        self.inventory_entry(name)
        self.write_manifest()

    def invoke(self, *, without_pynacl=False):
        command = [sys.executable]
        if without_pynacl:
            command.append('-S')  # Actual missing-import path, even when CI installs PyNaCl.
        command.extend([str(self.pack / 'verify.py'), '--verbose'])
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertNotIn('Traceback', completed.stderr)
        self.assertNotIn('VERIFICATION PASSED', completed.stdout)
        self.assertNotEqual(completed.returncode, 0)
        return completed

    def assert_indeterminate(self, completed):
        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertIn('Overall: INDETERMINATE', completed.stdout)

    def assert_invalid(self, completed):
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn('Overall: INVALID', completed.stdout)

    def test_missing_pynacl_is_indeterminate(self):
        result = self.invoke(without_pynacl=True)
        self.assert_indeterminate(result)
        self.assertIn('PyNaCl unavailable', result.stdout)

    def test_matching_real_signatures_do_not_establish_trust(self):
        result = self.invoke()
        self.assert_indeterminate(result)
        self.assertIn('Ed25519 mathematical checks (not authentication): 22 local matches, 0 failures',
                      result.stdout)
        self.assertIn('Signer/key trust: INDETERMINATE', result.stdout)

    def test_observed_bad_signature_is_invalid_despite_missing_trust(self):
        data = json.loads((self.pack / 'events.json').read_text())
        value = bytearray(base64.b64decode(data['events'][0]['Signature']['Value']))
        value[0] ^= 1
        data['events'][0]['Signature']['Value'] = base64.b64encode(value).decode('ascii')
        self.rewrite_json('events.json', data)
        result = self.invoke()
        self.assert_invalid(result)
        self.assertIn('Event 0: Invalid signature', result.stdout)

    def test_observed_hash_failure_precedes_missing_pynacl(self):
        data = json.loads((self.pack / 'events.json').read_text())
        data['events'][0]['test_mutation'] = 'changed payload without changing its event hash'
        self.rewrite_json('events.json', data)
        result = self.invoke(without_pynacl=True)
        self.assert_invalid(result)
        self.assertIn('EventHash mismatch', result.stdout)
        self.assertIn('PyNaCl unavailable', result.stdout)

    def test_missing_public_key_is_indeterminate(self):
        for name in ('keys/signer_ed25519_pub.jwk', 'keys/signer_ed25519_pub.pem'):
            (self.pack / name).unlink()
            self.manifest['files'].pop(name)
        self.write_manifest()
        result = self.invoke()
        self.assert_indeterminate(result)
        self.assertIn('no usable public key', result.stdout)

    def test_original_pem_key_still_allows_only_mathematical_matches(self):
        name = 'keys/signer_ed25519_pub.jwk'
        (self.pack / name).unlink()
        self.manifest['files'].pop(name)
        self.write_manifest()
        result = self.invoke()
        self.assert_indeterminate(result)
        self.assertIn('Ed25519 mathematical checks (not authentication): 22 local matches, 0 failures',
                      result.stdout)

    def test_malformed_selected_key_precedes_missing_pynacl_and_does_not_fall_back(self):
        name = 'keys/signer_ed25519_pub.jwk'
        jwk = json.loads((self.pack / name).read_text())
        jwk['x'] = base64.urlsafe_b64encode(b'\0' * 31).decode('ascii').rstrip('=')
        self.rewrite_json(name, jwk)
        result = self.invoke(without_pynacl=True)
        self.assert_invalid(result)
        self.assertIn('Invalid public key', result.stdout)

    def test_missing_or_unsupported_signature_is_incomplete(self):
        original = json.loads((self.pack / 'events.json').read_text())
        for replacement in ({'Algorithm': 'ED25519'},
                            {'Algorithm': 'UNSUPPORTED', 'Value': 'unused'}):
            with self.subTest(signature=replacement['Algorithm']):
                data = json.loads(json.dumps(original))
                data['events'][0]['Signature'] = replacement
                self.rewrite_json('events.json', data)
                result = self.invoke()
                self.assert_indeterminate(result)
                self.assertIn('Required signature checks are incomplete', result.stdout)

    def test_malformed_events_are_invalid_when_authentication_is_unavailable(self):
        (self.pack / 'events.json').write_text('{broken json')
        self.inventory_entry('events.json')
        self.write_manifest()
        result = self.invoke(without_pynacl=True)
        self.assert_invalid(result)
        self.assertIn('Events: malformed evidence', result.stdout)


if __name__ == '__main__':
    unittest.main()
