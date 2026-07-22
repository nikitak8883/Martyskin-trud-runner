'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function parseArgs(argv) {
  const args = {
    source: 'assets/scripts/GameRoot.ts',
    output: 'docs/global_modernization/v3/M03/game_root_inventory.generated.json',
    typescript: process.env.COCOS_TYPESCRIPT_JS
      || 'C:/ProgramData/cocos/editors/Creator/3.8.8/resources/app.asar.unpacked/node_modules/typescript/lib/typescript.js',
  };
  for (let index = 2; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === '--source' || key === '--output' || key === '--typescript') {
      if (!value) throw new Error(`Missing value for ${key}`);
      args[key.slice(2)] = value;
      index += 1;
    } else {
      throw new Error(`Unknown argument: ${key}`);
    }
  }
  return args;
}

function normalizeText(node, sourceFile) {
  return node.getText(sourceFile).replace(/\s+/g, ' ').trim();
}

function lineOf(node, sourceFile) {
  return sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;
}

function endLineOf(node, sourceFile) {
  return sourceFile.getLineAndCharacterOfPosition(node.getEnd()).line + 1;
}

function visibilityOf(ts, node) {
  const modifiers = node.modifiers || [];
  if (modifiers.some((modifier) => modifier.kind === ts.SyntaxKind.PublicKeyword)) return 'public';
  if (modifiers.some((modifier) => modifier.kind === ts.SyntaxKind.ProtectedKeyword)) return 'protected';
  if (modifiers.some((modifier) => modifier.kind === ts.SyntaxKind.PrivateKeyword)) return 'private';
  return 'public';
}

function hasModifier(ts, node, kind) {
  return Boolean((node.modifiers || []).some((modifier) => modifier.kind === kind));
}

function decoratorNames(ts, node, sourceFile) {
  if (!ts.canHaveDecorators(node)) return [];
  return (ts.getDecorators(node) || []).map((decorator) => {
    const expression = decorator.expression;
    if (ts.isCallExpression(expression)) return normalizeText(expression.expression, sourceFile);
    return normalizeText(expression, sourceFile);
  });
}

function propertyRoot(ts, expression) {
  let current = expression;
  const names = [];
  while (ts.isPropertyAccessExpression(current) || ts.isElementAccessExpression(current)) {
    if (ts.isPropertyAccessExpression(current)) names.unshift(current.name.text);
    current = current.expression;
  }
  if (current.kind !== ts.SyntaxKind.ThisKeyword || names.length === 0) return null;
  return names[0];
}

function methodName(ts, member, sourceFile) {
  if (ts.isConstructorDeclaration(member)) return 'constructor';
  if (!member.name) return '<anonymous>';
  if (ts.isIdentifier(member.name) || ts.isStringLiteral(member.name) || ts.isNumericLiteral(member.name)) {
    return member.name.text;
  }
  return normalizeText(member.name, sourceFile);
}

function callName(ts, expression, sourceFile) {
  if (ts.isPropertyAccessExpression(expression)) return normalizeText(expression, sourceFile);
  if (ts.isIdentifier(expression)) return expression.text;
  return normalizeText(expression, sourceFile);
}

function literalOrText(ts, node, sourceFile) {
  if (!node) return null;
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  return normalizeText(node, sourceFile).slice(0, 240);
}

function uniqueSorted(values) {
  return [...new Set(values)].sort((left, right) => left.localeCompare(right));
}

