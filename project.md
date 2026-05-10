# Production RAG Pipeline with Full Eval Layer

## 1. Project Overview

### Project Name

Production RAG Pipeline with Hybrid Retrieval, Cross-Encoder Reranking, Full Evaluation Layer, and CI-Gated Regression Protection

### Core Goal

Build a production-grade Retrieval-Augmented Generation (RAG) system that goes far beyond a basic semantic-search prototype. The system must support hybrid retrieval, reranking, automated evaluation, observability, and CI-based quality protection so it resembles how real enterprise LLM systems are designed, measured, and maintained.

This project is not just a “chat with documents” application. It is a retrieval engineering and LLMOps project designed to demonstrate the following capabilities:

* building a robust ingestion and retrieval pipeline
* improving retrieval quality with hybrid search and reranking
* measuring quality through automated evaluation
* preventing silent regressions using CI gates
* tracking latency, token usage, and cost in production

### Why This Project Matters

Most junior RAG implementations only do:

* chunk documents
* create embeddings
* retrieve with vector similarity
* send retrieved chunks to an LLM
* generate an answer

That is not sufficient for production because it usually fails on:

* exact-match queries
* keyword-heavy queries
* noisy context retrieval
* hallucination risk from low-quality context
* absence of evaluation
* no regression protection after code changes
* no telemetry on latency and cost

This project solves those gaps.

---

## 2. Product Vision

### Vision Statement

Create a production-grade document QA platform that combines lexical and semantic retrieval, reranks retrieved evidence for precision, evaluates output quality automatically, and exposes operational telemetry for engineering and product decisions.

### Desired Outcome

At completion, the project should prove that the system can:

* answer document-grounded questions reliably
* retrieve context using both BM25 and vector search
* improve ranking quality using cross-encoder reranking
* quantify answer quality using RAGAS
* reject degraded retrieval/generation changes in CI
* log query-level telemetry for performance and cost monitoring

---

## 3. High-Level Functional Scope

The system will support five major capabilities:

1. Document ingestion and indexing
2. Query-time hybrid retrieval
3. Cross-encoder reranking and grounded answer generation
4. Evaluation and benchmark tracking
5. Production observability and CI quality gates

---

## 4. Tech Stack

### Primary Stack

* LangChain
* ChromaDB
* rank-bm25
* BAAI/bge-reranker
* RAGAS
* Supabase
* Next.js
* Vercel

### Supporting Stack

* Python backend for ingestion, retrieval, reranking, evaluation
* TypeScript frontend for UI
* GitHub Actions for CI
* OpenAI or another LLM provider for answer generation and judge/eval dependencies where needed

---

## 5. System Architecture

### Core Components

#### A. Ingestion Layer

Responsible for:

* document upload handling
* parsing and text extraction
* normalization and cleaning
* chunking
* metadata extraction
* embedding generation
* vector indexing in ChromaDB
* corpus preparation for BM25

#### B. Retrieval Layer

Responsible for:

* vector retrieval from ChromaDB
* BM25 retrieval over chunk corpus
* fusion of result sets using Reciprocal Rank Fusion (RRF)

#### C. Reranking Layer

Responsible for:

* taking top candidates from hybrid retrieval
* rescoring candidates using a cross-encoder reranker
* selecting final high-quality evidence chunks

#### D. Generation Layer

Responsible for:

* constructing the final prompt from top reranked chunks
* generating a grounded answer
* returning answer with citations/source references

#### E. Evaluation Layer

Responsible for:

* maintaining evaluation datasets
* running RAGAS-based scoring
* benchmarking retrieval and answer quality
* comparing improvements across experiments

#### F. Observability Layer

Responsible for:

* logging per-query latency
* tracking token counts
* estimating cost
* recording retrieved documents/chunks
* storing experiment/evaluation runs

#### G. CI Gate Layer

Responsible for:

* running eval suites on pull requests
* failing PRs when quality drops below thresholds
* protecting the system from unnoticed regressions

---

