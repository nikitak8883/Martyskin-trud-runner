async (page) => {
    const requestedUrl = new URL(page.url());
    const expectDevEvents = requestedUrl.searchParams.get('mtr_expect_dev_events') === '1';
    const consoleEvents = [];
    const pageErrors = [];
    const requestFailures = [];

    const onConsole = (message) => consoleEvents.push({ type: message.type(), text: message.text() });
    const onPageError = (error) => pageErrors.push(String(error?.stack || error?.message || error));
    const onRequestFailed = (request) => {
        const failure = request.failure()?.errorText || 'unknown';
        if (failure !== 'net::ERR_ABORTED') requestFailures.push({ url: request.url(), failure });
    };
    page.on('console', onConsole);
    page.on('pageerror', onPageError);
    page.on('requestfailed', onRequestFailed);

    const url = new URL('/index.html', requestedUrl);
    url.searchParams.delete('mtr_expect_dev_events');
    url.searchParams.set('mtr_qa_reset_loops', '10');
    url.searchParams.set('mtr_cache_bust', `${Date.now()}_game_root_dev_events`);

    const deadline = Date.now() + (expectDevEvents ? 30000 : 8000);
    await page.goto(url.href, { waitUntil: 'load', timeout: 30000 });
    while (Date.now() < deadline) {
        const messages = consoleEvents.map((event) => event.text);
        const runtimeReady = messages.some((text) => /MTR_RUNTIME_CORE_READY/i.test(text));
        const terminalEventQa = messages.some((text) => /MTR_DEV_EVENT_QA_(?:READY|FAIL|REJECTED)/i.test(text));
        if ((expectDevEvents && terminalEventQa) || (!expectDevEvents && runtimeReady)) break;
        await page.waitForTimeout(100);
    }
    await page.waitForTimeout(expectDevEvents ? 500 : 2000);

    const messages = consoleEvents.map((event) => event.text);
    const eventMessages = messages.filter((text) => /^MTR_DEV_EVENT sequence=/i.test(text));
    const sequences = eventMessages
        .map((text) => Number(text.match(/^MTR_DEV_EVENT sequence=(\d+)/i)?.[1]))
        .filter(Number.isSafeInteger);
    const readyMessages = messages.filter((text) => /MTR_DEV_EVENT_QA_READY/i.test(text));
    const failureMessages = messages.filter((text) => /MTR_DEV_EVENT_QA_(?:FAIL|REJECTED)/i.test(text));
    const runtimeReady = messages.some((text) => /MTR_RUNTIME_CORE_READY/i.test(text));
    const exactReady = readyMessages.some((text) => (
        /loops=10\b/i.test(text)
        && /epoch=11\b/i.test(text)
        && /events=33\b/i.test(text)
        && /unique=33\b/i.test(text)
        && /resetBegin=11\b/i.test(text)
        && /resetEnd=11\b/i.test(text)
        && /exportBound=32768\b/i.test(text)
    ));
    const knownWarning = /GL Driver Message .*GPU stall due to ReadPixels/i;
    const consoleErrors = consoleEvents.filter((event) => event.type === 'error').map((event) => event.text);
    const consoleWarnings = consoleEvents
        .filter((event) => event.type === 'warning' && !knownWarning.test(event.text))
        .map((event) => event.text);
    const uniqueSequenceCount = new Set(sequences).size;
    const passed = expectDevEvents
        ? runtimeReady
            && eventMessages.length === 33
            && sequences.length === 33
            && uniqueSequenceCount === 33
            && readyMessages.length === 1
            && exactReady
            && failureMessages.length === 0
        : runtimeReady
            && eventMessages.length === 0
            && readyMessages.length === 0
            && failureMessages.length === 0;
    const diagnosticsPassed = consoleErrors.length === 0
        && consoleWarnings.length === 0
        && pageErrors.length === 0
        && requestFailures.length === 0;

    page.off('console', onConsole);
    page.off('pageerror', onPageError);
    page.off('requestfailed', onRequestFailed);
    return {
        schema: 'mtr.game_root_dev_event_runtime.v1',
        status: passed && diagnosticsPassed ? 'pass' : 'fail',
        expectedMode: expectDevEvents ? 'dev-enabled' : 'release-hard-off',
        runtimeReady,
        eventCount: eventMessages.length,
        uniqueSequenceCount,
        readyCount: readyMessages.length,
        exactReady,
        failureMessages,
        diagnostics: {
            consoleErrors,
            consoleWarnings,
            pageErrors,
            requestFailures,
        },
    };
}
