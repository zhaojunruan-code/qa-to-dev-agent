#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import readline from "node:readline";
import { fileURLToPath } from "node:url";

const VERSION = readPackageVersion();

const IGNORED_DIRS = new Set([
  ".ace-tool",
  ".git",
  ".idea",
  ".venv",
  ".vscode",
  "__pycache__",
  "dependencies",
  "dependency",
  "dist",
  "generated",
  "lib",
  "node_modules",
  "vendor",
]);

const SAFE_TEXT_SUFFIXES = new Set([
  ".css",
  ".html",
  ".js",
  ".json",
  ".jsx",
  ".md",
  ".php",
  ".py",
  ".toml",
  ".ts",
  ".tsx",
  ".vue",
  ".yaml",
  ".yml",
]);

const SIGNAL_FILES = new Map([
  ["package.json", "Node.js or frontend project"],
  ["pnpm-lock.yaml", "pnpm package manager"],
  ["package-lock.json", "npm package manager"],
  ["yarn.lock", "Yarn package manager"],
  ["pyproject.toml", "Python project"],
  ["requirements.txt", "Python dependencies"],
  ["composer.json", "PHP project"],
  ["think", "ThinkPHP or FastAdmin command entry"],
  ["vite.config.ts", "Vite frontend"],
  ["vite.config.js", "Vite frontend"],
  ["src/main.ts", "frontend entry candidate"],
  ["src/main.js", "frontend entry candidate"],
  ["app/admin/controller", "FastAdmin admin controllers"],
  ["application/admin/controller", "ThinkPHP admin controllers"],
]);

const ENTRY_CANDIDATES = [
  "main.py",
  "app.py",
  "server.py",
  "src/main.ts",
  "src/main.js",
  "src/App.tsx",
  "src/App.jsx",
  "pages.json",
  "manifest.json",
  "application/admin/controller",
  "app/admin/controller",
];