## 6. End-to-End Query Flow

1. User submits a question through the UI
2. Backend receives query
3. Query embedding is generated
4. Vector retrieval is run against ChromaDB
5. BM25 retrieval is run against indexed chunk text
6. Results are merged using RRF
7. Top fused candidates are passed to cross-encoder reranker
8. Top reranked chunks are selected
9. Prompt is assembled with selected evidence
10. LLM generates grounded answer
11. UI returns answer with sources
12. Telemetry is logged to Supabase

---

## 7. End-to-End Indexing Flow

1. User uploads one or more documents
2. Files are parsed into raw text
3. Text is cleaned and normalized
4. Documents are split into chunks
5. Chunk metadata is attached
6. Embeddings are generated for each chunk
7. Chunks and embeddings are stored in ChromaDB
8. Chunk text is added to BM25 corpus/index
9. Metadata is stored in Supabase
10. Ingestion status is returned to UI

---

## 8. Functional Requirements

### 8.1 Document Ingestion

The system must:

* accept document uploads
* parse supported document formats
* split content into chunks
* preserve metadata such as file name, section title, page number if available, chunk ID, source ID
* generate embeddings for chunks
* store chunks in vector store
* prepare chunks for lexical retrieval

### 8.2 Chunking Strategy

The system should support configurable chunking with:

* chunk size
* overlap size
* fallback sentence-aware splitting
* optional heading-aware splitting if feasible

Chunking parameters must be tunable and comparable in evaluation experiments.

### 8.3 Vector Retrieval

The system must:

* embed incoming queries
* retrieve top-k semantically similar chunks from ChromaDB
* return chunk text, metadata, and similarity score

### 8.4 BM25 Retrieval

The system must:

* build lexical retrieval corpus over chunk text
* retrieve top-k keyword-relevant chunks for the user query
* return chunk text, metadata, and BM25 score

### 8.5 Reciprocal Rank Fusion

The system must:

* merge vector and BM25 ranked lists using RRF
* support configurable fusion constant
* produce a unified ranking for downstream reranking

### 8.6 Cross-Encoder Reranking

The system must:

* accept top-N candidates from fused retrieval
* rescore query-chunk pairs with BAAI/bge-reranker
* sort candidates by reranker score
* select final top-M chunks for generation

### 8.7 Grounded Answer Generation

The system must:

* use only selected chunks as evidence context
* generate concise, grounded answers
* return citations or source references
* avoid unsupported claims

### 8.8 Evaluation

The system must:

* support an eval dataset containing question, reference answer, and optional ideal context
* run RAGAS metrics including:

  * Faithfulness
  * Context Precision
  * Context Recall
  * Answer Relevance
* store evaluation results with timestamp and config version

### 8.9 CI Quality Gate

The system must:

* run evaluation during pull requests or selected pushes
* compare metrics against thresholds
* fail CI if the threshold is not met

### 8.10 Observability

The system must log:

* query text
* retrieval latency
* reranking latency
* generation latency
* total latency
* token usage
* estimated cost
* top retrieved chunk IDs
* final chunk IDs used in generation
* model names/config used

---

## 9. Non-Functional Requirements

### Performance

* retrieval should be low-latency enough for interactive use
* reranking should be applied only to shortlisted candidates to control cost and delay
* the system should expose p50 and p95 latency metrics

### Reliability

* ingestion should gracefully handle parse errors
* retrieval pipeline should degrade safely if one retriever fails
* logs should persist even if generation fails

### Maintainability

* architecture must be modular
* each retrieval stage should be isolated and testable
* configs must be externalized where practical

### Scalability

Initial implementation can target local/small-scale usage, but architecture should be designed so that components can later be replaced with more scalable systems.

### Transparency

* answer should be source-grounded
* user should be able to inspect supporting chunks

---

## 10. Data Model

### Suggested Core Entities

#### documents

Stores uploaded document-level metadata.
Fields may include:

* id
* title
* file_name
* source_type
* uploaded_at
* checksum
* parse_status