function main() {
  const args = parseArgs(process.argv);
  const root = process.cwd();
  const sourcePath = path.resolve(root, args.source);
  const outputPath = path.resolve(root, args.output);
  const typescriptPath = path.resolve(args.typescript);
  if (!fs.existsSync(typescriptPath)) throw new Error(`TypeScript runtime not found: ${typescriptPath}`);
  if (!fs.existsSync(sourcePath)) throw new Error(`Source not found: ${sourcePath}`);

  const ts = require(typescriptPath);
  const sourceText = fs.readFileSync(sourcePath, 'utf8');
  const sourceFile = ts.createSourceFile(sourcePath, sourceText, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const parseDiagnostics = sourceFile.parseDiagnostics.map((diagnostic) => ({
    line: diagnostic.start === undefined ? null : sourceFile.getLineAndCharacterOfPosition(diagnostic.start).line + 1,
    code: diagnostic.code,
    message: ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n'),
  }));

  const imports = sourceFile.statements
    .filter(ts.isImportDeclaration)
    .map((statement) => ({
      module: statement.moduleSpecifier.text,
      line: lineOf(statement, sourceFile),
      clause: statement.importClause ? normalizeText(statement.importClause, sourceFile) : '',
    }));
  const classNode = sourceFile.statements.find(
    (statement) => ts.isClassDeclaration(statement) && statement.name && statement.name.text === 'GameRoot',
  );
  if (!classNode) throw new Error('GameRoot class declaration not found');

  const propertyNodes = classNode.members.filter(ts.isPropertyDeclaration);
  const behaviorNodes = classNode.members.filter((member) => (
    ts.isMethodDeclaration(member)
    || ts.isConstructorDeclaration(member)
    || ts.isGetAccessorDeclaration(member)
    || ts.isSetAccessorDeclaration(member)
  ));
  const methodNames = new Set(behaviorNodes.map((member) => methodName(ts, member, sourceFile)));
  const callEdges = [];
  const listeners = [];
  const timers = [];
  const storage = [];
  const resourceLoads = [];
  const sceneNodes = [];
  const sceneOperations = [];
  const fieldWriteOwners = new Map();

  function recordFieldWrite(field, owner) {
    if (!field) return;
    if (!fieldWriteOwners.has(field)) fieldWriteOwners.set(field, new Set());
    fieldWriteOwners.get(field).add(owner);
  }

  const methods = behaviorNodes.map((member) => {
    const owner = methodName(ts, member, sourceFile);
    const internalCalls = [];
    const externalCalls = [];
    const writtenFields = [];

    function recordWrite(field) {
      if (!field) return;
      writtenFields.push(field);
      recordFieldWrite(field, owner);
    }

    function visit(node) {
      if (ts.isBinaryExpression(node)
        && node.operatorToken.kind >= ts.SyntaxKind.FirstAssignment
        && node.operatorToken.kind <= ts.SyntaxKind.LastAssignment) {
        recordWrite(propertyRoot(ts, node.left));
      }
      if ((ts.isPrefixUnaryExpression(node) || ts.isPostfixUnaryExpression(node))
        && (node.operator === ts.SyntaxKind.PlusPlusToken || node.operator === ts.SyntaxKind.MinusMinusToken)) {
        recordWrite(propertyRoot(ts, node.operand));
      }
      if (ts.isNewExpression(node) && normalizeText(node.expression, sourceFile) === 'Node') {
        sceneNodes.push({
          owner,
          line: lineOf(node, sourceFile),
          name: literalOrText(ts, node.arguments && node.arguments[0], sourceFile),
        });
      }
      if (ts.isCallExpression(node)) {
        const called = callName(ts, node.expression, sourceFile);
        const calledTail = called.split('.').pop();
        const internalMatch = /^this\.([A-Za-z_$][A-Za-z0-9_$]*)$/.exec(called);
        if (internalMatch && methodNames.has(internalMatch[1])) {
          internalCalls.push(internalMatch[1]);
          callEdges.push({ caller: owner, callee: internalMatch[1], line: lineOf(node, sourceFile) });
        } else {
          externalCalls.push(called);
        }

        if (ts.isPropertyAccessExpression(node.expression)) {
          const receiver = normalizeText(node.expression.expression, sourceFile);
          const operation = node.expression.name.text;
          if (['push', 'pop', 'shift', 'unshift', 'splice', 'sort', 'reverse'].includes(operation)) {
            recordWrite(propertyRoot(ts, node.expression.expression));
          }
          if (['on', 'once', 'addEventListener', 'off', 'removeEventListener'].includes(operation)) {
            listeners.push({
              owner,
              line: lineOf(node, sourceFile),
              action: ['on', 'once', 'addEventListener'].includes(operation) ? 'register' : 'unregister',
              api: operation,
              source: receiver,
              event: literalOrText(ts, node.arguments[0], sourceFile),
              handler: literalOrText(ts, node.arguments[1], sourceFile),
            });
          }
          if (['schedule', 'scheduleOnce', 'unschedule', 'unscheduleAllCallbacks', 'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval'].includes(operation)) {
            timers.push({
              owner,
              line: lineOf(node, sourceFile),
              api: operation,
              source: receiver,
              callback: literalOrText(ts, node.arguments[0], sourceFile),
              delay: literalOrText(ts, node.arguments[1], sourceFile),
            });
          }
          if (['getItem', 'setItem', 'removeItem', 'clear'].includes(operation) && receiver.includes('localStorage')) {
            storage.push({
              owner,
              line: lineOf(node, sourceFile),
              operation,
              key: literalOrText(ts, node.arguments[0], sourceFile),
            });
          }
          if (called === 'resources.load') {
            resourceLoads.push({
              owner,
              line: lineOf(node, sourceFile),
              key: literalOrText(ts, node.arguments[0], sourceFile),
              type: literalOrText(ts, node.arguments[1], sourceFile),
            });
          }
          if (['addChild', 'addComponent', 'setSiblingIndex'].includes(operation)) {
            sceneOperations.push({
              owner,
              line: lineOf(node, sourceFile),
              operation,
              target: receiver,
              argument: literalOrText(ts, node.arguments[0], sourceFile),
            });
          }
        } else if (['setTimeout', 'setInterval', 'clearTimeout', 'clearInterval'].includes(calledTail)) {
          timers.push({
            owner,
            line: lineOf(node, sourceFile),
            api: calledTail,
            source: '<global>',
            callback: literalOrText(ts, node.arguments[0], sourceFile),
            delay: literalOrText(ts, node.arguments[1], sourceFile),
          });
        }
      }
      ts.forEachChild(node, visit);
    }
    if (member.body) visit(member.body);

    const startLine = lineOf(member, sourceFile);
    const endLine = endLineOf(member, sourceFile);
    return {
      name: owner,
      kind: ts.isConstructorDeclaration(member)
        ? 'constructor'
        : ts.isGetAccessorDeclaration(member)
          ? 'getter'
          : ts.isSetAccessorDeclaration(member)
            ? 'setter'
            : 'method',
      start_line: startLine,
      end_line: endLine,
      line_count: endLine - startLine + 1,
      visibility: visibilityOf(ts, member),
      async: hasModifier(ts, member, ts.SyntaxKind.AsyncKeyword),
      parameters: member.parameters.map((parameter) => normalizeText(parameter, sourceFile)),
      return_type: member.type ? normalizeText(member.type, sourceFile) : '<inferred>',
      internal_calls: uniqueSorted(internalCalls),
      external_calls: uniqueSorted(externalCalls),
      written_fields: uniqueSorted(writtenFields),
    };
  });

  const properties = propertyNodes.map((member) => ({
    name: methodName(ts, member, sourceFile),
    line: lineOf(member, sourceFile),
    visibility: visibilityOf(ts, member),
    readonly: hasModifier(ts, member, ts.SyntaxKind.ReadonlyKeyword),
    optional: Boolean(member.questionToken),
    definite_assignment: Boolean(member.exclamationToken),
    type: member.type ? normalizeText(member.type, sourceFile) : '<inferred>',
    initializer: member.initializer ? normalizeText(member.initializer, sourceFile).slice(0, 240) : null,
    decorators: decoratorNames(ts, member, sourceFile),
  }));
  const serializedProperties = properties.filter((property) => property.decorators.includes('property'));
  const report = {
    schema_version: 1,
    generator: 'tools/codex/analyze-game-root.js',
    parser: { name: 'typescript', version: ts.version, runtime: typescriptPath.replace(/\\/g, '/') },
    source: {
      path: path.relative(root, sourcePath).replace(/\\/g, '/'),
      bytes: Buffer.byteLength(sourceText),
      lines: sourceText.length === 0 ? 0 : sourceText.replace(/\r?\n$/, '').split(/\r?\n/).length,
      sha256: crypto.createHash('sha256').update(sourceText).digest('hex').toUpperCase(),
      parse_diagnostics: parseDiagnostics,
    },
    imports,
    class: {
      name: classNode.name.text,
      extends: (classNode.heritageClauses || []).map((clause) => normalizeText(clause, sourceFile)),
      start_line: lineOf(classNode, sourceFile),
      end_line: endLineOf(classNode, sourceFile),
      property_count: properties.length,
      method_count: methods.length,
      constructor_count: methods.filter((member) => member.kind === 'constructor').length,
      accessor_count: methods.filter((member) => member.kind === 'getter' || member.kind === 'setter').length,
      serialized_property_count: serializedProperties.length,
      properties,
      methods,
    },
    call_edges: callEdges,
    listeners,
    timers,
    storage,
    resource_loads: resourceLoads,
    scene_bindings: {
      serialized_properties: serializedProperties,
      dynamic_nodes: sceneNodes,
      operations: sceneOperations,
    },
    field_write_owners: Object.fromEntries(
      [...fieldWriteOwners.entries()]
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([field, owners]) => [field, uniqueSorted(owners)]),
    ),
  };

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({
    status: parseDiagnostics.length === 0 ? 'PASS' : 'FAIL',
    source: report.source,
    class: {
      properties: properties.length,
      methods: methods.length,
      constructors: report.class.constructor_count,
      accessors: report.class.accessor_count,
      serialized_properties: serializedProperties.length,
    },
    call_edges: callEdges.length,
    listeners: listeners.length,
    timers: timers.length,
    storage_operations: storage.length,
    resource_loads: resourceLoads.length,
    dynamic_nodes: sceneNodes.length,
    output: path.relative(root, outputPath).replace(/\\/g, '/'),
  }, null, 2)}\n`);
  if (parseDiagnostics.length > 0) process.exitCode = 1;
}

main();
