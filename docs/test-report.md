# QA-to-Dev Prompt Agent Test Report

## Test Scope

- CLI startup and argument validation.
- Read-only project scan.
- Local structured task generation.
- Prompt preview.
- Markdown output saving.
- Local Issue Markdown fallback.
- Required section stability.
- Terminal interactive mode.
- Confirmation gates for file writes, LLM calls, and Issue creation.
- Sensitive local file input rejection.
- Target-project write boundary protection.

## Test Environment

- OS: Windows
- Runtime: Python 3
- Project: QA-to-Dev Prompt Agent
- LLM provider: not required for automated tests

## Test Cases

| Case | Result | Notes |
| --- | --- | --- |
| Source import through unittest | Passed | `python -m unittest discover -v` imports package and tests |
| CLI `--local-only` generates Markdown | Passed | Output file contains required sections |
| Empty input returns clear failure | Passed | Returns exit code 1 |
| Missing project path returns clear failure | Passed | Returns exit code 1 |
| `--print-prompt` works without API key | Passed | No LLM configuration required |
| Local Issue fallback writes Markdown | Passed | Issue Markdown created under configured directory |
| Scanner skips `.env` content and filename | Passed | `.env` excluded from sample tree and excerpts |
| Related file candidate discovery | Passed | QA terms match safe source filenames |
| Unreachable document URL | Passed | CLI records fetch failure and continues in local mode |
| Default unittest discovery | Passed | `python -m unittest discover -v` runs 28 tests |
| Explicit tests discovery | Passed | `python -m unittest discover -s tests -v` runs the suite |
| BOM `package.json` scripts | Passed | Build, test, and lint scripts are detected |
| `file://` document URL scheme | Passed | URL is rejected without calling `urlopen` |
| Interactive mode startup | Passed | `python -m qa_to_dev_agent.cli --interactive` starts without `--project` |
| Interactive plain text input | Passed | Text is appended to QA input |
| Interactive Windows project path | Passed | `/project C:\...` preserves backslashes |
| Interactive read-only scan | Passed | `/scan --max-files 5` returns project context |
| Interactive local generation | Passed | `/generate --local` returns the fixed Markdown structure |
| Interactive save confirmation | Passed | `/save` does not write on `n`; writes on `y` |
| Interactive LLM confirmation | Passed | `/generate --llm` cancels before client creation on `n` |
| Interactive remote Issue confirmation | Passed | Wrong typed confirmation cancels before Issue creation |
| Generated directory exclusion | Passed | `generated/` is skipped by the scanner |
| Sensitive input file rejection | Passed | `--input-file .env.local` returns a clear error |
| Sensitive docs file rejection | Passed | `--docs-file .env` returns a clear error |
| Ignored directory docs file rejection | Passed | `--docs-file lib/generated.md` returns a clear error |
| Dependency directory docs file rejection | Passed | `--docs-file dependencies/generated.md` returns a clear error |
| Singular dependency directory docs file rejection | Passed | `--docs-file dependency/generated.md` returns a clear error |
| Generated directory docs file rejection | Passed | `--docs-file generated/task.md` returns a clear error |
| Output inside target project rejection | Passed | `--output <project>/task.md` is blocked |
| Issue backup inside target project rejection | Passed | `--issue-dir <project>/docs/issues` is blocked |
| Real interactive local Issue path | Passed | `/issue local` uses `--issue-dir` and confirmation |
| Real interactive save boundary | Passed | `/save <project>/task.md` is blocked after confirmation |

## Passed Items

- CLI local generation path works.
- Prompt preview path works without network or API key.
- Required Markdown sections are present.
- Local Issue fallback works when remote permissions or CLIs are unavailable.
- Sensitive `.env` files are excluded from scanner output.
- Unreachable document URLs are reported explicitly instead of stopping the workflow.
- Default and explicit unittest discovery both execute the suite.
- BOM-prefixed `package.json` files are supported for script detection.
- `--docs-url` only allows `http` and `https`; `file://` is rejected without reading local file content.
- Terminal interactive mode starts without a project and supports stateful scan, generate, save, and Issue flows.
- Interactive write and remote side-effect operations are guarded by confirmation.
- `.env*`, `lib`, generated, `dependency`, and `dependencies` local file inputs are rejected before reading.
- Markdown output and Issue backups are blocked inside the selected target project.

## Failed Items

None after second regression.

## Defects

- Found during testing: scanner sample tree listed `.env` filename even though content was not read.
- Fix: sensitive filenames are now excluded before sample tree collection.
- Regression: passed.
- Found during independent testing: default `unittest discover` found 0 tests.
- Fix: added `tests/__init__.py`.
- Regression: passed.
- Found during independent testing: Windows console output could fail on uncommon Unicode.
- Fix: CLI reconfigures stdout/stderr to UTF-8 with replacement errors when supported.
- Regression: covered by CLI smoke and full unittest run.
- Found during independent testing: BOM `package.json` caused metadata read failure.
- Fix: package metadata now reads with `utf-8-sig`.
- Regression: passed.

## Fix Recommendations

- Add CI to run `python -m unittest discover -s tests`.
- Add provider mock tests for LLM HTTP response variants in a future iteration.

## Regression Recommendation

Run these commands before each release:

```powershell
python -m unittest discover -v
python -m unittest discover -s tests
python -m qa_to_dev_agent.cli --interactive
```

## Release Recommendation

The table above groups behavior-level cases; it is not a one-to-one list of unittest methods.

Recommended for MVP release after the final regression. The latest full unit run executed 28 tests successfully, including terminal interactive mode, scanner safety regressions, sensitive local input rejection, dependency directory rejection, generated directory rejection, and target-project write protection. Remote LLM calls and remote Issue creation still require provider credentials and GitHub/GitLab permissions, so they should remain documented as environment-dependent.
