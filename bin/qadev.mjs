#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import readline from "node:readline";
import { fileURLToPath } from "node:url";

const VERSION = readPackageVersion();

const IGNORED_DIRS = new Set([
  ".ace-tool",
  ".cache",
  ".git",
  ".idea",
  ".next",
  ".nuxt",
  ".output",
  ".parcel-cache",
  ".pnpm-store",
  ".turbo",
  ".venv",
  ".vite",
  ".vscode",
  ".yarn",
  "__pycache__",
  "build",
  "cache",
  "coverage",
  "dependencies",
  "dependency",
  "dist",
  "generated",
  "lib",
  "lock",
  "node_modules",
  "out",
  "unpackage",
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

const PRIORITY_PATHS = [
  "pages.json",
  "src/pages",
  "src/components",
  "src/api",
  "src/store",
  "src/router",
  "src/utils",
];

const TERM_EXPANSIONS = new Map([
  ["订单", ["order", "orders", "orderlist", "order-list"]],
  ["order", ["orders", "订单"]],
  ["orders", ["order", "订单"]],
  ["我的", ["mine", "my", "user", "profile", "account", "member", "me"]],
  ["mine", ["my", "user", "profile", "我的"]],
  ["user", ["mine", "profile", "account", "我的"]],
  ["profile", ["mine", "user", "account", "我的"]],
  ["状态", ["status", "state", "tab", "tabs", "switch", "filter"]],
  ["status", ["state", "状态", "tab", "tabs", "switch", "filter"]],
  ["tab", ["tabs", "status", "状态", "switch", "filter"]],
  ["tabs", ["tab", "status", "状态", "switch", "filter"]],
  ["switch", ["status", "状态", "tab", "tabs", "filter"]],
  ["filter", ["status", "状态", "tab", "tabs", "switch"]],
]);

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
      return await runCommand(parseRunArgs(argv.slice(1)));
    }
    if (command === "interactive") {
      return await interactiveCommand(parseInteractiveArgs(argv.slice(1)));
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
  qadev run --project <path> --input <text> --print-prompt --base-url <url> --api-key <key> --model <name>
  qadev interactive --base-url <url> --api-key <key> --model <name>

Commands:
  run          Preflight the LLM connection, then scan and print a local task prompt preview.
  interactive Preflight the LLM connection, then start a terminal project/input/status session.

Run options:
  --project <path>   Target project to scan in read-only mode.
  --input <text>     QA note or acceptance input.
  --local-only       Do not send QA input or project context to the model after preflight.
  --print-prompt     Print the structured prompt preview.
  --max-files <n>    Maximum files to list from the target project. Default: 80.
  --base-url <url>   OpenAI-compatible API base URL. Env: QADEV_LLM_BASE_URL.
  --api-key <key>    API key for the provider. Env: QADEV_LLM_API_KEY.
  --model <name>     Model name to use. Env: QADEV_LLM_MODEL.
  --http-referer <url> Optional HTTP-Referer header. Env: QADEV_LLM_HTTP_REFERER.
  --app-title <name> Optional X-Title header. Env: QADEV_LLM_APP_TITLE.

LLM preflight:
  The run and interactive commands must complete a tiny <base-url>/chat/completions
  health check before scanning or accepting project input. This request sends
  only a fixed health-check message, never QA notes or project code context.
  API keys are never printed or stored by this client.

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
    llm: {
      baseURL: undefined,
      apiKey: undefined,
      model: undefined,
      httpReferer: undefined,
      appTitle: undefined,
    },
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
    } else if (arg === "--base-url") {
      options.llm.baseURL = readValue(argv, ++index, "--base-url");
    } else if (arg === "--api-key") {
      options.llm.apiKey = readValue(argv, ++index, "--api-key");
    } else if (arg === "--model") {
      options.llm.model = readValue(argv, ++index, "--model");
    } else if (arg === "--http-referer") {
      options.llm.httpReferer = readValue(argv, ++index, "--http-referer");
    } else if (arg === "--app-title") {
      options.llm.appTitle = readValue(argv, ++index, "--app-title");
    } else {
      throw new UsageError(`Unknown run option: ${arg}`);
    }
  }
  return options;
}

