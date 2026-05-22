-- ============================================================
-- Migration : Japan-Alliance Phase 2 — Tables contenu dédiées
-- TricorderKit v0.9
-- Date      : 2026-05-22
-- Description : Tables dédiées pour les entités contenu du vault :
--               manga, anime, mangaka, studios
--               Complète le schéma générique de la migration 00001.
--               RLS, index, triggers et contraintes métier inclus.
-- Prérequis  : migration 20260518000001 (publishers, reliability_level ENUM)
-- ============================================================

-- ── Enums contenu ─────────────────────────────────────────────────────────────

CREATE TYPE manga_demographics AS ENUM (
  'shounen',        -- jeune garçon (Jump, Sunday, Magazine…)
  'shoujo',         -- jeune fille (Nakayoshi, Ribon…)
  'seinen',         -- homme adulte (Young Jump, Big Comic…)
  'josei',          -- femme adulte (Kiss, Chorus…)
  'kodomomuke',     -- enfant
  'unknown'
);

CREATE TYPE manga_pub_status AS ENUM (
  'serializing',    -- en cours de sérialisation
  'completed',      -- terminé
  'hiatus',         -- en pause
  'cancelled',      -- annulé
  'announced',      -- annoncé, pas encore publié
  'unknown'
);

CREATE TYPE anime_media_type AS ENUM (
  'tv',             -- série télévisée
  'movie',          -- film
  'ova',            -- Original Video Animation
  'ona',            -- Original Net Animation
  'special',        -- épisode spécial
  'music'           -- clip musical
);

CREATE TYPE anime_season_cour AS ENUM (
  'winter',         -- janvier–mars
  'spring',         -- avril–juin
  'summer',         -- juillet–septembre
  'fall'            -- octobre–décembre
);

CREATE TYPE mangaka_speciality AS ENUM (
  'story_and_art',  -- auteur complet
  'story',          -- scénariste
  'art',            -- dessinateur
  'light_novel',    -- romancier light novel
  'illustration',   -- illustrateur (couvertures, LN)
  'character_design',
  'mixed'           -- plusieurs spécialités
);

