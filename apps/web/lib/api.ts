const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type RetrievalMode = "vector" | "bm25" | "hybrid";

export interface UploadResponse {
  document_id: string;
  file_name: string;
  parse_status: string;
  num_chunks: number;
  error?: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  file_name: string;
  chunk_index: number;
  text: string;
  score: number;
  retriever: string;
  source_retrievers?: string[];
  source_ranks?: Record<string, number>;
  source_scores?: Record<string, number>;
}

export interface RetrievalDebug {
  vector_candidates: RetrievedChunk[];
  bm25_candidates: RetrievedChunk[];
}

export interface QueryResponse {
  question: string;
  answer: string;
  retrieval_mode: string;
  sources: RetrievedChunk[];
  debug: RetrievalDebug;
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  model: string;
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Upload failed");
  }

  return res.json();
}

export async function queryDocuments(
  question: string,
  mode: RetrievalMode
): Promise<QueryResponse> {
  const res = await fetch(`${API_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, retrieval_mode: mode }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Query failed");
  }

  return res.json();
}
