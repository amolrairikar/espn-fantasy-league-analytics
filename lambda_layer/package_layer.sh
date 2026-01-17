#!/bin/bash
set -e

# Run this script from the lambda_layer directory

# Clean up old deployment package
if [ -f "deployment_package.zip" ]; then
    rm deployment_package.zip
fi

# Remove any stale containers/images
docker rm -f temp-layer-packager 2>/dev/null || true
docker rmi -f layer-packager:latest 2>/dev/null || true

# Build the Docker image for x86_64 Lambda
docker buildx build --platform linux/amd64 -t layer-packager .

# Create a container and copy the deployment package without running the Lambda entrypoint
docker create --name temp-layer-packager layer-packager
docker cp temp-layer-packager:/app/deployment_package.zip ./deployment_package.zip
docker rm temp-layer-packager