async function main(argv) {
  try {
    if (argv.length === 0 || argv[0] === "--help" || argv[0] === "-h") {
      printHelp();
      return 0;
    }
    if (argv[0] === "--version" || argv[0] === "-v") {
      console.log(VERSION);
      return 0;
    }

    const command = argv[0];
    if (argv.length === 2 && (argv[1] === "--help" || argv[1] === "-h")) {
      printHelp();
      return 0;
    }
    if (command === "run") {
      return runCommand(parseRunArgs(argv.slice(1)));
    }
    if (command === "interactive") {
      return interactiveCommand(parseInteractiveArgs(argv.slice(1)));
    }

    throw new UsageError(`Unknown command: ${command}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`qadev error: ${message}`);
    console.error(`next step: ${nextStepFor(error)}`);
    return error instanceof UsageError ? 2 : 1;
  }
}

function printHelp() {
  console.log(`QA-to-Dev Client Runtime

Usage:
  qadev --help
  qadev --version
  qadev run --project <path> --input <text> --local-only --print-prompt
  qadev interactive

Commands:
  run          Read-only project scan and local task prompt preview.
  interactive Start a local terminal session for project/input/status state.

Run options:
  --project <path>   Target project to scan in read-only mode.
  --input <text>     QA note or acceptance input.
  --local-only       Required for this MVP. No LLM request is made.
  --print-prompt     Print the structured prompt preview.
  --max-files <n>    Maximum files to list from the target project. Default: 80.

Safety:
  The Node client ignores .env*, lib, generated, dependency/dependencies,
  node_modules, vendor, and .git. It does not write to or run commands in
  the target project.`);
}

function parseRunArgs(argv) {
  const options = {
    project: undefined,
    input: undefined,
    localOnly: false,
    printPrompt: false,
    maxFiles: 80,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--project") {
      options.project = readValue(argv, ++index, "--project");
    } else if (arg === "--input") {
      options.input = readValue(argv, ++index, "--input");
    } else if (arg === "--local-only") {
      options.localOnly = true;
    } else if (arg === "--print-prompt") {
      options.printPrompt = true;
    } else if (arg === "--max-files") {
      const raw = readValue(argv, ++index, "--max-files");
      const parsed = Number.parseInt(raw, 10);
      if (!Number.isFinite(parsed) || parsed < 1) {
        throw new UsageError("--max-files must be a positive integer");
      }
      options.maxFiles = parsed;
    } else {
      throw new UsageError(`Unknown run option: ${arg}`);
    }
  }
  return options;
}

function parseInteractiveArgs(argv) {
  if (argv.length === 0) {
    return {};
  }
  throw new UsageError(`Unknown interactive option: ${argv[0]}`);
}

function runCommand(options) {
  if (!options.project) {
    throw new UsageError("run requires --project <path>");
  }
  if (!options.input || !options.input.trim()) {
    throw new UsageError("run requires non-empty --input <text>");
  }
  if (!options.localOnly) {
    throw new UsageError("LLM requests are not implemented in the client-first MVP; use --local-only.");
  }
  if (!options.printPrompt) {
    throw new UsageError("This MVP only supports prompt preview output; add --print-prompt.");
  }

  const context = scanProject(options.project, options.input, options.maxFiles);
  console.log(renderPrompt(options.input, context));
  return 0;
}

async function interactiveCommand() {
  const state = {
    project: undefined,
    input: "",
    scan: undefined,
    generated: false,
  };

  console.log("QA-to-Dev Client Runtime Interactive");
  console.log("");
  console.log("Mode: local read-only MVP. LLM requests, file writes, and target commands are disabled.");
  console.log("Type /status, /project <path>, /input <text>, /scan, /help, or /exit.");

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: process.stdin.isTTY,
    prompt: "qadev> ",
  });

  rl.prompt();
  for await (const rawLine of rl) {
    const line = rawLine.trim();
    try {
      if (!line) {
        rl.prompt();
        continue;
      }
      if (line === "/exit" || line === "exit" || line === "/quit" || line === "quit") {
        console.log("bye");
        rl.close();
        return 0;
      }
      handleInteractiveLine(state, line);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`qadev error: ${message}`);
    }
    rl.prompt();
  }
  console.log("bye");
  return 0;
}

function handleInteractiveLine(state, line) {
  if (line === "/help" || line === "help") {
    console.log("Commands: /status, /project <path>, /input <text>, /scan, /preview, /exit");
    return;
  }
  if (line === "/status" || line === "status") {
    printStatus(state);
    return;
  }
  if (line.startsWith("/project ")) {
    state.project = path.resolve(line.slice("/project ".length).trim());
    markStale(state);
    console.log(`Project set: ${state.project}`);
    return;
  }
  if (line.startsWith("/input ")) {
    appendInput(state, line.slice("/input ".length));
    return;
  }
  if (line === "/scan") {
    if (!state.project) {
      throw new UsageError("Set a project first with /project <path>");
    }
    if (!state.input.trim()) {
      throw new UsageError("Add QA input first with /input <text> or by pasting text.");
    }
    state.scan = scanProject(state.project, state.input, 80);
    state.generated = false;
    console.log(`Scanned ${state.scan.fileCount} files from ${state.scan.root}`);
    return;
  }
  if (line === "/preview") {
    if (!state.scan) {
      throw new UsageError("Run /scan first.");
    }
    console.log(renderPrompt(state.input, state.scan));
    state.generated = true;
    return;
  }
  if (line.startsWith("/")) {
    throw new UsageError(`Unknown command: ${line}`);
  }
  appendInput(state, line);
}

function appendInput(state, value) {
  const cleaned = value.trim();
  if (!cleaned) {
    return;
  }
  state.input = `${state.input.trim()}\n${cleaned}`.trim();
  markStale(state);
  console.log(`QA input: ${state.input.length} chars`);
}

function markStale(state) {
  state.scan = undefined;
  state.generated = false;
}

function printStatus(state) {
  console.log("Session");
  console.log(`- Project: ${state.project ?? "not selected"}`);
  console.log(`- QA input: ${state.input.length} chars`);
  console.log(`- Scan: ${state.scan ? "ready" : "not run"}`);
  console.log(`- Generated preview: ${state.generated ? "yes" : "no"}`);
  console.log("- LLM: disabled in this MVP");
}

function scanProject(projectRoot, qaInput, maxFiles) {
  const root = path.resolve(projectRoot);
  let stat;
  try {
    stat = fs.statSync(root);
  } catch {
    throw new Error(`Project path does not exist: ${root}`);
  }
  if (!stat.isDirectory()) {
    throw new Error(`Project path is not a directory: ${root}`);
  }

  const files = [];
  walk(root, root, files, maxFiles);
  const fileSet = new Set(files.map(toPosix));
  const signals = detectSignals(root, fileSet);
  const metadata = detectMetadata(root);
  const entryFiles = ENTRY_CANDIDATES.filter((candidate) => fileSet.has(candidate) || fs.existsSync(path.join(root, candidate)));
  const keyCodeLocations = findRelatedFiles(files, qaInput);

  return {
    root,
    fileCount: files.length,
    signals,
    sampleTree: files.slice(0, maxFiles).map(toPosix),
    techStack: metadata.techStack,
    buildScripts: metadata.buildScripts,
    testScripts: metadata.testScripts,
    entryFiles,
    keyCodeLocations,
  };
}

function walk(root, current, files, maxFiles) {
  if (files.length >= maxFiles) {
    return;
  }
  let entries;
  try {
    entries = fs.readdirSync(current, { withFileTypes: true });
  } catch {
    return;
  }
  entries.sort((left, right) => left.name.localeCompare(right.name));

  for (const entry of entries) {
    if (files.length >= maxFiles) {
      return;
    }
    if (entry.isDirectory()) {
      if (!IGNORED_DIRS.has(entry.name)) {
        walk(root, path.join(current, entry.name), files, maxFiles);
      }
      continue;
    }
    if (!entry.isFile() || isSensitiveFileName(entry.name)) {
      continue;
    }
    const absolute = path.join(current, entry.name);
    const relative = path.relative(root, absolute);
    if (relative.split(path.sep).some((part) => IGNORED_DIRS.has(part))) {
      continue;
    }
    files.push(relative);
  }
}

function detectSignals(root, fileSet) {
  const signals = [];
  for (const [candidate, description] of SIGNAL_FILES) {
    if (fileSet.has(candidate) || fs.existsSync(path.join(root, candidate))) {
      signals.push(`\`${candidate}\`: ${description}`);
    }
  }
  return signals;
}

