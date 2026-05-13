/**
 * TricorderKit — graph-server
 * Serveur MCP stdio — 4 outils graphify
 *
 * Outils :
 *   graphify_ping      → connectivité Neo4j + Qdrant
 *   graphify_store     → écrire un nœud (Neo4j + Qdrant)
 *   graphify_relate    → créer une relation Neo4j
 *   graphify_retrieve  → requête hybride (graph + vector)
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

import { Neo4jClient } from './neo4j_client.js';
import { TKQdrantClient } from './qdrant_client.js';

// ─── Clients ────────────────────────────────────────────────────────────────

const neo4j  = new Neo4jClient();
const qdrant = new TKQdrantClient();

// ─── Schémas Zod (alignés sur core/contracts/graph.schema.json) ─────────────

const NODE_TYPES = [
  'Concept', 'Entity', 'Task', 'Skill',
  'Agent', 'Source', 'Session', 'Decision',
] as const;

const REL_TYPES = [
  'RELATES_TO', 'DEPENDS_ON', 'PRODUCES', 'CONSUMES',
  'REFERENCES', 'DERIVED_FROM', 'PART_OF', 'IMPLEMENTS', 'DISCOVERED_IN',
] as const;

const NodeWriteSchema = z.object({
  id:          z.string().min(3).max(64).regex(/^[a-z][a-z0-9_-]+$/),
  type:        z.enum(NODE_TYPES),
  title:       z.string().max(256),
  content:     z.string().optional(),
  tags:        z.array(z.string()).optional(),
  source_url:  z.string().url().optional(),
  confidence:  z.number().min(0).max(1).optional(),
  created_by:  z.string().optional(),
  session_id:  z.string().optional(),
  extra:       z.record(z.unknown()).optional(),
});

const RelWriteSchema = z.object({
  from_id:  z.string(),
  rel_type: z.enum(REL_TYPES),
  to_id:    z.string(),
  weight:   z.number().min(0).max(1).optional(),
  metadata: z.record(z.unknown()).optional(),
});

const RetrieveSchema = z.object({
  query:      z.string().min(1),
  mode:       z.enum(['hybrid', 'graph', 'vector']).default('hybrid'),
  limit:      z.number().int().min(1).max(100).default(10),
  min_score:  z.number().min(0).max(1).default(0.5),
  node_types: z.array(z.enum(NODE_TYPES)).optional(),
});

// ─── Serveur MCP ─────────────────────────────────────────────────────────────

const server = new McpServer({
  name:    'graph-server',
  version: '0.1.0',
});

// ── Tool : graphify_ping ────────────────────────────────────────────────────

server.tool(
  'graphify_ping',
  'Vérifie la connectivité de Neo4j et Qdrant. Retourne un objet { neo4j: bool, qdrant: bool, ok: bool }.',
  {},
  async () => {
    const [neo4jOk, qdrantOk] = await Promise.all([
      neo4j.ping(),
      qdrant.ping(),
    ]);
    const ok = neo4jOk && qdrantOk;
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({ neo4j: neo4jOk, qdrant: qdrantOk, ok }),
      }],
      isError: !ok,
    };
  }
);

// ── Tool : graphify_store ───────────────────────────────────────────────────

server.tool(
  'graphify_store',
  'Écrit un nœud dans Neo4j ET génère son embedding dans Qdrant. Idempotent (MERGE sur id).',
  {
    id:         z.string().describe('Identifiant unique du nœud — minuscules, tirets autorisés (ex: dec-008-langgraph)'),
    type:       z.enum(NODE_TYPES).describe('Type de nœud : Concept | Entity | Task | Skill | Agent | Source | Session | Decision'),
    title:      z.string().describe('Titre court du nœud (max 256 chars)'),
    content:    z.string().optional().describe('Contenu textuel principal — utilisé pour l\'embedding Qdrant'),
    tags:       z.array(z.string()).optional().describe('Tags libres'),
    source_url: z.string().optional().describe('URL source (optionnelle)'),
    confidence: z.number().optional().describe('Score de confiance 0-1'),
    created_by: z.string().optional().describe('Agent ou skill auteur (ex: mainbrain, deep-research-core)'),
    session_id: z.string().optional().describe('ID de la session d\'origine'),
    extra:      z.record(z.unknown()).optional().describe('Champs métier spécifiques au type (ex: decision_id, status, impact)'),
  },
  async (args) => {
    const parsed = NodeWriteSchema.parse(args);
    const now = new Date().toISOString();
    const node = {
      ...parsed,
      created_at: now,
      updated_at: now,
      ...(parsed.extra ?? {}),
    };

    // Écriture Neo4j
    await neo4j.upsertNode(node);

    // Embedding Qdrant (sur title + content)
    const textToEmbed = [parsed.title, parsed.content].filter(Boolean).join(' — ');
    await qdrant.upsertVector(parsed.id, parsed.type, textToEmbed, {
      id: parsed.id,
      type: parsed.type,
      title: parsed.title,
      tags: parsed.tags ?? [],
      created_at: now,
    });

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'success',
          id: parsed.id,
          type: parsed.type,
          neo4j: 'upserted',
          qdrant: 'indexed',
          timestamp: now,
        }),
      }],
    };
  }
);

// ── Tool : graphify_relate ──────────────────────────────────────────────────

server.tool(
  'graphify_relate',
  'Crée une relation typée entre deux nœuds existants dans Neo4j. Idempotent (MERGE).',
  {
    from_id:  z.string().describe('ID du nœud source'),
    rel_type: z.enum(REL_TYPES).describe('Type de relation : RELATES_TO | DEPENDS_ON | PRODUCES | CONSUMES | REFERENCES | DERIVED_FROM | PART_OF | IMPLEMENTS | DISCOVERED_IN'),
    to_id:    z.string().describe('ID du nœud cible'),
    weight:   z.number().optional().describe('Force de la relation 0-1 (optionnel)'),
    metadata: z.record(z.unknown()).optional().describe('Propriétés libres sur la relation'),
  },
  async (args) => {
    const parsed = RelWriteSchema.parse(args);
    await neo4j.upsertRelationship(parsed);
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'success',
          from_id: parsed.from_id,
          rel_type: parsed.rel_type,
          to_id: parsed.to_id,
          timestamp: new Date().toISOString(),
        }),
      }],
    };
  }
);

// ── Tool : graphify_retrieve ────────────────────────────────────────────────

server.tool(
  'graphify_retrieve',
  'Requête hybride sur le knowledge graph. Mode hybrid = Neo4j keyword + Qdrant vector en parallèle, résultats fusionnés et rankés par score.',
  {
    query:      z.string().describe('Requête en langage naturel'),
    mode:       z.enum(['hybrid', 'graph', 'vector']).optional().describe('Mode de recherche : hybrid (défaut) | graph (Neo4j seul) | vector (Qdrant seul)'),
    limit:      z.number().optional().describe('Nombre maximum de résultats (défaut 10, max 100)'),
    min_score:  z.number().optional().describe('Score minimum de similarité 0-1 pour le mode vector (défaut 0.5)'),
    node_types: z.array(z.enum(NODE_TYPES)).optional().describe('Filtrer par types de nœuds (optionnel)'),
  },
  async (args) => {
    const parsed = RetrieveSchema.parse(args);
    const { query, mode, limit, min_score, node_types } = parsed;

    const graphResults =
      mode !== 'vector'
        ? await neo4j.queryByKeyword(query, node_types ?? [], limit)
        : [];

    const vectorResults =
      mode !== 'graph'
        ? await qdrant.search(query, node_types ?? [], limit, min_score)
        : [];

    // Fusion : enrichir les résultats vector avec les données Neo4j
    const vectorIds = vectorResults.map((r) => r.id);
    const enriched  = vectorIds.length > 0 ? await neo4j.getNodesByIds(vectorIds) : [];
    const enrichedMap = new Map(enriched.map((n) => [n.id, n]));

    const vectorNodes = vectorResults.map((r) => ({
      ...enrichedMap.get(r.id),
      _score: r.score,
      _source: 'vector',
    }));

    // Merge + déduplication par id
    const seen = new Set<string>();
    const merged = [
      ...graphResults.map((n) => ({ ...n, _source: 'graph', _score: 1.0 })),
      ...vectorNodes,
    ].filter((n) => {
      const id = n.id as string;
      if (!id || seen.has(id)) return false;
      seen.add(id);
      return true;
    });

    // Tri par score décroissant
    merged.sort((a, b) => ((b._score as number) ?? 0) - ((a._score as number) ?? 0));

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'success',
          query,
          mode,
          count: merged.length,
          results: merged.slice(0, limit),
        }),
      }],
    };
  }
);

// ─── Démarrage ───────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // Stdout réservé au protocole MCP — logs sur stderr
  process.stderr.write('graph-server MCP démarré (stdio)\n');
}

main().catch((err) => {
  process.stderr.write(`graph-server erreur fatale : ${err}\n`);
  process.exit(1);
});