#### chunks

Stores text chunks and metadata.
Fields may include:

* id
* document_id
* chunk_index
* text
* section_title
* page_number
* token_count
* embedding_model
* created_at

#### query_logs

Stores query execution telemetry.
Fields may include:

* id
* query_text
* answer_text
* retrieval_latency_ms
* rerank_latency_ms
* generation_latency_ms
* total_latency_ms
* input_tokens
* output_tokens
* estimated_cost
* created_at

#### retrieval_logs

Stores retrieval trace information.
Fields may include:

* id
* query_log_id
* retriever_type
* chunk_id
* rank
* score
* selected_for_generation

#### eval_runs

Stores benchmark run metadata.
Fields may include:

* id
* run_name
* dataset_version
* config_version
* created_at
* mean_faithfulness
* mean_context_precision
* mean_context_recall
* mean_answer_relevance
* pass_fail

#### eval_samples

Stores per-sample evaluation results.
Fields may include:

* id
* eval_run_id
* question
* generated_answer
* faithfulness
* context_precision
* context_recall
* answer_relevance

---

## 11. Retrieval Design Details

### Why Hybrid Retrieval

Pure vector search is weak on:

* exact terms
* identifiers
* section references
* rare technical phrases

Pure BM25 is weak on:

* paraphrases
* semantic similarity
* natural language rewordings

Hybrid retrieval improves both recall and robustness.

### Why RRF Instead of Raw Score Addition

BM25 and vector similarity scores are not naturally calibrated to the same scale. RRF uses ranked position rather than raw score, making fusion more robust and easier to implement.

### Why Cross-Encoder Reranking

Initial retrieval should optimize recall. Reranking improves precision by using a slower but more accurate query-document relevance model.

### Intended Retrieval Pattern

* broad retrieval first
* precise reranking second
* generation only after evidence refinement

---

## 12. Evaluation Design

### Evaluation Dataset Requirements

Create a benchmark dataset with at least:

* 30 to 100 high-quality questions for initial version
* reference answers
* optionally gold context or expected supporting source references

The dataset should cover:

* exact keyword queries
* paraphrased semantic queries
* multi-hop or multi-part questions where feasible
* section-specific or fact-specific questions
* ambiguous queries if the product must support them

### Core Metrics

#### Faithfulness

Measures whether the generated answer is supported by retrieved context.

#### Context Precision

Measures how much of the retrieved context is actually relevant.

#### Context Recall

Measures whether the retrieved context contains the information needed to answer.

#### Answer Relevance

Measures whether the answer meaningfully addresses the user question.

### Evaluation Goals

Primary goal:

* improve context precision substantially through hybrid retrieval and reranking

Secondary goals:

* maintain or improve faithfulness
* maintain strong answer relevance
* avoid harming context recall during precision tuning

---

## 13. CI/CD Requirements

### CI Objectives

The CI pipeline must:

* install dependencies
* run tests
* run evaluation suite on benchmark set
* compare resulting metrics against minimum thresholds
* fail the PR if metrics regress below required standards

### Example Quality Gate Thresholds

These are placeholders and must be updated after baseline experiments:

* Faithfulness >= 0.80
* Context Precision >= 0.80
* Context Recall >= 0.75
* Answer Relevance >= 0.78

### Expected GitHub Action Responsibilities

* set up Python environment
* install project dependencies
* run benchmark script
* save or print metric summary
* exit with non-zero status on failure

---

## 14. Observability Requirements

### Logged Metrics Per Query

* query timestamp
* query text
* retriever top-k sizes
* fused candidate count
* reranked candidate count
* retrieval latency
* reranking latency
* generation latency
* total latency
* input token count
* output token count
* estimated LLM cost
* final answer length
* source chunk IDs

### Aggregated Analytics

The system should support dashboarding for:

* p50 latency
* p95 latency
* cost per query
* average tokens per request
* most commonly retrieved docs
* retrieval failure cases
* evaluation score trends over time

