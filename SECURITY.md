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

## Threat Model and Residual Risks

Understanding what genaikeys does and does not protect against:

### What genaikeys protects against

- **Accidental logging of secret values** — only secret names are ever passed to the logger, never values.
- **Serialization leaks** — both `GenAIKeys` and `InMemorySecretManager` refuse `pickle`, `copy.copy`, and `copy.deepcopy`, raising `TypeError`. This prevents accidental inclusion of cached secrets in message queues, multiprocessing payloads, or serialized debugger state.
- **Accidental attribute exposure** — `__repr__` on both classes returns a redacted summary. Cache internals use `__slots__` and private attribute names so they don't appear in `vars()` output.
- **Framework probing via `__getattr__`** — attribute-style access (`sk.OPENAI_KEY`) is restricted to names matching `^[A-Z][A-Z0-9_]*$`. Framework-driven `getattr` probes for lowercase/dunder attributes fail fast with `AttributeError`, never hitting the backend.

### Residual risks (inherent Python limitations)

**Process memory dumps**

Secrets held in the in-process cache are Python `str` objects. CPython strings are immutable and may be interned, meaning the secret value can persist in memory beyond the lifetime of the local variable. A privileged attacker with access to the process address space (e.g. via `gdb`, `/proc/<pid>/mem`, core dumps, or a memory profiler) can extract live secrets. This is a fundamental CPython limitation.

Mitigations outside the scope of this library:
- Restrict OS-level access to your process (containers with `no-new-privileges`, minimal capabilities).
- Avoid core dump generation in production (`ulimit -c 0`).
- Use short `cache_duration` values and call `sk.clear()` proactively when a secret is no longer needed.

**Process-wide singleton**

`GenAIKeys` is a singleton. Any code running in the same Python interpreter that obtains a reference (e.g. via `from genaikeys import GenAIKeys; sk = GenAIKeys()`) can retrieve any cached secret. Do not run untrusted third-party code in the same interpreter as a `GenAIKeys` instance.

**Backend plugin trust**

`genaikeys` cannot enforce security guarantees on third-party `SecretManagerPlugin` implementations. A custom backend could log or persist secret values. Review any plugin you depend on.

**Secret names in logs**

Secret *names* (not values) appear in log output at `DEBUG` and `INFO` level. In some threat models the name alone is sensitive (it reveals what keys an application uses). If that applies to you, keep the `genaikeys` logger at `WARNING` or above in production.

