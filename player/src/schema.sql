CREATE TABLE IF NOT EXISTS videos (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  original_id   INTEGER NOT NULL UNIQUE,
  slug          INTEGER NOT NULL,
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

-- Migration (TEXT slug → numeric): recreate `videos` or ALTER; backfill slug = original_id + SLUG_OFFSET_VALUE then set NOT NULL.

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

CREATE TABLE IF NOT EXISTS languages (
  code        TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  locale      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
  id   INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categories (
  id   INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS video_tags (
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  tag_id   INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (video_id, tag_id)
);

CREATE TABLE IF NOT EXISTS video_categories (
  video_id    INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  PRIMARY KEY (video_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_slug ON videos(slug);
CREATE INDEX IF NOT EXISTS idx_video_translations_video_id ON video_translations(video_id);
CREATE INDEX IF NOT EXISTS idx_subtitle_tracks_video_id ON subtitle_tracks(video_id);
CREATE INDEX IF NOT EXISTS idx_video_tags_tag ON video_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_video_categories_category ON video_categories(category_id);

-- After creating these tables on an existing DB, run: POST /api/rebuild-taxonomies
-- (or re-sync videos so ingest repopulates junction rows). Crawler `keyword` is stored
-- in `video_categories` with `categories` JSON terms, not in `video_tags`.
