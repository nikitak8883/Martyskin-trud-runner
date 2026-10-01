'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const toolchainRoot = path.join(__dirname, 'node-test-toolchain');
const compilerVersion = '5.8.2';
// Official npm compiler and the qualified Creator3.8.8 compiler are identical.
const compilerSha256 = '795e49e46d497cc16e4b02916b50cbca257b4256d62cddc4cc504103f7961027';
const compilerIntegrity = 'sha512-aJn6wq13/afZp/jT9QZmwEjDqqvSGp1VT5GVg+f/t6/oVyrgXM6BY1h9BRh/O5p3PlUPAe+WuiEZOmb/49RqoQ==';
const installCommand = 'npm ci --prefix tools/codex/node-test-toolchain --ignore-scripts --no-audit --no-fund';

function validateTestToolchainManifest(manifest, lock) {
  const exactDependency = value => value && Object.keys(value).length === 1 && value.typescript === compilerVersion;
  if (manifest.name !== 'mtr-node-test-toolchain' || manifest.private !== true
      || !exactDependency(manifest.dependencies) || Object.keys(manifest.scripts || {}).length
      || Object.keys(manifest.devDependencies || {}).length) {
    throw new Error('Invalid isolated test toolchain manifest');
  }
  const packages = lock.packages || {};
  const root = packages[''] || {};
  const compiler = packages['node_modules/typescript'] || {};
  if (lock.lockfileVersion !== 3 || lock.name !== manifest.name || lock.version !== manifest.version
      || Object.keys(packages).sort().join('|') !== '|node_modules/typescript'
      || !exactDependency(root.dependencies) || root.version !== manifest.version
      || compiler.version !== compilerVersion
      || compiler.resolved !== `https://registry.npmjs.org/typescript/-/typescript-${compilerVersion}.tgz`
      || compiler.integrity !== compilerIntegrity || compiler.hasInstallScript === true
      || Object.keys(compiler.dependencies || {}).length) {
    throw new Error('Invalid isolated test compiler lock');
  }
  return true;
}

function inspectCompiler(compilerPath) {
  if (!path.isAbsolute(compilerPath)) throw new Error('Test compiler path must be absolute');
  const resolved = fs.realpathSync(compilerPath);
  const packageRoot = path.resolve(path.dirname(resolved), '..');
  const metadata = JSON.parse(fs.readFileSync(path.join(packageRoot, 'package.json'), 'utf8'));
  if (metadata.name !== 'typescript' || metadata.version !== compilerVersion) {
    throw new Error(`Test compiler version mismatch: expected typescript@${compilerVersion}`);
  }
  const hash = crypto.createHash('sha256').update(fs.readFileSync(resolved)).digest('hex');
  if (hash !== compilerSha256) throw new Error('Test compiler SHA-256 mismatch');
  return { compilerPath: resolved, compilerVersion, compilerSha256 };
}

function loadTestTypeScript(options = {}) {
  const root = path.resolve(options.toolchainRoot || toolchainRoot);
  validateTestToolchainManifest(
    JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')),
    JSON.parse(fs.readFileSync(path.join(root, 'package-lock.json'), 'utf8')),
  );
  const override = Object.hasOwn(options, 'override') ? options.override : process.env.COCOS_TYPESCRIPT_JS;
  const packageRoot = path.join(root, 'node_modules', 'typescript');
  const compilerPath = override || path.join(packageRoot, 'lib', 'typescript.js');
  let observation;
  try {
    observation = inspectCompiler(compilerPath);
  } catch (error) {
    throw new Error(`Pinned test compiler unavailable or invalid: ${error.message}. Install with: ${installCommand}`);
  }
  if (!override) {
    const expectedRoot = fs.realpathSync(packageRoot);
    if (!expectedRoot.startsWith(fs.realpathSync(root) + path.sep)
        || path.resolve(path.dirname(observation.compilerPath), '..') !== expectedRoot) {
      throw new Error('Pinned test compiler escapes its isolated package');
    }
  }
  // No require()/execution of the compiler until its version and bytes pass.
  const compiler = require(observation.compilerPath);
  if (compiler.version !== compilerVersion) throw new Error('Loaded test compiler version mismatch');
  return { ...observation, compiler, source: override ? 'explicit-verified-override' : 'isolated-lock' };
}

module.exports = { loadTestTypeScript, inspectCompiler, validateTestToolchainManifest, compilerVersion, compilerSha256, installCommand };
