/**
 * TricorderKit — graph-server
 * Qdrant Client — wrapper pour embedding + vector search
 */

import { QdrantClient } from '@qdrant/js-client-rest';
import OpenAI from 'openai';

const VECTOR_SIZE = 1536; // text-embedding-3-small
const DISTANCE    = 'Cosine';

// Collections = 1 par type de nœud (voir graph.schema.json)
const NODE_COLLECTIONS = [
  'concepts', 'entities', 'tasks', 'skills',
  'agents', 'sources', 'sessions', 'decisions',
] as const;

type NodeCollection = typeof NODE_COLLECTIONS[number];

const TYPE_TO_COLLECTION: Record<string, NodeCollection> = {
  Concept:  'concepts',
  Entity:   'entities',
  Task:     'tasks',
  Skill:    'skills',
  Agent:    'agents',
  Source:   'sources',
  Session:  'sessions',
  Decision: 'decisions',
};

export interface VectorSearchResult {
  id: string;
  score: number;
  payload: Record<string, unknown>;
}

// ─── Qdrant Client ──────────────────────────────────────────────────────────

export class TKQdrantClient {
  private qdrant: QdrantClient;
  private openai: OpenAI;

  constructor(
    qdrantUrl: string  = process.env.QDRANT_URL      ?? 'http://localhost:6333',
    qdrantKey: string  = process.env.QDRANT_API_KEY  ?? '',
    openaiKey: string  = process.env.OPENAI_API_KEY  ?? ''
  ) {
    this.qdrant = new QdrantClient({
      url: qdrantUrl,
      ...(qdrantKey ? { apiKey: qdrantKey } : {}),
    });
    this.openai = new OpenAI({ apiKey: openaiKey });
  }

  async ping(): Promise<boolean> {
    try {
      await this.qdrant.getCollections();
      return true;
    } catch {
      return false;
    }
  }

  // ── Initialiser les collections ─────────────────────────────────────────

  async ensureCollections(): Promise<void> {
    const existing = await this.qdrant.getCollections();
    const existingNames = existing.collections.map((c) => c.name);

    for (const name of NODE_COLLECTIONS) {
      if (!existingNames.includes(name)) {
        await this.qdrant.createCollection(name, {
          vectors: { size: VECTOR_SIZE, distance: DISTANCE },
        });
      }
    }
  }

  // ── Embedding ────────────────────────────────────────────────────────────

  async embed(text: string): Promise<number[]> {
    const response = await this.openai.embeddings.create({
      model: process.env.EMBEDDING_MODEL ?? 'text-embedding-3-small',
      input: text,
    });
    return response.data[0].embedding;
  }

  // ── Upsert vecteur ───────────────────────────────────────────────────────

  async upsertVector(
    nodeId: string,
    nodeType: string,
    textToEmbed: string,
    payload: Record<string, unknown>
  ): Promise<void> {
    const collection = TYPE_TO_COLLECTION[nodeType];
    if (!collection) throw new Error(`Type de nœud inconnu : ${nodeType}`);

    await this.ensureCollections();
    const vector = await this.embed(textToEmbed);

    await this.qdrant.upsert(collection, {
      wait: true,
      points: [{ id: this.toQdrantId(nodeId), vector, payload }],
    });
  }

  // ── Recherche sémantique ─────────────────────────────────────────────────

  async search(
    query: string,
    nodeTypes: string[] = [],
    limit: number = 10,
    minScore: number = 0.5
  ): Promise<VectorSearchResult[]> {
    const vector = await this.embed(query);
    const collections =
      nodeTypes.length > 0
        ? nodeTypes.map((t) => TYPE_TO_COLLECTION[t]).filter(Boolean)
        : [...NODE_COLLECTIONS];

    const allResults: VectorSearchResult[] = [];

    for (const collection of collections) {
      try {
        const res = await this.qdrant.search(collection as string, {
          vector,
          limit,
          score_threshold: minScore,
          with_payload: true,
        });
        for (const r of res) {
          allResults.push({
            id: String(r.id),
            score: r.score,
            payload: (r.payload ?? {}) as Record<string, unknown>,
          });
        }
      } catch {
        // Collection vide ou inexistante — on ignore
      }
    }

    return allResults
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

  // Qdrant accepte UUIDs ou entiers — on hash le node_id en entier unsigned 64
  // Implémentation simplifiée : on utilise le string directement via payload
  private toQdrantId(nodeId: string): string {
    // Qdrant accepte les strings UUID v4 et les entiers.
    // On padde en UUID-like pour compatibilité maximale.
    const padded = nodeId.replace(/-/g, '').padEnd(32, '0').slice(0, 32);
    return [
      padded.slice(0, 8),
      padded.slice(8, 12),
      padded.slice(12, 16),
      padded.slice(16, 20),
      padded.slice(20, 32),
    ].join('-');
  }
}
