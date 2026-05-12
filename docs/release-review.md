# QA-to-Dev Prompt Agent Release Review

## Review Conclusion

Approved for MVP release as a Git branch / pull request.

The implementation satisfies the agreed MVP scope: Python CLI entrypoint, read-only project scanning, fixed structured task output, local deterministic generation, OpenAI-compatible LLM configuration, Markdown output saving, local Issue fallback, remote Issue CLI fallback, README, product plan, test report, release review, and Issue backups.

## Release Blockers

None for the tracked release branch.

Resolved blockers from review:

- `--docs-url` no longer accepts `file://` or other local schemes. Only `http` and `https` are allowed.
- Default unittest discovery now runs the suite.
- BOM-prefixed `package.json` files are supported for script detection.
- Windows stdout/stderr are reconfigured to UTF-8 with replacement errors when supported.
- `docs/release-review.md` is now a real release artifact rather than a placeholder.

Local workstation note:

- A local `.env` file exists in the working directory, but it is ignored and not tracked by Git. `git ls-files .env` returned no tracked file. The release artifact is the Git branch / PR only; do not publish an ad-hoc zip of the full working directory including ignored files.

## Non-Blocking Recommendations

- Add output structure validation for LLM-generated responses.
- Add a mock HTTP server test for OpenAI-compatible provider variations.
- Add CI to run `python -m unittest discover -v`.
- Consider GitHub/GitLab API integration beyond `gh` / `glab`.
- Consider reading target-project `AGENTS.md` in a future version with explicit safety filtering.

## Risk Notes

- Static scanning provides candidate context, not a complete runtime call-chain proof.
- Remote document fetching depends on network and permissions.
- Remote LLM calls send scanned context to the configured provider; users should choose provider and project path deliberately.
- Remote Issue creation depends on local CLI authentication when using the CLI path.

## Release Approval

Allowed to release MVP.

Verification commands:

```powershell
python -m compileall qa_to_dev_agent tests
python -m unittest discover -v
python -m unittest discover -s tests -v
```

Latest verification result:

- Compile check: passed.
- Default unittest discovery: 9 tests passed.
- Explicit unittest discovery: 9 tests passed.
