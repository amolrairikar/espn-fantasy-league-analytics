FROM public.ecr.aws/lambda/python:3.13

WORKDIR /app

# Install zip using dnf since the container is Amazon Linux 2023 based
RUN dnf install -y zip

# Lambda layers require dependencies to be in a python/ directory
RUN mkdir -p python

COPY common_utils/requirements.txt .
COPY common_utils/ python/common_utils

# Install dependencies directly into /python
RUN pip install -r requirements.txt -t python

# Exclude pycache files from deployment package to reduce bloat
RUN zip -r deployment_package.zip python -x "*__pycache__*" "*.pyc"
