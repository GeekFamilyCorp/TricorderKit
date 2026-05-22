# README_PRIVACY.md — Règles d'anonymisation

> À lire obligatoirement avant tout push public, partage de screenshot
> ou publication d'un snippet issu d'un projet lié.

---

## Principe fondamental

Un projet lié TricorderKit contient par nature des données privées :
noms de projets internes, chemins locaux, clés API, prompts métier propriétaires.
Ces données ne doivent **jamais** apparaître dans un repo public.

---

## Table de remplacement

| Donnée réelle | Remplacer par |
|---|---|
| Nom du projet privé | `sample-linked-project` |
| Chemin du vault | `/path/to/private/vault` |
| Chemin racine projet | `/path/to/your/project` |
| Nom d'utilisateur local | `<your-username>` |
| Clé API réelle | `your_*_api_key_here` |
| Nom d'organisation GitHub | `your-org` |
| Nom de repo privé | `your-repo` |
| Nom de domaine métier | `your-domain-here` |
| Prompt métier propriétaire | `[REDACTED — prompt propriétaire]` |
| Email professionnel | `user@example.com` |

---

## Checklist avant push public

### Fichiers de config
- [ ] Aucun chemin absolu personnel (`C:/Users/votre-nom/...`)
- [ ] Aucune clé API (même expirée — l'historique git est permanent)
- [ ] Aucun token GitHub, Supabase, Langfuse, etc.
- [ ] ID projet remplacé par `sample-linked-project`
- [ ] Vault path remplacé par `/path/to/private/vault`

### Code source
- [ ] Aucune constante hardcodée avec un nom de projet réel
- [ ] Aucun `print()` ou `log()` révélant des chemins personnels
- [ ] Les commentaires ne mentionnent pas de clients, projets ou équipes internes
- [ ] Les messages de commit ne contiennent pas de noms internes

### Tests
- [ ] Les fixtures n'utilisent pas de données réelles
- [ ] Les snapshots ne contiennent pas de chemins locaux
- [ ] Les mocks ne reproduisent pas la structure interne du projet privé

### Vault / Notes Obsidian
- [ ] Aucune note personnelle ou confidentielle
- [ ] Les templates ne contiennent pas de contenu propriétaire
- [ ] Les exemples sont fictifs ou issus de sources publiques

---

## Vérification automatique

```bash
# Scanner les secrets dans le repo avant push
python cli/tk.py doctor --format json | python -c "
import json, sys
data = json.load(sys.stdin)
sec = next(c for c in data['checks'] if 'secret' in c['label'].lower())
print('Secrets:', sec['status'], sec.get('detail', ''))
"

# Grep manuel sur les patterns courants
git grep -rn "C:/Users/" -- examples/
git grep -rn "/home/" -- examples/
git grep -rn "your-real-" -- examples/
```

---

## Règles complémentaires

### Clés API
- Ne jamais committer une vraie clé, même en test
- Si une clé est accidentellement committée : révoquer immédiatement + git rebase/filter-branch
- Utiliser `git log -p --all -S "sk-"` pour vérifier l'historique

### Prompts métier
- Les prompts qui décrivent un processus interne sont propriétaires
- Remplacer par un prompt générique équivalent ou `[PROMPT REDACTED]`
- Ne pas publier de few-shots avec des données réelles du domaine

### Noms de personnes
- Aucun prénom/nom de collaborateurs internes dans les exemples
- Utiliser `Alice`, `Bob`, `User A` pour les exemples

---

## En cas de doute

Appliquer la règle la plus restrictive : **ne pas publier**.
Ouvrir une issue privée ou demander une revue avant tout push.

---

*TricorderKit v0.9 — politique de confidentialité des linked projects*
