-- One-time: align DB with ORM after removing author fields from ``Video``.
ALTER TABLE videos DROP COLUMN IF EXISTS author_name;
ALTER TABLE videos DROP COLUMN IF EXISTS author_url;
