# Agent Governance Pack Installation

## Purpose

Stage Apxoh's shared governance instructions, nine role definitions, and eight skills for later use by supported coding agents.

## Install

Project scope:

```powershell
arkhon install --scope project --project .
```

Global user scope:

```powershell
arkhon install --scope global
```

The managed destinations are `.arkhon/agent-pack/` in a project and `~/.arkhon/agent-pack/` for the current user. Existing packs are never overwritten unless `--force` is supplied.

## Important activation boundary

The installer stages files only. It does not edit editor settings, install plugins, change agent permissions, or guarantee that a product discovers the staged instructions. Product-specific adapters remain separately configured and must be verified using their own integration guide.

Do not infer activation from file presence. For each product and version, verify:
- instruction discovery and precedence;
- skill discovery and loading;
- persistence across sessions;
- tool permissions and consent behavior;
- expected and adverse behavior;
- evidence and failure reporting.

Missing tools, unavailable product features, and unverified behavior remain BLOCKED, not PASS.
