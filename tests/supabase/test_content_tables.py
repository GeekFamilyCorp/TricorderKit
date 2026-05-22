"""
test_content_tables.py — Tests contrat du schéma Supabase Japan-Alliance Phase 2
TricorderKit v0.9

Valide la migration 20260522000002_content_tables.sql sans connexion live :
  - Présence des tables dédiées (manga, anime, mangaka, studios, manga_mangaka)
  - Colonnes clés par table
  - Types ENUM déclarés (manga_demographics, manga_pub_status, anime_media_type,
                          anime_season_cour, mangaka_speciality)
  - Index de performance
  - Triggers updated_at
  - Politiques RLS (read_public + write_service)
  - Contraintes métier (CHECK, UNIQUE, FK)
  - Seed studios

Usage :
  pytest tests/supabase/test_content_tables.py -v
"""
from __future__ import annotations
import re
from pathlib import Path

MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent.parent
    / "supabase" / "migrations" / "20260522000002_content_tables.sql"
)

SEED_STUDIOS = (
    Path(__file__).resolve().parent.parent.parent
    / "supabase" / "seed" / "002_studios.sql"
)

SQL = MIGRATION_FILE.read_text(encoding="utf-8")


# ── Fixtures ───────────────────────────────────────────────────────────────────

REQUIRED_TABLES = [
    "studios",
    "mangaka",
    "manga",
    "manga_mangaka",
    "anime",
]

REQUIRED_ENUMS = [
    "manga_demographics",
    "manga_pub_status",
    "anime_media_type",
    "anime_season_cour",
    "mangaka_speciality",
]

REQUIRED_INDEXES = [
    "idx_studios_slug",
    "idx_mangaka_name_romanized",
    "idx_mangaka_active",
    "idx_manga_slug",
    "idx_manga_demographics",
    "idx_manga_pub_status",
    "idx_manga_genres",
    "idx_manga_mangadex",
    "idx_anime_slug",
    "idx_anime_media_type",
    "idx_anime_season",
    "idx_anime_studio",
    "idx_anime_genres",
]

REQUIRED_TRIGGERS = [
    "trg_studios_updated_at",
    "trg_mangaka_updated_at",
    "trg_manga_updated_at",
    "trg_anime_updated_at",
]

TABLE_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "studios": [
        "id", "name_ja", "slug", "founded_year", "country",
        "reliability", "created_at", "updated_at",
    ],
    "mangaka": [
        "id", "name_ja", "name_romanized", "pen_names",
        "debut_year", "debut_work", "speciality", "active",
        "reliability", "created_at", "updated_at",
    ],
    "manga": [
        "id", "title_ja", "slug", "demographics", "pub_status",
        "total_volumes", "total_chapters", "genres",
        "publisher_ja_id", "publisher_fr_id", "publisher_en_id",
        "mangadex_id", "anilist_id", "myanimelist_id",
        "avg_score", "reliability", "created_at", "updated_at",
    ],
    "anime": [
        "id", "title_ja", "slug", "media_type", "episode_count",
        "episode_duration", "season_year", "season_cour",
        "source_type", "source_manga_id", "studio_id",
        "anilist_id", "myanimelist_id",
        "avg_score", "reliability", "created_at", "updated_at",
    ],
}


# ── Tests : fichiers ───────────────────────────────────────────────────────────

def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"Migration introuvable : {MIGRATION_FILE}"


def test_migration_file_not_empty():
    assert len(SQL) > 1000, "Fichier migration trop court"


def test_seed_studios_exists():
    assert SEED_STUDIOS.exists(), f"Seed studios introuvable : {SEED_STUDIOS}"


# ── Tests : tables ────────────────────────────────────────────────────────────

def test_all_required_tables_present():
    for table in REQUIRED_TABLES:
        assert re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{table}\b",
            SQL, re.IGNORECASE,
        ), f"Table manquante : {table}"


def test_all_tables_have_uuid_pk():
    for table in [t for t in REQUIRED_TABLES if t != "manga_mangaka"]:
        assert re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{table}.*?uuid_generate_v4\(\)",
            SQL, re.IGNORECASE | re.DOTALL,
        ), f"{table}: PK UUID (uuid_generate_v4) manquante"


def test_all_content_tables_have_created_at():
    for table in [t for t in REQUIRED_TABLES if t != "manga_mangaka"]:
        assert re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{table}.*?created_at",
            SQL, re.IGNORECASE | re.DOTALL,
        ), f"{table}: colonne created_at manquante"


