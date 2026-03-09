#!/bin/bash
set -e

IMAGE_NAME="step-fn-lambda-packager"
CONTAINER_NAME="temp-lambda-build"

# Clean up old deployment package
if [ -f "deployment_package.zip" ]; then
    rm deployment_package.zip
fi

# Remove existing container if it exists. 
# Redirect stderr to /dev/null so it doesn't complain if the container isn't there.
docker rm -f $CONTAINER_NAME 2>/dev/null || true

# Build for the correct architecture (Lambda x86_64)
docker build --platform linux/amd64 -t $IMAGE_NAME .

# Extract the file
# We use 'create' because we don't need the container to actually run
docker create --name $CONTAINER_NAME $IMAGE_NAME
docker cp $CONTAINER_NAME:/app/deployment_package.zip ./deployment_package.zip

# Cleanup
docker rm -f $CONTAINER_NAME
echo "Successfully created deployment_package.zip"
