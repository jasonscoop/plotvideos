CREATE TABLE tags_new (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  lang_id     INTEGER NOT NULL REFERENCES languages(id),
  name        TEXT    NOT NULL,
  slug        TEXT    NOT NULL UNIQUE,
  video_count INTEGER NOT NULL DEFAULT 0,
  UNIQUE(name, lang_id)
);
INSERT INTO tags_new (id, lang_id, name, slug, video_count)
  SELECT t.id,
    COALESCE((SELECT vt.lang_id FROM video_tags vt WHERE vt.tag_id = t.id LIMIT 1), 1),
    t.name, t.slug, 0
  FROM tags t;
DROP TABLE tags;
ALTER TABLE tags_new RENAME TO tags;
CREATE INDEX IF NOT EXISTS idx_tags_lang ON tags(lang_id);

CREATE TABLE categories_new (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  lang_id     INTEGER NOT NULL REFERENCES languages(id),
  name        TEXT    NOT NULL,
  slug        TEXT    NOT NULL UNIQUE,
  video_count INTEGER NOT NULL DEFAULT 0,
  UNIQUE(name, lang_id)
);
INSERT INTO categories_new (id, lang_id, name, slug, video_count)
  SELECT c.id,
    COALESCE((SELECT vc.lang_id FROM video_categories vc WHERE vc.category_id = c.id LIMIT 1), 1),
    c.name, c.slug, 0
  FROM categories c;
DROP TABLE categories;
ALTER TABLE categories_new RENAME TO categories;
CREATE INDEX IF NOT EXISTS idx_categories_lang ON categories(lang_id);

CREATE TABLE video_tags_new (
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  tag_id   INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (video_id, tag_id)
);
INSERT OR IGNORE INTO video_tags_new (video_id, tag_id)
  SELECT video_id, tag_id FROM video_tags;
DROP TABLE video_tags;
ALTER TABLE video_tags_new RENAME TO video_tags;
CREATE INDEX IF NOT EXISTS idx_video_tags_tag ON video_tags(tag_id);

CREATE TABLE video_categories_new (
  video_id    INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  is_keyword  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (video_id, category_id)
);
INSERT OR IGNORE INTO video_categories_new (video_id, category_id, is_keyword)
  SELECT video_id, category_id, is_keyword FROM video_categories;
DROP TABLE video_categories;
ALTER TABLE video_categories_new RENAME TO video_categories;
CREATE INDEX IF NOT EXISTS idx_video_categories_category ON video_categories(category_id);

UPDATE tags SET video_count = (SELECT COUNT(*) FROM video_tags WHERE tag_id = tags.id);
UPDATE categories SET video_count = (SELECT COUNT(*) FROM video_categories WHERE category_id = categories.id);
