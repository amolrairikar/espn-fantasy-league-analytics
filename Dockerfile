FROM public.ecr.aws/lambda/python:3.13

WORKDIR /app

# Install zip using dnf since the container is Amazon Linux 2023 based
RUN dnf install -y zip

COPY api/requirements.txt .
COPY api ./api

# Install dependencies directly into /app (same as deployment package root)
RUN pip install -r requirements.txt -t .

RUN zip -r deployment_package.zip . -x "api/deployment_package.zip" "*__pycache__*" "*.pyc"
