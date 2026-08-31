# Deployment

## Fastest production-like demo: one free Render service
The FastAPI backend now serves a polished zero-dependency dashboard at `/`, so only one service is required.

1. Fork/use this repository in Render.
2. Create a Blueprint from the root `render.yaml` or create a Web Service with root directory `backend`.
3. Runtime: Docker. No environment variables or paid APIs are required.
4. Health check: `/health`.
5. After deploy, open the generated Render URL. The dashboard and `/api/v1/lab/run` share the same origin.

The separate Next.js frontend remains available for a richer split-service deployment, but it is optional for the submission demo.

## Local Docker
```bash
docker build -t aegisynth ./backend
docker run --rm -p 8000:8000 aegisynth
```
Open `http://localhost:8000`.

## Production hardening path
For a real payment-network pilot, keep the compiler in an offline/control plane, sign every policy artifact, require human approval, run shadow/canary deployment, enforce least-privilege service identities, persist audit trails, and connect only approved payment features. The compiled policy stays lightweight in the online path.
