#!/bin/bash

# Parse environment from argument
ENVIRONMENT=$1

# Make sure to run this from the frontend directory
npm run build

# automatically export all variables
set -o allexport
source .env
set +o allexport

if [ "$ENVIRONMENT" == "prod" ]; then
  S3_BUCKET_NAME=s3://${AWS_ACCOUNT_NUMBER}-fantasy-insights-app-react-site
else
  S3_BUCKET_NAME=s3://${AWS_ACCOUNT_NUMBER}-fantasy-insights-app-react-site-dev
fi

echo $S3_BUCKET_NAME
aws s3 sync ./dist $S3_BUCKET_NAME --delete