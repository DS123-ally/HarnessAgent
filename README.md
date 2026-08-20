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
