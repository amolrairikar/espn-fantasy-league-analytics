#!/bin/bash

# Make sure to run this from the frontend directory

# Load the .env file into the current shell
set -a
source .env
set +a

echo "Account ID: $AWS_ACCOUNT_ID"
echo "CloudFront Distribution ID: $CLOUDFRONT_DISTRIBUTION_ID"

aws s3 sync dist/ "s3://${AWS_ACCOUNT_ID}-fantasy-insights-app-react-site/" --delete

# Invalidate the CloudFront cache to ensure the latest files are served
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"