import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const cliPath = path.join(repoRoot, "bin", "qadev.mjs");

test("qadev help starts from the Node client entry", () => {
  const result = runNode(["--help"]);

  assert.equal(result.status, 0);
  assert.match(result.stdout, /QA-to-Dev Client Runtime/);
  assert.match(result.stdout, /qadev run --project <path>/);
});

test("qadev version comes from package metadata", () => {
  const result = runNode(["--version"]);

  assert.equal(result.status, 0);
  assert.equal(result.stdout.trim(), "0.1.0");
});

test("qadev run prints a local prompt and ignores protected paths", () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  fs.writeFileSync(path.join(fixture, "package.json"), JSON.stringify({ scripts: { test: "node --test", build: "vite build" } }), "utf8");
  fs.writeFileSync(path.join(fixture, "login.js"), "export const label = 'Login';\n", "utf8");
  fs.writeFileSync(path.join(fixture, ".env.local"), "SECRET=do-not-read\n", "utf8");
  fs.mkdirSync(path.join(fixture, "lib"));
  fs.writeFileSync(path.join(fixture, "lib", "generated.js"), "generated\n", "utf8");
  fs.mkdirSync(path.join(fixture, "node_modules"));
  fs.writeFileSync(path.join(fixture, "node_modules", "hidden.js"), "hidden\n", "utf8");

  const result = runNode([
    "run",
    "--project",
    fixture,
    "--input",
    "login button copy needs updating",
    "--local-only",
    "--print-prompt",
  ]);

  assert.equal(result.status, 0);
  assert.match(result.stdout, /LLM request: disabled in this MVP/);
  assert.match(result.stdout, /login button copy needs updating/);
  assert.match(result.stdout, /login\.js/);
  assert.doesNotMatch(result.stdout, /SECRET/);
  assert.doesNotMatch(result.stdout, /generated\.js/);
  assert.doesNotMatch(result.stdout, /hidden\.js/);
});

test("qadev run refuses non-local LLM mode in the MVP", () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  const result = runNode(["run", "--project", fixture, "--input", "needs work", "--print-prompt"]);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /LLM requests are not implemented/);
});

test("qadev run requires a project", () => {
  const result = runNode(["run", "--input", "needs work", "--local-only", "--print-prompt"]);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /run requires --project <path>/);
});

test("qadev run requires non-empty input", () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  const result = runNode(["run", "--project", fixture, "--local-only", "--print-prompt"]);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /run requires non-empty --input <text>/);
});

test("qadev run requires prompt preview flag in the MVP", () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  const result = runNode(["run", "--project", fixture, "--input", "needs work", "--local-only"]);

  assert.equal(result.status, 2);
  assert.match(result.stderr, /only supports prompt preview output/);
});

test("qadev interactive starts, reports status, and exits", () => {
  const result = runNode(["interactive"], { input: "/status\n/exit\n" });

  assert.equal(result.status, 0);
  assert.match(result.stdout, /QA-to-Dev Client Runtime Interactive/);
  assert.match(result.stdout, /Project: not selected/);
  assert.match(result.stdout, /bye/);
});

test("qadev interactive scans, previews, and marks stale after new input", () => {
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "qadev-node-"));
  fs.writeFileSync(path.join(fixture, "login.js"), "export const label = 'Login';\n", "utf8");
  const result = runNode(["interactive"], {
    input: `/project ${fixture}\n/input login copy needs work\n/scan\n/preview\n/input another note\n/status\n/exit\n`,
  });

  assert.equal(result.status, 0);
  assert.match(result.stdout, /Scanned 1 files/);
  assert.match(result.stdout, /QA-to-Dev Client Runtime Prompt Preview/);
  assert.match(result.stdout, /login\.js/);
  assert.match(result.stdout, /Scan: not run/);
  assert.match(result.stdout, /Generated preview: no/);
});

function runNode(args, options = {}) {
  return spawnSync(process.execPath, [cliPath, ...args], {
    cwd: repoRoot,
    encoding: "utf8",
    input: options.input,
  });
}
