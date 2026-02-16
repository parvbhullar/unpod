-- Initialize PostgreSQL databases for Unpod services
-- This script runs automatically when the postgres container starts

-- Create additional databases if needed
-- The default unpod_db is created via POSTGRES_DB env variable

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE unpod_db TO unpod;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialization complete for Unpod';
END $$;
