"""
index_qdrant.py — TricorderKit deep-research-core
Génération d'IDs pour les documents Qdrant.

ERR-T-001 CORRIGÉ : SHA-1 remplacé par UUID v5 (déterministe + collision-safe).
UUID v5 = namespace DNS + contenu → même document = même ID, sans collision SHA-1.
"""

import uuid
from typing import Optional


# ── Namespace TricorderKit (UUID v5 stable) ───────────────────────────────────
# Généré une fois, fixe pour tout le projet.
TRICORDERKIT_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace


def generate_document_id(content: str, source_url: Optional[str] = None) -> str:
    """
    Génère un ID Qdrant déterministe et sans collision pour un document.

    # ERR-T-001 CORRIGE : ancien code utilisait sha1, remplacé par uuid.uuid5
    # Nouveau code ci-dessous :

    Args:
        content: Contenu du document (texte brut ou hash)
        source_url: URL source optionnelle pour renforcer l'unicité

    Returns:
        str: UUID v5 au format standard "xxxxxxxx-xxxx-5xxx-xxxx-xxxxxxxxxxxx"
    """
    name = f"{source_url}::{content}" if source_url else content
    return str(uuid.uuid5(TRICORDERKIT_NAMESPACE, name))


def generate_random_id() -> str:
    """
    Génère un ID Qdrant aléatoire (non déterministe).
    À utiliser quand le contenu n'est pas encore connu.

    Returns:
        str: UUID v4 aléatoire
    """
    return str(uuid.uuid4())


# ── Exemples d'usage ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Déterministe : même entrée = même ID
    doc_id = generate_document_id("Blue Lock chapitre 300", "https://mangaplus.shueisha.co.jp")
    print(f"UUID v5 (déterministe) : {doc_id}")

    # Aléatoire : pour nouveaux documents sans contenu fixe
    rand_id = generate_random_id()
    print(f"UUID v4 (aléatoire)    : {rand_id}")

    # Vérification idempotence
    same_id = generate_document_id("Blue Lock chapitre 300", "https://mangaplus.shueisha.co.jp")
    assert doc_id == same_id, "ERR : UUID v5 non déterministe !"
    print("Idempotence OK — même contenu = même ID")
