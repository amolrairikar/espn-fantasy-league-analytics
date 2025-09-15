#!/bin/bash

# Make sure to run this from the API directory

if [ -f "api/deployment_package.zip" ]; then
    rm api/deployment_package.zip
fi

docker build -t lambda-packager .
docker run --name temp-lambda-packager lambda-packager
docker cp temp-lambda-packager:/app/deployment_package.zip ./api/deployment_package.zip
docker rm temp-lambda-packager

# Run Terraform plan and apply to deploy new Lambda package
cd infra/aws
terraform plan -out=terraform.tfplan
terraform apply terraform.tfplan
