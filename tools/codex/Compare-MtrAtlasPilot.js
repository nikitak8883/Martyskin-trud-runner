#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

function parseArguments(argv) {
    const values = new Map();
    for (let index = 0; index < argv.length; index += 2) {
        const key = argv[index];
        const value = argv[index + 1];
        if (!key?.startsWith('--') || value === undefined) throw new Error(`Invalid argument near ${key || '<end>'}.`);
        values.set(key, value);
    }
    return {
        projectRoot: values.get('--project-root') || process.cwd(),
        contract: values.get('--contract') || 'docs/global_modernization/v3/M04/M04_C_PILOT_CONTRACT.json',
        baselineRoot: values.get('--baseline-root') || 'temp/m04-c-pilot/baseline',
        candidateRoot: values.get('--candidate-root') || 'temp/m04-c-pilot/candidate',
        visualReport: values.get('--visual-report') || 'temp/m04-c-pilot/comparison/visual-parity.json',
        output: values.get('--output') || 'temp/m04-c-pilot/comparison/acceptance.json',
    };
}

function resolveContained(projectRoot, candidate, label) {
    const root = path.resolve(projectRoot);
    const resolved = path.resolve(root, candidate);
    const relative = path.relative(root, resolved);
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`${label} escapes project root.`);
    return resolved;
}

function readJson(file) {
    const value = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error(`Expected JSON object: ${file}`);
    return value;
}

function writeJsonAtomic(outputPath, value) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    const temporary = `${outputPath}.tmp-${process.pid}-${Date.now()}`;
    fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
    fs.renameSync(temporary, outputPath);
}

function artifactMetric(report, field) {
    if (field === 'runtime') return report.runtime || report.all;
    return report[field];
}

function isObject(value) {
    return Boolean(value) && !Array.isArray(value) && typeof value === 'object';
}

function isFiniteNumber(value, { minimum = Number.NEGATIVE_INFINITY, integer = false } = {}) {
    return Number.isFinite(value) && value >= minimum && (!integer || Number.isInteger(value));
}

function metricEnvelopeValid(report, phase, platform, contract) {
    const metric = report?.metric;
    const expectedRuntimeSchema = platform === 'web'
        ? 'mtr.web_atlas_pilot.v1'
        : 'mtr.android_atlas_pilot.v1';
    const expectedMetricPlatform = platform === 'web' ? 'web' : 'android';
    const ranges = ['draws', 'textureMemoryMb', 'bufferMemoryMb', 'fps'];
    return isObject(report)
        && report.schema === expectedRuntimeSchema
        && report.status === 'pass'
        && report.phase === phase
        && isObject(metric)
        && metric.contract === 'mtr.atlas_pilot_runtime_metric'
        && metric.schemaVersion === 2
        && metric.atlasId === contract.candidate.atlas_id
        && metric.platform === expectedMetricPlatform
        && metric.sourceCount === contract.candidate.source_count
        && isFiniteNumber(metric.sourceTextureCount, { minimum: 1, integer: true })
        && isFiniteNumber(metric.drawTextureCount, { minimum: 1, integer: true })
        && isFiniteNumber(metric.dynamicAtlasPackedCount, { minimum: 0, integer: true })
        && isFiniteNumber(metric.loadElapsedMs, { minimum: 0 })
        && isObject(metric.aggregate)
        && metric.aggregate.sampleCount === contract.measurement_protocol.sample_count
        && ranges.every((name) => {
            const range = metric.aggregate[name];
            const minimum = name === 'draws' || name === 'fps' ? Number.EPSILON : 0;
            return isObject(range)
                && isFiniteNumber(range.min, { minimum })
                && isFiniteNumber(range.median, { minimum })
                && isFiniteNumber(range.max, { minimum })
                && range.min <= range.median
                && range.median <= range.max;
        });
}

function artifactEnvelopeValid(report, phase, platform, contract) {
    return isObject(report)
        && report.schema === 'mtr.atlas_pilot_artifact_metric.v1'
        && report.phase === phase
        && report.platform === platform
        && typeof report.buildRoot === 'string'
        && report.buildRoot.length > 0
        && report.candidateSourceCount === contract.candidate.source_count
        && isFiniteNumber(report.candidateUuidArtifactCount, { minimum: 0, integer: true })
        && isObject(report.all)
        && isFiniteNumber(report.all.totalBytes, { minimum: 1 })
        && isObject(report.resources)
        && isFiniteNumber(report.resources.totalBytes, { minimum: 1 });
}

