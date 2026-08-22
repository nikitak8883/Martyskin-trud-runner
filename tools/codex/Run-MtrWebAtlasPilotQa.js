#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const ALLOWED_ARGUMENTS = new Set([
    '--project-root',
    '--url',
    '--output',
    '--runtime-function',
    '--width',
    '--height',
    '--timeout-ms',
]);

function parseArguments(argv) {
    const values = new Map();
    for (let index = 0; index < argv.length; index += 2) {
        const key = argv[index];
        const value = argv[index + 1];
        if (!key?.startsWith('--') || value === undefined) throw new Error(`Invalid argument near ${key || '<end>'}.`);
        if (!ALLOWED_ARGUMENTS.has(key)) throw new Error(`Unknown argument ${key}.`);
        if (values.has(key)) throw new Error(`Duplicate argument ${key}.`);
        values.set(key, value);
    }
    return {
        projectRoot: values.get('--project-root') || process.cwd(),
        url: values.get('--url'),
        output: values.get('--output'),
        runtimeFunction: values.get('--runtime-function') || 'tools/codex/web_atlas_pilot_runtime_function.js',
        width: Number(values.get('--width') || 1280),
        height: Number(values.get('--height') || 720),
        timeoutMs: Number(values.get('--timeout-ms') || 60000),
    };
}

function resolveContained(root, candidate, label) {
    if (!candidate) throw new Error(`${label} is required.`);
    const resolvedRoot = path.resolve(root);
    const resolved = path.resolve(resolvedRoot, candidate);
    const relative = path.relative(resolvedRoot, resolved);
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`${label} escapes project root.`);
    return resolved;
}

function validateLoopbackUrl(value) {
    if (!value) throw new Error('--url is required.');
    const parsed = new URL(value);
    if (parsed.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(parsed.hostname)) {
        throw new Error('--url must use HTTP on 127.0.0.1 or localhost.');
    }
    return parsed.toString();
}

function writeJsonAtomic(outputPath, value) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    const temporary = `${outputPath}.tmp-${process.pid}-${Date.now()}`;
    fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
    fs.renameSync(temporary, outputPath);
}

async function main() {
    const options = parseArguments(process.argv.slice(2));
    if (!Number.isSafeInteger(options.width) || options.width < 320 || options.width > 4096) throw new Error('Invalid --width.');
    if (!Number.isSafeInteger(options.height) || options.height < 240 || options.height > 2160) throw new Error('Invalid --height.');
    if (!Number.isSafeInteger(options.timeoutMs) || options.timeoutMs < 10000 || options.timeoutMs > 120000) {
        throw new Error('Invalid --timeout-ms.');
    }
    const projectRoot = path.resolve(options.projectRoot);
    const output = resolveContained(projectRoot, options.output, '--output');
    const runtimeFunctionPath = resolveContained(projectRoot, options.runtimeFunction, '--runtime-function');
    const url = validateLoopbackUrl(options.url);
    const source = fs.readFileSync(runtimeFunctionPath, 'utf8');
    const runtimeFunction = Function(`"use strict"; return (${source});`)();
    if (typeof runtimeFunction !== 'function') throw new Error('Runtime function did not evaluate to a function.');

    process.chdir(projectRoot);
    const browser = await chromium.launch({ headless: true });
    try {
        const context = await browser.newContext({ viewport: { width: options.width, height: options.height } });
        const page = await context.newPage();
        page.setDefaultTimeout(options.timeoutMs);
        await page.goto(url, { waitUntil: 'commit', timeout: options.timeoutMs });
        const report = await runtimeFunction(page);
        writeJsonAtomic(output, report);
        process.stdout.write(`${JSON.stringify({
            status: report.status,
            phase: report.phase,
            atlasId: report.atlasId,
            output: path.relative(projectRoot, output).replaceAll('\\', '/'),
        })}\n`);
        if (report.status !== 'pass') process.exitCode = 1;
        await context.close();
    } finally {
        await browser.close();
    }
}

main().catch((error) => {
    process.stderr.write(`${error?.stack || error}\n`);
    process.exitCode = 1;
});
