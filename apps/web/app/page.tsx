"use client";

import { useRef, useState } from "react";
import {
  queryDocuments,
  QueryResponse,
  RetrievedChunk,
  RetrievalMode,
  uploadDocument,
} from "@/lib/api";

const MODE_LABELS: Record<RetrievalMode, string> = {
  vector: "Vector",
  bm25: "BM25",
  hybrid: "Hybrid",
};

function Badge({ label, value }: { label: string; value: string | number }) {
  return (
    <span className="inline-flex min-h-7 items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 text-xs text-slate-500">
      <span>{label}</span>
      <span className="font-semibold text-slate-800">{value}</span>
    </span>
  );
}

function EmptyPanel({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-5">
      <p className="text-sm font-medium text-slate-800">{title}</p>
      <p className="mt-1 text-sm leading-6 text-slate-500">{body}</p>
    </div>
  );
}

function ChunkAccordion({
  chunks,
  label,
  accent = false,
}: {
  chunks: RetrievedChunk[];
  label: string;
  accent?: boolean;
}) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (chunks.length === 0) {
    return <EmptyPanel title="No chunks found" body="Upload a document and ask a question to populate this section." />;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {label}
        </p>
        <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
          {chunks.length}
        </span>
      </div>

      {chunks.map((chunk, i) => {
        const isOpen = expanded === i;
        return (
          <div
            key={chunk.chunk_id || i}
            className={`overflow-hidden rounded-lg border bg-white ${
              accent ? "border-cyan-200" : "border-slate-200"
            }`}
          >
            <button
              type="button"
              onClick={() => setExpanded(isOpen ? null : i)}
              className={`grid w-full grid-cols-[1fr_auto] items-start gap-3 px-3 py-3 text-left transition-colors ${
                accent
                  ? "hover:bg-cyan-50"
                  : "hover:bg-slate-50"
              }`}
            >
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium text-slate-900">
                  {i + 1}. {chunk.file_name || "Untitled source"}
                </span>
                <span className="mt-0.5 block text-xs text-slate-500">
                  Chunk {chunk.chunk_index} - {chunk.retriever}
                </span>
              </span>
              <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-600">
                {chunk.score.toFixed(3)}
              </span>
            </button>

            {isOpen && (
              <div className="border-t border-slate-100 bg-slate-50 px-3 py-3">
                <p className="max-h-72 overflow-auto whitespace-pre-wrap text-sm leading-6 text-slate-700">
                  {chunk.text}
                </p>
                {chunk.source_retrievers && chunk.source_retrievers.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {chunk.source_retrievers.map((retriever) => (
                      <span
                        key={retriever}
                        className="rounded-md bg-violet-50 px-2 py-1 text-xs font-medium text-violet-700"
                      >
                        {retriever} rank {chunk.source_ranks?.[retriever]} (
                        {chunk.source_scores?.[retriever]?.toFixed(3)})
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function Home() {
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<
    { name: string; chunks: number }[]
  >([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<RetrievalMode>("hybrid");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [showInspector, setShowInspector] = useState(false);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    try {
      const res = await uploadDocument(file);
      if (res.parse_status === "ok") {
        setUploadedFiles((prev) => [
          ...prev,
          { name: res.file_name, chunks: res.num_chunks },
        ]);
      } else {
        setUploadError(
          `Parse failed (${res.parse_status}): ${res.error ?? "unknown error"}`
        );
      }
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleQuery(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setResult(null);
    setQueryError(null);
    setShowInspector(false);

    try {
      setResult(await queryDocuments(question.trim(), mode));
    } catch (err: unknown) {
      setQueryError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 flex flex-col gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700">
              RAG Evaluation Workbench
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              Production RAG Pipeline
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Upload documents, ask grounded questions, compare retrieval modes,
              and inspect the exact chunks used to produce an answer.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
              <p className="text-lg font-semibold text-slate-900">{uploadedFiles.length}</p>
              <p className="text-xs text-slate-500">Files</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
              <p className="text-lg font-semibold text-slate-900">
                {uploadedFiles.reduce((sum, file) => sum + file.chunks, 0)}
              </p>
              <p className="text-xs text-slate-500">Chunks</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
              <p className="text-lg font-semibold text-slate-900">{MODE_LABELS[mode]}</p>
              <p className="text-xs text-slate-500">Mode</p>
            </div>
          </div>
        </header>

        <div className="grid flex-1 gap-5 lg:grid-cols-[380px_1fr]">
          <aside className="space-y-5">
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-4">
                <h2 className="text-base font-semibold text-slate-900">Documents</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Add PDF, TXT, or MD files to build the local vector index.
                </p>
              </div>

              <label className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center transition-colors hover:border-cyan-500 hover:bg-cyan-50">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.md"
                  onChange={handleUpload}
                  disabled={uploading}
                  className="sr-only"
                />
                <span className="text-sm font-semibold text-slate-900">
                  {uploading ? "Indexing document..." : "Choose a document"}
                </span>
                <span className="mt-1 text-xs leading-5 text-slate-500">
                  The file is parsed, chunked, embedded, and added to Chroma.
                </span>
              </label>

              {uploadError && (
                <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {uploadError}
                </div>
              )}

              <div className="mt-4 space-y-2">
                {uploadedFiles.length === 0 ? (
                  <p className="rounded-lg bg-slate-50 px-3 py-3 text-sm text-slate-500">
                    No documents uploaded in this session.
                  </p>
                ) : (
                  uploadedFiles.map((file, i) => (
                    <div
                      key={`${file.name}-${i}`}
                      className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2"
                    >
                      <span className="min-w-0 truncate text-sm font-medium text-slate-800">
                        {file.name}
                      </span>
                      <span className="shrink-0 rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">
                        {file.chunks} chunks
                      </span>
                    </div>
                  ))
                )}
              </div>
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-base font-semibold text-slate-900">Retrieval Mode</h2>
              <div className="mt-3 grid grid-cols-3 gap-2">
                {(Object.keys(MODE_LABELS) as RetrievalMode[]).map((retrievalMode) => (
                  <button
                    key={retrievalMode}
                    type="button"
                    onClick={() => setMode(retrievalMode)}
                    className={`min-h-10 rounded-lg border px-3 text-sm font-semibold transition-colors ${
                      mode === retrievalMode
                        ? "border-cyan-700 bg-cyan-700 text-white"
                        : "border-slate-200 bg-white text-slate-600 hover:border-cyan-400"
                    }`}
                  >
                    {MODE_LABELS[retrievalMode]}
                  </button>
                ))}
              </div>
            </section>
          </aside>

          <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 p-5">
              <h2 className="text-base font-semibold text-slate-900">Ask a Question</h2>
              <form onSubmit={handleQuery} className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question grounded in your uploaded documents..."
                  disabled={loading}
                  className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-cyan-600 focus:ring-4 focus:ring-cyan-100 disabled:opacity-60"
                />
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="min-h-11 rounded-lg bg-slate-950 px-5 text-sm font-semibold text-white transition-colors hover:bg-cyan-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {loading ? "Answering..." : "Ask"}
                </button>
              </form>
            </div>

            <div className="space-y-5 p-5">
              {queryError && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {queryError}
                </div>
              )}

              {!result && !queryError && (
                <EmptyPanel
                  title="Ready when you are"
                  body="Upload a document, choose a retrieval mode, and ask a question. The answer and supporting sources will appear here."
                />
              )}

              {result && (
                <>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        Grounded Answer
                      </p>
                      <span className="rounded-md bg-white px-2 py-1 text-xs font-medium text-slate-600">
                        {result.retrieval_mode}
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap text-sm leading-7 text-slate-800">
                      {result.answer}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge label="retrieval" value={`${result.retrieval_latency_ms}ms`} />
                    <Badge label="generation" value={`${result.generation_latency_ms}ms`} />
                    <Badge label="total" value={`${result.total_latency_ms}ms`} />
                    <Badge
                      label="tokens"
                      value={result.input_tokens + result.output_tokens}
                    />
                    <Badge label="model" value={result.model} />
                  </div>

                  <ChunkAccordion
                    chunks={result.sources}
                    label="Sources used in answer"
                    accent
                  />

                  <div className="rounded-xl border border-slate-200">
                    <button
                      type="button"
                      onClick={() => setShowInspector((value) => !value)}
                      className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold text-slate-900"
                    >
                      <span>Retrieval inspector</span>
                      <span className="text-slate-500">{showInspector ? "Hide" : "Show"}</span>
                    </button>

                    {showInspector && (
                      <div className="grid gap-4 border-t border-slate-200 bg-slate-50 p-4 xl:grid-cols-2">
                        <ChunkAccordion
                          chunks={result.debug.vector_candidates}
                          label="Vector candidates"
                        />
                        <ChunkAccordion
                          chunks={result.debug.bm25_candidates}
                          label="BM25 candidates"
                        />
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
