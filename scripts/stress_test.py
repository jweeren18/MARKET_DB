"""
Stress test: launch indicator and scoring pods in parallel via kubectl.
Simulates the market_pipeline DAG fan-out for 4,019 tickers at BATCH_SIZE=500.
"""
import json
import subprocess
import sys
import time

BATCH_SIZE = 500
TOTAL_TICKERS = 4019
IMAGE = "market-intelligence-jobs:latest"
NAMESPACE = "default"
SECRET = "market-pipeline-secrets"


def create_pod(name, command, args, memory_req, memory_lim, cpu_req, cpu_lim):
    """Create a K8s pod via kubectl."""
    overrides = json.dumps({
        "spec": {
            "containers": [{
                "name": "job",
                "image": IMAGE,
                "imagePullPolicy": "Never",
                "command": command,
                "args": args,
                "envFrom": [{"secretRef": {"name": SECRET}}],
                "env": [{"name": "PYTHONUNBUFFERED", "value": "1"}],
                "resources": {
                    "requests": {"memory": memory_req, "cpu": cpu_req},
                    "limits": {"memory": memory_lim, "cpu": cpu_lim},
                },
            }]
        }
    })
    subprocess.run([
        "kubectl", "run", name,
        "--image", IMAGE,
        "--restart=Never",
        f"--namespace={NAMESPACE}",
        "--image-pull-policy=Never",
        f"--overrides={overrides}",
    ], check=True)


def wait_for_pods(label_prefix, count, timeout=600):
    """Wait for pods to complete and return timing info."""
    start = time.time()
    while time.time() - start < timeout:
        result = subprocess.run(
            ["kubectl", "get", "pods", f"--namespace={NAMESPACE}",
             "-o", "json"],
            capture_output=True, text=True,
        )
        pods = json.loads(result.stdout)["items"]
        matching = [p for p in pods if p["metadata"]["name"].startswith(label_prefix)]

        succeeded = sum(1 for p in matching if p["status"]["phase"] == "Succeeded")
        failed = sum(1 for p in matching if p["status"]["phase"] == "Failed")
        running = sum(1 for p in matching if p["status"]["phase"] in ("Running", "Pending"))

        print(f"  [{time.time() - start:.0f}s] {succeeded} succeeded, {running} running/pending, {failed} failed")

        if succeeded + failed >= count:
            break
        time.sleep(5)

    elapsed = time.time() - start
    return elapsed, succeeded, failed


def show_pod_distribution(label_prefix):
    """Show which nodes pods ran on."""
    result = subprocess.run(
        ["kubectl", "get", "pods", f"--namespace={NAMESPACE}",
         "-o", "wide", "--no-headers"],
        capture_output=True, text=True,
    )
    print()
    print(f"  {'POD':<35} {'STATUS':<12} {'NODE':<30} {'AGE'}")
    print(f"  {'-'*35} {'-'*12} {'-'*30} {'-'*10}")
    for line in result.stdout.strip().split("\n"):
        if label_prefix in line:
            parts = line.split()
            if len(parts) >= 7:
                print(f"  {parts[0]:<35} {parts[2]:<12} {parts[6]:<30} {parts[4]}")


def main():
    batches = list(range(0, TOTAL_TICKERS, BATCH_SIZE))
    num_batches = len(batches)

    print(f"=== Stress Test: {TOTAL_TICKERS} tickers, batch size {BATCH_SIZE}, {num_batches} pods per stage ===")
    print()

    # --- Stage 2: Indicators ---
    print(f"--- Stage 2: Launching {num_batches} indicator pods ---")
    for i, start in enumerate(batches):
        print(f"  Creating stress-ind-{i}: tickers [{start}:{start + BATCH_SIZE}]")
        create_pod(
            f"stress-ind-{i}",
            ["python", "jobs/calculate_indicators.py"],
            ["--all", "--batch-start", str(start), "--batch-size", str(BATCH_SIZE)],
            "1Gi", "2Gi", "500m", "1000m",
        )

    print()
    elapsed, ok, fail = wait_for_pods("stress-ind-", num_batches)
    print(f"\n  Indicators complete: {ok} succeeded, {fail} failed in {elapsed:.1f}s")
    show_pod_distribution("stress-ind-")

    # --- Stage 3: Scoring ---
    print(f"\n--- Stage 3: Launching {num_batches} scoring pods ---")
    for i, start in enumerate(batches):
        print(f"  Creating stress-score-{i}: tickers [{start}:{start + BATCH_SIZE}]")
        create_pod(
            f"stress-score-{i}",
            ["python", "jobs/score_opportunities.py"],
            ["--all", "--batch-start", str(start), "--batch-size", str(BATCH_SIZE)],
            "512Mi", "1Gi", "500m", "1000m",
        )

    print()
    elapsed2, ok2, fail2 = wait_for_pods("stress-score-", num_batches)
    print(f"\n  Scoring complete: {ok2} succeeded, {fail2} failed in {elapsed2:.1f}s")
    show_pod_distribution("stress-score-")

    # --- Summary ---
    print("\n" + "=" * 60)
    print(f"STRESS TEST COMPLETE")
    print(f"  Tickers:    {TOTAL_TICKERS}")
    print(f"  Batches:    {num_batches} per stage")
    print(f"  Indicators: {ok}/{num_batches} passed in {elapsed:.1f}s")
    print(f"  Scoring:    {ok2}/{num_batches} passed in {elapsed2:.1f}s")
    print("=" * 60)

    # Cleanup
    print("\nCleaning up pods...")
    subprocess.run(["kubectl", "delete", "pods", "--namespace", NAMESPACE,
                    "-l", "run", "--field-selector=status.phase==Succeeded"],
                   capture_output=True)


if __name__ == "__main__":
    # Clean up any leftover stress pods first
    subprocess.run(["kubectl", "delete", "pods", "--namespace", NAMESPACE,
                    "--field-selector=status.phase!=Running",
                    "-l", "run"], capture_output=True)
    main()
