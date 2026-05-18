-- Seed : Publishers de référence Japan-Alliance
-- TricorderKit v0.9 — 2026-05-18
-- Sources : sites officiels, Wikipedia JP (✅ Confirmé)

INSERT INTO publishers (name_ja, name_en, name_fr, slug, website_url, founded_year, country, reliability, source_url, source_date)
VALUES
  ('集英社',          'Shueisha',    'Shueisha',     'shueisha',     'https://www.shueisha.co.jp', 1926, 'JP', 'confirmed', 'https://www.shueisha.co.jp/company/', '2026-01-01'),
  ('講談社',          'Kodansha',    'Kodansha',     'kodansha',     'https://www.kodansha.co.jp', 1909, 'JP', 'confirmed', 'https://www.kodansha.co.jp/about/',   '2026-01-01'),
  ('小学館',          'Shogakukan',  'Shogakukan',   'shogakukan',   'https://www.shogakukan.co.jp', 1922, 'JP', 'confirmed', 'https://www.shogakukan.co.jp/company/', '2026-01-01'),
  ('角川書店',        'Kadokawa',    'Kadokawa',     'kadokawa',     'https://www.kadokawa.co.jp', 1945, 'JP', 'confirmed', 'https://www.kadokawa.co.jp/corporation/', '2026-01-01'),
  ('白泉社',          'Hakusensha',  'Hakusensha',   'hakusensha',   'https://www.hakusensha.co.jp', 1973, 'JP', 'confirmed', 'https://www.hakusensha.co.jp/', '2026-01-01'),
  ('少年画報社',      'Shonen Gahosha', 'Shonen Gahosha', 'shonen-gahosha', 'https://www.shonengahosha.co.jp', 1948, 'JP', 'confirmed', 'https://www.shonengahosha.co.jp/', '2026-01-01'),
  ('スクウェア・エニックス', 'Square Enix', 'Square Enix', 'square-enix', 'https://www.square-enix.co.jp', 2003, 'JP', 'confirmed', 'https://www.square-enix.co.jp/ir/', '2026-01-01'),
  ('双葉社',          'Futabasha',   'Futabasha',    'futabasha',    'https://www.futabasha.co.jp', 1948, 'JP', 'confirmed', 'https://www.futabasha.co.jp/company/', '2026-01-01'),
  ('芳文社',          'Houbunsha',   'Houbunsha',    'houbunsha',    'https://www.houbunsha.co.jp', 1948, 'JP', 'confirmed', 'https://www.houbunsha.co.jp/', '2026-01-01'),
  ('秋田書店',        'Akita Shoten', 'Akita Shoten', 'akita-shoten', 'https://www.akitashoten.co.jp', 1948, 'JP', 'confirmed', 'https://www.akitashoten.co.jp/', '2026-01-01')
ON CONFLICT (slug) DO NOTHING;
