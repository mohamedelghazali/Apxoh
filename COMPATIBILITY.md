# COMPATIBILITY

## Purpose

This guide documents the current ARKHON foundation and its verified limits.

## Procedure

1. Use Python 3.11 or newer in an isolated environment.
2. Install the project and development dependencies using the documented package metadata.
3. Run `arkhon version`, `arkhon doctor`, and `pytest`.
4. Inspect the output and preserve logs as evidence where appropriate.
5. Treat missing dependencies, unavailable agent features, unavailable OS sandbox isolation (`bwrap` or `unshare -r --net`), and incomplete integrations as `BLOCKED` or `needs_validation` rather than `PASS`.

## Security Audit Subsystem Compatibility

- `arkhon audit` preserves legacy domain verification (`arkhon audit [project] --domain <domain>`) while adding `plan`, `run`, `status`, `coverage`, `verify-findings`, `validate`, `report`, `compare`, and `reassess` subcommands.
- Dynamic local security verification requires POSIX `O_NOFOLLOW`, `dir_fd`, `resource` rlimits, and Linux network-namespace isolation (`bwrap` or `unshare -r --net`). On platforms or containers where network-namespace creation is denied, `SandboxExecutor` fails closed to `BLOCKED` and static/structural source review remains available without fabricating sandbox claims.

Do not infer that an agent discovered or activated instructions merely because files exist. Test discovery, activation, persistence, and behavior for each supported product version.
