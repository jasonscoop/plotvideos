INSERT OR IGNORE INTO settings (key, value, description) VALUES
  ('ad_home_sidebar', '', 'HTML: home left column below categories/tags'),
  ('ad_home_list_top', '', 'HTML: home above video grid'),
  ('ad_home_list_bottom', '', 'HTML: home below grid, before pagination'),
  ('ad_listing_sidebar', '', 'HTML: tag/category/watch left column below categories/tags'),
  ('ad_listing_list_top', '', 'HTML: tag/category above video grid'),
  ('ad_listing_list_bottom', '', 'HTML: tag/category below grid, before pagination');

UPDATE settings SET value = (SELECT value FROM settings AS o WHERE o.key = 'ad_sidebar') WHERE key = 'ad_home_sidebar' AND EXISTS (SELECT 1 FROM settings WHERE key = 'ad_sidebar');
UPDATE settings SET value = (SELECT value FROM settings AS o WHERE o.key = 'ad_sidebar') WHERE key = 'ad_listing_sidebar' AND EXISTS (SELECT 1 FROM settings WHERE key = 'ad_sidebar');
UPDATE settings SET value = (SELECT value FROM settings AS o WHERE o.key = 'ad_list_top') WHERE key = 'ad_home_list_top' AND EXISTS (SELECT 1 FROM settings WHERE key = 'ad_list_top');
UPDATE settings SET value = (SELECT value FROM settings AS o WHERE o.key = 'ad_list_top') WHERE key = 'ad_listing_list_top' AND EXISTS (SELECT 1 FROM settings WHERE key = 'ad_list_top');
UPDATE settings SET value = (SELECT value FROM settings AS o WHERE o.key = 'ad_list_bottom') WHERE key = 'ad_home_list_bottom' AND EXISTS (SELECT 1 FROM settings WHERE key = 'ad_list_bottom');
UPDATE settings SET value = (SELECT value FROM settings AS o WHERE o.key = 'ad_list_bottom') WHERE key = 'ad_listing_list_bottom' AND EXISTS (SELECT 1 FROM settings WHERE key = 'ad_list_bottom');
