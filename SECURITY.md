# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅        |
| < 1.0   | ❌        |

## Reporting a Vulnerability

If you discover a security vulnerability in genaikeys, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email the maintainer directly at: **ndamulelo@rihonegroup.com**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You should receive an acknowledgement within **48 hours**. We aim to release a fix within
**7 days** of confirmation for critical issues.

## Security Best Practices

When using genaikeys:

- **Never hard-code credentials** — use your cloud provider's keyless authentication
- **Use managed identities** where possible (Azure MI, AWS IAM roles, GCP service accounts)
- **Rotate secrets regularly** in your cloud vault
- **Restrict IAM permissions** to the minimum required (e.g. `Key Vault Secrets User`, `secretsmanager:GetSecretValue`, `Secret Manager Secret Accessor`)
- **Pin dependencies** using `poetry.lock` to avoid supply-chain attacks
