# Security & Responsible AI

AEGISYNTH is a defensive research prototype.

- No real payment credentials or customer PII are required or included.
- Red-team simulations operate only on synthetic, fictional transaction objects.
- The compiler emits only `STEP_UP` or `REVIEW` actions for suspicious matches; it does not autonomously hard-decline customers.
- Protected demographic attributes are intentionally absent from the policy feature set.
- Generated policies are designed for human approval, shadow evaluation and canary deployment before production use.
- Do not connect this prototype to live payment infrastructure without organizational security review, access controls, signed policy artifacts, audit logging, and compliance assessment.
