/**
 * TricorderKit — graph-server
 * Neo4j Client — wrapper driver pour les opérations graph
 */

import neo4j, { Driver, Session } from 'neo4j-driver';

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

export interface GraphQueryResult {
  nodes: Neo4jNode[];
  relationships: Neo4jRelationship[];
  raw: unknown[];
}

// ─── Client ────────────────────────────────────────────────────────────────

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
      // MERGE sur l'ID — idempotent
      const query = `
        MERGE (n:TKNode { id: $id })
        SET n += $props
        SET n:${node.type}
        RETURN n
      `;
      const { id, type, ...rest } = node;
      await session.run(query, { id, props: { id, type, ...rest } });
    } finally {
      await session.close();
    }
  }

  // ── Créer une relation ───────────────────────────────────────────────────

  async upsertRelationship(rel: Neo4jRelationship): Promise<void> {
    const session = this.driver.session();
    try {
      const query = `
        MATCH (a:TKNode { id: $from_id })
        MATCH (b:TKNode { id: $to_id })
        MERGE (a)-[r:${rel.rel_type}]->(b)
        SET r += $props
        RETURN r
      `;
      const { from_id, to_id, rel_type, ...props } = rel;
      await session.run(query, {
        from_id,
        to_id,
        props: { created_at: new Date().toISOString(), ...props },
      });
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

  // ── Requête par IDs (pour merge avec résultats Qdrant) ──────────────────

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
