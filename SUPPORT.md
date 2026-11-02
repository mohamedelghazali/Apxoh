# Apxoh Support

Use this page for questions about installing, configuring, and using Apxoh. Security vulnerabilities must not be reported through public support issues; follow [SECURITY.md](SECURITY.md) instead.

## Before Opening a Support Issue

Include the information that is relevant and safe to share:

- Apxoh version (`arkhon version`).
- Python version and operating system.
- The exact command and working directory.
- Expected behavior and actual behavior.
- A minimal reproduction or sanitized configuration.
- Relevant logs with tokens, credentials, private URLs, and personal data removed.

Do not upload private source code, customer data, access tokens, API keys, or production evidence unless you have permission and have sanitized it.

## Support Channels

- **Bug reports:** use the [Bug Report issue template](https://github.com/mohamedelghazali/Apxoh/issues/new?template=bug_report.md).
- **Feature requests:** use the [Feature Request issue template](https://github.com/mohamedelghazali/Apxoh/issues/new?template=feature_request.md).
- **Rule proposals:** use the [New Rule issue template](https://github.com/mohamedelghazali/Apxoh/issues/new?template=new_rule.md).
- **Integration proposals:** use the [New Model Integration issue template](https://github.com/mohamedelghazali/Apxoh/issues/new?template=new_model_integration.md).
- **Security reports:** follow [SECURITY.md](SECURITY.md); do not create a public issue.

## What to Expect

Issues are reviewed on a best-effort basis. No guaranteed response or resolution time is promised by this document. Critical security reports should use the private channel described in the security policy.

## Troubleshooting

1. Run `arkhon version` to identify the installed release.
2. Run `arkhon doctor` when available in the installed version.
3. Run `arkhon validate` to validate the repository manifests, schemas, and rules.
4. Capture the exact error output and relevant environment details.
5. Check existing issues and documentation before opening a duplicate.

A diagnostic command passing does not prove that optional integrations, such as TSAR, are operational. If a required integration is unavailable, its required gate must remain BLOCKED.

---

**End of Support Guide**
