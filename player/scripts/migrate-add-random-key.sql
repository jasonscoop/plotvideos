ALTER TABLE videos ADD COLUMN random_key INTEGER NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_videos_random_key ON videos(random_key DESC);
UPDATE videos SET random_key = RANDOM();