function parseInteractiveArgs(argv) {
  const options = {
    llm: {
      baseURL: undefined,
      apiKey: undefined,
      model: undefined,
      httpReferer: undefined,
      appTitle: undefined,
    },
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--base-url") {
      options.llm.baseURL = readValue(argv, ++index, "--base-url");
    } else if (arg === "--api-key") {
      options.llm.apiKey = readValue(argv, ++index, "--api-key");
    } else if (arg === "--model") {
      options.llm.model = readValue(argv, ++index, "--model");
    } else if (arg === "--http-referer") {
      options.llm.httpReferer = readValue(argv, ++index, "--http-referer");
    } else if (arg === "--app-title") {
      options.llm.appTitle = readValue(argv, ++index, "--app-title");
    } else {
      throw new UsageError(`Unknown interactive option: ${arg}`);
    }
  }
  return options;
}

async function runCommand(options) {
  if (!options.project) {
    throw new UsageError("run requires --project <path>");
  }
  if (!options.input || !options.input.trim()) {
    throw new UsageError("run requires non-empty --input <text>");
  }
  if (!options.printPrompt) {
    throw new UsageError("This MVP only supports prompt preview output; add --print-prompt.");
  }

  const llm = await preflightLlmConnection(options.llm);
  console.error(`qadev: LLM connection ready (${llm.provider}, model: ${llm.model})`);
  const context = scanProject(options.project, options.input, options.maxFiles);
  console.log(renderPrompt(options.input, context, llm));
  return 0;
}

async function interactiveCommand(options) {
  const llm = await preflightLlmConnection(options.llm);
  const state = {
    project: undefined,
    input: "",
    scan: undefined,
    generated: false,
    llm,
    llmOptions: options.llm,
  };

  console.log("QA-to-Dev Client Runtime Interactive");
  console.log("");
  console.log(`LLM connection ready: ${llm.provider}, model: ${llm.model}`);
  console.log("Mode: read-only session. /preview is local only; /generate sends QA input and scan context to the configured LLM.");
  console.log("Type /status, /project <path>, /input <text>, /scan, /preview, /generate, /help, or /exit.");

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
      await handleInteractiveLine(state, line);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`qadev error: ${message}`);
    }
    rl.prompt();
  }
  console.log("bye");
  return 0;
}

async function handleInteractiveLine(state, line) {
  if (line === "/help" || line === "help") {
    console.log("Commands: /status, /project <path>, /input <text>, /scan, /preview, /generate, /exit");
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
    console.log(renderPrompt(state.input, state.scan, state.llm));
    state.generated = true;
    return;
  }
  if (line === "/generate") {
    if (!state.scan) {
      throw new UsageError("Run /scan first.");
    }
    console.log("Sending QA input and scanned context to the configured LLM...");
    const task = await generateTask(state.input, state.scan, state.llmOptions);
    console.log(task);
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
  console.log(`- LLM: connected (${state.llm.provider}, model: ${state.llm.model})`);
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
  const collectionLimit = Math.max(maxFiles * 20, 500);
  walk(root, root, files, collectionLimit);
  const prioritizedFiles = prioritizeFiles(files);
  const fileSet = new Set(files.map(toPosix));
  const signals = detectSignals(root, fileSet);
  const metadata = detectMetadata(root);
  const entryFiles = ENTRY_CANDIDATES.filter((candidate) => fileSet.has(candidate) || fs.existsSync(path.join(root, candidate)));
  const keyCodeLocations = findRelatedFiles(prioritizedFiles, qaInput);

  return {
    root,
    fileCount: files.length,
    signals,
    sampleTree: prioritizedFiles.slice(0, maxFiles).map(toPosix),
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
    return files
      .filter((file) => isSafeTextPath(file) && priorityRank(toPosix(file)) < PRIORITY_PATHS.length)
      .slice(0, limit)
      .map(toPosix);
  }
  return files
    .filter((file) => isSafeTextPath(file))
    .map((file) => {
      const haystack = toPosix(file).toLowerCase();
      const matchedTerms = terms.filter((term) => haystack.includes(term)).length;
      if (matchedTerms === 0) {
        return { file: toPosix(file), score: 0 };
      }
      const priorityBoost = Math.max(0, PRIORITY_PATHS.length - priorityRank(haystack));
      const score = matchedTerms * 10 + priorityBoost;
      return { file: toPosix(file), score };
    })
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score || left.file.localeCompare(right.file))
    .slice(0, limit)
    .map((item) => item.file);
}

