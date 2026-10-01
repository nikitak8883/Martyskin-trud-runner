"""Byte-integrity seals for quiescent staged experiment files, NOT input admission."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata
import uuid

PROTOCOL = 'docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_LOGISTICS_ATTEMPT02_PROTOCOL.json'
ATTEMPT = 'logistics-attempt02-20261001'
MAX_SEAL_BYTES = 32 * 1024 * 1024
MAX_FILES = 100000
HASH = re.compile(r'[a-f0-9]{64}\Z')
RESERVED = re.compile(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?\Z', re.I)


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError(code)


def portable(value: str) -> str:
    require(isinstance(value, str) and bool(value), 'PATH_TYPE')
    p = PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix() == value, 'PATH_CANONICAL')
    for part in p.parts:
        require(part not in ('.', '..') and len(part) <= 255, 'PATH_COMPONENT')
        require(not re.search(r'[\x00-\x1f\x7f\\:<>"|?*]', part), 'PATH_PORTABLE')
        require(not part.endswith((' ', '.')) and not RESERVED.fullmatch(part), 'PATH_WINDOWS')
        require(unicodedata.normalize('NFC', part) == part, 'PATH_UNICODE')
    require(bool(p.parts), 'PATH_EMPTY')
    return value


def regular_info(path: Path, *, directory: bool = False):
    info = path.lstat()
    require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, 'st_file_attributes', 0) & 0x400), 'LINK_OR_REPARSE')
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'FILE_TYPE')
    if not directory:
        require(info.st_nlink == 1, 'HARDLINK')
    return info


def guarded(path: Path, *, directory: bool = False):
    path = Path(os.path.abspath(path))
    for parent in reversed(path.parents):
        regular_info(parent, directory=True)
    regular_info(path, directory=directory)
    return path


def scoped(project: Path, relative: str, *, exists: bool = True) -> Path:
    portable(relative)
    require(PurePosixPath(relative).parts[0] == 'temp' and len(PurePosixPath(relative).parts) > 1, 'TEMP_SCOPE_REQUIRED')
    project = guarded(project, directory=True)
    path = project / relative
    if exists:
        guarded(path, directory=path.is_dir())
    else:
        guarded(path.parent, directory=True)
        require(not path.exists() and not path.is_symlink(), 'OUTPUT_EXISTS')
    return path


def fingerprint(info):
    # Windows ctime is deprecated and can differ between path/handle stats on
    # the qualified Python3.13 host. Use explicit birthtime there, not ctime.
    # Content hash + identity/size/mtime + two scans remain mandatory.
    metadata_time = getattr(info, 'st_birthtime_ns', None) if os.name == 'nt' else info.st_ctime_ns
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, metadata_time


def hash_regular(path: Path) -> tuple[int, str]:
    guarded(path)
    before = regular_info(path)
    require(before.st_ino != 0, 'FILE_ID_UNAVAILABLE')
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as stream:
        require(fingerprint(os.fstat(stream.fileno())) == fingerprint(before), 'FILE_CHANGED_OPEN')
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
        require(fingerprint(os.fstat(stream.fileno())) == fingerprint(before), 'FILE_CHANGED_READ')
    guarded(path)
    require(fingerprint(regular_info(path)) == fingerprint(before), 'FILE_CHANGED_PATH')
    return before.st_size, digest.hexdigest()


def inventory(root: Path) -> list[dict]:
    guarded(root, directory=True)
    records = []
    seen = set()
    pending = [root]
    while pending:
        current = pending.pop()
        regular_info(current, directory=True)
        for path in sorted(current.iterdir(), key=lambda p: p.name):
            name = portable(path.relative_to(root).as_posix())
            require(name.casefold() not in seen, 'CASE_ALIAS')
            seen.add(name.casefold())
            require(len(seen) <= MAX_FILES, 'ENTRY_LIMIT')
            info = path.lstat()
            if stat.S_ISDIR(info.st_mode):
                regular_info(path, directory=True)
                pending.append(path)
            else:
                size, digest = hash_regular(path)
                records.append({'path': name, 'bytes': size, 'sha256': digest})
                require(len(records) <= MAX_FILES, 'FILE_LIMIT')
    require(bool(records), 'EMPTY_STAGING')
    return sorted(records, key=lambda r: r['path'])


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def bounded_bytes(path: Path) -> bytes:
    regular_info(path)
    with path.open('rb') as stream:
        raw = stream.read(MAX_SEAL_BYTES + 1)
    require(len(raw) <= MAX_SEAL_BYTES, 'SEAL_SIZE_LIMIT')
    return raw


def protocol_hash(project: Path, expected: str) -> str:
    require(isinstance(expected, str) and HASH.fullmatch(expected) is not None, 'PROTOCOL_PIN_REQUIRED')
    path = guarded(project / PROTOCOL)
    require(path.stat().st_size <= MAX_SEAL_BYTES, 'PROTOCOL_SIZE_LIMIT')
    raw = bounded_bytes(path)
    digest = hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()
    require(digest == expected, 'PROTOCOL_CHANGED')
    p = json.loads(raw.decode('utf-8'), object_pairs_hook=no_duplicate_keys)
    require(p['attempt_id'] == ATTEMPT and type(p['protocol_revision']) is int and p['protocol_revision'] == 4, 'PROTOCOL_IDENTITY')
    return digest


def make_seal(project: Path, staging: str, expected_protocol: str) -> dict:
    pin = protocol_hash(project, expected_protocol)
    root = scoped(project, staging)
    first = inventory(root)
    require(inventory(root) == first, 'STAGING_CHANGED')
    require(protocol_hash(project, expected_protocol) == pin, 'PROTOCOL_CHANGED')
    return {'schema': 'mtr.atlas_input_integrity.v1', 'attempt_id': ATTEMPT,
            'protocol_revision': 4, 'protocol_sha256_utf8_lf': pin,
            'staging_root': staging, 'input_admission': False,
            'experiment_runtime': 'NOT_RUN', 'files': first,
            'file_count': len(first), 'total_bytes': sum(r['bytes'] for r in first)}


def encoded(seal: dict) -> bytes:
    raw = (json.dumps(seal, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    require(len(raw) <= MAX_SEAL_BYTES, 'SEAL_SIZE_LIMIT')
    return raw


def publish(project: Path, staging: str, output: str, raw: bytes) -> None:
    require(type(raw) is bytes and len(raw) <= MAX_SEAL_BYTES, 'SEAL_SIZE_LIMIT')
    root = scoped(project, staging)
    target = scoped(project, output, exists=False)
    require(target != root and root not in target.parents, 'OUTPUT_INSIDE_STAGING')
    temporary = target.with_name(target.name + '.pending-' + uuid.uuid4().hex)
    # Exclusive temporary creation + hard-link publication: atomic visibility,
    # no overwrite. Unsupported filesystems fail closed; no copy/replace fallback.
    owned = None
    try:
        with temporary.open('xb') as stream:
            info = os.fstat(stream.fileno())
            owned = (info.st_dev, info.st_ino)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        guarded(target.parent, directory=True)
        os.link(temporary, target)
    finally:
        if owned is not None:
            info = temporary.lstat()
            require((info.st_dev, info.st_ino) == owned and stat.S_ISREG(info.st_mode), 'TEMP_OWNERSHIP_CHANGED')
            temporary.unlink()


def verify(project: Path, staging: str, seal_path: str, expected_seal: str, expected_protocol: str) -> dict:
    require(isinstance(expected_seal, str) and HASH.fullmatch(expected_seal) is not None, 'SEAL_PIN_REQUIRED')
    path = scoped(project, seal_path)
    regular_info(path)
    require(path.stat().st_size <= MAX_SEAL_BYTES, 'SEAL_SIZE_LIMIT')
    raw = bounded_bytes(path)
    require(hashlib.sha256(raw).hexdigest() == expected_seal, 'SEAL_CHANGED')
    seal = json.loads(raw.decode('utf-8'), object_pairs_hook=no_duplicate_keys)
    require(type(seal) is dict and set(seal) == {'schema', 'attempt_id', 'protocol_revision', 'protocol_sha256_utf8_lf', 'staging_root', 'input_admission', 'experiment_runtime', 'files', 'file_count', 'total_bytes'}, 'SEAL_SCHEMA')
    require(seal['schema'] == 'mtr.atlas_input_integrity.v1' and seal['input_admission'] is False and seal['experiment_runtime'] == 'NOT_RUN', 'NOT_ADMISSION')
    expected = make_seal(project, staging, expected_protocol)
    # Exact typed canonical representation also rejects bool-as-int, duplicate,
    # omitted/unlisted files, unknown keys, path aliases and unsorted inventories.
    require(encoded(seal) == encoded(expected), 'INVENTORY_CHANGED')
    require(hash_regular(path)[1] == expected_seal, 'SEAL_CHANGED')
    return {'status': 'PASS', 'acceptance_layer': 'byte_integrity_only', 'input_admission': False,
            'experiment_runtime': 'NOT_RUN', 'release_accepted': False,
            'file_count': expected['file_count'], 'total_bytes': expected['total_bytes']}


def main(argv=None) -> int:
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('mode', choices=('seal', 'verify'))
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--staging-root', required=True)
    parser.add_argument('--expected-protocol-sha256', required=True)
    parser.add_argument('--seal', required=True)
    parser.add_argument('--expected-seal-sha256')
    keys = [a.split('=', 1)[0] for a in argv if a.startswith('--')]
    if len(keys) != len(set(keys)):
        parser.error('Duplicate options are forbidden.')
    args = parser.parse_args(argv)
    try:
        if args.mode == 'seal':
            require(args.expected_seal_sha256 is None, 'SEAL_MODE_PIN_NOT_ALLOWED')
            raw = encoded(make_seal(args.project_root, args.staging_root, args.expected_protocol_sha256))
            publish(args.project_root, args.staging_root, args.seal, raw)
            result = {'status': 'SEALED', 'seal_sha256': hashlib.sha256(raw).hexdigest(),
                      'acceptance_layer': 'byte_integrity_only', 'input_admission': False,
                      'experiment_runtime': 'NOT_RUN', 'release_accepted': False}
        else:
            result = verify(args.project_root, args.staging_root, args.seal,
                            args.expected_seal_sha256, args.expected_protocol_sha256)
        print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as error:
        print(json.dumps({'status': 'FAIL', 'error': str(error), 'input_admission': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
