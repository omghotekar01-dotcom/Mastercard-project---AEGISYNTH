# Deployment

## Fastest production-like demo: one free Render service
The FastAPI backend serves the judge-facing dashboard at `/`, so only one service is required for the submission demo.

1. Fork/use this repository in Render.
2. Create a Blueprint from the root `render.yaml` or create a Web Service with root directory `backend`.
3. Runtime: Docker. No environment variables or paid APIs are required.
4. Liveness health check: `/health`.
5. Capability readiness check: `/ready`.
6. After deploy, open the generated Render URL. The dashboard and `/api/v1/lab/run` share the same origin.

The separate Next.js frontend remains available for a richer split-service deployment, but it is optional for the submission demo.

## Liveness vs readiness
`/health` deliberately answers only one question: is the API process alive? It stays lightweight and returns HTTP 200 while the process is serving requests.

`/ready` is stricter and fail-closed. It returns HTTP 200 only when both judge-critical capabilities are present:

- the bundled dashboard exists; and
- the Z3 formal verifier is available.

If either capability is missing, `/ready` returns HTTP 503 with explicit failed checks. This prevents a deployment from presenting itself as ready while silently falling back from the formal-verification capability stated by the prototype.

`/api/v1/self-check` also includes the Z3 availability invariant alongside the deterministic benchmark, responsible-action, false-positive, human-approval, artifact-integrity, and dashboard checks.

## Local Docker
```bash
docker build -t aegisynth ./backend
docker run --rm -p 8000:8000 aegisynth
```

Then verify:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/api/v1/self-check
```

Open `http://localhost:8000` for the dashboard.

## Production hardening path
For a real payment-network pilot, keep the compiler in an offline/control plane, cryptographically sign approved policy artifacts with an organizational signing key, require human approval, run shadow/canary deployment, enforce least-privilege service identities, persist audit trails, and connect only approved payment features. The current SHA-256 review-package fingerprint is an integrity identifier, not an organizational digital signature. The compiled policy stays lightweight in the online path.
