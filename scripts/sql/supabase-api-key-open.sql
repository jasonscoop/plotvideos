-- STEP 1: Ensure UUID extension is enabled (required for uuid_generate_v4)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- STEP 2: Create the API keys table
CREATE TABLE IF NOT EXISTS api_keys
(
    id         SERIAL PRIMARY KEY,
    key        TEXT UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(16), 'hex'),
    name       VARCHAR,
    enabled    BOOLEAN              DEFAULT TRUE,
    expired_at TIMESTAMP            DEFAULT '2099-12-31',
    updated_at TIMESTAMP            DEFAULT now(),
    created_at TIMESTAMP            DEFAULT now()
);

-- STEP 3: Insert a sample key (auto-generated)
INSERT INTO api_keys (name)
VALUES ('Initial test key');

-- STEP 4: Enable RLS on videos
ALTER TABLE videos
    ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow access with x-api-key" ON videos;
CREATE POLICY "Allow access with x-api-key"
    ON videos
    FOR SELECT
    to anon
    USING (
    status = 'uploaded' AND
    EXISTS (SELECT 1
            FROM api_keys
            WHERE api_keys.key = current_setting('request.headers.x-api-key', true)
              AND api_keys.enabled = true
              AND api_keys.expired_at > now())
    );

-- Turn on security
alter table "videos"
    enable row level security;
-- Allow anonymous access
create policy "Allow public access"
    on videos
    for select
    to anon
    using (status = 'uploaded');