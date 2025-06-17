WITH ranked AS (SELECT id,
                       updated_at,
                       row_number() OVER (PARTITION BY updated_at ORDER BY id) AS rn
                FROM videos)
UPDATE videos t
SET updated_at = t.updated_at + (INTERVAL '1 millisecond' * r.rn)
FROM ranked r
WHERE t.id = r.id;