function detectMetadata(root) {
  const techStack = [];
  const buildScripts = [];
  const testScripts = [];
  const packageJson = path.join(root, "package.json");
  if (fs.existsSync(packageJson)) {
    techStack.push("Node.js");
    try {
      const data = JSON.parse(fs.readFileSync(packageJson, "utf8"));
      for (const [name, command] of Object.entries(data.scripts ?? {})) {
        const item = `\`npm run ${name}\`: \`${command}\``;
        if (name.includes("build")) {
          buildScripts.push(item);
        }
        if (name.includes("test") || name === "lint" || name === "check") {
          testScripts.push(item);
        }
      }
    } catch {
      techStack.push("Node.js metadata unreadable");
    }
  }
  if (fs.existsSync(path.join(root, "pyproject.toml"))) {
    techStack.push("Python");
  }
  if (fs.existsSync(path.join(root, "requirements.txt"))) {
    techStack.push("Python requirements.txt");
  }
  if (fs.existsSync(path.join(root, "composer.json"))) {
    techStack.push("PHP Composer");
  }
  if (fs.existsSync(path.join(root, "think"))) {
    techStack.push("ThinkPHP/FastAdmin candidate");
  }
  if (fs.existsSync(path.join(root, "pnpm-lock.yaml"))) {
    techStack.push("pnpm");
  }
  return { techStack, buildScripts, testScripts };
}

