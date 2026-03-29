ALTER TABLE videos DROP COLUMN keyword;

CREATE TABLE title_translations (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  lang     TEXT    NOT NULL,
  title    TEXT    NOT NULL DEFAULT '',
  UNIQUE(video_id, lang)
);
INSERT INTO title_translations (id, video_id, lang, title)
  SELECT id, video_id, lang, title FROM video_translations;
DROP TABLE video_translations;
CREATE INDEX IF NOT EXISTS idx_title_translations_video_id ON title_translations(video_id);

CREATE TABLE video_tags_new (
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  tag_id   INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  lang     TEXT    NOT NULL DEFAULT 'en',
  PRIMARY KEY (video_id, tag_id, lang)
);
INSERT INTO video_tags_new (video_id, tag_id, lang)
  SELECT video_id, tag_id, 'en' FROM video_tags;
DROP TABLE video_tags;
ALTER TABLE video_tags_new RENAME TO video_tags;
CREATE INDEX IF NOT EXISTS idx_video_tags_tag ON video_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_video_tags_lang ON video_tags(lang);

CREATE TABLE video_categories_new (
  video_id    INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  lang        TEXT    NOT NULL DEFAULT 'en',
  is_keyword  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (video_id, category_id, lang)
);
INSERT INTO video_categories_new (video_id, category_id, lang, is_keyword)
  SELECT video_id, category_id, 'en', 0 FROM video_categories;
DROP TABLE video_categories;
ALTER TABLE video_categories_new RENAME TO video_categories;
CREATE INDEX IF NOT EXISTS idx_video_categories_category ON video_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_video_categories_lang ON video_categories(lang);

ALTER TABLE subtitle_tracks DROP COLUMN label;