function compare(options) {
    const projectRoot = path.resolve(options.projectRoot);
    const contract = readJson(resolveContained(projectRoot, options.contract, '--contract'));
    const baselineRoot = resolveContained(projectRoot, options.baselineRoot, '--baseline-root');
    const candidateRoot = resolveContained(projectRoot, options.candidateRoot, '--candidate-root');
    const visual = readJson(resolveContained(projectRoot, options.visualReport, '--visual-report'));
    const checks = [];
    const add = (id, platform, actual, expected, passed) => checks.push({ id, platform, actual, expected, passed: Boolean(passed) });
    const runtimeByPlatform = {};
    const artifactsByPlatform = {};

    add(
        'visual_report_envelope',
        'all',
        { schema: visual.schema, status: visual.status, platforms: Object.keys(visual.comparisons || {}).sort() },
        { schema: 'mtr.atlas_pilot_visual_parity.v1', status: 'pass', platforms: ['android_emulator', 'web'] },
        visual.schema === 'mtr.atlas_pilot_visual_parity.v1'
            && visual.status === 'pass'
            && isObject(visual.comparisons)
            && ['android_emulator', 'web'].every((platform) => visual.comparisons[platform]?.status === 'pass'),
    );

    for (const [platform, directory] of [['web', 'web'], ['android_emulator', 'android']]) {
        const baselineRuntime = readJson(path.join(baselineRoot, directory, 'runtime.json'));
        const candidateRuntime = readJson(path.join(candidateRoot, directory, 'runtime.json'));
        const baselineArtifacts = readJson(path.join(baselineRoot, directory, 'artifacts.json'));
        const candidateArtifacts = readJson(path.join(candidateRoot, directory, 'artifacts.json'));
        const baseline = baselineRuntime.metric;
        const candidate = candidateRuntime.metric;
        runtimeByPlatform[platform] = { baseline, candidate };
        artifactsByPlatform[platform] = { baseline: baselineArtifacts, candidate: candidateArtifacts };

        const baselineRuntimeValid = metricEnvelopeValid(baselineRuntime, 'baseline', platform, contract);
        const candidateRuntimeValid = metricEnvelopeValid(candidateRuntime, 'candidate', platform, contract);
        add('baseline_runtime_envelope', platform, {
            schema: baselineRuntime.schema,
            status: baselineRuntime.status,
            phase: baselineRuntime.phase,
            atlasId: baseline?.atlasId,
            metricPlatform: baseline?.platform,
        }, 'frozen baseline runtime identity and finite metric envelope', baselineRuntimeValid);
        add('candidate_runtime_envelope', platform, {
            schema: candidateRuntime.schema,
            status: candidateRuntime.status,
            phase: candidateRuntime.phase,
            atlasId: candidate?.atlasId,
            metricPlatform: candidate?.platform,
        }, 'candidate runtime identity and finite metric envelope', candidateRuntimeValid);
        add('runtime_status', platform, candidateRuntime.status, 'pass', candidateRuntime.status === 'pass');
        add('metric_schema_version', platform, candidate?.schemaVersion, 2, candidate?.schemaVersion === 2);
        add('baseline_source_texture_count', platform, baseline?.sourceTextureCount,
            contract.acceptance.source_texture_count.baseline_by_platform[platform],
            baseline?.sourceTextureCount === contract.acceptance.source_texture_count.baseline_by_platform[platform]);
        add('baseline_draw_texture_count', platform, baseline?.drawTextureCount,
            contract.acceptance.draw_texture_count.baseline_by_platform[platform],
            baseline?.drawTextureCount === contract.acceptance.draw_texture_count.baseline_by_platform[platform]);
        add('baseline_dynamic_atlas_packed_count', platform, baseline?.dynamicAtlasPackedCount,
            contract.acceptance.dynamic_atlas_packed_count.baseline_by_platform[platform],
            baseline?.dynamicAtlasPackedCount === contract.acceptance.dynamic_atlas_packed_count.baseline_by_platform[platform]);
        add('source_texture_count', platform, candidate?.sourceTextureCount,
            contract.acceptance.source_texture_count.candidate_expected_by_platform[platform],
            candidate?.sourceTextureCount === contract.acceptance.source_texture_count.candidate_expected_by_platform[platform]);
        add('draw_texture_count', platform, candidate?.drawTextureCount,
            contract.acceptance.draw_texture_count.candidate_expected_by_platform[platform],
            candidate?.drawTextureCount === contract.acceptance.draw_texture_count.candidate_expected_by_platform[platform]);
        add('dynamic_atlas_packed_count', platform, candidate?.dynamicAtlasPackedCount,
            contract.acceptance.dynamic_atlas_packed_count.candidate_expected_by_platform[platform],
            candidate?.dynamicAtlasPackedCount === contract.acceptance.dynamic_atlas_packed_count.candidate_expected_by_platform[platform]);

        const baselineDraws = baseline?.aggregate?.draws?.median;
        const candidateDraws = candidate?.aggregate?.draws?.median;
        if (platform === 'web') {
            const allowed = baselineDraws + contract.acceptance.draw_calls.web.maximum_absolute_increase;
            add('draw_calls_web_non_regression', platform, candidateDraws, `<= ${allowed}`, candidateDraws <= allowed);
        } else {
            const absoluteReduction = baselineDraws - candidateDraws;
            const relativeReduction = absoluteReduction / baselineDraws;
            const rule = contract.acceptance.draw_calls.android_emulator;
            add('draw_calls_android_absolute_gain', platform, absoluteReduction,
                `>= ${rule.minimum_absolute_reduction}`, absoluteReduction >= rule.minimum_absolute_reduction);
            add('draw_calls_android_relative_gain', platform, Number(relativeReduction.toFixed(6)),
                `>= ${rule.minimum_relative_reduction}`, relativeReduction >= rule.minimum_relative_reduction);
        }

        const loadRule = contract.acceptance.load_elapsed_ms;
        const loadLimit = baseline?.loadElapsedMs * (1 + loadRule.maximum_relative_increase) + loadRule.maximum_absolute_slack_ms;
        add('load_elapsed_ms', platform, candidate?.loadElapsedMs, `<= ${loadLimit}`,
            isFiniteNumber(loadLimit, { minimum: 0 }) && isFiniteNumber(candidate?.loadElapsedMs, { minimum: 0 })
                && candidate.loadElapsedMs <= loadLimit);

        for (const [metricName, ruleName] of [['textureMemoryMb', 'texture_memory_mb'], ['bufferMemoryMb', 'buffer_memory_mb']]) {
            const baselineValue = baseline?.aggregate?.[metricName]?.median;
            const candidateValue = candidate?.aggregate?.[metricName]?.median;
            const rule = contract.acceptance[ruleName];
            add(`${ruleName}_relative`, platform, candidateValue, `<= ${baselineValue * (1 + rule.maximum_relative_increase)}`,
                isFiniteNumber(baselineValue, { minimum: 0 }) && isFiniteNumber(candidateValue, { minimum: 0 })
                    && candidateValue <= baselineValue * (1 + rule.maximum_relative_increase));
            add(`${ruleName}_absolute`, platform, candidateValue, `<= ${baselineValue + rule.maximum_absolute_increase_mb}`,
                isFiniteNumber(baselineValue, { minimum: 0 }) && isFiniteNumber(candidateValue, { minimum: 0 })
                    && candidateValue <= baselineValue + rule.maximum_absolute_increase_mb);
        }

        const baselineFps = baseline?.aggregate?.fps?.median;
        const candidateFps = candidate?.aggregate?.fps?.median;
        const fpsRule = contract.acceptance.fps;
        add('fps_relative', platform, candidateFps, `>= ${baselineFps * (1 - fpsRule.maximum_relative_drop)}`,
            candidateFps >= baselineFps * (1 - fpsRule.maximum_relative_drop));
        add('fps_absolute', platform, candidateFps, `>= ${baselineFps - fpsRule.maximum_absolute_drop}`,
            candidateFps >= baselineFps - fpsRule.maximum_absolute_drop);

        const sizeRule = contract.acceptance.artifact_size;
        const baselineArtifactsValid = artifactEnvelopeValid(baselineArtifacts, 'baseline', platform, contract);
        const candidateArtifactsValid = artifactEnvelopeValid(candidateArtifacts, 'candidate', platform, contract);
        add('baseline_artifact_envelope', platform, {
            schema: baselineArtifacts.schema,
            phase: baselineArtifacts.phase,
            platform: baselineArtifacts.platform,
            candidateSourceCount: baselineArtifacts.candidateSourceCount,
        }, 'frozen baseline artifact identity', baselineArtifactsValid);
        add('candidate_artifact_envelope', platform, {
            schema: candidateArtifacts.schema,
            phase: candidateArtifacts.phase,
            platform: candidateArtifacts.platform,
            candidateSourceCount: candidateArtifacts.candidateSourceCount,
        }, 'candidate artifact identity', candidateArtifactsValid);
        add('baseline_source_uuid_artifacts_present', platform, baselineArtifacts.candidateUuidArtifactCount,
            '> 0', isFiniteNumber(baselineArtifacts.candidateUuidArtifactCount, { minimum: 1, integer: true }));
        const retainedSourceUuidArtifacts = contract.candidate.expected_retained_source_uuid_artifacts_by_platform;
        const expectedRetainedSourceUuidArtifacts = isObject(retainedSourceUuidArtifacts)
            && isFiniteNumber(retainedSourceUuidArtifacts[platform], { minimum: 0, integer: true })
            ? retainedSourceUuidArtifacts[platform]
            : 0;
        add('candidate_source_uuid_artifact_policy', platform, candidateArtifacts.candidateUuidArtifactCount,
            expectedRetainedSourceUuidArtifacts,
            candidateArtifacts.candidateUuidArtifactCount === expectedRetainedSourceUuidArtifacts);
        for (const field of ['runtime', 'resources']) {
            const baselineBytes = artifactMetric(baselineArtifacts, field)?.totalBytes;
            const candidateBytes = artifactMetric(candidateArtifacts, field)?.totalBytes;
            add(`artifact_${field}_present`, platform, candidateBytes, 'finite bytes',
                Number.isFinite(baselineBytes) && Number.isFinite(candidateBytes));
            add(`artifact_${field}_relative`, platform, candidateBytes, `<= ${baselineBytes * (1 + sizeRule.maximum_relative_increase)}`,
                Number.isFinite(baselineBytes) && Number.isFinite(candidateBytes)
                && candidateBytes <= baselineBytes * (1 + sizeRule.maximum_relative_increase));
            add(`artifact_${field}_absolute`, platform, candidateBytes, `<= ${baselineBytes + sizeRule.maximum_absolute_increase_bytes}`,
                Number.isFinite(baselineBytes) && Number.isFinite(candidateBytes)
                && candidateBytes <= baselineBytes + sizeRule.maximum_absolute_increase_bytes);
        }
        if (platform === 'android_emulator') {
            const packageBytes = (report) => report.packageArtifacts.find((item) => item.path.endsWith('.apk'))?.bytes;
            const baselineBytes = packageBytes(baselineArtifacts);
            const candidateBytes = packageBytes(candidateArtifacts);
            add('artifact_android_package_present', platform, { baselineBytes, candidateBytes }, 'finite positive APK bytes',
                isFiniteNumber(baselineBytes, { minimum: 1 }) && isFiniteNumber(candidateBytes, { minimum: 1 }));
            add('artifact_android_package_relative', platform, candidateBytes, `<= ${baselineBytes * (1 + sizeRule.maximum_relative_increase)}`,
                isFiniteNumber(baselineBytes, { minimum: 1 }) && isFiniteNumber(candidateBytes, { minimum: 1 })
                    && candidateBytes <= baselineBytes * (1 + sizeRule.maximum_relative_increase));
            add('artifact_android_package_absolute', platform, candidateBytes, `<= ${baselineBytes + sizeRule.maximum_absolute_increase_bytes}`,
                isFiniteNumber(baselineBytes, { minimum: 1 }) && isFiniteNumber(candidateBytes, { minimum: 1 })
                    && candidateBytes <= baselineBytes + sizeRule.maximum_absolute_increase_bytes);
        }
        add('visual_parity', platform, visual.comparisons?.[platform]?.status, 'pass', visual.comparisons?.[platform]?.status === 'pass');
    }

    const report = {
        schema: 'mtr.atlas_pilot_comparison.v1',
        status: checks.every((check) => check.passed) ? 'pass' : 'fail',
        contractStatus: contract.status,
        checksPassed: checks.filter((check) => check.passed).length,
        checksTotal: checks.length,
        checksFailed: checks.filter((check) => !check.passed),
        checks,
        runtimeByPlatform,
        artifactsByPlatform,
        visualReport: path.relative(projectRoot, resolveContained(projectRoot, options.visualReport, '--visual-report')).replaceAll('\\', '/'),
    };
    return report;
}

function main() {
    const options = parseArguments(process.argv.slice(2));
    const report = compare(options);
    const projectRoot = path.resolve(options.projectRoot);
    const output = resolveContained(projectRoot, options.output, '--output');
    writeJsonAtomic(output, report);
    process.stdout.write(`${JSON.stringify({
        status: report.status,
        checksPassed: report.checksPassed,
        checksTotal: report.checksTotal,
        failed: report.checksFailed.map((check) => `${check.platform}:${check.id}`),
        output: path.relative(projectRoot, output).replaceAll('\\', '/'),
    })}\n`);
    if (report.status !== 'pass') process.exitCode = 1;
}

module.exports = { compare };
if (require.main === module) {
    try {
        main();
    } catch (error) {
        process.stderr.write(`${error?.stack || error}\n`);
        process.exitCode = 1;
    }
}