-- ── Table : studios ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS studios (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name_ja         TEXT NOT NULL,
  name_romanized  TEXT,
  name_en         TEXT,
  slug            TEXT UNIQUE NOT NULL,
  founded_year    SMALLINT CHECK (founded_year >= 1900 AND founded_year <= 2100),
  website_url     TEXT,
  twitter_handle  TEXT,
  country         CHAR(2) NOT NULL DEFAULT 'JP',
  notes           TEXT,
  reliability     reliability_level NOT NULL DEFAULT 'probable',
  source_url      TEXT,
  source_date     DATE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_studios_slug      ON studios(slug);
CREATE INDEX idx_studios_name_ja   ON studios(name_ja);
CREATE INDEX idx_studios_country   ON studios(country);

COMMENT ON TABLE studios IS 'Studios d''animation japonais et étrangers.';

-- ── Table : mangaka ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS mangaka (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  -- Identité
  name_ja         TEXT NOT NULL,
  name_romanized  TEXT,
  name_fr         TEXT,
  name_en         TEXT,
  pen_names       TEXT[],                         -- pseudonymes alternatifs
  -- Biographie
  birth_date      DATE,
  birth_place     TEXT,
  nationality     CHAR(2) NOT NULL DEFAULT 'JP',
  -- Carrière
  debut_year      SMALLINT CHECK (debut_year >= 1900 AND debut_year <= 2100),
  debut_work      TEXT,
  speciality      mangaka_speciality NOT NULL DEFAULT 'story_and_art',
  active          BOOLEAN NOT NULL DEFAULT TRUE,
  -- Contacts
  website_url     TEXT,
  twitter_handle  TEXT,
  -- Méta
  notes           TEXT,
  reliability     reliability_level NOT NULL DEFAULT 'probable',
  source_url      TEXT,
  source_date     DATE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mangaka_name_romanized ON mangaka(name_romanized);
CREATE INDEX idx_mangaka_name_ja        ON mangaka(name_ja);
CREATE INDEX idx_mangaka_speciality     ON mangaka(speciality);
CREATE INDEX idx_mangaka_active         ON mangaka(active) WHERE active = TRUE;
CREATE INDEX idx_mangaka_pen_names      ON mangaka USING GIN (pen_names);

COMMENT ON TABLE mangaka IS 'Mangakas, scénaristes, illustrateurs et romanciers LN.';

-- ── Table : manga ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS manga (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  -- Identité
  title_ja          TEXT NOT NULL,
  title_romanized   TEXT,
  title_fr          TEXT,
  title_en          TEXT,
  slug              TEXT UNIQUE NOT NULL,
  -- Publication
  magazine          TEXT,
  demographics      manga_demographics NOT NULL DEFAULT 'unknown',
  pub_status        manga_pub_status NOT NULL DEFAULT 'unknown',
  start_date        DATE,
  end_date          DATE,
  -- Contenu
  total_volumes     SMALLINT CHECK (total_volumes >= 0),
  total_chapters    SMALLINT CHECK (total_chapters >= 0),
  genres            TEXT[],
  themes            TEXT[],
  age_rating        TEXT,
  avg_score         NUMERIC(4,2) CHECK (avg_score >= 0 AND avg_score <= 100),
  cover_url         TEXT,
  synopsis_fr       TEXT,
  synopsis_en       TEXT,
  -- Éditeurs par marché (FK vers publishers)
  publisher_ja_id   UUID REFERENCES publishers(id) ON DELETE SET NULL,
  publisher_fr_id   UUID REFERENCES publishers(id) ON DELETE SET NULL,
  publisher_en_id   UUID REFERENCES publishers(id) ON DELETE SET NULL,
  -- Identifiants externes
  mangadex_id       TEXT UNIQUE,
  anilist_id        INTEGER UNIQUE,
  myanimelist_id    INTEGER UNIQUE,
  -- Méta
  notes             TEXT,
  reliability       reliability_level NOT NULL DEFAULT 'probable',
  source_url        TEXT,
  source_date       DATE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Contraintes métier
  CONSTRAINT chk_manga_dates CHECK (end_date IS NULL OR end_date >= start_date),
  CONSTRAINT chk_manga_score CHECK (avg_score IS NULL OR (avg_score >= 0 AND avg_score <= 100))
);

CREATE INDEX idx_manga_slug              ON manga(slug);
CREATE INDEX idx_manga_demographics      ON manga(demographics);
CREATE INDEX idx_manga_pub_status        ON manga(pub_status);
CREATE INDEX idx_manga_title_ja          ON manga(title_ja);
CREATE INDEX idx_manga_title_romanized   ON manga(title_romanized);
CREATE INDEX idx_manga_publisher_ja      ON manga(publisher_ja_id);
CREATE INDEX idx_manga_publisher_fr      ON manga(publisher_fr_id);
CREATE INDEX idx_manga_mangadex          ON manga(mangadex_id) WHERE mangadex_id IS NOT NULL;
CREATE INDEX idx_manga_anilist           ON manga(anilist_id) WHERE anilist_id IS NOT NULL;
CREATE INDEX idx_manga_genres            ON manga USING GIN (genres);
CREATE INDEX idx_manga_themes            ON manga USING GIN (themes);

COMMENT ON TABLE manga IS 'Mangas par titre, avec données éditoriales et identifiants externes.';

-- ── Table : manga_mangaka (M:N) ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS manga_mangaka (
  manga_id    UUID NOT NULL REFERENCES manga(id)   ON DELETE CASCADE,
  mangaka_id  UUID NOT NULL REFERENCES mangaka(id) ON DELETE CASCADE,
  role        TEXT NOT NULL DEFAULT 'story_and_art',
  -- role : story | art | story_and_art | character_design | color | assistant
  PRIMARY KEY (manga_id, mangaka_id, role)
);

CREATE INDEX idx_manga_mangaka_mangaka ON manga_mangaka(mangaka_id);

COMMENT ON TABLE manga_mangaka IS 'Association manga ↔ mangaka avec rôle (story, art, story_and_art…).';

-- ── Table : anime ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS anime (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  -- Identité
  title_ja            TEXT NOT NULL,
  title_romanized     TEXT,
  title_fr            TEXT,
  title_en            TEXT,
  slug                TEXT UNIQUE NOT NULL,
  -- Type et diffusion
  media_type          anime_media_type NOT NULL DEFAULT 'tv',
  episode_count       SMALLINT CHECK (episode_count >= 0),
  episode_duration    SMALLINT CHECK (episode_duration > 0),  -- en minutes
  season_year         SMALLINT CHECK (season_year >= 1960 AND season_year <= 2100),
  season_cour         anime_season_cour,
  -- Source d'adaptation
  source_type         TEXT CHECK (source_type IN ('manga', 'light_novel', 'original', 'game', 'other')),
  source_manga_id     UUID REFERENCES manga(id) ON DELETE SET NULL,
  -- Studio
  studio_id           UUID REFERENCES studios(id) ON DELETE SET NULL,
  -- Streaming
  crunchyroll_url     TEXT,
  wakanim_url         TEXT,
  -- Identifiants
  anilist_id          INTEGER UNIQUE,
  myanimelist_id      INTEGER UNIQUE,
  -- Contenu
  genres              TEXT[],
  themes              TEXT[],
  avg_score           NUMERIC(4,2) CHECK (avg_score >= 0 AND avg_score <= 100),
  cover_url           TEXT,
  trailer_url         TEXT,
  synopsis_fr         TEXT,
  synopsis_en         TEXT,
  -- Méta
  notes               TEXT,
  reliability         reliability_level NOT NULL DEFAULT 'probable',
  source_url          TEXT,
  source_date         DATE,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_anime_score CHECK (avg_score IS NULL OR (avg_score >= 0 AND avg_score <= 100))
);

CREATE INDEX idx_anime_slug              ON anime(slug);
CREATE INDEX idx_anime_media_type        ON anime(media_type);
CREATE INDEX idx_anime_season            ON anime(season_year, season_cour);
CREATE INDEX idx_anime_studio            ON anime(studio_id);
CREATE INDEX idx_anime_source_manga      ON anime(source_manga_id) WHERE source_manga_id IS NOT NULL;
CREATE INDEX idx_anime_anilist           ON anime(anilist_id) WHERE anilist_id IS NOT NULL;
CREATE INDEX idx_anime_title_ja          ON anime(title_ja);
CREATE INDEX idx_anime_genres            ON anime USING GIN (genres);

COMMENT ON TABLE anime IS 'Animés avec métadonnées de diffusion, studio et liens vers l''œuvre source.';

-- ── Trigger : updated_at automatique ─────────────────────────────────────────
-- (set_updated_at() définie dans migration 00001)

CREATE TRIGGER trg_studios_updated_at
  BEFORE UPDATE ON studios
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_mangaka_updated_at
  BEFORE UPDATE ON mangaka
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_manga_updated_at
  BEFORE UPDATE ON manga
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_anime_updated_at
  BEFORE UPDATE ON anime
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── Row-Level Security (RLS) ──────────────────────────────────────────────────

ALTER TABLE studios        ENABLE ROW LEVEL SECURITY;
ALTER TABLE mangaka        ENABLE ROW LEVEL SECURITY;
ALTER TABLE manga          ENABLE ROW LEVEL SECURITY;
ALTER TABLE manga_mangaka  ENABLE ROW LEVEL SECURITY;
ALTER TABLE anime          ENABLE ROW LEVEL SECURITY;

-- Lecture publique (données culturelles ouvertes)
CREATE POLICY "read_public" ON studios       FOR SELECT USING (TRUE);
CREATE POLICY "read_public" ON mangaka       FOR SELECT USING (TRUE);
CREATE POLICY "read_public" ON manga         FOR SELECT USING (TRUE);
CREATE POLICY "read_public" ON manga_mangaka FOR SELECT USING (TRUE);
CREATE POLICY "read_public" ON anime         FOR SELECT USING (TRUE);

-- Écriture : service_role uniquement (agents TricorderKit)
CREATE POLICY "write_service" ON studios       FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON mangaka       FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON manga         FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON manga_mangaka FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON anime         FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

-- ── Commentaire global ────────────────────────────────────────────────────────
COMMENT ON SCHEMA public IS 'Japan-Alliance MangaTracker — TricorderKit v0.9 (Phase 1 + 2)';
