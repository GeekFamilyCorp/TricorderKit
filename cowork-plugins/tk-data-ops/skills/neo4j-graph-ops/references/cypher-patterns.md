# Patterns Cypher — graphe de connaissances (personne → projets → versions)

Les labels et relations ci-dessous sont un **modèle générique** ; remplacer par ceux que renvoie
`get-schema`. Conventions : paramètres nommés (`$x`), `LIMIT` toujours présent en lecture,
`MERGE` en écriture, provenance sur tout ce qui est écrit.

## Modèle de référence

```
(:Personne {nom, nom_alias, id_externe})
   -[:AUTEUR_DE|:CONTRIBUE_A]-> (:Projet {nom, nom_alias, type, debut, id_externe})
(:Projet) -[:SOUTENU_PAR]-> (:Organisation {nom})
(:Article {titre, annee, id_externe}) -[:DECRIT]-> (:Projet)
(:Projet) -[:PUBLIE_EN]-> (:Version {type: 'majeure'|'mineure', debut})
(:Version) -[:PUBLIEE_PAR]-> (:Organisation {nom})
```

Propriétés de provenance sur nœuds et relations : `source` (nom du collecteur ou de la base),
`collecte_le` (ISO 8601), `confiance` (0–1), éventuellement `url`.

## Lecture

### Projets d'une personne
```cypher
MATCH (p:Personne)-[:AUTEUR_DE]->(o:Projet)
WHERE p.nom = $nom OR p.nom_alias = $nom
RETURN o.nom, o.type, o.debut
ORDER BY o.debut
LIMIT 100
```

### Chaîne complète projet → versions → organisation
```cypher
MATCH (o:Projet {id_externe: $id})
OPTIONAL MATCH (o)-[:PUBLIE_EN]->(a:Version)-[:PUBLIEE_PAR]->(s:Organisation)
RETURN o.nom, a.type, a.debut, s.nom
LIMIT 50
```

### Co-auteurs (même projet, rôles distincts)
```cypher
MATCH (p1:Personne)-[:AUTEUR_DE]->(o:Projet)<-[:CONTRIBUE_A]-(p2:Personne)
WHERE p1 <> p2
RETURN p1.nom, p2.nom, count(o) AS collaborations
ORDER BY collaborations DESC
LIMIT 50
```

### Plus court chemin entre deux entités
```cypher
MATCH (a {id_externe: $a}), (b {id_externe: $b})
MATCH chemin = shortestPath((a)-[*..6]-(b))
RETURN [n IN nodes(chemin) | coalesce(n.titre, n.nom)] AS etapes
LIMIT 1
```

### Orphelins (nœuds sans aucune relation)
```cypher
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n) AS labels, count(*) AS nb
ORDER BY nb DESC
```

### Doublons probables par nom normalisé
```cypher
MATCH (o:Projet)
WITH toLower(apoc.text.clean(o.nom)) AS cle, collect(o) AS projets
WHERE size(projets) > 1
RETURN cle, [x IN projets | x.id_externe] AS ids
LIMIT 100
```
(`apoc.text.clean` nécessite APOC ; sans APOC, `toLower(trim(...))`.) Un doublon se **prouve par le
contenu**, pas par le nom : lister, comparer, puis seulement fusionner sur GO.

### Provenance d'un nœud
```cypher
MATCH (n {id_externe: $id})
RETURN n.source, n.collecte_le, n.confiance, n.url
```

## Écriture (après GO, `NEO4J_READ_ONLY=false`)

### Compter avant
```cypher
MATCH (p:Personne {id_externe: $pid}), (o:Projet {id_externe: $oid})
RETURN count(*) AS cibles
```

### Lier auteur → projet, idempotent, avec provenance
```cypher
MATCH (p:Personne {id_externe: $pid}), (o:Projet {id_externe: $oid})
MERGE (p)-[r:AUTEUR_DE]->(o)
ON CREATE SET r.source = $source, r.collecte_le = datetime(), r.confiance = $confiance
RETURN type(r), r.source
```
Inverse : `MATCH (p {id_externe:$pid})-[r:AUTEUR_DE]->(o {id_externe:$oid}) DELETE r` —
à ne proposer qu'avec l'export préalable.

### Créer une version manquante
```cypher
MATCH (o:Projet {id_externe: $oid})
MERGE (a:Version {id_externe: $aid})
ON CREATE SET a.type = $type, a.debut = $debut, a.source = $source, a.collecte_le = datetime()
MERGE (o)-[:PUBLIE_EN]->(a)
RETURN a.id_externe
```

## Archivage (NO-DROP)

Marquer plutôt que supprimer :
```cypher
MATCH (n {id_externe: $id})
SET n.archive_le = datetime(), n.remplace_par = $canonique
```
Exclure les archivés des lectures courantes : `WHERE n.archive_le IS NULL`.

Si une suppression est exigée : exporter d'abord (`CALL apoc.export.json.query(...)` vers un fichier
daté), annoncer le compte, attendre le GO, puis `DETACH DELETE` sur les seuls `id_externe` listés.

## Contraintes et index utiles
```cypher
CREATE CONSTRAINT projet_id IF NOT EXISTS FOR (o:Projet) REQUIRE o.id_externe IS UNIQUE;
CREATE CONSTRAINT personne_id IF NOT EXISTS FOR (p:Personne) REQUIRE p.id_externe IS UNIQUE;
CREATE INDEX projet_nom IF NOT EXISTS FOR (o:Projet) ON (o.nom);
```

## GDS — projection ciblée
```cypher
CALL gds.graph.project('proj_2026_09_07', ['Personne','Projet'], ['AUTEUR_DE','CONTRIBUE_A']);
CALL gds.pageRank.stream('proj_2026_09_07') YIELD nodeId, score
RETURN gds.util.asNode(nodeId).nom AS nom, score ORDER BY score DESC LIMIT 20;
CALL gds.graph.drop('proj_2026_09_07');
```
