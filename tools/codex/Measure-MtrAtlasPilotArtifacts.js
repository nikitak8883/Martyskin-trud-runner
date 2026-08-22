#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ALLOWED_ARGUMENTS = new Set([
    '--project-root',
    '--build-root',
    '--output',
    '--phase',
    '--platform',
    '--candidate-source-directory',
]);

function parseArguments(argv) {
    const values = new Map();
    const candidateSourceDirectories = [];
    for (let index = 0; index < argv.length; index += 2) {
        const key = argv[index];
        const value = argv[index + 1];
        if (!key?.startsWith('--') || value === undefined) throw new Error(`Invalid argument near ${key || '<end>'}.`);
        if (!ALLOWED_ARGUMENTS.has(key)) throw new Error(`Unknown argument ${key}.`);
        if (key === '--candidate-source-directory') candidateSourceDirectories.push(value);
        else {
            if (values.has(key)) throw new Error(`Duplicate argument ${key}.`);
            values.set(key, value);
        }
    }
    return {
        projectRoot: values.get('--project-root') || process.cwd(),
        buildRoot: values.get('--build-root'),
        output: values.get('--output'),
        phase: values.get('--phase'),
        platform: values.get('--platform'),
        candidateSourceDirectories: candidateSourceDirectories.length > 0
            ? candidateSourceDirectories
            : ['assets/resources/objectives/npc'],
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

function walkFiles(root, skippedLinks = []) {
    if (!fs.existsSync(root)) return [];
    const files = [];
    const pending = [root];
    while (pending.length > 0) {
        const current = pending.pop();
        for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
            const absolute = path.join(current, entry.name);
            if (entry.isSymbolicLink()) {
                skippedLinks.push(absolute);
                continue;
            }
            if (entry.isDirectory()) pending.push(absolute);
            else if (entry.isFile()) files.push(absolute);
        }
    }
    return files.sort((left, right) => left.localeCompare(right));
}

function summarize(files) {
    return {
        fileCount: files.length,
        totalBytes: files.reduce((sum, file) => sum + fs.statSync(file).size, 0),
    };
}

function writeJsonAtomic(outputPath, value) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    const temporary = `${outputPath}.tmp-${process.pid}-${Date.now()}`;
    fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
    fs.renameSync(temporary, outputPath);
}

