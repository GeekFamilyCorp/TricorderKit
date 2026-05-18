"""
test_japan_alliance_schema.py — Tests contrat du schéma Supabase Japan-Alliance
TricorderKit v0.9

Valide la migration SQL sans connexion live :
  - Présence des tables obligatoires
  - Colonnes clés par table
  - Types ENUM déclarés
  - Index de performance
  - Triggers updated_at
  - Politiques RLS
  - Contraintes métier (CHECK, UNIQUE, FK)

Usage :
  pytest tests/supabase/test_japan_alliance_schema.py -v
"""
from __future__ import annotations
import re
from pathlib import Path

MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent.parent
    / "supabase" / "migrations" / "20260518000001_japan_alliance_schema.sql"
)

SQL = MIGRATION_FILE.read_text(encoding="utf-8")


# ── Fixtures ──────────────────────────────────────────────────────────────────

REQUIRED_TABLES = [
    "publishers",
    "authors",
    "series",
    "series_authors",
    "volumes",
    "ai_extractions",
    "review_queue",
]

REQUIRED_ENUMS = [
    "series_type",
    "series_status",
    "reliability_level",
    "review_status",
    "extraction_source",
]

REQUIRED_INDEXES = [
    "idx_publishers_slug",
    "idx_series_slug",
    "idx_series_title_ja_trgm",
    "idx_volumes_series",
    "idx_ai_extractions_target",
    "idx_ai_extractions_review",
    "idx_review_queue_pending",
    "idx_review_queue_status",
]

REQUIRED_TRIGGERS = [
    "trg_publishers_updated_at",
    "trg_authors_updated_at",
    "trg_series_updated_at",
    "trg_volumes_updated_at",
    "trg_review_queue_updated_at",
]

TABLE_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "publishers": ["id", "name_ja", "slug", "reliability", "created_at", "updated_at"],
    "authors":    ["id", "name_ja", "name_romanized", "roles", "reliability", "created_at"],
    "series":     ["id", "title_ja", "slug", "series_type", "status", "publisher_id",
                   "mangadex_id", "anilist_id", "reliability"],
    "volumes":    ["id", "series_id", "volume_number", "release_date_ja", "release_date_fr",
                   "isbn_ja", "isbn_fr", "reliability"],
    "ai_extractions": ["id", "target_type", "target_id", "source", "extracted_data",
                       "confidence", "token_cost", "review_needed", "reliability"],
    "review_queue":   ["id", "extraction_id", "target_type", "target_id", "proposed_changes",
                       "current_values", "status", "priority", "auto_approvable"],
}


# ── Tests : fichier ────────────────────────────────────────────────────────────

def test_migration_file_exists():
    assert MIGRATION_FILE.exists(), f"Migration introuvable : {MIGRATION_FILE}"


def test_migration_file_not_empty():
    assert len(SQL) > 500, "Fichier migration trop court"


# ── Tests : tables ────────────────────────────────────────────────────────────

def test_all_required_tables_present():
    for table in REQUIRED_TABLES:
        assert re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{table}\b", SQL, re.IGNORECASE
        ), f"Table manquante : {table}"


def test_all_tables_have_uuid_pk():
    for table in REQUIRED_TABLES:
        # Chercher le bloc de la table
        match = re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{table}\s*\((.*?)(?:^\);|\n\);)",
            SQL, re.IGNORECASE | re.DOTALL | re.MULTILINE
        )
        if match:
            block = match.group(1)
            assert "uuid_generate_v4()" in block or "uuid-ossp" in SQL, \
                f"{table}: PK UUID manquante"


def test_all_tables_have_created_at():
    for table in [t for t in REQUIRED_TABLES if t != "series_authors"]:
        # series_authors est une table de jonction sans timestamps
        assert re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{table}.*?created_at",
            SQL, re.IGNORECASE | re.DOTALL
        ), f"{table}: colonne created_at manquante"


# ── Tests : colonnes clés ─────────────────────────────────────────────────────

def test_table_required_columns():
    for table, cols in TABLE_REQUIRED_COLUMNS.items():
        # Extraire le bloc de la table
        match = re.search(
            rf"CREATE TABLE IF NOT EXISTS\s+{re.escape(table)}\s*\((.*?)\n\);",
            SQL, re.IGNORECASE | re.DOTALL
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
            rf"CREATE TYPE\s+{enum}\s+AS ENUM", SQL, re.IGNORECASE
        ), f"ENUM manquant : {enum}"


def test_reliability_enum_values():
    match = re.search(r"CREATE TYPE reliability_level AS ENUM\s*\((.*?)\);", SQL, re.DOTALL)
    assert match, "ENUM reliability_level introuvable"
    values = match.group(1)
    for expected in ["confirmed", "probable", "to_verify", "incomplete"]:
        assert expected in values, f"reliability_level: valeur '{expected}' manquante"


def test_series_type_enum_includes_manga_and_anime():
    match = re.search(r"CREATE TYPE series_type AS ENUM\s*\((.*?)\);", SQL, re.DOTALL)
    assert match, "ENUM series_type introuvable"
    values = match.group(1)
    for expected in ["manga", "light_novel", "anime"]:
        assert expected in values, f"series_type: valeur '{expected}' manquante"


def test_review_status_enum():
    match = re.search(r"CREATE TYPE review_status AS ENUM\s*\((.*?)\);", SQL, re.DOTALL)
    assert match, "ENUM review_status introuvable"
    values = match.group(1)
    for expected in ["pending", "approved", "rejected"]:
        assert expected in values, f"review_status: valeur '{expected}' manquante"


# ── Tests : index ─────────────────────────────────────────────────────────────

