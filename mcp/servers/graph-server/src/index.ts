/**
 * TricorderKit — graph-server
 * Serveur MCP stdio — 4 outils graphify
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

import { Neo4jClient } from './neo4j_client.js';
import { TKQdrantClient } from './qdrant_client.js';

const neo4j  = new Neo4jClient();
const qdrant = new TKQdrantClient();

const NODE_TYPES = [
  'Concept', 'Entity', 'Task', 'Skill',
  'Agent', 'Source', 'Session', 'Decision',
] as const;

const REL_TYPES = [
  'RELATES_TO', 'DEPENDS_ON', 'PRODUCES', 'CONSUMES',
  'REFERENCES', 'DERIVED_FROM', 'PART_OF', 'IMPLEMENTS', 'DISCOVERED_IN',
] as const;

const NodeWriteSchema = z.object({
  id:         z.string().min(3).max(64).regex(/^[a-z][a-z0-9_-]+$/),
  type:       z.enum(NODE_TYPES),
  title:      z.string().max(256),
  content:    z.string().optional(),
  tags:       z.array(z.string()).optional(),
  source_url: z.string().url().optional(),
  confidence: z.number().min(0).max(1).optional(),
  created_by: z.string().optional(),
  session_id: z.string().optional(),
  extra:      z.record(z.unknown()).optional(),
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

// ─── Helper log ──────────────────────────────────────────────────────────────
function log(msg: string): void {
  process.stderr.write(`[graph-server] ${msg}\n`);
}

function errResult(err: unknown) {
  const msg = err instanceof Error ? err.message : String(err);
  log(`ERROR: ${msg}`);
  return {
    content: [{ type: 'text' as const, text: JSON.stringify({ status: 'error', error: msg }) }],
    isError: true,
  };
}

// ─── Serveur MCP ─────────────────────────────────────────────────────────────

const server = new McpServer({ name: 'graph-server', version: '0.1.0' });

// ── graphify_ping ─────────────────────────────────────────────────────────────

server.tool(
  'graphify_ping',
  'Vérifie la connectivité de Neo4j et Qdrant.',
  {},
  async () => {
    try {
      const [neo4jOk, qdrantOk] = await Promise.all([neo4j.ping(), qdrant.ping()]);
      const ok = neo4jOk && qdrantOk;
      log(`ping — neo4j:${neo4jOk} qdrant:${qdrantOk}`);
      return {
        content: [{ type: 'text', text: JSON.stringify({ neo4j: neo4jOk, qdrant: qdrantOk, ok }) }],
        isError: !ok,
      };
    } catch (err) { return errResult(err); }
  }
);

// ── graphify_store ────────────────────────────────────────────────────────────

server.tool(
  'graphify_store',
  'Écrit un nœud dans Neo4j ET génère son embedding dans Qdrant. Idempotent (MERGE sur id).',
  {
    id:         z.string().describe('Identifiant unique — minuscules, tirets autorisés (ex: dec-008-langgraph)'),
    type:       z.enum(NODE_TYPES).describe('Type : Concept | Entity | Task | Skill | Agent | Source | Session | Decision'),
    title:      z.string().describe('Titre court (max 256 chars)'),
    content:    z.string().optional().describe('Contenu textuel — utilisé pour l\'embedding'),
    tags:       z.array(z.string()).optional().describe('Tags libres'),
    source_url: z.string().optional().describe('URL source'),
    confidence: z.number().optional().describe('Score de confiance 0-1'),
    created_by: z.string().optional().describe('Agent auteur'),
    session_id: z.string().optional().describe('ID session d\'origine'),
    extra:      z.record(z.unknown()).optional().describe('Champs métier additionnels'),
  },
  async (args) => {
    try {
      log(`graphify_store called — id:${args.id} type:${args.type}`);
      const parsed = NodeWriteSchema.parse(args);
      const now    = new Date().toISOString();
      const node   = { ...parsed, created_at: now, updated_at: now, ...(parsed.extra ?? {}) };

      log('writing to Neo4j...');
      await neo4j.upsertNode(node);
      log('Neo4j OK');

      const textToEmbed = [parsed.title, parsed.content].filter(Boolean).join(' — ');
      log(`embedding: "${textToEmbed.slice(0, 60)}..."`);
      await qdrant.upsertVector(parsed.id, parsed.type, textToEmbed, {
        id: parsed.id, type: parsed.type, title: parsed.title,
        tags: parsed.tags ?? [], created_at: now,
      });
      log('Qdrant OK');

      return {
        content: [{ type: 'text', text: JSON.stringify({
          status: 'success', id: parsed.id, type: parsed.type,
          neo4j: 'upserted', qdrant: 'indexed', timestamp: now,
        })}],
      };
    } catch (err) { return errResult(err); }
  }
);

// ── graphify_relate ───────────────────────────────────────────────────────────

server.tool(
  'graphify_relate',
  'Crée une relation typée entre deux nœuds Neo4j. Idempotent (MERGE).',
  {
    from_id:  z.string().describe('ID nœud source'),
    rel_type: z.enum(REL_TYPES).describe('Type de relation'),
    to_id:    z.string().describe('ID nœud cible'),
    weight:   z.number().optional().describe('Force 0-1'),
    metadata: z.record(z.unknown()).optional().describe('Propriétés libres'),
  },
  async (args) => {
    try {
      log(`graphify_relate — ${args.from_id} -[${args.rel_type}]-> ${args.to_id}`);
      const parsed = RelWriteSchema.parse(args);
      await neo4j.upsertRelationship(parsed);
      return {
        content: [{ type: 'text', text: JSON.stringify({
          status: 'success', from_id: parsed.from_id,
          rel_type: parsed.rel_type, to_id: parsed.to_id,
          timestamp: new Date().toISOString(),
        })}],
      };
    } catch (err) { return errResult(err); }
  }
);

// ── graphify_retrieve ─────────────────────────────────────────────────────────

server.tool(
  'graphify_retrieve',
  'Requête hybride Neo4j + Qdrant, résultats fusionnés par score.',
  {
    query:      z.string().describe('Requête en langage naturel'),
    mode:       z.enum(['hybrid', 'graph', 'vector']).optional().describe('hybrid | graph | vector'),
    limit:      z.number().optional().describe('Max résultats (défaut 10)'),
    min_score:  z.number().optional().describe('Score minimum 0-1 (défaut 0.5)'),
    node_types: z.array(z.enum(NODE_TYPES)).optional().describe('Filtrer par types'),
  },
  async (args) => {
    try {
      log(`graphify_retrieve — "${args.query}" mode:${args.mode ?? 'hybrid'}`);
      const parsed = RetrieveSchema.parse(args);
      const { query, mode, limit, min_score, node_types } = parsed;

      const graphResults = mode !== 'vector'
        ? await neo4j.queryByKeyword(query, node_types ?? [], limit) : [];
      const vectorResults = mode !== 'graph'
        ? await qdrant.search(query, node_types ?? [], limit, min_score) : [];

      const vectorIds   = vectorResults.map((r) => r.id);
      const enriched    = vectorIds.length > 0 ? await neo4j.getNodesByIds(vectorIds) : [];
      const enrichedMap = new Map(enriched.map((n) => [n.id, n]));
      const vectorNodes = vectorResults.map((r) => ({ ...enrichedMap.get(r.id), _score: r.score, _source: 'vector' }));

      const seen   = new Set<string>();
      const merged = [
        ...graphResults.map((n) => ({ ...n, _source: 'graph', _score: 1.0 })),
        ...vectorNodes,
      ].filter((n) => { const id = n.id as string; if (!id || seen.has(id)) return false; seen.add(id); return true; });

      merged.sort((a, b) => ((b._score as number) ?? 0) - ((a._score as number) ?? 0));
      log(`retrieve — ${merged.length} results`);

      return {
        content: [{ type: 'text', text: JSON.stringify({
          status: 'success', query, mode, count: merged.length,
          results: merged.slice(0, limit),
        })}],
      };
    } catch (err) { return errResult(err); }
  }
);

// ─── Démarrage ────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  log('graph-server MCP démarré (stdio)');
}

main().catch((err) => {
  log(`erreur fatale : ${err}`);
  process.exit(1);
});
