#!/bin/bash
# Build and push the jobs Docker image
# Usage: ./build-jobs.sh [tag]

set -e

TAG=${1:-latest}
IMAGE_NAME="market-intelligence-jobs"
REGISTRY=${DOCKER_REGISTRY:-""}  # Set DOCKER_REGISTRY env var for remote registry

# Full image name
if [ -z "$REGISTRY" ]; then
    FULL_IMAGE="${IMAGE_NAME}:${TAG}"
else
    FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"
fi

echo "Building image: ${FULL_IMAGE}"

# Build from project root
cd "$(dirname "$0")/.."

docker build \
    -f kubernetes/jobs/Dockerfile \
    -t "${FULL_IMAGE}" \
    .

echo "Build complete: ${FULL_IMAGE}"

# Push to registry if DOCKER_REGISTRY is set
if [ -n "$REGISTRY" ]; then
    echo "Pushing to registry: ${REGISTRY}"
    docker push "${FULL_IMAGE}"
    echo "Push complete"
else
    echo "Skipping push (DOCKER_REGISTRY not set)"
    echo "For local K8s (Docker Desktop), make sure the image is available:"
    echo "  docker images | grep ${IMAGE_NAME}"
fi
