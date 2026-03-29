CREATE TABLE languages_new (
  id     INTEGER PRIMARY KEY AUTOINCREMENT,
  code   TEXT NOT NULL UNIQUE,
  name   TEXT NOT NULL,
  locale TEXT NOT NULL
);
INSERT INTO languages_new (code, name, locale) SELECT code, name, locale FROM languages;
DROP TABLE languages;
ALTER TABLE languages_new RENAME TO languages;

CREATE TABLE title_translations_new (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  lang_id  INTEGER NOT NULL REFERENCES languages(id),
  title    TEXT    NOT NULL DEFAULT '',
  UNIQUE(video_id, lang_id)
);
INSERT INTO title_translations_new (id, video_id, lang_id, title)
  SELECT tt.id, tt.video_id, l.id, tt.title
  FROM title_translations tt INNER JOIN languages l ON l.code = tt.lang;
DROP TABLE title_translations;
ALTER TABLE title_translations_new RENAME TO title_translations;
CREATE INDEX IF NOT EXISTS idx_title_translations_video_id ON title_translations(video_id);

CREATE TABLE subtitle_tracks_new (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  lang_id  INTEGER NOT NULL REFERENCES languages(id),
  url      TEXT    NOT NULL,
  UNIQUE(video_id, lang_id)
);
INSERT INTO subtitle_tracks_new (id, video_id, lang_id, url)
  SELECT st.id, st.video_id, l.id, st.url
  FROM subtitle_tracks st INNER JOIN languages l ON l.code = st.lang;
DROP TABLE subtitle_tracks;
ALTER TABLE subtitle_tracks_new RENAME TO subtitle_tracks;
CREATE INDEX IF NOT EXISTS idx_subtitle_tracks_video_id ON subtitle_tracks(video_id);

CREATE TABLE video_tags_new (
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  tag_id   INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  lang_id  INTEGER NOT NULL REFERENCES languages(id),
  PRIMARY KEY (video_id, tag_id, lang_id)
);
INSERT INTO video_tags_new (video_id, tag_id, lang_id)
  SELECT vt.video_id, vt.tag_id, l.id
  FROM video_tags vt INNER JOIN languages l ON l.code = vt.lang;
DROP TABLE video_tags;
ALTER TABLE video_tags_new RENAME TO video_tags;
CREATE INDEX IF NOT EXISTS idx_video_tags_tag ON video_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_video_tags_lang ON video_tags(lang_id);

CREATE TABLE video_categories_new (
  video_id    INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  lang_id     INTEGER NOT NULL REFERENCES languages(id),
  is_keyword  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (video_id, category_id, lang_id)
);
INSERT INTO video_categories_new (video_id, category_id, lang_id, is_keyword)
  SELECT vc.video_id, vc.category_id, l.id, vc.is_keyword
  FROM video_categories vc INNER JOIN languages l ON l.code = vc.lang;
DROP TABLE video_categories;
ALTER TABLE video_categories_new RENAME TO video_categories;
CREATE INDEX IF NOT EXISTS idx_video_categories_category ON video_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_video_categories_lang ON video_categories(lang_id);
