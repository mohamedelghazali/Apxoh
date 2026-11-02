# Model Integration

**Maximum verification level:** Configured

## Setup

1. Install Apxoh and configure the provider credentials described in `config.yaml`.
2. Set the required environment variable; do not store API keys in source control.
3. Review `prompts/system.md` and `prompts/governance-injection.md`.
4. Run the model integration tests with the repository's test suite.

## Verification level

This adapter provides a configured transport boundary. Its presence and a successful health check do not prove model quality, policy compliance, or safe behavior. Behavioral verification must be performed separately, and Apxoh remains responsible for governance decisions.

## Security notes

- Responses are untrusted input.
- Credentials are read from environment variables and must never be logged.
- Network failures and provider errors are returned as failed integration responses.
- Do not use model output as evidence of security or compliance without independent validation.
