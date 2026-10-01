-- Runs once, when Postgres starts with an empty data volume.
-- To re-run after editing: docker compose down -v (this deletes the data).

CREATE TABLE IF NOT EXISTS requests_history (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    endpoint    TEXT NOT NULL,      -- request type, e.g. 'commits'
    params      JSONB NOT NULL,     -- e.g. {"target": "facebook/react"}
    status_code INTEGER,            -- NULL when GitHub was never reached (timeout, DNS)
    duration_ms INTEGER NOT NULL,
    response    JSONB,
    error       TEXT
);

-- The history page lists newest first.
CREATE INDEX IF NOT EXISTS idx_requests_history_created_at
    ON requests_history (created_at DESC, id DESC);
