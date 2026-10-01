'use strict';

const childProcess = require('child_process');
const fs = require('fs');
const path = require('path');

function assessSnapshot(processes, projectRoot, excludedPids = []) {
  const excluded = new Set(excludedPids.map(Number));
  const normalizedRoot = path.resolve(projectRoot).replace(/\\/g, '/').toLowerCase();
  const escapedRoot = normalizedRoot.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const rootPattern = new RegExp(`${escapedRoot}(?:/|\\s|["']|$)`);
  const blockers = [];
  for (const item of processes) {
    if (excluded.has(Number(item.ProcessId))) continue;
    const name = String(item.Name || '').toLowerCase();
    const command = String(item.CommandLine || '').replace(/\\/g, '/').toLowerCase();
    const projectScoped = rootPattern.test(command);
    let kind;
    if (/run-mtrcocosbuild\.ps1(?:\s|"|$)/.test(command)) kind = 'mtr-build-wrapper';
    else if (projectScoped && name === 'cocoscreator.exe' && /(?:^|\s)--build(?:\s|=)/.test(command)) kind = 'cocos-export';
    else if (projectScoped && /^(?:ninja|clang\+\+|cmake|java)\.exe$/.test(name)) kind = 'project-native-build';
    else if (/run-mtr(?:web(?:matrix|atlaspilot)qa\.js|android(?:atlaspilot|emulatormatrix|emulatorinteraction)qa\.ps1)(?:\s|"|$)/.test(command)) kind = 'other-mtr-runtime-qa';
    if (kind) blockers.push({ pid: Number(item.ProcessId), process: name, kind });
  }
  return {
    contract: 'mtr.runtime_qa_host_preflight', schema_version: 1,
    status: blockers.length ? 'blocked' : 'pass', blockers,
    policy: 'isolated-runtime-measurement-no-parallel-MTR-build-or-QA',
    mutation: false,
    limitation: 'Read-only start-time snapshot, not an interprocess lock; orchestration must serialize measurement pairs.',
  };
}

function checkHost(projectRoot) {
  if (process.platform !== 'win32') return { status: 'not_applicable', reason: 'Win32 local-process probe unavailable; serialize measurement pairs in orchestration.' };
  const raw = childProcess.execFileSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
    'Get-CimInstance Win32_Process -ErrorAction Stop | Select-Object Name,ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress'],
  { encoding: 'utf8', timeout: 20000, maxBuffer: 4 * 1024 * 1024, windowsHide: true }).replace(/^\uFEFF/, '').trim();
  const parsed = JSON.parse(raw || '[]');
  const processes = Array.isArray(parsed) ? parsed : [parsed];
  const ancestors = new Set([process.pid]);
  let pid = process.ppid;
  while (pid > 0 && !ancestors.has(pid)) {
    ancestors.add(pid);
    pid = Number(processes.find(item => Number(item.ProcessId) === pid)?.ParentProcessId || 0);
  }
  return assessSnapshot(processes, projectRoot, [...ancestors]);
}

function assertHostQuiescent(projectRoot) {
  const report = checkHost(projectRoot);
  if (report.status === 'blocked') throw new Error(`Runtime QA host preflight blocked: ${JSON.stringify(report)}`);
  return report;
}

if (require.main === module) {
  try {
    if (process.argv.length !== 4 || process.argv[2] !== '--project-root') throw new Error('Usage: node runtime_qa_host_guard.js --project-root <path>');
    const root = path.resolve(process.argv[3]);
    if (!fs.statSync(root).isDirectory()) throw new Error('Project root is not a directory');
    const report = checkHost(root);
    process.stdout.write(`${JSON.stringify(report)}\n`);
    if (report.status === 'blocked') process.exitCode = 1;
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}

module.exports = { assessSnapshot, checkHost, assertHostQuiescent };
