# DEC-049 — Gate docs-sync étendu au ROADMAP (cohérence vitrine indispensable)

> Statut : Adoptée — 2026-06-12
> Auteur : GeekFamilyCorp (assisté Claude)
> Lié : DEC-028 (gate docs-sync initial / R39), DEC-026 (gate frontière publique / R37), DEC-016 (routage dépôts)
> Règle préventive associée : **R46**
>
> NB numérotation : DEC-047 = *project_scope générique learning-engine* et DEC-048 = *plugin document-ingestion (MarkItDown)* étaient déjà attribués (travail parallèle, 2026-06-11/12). Cette décision prend donc **DEC-049** (premier numéro libre) — une première rédaction l'avait étiquetée DEC-047 par erreur (collision corrigée).

---

## Contexte

Le push **v1.0.0 (2026-06-11)** a aligné `README.md`, `STATUS.md` et `CHANGELOG.md`
sur la version 1.0.0 / 634 tests / 12 plugins, mais a laissé **`ROADMAP.md` en
v0.9.5 / 544 tests / 10 plugins**. Une analyse externe du dépôt a relevé cette
incohérence (version, compte de tests, décompte plugins) entre la vitrine.

Le gate `scripts/check_docs_sync.py` (DEC-028) existait déjà et est câblé en
pre-push + CI, **mais il ne lisait jamais `ROADMAP.md`** : la dérive est donc
passée sans alerte. C'est un angle mort, pas un manque d'outil.

## Décision

Étendre `check_docs_sync.py` plutôt que créer un nouveau contrôle (règle
anti-recréation §6) :

1. **VERSION** — `ROADMAP.md` est désormais inspecté : entête `> Version : X`,
   pied `TricorderKit vX`, bloc `État actuel (vX)`. Toute valeur ≠ version
   canonique du CHANGELOG (`## [X.Y.Z]`) = échec.
2. **TESTS** — le compteur courant du bloc « État actuel » du ROADMAP
   (`Tests : NNN`) et les mentions `NNN tests collected` doivent égaler le badge
   README. Les compteurs **historiques** versionnés (tableaux de phases,
   « What's New », ex. « 503 tests PASS » de la phase 8) sont **volontairement
   ignorés** pour éviter les faux positifs.
3. **STRUCTURE** — le décompte de plugins se fait sur les sous-dossiers de
   `plugins/` **suivis par git** (`git ls-files`), pas sur le listing disque :
   un plugin WIP non commité ne fait pas partie du push et ne doit donc pas
   bloquer. Le verdict local (pre-push) reflète ainsi ce que verra la CI.

## Règle R46 (préventive, indispensable)

> **Avant tout push public, la vitrine doit être cohérente.** Version, nombre de
> tests et décompte de plugins doivent être IDENTIQUES dans `README.md`,
> `STATUS.md`, `ROADMAP.md` et concordants avec `CHANGELOG.md` (source canonique
> de version) et l'arborescence réelle `plugins/`. Le gate `make docs-sync`
> (ou `check_docs_sync.py`) est **bloquant** en pre-push et en CI. Tout ajout de
> plugin DOIT s'accompagner de sa déclaration dans le tableau de bord STATUS, du
> décompte README/ROADMAP et du Résumé STATUS. Un fichier de vitrine modifié
> sans réaligner les autres est un défaut de cohérence, pas une simple coquille.

Vérification : `python scripts/check_docs_sync.py` (rapide) ou
`python scripts/check_docs_sync.py --check-tests` (confronte aussi à la collecte
pytest réelle).

## Conséquences

- Le pre-push (`.githooks/pre-push`) et la CI (`.github/workflows/docs-sync.yml`)
  exécutent déjà ce script : aucune nouvelle plomberie nécessaire, la couverture
  ROADMAP est immédiate.
- Validé en conditions réelles : l'ajout du 13ᵉ plugin `document-ingestion`
  (DEC-048) sans mise à jour de la vitrine a été **bloqué par ce gate** ; la
  vitrine a été réalignée (13 plugins) avant le push.
- Suivi : `BOOT_SUMMARY.md` est auto-généré et reste en v0.9 ; il doit être
  régénéré via le skill `rapport` / `/tk:boot --update-summary` (hors périmètre
  de ce gate, non bloquant pour le public).

---

*DEC-049 — TricorderKit — 2026-06-12.*
