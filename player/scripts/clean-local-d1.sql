-- Wipe all player rows so you can refetch from the crawler (local D1 only).
-- Run: npx wrangler d1 execute luckvideos-db --local --file=scripts/clean-local-d1.sql

DELETE FROM video_tags;
DELETE FROM video_categories;
DELETE FROM subtitle_tracks;
DELETE FROM video_translations;
DELETE FROM videos;
DELETE FROM tags;
DELETE FROM categories;
DELETE FROM languages;
