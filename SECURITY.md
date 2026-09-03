# Security & Responsible AI

AEGISYNTH is a **defensive, synthetic payment-security research prototype**. It turns simulated fraud patterns into human-reviewable defensive policies; it is not a payment processor, credential store, autonomous enforcement engine, or production fraud-decision service.

## Safety contract

- **Synthetic evidence only.** Demonstrations and benchmark results use synthetic transactions. Do not add real card data, payment credentials, authentication secrets, or production customer records.
- **No autonomous hard decline.** Compiled triggered actions are limited to `STEP_UP` or `REVIEW`; review artifacts must not be interpreted as authorization to block a real payment.
- **Human approval required.** Judge-facing review packages remain `HUMAN_APPROVAL_REQUIRED` and `NOT_DEPLOYED`. Deployment decisions belong to an external, accountable governance process.
- **Formal/business checks fail closed.** Review packaging requires the declared Z3 verifier and configured false-positive/latency budgets. Missing formal verification must not be presented as verified evidence.
- **Protected demographic attributes stay out of policy features.** The current defensive policy uses operational payment features only.
- **Benchmark claims are reproducible prototype claims, not Mastercard claims.** Submitted metrics describe this repository's deterministic synthetic benchmark configuration and must not be changed unless a reproducible rerun justifies the update.

## Review artifact trust model

`artifact_sha256` is an **integrity fingerprint, not a digital signature or proof of authorship**. It detects accidental or uncoordinated modification of protected review-package fields, but a party capable of rewriting an artifact can also recompute a SHA-256 digest.

Consumers must therefore use the repository's semantic review verification path rather than trusting the digest alone. The verifier independently checks the supported review contract, defensive action boundary, current verification evidence, and declared business budgets.

A verified review package means only that a synthetic defensive policy passed the repository's current checks and is ready for human review. It does **not** mean that the policy is authenticated, approved for production, safe for every payment environment, or authorized to make autonomous payment decisions.

## Secrets and data handling

Never commit or upload:

- PAN/card numbers, CVVs, PINs, bank credentials, payment tokens, or real transaction histories;
- production API keys, signing keys, passwords, session cookies, private certificates, or webhook secrets;
- personally identifiable customer data that could reconstruct real payment activity.

Use synthetic fixtures and placeholder environment values for development. If a secret is accidentally committed, revoke or rotate it at the provider first, then remove it from repository history as appropriate.

## Safe contribution rules

Security changes should preserve the project's defensive scope. Good contributions include stronger schema validation, benchmark reproducibility checks, policy-compiler correctness, Z3/business guardrails, review-evidence integrity, dependency/deployment hardening, and regression tests for those controls.

Do not contribute operational fraud playbooks, credential-harvesting logic, evasion recipes, real-payment attack tooling, or features whose purpose is to defeat payment-security controls.

When changing a benchmark-sensitive path, keep submitted benchmark claims unchanged unless a deterministic rerun justifies new values. Prefer regression tests that bind important claims to executable evidence.

## Reporting a vulnerability

If you find a flaw that could cause AEGISYNTH to misrepresent verification status, benchmark evidence, governance state, or defensive policy behavior, open a GitHub issue with a minimal synthetic reproduction. Do not include real payment data or secrets.
