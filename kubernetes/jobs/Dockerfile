# Dockerfile for Kubernetes batch jobs
# This container includes all dependencies needed to run data processing tasks

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements-jobs.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-jobs.txt

# Copy application code
COPY backend/app /app/app
COPY backend/jobs /app/jobs

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Jobs will be executed by running specific scripts
# Example: python jobs/data_ingestion.py
ENTRYPOINT ["python"]
