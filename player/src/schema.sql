CREATE TABLE IF NOT EXISTS videos (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  original_id   INTEGER NOT NULL UNIQUE,
  slug          TEXT    NOT NULL DEFAULT '',
  title         TEXT    NOT NULL,
  duration      INTEGER NOT NULL DEFAULT 0,
  width         INTEGER NOT NULL DEFAULT 0,
  height        INTEGER NOT NULL DEFAULT 0,
  thumbnail_url TEXT    NOT NULL DEFAULT '',
  video_url     TEXT    NOT NULL DEFAULT '',
  hls_url       TEXT    NOT NULL DEFAULT '',
  store_dir     TEXT    NOT NULL DEFAULT '',
  keyword       TEXT    NOT NULL DEFAULT '',
  tags          TEXT    NOT NULL DEFAULT '[]',
  categories    TEXT    NOT NULL DEFAULT '[]',
  created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Migration: ALTER TABLE videos ADD COLUMN slug TEXT NOT NULL DEFAULT '';
-- Migration: CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_slug ON videos(slug) WHERE slug != '';

CREATE TABLE IF NOT EXISTS video_translations (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id    INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  lang        TEXT    NOT NULL,
  title       TEXT    NOT NULL DEFAULT '',
  keyword     TEXT    NOT NULL DEFAULT '',
  tags        TEXT    NOT NULL DEFAULT '[]',
  categories  TEXT    NOT NULL DEFAULT '[]',
  UNIQUE(video_id, lang)
);

CREATE TABLE IF NOT EXISTS subtitle_tracks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id    INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  lang        TEXT    NOT NULL,
  label       TEXT    NOT NULL,
  url         TEXT    NOT NULL,
  UNIQUE(video_id, lang)
);

CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_slug ON videos(slug) WHERE slug != '';
CREATE INDEX IF NOT EXISTS idx_video_translations_video_id ON video_translations(video_id);
CREATE INDEX IF NOT EXISTS idx_subtitle_tracks_video_id ON subtitle_tracks(video_id);
