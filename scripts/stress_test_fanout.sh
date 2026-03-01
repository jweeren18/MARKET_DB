#!/bin/bash
# Stress test: fan-out 9 indicator pods + 9 scoring pods across Kind workers.
# Simulates exactly what the market_pipeline DAG does for 4,019 tickers at BATCH_SIZE=500.

set -e

NAMESPACE=default
IMAGE=market-intelligence-jobs:latest
BATCH_SIZE=500
TOTAL_TICKERS=4019

echo "=== Stress Test: Fan-out at $TOTAL_TICKERS tickers (batch size $BATCH_SIZE) ==="
echo ""

# Stage 2: Indicators (9 pods in parallel)
echo "--- Stage 2: Launching indicator pods ---"
for start in $(seq 0 $BATCH_SIZE $((TOTAL_TICKERS - 1))); do
    idx=$((start / BATCH_SIZE))
    echo "  Pod indicators-$idx: tickers [$start:$((start + BATCH_SIZE))]"
    kubectl run "stress-indicators-$idx" \
        --image=$IMAGE \
        --restart=Never \
        --namespace=$NAMESPACE \
        --image-pull-policy=Never \
        --overrides="{
            \"spec\": {
                \"containers\": [{
                    \"name\": \"stress-indicators-$idx\",
                    \"image\": \"$IMAGE\",
                    \"imagePullPolicy\": \"Never\",
                    \"command\": [\"python\", \"jobs/calculate_indicators.py\"],
                    \"args\": [\"--all\", \"--batch-start\", \"$start\", \"--batch-size\", \"$BATCH_SIZE\"],
                    \"envFrom\": [{\"secretRef\": {\"name\": \"market-pipeline-secrets\"}}],
                    \"env\": [{\"name\": \"PYTHONUNBUFFERED\", \"value\": \"1\"}],
                    \"resources\": {
                        \"requests\": {\"memory\": \"1Gi\", \"cpu\": \"500m\"},
                        \"limits\": {\"memory\": \"2Gi\", \"cpu\": \"1000m\"}
                    }
                }]
            }
        }" &
done

echo ""
echo "Waiting for all indicator pods to complete..."
kubectl wait --for=jsonpath='{.status.phase}'=Succeeded \
    -l 'run' --namespace=$NAMESPACE --timeout=600s 2>/dev/null || true

echo ""
echo "--- Indicator pod results ---"
kubectl get pods --namespace=$NAMESPACE -o wide | grep stress-indicators

echo ""
echo "--- Stage 3: Launching scoring pods ---"
# Clean up indicator pods first
# kubectl delete pods -l run --namespace=$NAMESPACE --field-selector=status.phase==Succeeded

for start in $(seq 0 $BATCH_SIZE $((TOTAL_TICKERS - 1))); do
    idx=$((start / BATCH_SIZE))
    echo "  Pod scoring-$idx: tickers [$start:$((start + BATCH_SIZE))]"
    kubectl run "stress-scoring-$idx" \
        --image=$IMAGE \
        --restart=Never \
        --namespace=$NAMESPACE \
        --image-pull-policy=Never \
        --overrides="{
            \"spec\": {
                \"containers\": [{
                    \"name\": \"stress-scoring-$idx\",
                    \"image\": \"$IMAGE\",
                    \"imagePullPolicy\": \"Never\",
                    \"command\": [\"python\", \"jobs/score_opportunities.py\"],
                    \"args\": [\"--all\", \"--batch-start\", \"$start\", \"--batch-size\", \"$BATCH_SIZE\"],
                    \"envFrom\": [{\"secretRef\": {\"name\": \"market-pipeline-secrets\"}}],
                    \"env\": [{\"name\": \"PYTHONUNBUFFERED\", \"value\": \"1\"}],
                    \"resources\": {
                        \"requests\": {\"memory\": \"512Mi\", \"cpu\": \"500m\"},
                        \"limits\": {\"memory\": \"1Gi\", \"cpu\": \"1000m\"}
                    }
                }]
            }
        }" &
done

echo ""
echo "Waiting for all scoring pods to complete..."
kubectl wait --for=jsonpath='{.status.phase}'=Succeeded \
    -l 'run' --namespace=$NAMESPACE --timeout=600s 2>/dev/null || true

echo ""
echo "--- All pod results ---"
kubectl get pods --namespace=$NAMESPACE -o wide | grep stress-
