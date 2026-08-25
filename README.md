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
uv run harness
```

An interactive model selector appears when no provider or model flags are
given. Choose Codex with your ChatGPT account, the default local Gemma model,
or another configured provider. In the Codex submenu, choose `1` for the
account's default model or `2` to enter a custom model ID.

Explicit flags skip the selector, which keeps scripts and one-shot commands
non-interactive:

```powershell
uv run harness --provider codex
uv run harness --provider lmstudio --model "google/gemma-4-e4b"
```

You can also use the Python entry point:

```powershell
uv run python main.py
```

Run a single prompt and exit:

```powershell
uv run harness --once "read README.md"
```

Use a different local model id:

```powershell
uv run harness --model "google/gemma-4-e4b"
```

Use OpenAI with an API key from your environment:

```powershell
$env:OPENAI_API_KEY="your-api-key"
uv run harness --provider openai --model "gpt-5-codex"
```

Use a ChatGPT account through the official Codex App Server, without an API
key:

```powershell
uv run harness login
uv run harness login status
uv run harness --provider codex
```

For a remote machine or when the browser callback does not work:

```powershell
uv run harness login --device-code
```

Sign out with:

```powershell
uv run harness logout
```

The `codex` provider uses Codex-managed authentication and routes model tool
requests through HarnessAgent's registry, security policy, and approval gate.
The Codex CLI must be installed and available as `codex`.

Use Gemini through Google's OpenAI-compatible API:

```powershell
$env:GEMINI_API_KEY="your-gemini-api-key"
uv run harness --provider gemini --model "your-gemini-model-id"
```

Use any OpenAI-compatible endpoint:

```powershell
$env:OPENAI_API_KEY="your-provider-key"
uv run harness --provider openai-compatible --base-url "https://example.com/v1" --model "provider-model"
```

Do not pass API keys directly on the command line. Keep them in environment
variables so they do not appear in shell history.

Run HarnessAgent against another project folder:

```powershell
uv run harness --project "C:\Users\Dinesh\MyProject"
```

From any directory, point `uv` at the HarnessAgent package and choose the
target project:

```powershell
uv run --project "C:\Users\Dinesh\HarnessAgent" harness --project "C:\Users\Dinesh\MyProject"
```

## CLI Commands

Inside the interactive CLI:

```text
/help
/tools
/status
/security
/verify
/clear
/exit
```

## Test

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run python -m unittest discover -s tests
```
