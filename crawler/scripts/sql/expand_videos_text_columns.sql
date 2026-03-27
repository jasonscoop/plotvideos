-- PostgreSQL: cap title, url, thumbnail_url at 2000 characters.
--
-- Use this when widening from VARCHAR(512) (or any length ≤ 2000) with no long values:
ALTER TABLE videos
  ALTER COLUMN title TYPE VARCHAR(2000),
  ALTER COLUMN url TYPE VARCHAR(2000),
  ALTER COLUMN thumbnail_url TYPE VARCHAR(2000);
--
-- If those columns are TEXT and any row exceeds 2000 chars, the above will error.
-- Then use this instead (truncates overlong values to 2000):
-- ALTER TABLE videos
--   ALTER COLUMN title TYPE VARCHAR(2000) USING LEFT(title::text, 2000),
--   ALTER COLUMN url TYPE VARCHAR(2000) USING LEFT(url::text, 2000),
--   ALTER COLUMN thumbnail_url TYPE VARCHAR(2000) USING LEFT(COALESCE(thumbnail_url, '')::text, 2000);
