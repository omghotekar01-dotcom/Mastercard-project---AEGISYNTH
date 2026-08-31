# AEGISYNTH Claim-to-Test Matrix

This document maps every material public claim in the Kaggle writeup, README, demo and deck to concrete implementation evidence. The project intentionally stays inside the submitted scope.

| Public claim | Implementation evidence | Verification / test |
|---|---|---|
| AEGISYNTH uses a safe synthetic payment world | `backend/app/simulator.py` generates fictional transactions only | `backend/tests/test_safety.py::test_synthetic_world_contains_no_real_identifiers` |
| A novel attack is converted into a defence policy | `AegisynthEngine.run()` + `DefenceCompiler.synthesize()` | `test_engine.py::test_lab_compiles_verified_policy` |
| The defence is attacked again and bypasses become counterexamples | `engine.py` creates harder generations and collects escaped transactions | `test_safety.py::test_counterexamples_are_escaped_attack_variants` |
| Final controls respect a strict false-positive budget | `DefenceCompiler(max_fpr=0.02)` and `verify_policy()` | `test_engine.py::test_lab_compiles_verified_policy` |
| AEGISYNTH never emits an autonomous hard decline | allowed triggered actions are `STEP_UP` / `REVIEW` | `test_safety.py::test_compiler_never_emits_hard_decline` |
| Sensitive demographic attributes are not part of the compiled policy | policy schema contains operational payment features only | `test_safety.py::test_policy_schema_contains_only_approved_features` |
| Formal verification is performed with Z3 when installed | `backend/app/verification.py` | `test_safety.py::test_verifier_rejects_invalid_policy_domain` |
| Human governance remains required | policy output is reviewable and action is step-up/review; no deployment write API exists | API/meta tests + README governance notes |
| No per-transaction LLM call is required | online output is a compact deterministic policy; MVP has no paid LLM dependency | dependency audit + `/api/v1/meta` |
| Seed-42 benchmark is reproducible | deterministic `random.Random(seed)` simulator | `test_api.py::test_reproducible_demo_matches_committed_benchmark` |
| Benchmark values are prototype-only | `/api/v1/meta` and UI explicitly label synthetic scope | `test_api.py::test_meta_is_explicitly_synthetic_and_governed` |
| Public service exposes health/readiness signals | `/health` and `/ready` | `test_api.py::test_health_readiness_and_dashboard` |
| A judge can reproduce the submitted benchmark directly | `/api/v1/demo` fixes seed 42 and four generations | API regression test |

## Reproducible benchmark contract

The public benchmark contract is stored in `submission/benchmark_seed42.json` and is expected to remain stable unless the benchmark methodology is explicitly versioned and the public submission is updated.

Current seed-42 values:

- baseline attack success: **53.83%**
- final attack success: **7.43%**
- attack-family coverage: **92.57%**
- benign acceptance: **99.43%**

These are synthetic prototype results, **not Mastercard production claims**.

## Scope guardrail

AEGISYNTH is a defensive research/MVP system. It does not contain real card credentials, real merchant identities, instructions for exploiting payment networks, autonomous hard-decline logic, or production Mastercard data.
