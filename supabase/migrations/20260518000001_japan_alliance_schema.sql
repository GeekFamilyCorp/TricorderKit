-- ============================================================
-- Migration : Japan-Alliance Phase 1 — Schéma principal
-- TricorderKit v0.9
-- Date      : 2026-05-18
-- Description : Tables series, authors, publishers, volumes,
--               ai_extractions, review_queue
--               avec RLS, index et contraintes métier.
-- ============================================================

-- ── Extensions ────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- recherche textuelle floue

-- ── Enum types ────────────────────────────────────────────────────────────────

CREATE TYPE series_type AS ENUM (
  'manga', 'light_novel', 'anime', 'manhwa', 'manhua', 'novel', 'webtoon'
);

CREATE TYPE series_status AS ENUM (
  'ongoing', 'completed', 'hiatus', 'cancelled', 'announced', 'unknown'
);

CREATE TYPE reliability_level AS ENUM (
  'confirmed',   -- source officielle ou croisée validée
  'probable',    -- source secondaire fiable
  'to_verify',   -- annonce non officielle ou en attente
  'incomplete'   -- donnée manquante ou conflit non résolu
);

CREATE TYPE review_status AS ENUM (
  'pending', 'approved', 'rejected', 'needs_info'
);

CREATE TYPE extraction_source AS ENUM (
  'mangadex', 'anilist', 'jikan', 'bookwalker', 'cdjapan',
  'natalie', 'oricon', 'official_site', 'manual', 'unknown'
);

