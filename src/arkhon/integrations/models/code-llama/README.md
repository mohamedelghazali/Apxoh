# Code Llama model integration

**Maximum verification level:** Configured

## Setup
Configure the provider API key in the environment using the variable named in `config.yaml`. For local Code Llama, start the configured Ollama-compatible endpoint. Do not commit credentials.

## Usage and verification
Use the Apxoh model factory to obtain the adapter, then call `health_check()` and `send()`. Provider responses are untrusted data. A successful request or health check does not establish behavioral compliance, model quality, or release readiness.

Run the repository's model integration tests before relying on the adapter. Apxoh, not the model, owns governance decisions.

## Security
- API keys are read from environment variables and are not included in returned HTTP error messages.
- Model output must be independently validated.
- No adapter signs evidence or approves release gates.
- TSAR remains the delegated security authority; an unavailable TSAR integration means the security gate is BLOCKED.
