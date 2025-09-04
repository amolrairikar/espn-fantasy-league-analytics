#!/bin/bash

# Make sure to run this from the API directory

if [ -f "deployment_package.zip" ]; then
    rm deployment_package.zip
fi

docker build -t lambda-packager .
docker run --name temp-lambda-packager lambda-packager
docker cp temp-lambda-packager:/app/deployment_package.zip ./deployment_package.zip
docker rm temp-lambda-packager