function main() {
    const options = parseArguments(process.argv.slice(2));
    if (!/^(baseline|candidate|rollback)$/.test(options.phase || '')) throw new Error('Invalid --phase.');
    if (!/^(web|android_emulator)$/.test(options.platform || '')) throw new Error('Invalid --platform.');
    const projectRoot = path.resolve(options.projectRoot);
    const buildRoot = resolveContained(projectRoot, options.buildRoot, '--build-root');
    const output = resolveContained(projectRoot, options.output, '--output');
    const candidateRoots = options.candidateSourceDirectories.map((directory) => resolveContained(
        projectRoot,
        directory,
        '--candidate-source-directory',
    ));
    if (new Set(candidateRoots.map((root) => root.toLowerCase())).size !== candidateRoots.length) {
        throw new Error('Duplicate --candidate-source-directory values are forbidden.');
    }
    for (let left = 0; left < candidateRoots.length; left += 1) {
        for (let right = left + 1; right < candidateRoots.length; right += 1) {
            const relative = path.relative(candidateRoots[left], candidateRoots[right]);
            const reverse = path.relative(candidateRoots[right], candidateRoots[left]);
            const overlaps = relative === ''
                || (!relative.startsWith('..') && !path.isAbsolute(relative))
                || (!reverse.startsWith('..') && !path.isAbsolute(reverse));
            if (overlaps) throw new Error('Overlapping --candidate-source-directory values are forbidden.');
        }
    }
    if (!fs.statSync(buildRoot).isDirectory()) throw new Error(`Build root is not a directory: ${buildRoot}`);
    for (const candidateRoot of candidateRoots) {
        if (!fs.statSync(candidateRoot).isDirectory()) {
            throw new Error(`Candidate source directory is not a directory: ${candidateRoot}`);
        }
    }

    const skippedLinks = [];
    const files = walkFiles(buildRoot, skippedLinks);
    const runtimeRoot = options.platform === 'android_emulator' ? path.join(buildRoot, 'data') : buildRoot;
    const runtimeFiles = walkFiles(runtimeRoot);
    const resourcesRoot = path.join(runtimeRoot, 'assets', 'resources');
    const resourcesFiles = walkFiles(resourcesRoot);
    const nativeImageFiles = walkFiles(path.join(resourcesRoot, 'native'))
        .filter((file) => /\.(?:png|jpe?g|webp|ktx2?)$/i.test(file));
    const importFiles = walkFiles(path.join(resourcesRoot, 'import'));
    const candidateMetaFiles = candidateRoots.flatMap((candidateRoot) => walkFiles(candidateRoot)
        .filter((file) => file.endsWith('.png.meta')));
    const candidateUuids = candidateMetaFiles
        .map((file) => JSON.parse(fs.readFileSync(file, 'utf8')).uuid)
        .sort();
    if (candidateUuids.some((uuid) => typeof uuid !== 'string' || uuid.length === 0)) {
        throw new Error('Every candidate PNG meta must contain a non-empty UUID.');
    }
    if (new Set(candidateUuids).size !== candidateUuids.length) {
        throw new Error('Candidate PNG UUIDs must be unique across source directories.');
    }
    const candidateUuidArtifacts = runtimeFiles
        .filter((file) => candidateUuids.some((uuid) => path.basename(file).includes(uuid)))
        .map((file) => ({
            path: path.relative(runtimeRoot, file).replaceAll('\\', '/'),
            bytes: fs.statSync(file).size,
        }));
    const extensionTotals = {};
    for (const file of runtimeFiles) {
        const extension = path.extname(file).toLowerCase() || '<none>';
        if (!extensionTotals[extension]) extensionTotals[extension] = { fileCount: 0, totalBytes: 0 };
        extensionTotals[extension].fileCount += 1;
        extensionTotals[extension].totalBytes += fs.statSync(file).size;
    }

    const report = {
        schema: 'mtr.atlas_pilot_artifact_metric.v1',
        phase: options.phase,
        platform: options.platform,
        buildRoot: path.relative(projectRoot, buildRoot).replaceAll('\\', '/'),
        candidateSourceDirectory: candidateRoots.length === 1
            ? path.relative(projectRoot, candidateRoots[0]).replaceAll('\\', '/')
            : null,
        candidateSourceDirectories: candidateRoots
            .map((candidateRoot) => path.relative(projectRoot, candidateRoot).replaceAll('\\', '/')),
        all: summarize(files),
        runtime: summarize(runtimeFiles),
        resources: summarize(resourcesFiles),
        nativeImages: summarize(nativeImageFiles),
        imports: summarize(importFiles),
        candidateSourceCount: candidateUuids.length,
        candidateUuidArtifactCount: candidateUuidArtifacts.length,
        candidateUuidArtifactBytes: candidateUuidArtifacts.reduce((sum, item) => sum + item.bytes, 0),
        candidateUuidArtifacts,
        extensionTotals,
        packageArtifacts: files
            .filter((file) => /\.(?:apk|aab)$/i.test(file))
            .map((file) => ({
                path: path.relative(buildRoot, file).replaceAll('\\', '/'),
                bytes: fs.statSync(file).size,
            })),
        skippedLinks: skippedLinks.map((file) => path.relative(buildRoot, file).replaceAll('\\', '/')),
    };
    writeJsonAtomic(output, report);
    process.stdout.write(`${JSON.stringify({
        status: 'pass',
        phase: report.phase,
        platform: report.platform,
        allFiles: report.all.fileCount,
        runtimeFiles: report.runtime.fileCount,
        runtimeBytes: report.runtime.totalBytes,
        resourcesBytes: report.resources.totalBytes,
        candidateUuidArtifacts: report.candidateUuidArtifactCount,
        skippedLinks: report.skippedLinks.length,
        output: path.relative(projectRoot, output).replaceAll('\\', '/'),
    })}\n`);
}

try {
    main();
} catch (error) {
    process.stderr.write(`${error?.stack || error}\n`);
    process.exitCode = 1;
}
