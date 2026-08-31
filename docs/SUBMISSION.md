# Mastercard AI Defence Lab - Submission Package

## Challenge alignment
The public Mastercard AI Garage challenge asks for an end-to-end adversarial AI system that **identifies emerging/novel GenAI fraud, simulates attacks at scale, and defends against them in real time**. AEGISYNTH addresses the adaptation bottleneck: it turns a novel attack family into a verified deployment policy rather than only returning a fraud score.

## Deliverables
1. **Code repository** - this repository.
2. **Working web prototype** - frontend + FastAPI backend, deployable on free-tier hosting or Docker locally.
3. **Solution walkthrough deck/document** - generated separately in `/submission` in the final package.

## 60-second demo script
1. Open the dashboard: current baseline attack success is high against an unknown synthetic family.
2. Click **Release zero-day simulation**.
3. Show four synthesis generations; the red team mutates attacks and the compiler receives the escaped variants as counterexamples.
4. Show the final compiled policy, false-positive budget, benign acceptance and estimated policy latency.
5. Show the verification ledger: satisfiable policy, bounded false-positive rate, no hard decline, no protected attributes.
6. Close with: **"Fraudsters can mutate attacks in minutes. AEGISYNTH compresses the defender's response from analysis-to-code into attack-to-verified-policy."**

## Safety statement
The demo does not provide instructions for attacking real payment infrastructure. All attacks, merchants and transactions are fictional synthetic objects created inside the sandbox.
