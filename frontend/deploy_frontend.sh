#!/bin/bash

# Make sure to run this from the frontend directory
npm run build

# automatically export all variables
set -o allexport
source .env
set +o allexport

echo s3://${AWS_ACCOUNT_NUMBER}-fantasy-insights-app-react-site
aws s3 sync ./dist s3://${AWS_ACCOUNT_NUMBER}-fantasy-insights-app-react-site --delete