function prioritizeFiles(files) {
  return [...files].sort((left, right) => {
    const leftPath = toPosix(left).toLowerCase();
    const rightPath = toPosix(right).toLowerCase();
    const leftRank = priorityRank(leftPath);
    const rightRank = priorityRank(rightPath);
    return leftRank - rightRank || leftPath.localeCompare(rightPath);
  });
}

function priorityRank(posixPath) {
  const normalized = posixPath.toLowerCase();
  const rank = PRIORITY_PATHS.findIndex((candidate) => normalized === candidate || normalized.startsWith(`${candidate}/`));
  return rank === -1 ? PRIORITY_PATHS.length : rank;
}

function renderPrompt(qaInput, context, llm) {
  return `# QA-to-Dev Client Runtime Prompt Preview

## Runtime Status
- CLI entry: \`qadev\`
- Mode: read-only prompt preview
- LLM preflight: completed via \`${llm.preflightEndpoint}\`
- LLM model: \`${llm.model}\`
- LLM generation request: not sent by this preview command
- Target commands: not executed
- Target writes: not performed

## QA Input
${qaInput.trim()}

## Current Project Context
${contextToMarkdown(context)}

## 需要优先调查的代码位置
${priorityInvestigationMarkdown(context)}

## 开发任务骨架
- 背景: summarize the QA report and the user-visible behavior gap.
- 目标: define the smallest runtime-specific change that satisfies the QA input.
- 入口与调用链: confirm the active platform, route, page/component, store/API wrapper, and event path before editing.
- 实现要求: list concrete code changes after inspecting the files above.
- 保留逻辑: call out existing API contracts, fields, filters, tabs, status mappings, and navigation that must not be renamed or silently changed.
- 验收标准: describe observable UI/API behavior plus regression scope.
- 风险与待确认: record missing backend interfaces, unclear runtime branches, or manual device/browser checks.

## Safety Boundary
- Read-only scan only.
- Ignored paths: .env*, lib, generated, dependency, dependencies, node_modules, vendor, .git, .pnpm-store, unpackage, and package cache/build output directories.
- No shell, git, build, test, install, Issue creation, or LLM generation request is run by this command.
- The LLM preflight sends only a fixed health-check message and does not send QA input or project code context.

## Developer Task Prompt
Use the QA input and scanned context above to produce a developer-ready task. Before coding, identify the real target runtime, entry point, call chain, affected files, acceptance criteria, risk points, and open questions. Do not invent API fields, routes, files, or business rules.`;
}

