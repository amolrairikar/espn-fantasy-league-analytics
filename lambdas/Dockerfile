FROM public.ecr.aws/lambda/python:3.13

WORKDIR /app

# Install zip using dnf since the container is Amazon Linux 2023 based
RUN dnf install -y zip

# Install dependencies directly into /app (same as deployment package root)
COPY requirements.txt .
RUN pip install -r requirements.txt -t .

# Copy code and subdirectories. This ensures /app/utils, /app/main.py, etc. exist
COPY . .

# Create the zip file
RUN zip -r deployment_package.zip . \
    -x "Dockerfile" \
    "*.sh" \
    "*.git*" \
    "*__pycache__*" \
    "*.pyc"
