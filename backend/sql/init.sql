-- Initialize PostgreSQL database for Stock Analysis System
-- This script creates necessary extensions and basic setup

-- Create extensions if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas if not exists
CREATE SCHEMA IF NOT EXISTS public;

-- Set timezone
SET timezone = 'Asia/Taipei';

-- Grant permissions to stock_user
GRANT ALL PRIVILEGES ON SCHEMA public TO stock_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO stock_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO stock_user;

-- Default permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO stock_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO stock_user;

-- Log initialization completion
SELECT 'PostgreSQL database initialized successfully for Stock Analysis System' AS status;