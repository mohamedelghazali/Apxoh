# Apxoh Agent Governance Pack

This pack contains the repository's general agent instructions, nine role definitions, and eight skills.

Installation stages these files in a managed directory. It does **not** edit editor settings, install plugins, activate a coding agent, or claim behavioral integration. Follow the product-specific integration guide separately and verify instruction discovery and behavior in that product.

Managed destinations:
- Project scope: `.arkhon/agent-pack/`
- Global scope: `~/.arkhon/agent-pack/`

The generated `manifest.json` records the pack version, scope, and staged files. Re-running without `--force` never overwrites an existing pack.
