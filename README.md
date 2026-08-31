# AEGISYNTH
## Autonomous Payment Defence Compiler

> **Don't build another fraud detector. Build the machine that builds fraud defences.**

AEGISYNTH is a safe red-team / blue-team payment-security laboratory built for the **Mastercard AI Defence Lab for Payment Security @ GFF 2026**. It turns a newly observed synthetic attack family into a compact, explainable, formally checked defence package.

### Why it is different
Conventional fraud systems output a score. AEGISYNTH targets the slower operational gap after discovery: analysts still need to understand a new attack, write controls, test false positives, find bypasses, revise thresholds and safely deploy. AEGISYNTH automates that defensive compilation loop:

**Attack → Counterexample → Synthesis → Verification → Defence**

### What works today
- Safe synthetic payment-world generator (no real cards, PII, merchants or credentials).
- Adaptive fictional `ghost_merchant_swarm` attack family.
- Compact policy compiler with a strict false-positive budget.
- Counterexample-guided iterative synthesis (CEGIS-style feedback).
- Z3 formal satisfiability + governance checks.
- Responsible actions: `STEP_UP` / `REVIEW`, never automatic hard decline.
- Live Next.js dashboard with attack-evolution and verification views.
- FastAPI API with OpenAPI docs.
- Automated tests + GitHub Actions.
- Docker + free-tier Render blueprint.

### Run locally

```bash
# backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend (new terminal)
cd frontend
npm install
# PowerShell: $env:NEXT_PUBLIC_API_URL="http://localhost:8000"
# bash: export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:3000`. API docs: `http://localhost:8000/docs`.

Or run both with Docker:

```bash
docker compose up --build
```

### One-click lab API

```bash
curl "http://localhost:8000/api/v1/lab/run?seed=42&generations=4"
```

### Architecture
See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/SUBMISSION.md`](docs/SUBMISSION.md).

### Cost/scalability model
AEGISYNTH intentionally separates the **expensive control plane** (simulation/synthesis/verification, run when a new threat is discovered) from the **cheap data plane** (a compact compiled policy evaluated per transaction). The MVP therefore requires no paid LLM API and no proprietary Mastercard data. Production connectors can map existing payment feature stores and decisioning systems into the same compiler interface.

### Responsible AI
This repository is defensive and sandboxed. It does not contain instructions or credentials for attacking real payment systems. See [`SECURITY.md`](SECURITY.md).
