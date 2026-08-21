'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..');
const metricsPath = path.join(projectRoot, 'assets', 'scripts', 'qa', 'AtlasPilotMetrics.ts');
const gameRootPath = path.join(projectRoot, 'assets', 'scripts', 'GameRoot.ts');
const appActivityPath = path.join(projectRoot, 'native', 'engine', 'android', 'app', 'src', 'com', 'cocos', 'game', 'AppActivity.java');
const webQaConfigPath = path.join(projectRoot, 'build-web-mobile-qa.json');
const androidQaConfigPath = path.join(projectRoot, 'build-android-emulator.json');
const releaseWebConfigPath = path.join(projectRoot, 'build-web-mobile.json');
const contractPath = path.join(projectRoot, 'docs', 'global_modernization', 'v3', 'M04', 'M04_C_PILOT_CONTRACT.json');
const achievementUiContractPath = path.join(projectRoot, 'docs', 'global_modernization', 'v3', 'M04', 'M04_C_FAMILY_ACHIEVEMENT_UI_CONTRACT.json');
const webRuntimeFunctionPath = path.join(projectRoot, 'tools', 'codex', 'web_atlas_pilot_runtime_function.js');
const artifactMeasurerPath = path.join(projectRoot, 'tools', 'codex', 'Measure-MtrAtlasPilotArtifacts.js');
const androidRunnerPath = path.join(projectRoot, 'tools', 'codex', 'Run-MtrAndroidAtlasPilotQa.ps1');
const visualComparatorPath = path.join(projectRoot, 'tools', 'codex', 'Compare-MtrAtlasPilotVisuals.py');
const comparisonPath = path.join(projectRoot, 'tools', 'codex', 'Compare-MtrAtlasPilot.js');
const typescriptPath = process.env.COCOS_TYPESCRIPT_JS
  || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js';

for (const requiredPath of [
  metricsPath,
  gameRootPath,
  appActivityPath,
  webQaConfigPath,
  androidQaConfigPath,
  releaseWebConfigPath,
  contractPath,
  achievementUiContractPath,
  webRuntimeFunctionPath,
  artifactMeasurerPath,
  androidRunnerPath,
  visualComparatorPath,
  comparisonPath,
  typescriptPath,
]) {
  if (!fs.existsSync(requiredPath)) throw new Error(`Required file not found: ${requiredPath}`);
}

const ts = require(typescriptPath);
const program = ts.createProgram([metricsPath], {
  module: ts.ModuleKind.CommonJS,
  moduleResolution: ts.ModuleResolutionKind.Node10,
  target: ts.ScriptTarget.ES2015,
  strict: true,
  noEmit: true,
  skipLibCheck: true,
});
const diagnostics = ts.getPreEmitDiagnostics(program)
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n'));
assert.deepStrictEqual(diagnostics, [], `Strict TypeScript diagnostics:\n${diagnostics.join('\n')}`);

