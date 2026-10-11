# Checklist OWASP Top 10 (2021) — grille de passage systématique

Pour chaque item, répondre à quatre questions : **présent ?** · **exploitable ?** · **gravité ?**
(Critique / Élevé / Moyen / Faible) · **correctif local ou STRUCTURAL ?** (cf. règle cardinale du SKILL.md).

| Réf | Catégorie | Où regarder | Signaux typiques | Correctif local (applicable) | Correctif STRUCTURAL (à proposer) |
|---|---|---|---|---|---|
| A01 | Contrôle d'accès défaillant | routes, middlewares, requêtes par id | IDOR (`/users/{id}` sans vérification), rôles vérifiés côté client seulement, CORS `*` avec credentials | vérifier l'appartenance de la ressource dans le handler | refonte du modèle de rôles, changement de politique CORS |
| A02 | Défaillances cryptographiques | stockage mots de passe, tokens, transport | MD5/SHA1 pour les mots de passe, secrets dans le code, HTTP en clair, JWT `alg:none` | passer à bcrypt/argon2 sur les nouveaux hashes | migration des hashes existants, rotation de clés |
| A03 | Injection | toute concaténation vers SQL/NoSQL/shell/HTML | `f"SELECT … {x}"`, `innerHTML = data`, `os.system(cmd + arg)` | requêtes paramétrées, échappement contextuel, `subprocess.run([...])` | changement d'ORM / de moteur de templates |
| A04 | Conception non sécurisée | flux métier | absence de limite de tentatives, logique de prix côté client, workflow contournable | ajouter la validation manquante côté serveur | redesign du flux |
| A05 | Mauvaise configuration | headers, fichiers de config, mode debug | `DEBUG=True` en prod, CSP absente, listing de répertoire, stack traces exposées | désactiver le debug, ajouter les headers manquants | changement de reverse-proxy, politique CSP stricte |
| A06 | Composants vulnérables | lockfiles, versions | dépendances non épinglées, CVE connues (`pip-audit`, `npm audit`) | bump de patch sans changement d'API | montée de version majeure |
| A07 | Authentification défaillante | login, sessions, reset | pas de rate-limit sur le login, session non renouvelée après login, reset prévisible | renouveler l'id de session, limiter les tentatives | changement de fournisseur d'auth |
| A08 | Intégrité des données/logiciels | pipeline CI, désérialisation, mises à jour | `pickle.loads` sur entrée externe, scripts distants exécutés sans hash | remplacer par un format sûr (JSON) | refonte du pipeline de déploiement |
| A09 | Journalisation insuffisante | logs, alertes | échecs d'auth non tracés, logs sans horodatage, secrets dans les logs | logger les événements de sécurité, masquer les secrets | mise en place d'une chaîne d'alerte |
| A10 | SSRF | tout fetch d'URL fournie par l'utilisateur | `requests.get(user_url)` sans liste blanche, accès aux métadonnées cloud | liste blanche de schémas/hôtes, timeouts | isolation réseau du composant qui fetch |

## Ordre de passage conseillé
1. A03 et A01 d'abord (les plus fréquents et les plus exploitables).
2. A05 et A07 ensuite (souvent des quick wins de configuration).
3. Le reste selon la surface réelle de l'application.

## Rappel « flux illimité »
Une limite qui protège (rate-limit, quota, taille max, timeout) relève de A04/A07 : la retirer crée une
faille → catégorie STRUCTURAL, jamais en correctif local.
