ALTER TABLE languages ADD COLUMN flag TEXT NOT NULL DEFAULT '';
UPDATE languages SET flag = CASE code
  WHEN 'en' THEN '🇺🇸'
  WHEN 'de' THEN '🇩🇪'
  WHEN 'fr' THEN '🇫🇷'
  WHEN 'nl' THEN '🇳🇱'
  WHEN 'ja' THEN '🇯🇵'
  WHEN 'ko' THEN '🇰🇷'
  WHEN 'pt' THEN '🇧🇷'
  WHEN 'ar' THEN '🇸🇦'
  WHEN 'es' THEN '🇪🇸'
  WHEN 'zh' THEN '🇨🇳'
  ELSE ''
END;
