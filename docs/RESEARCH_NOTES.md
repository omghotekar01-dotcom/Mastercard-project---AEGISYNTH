# Research and Challenge Alignment

## Official challenge
Mastercard AI Garage publicly describes the GFF 2026 AI Defence Lab as a red-team / blue-team challenge to build an end-to-end adversarial AI system that:
1. identifies emerging and novel GenAI-powered payment fraud,
2. simulates attacks at scale, and
3. defends against them in real time.

Public organizer source: Mastercard AI Garage LinkedIn page/post for the GFF 2026 challenge (August 2026).

## Product-design principle
AEGISYNTH deliberately does not require a generative-model inference on every payment. The computationally expensive part is the defence-creation control plane; enforcement uses the compiled policy. This is intended to make the concept affordable and compatible with high-throughput payment decisioning.

## Adjacent methods, not novelty claims
- Counterexample-guided inductive synthesis / program synthesis is an established formal-methods family.
- Adversarial simulation and red teaming are established security methods.
- Rule-based payment controls and fraud scoring already exist.

AEGISYNTH's proposed contribution is the **integration of those ideas into an attack-to-deployable-defence compiler for novel payment-fraud families**, with explicit business constraints, adversarial counterexamples, formal verification and human-governed deployment artifacts.

The project intentionally avoids claiming that program synthesis or adversarial ML was invented here.
