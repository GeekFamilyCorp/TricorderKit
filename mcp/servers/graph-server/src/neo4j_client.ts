/**
 * TricorderKit — graph-server
 * Neo4j Client — wrapper driver pour les opérations graph
 */

import neo4j, { Driver } from 'neo4j-driver';

export interface Neo4jNode {
  id: string;
  type: string;
  title: string;
  content?: string;
  tags?: string[];
  source_url?: string;
  confidence?: number;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  session_id?: string;
  [key: string]: unknown;
}

export interface Neo4jRelationship {
  from_id: string;
  rel_type: string;
  to_id: string;
  weight?: number;
  created_at?: string;
  metadata?: Record<string, unknown>;
}

// ─── Sanitize ────────────────────────────────────────────────────────────────
// Neo4j n'accepte que les primitives et tableaux de primitives.
// On convertit les objets imbriqués en JSON string.

function sanitizeProps(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, val] of Object.entries(obj)) {
    if (val === null || val === undefined) continue;
    if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
      result[key] = val;
    } else if (Array.isArray(val)) {
      // Tableaux de primitives uniquement — on sérialise les éléments objets
      result[key] = val.map((v) =>
        typeof v === 'object' && v !== null ? JSON.stringify(v) : v
      );
    } else if (typeof val === 'object') {
      // Objet imbriqué → JSON string
      result[key] = JSON.stringify(val);
    }
  }
  return result;
}

// ─── Client ──────────────────────────────────────────────────────────────────

export class Neo4jClient {
  private driver: Driver;

  constructor(
    uri: string = process.env.NEO4J_URI ?? 'bolt://localhost:7687',
    user: string = process.env.NEO4J_USER ?? 'neo4j',
    password: string = process.env.NEO4J_PASSWORD ?? ''
  ) {
    this.driver = neo4j.driver(uri, neo4j.auth.basic(user, password));
  }

  async ping(): Promise<boolean> {
    const session = this.driver.session();
    try {
      await session.run('RETURN 1');
      return true;
    } catch {
      return false;
    } finally {
      await session.close();
    }
  }

  // ── Écrire un nœud ───────────────────────────────────────────────────────

  async upsertNode(node: Neo4jNode): Promise<void> {
    const session = this.driver.session();
    try {
      const { id, type, ...rest } = node;
      const props = sanitizeProps({ id, type, ...rest });
      const query = `
        MERGE (n:TKNode { id: $id })
        SET n += $props
        SET n:${type}
        RETURN n
      `;
      await session.run(query, { id, props });
    } finally {
      await session.close();
    }
  }

  // ── Créer une relation ───────────────────────────────────────────────────

  async upsertRelationship(rel: Neo4jRelationship): Promise<void> {
    const session = this.driver.session();
    try {
      const { from_id, to_id, rel_type, metadata, ...rest } = rel;
      const props = sanitizeProps({
        created_at: new Date().toISOString(),
        ...rest,
        ...(metadata ?? {}),
      });
      const query = `
        MATCH (a:TKNode { id: $from_id })
        MATCH (b:TKNode { id: $to_id })
        MERGE (a)-[r:${rel_type}]->(b)
        SET r += $props
        RETURN r
      `;
      await session.run(query, { from_id, to_id, props });
    } finally {
      await session.close();
    }
  }

  // ── Requête graph traversal ──────────────────────────────────────────────

  async queryByKeyword(
    keyword: string,
    nodeTypes: string[] = [],
    limit: number = 10
  ): Promise<Neo4jNode[]> {
    const session = this.driver.session();
    try {
      const typeFilter =
        nodeTypes.length > 0
          ? `WHERE n.type IN [${nodeTypes.map((t) => `'${t}'`).join(', ')}]`
          : '';

      const query = `
        MATCH (n:TKNode)
        ${typeFilter}
        WHERE toLower(n.title) CONTAINS toLower($keyword)
           OR toLower(coalesce(n.content, '')) CONTAINS toLower($keyword)
        RETURN n
        ORDER BY n.confidence DESC
        LIMIT $limit
      `;

      const result = await session.run(query, { keyword, limit: neo4j.int(limit) });
      return result.records.map((r) => r.get('n').properties as Neo4jNode);
    } finally {
      await session.close();
    }
  }

  // ── Requête par IDs ──────────────────────────────────────────────────────

  async getNodesByIds(ids: string[]): Promise<Neo4jNode[]> {
    if (ids.length === 0) return [];
    const session = this.driver.session();
    try {
      const result = await session.run(
        'MATCH (n:TKNode) WHERE n.id IN $ids RETURN n',
        { ids }
      );
      return result.records.map((r) => r.get('n').properties as Neo4jNode);
    } finally {
      await session.close();
    }
  }

  async close(): Promise<void> {
    await this.driver.close();
  }
}