async function generateTask(qaInput, context, rawOptions) {
  const config = resolveLlmConfig(rawOptions);
  const endpoint = buildChatCompletionsEndpoint(config.baseURL);
  const headers = buildLlmHeaders(config);
  const messages = buildGenerationMessages(qaInput, context);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  let response;

  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model: config.model,
        messages,
        temperature: 0.2,
        max_tokens: 1800,
      }),
      signal: controller.signal,
    });
  } catch (error) {
    throw new Error(`LLM generation failed: ${safeFetchMessage(error)}`);
  } finally {
    clearTimeout(timeout);
  }

  if (!response.ok) {
    const detail = await readErrorResponse(response, config.apiKey);
    throw new Error(`LLM generation failed: chat completions endpoint returned HTTP ${response.status}${detail ? `: ${detail}` : ""}`);
  }

  const body = await readJsonResponse(response);
  const firstChoice = body?.choices?.[0];
  const content = firstChoice?.message?.content ?? firstChoice?.text;
  if (typeof content !== "string" || !content.trim()) {
    throw new Error("LLM generation failed: chat completions endpoint did not return task content");
  }
  return content.trim();
}

function buildGenerationMessages(qaInput, context) {
  return [
    {
      role: "system",
      content: [
        "You generate developer-ready implementation task briefs from QA input and read-only scan context.",
        "Return Markdown only. Do not ask to modify files yourself.",
        "Do not invent API fields, routes, files, or business rules.",
        "Preserve request/response field names exactly unless the scan context proves otherwise.",
      ].join(" "),
    },
    {
      role: "user",
      content: [
        "# QA Input",
        qaInput.trim(),
        "",
        "# Read-only Scan Context",
        contextToMarkdown(context),
        "",
        "# Required Markdown Structure",
        "## 背景",
        "## 开发目标",
        "## 需要优先调查的代码位置",
        "## 实现要求",
        "## 需要保留的现有逻辑",
        "## 错误处理要求",
        "## 验收标准",
        "## 回归范围",
        "## 风险点",
        "## 待确认问题",
      ].join("\n"),
    },
  ];
}

async function preflightLlmConnection(rawOptions) {
  const config = resolveLlmConfig(rawOptions);
  const endpoint = buildChatCompletionsEndpoint(config.baseURL);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  let response;

  try {
    const headers = buildLlmHeaders(config);

    response = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model: config.model,
        messages: [
          { role: "system", content: "You are a connection health check. Reply with OK only." },
          { role: "user", content: "Reply with OK." },
        ],
        max_tokens: 2,
      }),
      signal: controller.signal,
    });
  } catch (error) {
    throw new Error(`LLM connection failed: ${safeFetchMessage(error)}`);
  } finally {
    clearTimeout(timeout);
  }

  if (!response.ok) {
    const detail = await readErrorResponse(response, config.apiKey);
    throw new Error(`LLM connection failed: chat completions endpoint returned HTTP ${response.status}${detail ? `: ${detail}` : ""}`);
  }

  const body = await readJsonResponse(response);
  const firstChoice = body?.choices?.[0];
  const content = firstChoice?.message?.content ?? firstChoice?.text;
  if (typeof content !== "string") {
    throw new Error("LLM connection failed: chat completions endpoint did not return a compatible response");
  }

  return {
    provider: endpoint.origin,
    model: config.model,
    preflightEndpoint: endpoint.toString(),
  };
}

