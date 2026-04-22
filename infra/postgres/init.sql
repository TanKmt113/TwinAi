CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS system_bootstrap (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  value TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO system_bootstrap (name, value)
VALUES ('phase', '01-foundation')
ON CONFLICT (name) DO UPDATE SET value = EXCLUDED.value;

