# Patterns Cypher — graphe culturel (auteur → œuvres → adaptations)

Les labels et relations ci-dessous sont un **modèle générique** ; remplacer par ceux que renvoie
`get-schema`. Conventions : paramètres nommés (`$x`), `LIMIT` toujours présent en lecture,
`MERGE` en écriture, provenance sur tout ce qui est écrit.

## Modèle de référence

```
(:Personne {nom_jp, nom_romaji, id_externe})
   -[:AUTEUR_DE|:ILLUSTRATEUR_DE]-> (:Oeuvre {titre_jp, titre_fr, type, debut, id_externe})
(:Oeuvre) -[:PUBLIE_PAR]-> (:Editeur {nom})
(:Oeuvre) -[:PREPUBLIE_DANS]-> (:Magazine {nom})
(:Oeuvre) -[:ADAPTE_EN]-> (:Adaptation {type: 'serie'|'film', debut})
(:Adaptation) -[:PRODUIT_PAR]-> (:Studio {nom})
```

Propriétés de provenance sur nœuds et relations : `source` (nom du collecteur ou de la base),
`collecte_le` (ISO 8601), `confiance` (0–1), éventuellement `url`.

## Lecture

### Bibliographie d'un auteur
```cypher
MATCH (p:Personne)-[:AUTEUR_DE]->(o:Oeuvre)
WHERE p.nom_jp = $nom OR p.nom_romaji = $nom
RETURN o.titre_jp, o.titre_fr, o.type, o.debut
ORDER BY o.debut
LIMIT 100
```

### Chaîne complète œuvre → adaptations → studio
```cypher
MATCH (o:Oeuvre {id_externe: $id})
OPTIONAL MATCH (o)-[:ADAPTE_EN]->(a:Adaptation)-[:PRODUIT_PAR]->(s:Studio)
RETURN o.titre_jp, a.type, a.debut, s.nom
LIMIT 50
```

### Co-auteurs (même œuvre, rôles distincts)
```cypher
MATCH (p1:Personne)-[:AUTEUR_DE]->(o:Oeuvre)<-[:ILLUSTRATEUR_DE]-(p2:Personne)
WHERE p1 <> p2
RETURN p1.nom_romaji, p2.nom_romaji, count(o) AS collaborations
ORDER BY collaborations DESC
LIMIT 50
```

### Plus court chemin entre deux entités
```cypher
MATCH (a {id_externe: $a}), (b {id_externe: $b})
MATCH chemin = shortestPath((a)-[*..6]-(b))
RETURN [n IN nodes(chemin) | coalesce(n.titre_jp, n.nom_jp, n.nom)] AS etapes
LIMIT 1
```

### Orphelins (nœuds sans aucune relation)
```cypher
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n) AS labels, count(*) AS nb
ORDER BY nb DESC
```

### Doublons probables par titre normalisé
```cypher
MATCH (o:Oeuvre)
WITH toLower(apoc.text.clean(o.titre_jp)) AS cle, collect(o) AS oeuvres
WHERE size(oeuvres) > 1
RETURN cle, [x IN oeuvres | x.id_externe] AS ids
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
MATCH (p:Personne {id_externe: $pid}), (o:Oeuvre {id_externe: $oid})
RETURN count(*) AS cibles
```

### Lier auteur → œuvre, idempotent, avec provenance
```cypher
MATCH (p:Personne {id_externe: $pid}), (o:Oeuvre {id_externe: $oid})
MERGE (p)-[r:AUTEUR_DE]->(o)
ON CREATE SET r.source = $source, r.collecte_le = datetime(), r.confiance = $confiance
RETURN type(r), r.source
```
Inverse : `MATCH (p {id_externe:$pid})-[r:AUTEUR_DE]->(o {id_externe:$oid}) DELETE r` —
à ne proposer qu'avec l'export préalable.

### Créer une adaptation manquante
```cypher
MATCH (o:Oeuvre {id_externe: $oid})
MERGE (a:Adaptation {id_externe: $aid})
ON CREATE SET a.type = $type, a.debut = $debut, a.source = $source, a.collecte_le = datetime()
MERGE (o)-[:ADAPTE_EN]->(a)
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
CREATE CONSTRAINT oeuvre_id IF NOT EXISTS FOR (o:Oeuvre) REQUIRE o.id_externe IS UNIQUE;
CREATE CONSTRAINT personne_id IF NOT EXISTS FOR (p:Personne) REQUIRE p.id_externe IS UNIQUE;
CREATE INDEX oeuvre_titre IF NOT EXISTS FOR (o:Oeuvre) ON (o.titre_jp);
```

## GDS — projection ciblée
```cypher
CALL gds.graph.project('proj_2026_09_07', ['Personne','Oeuvre'], ['AUTEUR_DE','ILLUSTRATEUR_DE']);
CALL gds.pageRank.stream('proj_2026_09_07') YIELD nodeId, score
RETURN gds.util.asNode(nodeId).nom_romaji AS nom, score ORDER BY score DESC LIMIT 20;
CALL gds.graph.drop('proj_2026_09_07');
```
