-- Seed : Studios d'animation de référence Japan-Alliance
-- TricorderKit v0.9 — 2026-05-22
-- Sources : sites officiels, Wikipedia JP (✅ Confirmé)

INSERT INTO studios (name_ja, name_romanized, name_en, slug, founded_year, website_url, country, reliability, source_url, source_date)
VALUES
  ('東映アニメーション', 'Toei Animation',    'Toei Animation',    'toei-animation',    1948, 'https://www.toei-animation.co.jp', 'JP', 'confirmed', 'https://www.toei-animation.co.jp/company/', '2026-01-01'),
  ('MAPPA',             'MAPPA',              'MAPPA',              'mappa',             2011, 'https://www.mappa.co.jp',          'JP', 'confirmed', 'https://www.mappa.co.jp/company/',          '2026-01-01'),
  ('ufotable',          'ufotable',           'ufotable',           'ufotable',          2000, 'https://www.ufotable.com',         'JP', 'confirmed', 'https://www.ufotable.com/',                 '2026-01-01'),
  ('マッドハウス',      'Madhouse',           'Madhouse',           'madhouse',          1972, 'https://www.madhouse.co.jp',       'JP', 'confirmed', 'https://www.madhouse.co.jp/company/',       '2026-01-01'),
  ('WIT STUDIO',        'Wit Studio',         'Wit Studio',         'wit-studio',        2012, 'https://www.witstudio.co.jp',      'JP', 'confirmed', 'https://www.witstudio.co.jp/',              '2026-01-01'),
  ('CloverWorks',       'CloverWorks',        'CloverWorks',        'cloverworks',       2018, 'https://cloverworks.co.jp',        'JP', 'confirmed', 'https://cloverworks.co.jp/',                '2026-01-01'),
  ('京都アニメーション','Kyoto Animation',    'Kyoto Animation',   'kyoto-animation',   1981, 'https://www.kyotoanimation.co.jp', 'JP', 'confirmed', 'https://www.kyotoanimation.co.jp/company/', '2026-01-01'),
  ('Production I.G',    'Production I.G',     'Production I.G',     'production-ig',     1987, 'https://www.production-ig.co.jp',  'JP', 'confirmed', 'https://www.production-ig.co.jp/company/',  '2026-01-01'),
  ('A-1 Pictures',      'A-1 Pictures',       'A-1 Pictures',       'a1-pictures',       2005, 'https://a1p.jp',                   'JP', 'confirmed', 'https://a1p.jp/company/',                   '2026-01-01'),
  ('スタジオ地図',      'Studio Chizu',       'Studio Chizu',       'studio-chizu',      2011, 'https://www.studio-chizu.jp',      'JP', 'confirmed', 'https://www.studio-chizu.jp/',              '2026-01-01')
ON CONFLICT (slug) DO NOTHING;
