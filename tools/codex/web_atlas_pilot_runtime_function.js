async function (page) {
    const startedAt = Date.now();
    const query = new URL(page.url()).searchParams;
    const phase = query.get('mtr_qa_atlas_phase') || 'unlabelled';
    if (!/^[a-z0-9_-]{3,32}$/i.test(phase)) throw new Error(`Unsafe atlas pilot phase: ${phase}`);
    const atlasId = query.get('mtr_qa_atlas_pilot') || '';
    const atlasSourceCounts = Object.freeze({
        objective_npc: 10,
        achievement_ui: 9,
        runner_collectibles: 14,
    });
    if (!Object.prototype.hasOwnProperty.call(atlasSourceCounts, atlasId)) {
        throw new Error(`Unsupported atlas QA id: ${atlasId || '-'}`);
    }
    const expectedSourceCount = atlasSourceCounts[atlasId];
    const requestedSourceCount = query.get('mtr_qa_atlas_source_count');
    if (requestedSourceCount !== null && Number(requestedSourceCount) !== expectedSourceCount) {
        throw new Error(`Atlas QA source count mismatch: ${requestedSourceCount} != ${expectedSourceCount}`);
    }

    const consoleEvents = [];
    const pageErrors = [];
    const requestFailures = [];
    let terminal = null;
    let resolveTerminal;
    const terminalPromise = new Promise((resolve) => { resolveTerminal = resolve; });

    const onConsole = (message) => {
        const event = {
            type: message.type(),
            text: message.text(),
            location: message.location(),
        };
        consoleEvents.push(event);
        if (event.text.startsWith('MTR_ATLAS_PILOT_COMPLETE ')) {
            try {
                terminal = {
                    kind: 'complete',
                    payload: JSON.parse(event.text.slice('MTR_ATLAS_PILOT_COMPLETE '.length)),
                };
            } catch (error) {
                terminal = { kind: 'invalid_complete', error: String(error?.message || error) };
            }
            resolveTerminal(terminal);
        } else if (event.text.startsWith('MTR_ATLAS_PILOT_FAIL ')) {
            terminal = { kind: 'fail', text: event.text };
            resolveTerminal(terminal);
        }
    };
    const onPageError = (error) => pageErrors.push(String(error?.stack || error));
    const onRequestFailed = (request) => requestFailures.push({
        url: request.url(),
        error: request.failure()?.errorText || 'unknown',
    });
    page.on('console', onConsole);
    page.on('pageerror', onPageError);
    page.on('requestfailed', onRequestFailed);

    try {
        const timeout = new Promise((resolve) => setTimeout(
            () => resolve({ kind: 'timeout', timeoutMs: 45000 }),
            45000,
        ));
        terminal = await Promise.race([terminalPromise, timeout]);
        await page.waitForTimeout(350);

        const evidenceRoot = atlasId === 'objective_npc'
            ? 'temp/m04-c-pilot'
            : `temp/m04-c-families/${atlasId}`;
        const screenshot = `${evidenceRoot}/${phase}/web/atlas-family.png`;
        await page.screenshot({ path: screenshot });
        const metric = terminal?.kind === 'complete' ? terminal.payload : null;
        const expectedInfrastructureErrors = consoleEvents.filter((event) => (
            event.type === 'error'
            && /\/favicon\.ico(?:$|\?)/i.test(event.location?.url || '')
            && /404|failed to load resource/i.test(event.text)
        ));
        const errors = consoleEvents.filter((event) => (
            event.type === 'error' && !expectedInfrastructureErrors.includes(event)
        ));
        const warnings = consoleEvents.filter((event) => event.type === 'warning');
        const expectedMetric = Boolean(
            metric
            && metric.contract === 'mtr.atlas_pilot_runtime_metric'
            && metric.schemaVersion === 2
            && metric.atlasId === atlasId
            && metric.platform === 'web'
            && metric.sourceCount === expectedSourceCount
            && metric.aggregate?.sampleCount === 7
            && Number.isFinite(metric.sourceTextureCount)
            && metric.sourceTextureCount > 0
            && Number.isFinite(metric.drawTextureCount)
            && metric.drawTextureCount > 0
            && Number.isFinite(metric.dynamicAtlasPackedCount)
            && Number.isFinite(metric.loadElapsedMs)
        );
        const status = terminal?.kind === 'complete'
            && expectedMetric
            && errors.length === 0
            && warnings.length === 0
            && pageErrors.length === 0
            && requestFailures.length === 0
            ? 'pass'
            : 'fail';

        return {
            schema: 'mtr.web_atlas_pilot.v1',
            status,
            phase,
            atlasId,
            expectedSourceCount,
            elapsedMs: Date.now() - startedAt,
            expectedMetric,
            terminal,
            metric,
            screenshot,
            diagnostics: {
                consoleErrors: errors,
                consoleWarnings: warnings,
                pageErrors,
                requestFailures,
                expectedInfrastructureErrors,
            },
            consoleEvents,
        };
    } finally {
        page.off('console', onConsole);
        page.off('pageerror', onPageError);
        page.off('requestfailed', onRequestFailed);
    }
}
