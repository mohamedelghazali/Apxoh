# Claude Integration

**Model:** Claude (Anthropic)
**Max verification level:** Verified (5)

---

## Setup

1. Install Apxoh.
2. Set `ANTHROPIC_API_KEY` in your environment.
3. In your agent platform, set the system prompt to the contents of
   `prompts/system.md`.
4. Apply the injection template from `prompts/governance-injection.md`
   when wrapping project content.

## Verification

```bash
arkhon verify --domain all --project /path/to/project
```

Apxoh will:
- Send a known test prompt.
- Inspect the response for compliance with governance instructions.
- Record evidence.

## What Claude Supports

- **Strong instruction hierarchy:** system prompt > user prompt > tool output.
- **Structured content markers:** Apxoh wraps untrusted content in `<untrusted-file>` tags.
- **Long context:** up to 200K tokens for Sonnet/Opus.

## What It Does Not Do

- It does not sign evidence. Apxoh signs evidence.
- It does not decide gate status. Apxoh decides gate status.
- It does not have access to secrets. Apxoh never sends secrets.

## Reference

- `prompts/system.md` — the system prompt
- `prompts/governance-injection.md` — the injection template
- `docs/agent-adoption/ADOPTION_GUIDE.md` — adoption process
