ALTER TABLE tags ADD COLUMN video_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE categories ADD COLUMN video_count INTEGER NOT NULL DEFAULT 0;
UPDATE tags SET video_count = (SELECT COUNT(*) FROM video_tags WHERE tag_id = tags.id);
UPDATE categories SET video_count = (SELECT COUNT(*) FROM video_categories WHERE category_id = categories.id);