function findRelatedFiles(files, qaInput, limit = 8) {
  const terms = tokenize(qaInput);
  if (terms.length === 0) {
    return [];
  }
  return files
    .filter((file) => isSafeTextPath(file))
    .map((file) => {
      const haystack = toPosix(file).toLowerCase();
      const score = terms.filter((term) => haystack.includes(term)).length;
      return { file: toPosix(file), score };
    })
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score || left.file.localeCompare(right.file))
    .slice(0, limit)
    .map((item) => item.file);
}

function renderPrompt(qaInput, context) {
  return `# QA-to-Dev Client Runtime Prompt Preview

## Runtime Status
- CLI entry: \`qadev\`
- Mode: local-only
- LLM request: disabled in this MVP
- Target commands: not executed
- Target writes: not performed

## QA Input
${qaInput.trim()}

## Current Project Context
${contextToMarkdown(context)}

## Safety Boundary
- Read-only scan only.
- Ignored paths: .env*, lib, generated, dependency, dependencies, node_modules, vendor, .git.
- No shell, git, build, test, install, Issue creation, or LLM request is run by this command.

## Developer Task Prompt
Use the QA input and scanned context above to produce a developer-ready task. Before coding, identify the real target runtime, entry point, call chain, affected files, acceptance criteria, risk points, and open questions. Do not invent API fields, routes, files, or business rules.`;
}

function contextToMarkdown(context) {
  const lines = [
    `- Project root: \`${context.root}\``,
    `- Scanned files: ${context.fileCount}`,
  ];
  pushList(lines, "Detected signals", context.signals);
  pushList(lines, "Sample tree", context.sampleTree.map((item) => `\`${item}\``));
  pushList(lines, "Technology stack", context.techStack);
  pushList(lines, "Entry files", context.entryFiles.map((item) => `\`${item}\``));
  pushList(lines, "Build scripts", context.buildScripts);
  pushList(lines, "Test scripts", context.testScripts);
  pushList(lines, "Requirement-related code candidates", context.keyCodeLocations.map((item) => `\`${item}\``));
  return lines.join("\n");
}

function pushList(lines, title, values) {
  if (!values.length) {
    lines.push(`- ${title}: none from the lightweight scanner`);
    return;
  }
  lines.push(`- ${title}:`);
  for (const value of values) {
    lines.push(`  - ${value}`);
  }
}

function readValue(argv, index, flag) {
  const value = argv[index];
  if (!value || value.startsWith("--")) {
    throw new UsageError(`${flag} requires a value`);
  }
  return value;
}

function isSensitiveFileName(name) {
  return name.toLowerCase().startsWith(".env");
}

function isSafeTextPath(value) {
  return !isSensitiveFileName(path.basename(value)) && SAFE_TEXT_SUFFIXES.has(path.extname(value).toLowerCase());
}

function tokenize(text) {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .split(/\s+/)
    .filter((part) => part.length >= 2)
    .slice(0, 20);
}

function toPosix(value) {
  return value.split(path.sep).join("/");
}

function readPackageVersion() {
  try {
    const currentFile = fileURLToPath(import.meta.url);
    const packagePath = path.resolve(path.dirname(currentFile), "..", "package.json");
    const data = JSON.parse(fs.readFileSync(packagePath, "utf8"));
    return data.version ?? "0.0.0";
  } catch {
    return "0.0.0";
  }
}

function nextStepFor(error) {
  if (error instanceof UsageError) {
    return "run `node bin/qadev.mjs --help` and retry with the documented arguments.";
  }
  return "check the project path and retry in local-only prompt-preview mode.";
}

class UsageError extends Error {}

const exitCode = await main(process.argv.slice(2));
process.exitCode = exitCode;
