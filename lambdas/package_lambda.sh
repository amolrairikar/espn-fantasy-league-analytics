#!/bin/bash

# Run this script from the root of the lambdas directory

DIRECTORY=$1
cd $DIRECTORY

if [ -f "$DIRECTORY/deployment_package.zip" ]; then
    rm "$DIRECTORY/deployment_package.zip"
fi

# Copy the Dockerfile from the root of the lambdas directory
cp ../../Dockerfile .

docker build -t step-fn-lambda-packager .
docker run --name temp-step-fn-lambda-packager step-fn-lambda-packager
docker cp temp-step-fn-lambda-packager:/app/deployment_package.zip ./deployment_package.zip
docker rm temp-step-fn-lambda-packager

rm Dockerfile

# # Run Terraform plan and apply to deploy new Lambda package
# cd ../../infra/aws
# terraform plan -out=terraform.tfplan
# terraform apply terraform.tfplan