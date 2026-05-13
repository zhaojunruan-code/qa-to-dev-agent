# QA-to-Dev Prompt Agent Release Review

## Review Conclusion

Approved for client-first runtime MVP release as a Git branch / pull request after the new Node client files are committed.

The implementation satisfies the expanded MVP scope: a client-first zero-dependency Node.js CLI shell/prototype, `qadev` help/version/run/interactive commands, mandatory LLM startup preflight with custom OpenAI-compatible `baseURL/apiKey/model`, explicit interactive `/generate`, a documented OpenAI Developers style app contract, read-only project scanning, prompt preview without LLM generation, existing Python compatibility path, README updates, product plan, test report, release review, and safety-focused regression tests.

## Release Blockers

None for the tracked release branch.

Resolved blockers from review:

- `--docs-url` no longer accepts `file://` or other local schemes. Only `http` and `https` are allowed.
- Default unittest discovery now runs the suite.
- BOM-prefixed `package.json` files are supported for script detection.
- Windows stdout/stderr are reconfigured to UTF-8 with replacement errors when supported.
- `docs/release-review.md` is now a real release artifact rather than a placeholder.
- `--interactive` starts a stateful REPL without requiring `--project`.
- `/generate --llm`, `/save`, `/issue local`, and `/issue remote` require explicit confirmation before side effects.
- Local `.env*`, `lib`, generated, `dependency`, `dependencies`, `.pnpm-store`, and `unpackage` file inputs are rejected before reading.
- Markdown output and Issue backups are blocked inside the selected target project.
- `qadev` Node client is available through `bin/qadev.mjs` and `package.json` bin metadata.
- `docs/client-first-runtime-plan.md` records the product-management requirement that feature descriptions must be standardized, executable, and unambiguous.
- `docs/client-runtime-contract.md` records agent goal, input shape, expected output, tools, state, approval gates, mandatory LLM preflight, and prove command.
- Node client startup requires a fixed `/chat/completions` health check before `run` scans or `interactive` accepts commands. It does not send QA input, target project paths, file names, source content, or generated prompts during preflight.
- Node and Python scanners ignore `.pnpm-store`, `unpackage`, and package cache/build output directories, prioritize `pages.json` and common `src/*` runtime paths, and expand common Chinese/English requirement terms for order/mine/status style requests.
- Node interactive `/preview` now prints a developer task skeleton and priority investigation locations while remaining local-only.
- Node interactive `/generate` sends QA input and scan context only after the explicit slash command, using the configured OpenAI-compatible `/chat/completions` endpoint.

Local workstation note:

- A local `.env` file exists in the working directory, but it is ignored and not tracked by Git. `git ls-files .env` returned no tracked file. The release artifact is the Git branch / PR only; do not publish an ad-hoc zip of the full working directory including ignored files.

## Non-Blocking Recommendations

- Add stricter output structure validation for LLM-generated responses.
- Add CI to run `python -m unittest discover -v`.
- Consider GitHub/GitLab API integration beyond `gh` / `glab`.
- Consider reading target-project `AGENTS.md` in a future version with explicit safety filtering.
- Consider a richer TUI after the slash-command REPL proves useful.
- Replace the zero-dependency JavaScript client shell/prototype with TypeScript build tooling once package installation and CI are in place.
- Add a structured JSON boundary between the Node client and the existing Python engine before enabling richer tools.
- Add OpenAI Agents SDK eval cases before enabling LLM-backed client generation.

## Risk Notes

- Static scanning provides candidate context, not a complete runtime call-chain proof.
- Remote document fetching depends on network and permissions.
- The startup LLM preflight sends the configured model name and fixed health-check text to the configured provider; users should choose provider settings deliberately.
- Interactive `/generate` sends scanned context to the configured provider only after the explicit slash command; users should treat it as a network/cost action.
- Remote Issue creation depends on local CLI authentication when using the CLI path.
- Users must choose an output or Issue backup directory outside the selected target project.
- The Node client currently implements prompt preview plus interactive generation only; Python remains the compatibility path for Markdown write and Issue features.
- `npm test` invokes both Node and Python suites, so CI should include Node.js and Python runtimes.

## Release Approval

Allowed to release MVP.

Verification commands:

```powershell
python -m unittest discover -v
python -m unittest discover -s tests -v
python -m qa_to_dev_agent.cli --interactive
node bin/qadev.mjs --help
node bin/qadev.mjs --version
$env:QADEV_LLM_BASE_URL="<provider-base-url>"
$env:QADEV_LLM_API_KEY="<provider-key>"
$env:QADEV_LLM_MODEL="<model-name>"
node bin/qadev.mjs run --project . --input "verify client-first CLI runtime" --print-prompt
npm test
```

Latest verification result:

- Default unittest discovery: 31 tests passed.
- Interactive smoke: passed.
- Node smoke: 17 tests passed with a local mock OpenAI-compatible provider.
- Combined `npm test`: passed 17 Node smoke tests and 31 Python regression tests.
- Client prove command: covered by Node mock-provider tests; real provider smoke remains a manual environment-dependent check.
- Compile check note: source import and unittest validation are the release gate on this workstation because existing ignored `__pycache__` files can block `compileall` cache writes.
