"""
note_builder.py — Construction de notes Obsidian structurées
TricorderKit obsidian-agent-layer v0.1.0

Génère du contenu Markdown + frontmatter YAML conforme aux templates TricorderKit.
Supporte : project, paper, person, organization, concept, source, note générique.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# -- Dataclasses --------------------------------------------------------------

@dataclass
class NoteSpec:
    """Spécification d'une note à créer."""
    note_type: str              # project | paper | person | organization | concept | source | note
    title: str
    fields: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    body_extra: str = ""        # Contenu Markdown libre à ajouter après le template
    reliability: str = "🟡 Probable"  # Niveau de fiabilité par défaut


@dataclass
class BuiltNote:
    """Note construite prête à être écrite dans Obsidian."""
    path: str               # Chemin relatif dans le vault
    content: str            # Contenu complet (frontmatter + body)
    note_type: str
    title: str


# -- Helpers ------------------------------------------------------------------

def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _slugify(text: str) -> str:
    """Convertit un titre en slug de fichier."""
    slug = text.strip()
    slug = re.sub(r"[^\w\s\-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def _yaml_value(v: Any) -> str:
    """Sérialise une valeur Python en YAML inline."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        if not v:
            return "[]"
        items = "\n".join(f"  - {_yaml_value(item)}" for item in v)
        return f"\n{items}"
    s = str(v)
    if any(c in s for c in (':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|', '>', '!')):
        return f'"{s}"'
    return s


def _build_frontmatter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        val = _yaml_value(value)
        if val.startswith("\n"):
            lines.append(f"{key}:{val}")
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    return "\n".join(lines)


# -- Templates ----------------------------------------------------------------

def _list_md(items: Any, empty: str) -> str:
    if not items:
        return empty
    if isinstance(items, str):
        items = [items]
    return "\n".join(f"- {i}" for i in items)


def _table_md(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Champ | Valeur |", "|---|---|"]
    for label, value in rows:
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value) if value else "—"
        lines.append(f"| {label} | {value if value not in (None, '') else '—'} |")
    return "\n".join(lines)


def _entity_note(
    spec: NoteSpec,
    note_type: str,
    path: str,
    frontmatter: dict[str, Any],
    table_title: str,
    rows: list[tuple[str, Any]],
    sections: list[tuple[str, str]],
    extra_tags: list[str] | None = None,
) -> BuiltNote:
    """Assemble frontmatter + tableau + sections pour une fiche d'entité."""
    fm = _build_frontmatter({
        "type": note_type,
        **frontmatter,
        "tags": [note_type] + spec.tags + (extra_tags or []),
        "source": spec.fields.get("source", ""),
        "created": _today(),
        "updated": _today(),
        "fiabilite": spec.reliability,
    })
    parts = [f"\n# {spec.title}\n", f"## {table_title}\n", _table_md(rows) + "\n"]
    for heading, content in sections:
        parts.append(f"## {heading}\n\n{content}\n")
    parts.append(f"## Notes\n\n{spec.body_extra or '_Aucune note._'}\n")
    parts.append(
        f"## 📊 Fiabilité : {spec.reliability}\n\n"
        f"- Source : {spec.fields.get('source', 'non renseignée') or 'non renseignée'}\n"
        f"- Créé le : {_today()}\n"
    )
    return BuiltNote(path=path, content=fm + "\n".join(parts), note_type=note_type, title=spec.title)


def build_project_note(spec: NoteSpec) -> BuiltNote:
    """Fiche projet logiciel (ex. SQLite, Qdrant, Temporal)."""
    f = spec.fields
    status = f.get("status", "Actif")
    return _entity_note(
        spec, "project", f"Knowledge/Projects/{_slugify(spec.title)}.md",
        {
            "title": spec.title,
            "url": f.get("url", ""),
            "repository": f.get("repository", ""),
            "license": f.get("license", ""),
            "language": f.get("language", ""),
            "maintainer": f.get("maintainer", f.get("author", "")),
            "status": status,
            "topics": f.get("topics", []),
        },
        "Informations générales",
        [
            ("Dépôt", f.get("repository", f.get("url"))),
            ("Licence", f.get("license")),
            ("Langage", f.get("language")),
            ("Mainteneur", f.get("maintainer", f.get("author"))),
            ("Statut", status),
        ],
        [("Description", f.get("description", "_Description à compléter._"))],
        extra_tags=[f"status/{str(status).lower().replace(' ', '-')}"],
    )


def build_paper_note(spec: NoteSpec) -> BuiltNote:
    """Fiche article de recherche (ex. preprint arXiv)."""
    f = spec.fields
    authors = f.get("authors", f.get("author", []))
    return _entity_note(
        spec, "paper", f"Knowledge/Papers/{_slugify(spec.title)}.md",
        {
            "title": spec.title,
            "authors": authors,
            "year": f.get("year", ""),
            "venue": f.get("venue", ""),
            "arxiv_id": f.get("arxiv_id", ""),
            "doi": f.get("doi", ""),
            "url": f.get("url", ""),
        },
        "Référence",
        [
            ("Auteurs", authors),
            ("Année", f.get("year")),
            ("Publication", f.get("venue")),
            ("arXiv", f.get("arxiv_id")),
            ("DOI", f.get("doi")),
        ],
        [("Résumé", f.get("abstract", "_Résumé à compléter._"))],
    )


def build_person_note(spec: NoteSpec) -> BuiltNote:
    """Fiche personne (ex. Grace Hopper)."""
    f = spec.fields
    known_for = f.get("known_for", [])
    return _entity_note(
        spec, "person", f"Knowledge/People/{_slugify(spec.title)}.md",
        {
            "name": spec.title,
            "birth_date": f.get("birth_date", ""),
            "affiliation": f.get("affiliation", ""),
            "known_for": known_for,
        },
        "Informations",
        [
            ("Date de naissance", f.get("birth_date")),
            ("Affiliation", f.get("affiliation")),
        ],
        [("Contributions notables", _list_md(known_for, "_Aucune contribution renseignée._"))],
    )


def build_organization_note(spec: NoteSpec) -> BuiltNote:
    """Fiche organisation (ex. Apache Software Foundation, Mozilla)."""
    f = spec.fields
    projects = f.get("notable_projects", [])
    return _entity_note(
        spec, "organization", f"Knowledge/Organizations/{_slugify(spec.title)}.md",
        {
            "name": spec.title,
            "founded": f.get("founded", ""),
            "location": f.get("location", ""),
            "url": f.get("url", ""),
            "notable_projects": projects,
        },
        "Informations",
        [
            ("Fondée en", f.get("founded")),
            ("Localisation", f.get("location")),
            ("Site", f.get("url")),
        ],
        [("Projets notables", _list_md(projects, "_Aucun projet renseigné._"))],
    )


def build_concept_note(spec: NoteSpec) -> BuiltNote:
    """Fiche concept (ex. local-first software, vector databases)."""
    f = spec.fields
    related = f.get("related", [])
    return _entity_note(
        spec, "concept", f"Knowledge/Concepts/{_slugify(spec.title)}.md",
        {"title": spec.title, "related": related},
        "Informations",
        [("Domaine", f.get("field"))],
        [
            ("Définition", f.get("definition", f.get("description", "_Définition à compléter._"))),
            ("Liens", _list_md([f"[[{r}]]" for r in related], "_Aucun lien._")),
        ],
    )


def build_source_note(spec: NoteSpec) -> BuiltNote:
    """Fiche source d'information (API, flux, site)."""
    f = spec.fields
    return _entity_note(
        spec, "source", f"Knowledge/Sources/{_slugify(spec.title)}.md",
        {"title": spec.title, "url": f.get("url", ""), "kind": f.get("kind", "api")},
        "Informations",
        [("URL", f.get("url")), ("Nature", f.get("kind", "api"))],
        [("Usage", f.get("description", "_Usage à documenter._"))],
    )


def build_generic_note(spec: NoteSpec) -> BuiltNote:
    """Construit une note générique."""
    f = spec.fields
    slug = _slugify(spec.title)
    folder = f.get("folder", "10_INBOX")
    path = f"{folder}/{slug}.md"

    tags = ["note"] + spec.tags

    fm = _build_frontmatter({
        "type": "note",
        "title": spec.title,
        "tags": tags,
        "created": _today(),
        "updated": _today(),
    })

    body = f"\n# {spec.title}\n\n{spec.body_extra or f.get('content', '_Contenu à compléter._')}\n"

    return BuiltNote(path=path, content=fm + body, note_type="note", title=spec.title)


# -- Dispatcher ---------------------------------------------------------------

_BUILDERS = {
    "project": build_project_note,
    "paper": build_paper_note,
    "person": build_person_note,
    "organization": build_organization_note,
    "concept": build_concept_note,
    "source": build_source_note,
    "note": build_generic_note,
    "daily_log": build_generic_note,
    "memory": build_generic_note,
}


def build_note(spec: NoteSpec) -> BuiltNote:
    """
    Construit une note Obsidian selon son type.

    Args:
        spec: Spécification de la note

    Returns:
        BuiltNote prête à être écrite dans le vault
    """
    builder = _BUILDERS.get(spec.note_type.lower(), build_generic_note)
    return builder(spec)