def test_all_content_tables_have_reliability():
    for table in [t for t in REQUIRED_TABLES if t not in ("manga_mangaka",)]:
        assert re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{table}.*?reliability",
            SQL, re.IGNORECASE | re.DOTALL,
        ), f"{table}: colonne reliability manquante"


# ── Tests : colonnes clés ─────────────────────────────────────────────────────

def test_table_required_columns():
    for table, cols in TABLE_REQUIRED_COLUMNS.items():
        match = re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{re.escape(table)}\s*\((.*?)\n\);",
            SQL, re.IGNORECASE | re.DOTALL,
        )
        assert match, f"Bloc table non trouvé : {table}"
        block = match.group(1)
        for col in cols:
            assert re.search(rf"\b{re.escape(col)}\b", block), \
                f"{table}: colonne '{col}' manquante"


# ── Tests : ENUMs ─────────────────────────────────────────────────────────────

def test_all_enums_declared():
    for enum in REQUIRED_ENUMS:
        assert re.search(
            rf"CREATE TYPE\s+{enum}\s+AS ENUM",
            SQL, re.IGNORECASE,
        ), f"ENUM manquant : {enum}"


def test_manga_demographics_values():
    match = re.search(r"CREATE TYPE manga_demographics AS ENUM\s*\((.*?)\);", SQL, re.DOTALL)
    assert match, "ENUM manga_demographics introuvable"
    values = match.group(1)
    for expected in ["shounen", "shoujo", "seinen", "josei", "kodomomuke"]:
        assert expected in values, f"manga_demographics: valeur '{expected}' manquante"


def test_manga_pub_status_values():
    match = re.search(r"CREATE TYPE manga_pub_status AS ENUM\s*\((.*?)\);", SQL, re.DOTALL)
    assert match, "ENUM manga_pub_status introuvable"
    values = match.group(1)
    for expected in ["serializing", "completed", "hiatus", "cancelled"]:
        assert expected in values, f"manga_pub_status: valeur '{expected}' manquante"


def test_anime_media_type_values():
    match = re.search(r"CREATE TYPE anime_media_type AS ENUM\s*\((.*?)\);", SQL, re.DOTALL)
    assert match, "ENUM anime_media_type introuvable"
    values = match.group(1)
    for expected in ["tv", "movie", "ova", "ona"]:
        assert expected in values, f"anime_media_type: valeur '{expected}' manquante"


def test_anime_season_cour_values():
    match = re.search(r"CREATE TYPE anime_season_cour AS ENUM\s*\((.*?)\);", SQL, re.DOTALL)
    assert match, "ENUM anime_season_cour introuvable"
    values = match.group(1)
    for expected in ["winter", "spring", "summer", "fall"]:
        assert expected in values, f"anime_season_cour: valeur '{expected}' manquante"


def test_mangaka_speciality_values():
    match = re.search(r"CREATE TYPE mangaka_speciality AS ENUM\s*\((.*?)\);", SQL, re.DOTALL)
    assert match, "ENUM mangaka_speciality introuvable"
    values = match.group(1)
    for expected in ["story_and_art", "story", "art", "light_novel"]:
        assert expected in values, f"mangaka_speciality: valeur '{expected}' manquante"


# ── Tests : index ──────────────────────────────────────────────────────────────

def test_all_required_indexes_present():
    for idx in REQUIRED_INDEXES:
        assert re.search(
            rf"CREATE INDEX\s+{idx}\b",
            SQL, re.IGNORECASE,
        ), f"Index manquant : {idx}"


def test_mangaka_active_partial_index():
    assert "WHERE active = TRUE" in SQL, \
        "Index partiel mangaka active=TRUE manquant"


def test_manga_mangadex_partial_index():
    assert "WHERE mangadex_id IS NOT NULL" in SQL, \
        "Index partiel manga mangadex_id IS NOT NULL manquant"


def test_anime_source_manga_partial_index():
    assert "WHERE source_manga_id IS NOT NULL" in SQL, \
        "Index partiel anime source_manga_id IS NOT NULL manquant"


def test_gin_indexes_for_array_columns():
    gin_indexes = re.findall(r"CREATE INDEX\s+\w+\s+ON\s+\w+\s+(USING GIN.*?);", SQL, re.IGNORECASE)
    assert len(gin_indexes) >= 3, f"Trop peu d'index GIN (array/trgm) : {len(gin_indexes)} trouvés"


# ── Tests : triggers ──────────────────────────────────────────────────────────

