#!/bin/bash

set -e

echo "=========================================="
echo "Creating databases for Unpod services..."
echo "=========================================="

# Wait for services to be ready
echo "Waiting for PostgreSQL..."
until docker exec unpod-postgres pg_isready -U unpod -d unpod_db 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready!"

echo "Waiting for MongoDB..."
until docker exec unpod-mongodb mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null; do
    sleep 1
done
echo "MongoDB is ready!"

echo "Waiting for Redis..."
until docker exec unpod-redis redis-cli -a redis_secret ping 2>/dev/null | grep -q PONG; do
    sleep 1
done
echo "Redis is ready!"

echo "=========================================="
echo "All databases are ready!"
echo "=========================================="
echo ""
echo "Connection strings:"
echo "  PostgreSQL: postgres://unpod:unpod_secret@localhost:5432/unpod_db"
echo "  MongoDB:    mongodb://admin:admin_secret@localhost:27017/unpod_mongo"
echo "  Redis:      redis://:redis_secret@localhost:6379"
echo "  Kafka:      localhost:29092"
echo ""
