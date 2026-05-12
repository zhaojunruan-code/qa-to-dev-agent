# QA-to-Dev Prompt Agent Release Review

## Review Conclusion

Approved for MVP release as a Git branch / pull request.

The implementation satisfies the agreed MVP scope: Python CLI entrypoint, terminal interactive mode, read-only project scanning, fixed structured task output, local deterministic generation, OpenAI-compatible LLM configuration, Markdown output saving, local Issue fallback, remote Issue CLI fallback, README, product plan, test report, release review, and Issue backups.

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
- Local `.env*`, `lib`, generated, `dependency`, and `dependencies` file inputs are rejected before reading.
- Markdown output and Issue backups are blocked inside the selected target project.

Local workstation note:

- A local `.env` file exists in the working directory, but it is ignored and not tracked by Git. `git ls-files .env` returned no tracked file. The release artifact is the Git branch / PR only; do not publish an ad-hoc zip of the full working directory including ignored files.

## Non-Blocking Recommendations

- Add output structure validation for LLM-generated responses.
- Add a mock HTTP server test for OpenAI-compatible provider variations.
- Add CI to run `python -m unittest discover -v`.
- Consider GitHub/GitLab API integration beyond `gh` / `glab`.
- Consider reading target-project `AGENTS.md` in a future version with explicit safety filtering.
- Consider a richer TUI after the slash-command REPL proves useful.

## Risk Notes

- Static scanning provides candidate context, not a complete runtime call-chain proof.
- Remote document fetching depends on network and permissions.
- Remote LLM calls send scanned context to the configured provider; users should choose provider and project path deliberately.
- Remote Issue creation depends on local CLI authentication when using the CLI path.
- Users must choose an output or Issue backup directory outside the selected target project.

## Release Approval

Allowed to release MVP.

Verification commands:

```powershell
python -m unittest discover -v
python -m unittest discover -s tests -v
python -m qa_to_dev_agent.cli --interactive
```

Latest verification result:

- Default unittest discovery: 28 tests passed.
- Interactive smoke: passed.
- Compile check note: source import and unittest validation are the release gate on this workstation because existing ignored `__pycache__` files can block `compileall` cache writes.
