#!/bin/bash
set -e

# Make sure to run this from the root directory

# Clean up old deployment package
if [ -f "deployment_package.zip" ]; then
    rm deployment_package.zip
fi

# Remove stale containers/images
docker rm -f temp-lambda-packager 2>/dev/null || true
docker rmi -f lambda-packager:latest 2>/dev/null || true

# Build image for x86_64 Lambda
docker buildx build --platform linux/amd64 -t lambda-packager .

# Create a container from the image
docker create --name temp-lambda-packager lambda-packager

# Copy zip
docker cp temp-lambda-packager:/app/deployment_package.zip ./api/deployment_package.zip

# Clean up
docker rm temp-lambda-packager

# Run Terraform plan and apply to deploy new Lambda package
cd infra/aws
terraform plan -out=terraform.tfplan
terraform apply terraform.tfplan
