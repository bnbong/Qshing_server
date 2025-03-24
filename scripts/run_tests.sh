#!/bin/bash
# Script to run tests safely in docker environment

# Set up environment for testing
export ENVIRONMENT="development"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_USER="admin"
export POSTGRES_PASSWORD="password"
export POSTGRES_DB="phishing_data"
export MONGODB_HOST="localhost"
export MONGODB_PORT="27017"
export MONGODB_USER="admin"
export MONGODB_PASSWORD="password"
export MONGODB_NAME="phishing_feedback"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"

# Make sure Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Please start Docker and try again."
  exit 1
fi

# Start test containers
echo "Starting test containers..."
docker-compose up -d

# Wait for containers to be fully operational
echo "Waiting for containers to be ready..."
sleep 10

# Run tests
echo "Running tests..."
python -m pytest tests

# Cleanup
echo "Cleaning up..."
docker-compose down

echo "Tests completed!" 