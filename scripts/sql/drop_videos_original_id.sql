-- Removes legacy ``original_id`` column from crawler ``videos`` (replaced by id-based paths).
-- One-time per database. No-op if the column is already gone.
ALTER TABLE videos DROP COLUMN IF EXISTS original_id;
