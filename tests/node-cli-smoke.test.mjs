import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const cliPath = path.join(repoRoot, "bin", "qadev.mjs");

test("qadev help starts from the Node client entry", async () => {
  const result = await runNode(["--help"]);

  assert.equal(result.status, 0);
  assert.match(result.stdout, /QA-to-Dev Client Runtime/);
  assert.match(result.stdout, /qadev run --project <path>/);
});

test("qadev version comes from package metadata", async () => {
  const result = await runNode(["--version"]);

  assert.equal(result.status, 0);
  assert.equal(result.stdout.trim(), "0.1.0");
});

test("qadev run preflights LLM, prints a local prompt, and ignores protected paths", async () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  fs.writeFileSync(path.join(fixture, "package.json"), JSON.stringify({ scripts: { test: "node --test", build: "vite build" } }), "utf8");
  fs.writeFileSync(path.join(fixture, "login.js"), "export const label = 'Login';\n", "utf8");
  fs.writeFileSync(path.join(fixture, ".env.local"), "SECRET=do-not-read\n", "utf8");
  fs.mkdirSync(path.join(fixture, "lib"));
  fs.writeFileSync(path.join(fixture, "lib", "generated.js"), "generated\n", "utf8");
  fs.mkdirSync(path.join(fixture, "node_modules"));
  fs.writeFileSync(path.join(fixture, "node_modules", "hidden.js"), "hidden\n", "utf8");

  await withMockChatServer(async ({ baseURL, requests }) => {
    const result = await runNode([
      "run",
      "--project",
      fixture,
      "--input",
      "login button copy needs updating",
      "--local-only",
      "--print-prompt",
    ], {
      env: llmEnv(baseURL, "mock-secret-key", "openrouter/mock-model"),
    });

    assert.equal(result.status, 0);
    assert.equal(requests.length, 1);
    assert.equal(requests[0].method, "POST");
    assert.equal(requests[0].url, "/api/v1/chat/completions");
    assert.equal(requests[0].authorization, "Bearer mock-secret-key");
    assert.equal(requests[0].body.model, "openrouter/mock-model");
    assert.doesNotMatch(JSON.stringify(requests[0].body), /login button copy/);
    assert.doesNotMatch(JSON.stringify(requests[0].body), new RegExp(escapeRegExp(fixture)));
    assert.doesNotMatch(JSON.stringify(requests[0].body), /login\.js/);
    assert.doesNotMatch(JSON.stringify(requests[0].body), /Login/);
    assert.match(result.stderr, /LLM connection ready/);
    assert.match(result.stdout, /LLM preflight: completed/);
    assert.match(result.stdout, /LLM generation request: not sent/);
    assert.match(result.stdout, /login button copy needs updating/);
    assert.match(result.stdout, /login\.js/);
    assert.doesNotMatch(result.stdout, /SECRET/);
    assert.doesNotMatch(result.stdout, /mock-secret-key/);
    assert.doesNotMatch(result.stderr, /mock-secret-key/);
    assert.doesNotMatch(result.stdout, /generated\.js/);
    assert.doesNotMatch(result.stdout, /hidden\.js/);
  });
});

test("qadev run accepts CLI LLM options before scanning", async () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  fs.writeFileSync(path.join(fixture, "todo.js"), "export const todo = true;\n", "utf8");

  await withMockChatServer(async ({ baseURL, requests }) => {
    const result = await runNode([
      "run",
      "--project",
      fixture,
      "--input",
      "needs work",
      "--print-prompt",
      "--base-url",
      baseURL,
      "--api-key",
      "cli-secret-key",
      "--model",
      "openrouter/mock-model",
    ], {
      env: llmEnv("http://127.0.0.1:1/api/v1", "env-secret-key", "env/model"),
    });

    assert.equal(result.status, 0);
    assert.equal(requests[0].authorization, "Bearer cli-secret-key");
    assert.equal(requests[0].body.model, "openrouter/mock-model");
    assert.match(result.stdout, /needs work/);
    assert.doesNotMatch(result.stdout, /cli-secret-key/);
    assert.doesNotMatch(result.stderr, /cli-secret-key/);
    assert.doesNotMatch(result.stdout, /env-secret-key/);
    assert.doesNotMatch(result.stderr, /env-secret-key/);
  });
});

test("qadev run rejects base URLs with credentials", async () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  const result = await runNode(["run", "--project", fixture, "--input", "needs work", "--print-prompt"], {
    env: llmEnv("https://user:password@example.com/v1", "secret-key", "openrouter/mock-model"),
  });

  assert.equal(result.status, 2);
  assert.match(result.stderr, /base URL must not include username or password/);
  assert.doesNotMatch(result.stderr, /secret-key/);
});

test("qadev run requires a project", async () => {
  const result = await runNode(["run", "--input", "needs work", "--local-only", "--print-prompt"]);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /run requires --project <path>/);
});