function buildLlmHeaders(config) {
  const headers = {
    Authorization: `Bearer ${config.apiKey}`,
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  if (config.httpReferer) {
    headers["HTTP-Referer"] = config.httpReferer;
  }
  if (config.appTitle) {
    headers["X-Title"] = config.appTitle;
  }
  return headers;
}

function resolveLlmConfig(rawOptions = {}) {
  const baseURL = firstNonEmpty(rawOptions.baseURL, process.env.QADEV_LLM_BASE_URL);
  const apiKey = firstNonEmpty(rawOptions.apiKey, process.env.QADEV_LLM_API_KEY);
  const model = firstNonEmpty(rawOptions.model, process.env.QADEV_LLM_MODEL);
  const httpReferer = firstNonEmpty(rawOptions.httpReferer, process.env.QADEV_LLM_HTTP_REFERER);
  const appTitle = firstNonEmpty(rawOptions.appTitle, process.env.QADEV_LLM_APP_TITLE);
  const missing = [];
  if (!baseURL) {
    missing.push("base URL (--base-url or QADEV_LLM_BASE_URL)");
  }
  if (!apiKey) {
    missing.push("API key (--api-key or QADEV_LLM_API_KEY)");
  }
  if (!model) {
    missing.push("model (--model or QADEV_LLM_MODEL)");
  }
  if (missing.length > 0) {
    throw new UsageError(`Missing LLM configuration: ${missing.join(", ")}`);
  }
  return { baseURL, apiKey, model, httpReferer, appTitle };
}

function buildChatCompletionsEndpoint(baseURL) {
  let parsed;
  try {
    parsed = new URL(baseURL);
  } catch {
    throw new UsageError("LLM base URL must be an absolute http(s) URL");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new UsageError("LLM base URL must use http or https");
  }
  if (parsed.username || parsed.password) {
    throw new UsageError("LLM base URL must not include username or password");
  }
  const pathname = parsed.pathname.replace(/\/+$/, "");
  parsed.pathname = `${pathname}/chat/completions`;
  parsed.search = "";
  parsed.hash = "";
  return parsed;
}

async function readJsonResponse(response) {
  const text = await response.text();
  if (!text.trim()) {
    return {};
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("LLM connection failed: chat completions endpoint did not return valid JSON");
  }
}

async function readErrorResponse(response, apiKey) {
  let text;
  try {
    text = await response.text();
  } catch {
    return "";
  }
  const safeText = sanitizeProviderText(text, apiKey);
  if (!safeText) {
    return "";
  }

  try {
    const body = JSON.parse(safeText);
    const details = [
      body?.error?.message,
      body?.error?.type,
      body?.error?.code,
      body?.message,
      body?.detail,
      body?.title,
    ].filter((value) => typeof value === "string" && value.trim());
    if (details.length > 0) {
      return truncateProviderDetail([...new Set(details)].join(" | "));
    }
  } catch {
    // Fall through to the raw provider text below.
  }
  return truncateProviderDetail(safeText);
}

function safeFetchMessage(error) {
  if (error?.name === "AbortError") {
    return "chat completions endpoint timed out";
  }
  return error instanceof Error && error.message ? sanitizeProviderText(error.message) : "chat completions endpoint request failed";
}

function sanitizeProviderText(value, apiKey) {
  if (typeof value !== "string") {
    return "";
  }
  let sanitized = value.replace(/Bearer\s+\S+/gi, "Bearer [redacted]");
  if (apiKey) {
    sanitized = sanitized.split(apiKey).join("[redacted]");
  }
  return sanitized.replace(/\s+/g, " ").trim();
}

function truncateProviderDetail(value) {
  return value.length > 500 ? `${value.slice(0, 500)}...` : value;
}

function firstNonEmpty(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return undefined;
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

function priorityInvestigationMarkdown(context) {
  const locations = [
    ...context.entryFiles,
    ...context.keyCodeLocations,
    ...context.sampleTree.filter((item) => priorityRank(item) < PRIORITY_PATHS.length),
  ];
  const unique = [...new Set(locations)].slice(0, 12);
  if (unique.length === 0) {
    return "- No priority path matched in the lightweight scan. Confirm the runtime entry point before editing.";
  }
  return unique.map((item) => `- \`${item}\``).join("\n");
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
  const normalized = text.toLowerCase();
  const tokens = normalized
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .split(/\s+/)
    .filter((part) => part.length >= 2)
    .slice(0, 20);
  const expanded = new Set(tokens);
  for (const [trigger, additions] of TERM_EXPANSIONS) {
    if (normalized.includes(trigger) || tokens.includes(trigger)) {
      expanded.add(trigger);
      for (const addition of additions) {
        expanded.add(addition);
      }
    }
  }
  return [...expanded].slice(0, 60);
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
  return "check the LLM base URL, API key, model, and project path; then retry.";
}

class UsageError extends Error {}

const exitCode = await main(process.argv.slice(2));
process.exitCode = exitCode;
