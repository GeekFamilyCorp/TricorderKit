/**
 * TricorderKit — graph-server
 * Qdrant Client — wrapper pour embedding + vector search
 * Embedding : Ollama / nomic-embed-text (local, zéro coût, 768 dims)
 * Ollama >= 0.1.26 : POST /api/embed { model, input } → { embeddings: number[][] }
 */

import { QdrantClient } from '@qdrant/js-client-rest';

const VECTOR_SIZE = 768;
const DISTANCE    = 'Cosine';

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

async function ollamaEmbed(text: string): Promise<number[]> {
  const ollamaUrl = process.env.OLLAMA_URL      ?? 'http://localhost:11434';
  const model     = process.env.EMBEDDING_MODEL ?? 'nomic-embed-text';

  const res = await fetch(`${ollamaUrl}/api/embed`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ model, input: text }),
  });

  if (!res.ok) {
    throw new Error(`Ollama embed error ${res.status}: ${await res.text()}`);
  }

  const data = await res.json() as { embeddings: number[][] };
  return data.embeddings[0];
}

export class TKQdrantClient {
  private qdrant: QdrantClient;

  constructor(
    qdrantUrl: string = process.env.QDRANT_URL     ?? 'http://localhost:6333',
    qdrantKey: string = process.env.QDRANT_API_KEY ?? ''
  ) {
    this.qdrant = new QdrantClient({
      url: qdrantUrl,
      ...(qdrantKey ? { apiKey: qdrantKey } : {}),
    });
  }

  async ping(): Promise<boolean> {
    try {
      await this.qdrant.getCollections();
      return true;
    } catch {
      return false;
    }
  }

  async ensureCollections(): Promise<void> {
    const existing      = await this.qdrant.getCollections();
    const existingNames = existing.collections.map((c) => c.name);
    for (const name of NODE_COLLECTIONS) {
      if (!existingNames.includes(name)) {
        await this.qdrant.createCollection(name, {
          vectors: { size: VECTOR_SIZE, distance: DISTANCE },
        });
      }
    }
  }

  async embed(text: string): Promise<number[]> {
    return ollamaEmbed(text);
  }

  async upsertVector(
    nodeId: string,
    nodeType: string,
    textToEmbed: string,
    payload: Record<string, unknown>
  ): Promise<void> {
    const collection = TYPE_TO_COLLECTION[nodeType];
    if (!collection) throw new Error(`Type de noeud inconnu : ${nodeType}`);
    await this.ensureCollections();
    const vector = await this.embed(textToEmbed);
    await this.qdrant.upsert(collection, {
      wait: true,
      points: [{ id: this.toQdrantId(nodeId), vector, payload }],
    });
  }

  async search(
    query: string,
    nodeTypes: string[] = [],
    limit: number = 10,
    minScore: number = 0.5
  ): Promise<VectorSearchResult[]> {
    const vector      = await this.embed(query);
    const collections =
      nodeTypes.length > 0
        ? nodeTypes.map((t) => TYPE_TO_COLLECTION[t]).filter(Boolean)
        : [...NODE_COLLECTIONS];
    const allResults: VectorSearchResult[] = [];
    for (const collection of collections) {
      try {
        const res = await this.qdrant.search(collection as string, {
          vector, limit, score_threshold: minScore, with_payload: true,
        });
        for (const r of res) {
          allResults.push({ id: String(r.id), score: r.score, payload: (r.payload ?? {}) as Record<string, unknown> });
        }
      } catch { /* collection vide */ }
    }
    return allResults.sort((a, b) => b.score - a.score).slice(0, limit);
  }

  private toQdrantId(nodeId: string): string {
    const padded = nodeId.replace(/-/g, '').padEnd(32, '0').slice(0, 32);
    return [padded.slice(0,8), padded.slice(8,12), padded.slice(12,16), padded.slice(16,20), padded.slice(20,32)].join('-');
  }
}
