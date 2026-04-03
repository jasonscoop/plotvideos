CREATE TABLE IF NOT EXISTS languages (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  code   TEXT NOT NULL UNIQUE,
  name   TEXT NOT NULL,
  locale TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS videos (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  original_id   INTEGER NOT NULL UNIQUE,
  title         TEXT    NOT NULL,
  duration      INTEGER NOT NULL DEFAULT 0,
  width         INTEGER NOT NULL DEFAULT 0,
  height        INTEGER NOT NULL DEFAULT 0,
  thumbnail_url TEXT    NOT NULL DEFAULT '',
  video_url     TEXT    NOT NULL DEFAULT '',
  hls_url       TEXT    NOT NULL DEFAULT '',
  slug          TEXT    NOT NULL DEFAULT '',
  created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
  random_key    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS title_translations (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  lang_id  INTEGER NOT NULL REFERENCES languages(id),
  title    TEXT    NOT NULL DEFAULT '',
  UNIQUE(video_id, lang_id)
);

CREATE TABLE IF NOT EXISTS subtitle_tracks (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  lang_id  INTEGER NOT NULL REFERENCES languages(id),
  url      TEXT    NOT NULL,
  UNIQUE(video_id, lang_id)
);

CREATE TABLE IF NOT EXISTS tags (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  lang_id     INTEGER NOT NULL REFERENCES languages(id),
  name        TEXT    NOT NULL,
  slug        TEXT    NOT NULL UNIQUE,
  video_count INTEGER NOT NULL DEFAULT 0,
  UNIQUE(name, lang_id)
);

CREATE TABLE IF NOT EXISTS categories (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  lang_id     INTEGER NOT NULL REFERENCES languages(id),
  name        TEXT    NOT NULL,
  slug        TEXT    NOT NULL UNIQUE,
  video_count INTEGER NOT NULL DEFAULT 0,
  UNIQUE(name, lang_id)
);

CREATE TABLE IF NOT EXISTS video_tags (
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  tag_id   INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (video_id, tag_id)
);

CREATE TABLE IF NOT EXISTS video_categories (
  video_id    INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  is_keyword  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (video_id, category_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_slug ON videos(slug);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_random_key ON videos(random_key DESC);
CREATE INDEX IF NOT EXISTS idx_title_translations_video_id ON title_translations(video_id);
CREATE INDEX IF NOT EXISTS idx_subtitle_tracks_video_id ON subtitle_tracks(video_id);
CREATE INDEX IF NOT EXISTS idx_tags_lang ON tags(lang_id);
CREATE INDEX IF NOT EXISTS idx_categories_lang ON categories(lang_id);
CREATE INDEX IF NOT EXISTS idx_video_tags_tag ON video_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_video_categories_category ON video_categories(category_id);

CREATE TABLE IF NOT EXISTS settings (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  key         TEXT NOT NULL UNIQUE CHECK(key <> '' AND key NOT GLOB '*[^a-z0-9_]*'),
  value       TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO settings (key, value, description) VALUES
  ('site_name', 'PlotVideos', 'Site brand name'),
  ('site_slogan', '', 'Site slogan'),
  ('site_description', '', 'Site home page description'),
  ('fetch_api_url', '', 'Crawler API base URL'),
  ('fetch_api_key', '', 'Crawler API key'),
  ('id_offset', '0', 'Public video ID offset'),
  ('slug_from', 'original_id_plus_offset', 'Video slug mode: original_id_plus_offset or title_original_id (title slug + original_id + id_offset)'),
  ('home_page_size', '16', 'Home index videos per page'),
  ('head_code', '', 'Extra code in <head> tag'),
  ('footer_code', '', 'Extra code in <footer> tag'),
  ('contact_email', '', 'DMCA and compliance contact email'),
  ('contact_telegram', '', 'Telegram contact'),
  ('contact_whatsapp', '', 'WhatsApp contact'),
  ('compliance_2257_title', '18 U.S.C. 2257 Compliance Statement', ''),
  ('compliance_2257_enabled', '1', ''),
  ('compliance_2257_content', '', ''),
  ('dmca_title', 'DMCA / Copyright Policy', ''),
  ('dmca_enabled', '1', ''),
  ('dmca_content', '', '');
