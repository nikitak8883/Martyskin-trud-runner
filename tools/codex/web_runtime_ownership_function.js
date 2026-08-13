async (page) => {
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

    const url = new URL('/index.html', page.url());
    url.searchParams.set('mtr_dev', '1');
    url.searchParams.set('mtr_autostart', '1');
    url.searchParams.set('mtr_level', '1');
    url.searchParams.set('mtr_qa_ownership', '1');
    url.searchParams.set('mtr_cache_bust', `${Date.now()}_runtime_ownership`);

    const deadline = Date.now() + 45000;
    await page.goto(url.href, { waitUntil: 'load', timeout: 30000 });
    while (Date.now() < deadline) {
        const messages = consoleEvents.map((event) => event.text);
        if (messages.some((text) => /MTR_OWNERSHIP_QA_(?:READY|FAIL)/i.test(text))) break;
        await page.waitForTimeout(100);
    }
    await page.waitForTimeout(500);

    const messages = consoleEvents.map((event) => event.text);
    const readyMessages = messages.filter((text) => /MTR_OWNERSHIP_QA_READY/i.test(text));
    const failureMessages = messages.filter((text) => /MTR_OWNERSHIP_QA_FAIL/i.test(text));
    const runtimeReady = messages.some((text) => /MTR_RUNTIME_CORE_READY/i.test(text));
    const exactReady = readyMessages.some((text) => (
        /checks=8\/8\b/i.test(text)
        && /listeners=8\b/i.test(text)
        && /sessionCancelled=1\b/i.test(text)
        && /componentSurvived=1\b/i.test(text)
        && /uiTransition=1\b/i.test(text)
        && /state=playing\b/i.test(text)
    ));
    const knownWarning = /GL Driver Message .*GPU stall due to ReadPixels/i;
    const consoleErrors = consoleEvents.filter((event) => event.type === 'error').map((event) => event.text);
    const consoleWarnings = consoleEvents
        .filter((event) => event.type === 'warning' && !knownWarning.test(event.text))
        .map((event) => event.text);
    const passed = runtimeReady
        && readyMessages.length === 1
        && exactReady
        && failureMessages.length === 0
        && consoleErrors.length === 0
        && consoleWarnings.length === 0
        && pageErrors.length === 0
        && requestFailures.length === 0;

    page.off('console', onConsole);
    page.off('pageerror', onPageError);
    page.off('requestfailed', onRequestFailed);
    return {
        schema: 'mtr.web_runtime_ownership.v1',
        status: passed ? 'pass' : 'fail',
        runtimeReady,
        readyCount: readyMessages.length,
        exactReady,
        readyMessages,
        failureMessages,
        diagnostics: { consoleErrors, consoleWarnings, pageErrors, requestFailures },
    };
}
