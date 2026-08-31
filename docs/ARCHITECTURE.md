# AEGISYNTH Architecture

## Thesis
AEGISYNTH treats fraud defence creation as a constrained program-synthesis problem. The system converts a newly observed attack family into a low-latency payment policy by repeatedly generating candidate controls, mutating attacks to find bypasses, feeding those bypasses back as counterexamples, and formally checking safety constraints before a defence package is eligible for human approval.

## Control plane vs data plane
The expensive reasoning and adversarial simulation runs in a **control plane**. The online **data plane** executes only a compact compiled policy. This keeps inference cost and latency away from every payment transaction.

```text
Threat / novel cluster
        |
        v
Synthetic Payment World ---> Red-Team Mutator
        |                         |
        v                         v
Invariant/feature search --> Candidate Policy
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
             Counterexample test          Formal verifier
                    |                           |
                    +---------- fail -----------+
                               |
                               v
                           Re-synthesize
                               |
                            verified
                               v
                     Defence Package Registry
                               |
                       human/canary approval
                               |
                               v
                     low-latency enforcement
```

## Current MVP
- Fully synthetic data only; no card numbers, PII or real merchants.
- Parameterized attack-family generator.
- Constrained policy search with explicit false-positive budget.
- CEGIS-style counterexample loop.
- Z3 satisfiability and governance checks.
- Human-safe actions (`STEP_UP` / `REVIEW`) rather than automatic hard declines.
- Interactive dashboard and reproducible metrics.

## Production adaptation
Adapters can ingest an issuer/acquirer/network feature schema without changing the core compiler. A production deployment would add an authenticated feature store, stream processing, policy signing, change-management approvals, shadow/canary modes, audit retention and integration with existing risk-decisioning controls.