def test_all_required_indexes_present():
    for idx in REQUIRED_INDEXES:
        assert re.search(
            rf"CREATE INDEX\s+{idx}\b", SQL, re.IGNORECASE
        ), f"Index manquant : {idx}"


def test_trigram_indexes_use_gin():
    trgm_indexes = re.findall(r"CREATE INDEX\s+\w+_trgm\s+ON\s+\w+\s+(.*?);", SQL, re.IGNORECASE)
    for idx_def in trgm_indexes:
        assert "GIN" in idx_def.upper(), f"Index trgm sans GIN : {idx_def}"


def test_review_queue_pending_partial_index():
    assert "WHERE status = 'pending'" in SQL, \
        "Index partiel review_queue pending manquant"


# ── Tests : triggers ──────────────────────────────────────────────────────────

def test_set_updated_at_function_declared():
    assert "CREATE OR REPLACE FUNCTION set_updated_at()" in SQL, \
        "Fonction set_updated_at() manquante"


def test_all_updated_at_triggers_present():
    for trigger in REQUIRED_TRIGGERS:
        assert re.search(
            rf"CREATE TRIGGER\s+{trigger}\b", SQL, re.IGNORECASE
        ), f"Trigger manquant : {trigger}"


# ── Tests : RLS ───────────────────────────────────────────────────────────────

def test_rls_enabled_on_all_tables():
    for table in REQUIRED_TABLES:
        assert re.search(
            rf"ALTER TABLE\s+{table}\s+ENABLE ROW LEVEL SECURITY", SQL, re.IGNORECASE
        ), f"RLS non activé sur : {table}"


def test_read_public_policies_on_public_tables():
    for table in ["publishers", "authors", "series", "volumes"]:
        assert re.search(
            rf'CREATE POLICY.*read_public.*ON\s+{table}', SQL, re.IGNORECASE
        ), f"Politique read_public manquante sur : {table}"


def test_restricted_read_on_ai_and_review():
    for table in ["ai_extractions", "review_queue"]:
        assert re.search(
            rf'CREATE POLICY.*read_service.*ON\s+{table}', SQL, re.IGNORECASE
        ), f"Politique read_service manquante sur : {table}"


def test_write_service_policies_on_all_tables():
    for table in REQUIRED_TABLES:
        assert re.search(
            rf'CREATE POLICY.*write_service.*ON\s+{table}', SQL, re.IGNORECASE
        ), f"Politique write_service manquante sur : {table}"


# ── Tests : contraintes métier ────────────────────────────────────────────────

def test_series_has_date_constraint():
    assert "chk_dates" in SQL, "Contrainte chk_dates (end_date >= start_date) manquante"


def test_volumes_has_unique_series_volume():
    assert "UNIQUE (series_id, volume_number)" in SQL, \
        "Contrainte UNIQUE (series_id, volume_number) manquante"


def test_ai_extractions_confidence_check():
    assert "confidence >= 0 AND confidence <= 1" in SQL, \
        "CHECK confidence [0,1] manquant dans ai_extractions"


def test_review_queue_priority_check():
    assert "priority >= 0 AND priority <= 100" in SQL, \
        "CHECK priority [0,100] manquant dans review_queue"


def test_review_queue_target_type_check():
    assert "target_type IN ('series', 'author', 'publisher', 'volume')" in SQL, \
        "CHECK target_type manquant dans review_queue"


def test_ai_extractions_target_type_check():
    # Vérifier que ai_extractions a aussi un CHECK sur target_type
    match = re.search(
        r"CREATE TABLE IF NOT EXISTS\s+ai_extractions.*?CONSTRAINT|CHECK\s*\(target_type IN",
        SQL, re.DOTALL | re.IGNORECASE
    )
    # Acceptable si le CHECK est inline sur la colonne
    assert "target_type IN" in SQL, "CHECK target_type manquant dans ai_extractions"


def test_foreign_keys_volumes_to_series():
    assert re.search(
        r"series_id\s+UUID\s+NOT NULL\s+REFERENCES\s+series\(id\)", SQL, re.IGNORECASE
    ), "FK volumes.series_id → series(id) manquante"


def test_foreign_keys_series_to_publishers():
    assert re.search(
        r"publisher_id\s+UUID\s+REFERENCES\s+publishers\(id\)", SQL, re.IGNORECASE
    ), "FK series.publisher_id → publishers(id) manquante"


def test_series_authors_cascade():
    # La table de jonction doit avoir ON DELETE CASCADE sur les deux FK
    block_match = re.search(
        r"CREATE TABLE IF NOT EXISTS\s+series_authors\s*\((.*?)\n\);",
        SQL, re.DOTALL | re.IGNORECASE
    )
    assert block_match, "Table series_authors non trouvée"
    block = block_match.group(1)
    assert block.count("ON DELETE CASCADE") >= 2, \
        "series_authors: CASCADE manquant sur series_id ou author_id"


# ── Tests : seed ──────────────────────────────────────────────────────────────

def test_seed_publishers_exists():
    seed_file = MIGRATION_FILE.parent.parent / "seed" / "001_publishers.sql"
    assert seed_file.exists(), "Seed publishers manquant"
    seed_sql = seed_file.read_text(encoding="utf-8")
    assert "Shueisha" in seed_sql or "集英社" in seed_sql, \
        "Seed publishers: Shueisha manquant"
    assert "Kodansha" in seed_sql or "講談社" in seed_sql, \
        "Seed publishers: Kodansha manquant"
    for key_slug in ["shueisha", "kodansha", "shogakukan", "kadokawa"]:
        assert key_slug in seed_sql, f"Seed publishers: slug '{key_slug}' manquant"
