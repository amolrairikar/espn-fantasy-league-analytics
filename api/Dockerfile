FROM python:3.12-slim

# Install zip utility and clean cache
RUN apt-get update && apt-get install -y zip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip

RUN rm -rf deployment_package.zip \
    && mkdir deployment_package \
    && pip install -r requirements.txt -t deployment_package \
    && cp main.py deployment_package/ \
    && cd deployment_package \
    && zip -r ../deployment_package.zip .
