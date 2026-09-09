FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --shell /usr/sbin/nologin aegisynth

COPY app ./app
RUN chown -R aegisynth:aegisynth /app

USER aegisynth
EXPOSE 8000

# Container health is a liveness contract. The deeper /ready endpoint deliberately
# executes the deterministic benchmark, review-package verification, and Z3 canary;
# keep that fail-closed readiness gate available to deployment/smoke checks without
# making container startup depend on completing the full verification workload inside
# Docker's short healthcheck timeout.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; port=os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3).read()" || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\" --proxy-headers"]
