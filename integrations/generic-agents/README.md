# Generic agent integrations

This directory groups editor, coding-agent, and autonomous-agent integrations that are not model-provider adapters or platform integrations.

Each adapter lives in its own directory and retains its own configuration, installation guidance, prompts, skill bindings, and integration-test notes.

## Available adapters

- `aider/`
- `amazon-q/`
- `claude-code/`
- `cline/`
- `codex-openai/`
- `continue/`
- `cursor/`
- `devin/`
- `gemini-cli/`
- `jetbrains-ai/`
- `replit-agent/`
- `sourcegraph-cody/`
- `tabnine/`
- `windsurf/`

The root `config.yaml` describes the manual fallback integration. Individual adapter status and consent requirements are defined in each adapter's `config.yaml`.

Presence of an adapter is not proof of activation or behavioral verification. Follow each adapter's documented verification requirements.
