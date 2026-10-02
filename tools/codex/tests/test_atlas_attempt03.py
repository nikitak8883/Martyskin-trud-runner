"""Preregistration/source negative controls; no builds, models or runtime samples."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'tools/codex'))
import atlas_attempt03 as m


def raw(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


class Attempt03(unittest.TestCase):
    def setUp(self):
        self.protocol = m.decode(m.read_file(PROJECT, m.PROTOCOL))
        self.inventory = m.decode(m.read_file(PROJECT, m.INVENTORY))
        self.anchored = copy.deepcopy(self.inventory)
        self.overrides = {}

    def read(self, path):
        if path in self.overrides:
            return self.overrides[path]
        if path == m.INVENTORY:
            return raw(self.inventory)
        return m.read_file(PROJECT, path)

    def validate(self):
        m.validate_documents(self.protocol, self.inventory, self.anchored, self.read)

    def test_repository_anchor_sources_tooling_and_acceptance_boundary(self):
        result = m.validate(PROJECT)
        self.assertEqual((result['status'], result['source_count'], result['measurement_tool_pins']), ('PASS', 26, 9))
        self.assertFalse(result['input_admission'])
        self.assertFalse(result['release_accepted'])
        self.assertEqual(result['experiment_runtime'], 'NOT_RUN')

    def test_frozen_thresholds_schedule_cohorts_silence_and_tooling(self):
        mutations = {
            'acceptance_overrides': {'max_load_ms': 99999}, 'source_count': 25,
            'pair_order': list(reversed(self.protocol['pair_order'])),
            'input_admission': {'verify_input_hashes_before_and_after_each_state': False},
            'android': dict(self.protocol['android'], media_volume=1),
            'evaluation': dict(self.protocol['evaluation'], checks_per_comparison=62),
            'tooling_pins': self.protocol['tooling_pins'][:-1],
        }
        original = copy.deepcopy(self.protocol)
        for key, value in mutations.items():
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'FROZEN_CRITERIA_CHANGED'):
                self.protocol = dict(original, **{key: value})
                self.validate()

    def test_candidate_web_identity_and_unknown_fields(self):
        original = copy.deepcopy(self.protocol)
        for key, value, error in (
            ('candidate', dict(original['candidate'], descriptor_uuid='wrong'), 'CANDIDATE_CHANGED'),
            ('web', dict(original['web'], sample_count=4), 'WEB_COHORT_CHANGED'),
            ('protocol_revision', True, 'PROTOCOL_IDENTITY'),
            ('source_anchor', '0' * 40, 'SOURCE_ANCHOR'),
            ('unknown_admission', True, 'PROTOCOL_SHAPE'),
        ):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, error):
                self.protocol = dict(original, **{key: value})
                self.validate()

    def test_predecessor_provenance_and_admission_cannot_be_relabelled(self):
        for key, field, value, error in (
            ('revision_provenance', 'predecessor_status', 'accepted', 'PROVENANCE_CHANGED'),
            ('facts_at_preregistration', 'input_admission', True, 'NOT_ADMISSION'),
            ('facts_at_preregistration', 'timed_web_samples', 1, 'NOT_ADMISSION'),
            ('facts_at_preregistration', 'timed_android_samples', False, 'NOT_ADMISSION'),
        ):
            original = copy.deepcopy(self.protocol)
            self.protocol[key][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, error):
                self.validate()
            self.protocol = original

    def test_repinned_inventory_omission_duplicate_geometry_and_uuid_rejected(self):
        original = copy.deepcopy(self.inventory)
        for kind in ('omission', 'duplicate', 'geometry', 'uuid', 'hash', 'type', 'unknown'):
            self.inventory = copy.deepcopy(original)
            if kind == 'omission': self.inventory['items'].pop()
            if kind == 'duplicate': self.inventory['items'][-1] = self.inventory['items'][0]
            if kind == 'geometry': self.inventory['items'][0]['geometry']['pivotX'] = 0.4
            if kind == 'uuid': self.inventory['items'][0]['uuid'] = m.UUID
            if kind == 'hash': self.inventory['items'][0]['sha256'] = '0' * 64
            if kind == 'type': self.inventory['source_count'] = 26.0
            if kind == 'unknown': self.inventory['admitted'] = True
            self.protocol['source_inventory_sha256'] = m.sha(raw(self.inventory), lf=True)
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'INVENTORY_ANCHOR_MISMATCH'):
                self.validate()

    def test_actual_png_substitution_even_when_inventory_is_repinned(self):
        path = self.inventory['items'][0]['path']
        self.overrides[path] = m.read_file(PROJECT, path) + b'changed'
        self.inventory = m.source_inventory(self.read)
        self.protocol['source_inventory_sha256'] = m.sha(raw(self.inventory), lf=True)
        with self.assertRaisesRegex(ValueError, 'INVENTORY_ANCHOR_MISMATCH'):
            self.validate()

    def test_actual_metadata_substitution_without_inventory_repin(self):
        path = self.inventory['items'][0]['path'] + '.meta'
        metadata = m.decode(m.read_file(PROJECT, path))
        frame = next(v for v in metadata['subMetas'].values() if v['importer'] == 'sprite-frame')
        frame['userData']['pivotX'] = 0.4
        self.overrides[path] = raw(metadata)
        with self.assertRaisesRegex(ValueError, 'SOURCE_ANCHOR_MISMATCH'):
            self.validate()

    def test_metadata_and_manifest_crlf_only_portability(self):
        paths = [m.MANIFEST] + [v['path'] + '.meta' for v in self.inventory['items']]
        for path in paths:
            self.overrides[path] = m.read_file(PROJECT, path).replace(b'\r\n', b'\n')
        self.validate()

    def test_tool_template_and_inventory_pins_fail_closed(self):
        for path, error in ((m.TEMPLATE, 'TEMPLATE_CHANGED'),
                            (self.protocol['tooling_pins'][0]['path'], 'INPUT_PIN_CHANGED')):
            with self.subTest(path=path):
                self.overrides = {path: m.read_file(PROJECT, path) + b' '}
                with self.assertRaisesRegex(ValueError, error): self.validate()
        self.overrides = {}
        self.protocol['source_inventory_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'INVENTORY_PIN'): self.validate()

    def test_immutable_registration_outer_pin_cannot_be_self_repinned(self):
        self.protocol['source_qualification_pins'][0]['sha256_utf8_lf'] = '0' * 64
        actual = m.read_file
        def altered(project, path):
            return raw(self.protocol) if path == m.PROTOCOL else actual(project, path)
        with mock.patch.object(m, 'read_file', side_effect=altered):
            with self.assertRaisesRegex(ValueError, 'PREREGISTRATION_CHANGED'): m.validate(PROJECT)

    def test_old_registration_and_duplicate_json_keys_rejected(self):
        self.overrides[m.integrity.PROTOCOL] = m.read_file(PROJECT, m.integrity.PROTOCOL) + b' '
        with self.assertRaisesRegex(ValueError, 'PREDECESSOR_CHANGED'): self.validate()
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_JSON_KEY'):
            m.decode(b'{"attempt_id":"x","attempt_id":"x"}')


if __name__ == '__main__':
    unittest.main()
