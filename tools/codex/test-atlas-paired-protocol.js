'use strict';
const assert = require('assert/strict');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../..');
const protocolPath = 'docs/global_modernization/v3/M04/M04_C_FAMILY_THEME_LOGISTICS_ATTEMPT02_PROTOCOL.json';
const protocol = JSON.parse(fs.readFileSync(path.join(root, protocolPath), 'utf8'));
const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(path.join(root, file), 'utf8').replace(/\r\n/g, '\n')).digest('hex');
const hashes = new Map(protocol.tooling_pins.map((pin) => [pin.path, sha(pin.path)]));
hashes.set(protocol.acceptance_contract, sha(protocol.acceptance_contract));

function validate(record, observedHashes) {
    const errors = [];
    const check = (ok, code) => { if (!ok) errors.push(code); };
    check(record.schema === 'mtr.atlas_paired_experiment_protocol.v1' && record.unit_id === 'M04-C-FAMILY-THEME-LOGISTICS', 'identity');
    check(record.status_at_preregistration === 'protocol_only_inputs_not_ready_runtime_not_run', 'not_acceptance');
    check(JSON.stringify(record.acceptance_overrides) === '{}', 'no_gate_overrides');
    check(observedHashes.get(record.acceptance_contract) === record.acceptance_contract_sha256_utf8_lf, 'acceptance_pin');
    check(Array.isArray(record.tooling_pins) && record.tooling_pins.length === 9 && new Set(record.tooling_pins.map(p => p.path)).size === 9, 'tooling_set');
    for (const pin of record.tooling_pins || []) check(observedHashes.get(pin.path) === pin.sha256_utf8_lf, `tooling_pin:${pin.path}`);
    check(JSON.stringify(record.pair_order?.map(p => [p.id, ...p.order])) === JSON.stringify([
        ['p01', 'baseline', 'candidate'], ['p02', 'candidate', 'baseline'],
        ['p03', 'baseline', 'candidate'], ['p04', 'candidate', 'baseline'],
    ]), 'balanced_frozen_order');
    check(record.input_admission?.verify_input_hashes_before_and_after_each_state === true && record.input_admission?.builds_and_staging_complete_before_measurements === true && record.input_admission?.first_attempt_or_tooling_qualification_samples_reusable === false, 'input_admission');
    check(record.android?.serial === 'emulator-5554' && record.android?.user === 0 && record.android?.physical_device_allowed === false, 'emulator_only');
    check(record.android?.media_stream === 3 && record.android?.media_volume === 0 && record.android?.guard_before_every_runtime_run === true && ['-no-audio', '-no-snapshot-load', '-no-snapshot-save'].every(flag => record.android?.startup_flags?.includes(flag)), 'silent_cold_boot');
    check(record.android?.cold_boots === 8 && record.android?.sample_count === 16 && record.android?.settle_after_install_seconds === 30 && record.android?.wait_between_cohorts_seconds === 20 && record.android?.force_stop_before_each_cohort === true, 'android_samples');
    check(record.android?.cache_definition.includes('neither_disk_cold_nor_shader_cold_nor_in_process_warm_is_claimed'), 'honest_cache_definition');
    check(record.web?.sample_count === 8 && record.web?.new_chromium_process_and_context_per_sample === true && record.web?.emulator_stopped_for_all_web_samples === true && record.web?.startup_flags?.includes('--mute-audio'), 'web_symmetry_and_silence');
    check(record.evaluation?.paired_cohort_comparisons === 8 && record.evaluation?.checks_per_comparison === 63 && record.evaluation?.retain_every_sample_in_fixed_order === true && record.evaluation?.best_of_repeat_exclusion_or_outlier_removal_allowed === false && record.evaluation?.web_samples_double_counted_as_independent === false, 'all_sample_decision');
    check(JSON.stringify(record.evaluation?.candidate_independent_repeat_mapping) === JSON.stringify({p01: 'p02', p02: 'p03', p03: 'p04', p04: 'p01'}), 'independent_repeats');
    return errors;
}
assert.deepEqual(validate(protocol, hashes), []);
assert.equal(protocol.protocol_revision, 3);
assert.equal(sha(protocol.revision_provenance.predecessor), protocol.revision_provenance.predecessor_sha256_utf8_lf);
assert.equal(protocol.revision_provenance.timed_attempt02_samples_observed_before_revision, 0);
const predecessor = JSON.parse(fs.readFileSync(path.join(root, protocol.revision_provenance.predecessor), 'utf8'));
assert.equal(predecessor.protocol_revision, 2);
assert.equal(sha(predecessor.revision_provenance.predecessor), predecessor.revision_provenance.predecessor_sha256_utf8_lf);
for (const field of ['acceptance_overrides', 'pair_order', 'android', 'web', 'evaluation', 'input_admission']) assert.deepEqual(protocol[field], predecessor[field]);
let count = 4;
const mutations = [
    [p => { p.acceptance_overrides.load_elapsed_ms = 9999; }, 'no_gate_overrides'],
    [p => { p.pair_order[1].order.reverse(); }, 'balanced_frozen_order'],
    [p => { p.input_admission.first_attempt_or_tooling_qualification_samples_reusable = true; }, 'input_admission'],
    [p => { p.android.physical_device_allowed = true; }, 'emulator_only'],
    [p => { p.android.media_volume = 1; }, 'silent_cold_boot'],
    [p => { p.android.startup_flags.pop(); }, 'silent_cold_boot'],
    [p => { p.android.sample_count = 2; }, 'android_samples'],
    [p => { p.android.cache_definition = 'disk-cold'; }, 'honest_cache_definition'],
    [p => { p.web.emulator_stopped_for_all_web_samples = false; }, 'web_symmetry_and_silence'],
    [p => { p.evaluation.best_of_repeat_exclusion_or_outlier_removal_allowed = true; }, 'all_sample_decision'],
    [p => { p.evaluation.candidate_independent_repeat_mapping.p01 = 'p01'; }, 'independent_repeats'],
    [p => { p.tooling_pins[0].sha256_utf8_lf = 'wrong'; }, 'tooling_pin:'],
    [p => { p.acceptance_contract_sha256_utf8_lf = 'wrong'; }, 'acceptance_pin'],
];
for (const [mutate, code] of mutations) {
    const changed = structuredClone(protocol);
    mutate(changed);
    assert.ok(validate(changed, hashes).some(error => error.startsWith(code)), `Negative control accepted: ${code}`);
    count++;
}
process.stdout.write(JSON.stringify({ status: 'PASS', testsPassed: count, testsTotal: count, acceptance: false, inputAdmission: 'NOT_RUN', experimentRuntime: 'NOT_RUN' }) + '\n');
