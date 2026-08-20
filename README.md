# HarnessAgent

HarnessAgent is a small Python coding-agent framework built around local
OpenAI-compatible models such as LM Studio.

## Current Primitives

- Model provider for LM Studio
- Conversation history
- Project instructions from `AGENTS.md`
- Context delivery and compaction
- File and shell tools with approval gates
- Project-root file safety
- Local skills from `.harness/skills`
- Durable memory in `.harness/state.json`
- Persistent task orchestration in `.harness/tasks.json`
- Subagent delegation records in `.harness/subagents.json`
- Verification through `uv run python -m unittest discover -s tests`
- JSONL observability events in `.harness/events.jsonl`
- Security policy enforcement from `.harness/security.json`

## Security

HarnessAgent applies a local security policy before file and shell actions.

- File tools stay inside the project root.
- Policy-denied paths such as `.git/**`, `.venv/**`, `.env`, `*.pem`, and
  `*.key` are blocked.
- Shell commands run from the project root.
- Shell commands must match the allowlist in `.harness/security.json`.
- Network and destructive commands are blocked by default.
- Secret-like values are redacted from file reads, shell output, and event logs.

Inspect the active policy from the agent with:

```text
show security policy
```

## Run

Start LM Studio with the local server enabled at:

```text
http://localhost:1234/v1
```

Then run:

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run python main.py
```

## Test

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run python -m unittest discover -s tests
```