test("qadev run requires non-empty input", async () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  const result = await runNode(["run", "--project", fixture, "--local-only", "--print-prompt"]);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /run requires non-empty --input <text>/);
});

test("qadev run requires prompt preview flag in the MVP", async () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  const result = await runNode(["run", "--project", fixture, "--input", "needs work", "--local-only"]);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /only supports prompt preview output/);
});

test("qadev run requires LLM configuration before scanning", async () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  const result = await runNode(["run", "--project", fixture, "--input", "needs work", "--print-prompt"]);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /Missing LLM configuration/);
  assert.match(result.stderr, /QADEV_LLM_BASE_URL/);
});

test("qadev run reports connection failure without leaking the key", async () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));

  await withMockChatServer(async ({ baseURL }) => {
    const result = await runNode(["run", "--project", fixture, "--input", "needs work", "--print-prompt"], {
      env: llmEnv(baseURL, "bad-secret-key", "openrouter/mock-model"),
    });

    assert.equal(result.status, 1);
    assert.match(result.stderr, /chat completions endpoint returned HTTP 401/);
    assert.doesNotMatch(result.stderr, /bad-secret-key/);
  }, { status: 401 });
});

test("qadev interactive starts after LLM preflight, reports status, and exits", async () => {
  await withMockChatServer(async ({ baseURL }) => {
    const result = await runNode(["interactive"], {
      input: "/status\n/exit\n",
      env: llmEnv(baseURL, "mock-secret-key", "openrouter/mock-model"),
    });

    assert.equal(result.status, 0);
    assert.match(result.stdout, /QA-to-Dev Client Runtime Interactive/);
    assert.match(result.stdout, /LLM connection ready/);
    assert.match(result.stdout, /Project: not selected/);
    assert.match(result.stdout, /LLM: connected/);
    assert.match(result.stdout, /bye/);
    assert.doesNotMatch(result.stdout, /mock-secret-key/);
  });
});

test("qadev interactive requires LLM configuration before accepting commands", async () => {
  const result = await runNode(["interactive"], { input: "/status\n/exit\n" });

  assert.equal(result.status, 2);
  assert.match(result.stderr, /Missing LLM configuration/);
  assert.doesNotMatch(result.stdout, /QA-to-Dev Client Runtime Interactive/);
  assert.doesNotMatch(result.stdout, /Project: not selected/);
});

test("qadev interactive scans, previews, and marks stale after new input", async () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  fs.writeFileSync(path.join(fixture, "login.js"), "export const label = 'Login';\n", "utf8");

  await withMockChatServer(async ({ baseURL }) => {
    const result = await runNode(["interactive"], {
      input: `/project ${fixture}\n/input login copy needs work\n/scan\n/preview\n/input another note\n/status\n/exit\n`,
      env: llmEnv(baseURL, "mock-secret-key", "openrouter/mock-model"),
    });

    assert.equal(result.status, 0);
    assert.match(result.stdout, /Scanned 1 files/);
    assert.match(result.stdout, /QA-to-Dev Client Runtime Prompt Preview/);
    assert.match(result.stdout, /login\.js/);
    assert.match(result.stdout, /Scan: not run/);
    assert.match(result.stdout, /Generated preview: no/);
  });
});

function runNode(args, options = {}) {
  return new Promise((resolve) => {
    const env = { ...process.env };
    delete env.QADEV_LLM_BASE_URL;
    delete env.QADEV_LLM_API_KEY;
    delete env.QADEV_LLM_MODEL;
    Object.assign(env, options.env ?? {});

    const child = spawn(process.execPath, [cliPath, ...args], {
      cwd: repoRoot,
      env,
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";

    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("close", (status) => {
      resolve({ status, stdout, stderr });
    });

    if (options.input) {
      child.stdin.end(options.input);
    } else {
      child.stdin.end();
    }
  });
}

async function withMockChatServer(fn, options = {}) {
  const requests = [];
  const status = options.status ?? 200;
  const server = http.createServer((request, response) => {
    let rawBody = "";
    request.setEncoding("utf8");
    request.on("data", (chunk) => {
      rawBody += chunk;
    });
    request.on("end", () => {
      requests.push({
        method: request.method,
        url: request.url,
        authorization: request.headers.authorization,
        body: rawBody ? JSON.parse(rawBody) : undefined,
      });
      response.writeHead(status, { "content-type": "application/json" });
      response.end(JSON.stringify({
        id: "chatcmpl-test",
        object: "chat.completion",
        choices: [{ message: { role: "assistant", content: "OK" } }],
      }));
    });
  });

  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  try {
    await fn({ baseURL: `http://127.0.0.1:${address.port}/api/v1`, requests });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
}

function llmEnv(baseURL, apiKey, model) {
  return {
    QADEV_LLM_BASE_URL: baseURL,
    QADEV_LLM_API_KEY: apiKey,
    QADEV_LLM_MODEL: model,
  };
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
