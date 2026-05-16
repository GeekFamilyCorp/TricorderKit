"""
note_builder.py — Construction de notes Obsidian structurées
TricorderKit obsidian-agent-layer v0.1.0

Génère du contenu Markdown + frontmatter YAML conforme aux templates TricorderKit.
Supporte : manga, anime, seiyuu, studio, mangaka, note générique.
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
    note_type: str              # manga | anime | seiyuu | studio | mangaka | note
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

def build_manga_note(spec: NoteSpec) -> BuiltNote:
    """Construit une fiche manga structurée."""
    f = spec.fields
    slug = _slugify(spec.title)
    path = f"Mangas/{spec.title}/{slug}.md"

    tags = ["manga"] + spec.tags
    if f.get("status"):
        tags.append(f"status/{f['status'].lower().replace(' ', '-')}")

    fm = _build_frontmatter({
        "type": "manga",
        "title": spec.title,
        "title_jp": f.get("title_jp", ""),
        "author": f.get("author", ""),
        "artist": f.get("artist", f.get("author", "")),
        "publisher_jp": f.get("publisher", ""),
        "publisher_fr": f.get("publisher_fr", ""),
        "magazine": f.get("magazine", ""),
        "volumes": f.get("volumes", ""),
        "status": f.get("status", "En cours"),
        "genre": f.get("genre", []),
        "tags": tags,
        "source": f.get("source", ""),
        "date_debut": f.get("date_debut", ""),
        "date_fin": f.get("date_fin", ""),
        "created": _today(),
        "updated": _today(),
        "fiabilite": spec.reliability,
    })

    body = f"""
# {spec.title}

## Informations générales

| Champ | Valeur |
|---|---|
| Titre JP | {f.get("title_jp", "—")} |
| Auteur | {f.get("author", "—")} |
| Éditeur JP | {f.get("publisher", "—")} |
| Magazine | {f.get("magazine", "—")} |
| Volumes | {f.get("volumes", "—")} |
| Statut | {f.get("status", "—")} |

## Synopsis

{f.get("synopsis", "_Synopsis à compléter._")}

## Notes

{spec.body_extra or "_Aucune note._"}

## 📊 Fiabilité : {spec.reliability}

- Source : {f.get("source", "non renseignée")}
- Créé le : {_today()}
"""

    return BuiltNote(path=path, content=fm + body, note_type="manga", title=spec.title)


def build_anime_note(spec: NoteSpec) -> BuiltNote:
    """Construit une fiche animé structurée."""
    f = spec.fields
    slug = _slugify(spec.title)
    path = f"Animes/{spec.title}/{slug}.md"

    tags = ["anime"] + spec.tags

    fm = _build_frontmatter({
        "type": "anime",
        "title": spec.title,
        "title_jp": f.get("title_jp", ""),
        "studio": f.get("studio", ""),
        "director": f.get("director", ""),
        "series_composition": f.get("series_composition", ""),
        "seasons": f.get("seasons", 1),
        "episodes": f.get("episodes", ""),
        "status": f.get("status", "En cours"),
        "genre": f.get("genre", []),
        "tags": tags,
        "source_manga": f.get("source_manga", ""),
        "diffusion": f.get("diffusion", ""),
        "created": _today(),
        "updated": _today(),
        "fiabilite": spec.reliability,
    })

    body = f"""
# {spec.title}

## Informations générales

| Champ | Valeur |
|---|---|
| Titre JP | {f.get("title_jp", "—")} |
| Studio | {f.get("studio", "—")} |
| Réalisateur | {f.get("director", "—")} |
| Saisons | {f.get("seasons", "—")} |
| Épisodes | {f.get("episodes", "—")} |
| Statut | {f.get("status", "—")} |
| Diffusion | {f.get("diffusion", "—")} |

## Synopsis

{f.get("synopsis", "_Synopsis à compléter._")}

## Notes

{spec.body_extra or "_Aucune note._"}

## 📊 Fiabilité : {spec.reliability}
"""

    return BuiltNote(path=path, content=fm + body, note_type="anime", title=spec.title)


def build_seiyuu_note(spec: NoteSpec) -> BuiltNote:
    """Construit une fiche seiyū structurée."""
    f = spec.fields
    name = spec.title
    slug = _slugify(name)
    path = f"Personnes/Seiyuu/{slug}.md"

    tags = ["seiyuu", "personne"] + spec.tags

    fm = _build_frontmatter({
        "type": "seiyuu",
        "name": name,
        "name_jp": f.get("name_jp", ""),
        "birth_date": f.get("birth_date", ""),
        "agency": f.get("agency", ""),
        "notable_roles": f.get("notable_roles", []),
        "tags": tags,
        "source": f.get("source", ""),
        "created": _today(),
        "updated": _today(),
        "fiabilite": spec.reliability,
    })

    roles = f.get("notable_roles", [])
    roles_md = "\n".join(f"- {r}" for r in roles) if roles else "_Aucun rôle renseigné._"

    body = f"""
# {name}

## Informations

| Champ | Valeur |
|---|---|
| Nom JP | {f.get("name_jp", "—")} |
| Date de naissance | {f.get("birth_date", "—")} |
| Agence | {f.get("agency", "—")} |

## Rôles notables

{roles_md}

## Notes

{spec.body_extra or "_Aucune note._"}

## 📊 Fiabilité : {spec.reliability}
"""

    return BuiltNote(path=path, content=fm + body, note_type="seiyuu", title=name)


def build_studio_note(spec: NoteSpec) -> BuiltNote:
    """Construit une fiche studio d'animation structurée."""
    f = spec.fields
    slug = _slugify(spec.title)
    path = f"Studios/{slug}.md"

    tags = ["studio", "animation"] + spec.tags

    fm = _build_frontmatter({
        "type": "studio",
        "name": spec.title,
        "name_jp": f.get("name_jp", ""),
        "founded": f.get("founded", ""),
        "location": f.get("location", "Tokyo"),
        "notable_works": f.get("notable_works", []),
        "type_studio": f.get("type_studio", "animation"),
        "tags": tags,
        "source": f.get("source", ""),
        "created": _today(),
        "updated": _today(),
        "fiabilite": spec.reliability,
    })

    works = f.get("notable_works", [])
    works_md = "\n".join(f"- {w}" for w in works) if works else "_Aucune œuvre renseignée._"

    body = f"""
# {spec.title}

## Informations

| Champ | Valeur |
|---|---|
| Nom JP | {f.get("name_jp", "—")} |
| Fondé en | {f.get("founded", "—")} |
| Localisation | {f.get("location", "—")} |

## Œuvres notables

{works_md}

## Notes

{spec.body_extra or "_Aucune note._"}

## 📊 Fiabilité : {spec.reliability}
"""

    return BuiltNote(path=path, content=fm + body, note_type="studio", title=spec.title)


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
    "manga": build_manga_note,
    "anime": build_anime_note,
    "seiyuu": build_seiyuu_note,
    "studio": build_studio_note,
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
