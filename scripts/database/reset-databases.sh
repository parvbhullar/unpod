#!/bin/bash

set -e

echo "WARNING: This will delete all data in the databases!"
read -p "Are you sure? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "Stopping containers..."
docker-compose down -v

echo "Removing volumes..."
docker volume rm unpod-github_postgres_data 2>/dev/null || true
docker volume rm unpod-github_mongodb_data 2>/dev/null || true
docker volume rm unpod-github_redis_data 2>/dev/null || true
docker volume rm unpod-github_kafka_data 2>/dev/null || true
docker volume rm unpod-github_zookeeper_data 2>/dev/null || true
docker volume rm unpod-github_zookeeper_log 2>/dev/null || true

echo "Starting fresh containers..."
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 10

echo "Running database initialization..."
./scripts/database/create-databases.sh

echo "Database reset complete!"