---

## 15. Frontend Requirements

### Primary UI Features

* document upload
* list of uploaded documents
* chat interface for asking questions
* answer display with supporting sources
* basic loading/error states

### Nice-to-Have UI Features

* inspect raw retrieved chunks
* inspect BM25 results vs vector results vs reranked results
* show latency and token usage for current query
* show evaluation dashboard for developers/admins

---

## 16. Backend Requirements

### Backend Responsibilities

* expose upload endpoint
* expose query endpoint
* manage document ingestion pipeline
* manage retriever orchestration
* call reranker
* construct generation prompt
* call LLM
* persist telemetry and evaluation results

### Suggested Service Separation

* ingestion service
* retrieval service
* reranking service
* generation service
* evaluation service
* telemetry service

---

## 17. Suggested Folder Structure

```text
project-root/
├── apps/
│   ├── web/                         # Next.js frontend
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── package.json
│   └── api/                         # Python backend
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── api/
│       │   │   ├── routes_upload.py
│       │   │   ├── routes_query.py
│       │   │   └── routes_eval.py
│       │   ├── core/
│       │   │   ├── ingestion/
│       │   │   ├── retrieval/
│       │   │   ├── reranking/
│       │   │   ├── generation/
│       │   │   ├── evaluation/
│       │   │   └── telemetry/
│       │   ├── db/
│       │   └── schemas/
│       ├── scripts/
│       │   ├── ingest_documents.py
│       │   ├── run_eval.py
│       │   └── benchmark_compare.py
│       ├── tests/
│       └── pyproject.toml
├── data/
│   ├── raw/
│   ├── processed/
│   └── eval/
│       ├── benchmark_v1.json
│       └── benchmark_v2.json
├── infra/
│   ├── github/
│   │   └── workflows/
│   │       └── rag_eval.yml
│   └── sql/
│       └── supabase_schema.sql
├── docs/
│   ├── prd.md
│   ├── architecture.md
│   ├── eval-plan.md
│   └── decisions/
└── README.md
```

---

## 18. Phased Development Plan

## Phase 0 — Project Setup

### Objective

Initialize monorepo/project structure and baseline environment.

### Deliverables

* frontend and backend scaffolding
* env management
* dependency installation
* local startup documentation

### Exit Criteria

* project boots locally
* frontend and backend communicate

---

## Phase 1 — Baseline Vector RAG

### Objective

Build minimal end-to-end RAG with document upload, chunking, embeddings, vector retrieval, and answer generation.

### Deliverables

* document ingestion flow
* ChromaDB indexing
* query endpoint
* LLM answer generation with retrieved sources
* basic UI chat flow

### Exit Criteria

* user can upload documents and ask questions
* answers are returned with source chunks

---

## Phase 2 — BM25 Lexical Retrieval

### Objective

Add lexical retrieval pipeline.

### Deliverables

* BM25 corpus over chunk text
* BM25 search function
* comparable retrieval outputs for debugging

### Exit Criteria

* query returns BM25 candidates alongside vector candidates

---

## Phase 3 — Hybrid Retrieval with RRF

### Objective

Merge vector and BM25 retrieval into a unified ranking.

### Deliverables

* RRF implementation
* configurable retrieval depths
* debug trace for fused ranking

### Exit Criteria

* query pipeline uses fused retrieval results
* ranking behaves sensibly on keyword and semantic queries

---

## Phase 4 — Cross-Encoder Reranking

### Objective

Improve precision with reranking.

### Deliverables

* integration with BAAI/bge-reranker
* rerank top fused candidates
* select final chunks for prompt construction

### Exit Criteria

* final generation context comes from reranked results
* manual query inspection shows reduced noise

---

## Phase 5 — Evaluation Dataset and RAGAS

### Objective

Create benchmark set and automated measurement.

### Deliverables

* curated eval dataset
* evaluation script
* RAGAS metrics output
* experiment comparison notes

### Exit Criteria

* system produces reproducible metric scores
* baseline scores are recorded

