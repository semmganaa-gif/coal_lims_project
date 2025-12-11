-- PostgreSQL Database Setup for Coal LIMS
-- Run this script as postgres superuser

-- 1. Create user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'coal_lims_user') THEN
        CREATE USER coal_lims_user WITH PASSWORD 'coal_lims_2025';
    END IF;
END $$;

-- 2. Create database (if not exists)
SELECT 'CREATE DATABASE coal_lims OWNER coal_lims_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'coal_lims')\gexec

-- 3. Grant privileges
GRANT ALL PRIVILEGES ON DATABASE coal_lims TO coal_lims_user;

-- 4. Connect to coal_lims and set up schema permissions
\c coal_lims

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO coal_lims_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO coal_lims_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO coal_lims_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO coal_lims_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO coal_lims_user;
