async (page) => {
    const cycle = 'cycle2';
    const screenshotRoot = `output/playwright/${cycle}`;
    const baseUrl = new URL('/index.html', page.url());
    const consoleEvents = [];
    const pageErrors = [];
    const requestFailures = [];

    const onConsole = (message) => {
        consoleEvents.push({
            at: Date.now(),
            type: message.type(),
            text: message.text(),
        });
    };
    const onPageError = (error) => {
        pageErrors.push({ at: Date.now(), text: String(error?.stack || error?.message || error) });
    };
    const onRequestFailed = (request) => {
        const failure = request.failure()?.errorText || 'unknown';
        if (failure === 'net::ERR_ABORTED') return;
        requestFailures.push({ at: Date.now(), url: request.url(), failure });
    };

    page.on('console', onConsole);
    page.on('pageerror', onPageError);
    page.on('requestfailed', onRequestFailed);

    const waitForConsole = async (pattern, startIndex, timeoutMs = 30000) => {
        const deadline = Date.now() + timeoutMs;
        while (Date.now() < deadline) {
            const match = consoleEvents.slice(startIndex).find((event) => pattern.test(event.text));
            if (match) return { found: true, waitMs: timeoutMs - Math.max(0, deadline - Date.now()), text: match.text };
            await page.waitForTimeout(200);
        }
        return { found: false, waitMs: timeoutMs, text: '' };
    };

    const makeUrl = (params, caseName) => {
        const url = new URL(baseUrl.href);
        const values = { ...params, mtr_cycle: cycle, mtr_case: caseName, mtr_cache_bust: `${Date.now()}_${caseName}` };
        for (const [key, value] of Object.entries(values)) url.searchParams.set(key, String(value));
        return url.href;
    };

    const diagnosticsFrom = (consoleStart, pageErrorStart, requestFailureStart) => {
        const scopedConsole = consoleEvents.slice(consoleStart);
        const errors = scopedConsole.filter((event) => event.type === 'error').map((event) => event.text);
        const allWarnings = scopedConsole.filter((event) => event.type === 'warning').map((event) => event.text);
        const knownWarnings = allWarnings.filter((text) => /GL Driver Message .*GPU stall due to ReadPixels/i.test(text));
        const warnings = allWarnings.filter((text) => !/GL Driver Message .*GPU stall due to ReadPixels/i.test(text));
        const productFailures = scopedConsole
            .filter((event) => /MTR_[A-Z0-9_]*(?:_FAIL|_ERROR)\b/i.test(event.text))
            .map((event) => event.text);
        return {
            consoleErrorCount: errors.length,
            consoleWarningCount: warnings.length,
            knownConsoleWarningCount: knownWarnings.length,
            productFailureCount: productFailures.length,
            pageErrors: pageErrors.slice(pageErrorStart),
            requestFailures: requestFailures.slice(requestFailureStart),
            errors: errors.slice(0, 10),
            warnings: warnings.slice(0, 10),
            knownWarnings: knownWarnings.slice(0, 10),
            productFailures: productFailures.slice(0, 10),
        };
    };

    const runCase = async ({ name, params, expected, screen = '', level = 0, viewport = { width: 1280, height: 720 }, settleMs = 2500 }) => {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(150);
        const consoleStart = consoleEvents.length;
        const pageErrorStart = pageErrors.length;
        const requestFailureStart = requestFailures.length;
        const startedAt = Date.now();
        const url = makeUrl(params, name);
        let navigationError = '';
        try {
            await page.goto(url, { waitUntil: 'load', timeout: 30000 });
        } catch (error) {
            navigationError = String(error?.message || error);
        }
        const expectedWait = await waitForConsole(expected, consoleStart, 30000);
        await page.waitForTimeout(settleMs);
        const messages = consoleEvents.slice(consoleStart).map((event) => event.text);
        const menuGateReady = screen
            ? messages.some((text) => new RegExp(`MTR_MENU_UI_GATE_READY[^\\n]*screen=${screen}`, 'i').test(text))
            : true;
        const backgroundReady = level > 0 && !screen
            ? messages.some((text) => new RegExp(`MTR_BACKGROUND_BITMAP_APPLIED level=${level} source=full`, 'i').test(text))
            : true;
        const assetSummaryReady = level > 0 && !screen
            ? messages.some((text) => new RegExp(`MTR_ASSET_USAGE_SUMMARY level=${level}`, 'i').test(text))
            : true;
        const screenshot = `${screenshotRoot}/${name}.png`;
        let screenshotError = '';
        try {
            await page.screenshot({ path: screenshot });
        } catch (error) {
            screenshotError = String(error?.message || error);
        }
        const diagnostics = diagnosticsFrom(consoleStart, pageErrorStart, requestFailureStart);
        const passed = !navigationError
            && expectedWait.found
            && menuGateReady
            && backgroundReady
            && assetSummaryReady
            && !screenshotError
            && diagnostics.consoleErrorCount === 0
            && diagnostics.consoleWarningCount === 0
            && diagnostics.productFailureCount === 0
            && diagnostics.pageErrors.length === 0
            && diagnostics.requestFailures.length === 0;
        return {
            name,
            status: passed ? 'pass' : 'fail',
            url,
            viewport,
            screen,
            level,
            expectedMarker: expected.source,
            markerReady: expectedWait.found,
            markerWaitMs: expectedWait.waitMs,
            menuGateReady,
            backgroundReady,
            assetSummaryReady,
            elapsedMs: Date.now() - startedAt,
            screenshot,
            navigationError,
            screenshotError,
            diagnostics,
        };
    };

    const uiCases = [
        { name: 'ui_menu', params: { mtr_state: 'menu' }, expected: /MTR_QA_SCREEN_READY screen=menu/i, screen: 'menu' },
        { name: 'ui_name', params: { mtr_state: 'name' }, expected: /MTR_QA_SCREEN_READY screen=name/i, screen: 'name' },
        { name: 'ui_levels', params: { mtr_dev: 1, mtr_state: 'levels' }, expected: /MTR_QA_SCREEN_READY screen=levels/i, screen: 'levels' },
        { name: 'ui_skins', params: { mtr_state: 'skins' }, expected: /MTR_QA_SCREEN_READY screen=skins/i, screen: 'skins' },
        { name: 'ui_sound', params: { mtr_state: 'sound' }, expected: /MTR_QA_SCREEN_READY screen=sound/i, screen: 'sound' },
        { name: 'ui_records', params: { mtr_state: 'records', mtr_seed_records: 1 }, expected: /MTR_QA_SCREEN_READY screen=records/i, screen: 'records' },
        { name: 'ui_achievements', params: { mtr_state: 'achievements', mtr_unlock_achievements: 1 }, expected: /MTR_QA_SCREEN_READY screen=achievements/i, screen: 'achievements' },
        { name: 'ui_devgate', params: { mtr_state: 'devgate' }, expected: /MTR_QA_SCREEN_READY screen=devgate/i, screen: 'devgate' },
        { name: 'ui_devpanel', params: { mtr_dev: 1, mtr_state: 'devpanel' }, expected: /MTR_QA_SCREEN_READY screen=devpanel/i, screen: 'devpanel' },
        { name: 'ui_paused', params: { mtr_dev: 1, mtr_autostart: 1, mtr_level: 8, mtr_pause: 1, mtr_show_touch_zones: 1 }, expected: /MTR_QA_SCREEN_READY screen=paused/i, screen: 'paused', level: 8, settleMs: 3000 },
        { name: 'ui_clear', params: { mtr_dev: 1, mtr_state: 'clear', mtr_level: 1 }, expected: /MTR_QA_SCREEN_READY screen=clear/i, screen: 'clear' },
        { name: 'ui_over', params: { mtr_dev: 1, mtr_state: 'over', mtr_level: 1 }, expected: /MTR_QA_SCREEN_READY screen=over/i, screen: 'over' },
        { name: 'ui_finished', params: { mtr_dev: 1, mtr_state: 'finished', mtr_level: 15 }, expected: /MTR_QA_SCREEN_READY screen=finished/i, screen: 'finished' },
    ];

    const responsiveViewports = [
        { width: 1920, height: 1080 },
        { width: 1280, height: 720 },
        { width: 844, height: 422 },
        { width: 915, height: 422 },
        { width: 1024, height: 768 },
        { width: 390, height: 844 },
    ];

    const startedAt = new Date().toISOString();
    const uiResults = [];
    for (const item of uiCases) uiResults.push(await runCase(item));

    const responsiveResults = [];
    for (const viewport of responsiveViewports) {
        const name = `responsive_${viewport.width}x${viewport.height}`;
        responsiveResults.push(await runCase({
            name,
            params: { mtr_state: 'menu' },
            expected: /MTR_QA_SCREEN_READY screen=menu/i,
            screen: 'menu',
            viewport,
        }));
    }

    await page.setViewportSize({ width: 390, height: 844 });
    const portraitConsoleStart = consoleEvents.length;
    const portraitPageErrorStart = pageErrors.length;
    const portraitRequestFailureStart = requestFailures.length;
    const portraitStarted = Date.now();
    await page.mouse.click(131, 399);
    const portraitNameWait = await waitForConsole(/MTR_QA_SCREEN_READY screen=name/i, portraitConsoleStart, 10000);
    await page.waitForTimeout(1200);
    const portraitMessages = consoleEvents.slice(portraitConsoleStart).map((event) => event.text);
    const portraitMenuGate = portraitMessages.some((text) => /MTR_MENU_UI_GATE_READY[^\n]*screen=name/i.test(text));
    const portraitScreenshot = `${screenshotRoot}/responsive_390x844_touch_name.png`;
    await page.screenshot({ path: portraitScreenshot });
    const portraitDiagnostics = diagnosticsFrom(portraitConsoleStart, portraitPageErrorStart, portraitRequestFailureStart);
    const portraitScreenReady = portraitNameWait.found || portraitMenuGate;
    const portraitTouch = {
        status: portraitScreenReady && portraitMenuGate
            && portraitDiagnostics.consoleErrorCount === 0
            && portraitDiagnostics.consoleWarningCount === 0
            && portraitDiagnostics.productFailureCount === 0
            && portraitDiagnostics.pageErrors.length === 0
            && portraitDiagnostics.requestFailures.length === 0 ? 'pass' : 'fail',
        markerReady: portraitNameWait.found,
        screenReady: portraitScreenReady,
        acceptedBy: portraitNameWait.found ? 'screen_and_menu_gates' : 'repeat_screen_menu_gate',
        menuGateReady: portraitMenuGate,
        elapsedMs: Date.now() - portraitStarted,
        screenshot: portraitScreenshot,
        diagnostics: portraitDiagnostics,
    };

    const levelResults = [];
    for (let level = 1; level <= 15; level += 1) {
        levelResults.push(await runCase({
            name: `level_${String(level).padStart(2, '0')}`,
            params: { mtr_dev: 1, mtr_autostart: 1, mtr_level: level, mtr_qa_obstacles: 1, mtr_qa_bonuses: 1 },
            expected: new RegExp(`MTR_GAMEPLAY_START_GATE_READY level=${level}`, 'i'),
            level,
            settleMs: 4000,
        }));
    }

    await page.setViewportSize({ width: 1280, height: 720 });
    const interactionConsoleStart = consoleEvents.length;
    const interactionPageErrorStart = pageErrors.length;
    const interactionRequestFailureStart = requestFailures.length;
    await page.goto(makeUrl({ mtr_dev: 1, mtr_autostart: 1, mtr_level: 1 }, 'interaction'), { waitUntil: 'load', timeout: 30000 });
    const interactionBoot = await waitForConsole(/MTR_GAMEPLAY_START_GATE_READY level=1/i, interactionConsoleStart, 30000);
    await page.bringToFront();
    await page.evaluate(() => document.querySelector('canvas')?.focus());
    const pressGameKey = async (key) => {
        await page.keyboard.down(key);
        await page.waitForTimeout(120);
        await page.keyboard.up(key);
    };
    const jumpStart = consoleEvents.length;
    await pressGameKey(' ');
    const jump = await waitForConsole(/MTR_PLAYER_POSE[^\n]*pose=jump\b/i, jumpStart, 5000);
    await page.screenshot({ path: `${screenshotRoot}/interaction_jump.png` });
    const dashStart = consoleEvents.length;
    await pressGameKey('d');
    const dash = await waitForConsole(/MTR_PLAYER_POSE[^\n]*pose=crouch_dash\b/i, dashStart, 5000);
    await page.screenshot({ path: `${screenshotRoot}/interaction_dash.png` });
    const pauseStart = consoleEvents.length;
    await pressGameKey('p');
    const pause = await waitForConsole(/state=playing->paused[^\n]*reason=pause_input/i, pauseStart, 5000);
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${screenshotRoot}/interaction_pause.png` });
    const resumeStart = consoleEvents.length;
    await pressGameKey('p');
    const resume = await waitForConsole(/state=paused->playing/i, resumeStart, 5000);
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${screenshotRoot}/interaction_resume.png` });
    const interactionDiagnostics = diagnosticsFrom(interactionConsoleStart, interactionPageErrorStart, interactionRequestFailureStart);
    const interaction = {
        status: interactionBoot.found && jump.found && dash.found && pause.found && resume.found
            && interactionDiagnostics.consoleErrorCount === 0
            && interactionDiagnostics.consoleWarningCount === 0
            && interactionDiagnostics.productFailureCount === 0
            && interactionDiagnostics.pageErrors.length === 0
            && interactionDiagnostics.requestFailures.length === 0 ? 'pass' : 'fail',
        boot: interactionBoot,
        jump,
        dash,
        pause,
        resume,
        diagnostics: interactionDiagnostics,
    };

    const restartResults = [];
    for (let iteration = 1; iteration <= 10; iteration += 1) {
        const consoleStart = consoleEvents.length;
        const pageErrorStart = pageErrors.length;
        const requestFailureStart = requestFailures.length;
        await page.goto(makeUrl({ mtr_dev: 1, mtr_state: 'over', mtr_level: 1 }, `restart_${iteration}`), { waitUntil: 'load', timeout: 30000 });
        const overGate = await waitForConsole(/MTR_QA_SCREEN_READY screen=over/i, consoleStart, 30000);
        const menuGate = await waitForConsole(/MTR_MENU_UI_GATE_READY[^\n]*screen=over/i, consoleStart, 10000);
        const retryStart = consoleEvents.length;
        const retryStarted = Date.now();
        await page.mouse.click(640, 448);
        const retry = await waitForConsole(/state=over->playing[^\n]*reason=start_level/i, retryStart, 10000);
        const retryMs = Date.now() - retryStarted;
        if (iteration === 1 || iteration === 10) {
            await page.waitForTimeout(350);
            await page.screenshot({ path: `${screenshotRoot}/restart_${String(iteration).padStart(2, '0')}.png` });
        }
        const diagnostics = diagnosticsFrom(consoleStart, pageErrorStart, requestFailureStart);
        const passed = overGate.found && menuGate.found && retry.found
            && diagnostics.consoleErrorCount === 0
            && diagnostics.consoleWarningCount === 0
            && diagnostics.productFailureCount === 0
            && diagnostics.pageErrors.length === 0
            && diagnostics.requestFailures.length === 0;
        restartResults.push({ iteration, status: passed ? 'pass' : 'fail', retryMs, overGate, menuGate, retry, diagnostics });
    }

    const allCases = [...uiResults, ...responsiveResults, ...levelResults];
    const failedCases = allCases.filter((item) => item.status !== 'pass');
    const failedRestarts = restartResults.filter((item) => item.status !== 'pass');
    const status = failedCases.length === 0
        && portraitTouch.status === 'pass'
        && interaction.status === 'pass'
        && failedRestarts.length === 0 ? 'pass' : 'fail';
    const summary = {
        schema: 'mtr.web_matrix_interaction.v1',
        cycle: 2,
        status,
        startedAt,
        finishedAt: new Date().toISOString(),
        caseCount: allCases.length,
        passCount: allCases.length - failedCases.length,
        failCount: failedCases.length,
        uiResults,
        responsiveResults,
        portraitTouch,
        levelResults,
        interaction,
        restartLoop: {
            requestedIterations: restartResults.length,
            passCount: restartResults.length - failedRestarts.length,
            failCount: failedRestarts.length,
            iterations: restartResults,
        },
    };

    await page.evaluate(({ key, value }) => localStorage.setItem(key, JSON.stringify(value)), {
        key: 'mtr_web_matrix_cycle2_result',
        value: summary,
    });
    page.off('console', onConsole);
    page.off('pageerror', onPageError);
    page.off('requestfailed', onRequestFailed);
    return summary;
}