-- ── Table : publishers ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS publishers (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name_ja       TEXT NOT NULL,
  name_en       TEXT,
  name_fr       TEXT,
  slug          TEXT UNIQUE NOT NULL,
  website_url   TEXT,
  founded_year  SMALLINT CHECK (founded_year >= 1900 AND founded_year <= 2100),
  country       CHAR(2) DEFAULT 'JP',  -- ISO 3166-1 alpha-2
  notes         TEXT,
  reliability   reliability_level NOT NULL DEFAULT 'probable',
  source_url    TEXT,
  source_date   DATE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_publishers_slug ON publishers(slug);
CREATE INDEX idx_publishers_name_ja_trgm ON publishers USING GIN (name_ja gin_trgm_ops);

COMMENT ON TABLE publishers IS 'Maisons d''édition japonaises et étrangères.';

-- ── Table : authors ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS authors (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name_ja         TEXT NOT NULL,          -- kanji/kana
  name_romanized  TEXT,                   -- romaji
  name_fr         TEXT,
  name_en         TEXT,
  pen_names       TEXT[],                 -- pseudonymes alternatifs
  birth_date      DATE,
  birth_place     TEXT,
  nationality     CHAR(2) DEFAULT 'JP',
  roles           TEXT[] NOT NULL DEFAULT ARRAY['mangaka'],
  -- roles possibles : mangaka, writer, artist, colorist, letterer, editor
  website_url     TEXT,
  twitter_handle  TEXT,
  notes           TEXT,
  reliability     reliability_level NOT NULL DEFAULT 'probable',
  source_url      TEXT,
  source_date     DATE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_authors_name_ja_trgm ON authors USING GIN (name_ja gin_trgm_ops);
CREATE INDEX idx_authors_name_romanized ON authors(name_romanized);
CREATE INDEX idx_authors_roles ON authors USING GIN (roles);

COMMENT ON TABLE authors IS 'Auteurs, artistes, scénaristes de l''écosystème manga/LN/animé.';

-- ── Table : series ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS series (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title_ja           TEXT NOT NULL,
  title_romanized    TEXT,
  title_fr           TEXT,
  title_en           TEXT,
  slug               TEXT UNIQUE NOT NULL,
  series_type        series_type NOT NULL DEFAULT 'manga',
  status             series_status NOT NULL DEFAULT 'unknown',
  start_date         DATE,
  end_date           DATE,
  synopsis_fr        TEXT,
  synopsis_en        TEXT,
  genres             TEXT[],
  tags               TEXT[],
  age_rating         TEXT,                 -- G, PG, PG-13, R, R+, Rx
  cover_url          TEXT,
  -- Relations
  publisher_id       UUID REFERENCES publishers(id) ON DELETE SET NULL,
  magazine_id        UUID,                -- FK vers magazines (table future)
  -- Identifiants externes
  mangadex_id        TEXT UNIQUE,
  anilist_id         INTEGER UNIQUE,
  myanimelist_id     INTEGER UNIQUE,
  bookwalker_id      TEXT,
  -- Stats
  volumes_count      SMALLINT,
  chapters_count     SMALLINT,
  avg_score          NUMERIC(4,2) CHECK (avg_score >= 0 AND avg_score <= 100),
  -- Méta
  notes              TEXT,
  reliability        reliability_level NOT NULL DEFAULT 'probable',
  source_url         TEXT,
  source_date        DATE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Contraintes
  CONSTRAINT chk_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_series_slug ON series(slug);
CREATE INDEX idx_series_type ON series(series_type);
CREATE INDEX idx_series_status ON series(status);
CREATE INDEX idx_series_title_ja_trgm ON series USING GIN (title_ja gin_trgm_ops);
CREATE INDEX idx_series_title_romanized_trgm ON series USING GIN (COALESCE(title_romanized, '') gin_trgm_ops);
CREATE INDEX idx_series_genres ON series USING GIN (genres);
CREATE INDEX idx_series_tags ON series USING GIN (tags);
CREATE INDEX idx_series_publisher ON series(publisher_id);

COMMENT ON TABLE series IS 'Œuvres sérialisées : mangas, light novels, animés, webtoons.';

-- ── Table : series_authors (M:N) ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS series_authors (
  series_id  UUID NOT NULL REFERENCES series(id) ON DELETE CASCADE,
  author_id  UUID NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
  role       TEXT NOT NULL DEFAULT 'mangaka',
  PRIMARY KEY (series_id, author_id, role)
);

CREATE INDEX idx_series_authors_author ON series_authors(author_id);

COMMENT ON TABLE series_authors IS 'Association série ↔ auteur avec rôle (story, art, both…).';

-- ── Table : volumes ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS volumes (
  id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  series_id        UUID NOT NULL REFERENCES series(id) ON DELETE CASCADE,
  volume_number    SMALLINT NOT NULL CHECK (volume_number >= 0),
  title_ja         TEXT,
  title_fr         TEXT,
  title_en         TEXT,
  isbn_ja          TEXT,
  isbn_fr          TEXT,
  isbn_en          TEXT,
  release_date_ja  DATE,
  release_date_fr  DATE,
  release_date_en  DATE,
  pages            SMALLINT CHECK (pages > 0),
  cover_url        TEXT,
  -- Éditeurs par marché
  publisher_ja_id  UUID REFERENCES publishers(id) ON DELETE SET NULL,
  publisher_fr_id  UUID REFERENCES publishers(id) ON DELETE SET NULL,
  publisher_en_id  UUID REFERENCES publishers(id) ON DELETE SET NULL,
  -- Prix indicatifs (en centimes pour éviter les floats)
  price_ja_yen     INTEGER CHECK (price_ja_yen >= 0),
  price_fr_cent    INTEGER CHECK (price_fr_cent >= 0),
  notes            TEXT,
  reliability      reliability_level NOT NULL DEFAULT 'probable',
  source_url       TEXT,
  source_date      DATE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (series_id, volume_number)
);

CREATE INDEX idx_volumes_series ON volumes(series_id);
CREATE INDEX idx_volumes_release_ja ON volumes(release_date_ja DESC NULLS LAST);
CREATE INDEX idx_volumes_release_fr ON volumes(release_date_fr DESC NULLS LAST);

COMMENT ON TABLE volumes IS 'Tomes physiques/numériques par série, par marché.';

-- ── Table : ai_extractions ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ai_extractions (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  -- Cible de l'extraction
  target_type     TEXT NOT NULL CHECK (target_type IN ('series', 'author', 'publisher', 'volume')),
  target_id       UUID NOT NULL,
  -- Source de la donnée brute
  source          extraction_source NOT NULL DEFAULT 'unknown',
  source_url      TEXT,
  source_raw      JSONB,           -- payload brut de la source
  fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Résultat de l'extraction IA
  model_used      TEXT,            -- ex: claude-sonnet-4-6
  prompt_version  TEXT,
  extracted_data  JSONB NOT NULL,  -- données structurées extraites
  confidence      NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
  token_cost      INTEGER,         -- tokens consommés
  -- Statut
  reliability     reliability_level NOT NULL DEFAULT 'to_verify',
  review_needed   BOOLEAN NOT NULL DEFAULT TRUE,
  applied_at      TIMESTAMPTZ,     -- NULL = pas encore appliqué à la table cible
  applied_by      TEXT,            -- agent ou user qui a validé
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_extractions_target ON ai_extractions(target_type, target_id);
CREATE INDEX idx_ai_extractions_source ON ai_extractions(source);
CREATE INDEX idx_ai_extractions_review ON ai_extractions(review_needed) WHERE review_needed = TRUE;
CREATE INDEX idx_ai_extractions_fetched ON ai_extractions(fetched_at DESC);
CREATE INDEX idx_ai_extractions_data ON ai_extractions USING GIN (extracted_data);

COMMENT ON TABLE ai_extractions IS 'Extractions IA brutes en attente de validation. Pipeline : fetch → extract → review → apply.';

-- ── Table : review_queue ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS review_queue (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  -- Contexte
  extraction_id      UUID REFERENCES ai_extractions(id) ON DELETE CASCADE,
  target_type        TEXT NOT NULL CHECK (target_type IN ('series', 'author', 'publisher', 'volume')),
  target_id          UUID,          -- NULL si création d'une nouvelle entrée
  -- Données proposées
  proposed_changes   JSONB NOT NULL,
  current_values     JSONB,         -- snapshot de l'état actuel (pour diff)
  change_summary     TEXT,          -- résumé humain lisible des changements
  -- Priorité & statut
  priority           SMALLINT NOT NULL DEFAULT 50 CHECK (priority >= 0 AND priority <= 100),
  status             review_status NOT NULL DEFAULT 'pending',
  -- Résolution
  reviewed_by        TEXT,
  reviewed_at        TIMESTAMPTZ,
  rejection_reason   TEXT,
  -- Méta
  auto_approvable    BOOLEAN NOT NULL DEFAULT FALSE,
  -- TRUE si règle métier permet approbation auto (ex: ajout ISBN seul)
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_review_queue_status ON review_queue(status);
CREATE INDEX idx_review_queue_pending ON review_queue(priority DESC, created_at ASC)
  WHERE status = 'pending';
CREATE INDEX idx_review_queue_target ON review_queue(target_type, target_id);
CREATE INDEX idx_review_queue_extraction ON review_queue(extraction_id);

COMMENT ON TABLE review_queue IS 'File de validation humaine pour les extractions IA. priorité 0-100 (100 = urgent).';

-- ── Trigger : updated_at automatique ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_publishers_updated_at
  BEFORE UPDATE ON publishers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_authors_updated_at
  BEFORE UPDATE ON authors
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_series_updated_at
  BEFORE UPDATE ON series
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_volumes_updated_at
  BEFORE UPDATE ON volumes
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_review_queue_updated_at
  BEFORE UPDATE ON review_queue
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── Row-Level Security (RLS) ──────────────────────────────────────────────────
-- Activé sur toutes les tables. En production, remplacer par des politiques
-- basées sur auth.uid() et les rôles Supabase.

ALTER TABLE publishers      ENABLE ROW LEVEL SECURITY;
ALTER TABLE authors         ENABLE ROW LEVEL SECURITY;
ALTER TABLE series          ENABLE ROW LEVEL SECURITY;
ALTER TABLE series_authors  ENABLE ROW LEVEL SECURITY;
ALTER TABLE volumes         ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_extractions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_queue    ENABLE ROW LEVEL SECURITY;

-- Politique de lecture publique (données culturelles ouvertes)
-- En production : ajuster pour les rôles authenticated/service_role
CREATE POLICY "read_public" ON publishers      FOR SELECT USING (TRUE);
CREATE POLICY "read_public" ON authors         FOR SELECT USING (TRUE);
CREATE POLICY "read_public" ON series          FOR SELECT USING (TRUE);
CREATE POLICY "read_public" ON series_authors  FOR SELECT USING (TRUE);
CREATE POLICY "read_public" ON volumes         FOR SELECT USING (TRUE);

-- ai_extractions et review_queue : lecture restreinte (service_role ou authentifié)
CREATE POLICY "read_service" ON ai_extractions FOR SELECT
  USING (auth.role() IN ('service_role', 'authenticated'));
CREATE POLICY "read_service" ON review_queue   FOR SELECT
  USING (auth.role() IN ('service_role', 'authenticated'));

-- Écriture : service_role uniquement (agents TricorderKit)
CREATE POLICY "write_service" ON publishers      FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON authors         FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON series          FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON series_authors  FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON volumes         FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON ai_extractions  FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "write_service" ON review_queue    FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

-- ── Commentaire global ────────────────────────────────────────────────────────
COMMENT ON SCHEMA public IS 'Japan-Alliance MangaTracker — TricorderKit v0.9';
