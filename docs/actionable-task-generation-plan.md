# Actionable Task Generation Plan

## Background

The first Node interactive flow proved that the client can connect to an LLM, scan a project, and print a prompt preview. A real user run exposed the next product gap: `/preview` still looked like a raw scan summary, included `.pnpm-store` package-cache noise, and did not give a developer enough concrete entry points to start fixing the reported issue.

This iteration upgrades the Node client from scan preview toward a usable QA-to-dev task workflow.

## Product Goal

Turn a QA note such as `小程序我的订单页面顶部状态切换消失了` into a developer-usable task flow:

1. local `/preview` identifies likely project type, priority files, and a task skeleton without sending QA or scan context to the model;
2. explicit `/generate` sends QA input plus read-only scan context to the configured LLM and returns a structured development task.

## Scope

- Filter package/cache/build noise including `.pnpm-store`, `.cache`, `.vite`, `.yarn`, `.nuxt`, `.output`, `unpackage`, `dist`, `build`, `coverage`, `node_modules`, generated folders, and ignored dependency folders.
- Prioritize uni-app and frontend paths including `pages.json`, `src/pages`, `src/components`, `src/api`, `src/store`, `src/router`, and `src/utils`.
- Expand Chinese requirement terms into common code vocabulary:
  - `订单` -> `order`, `orders`, `orderList`;
  - `我的` -> `mine`, `my`, `user`, `profile`, `member`;
  - `状态` / `切换` -> `status`, `state`, `tab`, `tabs`, `switch`, `filter`.
- Add a developer task skeleton to `/preview`.
- Add interactive `/generate` as the only command that sends QA input and scan context for LLM generation.
- Keep the target project read-only.

## Non-Goals

- No automatic code modification.
- No target project command execution.
- No automatic Issue creation from the Node client.
- No full runtime call-chain proof from static scan alone.
- No provider-specific SDK dependency.

## User Flow

```text
node bin/qadev.mjs interactive
/project C:\path\to\target-project
/input 小程序我的订单页面顶部状态切换消失了
/scan
/preview
/generate
```

`/preview` is local and safe for quick inspection. `/generate` is the explicit model-call boundary.

## Acceptance Criteria

- `.pnpm-store` and cache/build output paths do not appear in scan previews or generation context.
- `pages.json` and key `src/*` frontend paths are ranked before unrelated file-tree noise.
- Chinese QA input can match common English code paths for order, mine/user/profile, status, tabs, switch, and filter.
- `/preview` includes priority investigation files and a developer task skeleton.
- `/generate` sends QA input and scan context only after the user types `/generate`.
- API keys do not appear in stdout, stderr, preview output, or generated task output from the client.
- Node and Python regression suites pass.

## Risks

- Static matching can still miss heavily customized naming conventions.
- Static scan can suggest candidate files, but cannot prove UI visibility or platform-specific rendering bugs.
- `/generate` quality depends on the configured provider and model.

## Follow-Ups

- Add per-project synonym configuration.
- Parse `pages.json` route metadata more deeply.
- Add optional target platform selection such as `mp-weixin`, `h5`, or `app-android`.