def test_all_updated_at_triggers_present():
    for trigger in REQUIRED_TRIGGERS:
        assert re.search(
            rf"CREATE TRIGGER\s+{trigger}\b",
            SQL, re.IGNORECASE,
        ), f"Trigger manquant : {trigger}"


def test_triggers_use_set_updated_at_function():
    trigger_count = len(re.findall(r"EXECUTE FUNCTION set_updated_at\(\)", SQL, re.IGNORECASE))
    assert trigger_count >= 4, \
        f"set_updated_at() utilisé dans {trigger_count} triggers, attendu ≥ 4"


# ── Tests : RLS ───────────────────────────────────────────────────────────────

def test_rls_enabled_on_all_tables():
    for table in REQUIRED_TABLES:
        assert re.search(
            rf"ALTER TABLE\s+{table}\s+ENABLE ROW LEVEL SECURITY",
            SQL, re.IGNORECASE,
        ), f"RLS non activé sur : {table}"


def test_read_public_policies_on_all_tables():
    for table in REQUIRED_TABLES:
        assert re.search(
            rf'CREATE POLICY.*"read_public".*ON\s+{table}',
            SQL, re.IGNORECASE,
        ), f"Politique read_public manquante sur : {table}"


def test_write_service_policies_on_all_tables():
    for table in REQUIRED_TABLES:
        assert re.search(
            rf'CREATE POLICY.*"write_service".*ON\s+{table}',
            SQL, re.IGNORECASE,
        ), f"Politique write_service manquante sur : {table}"


# ── Tests : contraintes métier ────────────────────────────────────────────────

def test_manga_date_constraint():
    assert "chk_manga_dates" in SQL, "Contrainte chk_manga_dates manquante"


def test_manga_score_constraint():
    assert "chk_manga_score" in SQL, "Contrainte chk_manga_score manquante"


def test_anime_score_constraint():
    assert "chk_anime_score" in SQL, "Contrainte chk_anime_score manquante"


def test_episode_duration_positive_check():
    assert "episode_duration > 0" in SQL, "CHECK episode_duration > 0 manquant"


def test_anime_source_type_check():
    assert "source_type IN" in SQL, "CHECK source_type IN (...) manquant dans anime"


# ── Tests : clés étrangères ───────────────────────────────────────────────────

def test_manga_references_publishers():
    assert re.search(
        r"publisher_ja_id\s+UUID\s+REFERENCES\s+publishers\(id\)",
        SQL, re.IGNORECASE,
    ), "FK manga.publisher_ja_id → publishers(id) manquante"


def test_anime_references_manga():
    assert re.search(
        r"source_manga_id\s+UUID\s+REFERENCES\s+manga\(id\)",
        SQL, re.IGNORECASE,
    ), "FK anime.source_manga_id → manga(id) manquante"


def test_anime_references_studios():
    assert re.search(
        r"studio_id\s+UUID\s+REFERENCES\s+studios\(id\)",
        SQL, re.IGNORECASE,
    ), "FK anime.studio_id → studios(id) manquante"


def test_manga_mangaka_cascade():
    block_match = re.search(
        r"CREATE TABLE IF NOT EXISTS\s+manga_mangaka\s*\((.*?)\n\);",
        SQL, re.DOTALL | re.IGNORECASE,
    )
    assert block_match, "Table manga_mangaka non trouvée"
    block = block_match.group(1)
    assert block.count("ON DELETE CASCADE") >= 2, \
        "manga_mangaka: CASCADE manquant sur manga_id ou mangaka_id"


# ── Tests : seed studios ──────────────────────────────────────────────────────

def test_seed_studios_has_key_studios():
    seed_sql = SEED_STUDIOS.read_text(encoding="utf-8")
    for slug in ["mappa", "ufotable", "kyoto-animation", "madhouse", "wit-studio"]:
        assert slug in seed_sql, f"Seed studios: slug '{slug}' manquant"


def test_seed_studios_has_japanese_names():
    seed_sql = SEED_STUDIOS.read_text(encoding="utf-8")
    assert "MAPPA" in seed_sql, "Seed studios: MAPPA manquant"
    assert "京都アニメーション" in seed_sql, "Seed studios: KyoAni (京都アニメーション) manquant"


def test_seed_studios_has_correct_format():
    seed_sql = SEED_STUDIOS.read_text(encoding="utf-8")
    assert "INSERT INTO studios" in seed_sql, "Seed studios: INSERT manquant"
    assert "ON CONFLICT (slug) DO NOTHING" in seed_sql, "Seed studios: ON CONFLICT manquant"
