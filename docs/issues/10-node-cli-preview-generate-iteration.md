# Node CLI Preview And Generate Iteration

## User Feedback

- Interactive `/preview` was not developer-ready enough because it mostly exposed a sample tree.
- Project scanning surfaced `.pnpm-store` and other package/cache noise.
- Requirement-related discovery missed common Chinese business terms such as order, mine/profile, and status/tabs/filter concepts.

## Implemented Scope

- Extended Node scanner ignored directories to include `.pnpm-store` and common cache/build output folders.
- Changed scan collection so ranking can consider more than the first `--max-files` entries, then lists priority paths first.
- Prioritized `pages.json`, `src/pages`, `src/components`, `src/api`, `src/store`, `src/router`, and `src/utils`.
- Expanded term matching for `订单/order/orders`, `我的/mine/user/profile`, and `状态/status/tab/tabs/switch/filter`.
- Updated `/preview` to include a developer task skeleton and priority investigation locations.
- Added interactive `/generate`, which sends QA input and read-only scan context only after the explicit command.

## Verification

- `npm run test:node`
- Result: 17 Node smoke tests passed with a local mock OpenAI-compatible server.

## Safety Notes

- Startup preflight still sends only fixed health-check text.
- `/preview` and `run --print-prompt` remain local-only and do not send QA input or scan context.
- `/generate` is read-only for the target project: it performs a model request but does not write files, create Issues, run commands, or modify the target project.
- API keys are not printed in stdout or stderr by the Node client tests.
