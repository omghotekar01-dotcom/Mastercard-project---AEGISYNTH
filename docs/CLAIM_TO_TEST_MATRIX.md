# AEGISYNTH Claim-to-Test Matrix

This document maps every material public claim in the Kaggle writeup, README, demo and deck to concrete implementation evidence. The project intentionally stays inside the submitted scope.

| Public claim | Implementation evidence | Verification / test |
|---|---|---|
| AEGISYNTH uses a safe synthetic payment world | `backend/app/simulator.py` generates fictional transactions only | `backend/tests/test_safety.py::test_synthetic_world_contains_no_real_identifiers` |
| Synthetic benchmark evidence excludes payment credentials | `Transaction` exposes only synthetic feature-level benchmark fields; generated rows serialize to that same approved schema | `backend/tests/test_synthetic_data_minimization_contract.py::test_synthetic_transaction_contract_excludes_payment_credentials` |
| A novel attack is converted into a defence policy | `AegisynthEngine.run()` + `DefenceCompiler.synthesize()` | `test_engine.py::test_lab_compiles_verified_policy` |
| The defence is attacked again and bypasses become counterexamples | `engine.py` creates harder generations and collects escaped transactions | `test_safety.py::test_counterexamples_are_escaped_attack_variants` |
| Final controls respect a strict false-positive budget | `DefenceCompiler(max_fpr=0.02)` and `verify_policy()` | `test_engine.py::test_lab_compiles_verified_policy` |
| Schema-bypassed numeric evidence cannot weaken compiler or verifier guardrails | compiler policy-driving features require real, finite in-domain values; verifier budgets and policy numerics independently reject booleans and non-finite values | `backend/tests/test_compiler_boolean_evidence_guardrails.py`; `backend/tests/test_compiler_nonfinite_evidence_guardrails.py`; `backend/tests/test_verifier_boolean_numeric_guardrails.py`; `backend/tests/test_verifier_nonfinite_guardrails.py` |
| AEGISYNTH never emits an autonomous hard decline | allowed triggered actions are `STEP_UP` / `REVIEW`; direct scoring fails closed on malformed, unknown or `PASS` triggered actions | `test_safety.py::test_compiler_never_emits_hard_decline`; `test_policy_scoring_identity.py` action-safety regressions |
| Sensitive demographic attributes are not part of the compiled policy | policy schema contains operational payment features only | `test_safety.py::test_policy_schema_contains_only_approved_features` |
| Formal verification is performed with Z3 when installed | `backend/app/verification.py` | `test_safety.py::test_verifier_rejects_invalid_policy_domain` |
| Formal verification fails closed when Z3 is inconclusive | `verify_policy()` rejects non-`sat`/non-`unsat` solver outcomes instead of promoting the policy | `backend/tests/test_verifier_inconclusive_fail_closed.py::test_verifier_fails_closed_when_z3_is_inconclusive` |
| Human governance remains required | policy output is reviewable and action is step-up/review; no deployment write API exists | API/meta tests + README governance notes |
| No per-transaction LLM call is required | online output is a compact deterministic policy; MVP has no paid LLM dependency | dependency audit + `/api/v1/meta` |
| Seed-42 benchmark is reproducible | deterministic `random.Random(seed)` simulator; invalid calibration inputs are rejected before consuming RNG state; repeated engine runs and fresh engine instances must emit identical serialized evidence for identical inputs | `test_api.py::test_reproducible_demo_matches_committed_benchmark`; `test_simulator_sample_counts.py` RNG-state regressions; `backend/tests/test_engine_reproducibility_contract.py` |
| Benchmark values are prototype-only | `/api/v1/meta` and UI explicitly label synthetic scope | `test_api.py::test_meta_is_explicitly_synthetic_and_governed` |
| Public service exposes health/readiness signals | `/health` and `/ready` | `test_api.py::test_health_readiness_and_dashboard` |
| A judge can reproduce the submitted benchmark directly | `/api/v1/demo` fixes seed 42 and four generations | API regression test |
| Judge-facing review provenance is bound to deterministic replay, not only a recomputable SHA-256 fingerprint | `verify_review_package()` replays the deterministic engine from the package seed, attack family, generation count and business budget, then requires reproduced policy/evidence equality | `backend/tests/test_review_package_replay_provenance_contract.py::test_recomputed_fingerprint_cannot_relabel_benchmark_seed` |
| Review-package semantic verification fails closed on verifier or replay runtime failures | `_has_current_semantic_evidence()` catches verifier/replay dependency and runtime exceptions at the review trust boundary and rejects the artifact instead of allowing an exception to weaken provenance checks | `backend/tests/test_review_package_replay_provenance_contract.py::test_replay_runtime_failure_fails_closed`; `backend/tests/test_review_package_replay_provenance_contract.py::test_unexpected_replay_exception_fails_closed`; `backend/tests/test_review_package_replay_provenance_contract.py::test_unexpected_verifier_exception_fails_closed` |
| Review-package compiler provenance fails closed on malformed threshold evidence | `_matches_compiler_profile()` rejects schema-bypassed arithmetic/type/value failures while reconstructing the semantic `ZD-*` policy identity, so malformed or non-finite compiler thresholds cannot escape as verifier/runtime exceptions | `backend/tests/test_review_package_compiler_profile_failclosed.py::test_review_verifier_rejects_schema_bypassed_nonfinite_compiler_thresholds` |
| Scoring evidence cannot silently alias transaction identities | `score_policy()` rejects blank, over-length, whitespace-containing, duplicate and cross-population transaction IDs | `test_policy_evidence_metadata.py` |
| Benign and attack scoring populations keep canonical synthetic provenance | scoring requires `benign` provenance for benign rows and a non-benign canonical family for attack rows | `test_policy_attack_family_provenance.py` |
| Simulator attack-family provenance is validated before RNG use | `PaymentWorld.attack()` rejects malformed/reserved family labels before generating samples | `test_simulator_sample_counts.py` attack-family/RNG-state regressions |
| Counterexample traces cannot present ambiguous escaped-sample identities | `CounterexampleTrace` rejects blank, whitespace-containing, over-length and duplicate sample IDs | `test_iteration_evidence_integrity.py` |
| Judge-facing attack-family provenance is canonical | `LabResult` and `ReviewPackage` reject whitespace-containing and reserved `benign` attack-family labels | `test_judge_attack_family_provenance.py` |
| Policy identity is consistent across schema, scoring and verification boundaries | canonical `policy_id` is required even when callers bypass ordinary Pydantic construction | `test_policy_identity_schema.py`; `test_policy_scoring_identity.py`; `test_verification_policy_identity.py` |
| Direct benchmark scoring fails closed on ambiguous identity or malformed latency evidence | `score_policy()` requires meaningful ASCII-safe policy/transaction identities and finite non-negative latency before computing coverage/FPR | `backend/tests/test_scoring_policy_identity_quality.py`; `backend/tests/test_scoring_transaction_identity_quality.py`; `backend/tests/test_scoring_latency_guardrails.py` |

## Reproducible benchmark contract

The public benchmark contract is stored in `submission/benchmark_seed42.json` and is expected to remain stable unless the benchmark methodology is explicitly versioned and the public submission is updated.

Current seed-42 values:

- baseline attack success: **53.83%**
- final attack success: **7.43%**
- attack-family coverage: **92.57%**
- benign acceptance: **99.43%**

These are synthetic prototype results, **not Mastercard production claims**.

### Integrity rule for benchmark changes

A code change must **not** edit the submitted benchmark contract merely to make a regression pass. If deterministic code legitimately changes benchmark output, the new result must first be reproduced from the pinned seed/methodology, reviewed for scope and safety, and then deliberately versioned alongside any public claim update. Until that happens, mismatch against `submission/benchmark_seed42.json` is a failure signal.

## Scope guardrail

AEGISYNTH is a defensive research/MVP system. It does not contain real card credentials, real merchant identities, instructions for exploiting payment networks, autonomous hard-decline logic, or production Mastercard data.
