# Gemini model integration

**Maximum verification level:** Configured

## Setup
Set `GOOGLE_API_KEY` in the environment. Do not commit credentials.

## Usage and verification
Use the Apxoh model factory to obtain the adapter, then call `health_check()` and `send()`. Provider responses are untrusted data. A successful request or health check does not establish behavioral compliance, model quality, or release readiness.

Run the repository's model integration tests before relying on the adapter. Apxoh, not the model, owns governance decisions.

## Security
- The API key is sent in the `x-goog-api-key` header and is not placed in the request URL.
- Model output must be independently validated.
- No adapter signs evidence or approves release gates.
- TSAR remains the delegated security authority; an unavailable TSAR integration means the security gate is BLOCKED.
