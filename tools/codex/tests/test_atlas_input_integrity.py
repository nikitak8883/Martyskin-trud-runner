"""Real temporary byte fixtures; no emulator/browser/build/model/actual input admission."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOL = Path(__file__).resolve().parents[1] / 'atlas_input_integrity.py'
spec = importlib.util.spec_from_file_location('atlas_input_integrity', TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class InputIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mtr-input-integrity-')
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.stage = self.project / 'temp/staged'
        self.stage.mkdir(parents=True)
        (self.stage / 'web').mkdir()
        (self.stage / 'web/index.html').write_bytes(b'<html>fixture</html>')
        (self.stage / 'web/primat.txt').write_bytes('Примат\n'.encode())
        (self.stage / 'app.apk').write_bytes(b'fixture-not-real-APK\x00\xff')
        self.protocol = self.project / m.PROTOCOL
        self.protocol.parent.mkdir(parents=True)
        self.protocol.write_bytes(b'{"attempt_id":"logistics-attempt02-20261001","protocol_revision":4}\r\n')
        self.pin = hashlib.sha256(self.protocol.read_bytes().replace(b'\r\n', b'\n')).hexdigest()

    def seal(self):
        value = m.make_seal(self.project, 'temp/staged', self.pin)
        raw = m.encoded(value)
        m.publish(self.project, 'temp/staged', 'temp/seal.json', raw)
        return value, hashlib.sha256(raw).hexdigest()

    def verify(self, pin):
        return m.verify(self.project, 'temp/staged', 'temp/seal.json', pin, self.pin)

    def test_success_deterministic_unicode_and_acceptance_boundary(self):
        value, pin = self.seal()
        self.assertEqual(value, m.make_seal(self.project, 'temp/staged', self.pin))
        result = self.verify(pin)
        self.assertEqual(result['file_count'], 3)
        self.assertFalse(result['input_admission'])
        self.assertFalse(result['release_accepted'])
        self.assertEqual(result['acceptance_layer'], 'byte_integrity_only')

    def test_same_length_content_change(self):
        _, pin = self.seal()
        (self.stage / 'app.apk').write_bytes(b'changed-not-real-APK\x00\xff')
        with self.assertRaisesRegex(ValueError, 'INVENTORY_CHANGED'):
            self.verify(pin)

    def test_add_unlisted_file(self):
        _, pin = self.seal()
        (self.stage / 'new.bin').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'INVENTORY_CHANGED'):
            self.verify(pin)

    def test_deleted_file(self):
        _, pin = self.seal()
        (self.stage / 'app.apk').unlink()
        with self.assertRaisesRegex(ValueError, 'INVENTORY_CHANGED'):
            self.verify(pin)

    def test_rename_file(self):
        _, pin = self.seal()
        (self.stage / 'app.apk').rename(self.stage / 'app2.apk')
        with self.assertRaisesRegex(ValueError, 'INVENTORY_CHANGED'):
            self.verify(pin)

    def test_seal_tamper_cannot_repin_itself(self):
        value, pin = self.seal()
        value['files'][0]['sha256'] = '0' * 64
        (self.project / 'temp/seal.json').write_bytes(m.encoded(value))
        with self.assertRaisesRegex(ValueError, 'SEAL_CHANGED'):
            self.verify(pin)

    def test_missing_external_pin(self):
        self.seal()
        with self.assertRaisesRegex(ValueError, 'SEAL_PIN_REQUIRED'):
            self.verify(None)

    def test_foreign_admission_shape_bool_count_unsorted_and_duplicates(self):
        value, _ = self.seal()
        for change in ('acceptance', 'unknown', 'count', 'path', 'duplicate', 'order'):
            with self.subTest(change=change):
                wrong = copy.deepcopy(value)
                if change == 'acceptance': wrong['input_admission'] = True
                if change == 'unknown': wrong['accepted'] = True
                if change == 'count': wrong['total_bytes'] = float(wrong['total_bytes'])
                if change == 'path': wrong['files'][0]['path'] = '../outside'
                if change == 'duplicate': wrong['files'].append(wrong['files'][0])
                if change == 'order': wrong['files'].reverse()
                raw = m.encoded(wrong)
                (self.project / 'temp/seal.json').write_bytes(raw)
                with self.assertRaises(ValueError): self.verify(hashlib.sha256(raw).hexdigest())

    def test_duplicate_json_keys_rejected_even_with_correct_outer_pin(self):
        value, _ = self.seal()
        raw = m.encoded(value).replace(b'"input_admission": false,', b'"input_admission": false, "input_admission": false,')
        (self.project / 'temp/seal.json').write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_JSON_KEY'):
            self.verify(hashlib.sha256(raw).hexdigest())

    def test_protocol_drift(self):
        _, pin = self.seal()
        self.protocol.write_bytes(self.protocol.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'PROTOCOL_CHANGED'):
            self.verify(pin)

    def test_invalid_portable_paths(self):
        for p in ('../x', '/x', 'temp/../x', 'temp//x', 'temp/./x', 'temp/x:stream', 'temp/NUL.txt', 'temp/x.', 'temp/x ', 'temp/x\\y', 'temp/e\u0301', ''):
            with self.subTest(path=p), self.assertRaises(ValueError): m.portable(p)

    def test_source_tree_not_staging(self):
        with self.assertRaisesRegex(ValueError, 'TEMP_SCOPE_REQUIRED'):
            m.scoped(self.project, 'assets/resources')

    def test_output_inside_input_and_existing_output_never_overwritten(self):
        value, _ = self.seal()
        before = (self.project / 'temp/seal.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'OUTPUT_EXISTS'):
            m.publish(self.project, 'temp/staged', 'temp/seal.json', b'wrong')
        self.assertEqual(before, (self.project / 'temp/seal.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'OUTPUT_INSIDE_STAGING'):
            m.publish(self.project, 'temp/staged', 'temp/staged/seal.json', m.encoded(value))

    def test_hardlinked_input_rejected(self):
        os.link(self.stage / 'app.apk', self.project / 'alias.apk')
        with self.assertRaisesRegex(ValueError, 'HARDLINK'):
            m.make_seal(self.project, 'temp/staged', self.pin)

    def test_directory_link_or_windows_junction_is_rejected_without_target_traversal(self):
        target = self.project / 'outside'
        target.mkdir()
        keep = target / 'keep.bin'
        keep.write_bytes(b'keep')
        link = self.stage / 'linked'
        if os.name == 'nt':
            r = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True, timeout=15)
            self.assertEqual(r.returncode, 0, r.stderr)
        else:
            link.symlink_to(target, target_is_directory=True)
        try:
            with self.assertRaisesRegex(ValueError, 'LINK_OR_REPARSE'):
                m.make_seal(self.project, 'temp/staged', self.pin)
            self.assertEqual(keep.read_bytes(), b'keep')
        finally:
            if os.name == 'nt': link.rmdir()  # Remove only the owned junction, never its target.
            else: link.unlink()

    def test_link_in_output_parent_rejected(self):
        linked = self.project / 'temp/linked'
        target = self.project / 'outside'
        target.mkdir()
        if os.name == 'nt':
            r = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(linked), str(target)], capture_output=True, timeout=15)
            self.assertEqual(r.returncode, 0, r.stderr)
        else: linked.symlink_to(target, target_is_directory=True)
        try:
            with self.assertRaisesRegex(ValueError, 'LINK_OR_REPARSE'):
                m.publish(self.project, 'temp/staged', 'temp/linked/seal.json', b'no')
            self.assertFalse((target / 'seal.json').exists())
        finally:
            if os.name == 'nt': linked.rmdir()
            else: linked.unlink()

    def test_mutation_between_scans_is_not_sealed(self):
        original = m.inventory
        calls = 0
        def mutate(root):
            nonlocal calls
            result = original(root)
            calls += 1
            if calls == 1: (self.stage / 'app.apk').write_bytes(b'mutated')
            return result
        with mock.patch.object(m, 'inventory', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'STAGING_CHANGED'):
                m.make_seal(self.project, 'temp/staged', self.pin)

    def test_windows_deprecated_ctime_is_not_cross_api_identity(self):
        from types import SimpleNamespace
        a = SimpleNamespace(st_dev=1, st_ino=2, st_size=3, st_mtime_ns=4, st_ctime_ns=5, st_birthtime_ns=6)
        b = copy.copy(a)
        b.st_ctime_ns = 7
        with mock.patch.object(m.os, 'name', 'nt'):
            self.assertEqual(m.fingerprint(a), m.fingerprint(b))
            b.st_mtime_ns = 8
            self.assertNotEqual(m.fingerprint(a), m.fingerprint(b))
        with mock.patch.object(m.os, 'name', 'posix'):
            b.st_mtime_ns = 4
            self.assertNotEqual(m.fingerprint(a), m.fingerprint(b))

    def test_content_changed_while_handle_open(self):
        actual = m.os.fstat
        calls = 0
        def mutation(fd):
            nonlocal calls
            calls += 1
            if calls == 2: (self.stage / 'app.apk').write_bytes(b'changed-and-longer-fixture-data')
            return actual(fd)
        with mock.patch.object(m.os, 'fstat', side_effect=mutation):
            with self.assertRaisesRegex(ValueError, 'FILE_CHANGED_READ'):
                m.hash_regular(self.stage / 'app.apk')

    def test_entry_limit_fails_without_truncation(self):
        with mock.patch.object(m, 'MAX_FILES', 1):
            with self.assertRaises(ValueError): m.inventory(self.stage)

    def test_publish_collision_and_disk_failure_leave_no_owned_temp(self):
        with mock.patch.object(m.os, 'link', side_effect=FileExistsError('collision')):
            with self.assertRaises(FileExistsError): m.publish(self.project, 'temp/staged', 'temp/new.json', b'fixture')
        self.assertFalse((self.project / 'temp/new.json').exists())
        with mock.patch.object(m.os, 'fsync', side_effect=OSError('disk error')):
            with self.assertRaises(OSError): m.publish(self.project, 'temp/staged', 'temp/new.json', b'fixture')
        self.assertEqual(list((self.project / 'temp').glob('*.pending-*')), [])

    def test_empty_staging_and_size_limit(self):
        empty = self.project / 'temp/empty'
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, 'EMPTY_STAGING'): m.inventory(empty)
        with mock.patch.object(m, 'MAX_SEAL_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'SEAL_SIZE_LIMIT'): m.encoded({'x': 1})

    def test_case_alias_portability_without_host_case_assumptions(self):
        value, _ = self.seal()
        value['files'].append(dict(value['files'][0], path=value['files'][0]['path'].upper()))
        raw = m.encoded(value)
        (self.project / 'temp/seal.json').write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'INVENTORY_CHANGED'): self.verify(hashlib.sha256(raw).hexdigest())
        if os.name != 'nt':
            (self.stage / 'APP.apk').write_bytes(b'different-case')
            with self.assertRaisesRegex(ValueError, 'CASE_ALIAS'): m.inventory(self.stage)

    def test_cli_live_success_wrong_pin_and_duplicate_arguments(self):
        args = [sys.executable, '-B', str(TOOL), 'seal', '--project-root', str(self.project),
                '--staging-root', 'temp/staged', '--expected-protocol-sha256', self.pin,
                '--seal', 'temp/seal.json']
        r = subprocess.run(args, capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        pin = json.loads(r.stdout)['seal_sha256']
        args[3] = 'verify'
        r = subprocess.run(args + ['--expected-seal-sha256', pin], capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse(json.loads(r.stdout)['input_admission'])
        r = subprocess.run(args + ['--expected-seal-sha256', '0' * 64], capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 1)
        r = subprocess.run(args + ['--seal', 'temp/other.json'], capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 2)
        self.assertFalse((self.project / 'temp/other.json').exists())
        abbreviated = args.copy()
        abbreviated[abbreviated.index('--project-root')] = '--project-r'
        r = subprocess.run(abbreviated, capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 2)
        r = subprocess.run(args + ['--unknown', 'x'], capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
