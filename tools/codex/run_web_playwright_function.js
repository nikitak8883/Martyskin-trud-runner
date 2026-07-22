'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');
const playwrightVersion = require('playwright-core/package.json').version;

function resolveBrowserExecutable() {
    let managedExecutable = null;
    try {
        managedExecutable = chromium.executablePath();
    } catch {
        // Fall through to an explicitly configured or system browser.
    }

    const under = (base, ...parts) => base ? path.join(base, ...parts) : null;
    const candidates = [
        process.env.MTR_PLAYWRIGHT_BROWSER_EXECUTABLE,
        managedExecutable,
    ];

    if (process.platform === 'win32') {
        candidates.push(
            under(process.env.PROGRAMFILES, 'Google', 'Chrome', 'Application', 'chrome.exe'),
            under(process.env['PROGRAMFILES(X86)'], 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
            under(process.env.LOCALAPPDATA, 'Google', 'Chrome', 'Application', 'chrome.exe'),
        );
    } else if (process.platform === 'darwin') {
        candidates.push(
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
        );
    } else {
        candidates.push(
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
        );
    }

    const executable = candidates.find(
        (candidate) => candidate && path.isAbsolute(candidate) && fs.existsSync(candidate),
    );
    if (!executable) {
        throw new Error(
            'No Chromium-family browser found. Set MTR_PLAYWRIGHT_BROWSER_EXECUTABLE '
            + 'or run `npx playwright-core install chromium`.',
        );
    }
    return path.resolve(executable);
}

function evaluateResult(summary) {
    if (summary?.schema === 'mtr.web_soak.v1') {
        return Boolean(
            summary.complete
            && summary.elapsedMs >= summary.targetDurationSeconds * 1000
            && summary.inputBursts > 0
            && summary.consoleErrors?.length === 0
            && summary.consoleWarnings?.length === 0,
        );
    }
    return summary?.status === 'pass';
}

function compactResult(summary, summaryPath, passed) {
    if (summary?.schema === 'mtr.web_soak.v1') {
        return {
            status: passed ? 'pass' : 'fail',
            complete: summary.complete,
            durationSeconds: Number((summary.elapsedMs / 1000).toFixed(3)),
            finalState: summary.finalState,
            inputBursts: summary.inputBursts,
            clearClicks: summary.clearClicks,
            overClicks: summary.overClicks,
            finishedClicks: summary.finishedClicks,
            consoleErrors: summary.consoleErrors?.length || 0,
            consoleWarnings: summary.consoleWarnings?.length || 0,
            fpsSamples: summary.fpsSamples?.length || 0,
            heapSamples: summary.heapSamples?.length || 0,
            summary: path.resolve(summaryPath),
        };
    }
    return {
        status: summary?.status || (passed ? 'pass' : 'fail'),
        cases: summary?.caseCount,
        passed: summary?.passCount,
        failed: summary?.failCount,
        portrait: summary?.portraitTouch?.status,
        interaction: summary?.interaction?.status,
        restartsPassed: summary?.restartLoop?.passCount,
        restartsFailed: summary?.restartLoop?.failCount,
        summary: path.resolve(summaryPath),
    };
}

async function main() {
    const [, , url, functionPath, summaryPath] = process.argv;
    if (!url || !functionPath || !summaryPath) {
        throw new Error('Usage: node run_web_playwright_function.js <url> <function.js> <summary.json>');
    }

    const source = fs.readFileSync(path.resolve(functionPath), 'utf8');
    const run = Function(`"use strict"; return (${source});`)();
    if (typeof run !== 'function') throw new Error('Playwright source did not evaluate to a function.');

    fs.mkdirSync(path.resolve('output/playwright/cycle2'), { recursive: true });
    fs.mkdirSync(path.dirname(path.resolve(summaryPath)), { recursive: true });

    const browserExecutable = resolveBrowserExecutable();
    const browser = await chromium.launch({
        headless: true,
        executablePath: browserExecutable,
        args: [
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--ignore-gpu-blocklist',
        ],
    });

    try {
        const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
        const page = await context.newPage();
        await page.goto(url, { waitUntil: 'load', timeout: 30000 });
        const summary = await run(page);
        summary.runner = {
            package: 'playwright-core',
            packageVersion: playwrightVersion,
            browserExecutable,
            browserVersion: browser.version(),
            nodeVersion: process.version,
        };
        const passed = evaluateResult(summary);
        fs.writeFileSync(path.resolve(summaryPath), `${JSON.stringify(summary, null, 2)}\n`, 'utf8');
        process.stdout.write(`${JSON.stringify(compactResult(summary, summaryPath, passed))}\n`);
        if (!passed) process.exitCode = 1;
        await context.close();
    } finally {
        await browser.close();
    }
}

main().catch((error) => {
    process.stderr.write(`${error?.stack || error}\n`);
    process.exitCode = 1;
});
