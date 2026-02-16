-- PostgreSQL initialization script
-- Creates required extensions and initial setup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable text search extension
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE postgres TO app_user;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialization completed successfully';
END
$$;