const transpiled = ts.transpileModule(fs.readFileSync(metricsPath, 'utf8'), {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2015,
    strict: true,
  },
  fileName: metricsPath,
  reportDiagnostics: true,
});
const transpileErrors = (transpiled.diagnostics || [])
  .filter((diagnostic) => diagnostic.category === ts.DiagnosticCategory.Error)
  .map((diagnostic) => ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n'));
assert.deepStrictEqual(transpileErrors, [], `Transpile diagnostics:\n${transpileErrors.join('\n')}`);

const loadedModule = { exports: {} };
const load = new Function('exports', 'require', 'module', '__filename', '__dirname', transpiled.outputText);
load(
  loadedModule.exports,
  (request) => { throw new Error(`Unexpected dependency: ${request}`); },
  loadedModule,
  metricsPath,
  path.dirname(metricsPath),
);
const { aggregateAtlasPilotSamples } = loadedModule.exports;

const aggregate = aggregateAtlasPilotSamples([
  { sampledAtMs: 1000, draws: 20, textureMemoryMb: 12.5, bufferMemoryMb: 2.1, fps: 58 },
  { sampledAtMs: 1550, draws: 14, textureMemoryMb: 12.7, bufferMemoryMb: 2.2, fps: 60 },
  { sampledAtMs: 2100, draws: 16, textureMemoryMb: 12.6, bufferMemoryMb: 2.1, fps: 59 },
  { sampledAtMs: 2650, draws: 12, textureMemoryMb: 12.8, bufferMemoryMb: 2.3, fps: 57 },
  { sampledAtMs: 3200, draws: 18, textureMemoryMb: 12.4, bufferMemoryMb: 2.2, fps: 61 },
]);
assert.deepStrictEqual(aggregate, {
  sampleCount: 5,
  draws: { min: 12, median: 16, max: 20 },
  textureMemoryMb: { min: 12.4, median: 12.6, max: 12.8 },
  bufferMemoryMb: { min: 2.1, median: 2.2, max: 2.3 },
  fps: { min: 57, median: 59, max: 61 },
});
assert.throws(() => aggregateAtlasPilotSamples([]), /at least one sample/);
assert.throws(() => aggregateAtlasPilotSamples([
  { sampledAtMs: 0, draws: Number.NaN, textureMemoryMb: 1, bufferMemoryMb: 1, fps: 60 },
]), /one finite value per sample/);

const gameRootSource = fs.readFileSync(gameRootPath, 'utf8');
const appActivitySource = fs.readFileSync(appActivityPath, 'utf8');
assert.ok(gameRootSource.includes("params.get('mtr_qa_atlas_pilot')"));
assert.ok(gameRootSource.includes("objective_npc: {"));
assert.ok(gameRootSource.includes("achievement_ui: {"));
assert.ok(gameRootSource.includes("'objectives/ui/ui_monkey_profile_badge_01'"));
assert.ok(gameRootSource.includes('if (!DEBUG) return;'));
assert.ok(gameRootSource.includes('MTR_ATLAS_PILOT_COMPLETE'));
assert.ok(gameRootSource.includes("'m04_c_atlas_pilot'"));
assert.ok(appActivitySource.includes('"mtr_qa_atlas_pilot"'));
assert.strictEqual(JSON.parse(fs.readFileSync(webQaConfigPath, 'utf8')).debug, true);
assert.strictEqual(JSON.parse(fs.readFileSync(androidQaConfigPath, 'utf8')).debug, true);
assert.strictEqual(JSON.parse(fs.readFileSync(releaseWebConfigPath, 'utf8')).debug, false);

const contract = JSON.parse(fs.readFileSync(contractPath, 'utf8'));
assert.strictEqual(contract.$schema, 'mtr.m04_c_atlas_pilot_contract.v1');
assert.strictEqual(contract.status, 'candidate_accepted');
assert.strictEqual(contract.amendment.candidate_descriptor_present_at_amendment, false);
assert.strictEqual(contract.amendment.metric_fishing_prohibited, true);
assert.strictEqual(contract.candidate.atlas_id, 'objective_npc');
assert.strictEqual(contract.candidate.source_count, 10);
assert.deepStrictEqual(contract.measurement_protocol.platforms, ['web', 'android_emulator']);
assert.strictEqual(contract.measurement_protocol.sample_count, 7);
assert.strictEqual(contract.acceptance.source_texture_count.baseline_by_platform.web, 10);
assert.strictEqual(contract.acceptance.source_texture_count.candidate_expected_by_platform.android_emulator, 1);
assert.strictEqual(contract.acceptance.draw_texture_count.baseline_by_platform.web, 1);
assert.strictEqual(contract.acceptance.draw_texture_count.baseline_by_platform.android_emulator, 10);
assert.strictEqual(contract.acceptance.dynamic_atlas_packed_count.candidate_expected_by_platform.web, 0);
assert.strictEqual(contract.acceptance.draw_calls.web.maximum_absolute_increase, 1);
assert.strictEqual(contract.acceptance.draw_calls.android_emulator.minimum_relative_reduction, 0.3);
assert.strictEqual(contract.acceptance.decision_rule, 'accept_only_if_every_applicable_platform_threshold_and_visual_gate_passes_with_material_android_gain');
assert.strictEqual(contract.rollback.broader_family_migration_authorized, false);
assert.strictEqual(contract.candidate_result.status, 'accepted');
assert.deepStrictEqual(contract.candidate_result.acceptance_checks, { passed: 63, total: 63 });

const achievementUiContract = JSON.parse(fs.readFileSync(achievementUiContractPath, 'utf8'));
assert.strictEqual(achievementUiContract.$schema, 'mtr.m04_c_atlas_family_contract.v1');
assert.strictEqual(achievementUiContract.unit_id, 'M04-C-FAMILY-ACHIEVEMENT-UI');
assert.strictEqual(achievementUiContract.parent_unit, 'M04-C-FAMILIES');
assert.strictEqual(achievementUiContract.status, 'candidate_accepted');
assert.strictEqual(achievementUiContract.selection.selected_before_runtime_asset_mutation, true);
assert.strictEqual(achievementUiContract.selection.candidate_descriptor_present_at_selection, false);
assert.strictEqual(achievementUiContract.selection.metric_fishing_prohibited, true);
assert.strictEqual(achievementUiContract.candidate.atlas_id, 'achievement_ui');
assert.strictEqual(achievementUiContract.candidate.source_count, 9);
assert.strictEqual(achievementUiContract.candidate.source_bytes, 1787287);
assert.strictEqual(achievementUiContract.candidate.descriptor_uuid, '35f049fd-ff92-47ec-bbe0-7ab05469eab2');
assert.strictEqual(achievementUiContract.measurement_protocol.screenshot_filename, 'atlas-family.png');
assert.strictEqual(achievementUiContract.acceptance.source_texture_count.baseline_by_platform.web, 9);
assert.strictEqual(achievementUiContract.acceptance.draw_texture_count.baseline_by_platform.android_emulator, 9);
assert.strictEqual(achievementUiContract.acceptance.dynamic_atlas_packed_count.candidate_expected_by_platform.web, 0);
assert.strictEqual(achievementUiContract.acceptance.draw_calls.android_emulator.minimum_relative_reduction, 0.3);
assert.strictEqual(achievementUiContract.rollback.parent_family_batch_authorized, false);
assert.strictEqual(achievementUiContract.candidate_result.status, 'accepted');
assert.deepStrictEqual(achievementUiContract.candidate_result.acceptance_checks, { passed: 63, total: 63 });

const webRuntimeFunction = fs.readFileSync(webRuntimeFunctionPath, 'utf8');
assert.ok(webRuntimeFunction.includes("schema: 'mtr.web_atlas_pilot.v1'"));
assert.ok(webRuntimeFunction.includes("MTR_ATLAS_PILOT_COMPLETE "));
assert.ok(webRuntimeFunction.includes("MTR_ATLAS_PILOT_FAIL "));
assert.ok(!webRuntimeFunction.includes('page.reload('));
assert.ok(webRuntimeFunction.includes('metric.sourceTextureCount'));
assert.ok(webRuntimeFunction.includes('metric.drawTextureCount'));
assert.ok(webRuntimeFunction.includes('achievement_ui: 9'));
assert.ok(webRuntimeFunction.includes('metric.atlasId === atlasId'));
assert.ok(webRuntimeFunction.includes('expectedInfrastructureErrors'));
assert.strictEqual(typeof Function(`"use strict"; return (${webRuntimeFunction});`)(), 'function');

const artifactMeasurer = fs.readFileSync(artifactMeasurerPath, 'utf8');
assert.ok(artifactMeasurer.includes("schema: 'mtr.atlas_pilot_artifact_metric.v1'"));
assert.ok(artifactMeasurer.includes('skippedLinks.push(absolute)'));
assert.ok(artifactMeasurer.includes("values.get('--candidate-source-directory')"));
assert.ok(artifactMeasurer.includes('candidateSourceDirectory: path.relative'));
assert.ok(!artifactMeasurer.includes("path.join(projectRoot, 'assets', 'resources', 'objectives', 'npc')"));
const androidRunner = fs.readFileSync(androidRunnerPath, 'utf8');
assert.ok(androidRunner.includes("$Serial -notmatch '^emulator-\\d+$'"));
assert.ok(androidRunner.includes("'shell', 'am', 'start', '--user', '0'"));
assert.ok(androidRunner.includes('MTR_ATLAS_PILOT_COMPLETE'));
assert.ok(androidRunner.includes("[string]$AtlasId = 'objective_npc'"));
assert.ok(androidRunner.includes('[int]$ExpectedSourceCount = 10'));
assert.ok(androidRunner.includes("[string]$ProjectRoot = ''"));
assert.ok(androidRunner.includes('$MyInvocation.MyCommand.Path'));
assert.ok(!androidRunner.includes("Join-Path $PSScriptRoot '..\\..'"));
assert.ok(androidRunner.includes("$ErrorActionPreference = 'Continue'"));
assert.ok(androidRunner.includes('$exitCode = $LASTEXITCODE'));
assert.ok(androidRunner.includes('$ErrorActionPreference = $previousErrorActionPreference'));
const visualComparator = fs.readFileSync(visualComparatorPath, 'utf8');
assert.ok(visualComparator.includes('mtr.atlas_pilot_visual_parity.v1'));
assert.ok(visualComparator.includes('maximum_changed_pixel_fraction'));
assert.ok(visualComparator.includes('screenshot_filename'));
assert.ok(visualComparator.includes('Unsafe screenshot filename in contract'));
const comparisonSource = fs.readFileSync(comparisonPath, 'utf8');
assert.ok(comparisonSource.includes('mtr.atlas_pilot_comparison.v1'));
assert.ok(comparisonSource.includes('minimum_relative_reduction'));

const comparisonModule = require(comparisonPath);
const compareFixtureRoot = fs.mkdtempSync(path.join(projectRoot, 'temp', 'm04-c-compare-test-'));
const fixtureRelative = path.relative(projectRoot, compareFixtureRoot).replaceAll('\\', '/');
const writeFixture = (relative, value) => {
  const target = path.join(compareFixtureRoot, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
};
const metricRange = (value) => ({ min: value, median: value, max: value });
const runtimeFixture = (phase, platform, sourceTextureCount, drawTextureCount, dynamicAtlasPackedCount, draws) => ({
  schema: platform === 'web' ? 'mtr.web_atlas_pilot.v1' : 'mtr.android_atlas_pilot.v1',
  status: 'pass',
  phase,
  metric: {
    contract: 'mtr.atlas_pilot_runtime_metric',
    schemaVersion: 2,
    atlasId: 'objective_npc',
    platform: platform === 'web' ? 'web' : 'android',
    sourceCount: 10,
    sourceTextureCount,
    drawTextureCount,
    dynamicAtlasPackedCount,
    loadElapsedMs: 200,
    aggregate: {
      sampleCount: 7,
      draws: metricRange(draws),
      textureMemoryMb: metricRange(10),
      bufferMemoryMb: metricRange(8),
      fps: metricRange(60),
    },
  },
});
const artifactFixture = (phase, platform, candidateUuidArtifactCount) => ({
  schema: 'mtr.atlas_pilot_artifact_metric.v1',
  phase,
  platform,
  buildRoot: `build/${platform}-${phase}`,
  all: { fileCount: 10, totalBytes: 1000000 },
  runtime: { fileCount: 10, totalBytes: 1000000 },
  resources: { fileCount: 8, totalBytes: 800000 },
  candidateSourceCount: 10,
  candidateUuidArtifactCount,
  packageArtifacts: platform === 'android_emulator' ? [{ path: 'app.apk', bytes: 1000000 }] : [],
  skippedLinks: [],
});

try {
  for (const [platform, directory] of [['web', 'web'], ['android_emulator', 'android']]) {
    const baselineDrawTextures = platform === 'web' ? 1 : 10;
    const baselineDynamic = platform === 'web' ? 10 : 0;
    const baselineDraws = platform === 'web' ? 17 : 26;
    writeFixture(`baseline/${directory}/runtime.json`, runtimeFixture(
      'baseline', platform, 10, baselineDrawTextures, baselineDynamic, baselineDraws,
    ));
    writeFixture(`candidate/${directory}/runtime.json`, runtimeFixture(
      'candidate', platform, 1, 1, 0, 17,
    ));
    writeFixture(`baseline/${directory}/artifacts.json`, artifactFixture('baseline', platform, 30));
    writeFixture(`candidate/${directory}/artifacts.json`, artifactFixture('candidate', platform, 0));
  }
  writeFixture('visual.json', {
    schema: 'mtr.atlas_pilot_visual_parity.v1',
    status: 'pass',
    comparisons: { web: { status: 'pass' }, android_emulator: { status: 'pass' } },
  });
  const fixtureOptions = {
    projectRoot,
    contract: path.relative(projectRoot, contractPath),
    baselineRoot: `${fixtureRelative}/baseline`,
    candidateRoot: `${fixtureRelative}/candidate`,
    visualReport: `${fixtureRelative}/visual.json`,
  };
  const passingComparison = comparisonModule.compare(fixtureOptions);
  assert.strictEqual(passingComparison.status, 'pass');
  assert.strictEqual(passingComparison.checksPassed, 63);
  assert.strictEqual(passingComparison.checksTotal, 63);

  const candidateWebPath = path.join(compareFixtureRoot, 'candidate', 'web', 'runtime.json');
  const wrongIdentity = JSON.parse(fs.readFileSync(candidateWebPath, 'utf8'));
  wrongIdentity.metric.atlasId = 'wrong_atlas';
  fs.writeFileSync(candidateWebPath, `${JSON.stringify(wrongIdentity, null, 2)}\n`, 'utf8');
  const rejectedComparison = comparisonModule.compare(fixtureOptions);
  assert.strictEqual(rejectedComparison.status, 'fail');
  assert.ok(rejectedComparison.checksFailed.some((check) => (
    check.platform === 'web' && check.id === 'candidate_runtime_envelope'
  )));
} finally {
  fs.rmSync(compareFixtureRoot, { recursive: true, force: true });
}

process.stdout.write(`${JSON.stringify({
  status: 'PASS',
  strictTypeScript: true,
  typescriptVersion: ts.version,
  sampleCount: aggregate.sampleCount,
  medianDraws: aggregate.draws.median,
  qaQueryReleaseGated: true,
  webAndAndroidQaEnabled: true,
  acceptanceContractFrozen: true,
})}\n`);