---

## Phase 6 — Tuning and Improvement Loop

### Objective

Improve system metrics through controlled experiments.

### Areas to Tune

* chunk size
* chunk overlap
* top-k values
* RRF fusion constant
* rerank candidate depth
* number of final chunks in generation context
* prompt structure

### Exit Criteria

* measurable improvement over baseline, especially in context precision

---

## Phase 7 — Observability and Supabase Logging

### Objective

Track runtime quality and cost.

### Deliverables

* query logs persisted to Supabase
* latency measurements per stage
* token and cost estimates
* basic metrics dashboard or query views

### Exit Criteria

* per-query telemetry is visible and stored

---

## Phase 8 — CI-Gated Evaluation

### Objective

Protect quality in pull requests.

### Deliverables

* GitHub Action workflow
* metric threshold enforcement
* PR failure on regression

### Exit Criteria

* benchmark runs in CI
* threshold failure blocks merge

---

## Phase 9 — UX and Developer Tooling Polish

### Objective

Improve usability and debuggability.

### Deliverables

* source inspection UI
* retrieval trace panel
* better error handling
* developer documentation

### Exit Criteria

* project is portfolio-ready and demo-friendly

---

## 19. Success Metrics

### Primary Success Metrics

* context precision improved materially from baseline
* faithfulness remains strong or improves
* evaluation is reproducible
* CI prevents metric regressions
* latency and cost are visible per query

### Portfolio Success Criteria

The final project should be strong enough that the developer can confidently explain:

* lexical vs semantic retrieval
* RRF fusion
* cross-encoder reranking
* why retrieval quality affects hallucination risk
* how RAGAS metrics were used
* how CI gates protect LLM quality
* how observability informs engineering tradeoffs

---

## 20. Risks and Tradeoffs

### Reranking Latency

Cross-encoder reranking improves relevance but adds latency. Candidate count must be controlled.

### Eval Cost

RAGAS and LLM-based eval components may increase experiment cost.

### Benchmark Quality Risk

A weak benchmark dataset gives misleading metrics. Eval design must be taken seriously.

### Small-Scale Infra Choices

ChromaDB is sufficient for this project, but larger production systems may prefer other vector databases.

### Overengineering Risk

The goal is strong production architecture, but each phase must be completed and validated before adding complexity.

---

## 21. What This Project Demonstrates on Resume

This project demonstrates:

* retrieval engineering
* production RAG design
* ranking system design
* evaluation-driven improvement
* CI-based regression protection for LLM apps
* observability and cost awareness
* modular system thinking

### Resume Bullet

Built a production-grade RAG pipeline using hybrid BM25 plus vector retrieval, Reciprocal Rank Fusion, and BGE cross-encoder reranking; improved context precision through eval-driven tuning, added automated RAGAS benchmarking with CI-gated regression checks, and logged latency, token usage, and cost telemetry to Supabase.

---

## 22. Build Rules for Claude Code

Claude Code must follow these rules while implementing this project:

1. Build phase by phase only.
2. Do not skip directly to advanced features before a working baseline exists.
3. Keep backend modules separated by responsibility.
4. Prefer explicit and readable code over clever abstractions early on.
5. After each phase, ensure the feature works before moving on.
6. Do not hallucinate unavailable infrastructure.
7. Keep configuration values centralized.
8. Add logging and comments where debugging retrieval quality will matter.
9. Whenever retrieval behavior changes, preserve the ability to compare old vs new behavior.
10. Keep evaluation scripts reproducible and deterministic where possible.

---

## 23. Immediate Next Step

Start with Phase 0 and Phase 1 only.

That means:

* scaffold frontend and backend
* implement upload flow
* parse and chunk documents
* embed and store in ChromaDB
* implement vector retrieval
* generate answers with retrieved sources
* verify end-to-end baseline before adding BM25

Do not implement BM25, reranking, or RAGAS until the baseline vector RAG works correctly.


keep in mind codex will review your code so work accordingly
