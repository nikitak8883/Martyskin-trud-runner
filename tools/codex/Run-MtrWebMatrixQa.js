#!/usr/bin/env node
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const vm = require('vm');

function parseArguments(argv) {
    const values = new Map();
    for (let index = 0; index < argv.length; index += 1) {
        const key = argv[index];
        if (!key.startsWith('--')) throw new Error(`Unexpected argument: ${key}`);
        if (key === '--help') return { help: true };
        const value = argv[index + 1];
        if (!value || value.startsWith('--')) throw new Error(`Missing value for ${key}`);
        values.set(key, value);
        index += 1;
    }
    return {
        help: false,
        projectRoot: values.get('--project-root') || process.cwd(),
        url: values.get('--url'),
        output: values.get('--output'),
        screenshotRoot: values.get('--screenshot-root'),
        source: values.get('--source') || 'tools/codex/web_matrix_playwright_function.js',
        cycle: Number(values.get('--cycle') || '1'),
        cycleLabel: values.get('--cycle-label') || 'cli_cycle',
    };
}

function printHelp() {
    process.stdout.write([
        'Usage: node tools/codex/Run-MtrWebMatrixQa.js',
        '  --project-root <path> --url <http://127.0.0.1:port/index.html>',
        '  --output <project-relative.json> --screenshot-root <project-relative-dir>',
        '  --cycle <positive integer> --cycle-label <safe label>',
        '',
    ].join('\n'));
}

function resolveContained(root, candidate, label) {
    if (!candidate) throw new Error(`${label} is required.`);
    const resolvedRoot = path.resolve(root);
    const resolved = path.resolve(resolvedRoot, candidate);
    const relative = path.relative(resolvedRoot, resolved);
    if (relative.startsWith('..') || path.isAbsolute(relative)) {
        throw new Error(`${label} escapes the project root: ${candidate}`);
    }
    return resolved;
}

function loadPlaywright() {
    const candidates = [];
    if (process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES) {
        candidates.push(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES, 'playwright', 'index.js'));
    }
    candidates.push(path.join(
        os.homedir(),
        '.cache',
        'codex-runtimes',
        'codex-primary-runtime',
        'dependencies',
        'node',
        'node_modules',
        'playwright',
        'index.js',
    ));

    try {
        return { playwright: require('playwright'), identity: require.resolve('playwright') };
    } catch (error) {
        for (const candidate of candidates) {
            if (!fs.existsSync(candidate)) continue;
            return { playwright: require(candidate), identity: candidate };
        }
        throw new Error(`Playwright runtime was not found. Checked: ${candidates.join(', ')}. Initial error: ${error.message}`);
    }
}

function replaceExactlyOnce(source, pattern, replacement, label) {
    const matches = source.match(new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : `${pattern.flags}g`));
    if (!matches || matches.length !== 1) {
        throw new Error(`${label} replacement expected exactly one match, found ${matches ? matches.length : 0}.`);
    }
    return source.replace(pattern, replacement);
}

function writeJsonAtomic(outputPath, value) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    const temporaryPath = `${outputPath}.tmp-${process.pid}-${Date.now()}`;
    fs.writeFileSync(temporaryPath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
    fs.renameSync(temporaryPath, outputPath);
}

async function main() {
    const options = parseArguments(process.argv.slice(2));
    if (options.help) {
        printHelp();
        return;
    }
    if (!Number.isSafeInteger(options.cycle) || options.cycle < 1 || options.cycle > 9999) {
        throw new Error(`--cycle must be an integer in 1..9999, got ${options.cycle}.`);
    }
    if (!/^[a-z0-9][a-z0-9_-]{2,63}$/i.test(options.cycleLabel)) {
        throw new Error(`--cycle-label is not safe: ${options.cycleLabel}`);
    }
    if (!options.url) throw new Error('--url is required.');
    const targetUrl = new URL(options.url);
    if (targetUrl.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(targetUrl.hostname)) {
        throw new Error(`Only a local HTTP QA URL is accepted, got ${options.url}.`);
    }

    const projectRoot = path.resolve(options.projectRoot);
    const outputPath = resolveContained(projectRoot, options.output, '--output');
    const screenshotRoot = resolveContained(projectRoot, options.screenshotRoot, '--screenshot-root');
    const sourcePath = resolveContained(projectRoot, options.source, '--source');
    fs.mkdirSync(screenshotRoot, { recursive: true });

    let source = fs.readFileSync(sourcePath, 'utf8');
    source = replaceExactlyOnce(
        source,
        /const cycle = 'cycle2';/,
        `const cycle = ${JSON.stringify(options.cycleLabel)};`,
        'cycle label',
    );
    source = replaceExactlyOnce(
        source,
        /const screenshotRoot = `output\/playwright\/\$\{cycle\}`;/,
        `const screenshotRoot = ${JSON.stringify(screenshotRoot.replaceAll('\\', '/'))};`,
        'screenshot root',
    );
    source = replaceExactlyOnce(source, /cycle: 2,/, `cycle: ${options.cycle},`, 'cycle number');
    const matrixFunction = vm.runInThisContext(`(${source})`, { filename: sourcePath });
    if (typeof matrixFunction !== 'function') throw new Error('Web matrix source did not evaluate to a function.');

    const runtime = loadPlaywright();
    let browser;
    try {
        browser = await runtime.playwright.chromium.launch({ headless: true });
        const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
        const page = await context.newPage();
        await page.goto(targetUrl.href, { waitUntil: 'load', timeout: 30000 });
        const report = await matrixFunction(page);
        if (!report || report.schema !== 'mtr.web_matrix_interaction.v1') {
            throw new Error(`Unexpected Web matrix schema: ${report && report.schema}`);
        }
        writeJsonAtomic(outputPath, report);
        process.stdout.write(`${JSON.stringify({
            status: report.status,
            cycle: report.cycle,
            caseCount: report.caseCount,
            passCount: report.passCount,
            failCount: report.failCount,
            interaction: report.interaction && report.interaction.status,
            restartPassCount: report.restartLoop && report.restartLoop.passCount,
            output: path.relative(projectRoot, outputPath).replaceAll('\\', '/'),
            playwright: runtime.identity,
        })}\n`);
        if (report.status !== 'pass') process.exitCode = 1;
    } finally {
        if (browser) await browser.close();
    }
}

main().catch((error) => {
    process.stderr.write(`${error.stack || error.message || error}\n`);
    process.exitCode = 1;
});
