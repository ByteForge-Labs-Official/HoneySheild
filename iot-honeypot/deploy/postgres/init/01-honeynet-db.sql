-- ===========================================================================
-- Honeynet — initial database & roles.
-- Runs once on the first `docker compose up` (mounted under
-- /docker-entrypoint-initdb.d/).
-- ===========================================================================

-- App user — owns all tables.
CREATE ROLE honeynet_app LOGIN PASSWORD 'TZLdK4EVu58SPgY2Gpo7fznR9hFtcyXj';
-- Read-only role for Grafana.
CREATE ROLE honeynet_ro  LOGIN PASSWORD 'qxHuhLaEwTy4nXUGBsPJ6z2FYQcZDWv8';
-- Relay user (used by deploy/relay).
CREATE ROLE relay       LOGIN PASSWORD '2RBpTGQk5EWes9KHSqJfa78wbPyjDhun';
GRANT CONNECT ON DATABASE honeynet TO honeynet_app, honeynet_ro, relay;

-- Schemas.
CREATE SCHEMA IF NOT EXISTS events    AUTHORIZATION honeynet_app;
CREATE SCHEMA IF NOT EXISTS honeypots AUTHORIZATION honeynet_app;
CREATE SCHEMA IF NOT EXISTS ai        AUTHORIZATION honeynet_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA events, honeypots, ai
    GRANT SELECT ON TABLES TO honeynet_ro;