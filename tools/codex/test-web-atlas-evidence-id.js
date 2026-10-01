'use strict';
const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const source = fs.readFileSync(path.join(__dirname, 'web_atlas_pilot_runtime_function.js'), 'utf8');
const run = Function(`"use strict"; return (${source});`)();

async function testId(id, expectedId, rejects = false, screenshotFails = false) {
    let captured;
    let events = 0;
    const query = new URLSearchParams({ mtr_qa_atlas_pilot: 'level_theme_logistics', mtr_qa_atlas_phase: 'baseline' });
    if (id !== null) query.set('mtr_qa_atlas_evidence_id', id);
    const page = {
        url: () => `http://127.0.0.1:8133/index.html?${query}`,
        on: (type, callback) => {
            events++;
            if (type === 'console') callback({ type: () => 'log', location: () => ({}), text: () => 'MTR_ATLAS_PILOT_COMPLETE {}' });
        },
        off: () => {},
        waitForTimeout: async () => {},
        screenshot: async ({ path: filename }) => { if (screenshotFails) throw new Error('expected screenshot failure'); captured = filename; },
    };
    if (rejects) {
        await assert.rejects(() => run(page), /Unsafe atlas pilot evidence id/);
        assert.equal(events, 0, 'Unsafe ID must fail before page hooks/files');
    } else if (screenshotFails) {
        await assert.rejects(() => run(page), /expected screenshot failure/);
    } else {
        const report = await run(page);
        assert.equal(report.phase, 'baseline', 'Evidence ID must not relabel metrics');
        assert.equal(report.evidenceId, expectedId);
        assert.equal(captured, `temp/m04-c-families/level_theme_logistics/${expectedId}/web/atlas-family.png`);
    }
}
async function main() {
    // Runtime harness uses a 45s marker timer; don't keep this mocked test alive.
    const originalSetTimeout = global.setTimeout;
    const originalClearTimeout = global.clearTimeout;
    const activeTimers = new Set();
    global.setTimeout = (callback, delay) => { const timer = originalSetTimeout(callback, delay); timer.unref(); activeTimers.add(timer); return timer; };
    global.clearTimeout = (timer) => { activeTimers.delete(timer); return originalClearTimeout(timer); };
    try {
        await testId(null, 'baseline');
        await testId('a02_p01_baseline', 'a02_p01_baseline');
        assert.equal(activeTimers.size, 0, 'Successful terminal must cancel its timer');
        for (const invalid of ['../old', 'x/y', 'x\\y', 'x%2fy', 'x'.repeat(65), '<script>']) await testId(invalid, '', true);
        await testId('a02_exception', 'a02_exception', false, true);
        assert.equal(activeTimers.size, 0, 'Exception must cancel its terminal timer');
        process.stdout.write(JSON.stringify({ status: 'PASS', testsPassed: 10, testsTotal: 10, filesystemWrites: 0, activeTerminalTimers: activeTimers.size }) + '\n');
    } finally { for (const timer of activeTimers) originalClearTimeout(timer); global.setTimeout = originalSetTimeout; global.clearTimeout = originalClearTimeout; }
}
main().catch((error) => { process.stderr.write(`${error.stack}\n`); process.exitCode = 1; });
