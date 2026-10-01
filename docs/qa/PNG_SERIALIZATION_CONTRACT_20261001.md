# Byte-preserving PNG portability repair

Scope: source-only QA/asset tooling, not new art, runtime code, atlas acceptance,
signing or deployment. Original PNG/meta/provenance/index pins stay unchanged.

## Diagnosis and exact reproduction

Hosted source `bfeb49a46a070c83c6c7db80ffbac787e465fe84`, run `36849094035`:
Windows `33/34`, Linux `31/34`. The common atlas CLI failure is an early browser
package import. Linux also fails byte-exact PNG normalization and the M04-B index.
Rollback source projection and the four earlier fixes pass on both real runners.

Pillow12.3.0 Windows PNG codec reports `1.3.1.zlib-ng`; Linux reports `1.3.1`.
Linux's separate `zlib_ng` feature does not mean its PNG encoder uses that codec;
the shared-library probe resolves system `libz.so.1`. All29 pages and the reviewed
sprite have equal decoded RGBA AND equal decompressed PNG filter rows. Their
compressed bytes differ. The59 index differences are sheet SHA/size and dependent
HTML SHA; source records, coverage, font pixels, dimensions and categories match.

Local Windows laboratory: Python3.13.14. WSL laboratory: Python3.14.4 with exact
Pillow12.3.0 in a test-owned target directory, not global Python/inference. This
is diagnostic evidence, not hosted Python3.13 acceptance. Failed test-venv setup
lacking ensurepip did not trigger global apt/Python changes.

The exact `zlib-ng==1.0.0` binding, build/runtime codec2.2.5, reproduced complete
IDAT streams of all30 originals on BOTH hosts before implementation. Different
codec versions are not assumed equivalent. Parameters match the [official Pillow
encoder](https://github.com/python-pillow/Pillow/blob/12.3.0/src/libImaging/ZipEncode.c);
the [binding documentation](https://github.com/pycompression/python-zlib-ng)
defines its compressor API.

## Shared serializer and safeguards

`tools/asset_generation/canonical_png.py` retains Pillow12.3.0 transformations and
adaptive filters; explicit level9/window15/memory9/filtered strategy and65536-byte
IDAT chunks reproduce original bytes. Missing/different versions block, with no
system-compressor fallback. Both normalization and sheet rendering use it.

Signature, CRC, chunk order, 8-bit RGB(A), row size/filter, stream termination and
bounded decompression are validated before output. Ancillary metadata, palettes,
interlace and invalid inputs are rejected, never silently dropped. Limits are
16Mi pixels /128MiB container. Only explicit test/tool outputs are written.

Runtime PNGs are NOT rewritten. Reviewed sprite SHA remains
`0A430E298AF44E9615DB233AE1847FBDAFAAB73792AD30AE190D435D09504933`;
canonical index SHA remains
`923CB83556926935BA3591D6BAE6BE9498F6C7EB3E66DA235A4F09E818154827`.
Original source/meta SHA, UUID, provenance, alpha/trim dimensions, inventory,
experiment thresholds, schedules and baseline receipts are not refreshed.

## Receipt identity and acceptance boundary

Ignored repository-local evidence: `temp/ci-portability-20261001`.

- Windows diagnosis SHA `7D5D8D5920E33D0B71CAEC43166463DEB5B2AC654E4F3BE681D2E6301BA50A12`.
- Linux diagnosis SHA `2E58A1ADF9440A0D98E3B567A7AC6746588959A6A00650ACC0B78EF4681D04BC`.
- Windows exact codec probe SHA `895684CB213D0FE7BF3F542923DD175C455F39BCBA706301A6BB20B846BE7AD7`.
- Linux exact codec probe SHA `B812467FF3E3F1C5DE6887842279D50BBB112C1132DCA4EBAEE5F2CC911E73C6`.
- Failed hosted Linux report SHA `3CC3764B0B4AFEBFB0A9352CAA9B89EDD330DB8629C0BC82CFDA6E8C71F58C58`.
- Failed hosted Windows report SHA `FB34E0E8411FC21635462F960C123AAFD360ED9B0FA57330F06B425374CD99A6`.

Four targeted cycles bind helper/consumer/test/lock and unchanged golden inputs.
Final clean static/hosted receipts must pin the published commit; they cannot be
inferred from laboratory tests or embedded as self-referential commit hashes.
Runtime Web/Android QA is NOT_RUN for this tools-only slice. Silence is mandatory.
Native bootstrap, attempt02 inputs/timing and Release remain open.

Rollback: revert only this scoped source commit; reuse the prior lock's qualified
cache if necessary. Never overwrite/delete predecessor logs, goldens, atlas
rejection, unrelated files or global configuration.
