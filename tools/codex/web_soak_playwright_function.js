async (page) => {
    const source = await page.evaluate(() => ({
        params: Object.fromEntries(new URL(location.href).searchParams.entries()),
    }));
    const durationSeconds = Math.max(30, Number(source.params.mtr_soak_seconds || 300));
    const cycle = (source.params.mtr_soak_cycle || 'cycle').replace(/[^a-z0-9_-]/gi, '_');
    const run = (source.params.mtr_run || 'web_soak').replace(/[^a-z0-9_-]/gi, '_');
    const screenshotRoot = `output/playwright/${cycle}`;
    const resultKey = 'mtr_soak_last_result';

    let state = 'booting';
    let stateSince = Date.now();
    let startedAt = 0;
    let menuGateState = '';
    let menuGateAt = 0;
    const transitions = [];
    const consoleErrors = [];
    const consoleWarnings = [];

    const onConsole = (message) => {
        const text = message.text();
        if (message.type() === 'warning' && /GL Driver Message .*GPU stall due to ReadPixels/i.test(text)) return;
        const transition = text.match(/state=([a-z_]+)->([a-z_]+)/i);
        if (transition) {
            state = transition[2].toLowerCase();
            stateSince = Date.now();
            menuGateState = '';
            transitions.push({
                atMs: startedAt > 0 ? stateSince - startedAt : 0,
                from: transition[1].toLowerCase(),
                to: state,
                text,
            });
        }

        const gate = text.match(/MTR_MENU_UI_GATE_READY[^\n]*screen=([a-z_]+)/i);
        if (gate) {
            menuGateState = gate[1].toLowerCase();
            menuGateAt = Date.now();
        }

        if (message.type() === 'error') {
            consoleErrors.push(text);
        } else if (message.type() === 'warning') {
            consoleWarnings.push(text);
        }
    };

    page.on('console', onConsole);
    await page.reload({ waitUntil: 'load' });

    const bootDeadline = Date.now() + 30000;
    while (state !== 'playing' && Date.now() < bootDeadline) {
        await page.waitForTimeout(250);
    }
    if (state !== 'playing') {
        throw new Error(`Web soak boot gate failed: expected playing, got ${state}`);
    }

    await page.bringToFront();
    await page.evaluate(() => document.querySelector('canvas')?.focus());

    startedAt = Date.now();

    const heapSamples = [];
    const fpsSamples = [];
    const stateSamples = [];
    const milestones = [60, 120, 180, 240, 300].filter((value) => value <= durationSeconds);
    const capturedMilestones = new Set();
    let inputBursts = 0;
    let clearClicks = 0;
    let overClicks = 0;
    let finishedClicks = 0;
    let unpauseActions = 0;
    let lastInputAt = 0;
    let lastUiActionAt = 0;
    let lastSampleAt = -30000;
    let lastPersistAt = -5000;

    const snapshotProgress = (complete = false) => ({
        schema: 'mtr.web_soak.v1',
        complete,
        run,
        cycle,
        targetDurationSeconds: durationSeconds,
        elapsedMs: Date.now() - startedAt,
        finalState: state,
        transitions,
        inputBursts,
        clearClicks,
        overClicks,
        finishedClicks,
        unpauseActions,
        heapSamples,
        fpsSamples,
        stateSamples,
        consoleErrors: consoleErrors.slice(0, 25),
        consoleWarnings: consoleWarnings.slice(0, 25),
        recordedAt: new Date().toISOString(),
    });

    const persistProgress = async (complete = false) => {
        const value = snapshotProgress(complete);
        await page.evaluate(
            ({ key, payload }) => {
                const serialized = JSON.stringify(payload);
                localStorage.setItem(key, serialized);
                globalThis.__mtrSoakResult = payload;
            },
            { key: resultKey, payload: value },
        );
        return value;
    };

    while (Date.now() - startedAt < durationSeconds * 1000) {
        const now = Date.now();
        const elapsedMs = now - startedAt;
        const elapsedSeconds = elapsedMs / 1000;
        const stateAgeMs = now - stateSince;
        const gateReady = menuGateState === state && now - menuGateAt >= 250;
        // Gate telemetry is intentionally de-duplicated by the game. Repeated
        // visits to the same end-state therefore use a conservative visual
        // settle fallback instead of waiting forever for another gate line.
        const endStateReady = gateReady || stateAgeMs >= 1500;

        if (state === 'playing' && elapsedMs - lastInputAt >= 7500) {
            await page.keyboard.press('Space');
            await page.waitForTimeout(80);
            await page.keyboard.press('ArrowRight');
            inputBursts += 1;
            lastInputAt = elapsedMs;
        } else if (state === 'clear' && endStateReady && stateAgeMs >= 500 && elapsedMs - lastUiActionAt >= 1500) {
            await page.mouse.click(Math.round((await page.evaluate(() => innerWidth)) * 0.5), Math.round((await page.evaluate(() => innerHeight)) * 0.567));
            clearClicks += 1;
            lastUiActionAt = elapsedMs;
        } else if (state === 'over' && endStateReady && stateAgeMs >= 500 && elapsedMs - lastUiActionAt >= 1500) {
            await page.mouse.click(Math.round((await page.evaluate(() => innerWidth)) * 0.5), Math.round((await page.evaluate(() => innerHeight)) * 0.631));
            overClicks += 1;
            lastUiActionAt = elapsedMs;
        } else if (state === 'finished' && endStateReady && stateAgeMs >= 500 && elapsedMs - lastUiActionAt >= 1500) {
            await page.mouse.click(Math.round((await page.evaluate(() => innerWidth)) * 0.5), Math.round((await page.evaluate(() => innerHeight)) * 0.583));
            finishedClicks += 1;
            lastUiActionAt = elapsedMs;
        } else if (state === 'paused' && stateAgeMs >= 500 && elapsedMs - lastUiActionAt >= 1500) {
            await page.keyboard.press('p');
            unpauseActions += 1;
            lastUiActionAt = elapsedMs;
        }

        if (elapsedMs - lastSampleAt >= 30000) {
            const metrics = await page.evaluate(async () => {
                const started = performance.now();
                let frames = 0;
                await new Promise((resolve) => {
                    const tick = (now) => {
                        frames += 1;
                        if (now - started >= 750) {
                            resolve();
                        } else {
                            requestAnimationFrame(tick);
                        }
                    };
                    requestAnimationFrame(tick);
                });
                const elapsed = performance.now() - started;
                return {
                    fps: elapsed > 0 ? (frames * 1000) / elapsed : 0,
                    heapBytes: performance.memory ? performance.memory.usedJSHeapSize : null,
                };
            });
            heapSamples.push({ atMs: elapsedMs, bytes: metrics.heapBytes });
            fpsSamples.push({ atMs: elapsedMs, fps: Number(metrics.fps.toFixed(2)) });
            stateSamples.push({ atMs: elapsedMs, state });
            lastSampleAt = elapsedMs;
        }

        for (const milestone of milestones) {
            if (!capturedMilestones.has(milestone) && elapsedSeconds >= milestone) {
                await page.screenshot({ path: `${screenshotRoot}/${run}_${String(milestone).padStart(3, '0')}s.png` });
                capturedMilestones.add(milestone);
            }
        }

        if (elapsedMs - lastPersistAt >= 5000) {
            await persistProgress(false);
            lastPersistAt = elapsedMs;
        }

        await page.waitForTimeout(250);
    }

    await page.screenshot({ path: `${screenshotRoot}/${run}_final.png` });
    const result = await persistProgress(true);
    page.off('console', onConsole);
    return result;
}
