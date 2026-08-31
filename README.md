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
- Single-service FastAPI dashboard for the fastest free-tier deployment.
- Optional richer Next.js dashboard.
- FastAPI API with OpenAPI docs.
- Automated backend/API tests plus a ready-to-enable CI workflow template.
- Docker + free-tier Render blueprint.

### Fastest local run

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000` for the working dashboard and `http://localhost:8000/docs` for OpenAPI.

### Optional split Next.js frontend

```bash
cd frontend
npm install
# PowerShell: $env:NEXT_PUBLIC_API_URL="http://localhost:8000"
# bash: export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:3000`.

### Docker

```bash
docker build -t aegisynth ./backend
docker run --rm -p 8000:8000 aegisynth
```

Or run the split stack with:

```bash
docker compose up --build
```

### One-click lab API

```bash
curl "http://localhost:8000/api/v1/lab/run?seed=42&generations=4"
```

### Reproducible prototype benchmark
Seed `42` in the committed synthetic simulator currently produces:

- baseline attack success: **53.83%**
- final attack success after compilation: **7.43%**
- final fraud-family coverage: **92.57%**
- benign acceptance: **99.43%**

These numbers are synthetic prototype results, **not Mastercard production claims**. See [`submission/benchmark_seed42.json`](submission/benchmark_seed42.json).

### Architecture and deployment
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- [`docs/RESEARCH_NOTES.md`](docs/RESEARCH_NOTES.md)
- [`docs/SUBMISSION.md`](docs/SUBMISSION.md)

### Cost/scalability model
AEGISYNTH intentionally separates the **expensive control plane** (simulation/synthesis/verification, run when a new threat is discovered) from the **cheap data plane** (a compact compiled policy evaluated per transaction). The MVP therefore requires no paid LLM API and no proprietary Mastercard data. Production connectors can map existing payment feature stores and decisioning systems into the same compiler interface.

### Responsible AI
This repository is defensive and sandboxed. It does not contain instructions or credentials for attacking real payment systems. See [`SECURITY.md`](SECURITY.md).
