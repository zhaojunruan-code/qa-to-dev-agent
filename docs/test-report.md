# QA-to-Dev Prompt Agent Test Report

## Test Scope

- CLI startup and argument validation.
- Read-only project scan.
- Local structured task generation.
- Prompt preview.
- Markdown output saving.
- Local Issue Markdown fallback.
- Required section stability.

## Test Environment

- OS: Windows
- Runtime: Python 3
- Project: QA-to-Dev Prompt Agent
- LLM provider: not required for automated tests

## Test Cases

| Case | Result | Notes |
| --- | --- | --- |
| Compile package and tests | Passed | `python -m compileall qa_to_dev_agent tests` |
| CLI `--local-only` generates Markdown | Passed | Output file contains required sections |
| Empty input returns clear failure | Passed | Returns exit code 1 |
| Missing project path returns clear failure | Passed | Returns exit code 1 |
| `--print-prompt` works without API key | Passed | No LLM configuration required |
| Local Issue fallback writes Markdown | Passed | Issue Markdown created under configured directory |
| Scanner skips `.env` content and filename | Passed | `.env` excluded from sample tree and excerpts |
| Related file candidate discovery | Passed | QA terms match safe source filenames |
| Unreachable document URL | Passed | CLI records fetch failure and continues in local mode |
| Default unittest discovery | Passed | `python -m unittest discover -v` now runs 8 tests |
| Explicit tests discovery | Passed | `python -m unittest discover -s tests -v` runs 8 tests |
| BOM `package.json` scripts | Passed | Build, test, and lint scripts are detected |
| `file://` document URL scheme | Passed | URL is rejected without calling `urlopen` |

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
python -m compileall qa_to_dev_agent tests
python -m unittest discover -v
python -m unittest discover -s tests
```

## Release Recommendation

Recommended for MVP release after the final regression. The latest full run executed 9 tests successfully. Remote LLM calls and remote Issue creation still require provider credentials and GitHub/GitLab permissions, so they should remain documented as environment-dependent.
