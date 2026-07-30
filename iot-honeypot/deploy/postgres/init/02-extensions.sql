-- ===========================================================================
-- Honeynet — TimescaleDB extension + first hypertable.
-- ===========================================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Canonical hypertable for incoming attack events.
CREATE TABLE IF NOT EXISTS events.attack (
    id           BIGSERIAL,
    ts           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_ip    INET,
    source_country TEXT,
    honeypot     TEXT NOT NULL,
    protocol     TEXT NOT NULL,
    severity     TEXT NOT NULL DEFAULT 'low',
    raw          JSONB NOT NULL,
    PRIMARY KEY (id, ts)
);

SELECT create_hypertable(
    'events.attack', 'ts',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists       => TRUE
);

CREATE INDEX IF NOT EXISTS attack_protocol_ts_idx
    ON events.attack (protocol, ts DESC);
CREATE INDEX IF NOT EXISTS attack_source_ts_idx
    ON events.attack (source_ip, ts DESC);
CREATE INDEX IF NOT EXISTS attack_gin_raw
    ON events.attack USING GIN (raw);