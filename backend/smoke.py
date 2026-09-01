from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


REQUIRED_SELF_CHECKS = {
    "benchmark_seed",
    "baseline_attack_success",
    "final_attack_success",
    "fraud_coverage",
    "benign_acceptance",
    "policy_verified",
    "responsible_action",
    "false_positive_budget",
    "human_approval_required",
    "not_auto_deployed",
    "artifact_fingerprint",
    "artifact_integrity",
    "dashboard_present",
    "z3_formal_verifier_available",
}


def fetch_json(base_url: str, path: str) -> tuple[int, dict]:
    url = f"{base_url.rstrip('/')}{path}"
    try:
        with urlopen(url, timeout=20) as response:  # noqa: S310 - operator-supplied URL
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{path} returned HTTP {exc.code}: {body[:300]}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"{path} is unreachable: {exc}") from exc


def run(base_url: str) -> None:
    health_status, health = fetch_json(base_url, "/health")
    assert health_status == 200 and health.get("status") == "ok", "liveness check failed"

    ready_status, ready = fetch_json(base_url, "/ready")
    assert ready_status == 200 and ready.get("status") == "ready", "readiness check failed"
    assert all(ready.get("checks", {}).values()), "one or more readiness capabilities are unavailable"

    check_status, self_check = fetch_json(base_url, "/api/v1/self-check")
    assert check_status == 200 and self_check.get("status") == "pass", "runtime self-check failed"
    checks = self_check.get("checks", {})
    missing = REQUIRED_SELF_CHECKS - set(checks)
    assert not missing, f"self-check contract is missing: {sorted(missing)}"
    assert all(checks[name] is True for name in REQUIRED_SELF_CHECKS), "runtime contract contains a failed check"

    demo_status, demo = fetch_json(base_url, "/api/v1/demo")
    assert demo_status == 200, "reproducible demo endpoint failed"
    assert demo.get("seed") == 42, "demo seed drifted from the submitted benchmark contract"
    assert demo.get("final_policy", {}).get("verified") is True, "demo policy is not verified"
    assert demo.get("final_policy", {}).get("action") in {"STEP_UP", "REVIEW"}, "demo emitted an unsupported action"

    print(json.dumps({
        "status": "pass",
        "base_url": base_url,
        "service_version": health.get("version"),
        "checks_verified": len(REQUIRED_SELF_CHECKS),
    }, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="AEGISYNTH deployment smoke probe")
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        run(args.base_url)
    except (AssertionError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"SMOKE CHECK FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
