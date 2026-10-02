"""Validate frozen logistics preregistration and sources, never admit timed inputs."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess

import atlas_input_integrity as integrity

ATTEMPT = integrity.ATTEMPT03
PROTOCOL = integrity.PROTOCOLS[ATTEMPT][0]
INVENTORY = 'docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_LOGISTICS_ATTEMPT03_SOURCE_INVENTORY.json'
OLD_PROTOCOL_SHA = '41f0eaf2e08268282005f0b7f14eb5a5a469fde64145db15b1872de53136d5ff'
PROTOCOL_SHA = '9a11c35f8917ab428eb57dc36ec9eb48d8bc82b20842615eae39327aeec201ed'
ANCHOR = '87dd0fcbefc5ff19e3ba4a296cc7514886b16d7b'
TREE = '072b893af8fe33cf256a79c48ded40fbff083a65'
UUID = 'e5967660-4779-4e07-a4aa-94a785f2b37a'
MANIFEST = 'assets/resources/config/last_iteration_asset_manifest.generated.json'
SOURCE_ROOT = 'assets/resources/objectives/themed/last_iteration/logistics'
TEMPLATE = 'assets/resources/objectives/themed/last_iteration/farm/level_theme_farm.pac.meta'
DESCRIPTOR = SOURCE_ROOT + '/level_theme_logistics.pac'
INVENTORY_POLICY = 'PNG_raw_bytes; metadata_and_manifest_UTF8_bytes_after_CRLF_to_LF_only'


def sha(raw: bytes, *, lf=False) -> str:
    return hashlib.sha256(raw.replace(b'\r\n', b'\n') if lf else raw).hexdigest()


def decode(raw: bytes):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=integrity.no_duplicate_keys)


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def read_file(project: Path, relative: str) -> bytes:
    integrity.portable(relative)
    path = integrity.guarded(project / relative)
    size, before = integrity.hash_regular(path)
    integrity.require(size <= integrity.MAX_SEAL_BYTES, 'INPUT_SIZE_LIMIT')
    raw = integrity.bounded_bytes(path)
    integrity.require(sha(raw) == before == integrity.hash_regular(path)[1], 'INPUT_CHANGED')
    return raw


def git(project: Path, *args) -> bytes:
    return subprocess.check_output(['git', '-C', str(project), *args], timeout=30, stderr=subprocess.PIPE)


def anchored_file(project: Path, relative: str) -> bytes:
    integrity.portable(relative)
    # Published projection has the project at tree root on Windows and Linux.
    return git(project, 'cat-file', '-p', ANCHOR + ':' + relative)


def source_inventory(read) -> dict:
    manifest_raw = read(MANIFEST)
    entries = [e for e in decode(manifest_raw)['entries'] if e['theme'] == 'logistics'
               and e.get('runtimeEnabled') is not False and e['category'] in ('hazards', 'platforms')]
    integrity.require(len(entries) == 26, 'SOURCE_COUNT')
    items = []
    for e in sorted(entries, key=lambda v: v['runtimeResourceKey']):
        key = e['runtimeResourceKey']
        path = 'assets/resources/' + key + '.png'
        integrity.portable(path)
        integrity.require(path.startswith(SOURCE_ROOT + '/'), 'SOURCE_SCOPE')
        png, meta_raw = read(path), read(path + '.meta')
        integrity.require(png[:16] == b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' and len(png) >= 33, 'PNG_HEADER')
        dimensions = list(struct.unpack('>II', png[16:24]))
        meta = decode(meta_raw)
        frames = [v for v in meta['subMetas'].values() if v['importer'] == 'sprite-frame']
        integrity.require(meta['importer'] == 'image' and len(frames) == 1, 'SOURCE_IMPORTER')
        frame = frames[0]
        data = frame['userData']
        integrity.require(dimensions == [data['rawWidth'], data['rawHeight']] and data['atlasUuid'] == '', 'SOURCE_GEOMETRY')
        items.append({'key': key, 'path': path, 'sha256': sha(png), 'bytes': len(png),
                      'meta_sha256_utf8_lf': sha(meta_raw, lf=True), 'uuid': meta['uuid'],
                      'sprite_frame_uuid': frame['uuid'], 'dimensions': dimensions,
                      'geometry': {k: data[k] for k in ('trimType', 'trimX', 'trimY', 'width', 'height',
                                  'rawWidth', 'rawHeight', 'pivotX', 'pivotY', 'rotated', 'packable', 'atlasUuid')},
                      'category': e['category'], 'role': e['role'], 'critical': e['critical'], 'levels': e['levels']})
    integrity.require(len({v['key'] for v in items}) == 26 and len({v['uuid'] for v in items}) == 26, 'SOURCE_DUPLICATE')
    return {'schema': 'mtr.atlas_source_inventory.v1', 'attempt_id': ATTEMPT,
            'source_anchor': ANCHOR, 'source_project_tree': TREE, 'hash_policy': INVENTORY_POLICY,
            'manifest': MANIFEST, 'manifest_sha256_utf8_lf': sha(manifest_raw, lf=True),
            'source_count': 26, 'items': items}


def validate_documents(protocol: dict, inventory: dict, anchored: dict, read) -> None:
    old_raw = read(integrity.PROTOCOL)
    integrity.require(sha(old_raw, lf=True) == OLD_PROTOCOL_SHA, 'PREDECESSOR_CHANGED')
    old = decode(old_raw)
    added = {'source_anchor_kind', 'source_project_tree', 'source_inventory', 'source_qualification_pins',
             'candidate_template', 'facts_at_preregistration'}
    integrity.require(set(protocol) == set(old) | added, 'PROTOCOL_SHAPE')
    changed = {'attempt_id', 'protocol_revision', 'revision_provenance', 'source_anchor',
               'source_inventory_sha256', 'candidate', 'web'}
    for key in set(old) - changed:
        integrity.require(canonical(protocol[key]) == canonical(old[key]), 'FROZEN_CRITERIA_CHANGED:' + key)
    integrity.require(protocol['attempt_id'] == ATTEMPT and type(protocol['protocol_revision']) is int
                      and protocol['protocol_revision'] == 1, 'PROTOCOL_IDENTITY')
    integrity.require(protocol['source_anchor'] == ANCHOR and protocol['source_project_tree'] == TREE
                      and protocol['source_anchor_kind'] == 'published_project_projection', 'SOURCE_ANCHOR')
    candidate = copy.deepcopy(old['candidate'])
    candidate['descriptor_uuid'] = UUID
    integrity.require(canonical(protocol['candidate']) == canonical(candidate), 'CANDIDATE_CHANGED')
    web = copy.deepcopy(old['web'])
    web['evidence_query'] = 'mtr_qa_atlas_evidence_id=a03_<pair>_<state>'
    integrity.require(canonical(protocol['web']) == canonical(web), 'WEB_COHORT_CHANGED')
    provenance = {'predecessor': integrity.PROTOCOL, 'predecessor_sha256_utf8_lf': OLD_PROTOCOL_SHA,
                  'predecessor_attempt': integrity.ATTEMPT, 'predecessor_status': 'HOLD_zero_samples_NOT_RUN',
                  'reason': 'new_reviewed_26_source_art_inventory_requires_new_attempt_not_repinning_frozen_attempt02'}
    integrity.require(canonical(protocol['revision_provenance']) == canonical(provenance), 'PROVENANCE_CHANGED')
    facts = {'baseline_built': False, 'candidate_built': False, 'all_file_seals_created': False,
             'input_admission': False, 'timed_android_samples': 0, 'timed_web_samples': 0,
             'experiment_runtime': 'NOT_RUN', 'release_accepted': False}
    integrity.require(canonical(protocol['facts_at_preregistration']) == canonical(facts), 'NOT_ADMISSION')
    integrity.require(protocol['source_inventory'] == INVENTORY, 'INVENTORY_PATH')
    integrity.require(canonical(inventory) == canonical(anchored), 'INVENTORY_ANCHOR_MISMATCH')
    integrity.require(sha(read(INVENTORY), lf=True) == protocol['source_inventory_sha256'], 'INVENTORY_PIN')
    integrity.require(canonical(source_inventory(read)) == canonical(anchored), 'SOURCE_ANCHOR_MISMATCH')
    pins = protocol['tooling_pins'] + protocol['source_qualification_pins']
    integrity.require([v['path'] for v in protocol['source_qualification_pins']] == [
        'docs/global_modernization/v3/M04/M04_C_LOGISTICS_FAMILY_SOURCE_QA_20261002.json',
        'docs/qa/LOGISTICS_FAMILY_REVIEWED_SOURCE_PROMPTS_20261002.json',
        'tools/asset_generation/reviewed_runtime_sources.json'], 'QUALIFICATION_SCOPE')
    pins += [{'path': protocol['acceptance_contract'], 'sha256_utf8_lf': protocol['acceptance_contract_sha256_utf8_lf']}]
    for pin in pins:
        integrity.require(set(pin) == {'path', 'sha256_utf8_lf'} and sha(read(pin['path']), lf=True) == pin['sha256_utf8_lf'],
                          'INPUT_PIN_CHANGED:' + pin['path'])
    template = protocol['candidate_template']
    integrity.require(set(template) == {'path', 'sha256_utf8_lf', 'only_permitted_change'} and template['path'] == TEMPLATE
                      and template['only_permitted_change'] == 'uuid_to_registered_attempt03_descriptor_uuid'
                      and sha(read(TEMPLATE), lf=True) == template['sha256_utf8_lf'], 'TEMPLATE_CHANGED')


def validate(project: Path) -> dict:
    project = integrity.guarded(project, directory=True)
    read = lambda path: read_file(project, path)
    raw = read(PROTOCOL)
    integrity.require(sha(raw, lf=True) == PROTOCOL_SHA, 'PREREGISTRATION_CHANGED')
    integrity.require(git(project, 'rev-parse', ANCHOR + '^{tree}').decode().strip() == TREE, 'PROJECT_TREE_CHANGED')
    anchored = source_inventory(lambda path: anchored_file(project, path))
    protocol, inventory = decode(raw), decode(read(INVENTORY))
    validate_documents(protocol, inventory, anchored, read)
    # A future candidate may add exactly this descriptor pair. It never alters
    # the immutable preregistration facts or earns runtime/admission acceptance.
    root = integrity.guarded(project / SOURCE_ROOT, directory=True)
    found, pending = set(), [root]
    while pending:
        directory = pending.pop()
        integrity.guarded(directory, directory=True)
        for path in directory.iterdir():
            is_directory = path.is_dir()
            integrity.regular_info(path, directory=is_directory)
            if is_directory:
                pending.append(path)
            elif '.pac' in path.name:
                found.add(path.relative_to(project).as_posix())
    integrity.require(found in (set(), {DESCRIPTOR, DESCRIPTOR + '.meta'}), 'UNREGISTERED_DESCRIPTOR')
    if found:
        integrity.require(decode(read(DESCRIPTOR)) == {'__type__': 'cc.SpriteAtlas'}, 'DESCRIPTOR_BODY')
        template = decode(read(TEMPLATE))
        template['uuid'] = UUID
        integrity.require(canonical(decode(read(DESCRIPTOR + '.meta'))) == canonical(template), 'DESCRIPTOR_TEMPLATE')
    return {'status': 'PASS', 'acceptance_layer': 'preregistration_and_source_integrity_only',
            'attempt_id': ATTEMPT, 'source_count': 26, 'measurement_tool_pins': 9,
            'descriptor_state': 'present_exact_not_admitted' if found else 'absent',
            'input_admission': False, 'experiment_runtime': 'NOT_RUN', 'release_accepted': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--project-root', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.project_root), sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error), 'input_admission': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
